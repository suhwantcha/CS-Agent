# 🚀 AI 기반 CS 및 리뷰 관리 에이전트 (Self-Evolving CS & Review Management Agent)

> **Note:** 이 프로젝트는 현재 활발하게 개발 및 개선이 진행 중인 프로젝트입니다.

이 프로젝트는 멀티모달(Multimodal) 기능을 갖춘 AI 기반 CS(고객 서비스) 및 리뷰 관리 에이전트입니다. 고객 문의에 대한 자동 응답, 리뷰 분석 및 관리, 그리고 AI 스스로 과거의 실패로부터 학습하여 성능을 개선하는 '자기 진화' 기능을 제공합니다.

## ✨ 주요 기능

-   **멀티모달 CS 처리:** 고객이 이미지(예: 파손 상품 사진)를 첨부하여 문의할 경우, 이미지를 분석하여 더 정확하고 맥락에 맞는 답변을 제공합니다.
-   **RAG (Retrieval-Augmented Generation) 기반 답변:** CS 매뉴얼 데이터를 기반으로 고객 문의에 대한 관련성 높은 정보를 검색하고, 이를 바탕으로 LLM이 답변을 생성하여 정확도를 높입니다.
-   **실시간 자기 진화:** AI 에이전트가 과거의 실패 피드백(잘못된 답변)을 학습하여, 동일한 고객의 유사한 문의에 대해 같은 실수를 반복하지 않도록 스스로 행동을 교정합니다.
-   **리뷰 분석 및 관리:** (향후 확장 예정) 고객 리뷰(텍스트 + 이미지)를 분석하여 주제별 분류, 긴급 이슈 식별, 답변 초안 자동 생성 등의 기능을 제공합니다.
-   **비용 효율적인 LLM 사용:** 문의의 복잡도에 따라 GPT-3.5-turbo (저비용) 또는 GPT-4o (고비용) 모델을 동적으로 선택하여 운영 비용을 최적화합니다.

## 🛠️ 기술 스택

-   **백엔드 프레임워크:** FastAPI
-   **데이터베이스:** PostgreSQL (Google Cloud SQL 연동)
-   **벡터 데이터베이스:** ChromaDB
-   **LLM:** OpenAI GPT-4o, GPT-3.5-turbo
-   **임베딩 모델:** OpenAI `text-embedding-3-small`
-   **환경 관리:** `python-dotenv`
-   **데이터 처리:** `psycopg2`, `pydantic`

## 🚀 시작하기

### 📋 전제 조건

-   Python 3.9+
-   Google Cloud Platform (GCP) 계정 및 Cloud SQL for PostgreSQL 인스턴스
-   OpenAI API Key

### ⚙️ 설치

1.  **저장소 클론:**
    ```bash
    git clone https://github.com/suhwantcha/CS-Agent.git
    cd CS-Agent
    ```

2.  **가상 환경 설정 및 활성화:**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **의존성 설치:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **.env 파일 설정:**
    프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가합니다. `YOUR_PROJECT_ID`, `YOUR_REGION`, `YOUR_INSTANCE_NAME`, `YOUR_DB_PASSWORD`, `YOUR_OPENAI_API_KEY`는 실제 값으로 대체해야 합니다.

    ```dotenv
    DB_HOST=127.0.0.1
    DB_PORT=5433 # Cloud SQL Auth Proxy 사용 시
    DB_NAME=postgres
    DB_USER=postgres
    DB_PASSWORD=YOUR_DB_PASSWORD

    OPENAI_API_KEY=YOUR_OPENAI_API_KEY
    ```

5.  **Google Cloud SQL 인증 프록시 설정:**
    *   Google Cloud SQL 인증 프록시를 다운로드합니다: [Cloud SQL Auth Proxy 다운로드](https://cloud.google.com/sql/docs/postgres/connect-external-app#gcloud-sql-proxy)
    *   다운로드한 `cloud_sql_proxy.exe` (Windows) 또는 `cloud_sql_proxy` (macOS/Linux) 파일을 적절한 위치에 둡니다. (예: `C:\Users\mim30\Downloads` 또는 프로젝트 루트)

### ▶️ 애플리케이션 실행

1.  **Cloud SQL 인증 프록시 실행 (별도 터미널):**
    `YOUR_PROJECT_ID`, `YOUR_REGION`, `YOUR_INSTANCE_NAME`을 실제 값으로 대체하여 실행합니다. (예: `gen-lang-client-0179787481`, `us-central1`, `cs-agent-instance`)

    ```bash
    # Windows (예시: 다운로드 폴더에 있을 경우)
    C:\Users\mim30\Downloads\cloud_sql_proxy.exe -instances=YOUR_PROJECT_ID:YOUR_REGION:YOUR_INSTANCE_NAME=tcp:5433

    # macOS/Linux (예시: 현재 디렉토리에 있을 경우)
    ./cloud_sql_proxy -instances=YOUR_PROJECT_ID:YOUR_REGION:YOUR_INSTANCE_NAME=tcp:5433
    ```
    프록시가 "Ready for new connections!" 메시지를 출력하면 성공입니다.

2.  **FastAPI 서버 실행 (다른 터미널):**
    ```bash
    uvicorn main:app --host 127.0.0.1 --port 8000 --reload
    ```
    서버가 시작되면 `http://127.0.0.1:8000`에서 API 문서 (`/docs`)를 확인할 수 있습니다.

## 🧪 자기 진화 기능 테스트

AI 에이전트의 자기 진화 기능은 다음과 같이 테스트할 수 있습니다.

1.  **첫 번째 문의:** `/api/query` 엔드포인트로 고객 문의를 보냅니다.
    *   `customer_id`: `TEST_USER_1` (임의의 ID)
    *   `customer_query`: "배송이 너무 늦어요. 언제 오나요?"
    *   응답으로 받은 `log_id`를 기록해 둡니다.

2.  **"실패" 피드백 전송:** `/api/feedback` 엔드포인트로 피드백을 보냅니다.
    *   `log_id`: 1단계에서 기록한 `log_id`
    *   `resolution_feedback`: `failure`
    *   `final_resolution`: "고객님, 배송 지연으로 불편을 드려 죄송합니다. 현재 주문하신 상품은 2일 이내에 도착할 예정입니다." (AI가 학습할 올바른 답변)

3.  **동일한 문의 재전송:** `/api/query` 엔드포인트로 1단계와 **동일한 `customer_id`와 `customer_query`**로 다시 문의를 보냅니다.

4.  **로그 확인:** `uvicorn` 서버 터미널에서 `-> ⚙️ 자기진화: N개의 실패 기록을 발견하여 프롬프트에 반영합니다.` 와 같은 메시지가 출력되는지 확인합니다.

5.  **AI 답변 확인:** 두 번째 문의에 대한 AI의 답변이 첫 번째 답변보다 `final_resolution`에 가깝게 개선되었는지 확인합니다.

## 📁 프로젝트 구조

```
.
├── config.py                 # 설정 파일 (ChromaDB 경로 등)
├── db_connector.py           # PostgreSQL 데이터베이스 연결 및 데이터 처리 로직
├── evolution_agent.py        # 오프라인/배치 학습을 위한 에이전트 (실패 로그 기반 지식 생성)
├── llm_agent.py              # LLM과의 상호작용, RAG 검색, 자기 진화 로직 포함
├── main.py                   # FastAPI 애플리케이션 메인 파일, API 엔드포인트 정의
├── models.py                 # Pydantic 데이터 모델 정의 (FailureLog, ToolCall 등)
├── rag_connector.py          # RAG (ChromaDB) 연결 및 임베딩, 컨텍스트 검색 로직
├── requirements.txt          # Python 의존성 목록
├── review_analyzer.py        # 리뷰 분석 로직 (향후 확장 예정)
├── .env                      # 환경 변수 (DB 접속 정보, API 키 등)
├── data/
│   └── cs_manuals.json       # CS 매뉴얼 데이터 (RAG 지식 베이스)
└── chroma_data/              # ChromaDB 데이터 저장 폴더
```
