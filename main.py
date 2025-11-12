from fastapi import FastAPI, Form, HTTPException
import os
from dotenv import load_dotenv
from typing import Optional
import uuid  # ❶ 자기진화: 로그 ID 생성을 위해 uuid 모듈 임포트
from llm_agent import LLM_Agent
from rag_connector import RAGConnector
from db_connector import initialize_db_and_data, get_db_connection # ❷ 자기진화: DB 연결 함수 임포트

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv() 

app = FastAPI()

# 전역 변수로 AI 에이전트와 RAG 커넥터를 저장합니다.
rag_connector: Optional[RAGConnector] = None
llm_agent: Optional[LLM_Agent] = None

@app.on_event("startup")
async def startup_event():
    """FastAPI 서버 시작 시 DB 및 AI 에이전트를 초기화합니다."""
    global rag_connector, llm_agent
    
    print("\n--- 🚀 서버 시작 및 AI 시스템 초기화 중 ---")
    
    # 1. DB 연결 및 데이터 로드 (PostgreSQL 테이블 생성 + 매뉴얼 로드)
    manuals_data = initialize_db_and_data()
    
    # 2. ChromaDB 커넥터 초기화
    rag_connector = RAGConnector()
    
    # 3. LLM Agent 초기화
    llm_agent = LLM_Agent(rag_connector=rag_connector)
    
    print("--- ✅ AI 시스템 초기화 완료. 서버 가동 준비 완료. ---\n")


@app.get("/")
def read_root():
    """서버 상태 확인 엔드포인트"""
    api_key_status = "Loaded" if os.getenv("OPENAI_API_KEY") else "Not Found"
    return {
        "message": "CS Agent Backend is Running!",
        "api_key_status": api_key_status,
        "agent_status": "Ready" if llm_agent else "Initializing..."
    }

@app.post("/api/query")
async def handle_customer_query(
    customer_query: str = Form(...),
    customer_id: str = Form("TEST_USER"),
    image_url: Optional[str] = Form(None) # 멀티모달 시연을 위한 이미지 URL 입력 필드
):
    """
    고객 문의를 받아 AI 에이전트가 답변을 생성하고, 그 과정을 모두 기록하는 메인 엔드포인트
    """
    global llm_agent
    if not llm_agent:
        raise HTTPException(status_code=503, detail="AI Agent is not initialized yet.")
    
    log_id = uuid.uuid4()
    
    enriched_query = customer_query
    
    # ❶ 멀티모달: 이미지 URL이 있는 경우, 이미지 분석 후 쿼리 강화
    if image_url:
        print(f"-> ✨ 멀티모달 분석 실행: {image_url}")
        try:
            # GPT-4o Vision API 호출
            vision_response = llm_agent.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "당신은 CS 전문가입니다. 이 이미지를 보고 고객이 어떤 문제를 겪고 있는지, 상품의 상태는 어떤지 간결하게 설명해주세요."},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }
                ],
                max_tokens=300,
            )
            image_description = vision_response.choices[0].message.content
            enriched_query = f"[이미지 분석 결과: {image_description}]\n\n[고객 원본 질문]: {customer_query}"
            print(f"-> ✨ 강화된 쿼리 생성:\n{enriched_query}")
        except Exception as vision_error:
            print(f"⚠️ 이미지 분석 중 오류 발생: {vision_error}")
            # 이미지 분석에 실패하더라도 텍스트 쿼리만으로 계속 진행
            pass

    try:
        # LLM Agent를 호출하여 답변 생성 (강화된 쿼리 사용)
        response_text = llm_agent.generate_response(
            customer_id=customer_id,
            customer_query=enriched_query,
            complexity="complex_multimodal" if image_url else "medium"
        )
        
        is_tool_generated = "도구_생성_수동결제_링크" in response_text

        # DB에 로그 기록
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO inquiry_logs (log_id, customer_id, input_text, ai_action_failed)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (str(log_id), customer_id, enriched_query, response_text) # 강화된 쿼리를 로그에 저장
                    )
                conn.commit()
            except Exception as db_error:
                print(f"DB 로깅 오류: {db_error}")
            finally:
                conn.close()

        return {
            "status": "success",
            "log_id": str(log_id),
            "query": enriched_query,
            "answer": response_text,
            "tool_generated": is_tool_generated
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 처리 중 서버 오류: {e}")

@app.post("/api/feedback")
async def handle_feedback(
    log_id: str = Form(...),
    resolution_feedback: str = Form(...), # "success" 또는 "failure"
    final_resolution: Optional[str] = Form(None) # 실패 시, 올바른 답변
):
    """AI 답변에 대한 피드백을 받아 DB에 기록합니다."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection failed.")

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE inquiry_logs
                SET resolution_feedback = %s, final_resolution = %s
                WHERE log_id = %s
                """,
                (resolution_feedback, final_resolution, log_id)
            )
            # UPDATE 쿼리가 실제로 행을 변경했는지 확인
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail=f"Log ID '{log_id}' not found.")
        conn.commit()
        return {"status": "success", "message": f"Feedback for log {log_id} has been recorded."}
    except HTTPException as http_exc:
        # 404 오류를 다시 발생시켜 클라이언트에게 전달
        raise http_exc
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {e}")
    finally:
        conn.close()


# (참고: /api/feedback 엔드포인트는 추후 자기진화 로직 구현 시 추가됩니다.)

if __name__ == '__main__':
    import uvicorn
    # uvicorn을 직접 실행합니다.
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)