from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

# AI 자기진화 로직 구현 시 PostgreSQL inquiry_logs 테이블에 기록될 데이터 구조
class FailureLog(BaseModel):
    # UUID는 데이터베이스에 저장할 때 문자열로 변환하여 사용해야 합니다.
    log_id: UUID 
    customer_id: str
    input_text: str
    ai_action_failed: str
    resolution_feedback: str
    final_resolution: Optional[str] = None
    created_at: Optional[str] = None # DB에서 NOW()로 자동 생성되므로 Optional

# AI가 고객 문의를 분석한 후 결과를 저장하거나 반환할 때 사용할 구조
class CustomerInquiry(BaseModel):
    query_id: UUID
    customer_id: str
    query_text: str
    query_domain: str
    urgency: str
    image_url: Optional[str] = None
    audio_url: Optional[str] = None

# AI 도구 실행 요청 (LLM이 JSON 형태로 출력할 것을 예상)
class ToolCall(BaseModel):
    tool_name: str
    parameters: dict

# AI의 최종 응답 구조 (응답 텍스트 + 실행할 도구 목록)
class AgentResponse(BaseModel):
    answer_text: str
    tool_calls: List[ToolCall] = []

# (참고: 이 파일을 저장한 후, db_connector.py와 llm_agent.py에서 이 모델들을 import해야 오류가 사라집니다.)