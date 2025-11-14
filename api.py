import json
from datetime import datetime, date
from typing import List, Dict, Any
from uuid import UUID
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag_connector import RAGConnector
from llm_agent import LLM_Agent
import db_connector
import uuid

# --- FastAPI 애플리케이션 설정 ---
app = FastAPI()

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 프로덕션에서는 프론트엔드 주소로 제한해야 합니다.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 데이터 모델 ---
class ChatRequest(BaseModel):
    customer_id: str
    query: str

# --- 전역 인스턴스 초기화 ---
rag_connector: RAGConnector = None
llm_agent: LLM_Agent = None

@app.on_event("startup")
async def startup_event():
    """FastAPI 서버 시작 시 DB 및 AI 에이전트를 초기화합니다."""
    global rag_connector, llm_agent
    
    print("\n--- 🚀 서버 시작 및 AI 시스템 초기화 중 ---")
    
    # 1. DB 연결 및 데이터 로드 (PostgreSQL 테이블 생성 + 매뉴얼 로드)
    db_connector.initialize_db_and_data()
    
    # 2. ChromaDB 커넥터 초기화
    rag_connector = RAGConnector()
    
    # 3. LLM Agent 초기화
    llm_agent = LLM_Agent(rag_connector=rag_connector)
    
    print("--- ✅ AI 시스템 초기화 완료. 서버 가동 준비 완료. ---\n")

# --- API 엔드포인트 ---
@app.post("/api/chat")
async def handle_chat(request: ChatRequest):
    if not llm_agent:
        return {"error": "LLM 에이전트가 초기화되지 않았습니다."}
    
    print(f"-> 💬 수신된 쿼리: customer_id='{request.customer_id}', query='{request.query}'")
    
    try:
        # LLM 에이전트를 통해 응답 생성
        response_text = llm_agent.generate_response(
            customer_id=request.customer_id,
            customer_query=request.query
        )
        
        # 대화 로그 저장
        log_id = str(uuid.uuid4())
        db_connector.save_inquiry_log(
            log_id=log_id,
            customer_id=request.customer_id,
            input_text=request.query,
            ai_action_failed=response_text # 초기 응답을 저장
        )
        
        return {"response": response_text, "log_id": log_id}
    except Exception as e:
        print(f"❌ 채팅 처리 중 오류 발생: {e}")
        return {"error": "응답 생성 중 오류가 발생했습니다."}

@app.post("/api/feedback")
async def handle_feedback(
    log_id: str = Form(...),
    resolution_feedback: str = Form(...),
    final_resolution: str = Form(None)
):
    try:
        db_connector.update_inquiry_log_feedback(
            log_id=log_id,
            feedback=resolution_feedback,
            final_resolution=final_resolution
        )
        return {"message": "피드백이 성공적으로 저장되었습니다."}
    except Exception as e:
        print(f"❌ 피드백 처리 중 오류 발생: {e}")
        return {"error": "피드백 저장 중 오류가 발생했습니다."}

@app.get("/")
def read_root():
    return {"message": "CS & CRM LLM Agent API가 실행 중입니다."}

@app.get("/api/admin/kpis")
async def get_admin_kpis():
    try:
        unanswered_qnas = db_connector.get_unanswered_qnas_count()
        pending_claims = db_connector.get_pending_claims_count()
        low_stock_products = db_connector.get_low_stock_products_count()
        
        settlement_data = db_connector.get_settlement_data_from_db()
        latest_settlement_amount = settlement_data[-1]['total_settlement_amount'] if settlement_data else 0

        return {
            "unanswered_qnas": unanswered_qnas,
            "pending_claims": pending_claims,
            "low_stock_products": low_stock_products,
            "latest_settlement_amount": latest_settlement_amount
        }
    except Exception as e:
        print(f"❌ 관리자 KPI 조회 중 오류 발생: {e}")
        return {"error": "관리자 KPI 조회 중 오류가 발생했습니다."}

@app.get("/api/admin/warnings")
async def get_admin_warnings():
    warnings = []
    try:
        # 재고 경고
        low_stock_products = db_connector.get_low_stock_products(threshold=50)
        for product in low_stock_products:
            warnings.append(f"[재고 경고] '{product['product_name']}' (상품번호: {product['origin_product_no']}) 재고 {product['stock_quantity']}개 남음.")
        
        # 클레임 급증 경고 (예: 24시간 내 평점 2점 이하 리뷰 3건 이상)
        recent_negative_reviews = db_connector.get_recent_negative_reviews(hours=24, rating_threshold=2)
        
        # 상품별 부정 리뷰 카운트
        product_negative_review_counts = {}
        for review in recent_negative_reviews:
            product_id = review['product_id']
            product_negative_review_counts[product_id] = product_negative_review_counts.get(product_id, 0) + 1
        
        for product_id, count in product_negative_review_counts.items():
            if count >= 3: # 3건 이상이면 클레임 급증으로 간주
                # 상품명 조회 (db_connector에 get_product_name_by_id 함수가 필요할 수 있음)
                # 임시로 products 테이블에서 직접 조회한다고 가정
                product_info = next((p for p in db_connector.get_products_from_db() if p['origin_product_no'] == product_id), None)
                product_name = product_info['product_name'] if product_info else f"상품번호 {product_id}"
                warnings.append(f"[클레임 급증] '{product_name}' 상품, 24시간 내 부정 리뷰 {count}건 발생.")

    except Exception as e:
        print(f"❌ 관리자 경고 조회 중 오류 발생: {e}")
        warnings.append(f"경고 조회 중 오류 발생: {e}")
    
    return {"warnings": warnings}

@app.get("/api/admin/sales_trend")
async def get_admin_sales_trend():
    try:
        settlement_data = db_connector.get_settlement_data_from_db()
        
        # 최근 7일간의 데이터만 추출
        # settle_date는 datetime.date 객체이므로 ISO 형식 문자열로 변환
        sales_trend = [
            {"date": data['settle_date'].isoformat(), "amount": data['total_settlement_amount']}
            for data in settlement_data[-7:] # 마지막 7개 데이터
        ]
        return {"sales_trend": sales_trend}
    except Exception as e:
        print(f"❌ 일간 매출 추이 조회 중 오류 발생: {e}")
        return {"error": "일간 매출 추이 조회 중 오류가 발생했습니다."}

@app.get("/api/admin/negative_reviews")
async def get_negative_reviews_with_draft_replies():
    reviews_with_replies = []
    try:
        all_reviews = db_connector.get_reviews_from_db()
        negative_reviews = [r for r in all_reviews if r['rating'] <= 2] # 1점 또는 2점 리뷰
        
        products = db_connector.get_products_from_db()
        product_map = {p['origin_product_no']: p['product_name'] for p in products}

        for review in negative_reviews:
            product_name = product_map.get(review['product_id'], "알 수 없는 상품")
            # LLM Agent를 사용하여 답변 초안 생성
            try:
                llm_response_json = llm_agent.generate_review_reply(review_text=review['review_text'], product_name=product_name)
                print(f"DEBUG: Raw LLM response for review reply: {llm_response_json}") # 디버그 출력
                llm_response = json.loads(llm_response_json)
                draft_reply = llm_response.get('draft_reply', 'AI 답변 생성 실패 (키 없음)')
            except json.JSONDecodeError as e:
                print(f"ERROR: JSON 디코딩 오류: {e} - Raw response: {llm_response_json}")
                draft_reply = f"AI 답변 생성 실패 (JSON 오류: {e})"
            except Exception as e:
                print(f"ERROR: LLM 답변 생성 중 예외 발생: {e}")
                draft_reply = f"AI 답변 생성 실패 (예외: {e})"
            
            reviews_with_replies.append({
                "review_id": review['review_id'],
                "product_name": product_name,
                "rating": review['rating'],
                "review_text": review['review_text'],
                "created_at": review['created_at'].isoformat() if isinstance(review['created_at'], (datetime, date)) else str(review['created_at']),
                "draft_reply": draft_reply
            })
        
        # 최신 리뷰가 먼저 오도록 정렬
        reviews_with_replies.sort(key=lambda x: x['created_at'], reverse=True)

    except Exception as e:
        print(f"❌ 부정 리뷰 및 답변 초안 조회 중 오류 발생: {e}")
        return {"error": f"부정 리뷰 및 답변 초안 조회 중 오류 발생: {e}"}
    
    return {"negative_reviews": reviews_with_replies}

@app.get("/api/orders")
async def get_orders_by_customer_id(customer_id: str):
    """특정 고객의 주문 목록을 조회합니다."""
    try:
        all_orders = db_connector.get_orders_from_db()
        customer_orders = [order for order in all_orders if order['customer_id'] == customer_id]
        return {"orders": customer_orders}
    except Exception as e:
        print(f"❌ 고객 주문 내역 조회 중 오류 발생: {e}")
        return {"error": f"고객 주문 내역 조회 중 오류가 발생했습니다."}

@app.get("/api/customers/{customer_id}/claims")
async def get_customer_claims(customer_id: str):
    """특정 고객의 클레임 목록을 조회합니다."""
    try:
        claims = db_connector.get_claims_by_customer(customer_id)
        return {"claims": claims}
    except Exception as e:
        print(f"❌ 고객 클레임 조회 중 오류 발생: {e}")
        return {"error": "고객 클레임 조회 중 오류가 발생했습니다."}

@app.get("/api/customers/{customer_id}/reviews")
async def get_customer_reviews(customer_id: str):
    """특정 고객의 리뷰 목록을 조회합니다."""
    try:
        reviews = db_connector.get_reviews_by_customer(customer_id)
        return {"reviews": reviews}
    except Exception as e:
        print(f"❌ 고객 리뷰 조회 중 오류 발생: {e}")
        return {"error": "고객 리뷰 조회 중 오류가 발생했습니다."}

@app.get("/api/admin/customers_by_segment")
async def get_customers_by_segment_api(segment: str):
    try:
        if segment == "All":
            customers = db_connector.get_customers_from_db()
        else:
            customers = db_connector.get_customers_by_segment(segment=segment)
        return {"customers": customers}
    except Exception as e:
        print(f"❌ 고객 세그먼트 조회 중 오류 발생: {e}")
        return {"error": f"고객 세그먼트 조회 중 오류 발생: {e}"}

@app.post("/api/admin/send_coupon")
async def send_coupon_api(customer_ids: List[str], coupon_details: str):
    # 실제 시스템에서는 이 곳에서 쿠폰 발송 로직을 구현합니다.
    print(f"✅ {len(customer_ids)}명의 고객에게 쿠폰 발송 요청: {coupon_details}")
    print(f"   대상 고객 ID: {customer_ids}")
    return {"message": f"{len(customer_ids)}명의 고객에게 쿠폰 발송 요청이 접수되었습니다. (시뮬레이션)"}

@app.get("/api/inquiries")
async def get_inquiries(status: str):
    """문의 상태(new, completed)에 따라 문의 목록을 조회합니다."""
    try:
        if status == "new":
            is_answered = False
        elif status == "completed":
            is_answered = True
        else:
            return {"error": "Invalid status value"}, 400
        
        inquiries = db_connector.get_inquiries_by_status(is_answered)
        return {"inquiries": inquiries}
    except Exception as e:
        print(f"❌ 문의 목록 조회 중 오류 발생: {e}")
        return {"error": "문의 목록 조회 중 오류가 발생했습니다."}

@app.get("/api/ai/suggestion")
async def get_ai_suggestion(query: str):
    """고객 문의에 대한 AI 답변 제안을 생성합니다."""
    if not llm_agent:
        return {"error": "LLM 에이전트가 초기화되지 않았습니다."}
    try:
        suggestion = llm_agent.get_ai_suggestion(query)
        return {"suggestion": suggestion}
    except Exception as e:
        print(f"❌ AI 답변 제안 생성 중 오류 발생: {e}")
        return {"error": "AI 답변 제안 생성 중 오류가 발생했습니다."}

@app.post("/api/admin/approve_review_reply")
async def approve_review_reply(review_id: str, approved_reply: str):
    # 실제 시스템에서는 이 곳에서 DB를 업데이트하거나 외부 리뷰 시스템에 게시합니다.
    print(f"✅ 리뷰 답변 승인 및 게시 요청: Review ID={review_id}, Approved Reply='{approved_reply}'")
    return {"message": "리뷰 답변이 성공적으로 승인 및 게시되었습니다. (시뮬레이션)"}

# --- 서버 실행 ---
# 이 파일을 직접 실행하려면: uvicorn api:app --reload
# 예: venv\Scripts\uvicorn.exe api:app --reload --port 8000

