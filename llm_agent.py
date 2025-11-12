import os
import uuid
from openai import OpenAI
from rag_connector import RAGConnector
from db_connector import get_failure_logs_by_customer

# 모델 분기 및 비용 효율화를 위해 LLaMA 대신 GPT-3.5-turbo를 저비용 모델로 가정
LOW_COST_MODEL = "gpt-3.5-turbo"
HIGH_COST_MODEL = "gpt-4o"

class LLM_Agent:
    def __init__(self, rag_connector: RAGConnector):
        # AI 에이전트 초기화 시 RAG 시스템 연결
        self.rag = rag_connector
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        print("✅ LLM Agent 초기화 완료.")

    def _determine_model(self, inquiry_complexity: str):
        """문의 복잡도에 따라 사용할 LLM 모델을 결정 (비용 절감 로직)"""
        # 복잡도에 따라 GPT-4o를 호출할지, 저비용 모델을 호출할지 결정합니다.
        if inquiry_complexity in ["high_urgency", "complex_multimodal"]:
            return HIGH_COST_MODEL
        return LOW_COST_MODEL

    def generate_response(self, customer_id: str, customer_query: str, complexity="medium"):
        """
        고객 문의를 처리하고 답변을 생성하는 메인 함수
        """
        # 1. RAG 검색 (CS 매뉴얼 기반 지식 획득)
        print(f"-> 1. RAG 검색 실행 중: {customer_query}")
        
        query_vector = self.rag.get_embedding(customer_query)
        retrieved_context = self.rag.retrieve_context(query_vector)

        # 2. 자기진화 및 행동 교정 (동적 프롬프트)
        # DB에서 현재 고객의 실패 로그를 읽어와 GPT-4o의 행동을 교정하는 지시사항을 생성
        failure_logs = get_failure_logs_by_customer(customer_id)
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
        당신은 네이버 스마트스토어 CS 전문가입니다. 아래 RAG 컨텍스트와 교정 지침을 최우선으로 참고하여 고객 문의에 답변하고, 반드시 필요한 경우에만 도구 생성 명령 JSON을 출력해야 합니다.
        [CS 정책 및 매뉴얼]: {retrieved_context}
        {correction_prompt}
        """

        try:
            response = self.openai_client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": customer_query}
                ],
                temperature=0.0
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"API 호출 오류 발생: {e}"

# (참고: FailureLog와 같은 Pydantic 모델은 models.py에 정의되어 있어야 합니다.)