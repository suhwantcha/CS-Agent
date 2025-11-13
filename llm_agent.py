import os
import uuid
from openai import OpenAI
from rag_connector import RAGConnector
import db_connector # db_connector 모듈 임포트
from models import FailureLog
import json # JSON 처리를 위해 추가
from datetime import date, datetime # datetime 객체 처리를 위해 추가
from decimal import Decimal # Decimal 객체 처리를 위해 추가
import config # config 모듈 임포트
from review_analyzer import summarize_recent_negative_reviews # 리뷰 분석기 임포트

class LLM_Agent:
    def __init__(self, rag_connector: RAGConnector):
        # AI 에이전트 초기화 시 RAG 시스템 연결
        self.rag = rag_connector
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        print(f"DEBUG: LLM_Agent initialized. self.client set: {hasattr(self, 'client')}")
        # 사용 가능한 도구 목록
        self.available_tools = {
            "get_customer_info": self.get_customer_info,
            "get_order_details": self.get_order_details,
            "get_product_info": self.get_product_info,
            "get_qna_by_product": self.get_qna_by_product,
            "get_reviews_by_product": self.get_reviews_by_product,
            "summarize_recent_negative_reviews": summarize_recent_negative_reviews,
            "get_top_margin_products": self.get_top_margin_products, # 추가
        }
        print("✅ LLM Agent 초기화 완료.")

    def _determine_model(self, inquiry_complexity: str):
        """문의 복잡도에 따라 사용할 LLM 모델을 결정 (비용 절감 로직)"""
        # 복잡도에 따라 GPT-4o를 호출할지, 저비용 모델을 호출할지 결정합니다.
        if inquiry_complexity in ["high_urgency", "complex_multimodal"]:
            return config.HIGH_COST_MODEL
        return config.LOW_COST_MODEL

    def _json_serial(self, obj):
        """JSON 직렬화할 수 없는 객체(예: datetime, Decimal)를 처리하는 헬퍼 함수"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal): # Decimal 타입 추가
            return float(obj)
        raise TypeError ("Type %s not serializable" % type(obj))

    # --- LLM이 사용할 도구(Tools) 정의 시작 ---
    def get_customer_info(self, customer_id: str):
        """
        고객 ID를 기반으로 고객 정보를 조회합니다.
        :param customer_id: 조회할 고객의 ID
        :return: 고객 정보 딕셔너리 또는 None
        """
        customer = next((c for c in db_connector.get_customers_from_db() if c['customer_id'] == customer_id), None)
        if customer:
            return json.dumps(customer, ensure_ascii=False, default=self._json_serial)
        return json.dumps({"error": "고객 정보를 찾을 수 없습니다."}, ensure_ascii=False)

    def get_order_details(self, customer_id: str = None, order_id: str = None):
        """
        고객 ID 또는 주문 ID를 기반으로 주문 상세 정보를 조회합니다.
        :param customer_id: 조회할 고객의 ID (선택 사항)
        :param order_id: 조회할 주문의 ID (선택 사항)
        :return: 주문 정보 리스트 또는 None
        """
        orders = db_connector.get_orders_from_db()
        if order_id:
            filtered_orders = [o for o in orders if o['order_id'] == order_id or o['product_order_id'] == order_id]
        elif customer_id:
            filtered_orders = [o for o in orders if o['customer_id'] == customer_id]
        else:
            return json.dumps({"error": "고객 ID 또는 주문 ID가 필요합니다."}, ensure_ascii=False)
        
        if filtered_orders:
            return json.dumps(filtered_orders, ensure_ascii=False, default=self._json_serial)
        return json.dumps({"error": "주문 정보를 찾을 수 없습니다."}, ensure_ascii=False)

    def get_product_info(self, product_name: str = None, origin_product_no: int = None):
        """
        상품명 또는 원본 상품 번호를 기반으로 상품 정보를 조회합니다.
        :param product_name: 조회할 상품명 (선택 사항)
        :param origin_product_no: 조회할 원본 상품 번호 (선택 사항)
        :return: 상품 정보 딕셔너리 또는 None
        """
        products = db_connector.get_products_from_db()
        if origin_product_no:
            product = next((p for p in products if p['origin_product_no'] == origin_product_no), None)
        elif product_name:
            product = next((p for p in products if product_name in p['product_name']), None)
        else:
            return json.dumps({"error": "상품명 또는 원본 상품 번호가 필요합니다."}, ensure_ascii=False)
        
        if product:
            return json.dumps(product, ensure_ascii=False, default=self._json_serial)
        return json.dumps({"error": "상품 정보를 찾을 수 없습니다."}, ensure_ascii=False)

    def get_qna_by_product(self, product_name: str = None, origin_product_no: int = None):
        """
        상품명 또는 원본 상품 번호를 기반으로 해당 상품의 Q&A를 조회합니다.
        :param product_name: 조회할 상품명 (선택 사항)
        :param origin_product_no: 조회할 원본 상품 번호 (선택 사항)
        :return: Q&A 리스트 또는 None
        """
        qnas = db_connector.get_qnas_from_db()
        products = db_connector.get_products_from_db()
        
        target_product_no = None
        if origin_product_no:
            target_product_no = origin_product_no
        elif product_name:
            product = next((p for p in products if product_name in p['product_name']), None)
            if product:
                target_product_no = product['origin_product_no']
        
        if target_product_no:
            filtered_qnas = [q for q in qnas if q.get('origin_product_no') == target_product_no]
            if filtered_qnas:
                return json.dumps(filtered_qnas, ensure_ascii=False, default=self._json_serial)
            return json.dumps({"error": "해당 상품의 Q&A를 찾을 수 없습니다."}, ensure_ascii=False)
        return json.dumps({"error": "상품명 또는 원본 상품 번호가 필요합니다."}, ensure_ascii=False)

    def get_reviews_by_product(self, product_name: str = None, origin_product_no: int = None):
        """
        상품명 또는 원본 상품 번호를 기반으로 해당 상품의 리뷰를 조회합니다.
        :param product_name: 조회할 상품명 (선택 사항)
        :param origin_product_no: 조회할 원본 상품 번호 (선택 사항)
        :return: 리뷰 리스트 또는 None
        """
        reviews = db_connector.get_reviews_from_db()
        products = db_connector.get_products_from_db()

        target_product_no = None
        if origin_product_no:
            target_product_no = origin_product_no
        elif product_name:
            product = next((p for p in products if product_name in p['product_name']), None)
            if product:
                target_product_no = product['origin_product_no']
        
        if target_product_no:
            filtered_reviews = [r for r in reviews if r['product_id'] == target_product_no]
            if filtered_reviews:
                return json.dumps(filtered_reviews, ensure_ascii=False, default=self._json_serial)
            return json.dumps({"error": "해당 상품의 리뷰를 찾을 수 없습니다."}, ensure_ascii=False)
        return json.dumps({"error": "상품명 또는 원본 상품 번호가 필요합니다."}, ensure_ascii=False)

    def get_top_margin_products(self, limit: int = 3, period_days: int = 7):
        """
        지정된 기간 동안 마진이 가장 높은 상품 N개를 조회합니다.
        :param limit: 조회할 상품의 개수
        :param period_days: 마진을 계산할 기간(일 수)
        :return: 마진이 높은 상품 리스트 또는 오류 메시지
        """
        try:
            top_products = db_connector.calculate_product_margins(period_days=period_days)[:limit]
            if top_products:
                return json.dumps(top_products, ensure_ascii=False, default=self._json_serial)
            return json.dumps({"error": f"최근 {period_days}일간 마진 데이터를 찾을 수 없습니다."}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": f"마진 상품 조회 중 오류 발생: {e}"}, ensure_ascii=False)

    def generate_review_reply(self, review_text: str, product_name: str):
        """
        부정적인 리뷰에 대한 공손하고 도움이 되는 답변 초안을 생성합니다.
        :param review_text: 고객이 작성한 리뷰 텍스트
        :param product_name: 리뷰 대상 상품명
        :return: AI가 제안한 답변 초안
        """
        try:
            prompt = f"""
            다음은 고객이 '{product_name}' 상품에 대해 작성한 리뷰입니다:
            "{review_text}"

            이 부정적인 리뷰에 대해 고객에게 보낼 공손하고 도움이 되는 답변 초안을 작성해주세요.
            다음 사항을 포함해야 합니다:
            1. 고객의 불편함에 공감하는 내용
            2. 문제 해결을 위한 노력 또는 제안 (예: 추가 문의 유도, 개선 약속)
            3. 긍정적인 브랜드 이미지를 유지하는 어조
            
            응답은 반드시 다음과 같은 JSON 형식으로 제공해야 합니다:
            ```json
            {{
              "draft_reply": "여기에 생성된 답변을 입력하세요."
            }}
            ```
            """
            response = self.client.chat.completions.create(
                model=config.LOW_COST_MODEL, # 답변 생성은 저비용 모델 사용
                messages=[
                    {"role": "system", "content": "당신은 고객의 부정적인 리뷰에 대해 공손하고 도움이 되는 답변을 JSON 형식으로 생성하는 AI 어시스턴트입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"} # JSON 형식 강제
            )
            return response.choices[0].message.content # JSON 문자열을 직접 반환
        except Exception as e:
            return json.dumps({"error": f"리뷰 답변 생성 중 오류 발생: {e}"}, ensure_ascii=False)

    # --- LLM이 사용할 도구(Tools) 정의 끝 ---

    def _get_tool_definitions(self):
        """OpenAI API를 위한 도구 정의를 반환합니다."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_customer_info",
                    "description": "고객 ID를 기반으로 고객 정보를 조회합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {"type": "string", "description": "조회할 고객의 ID"}
                        },
                        "required": ["customer_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_order_details",
                    "description": "고객 ID 또는 주문 ID를 기반으로 주문 상세 정보를 조회합니다. 둘 중 하나는 반드시 제공되어야 합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {"type": "string", "description": "조회할 고객의 ID"},
                            "order_id": {"type": "string", "description": "조회할 주문의 ID"}
                        },
                        "required": []
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_product_info",
                    "description": "상품명 또는 원본 상품 번호를 기반으로 상품 정보를 조회합니다. 둘 중 하나는 반드시 제공되어야 합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "product_name": {"type": "string", "description": "조회할 상품명"},
                            "origin_product_no": {"type": "integer", "description": "조회할 원본 상품 번호"}
                        },
                        "required": []
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_qna_by_product",
                    "description": "상품명 또는 원본 상품 번호를 기반으로 해당 상품의 Q&A를 조회합니다. 둘 중 하나는 반드시 제공되어야 합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "product_name": {"type": "string", "description": "조회할 상품명"},
                            "origin_product_no": {"type": "integer", "description": "조회할 원본 상품 번호"}
                        },
                        "required": []
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_reviews_by_product",
                    "description": "상품명 또는 원본 상품 번호를 기반으로 해당 상품의 리뷰를 조회합니다. 둘 중 하나는 반드시 제공되어야 합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "product_name": {"type": "string", "description": "조회할 상품명"},
                            "origin_product_no": {"type": "integer", "description": "조회할 원본 상품 번호"}
                        },
                        "required": []
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "summarize_recent_negative_reviews",
                    "description": "지정된 기간(일 수) 동안의 부정적인 리뷰(평점 2점 이하)를 요약하여 보고서를 생성합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "days": {"type": "integer", "description": "요약할 기간(일 수), 기본값은 7일", "default": 7}
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_top_margin_products",
                    "description": "지정된 기간 동안 마진이 가장 높은 상품 N개를 조회합니다. BI 분석에 활용됩니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "description": "조회할 상품의 개수, 기본값은 3개", "default": 3},
                            "period_days": {"type": "integer", "description": "마진을 계산할 기간(일 수), 기본값은 7일", "default": 7}
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_review_reply",
                    "description": "부정적인 리뷰에 대한 공손하고 도움이 되는 답변 초안을 생성합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "review_text": {"type": "string", "description": "고객이 작성한 리뷰 텍스트"},
                            "product_name": {"type": "string", "description": "리뷰 대상 상품명"}
                        },
                        "required": ["review_text", "product_name"],
                    },
                },
            },
        ]

    def generate_response(self, customer_id: str, customer_query: str, complexity="medium"):
        """
        고객 문의를 처리하고 답변을 생성하는 메인 함수
        """
        # 1. RAG 검색 (CS 매뉴얼 기반 지식 획득)
        print(f"-> 1. RAG 검색 실행 중: {customer_query}")
        
        retrieved_context = self.rag.retrieve_context(customer_query)

        # 2. 자기진화 및 행동 교정 (동적 프롬프트)
        # DB에서 현재 고객의 실패 로그를 읽어와 GPT-4o의 행동을 교정하는 지시사항을 생성
        failure_logs = db_connector.get_failure_logs_by_customer(customer_id)
        correction_prompt = ""
        if failure_logs:
            print(f"-> ⚙️ 자기진화: {len(failure_logs)}개의 실패 기록을 발견하여 프롬프트에 반영합니다.")
            correction_prompt = "--- 경고: 이전 실패 기록 발견 ---\n"
            for log in failure_logs:
                correction_prompt += f"과거 '{log.input_text}' 문의에 대해 AI가 '{log.ai_action_failed}'라고 잘못 답변했습니다. 올바른 답변은 '{log.final_resolution}'입니다. 이 실수를 반복하지 마십시오.\n"
        
        # 3. 모델 선택 및 LLM 호출
        model_to_use = self._determine_model(complexity)
        print(f"-> 2. 모델 선택: {model_to_use}")

        system_prompt = f"""
        당신은 네이버 스마트스토어 CS 전문가입니다.
        고객 문의에 답변할 때, 가장 먼저 아래 제공된 [CS 정책 및 매뉴얼] RAG 컨텍스트를 활용하여 답변을 생성하십시오.
        만약 RAG 컨텍스트에서 답변을 찾을 수 없거나, 특정 고객, 주문, 상품, Q&A, 리뷰 정보와 같은 구체적인 데이터 조회가 필요한 경우에만 도구를 사용하십시오.
        도구 사용 후에는 도구의 결과를 바탕으로 고객 문의에 대한 최종 답변을 생성해야 합니다.
        {correction_prompt}
        [CS 정책 및 매뉴얼]: {retrieved_context}
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": customer_query}
        ]
        
        tools = self._get_tool_definitions()

        try:
            response = self.openai_client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                tools=tools,
                tool_choice="auto", # LLM이 사용할 도구를 자동으로 선택하도록 함
                temperature=0.0
            )
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # LLM이 도구 사용을 결정한 경우
            if tool_calls:
                print(f"-> 🛠️ LLM이 도구 사용을 결정했습니다: {tool_calls[0].function.name}")
                # 메시지 목록에 LLM의 응답을 추가
                messages.append(response_message) 

                # 각 도구 호출을 실행
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # 정의된 도구 함수를 호출
                    if function_name in self.available_tools:
                        function_to_call = self.available_tools[function_name]
                        tool_output = function_to_call(**function_args)
                        print(f"-> 💡 도구 '{function_name}' 실행 결과: {tool_output}")
                        # 도구의 결과를 메시지 목록에 추가
                        messages.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": tool_output,
                            }
                        )
                    else:
                        tool_output = json.dumps({"error": f"정의되지 않은 도구: {function_name}"}, ensure_ascii=False)
                        messages.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": tool_output,
                            }
                        )
                
                # 도구 실행 결과를 바탕으로 다시 LLM 호출
                second_response = self.openai_client.chat.completions.create(
                    model=model_to_use,
                    messages=messages,
                    temperature=0.0
                )
                return second_response.choices[0].message.content
            else:
                # LLM이 도구를 사용하지 않고 직접 답변을 생성한 경우
                return response_message.content

        except Exception as e:
            return f"API 호출 오류 발생: {e}"

# (참고: FailureLog와 같은 Pydantic 모델은 models.py에 정의되어 있어야 합니다.)