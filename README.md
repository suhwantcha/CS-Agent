# 🚀 AI 기반 CS 및 리뷰 관리 에이전트 (Self-Evolving CS & Review Management Agent)

> **Note:** 이 프로젝트는 현재 활발하게 개발 및 개선이 진행 중인 프로젝트입니다.

이 프로젝트는 멀티모달(Multimodal) 기능을 갖춘 AI 기반 CS(고객 서비스) 및 리뷰 관리 에이전트입니다. 고객 문의에 대한 자동 응답, 리뷰 분석 및 관리, 그리고 AI 스스로 과거의 실패로부터 학습하여 성능을 개선하는 '자기 진화' 기능을 제공합니다.

## ✨ 주요 기능

-   **웹 기반 채팅 UI:** React와 MUI로 구축된 직관적인 채팅 인터페이스를 통해 AI 에이전트와 상호작용할 수 있습니다.
-   **멀티모달 CS 처리:** 고객이 이미지(예: 파손 상품 사진)를 첨부하여 문의할 경우, 이미지를 분석하여 더 정확하고 맥락에 맞는 답변을 제공합니다.
-   **RAG (Retrieval-Augmented Generation) 기반 답변:** CS 매뉴얼 데이터를 기반으로 고객 문의에 대한 관련성 높은 정보를 검색하고, 이를 바탕으로 LLM이 답변을 생성하여 정확도를 높입니다.
-   **실시간 자기 진화:** AI 에이전트가 과거의 실패 피드백(잘못된 답변)을 학습하여, 동일한 고객의 유사한 문의에 대해 같은 실수를 반복하지 않도록 스스로 행동을 교정합니다.
-   **비용 효율적인 LLM 사용:** 문의의 복잡도에 따라 GPT-3.5-turbo (저비용) 또는 GPT-4o (고비용) 모델을 동적으로 선택하여 운영 비용을 최적화합니다.

## 🛠️ 기술 스택

-   **백엔드:** FastAPI, Python
-   **프론트엔드:** React, Vite, MUI (Material-UI), Axios
-   **데이터베이스:** PostgreSQL (Google Cloud SQL 연동)
-   **벡터 데이터베이스:** ChromaDB
-   **LLM:** OpenAI GPT-4o, GPT-3.5-turbo
-   **임베딩 모델:** OpenAI `text-embedding-3-small`

## 🚀 시작하기

### 📋 전제 조건

-   Python 3.9+
-   Node.js 18+
-   Google Cloud Platform (GCP) 계정 및 Cloud SQL for PostgreSQL 인스턴스
-   OpenAI API Key

### ⚙️ 설치

1.  **저장소 클론:**
    ```bash
    git clone https://github.com/suhwantcha/CS-Agent.git
    cd CS-Agent
    ```

2.  **백엔드 설정:**
    ```bash
    # 가상 환경 생성 및 활성화
    python -m venv venv
    # Windows: .\venv\Scripts\activate | macOS/Linux: source venv/bin/activate

    # 의존성 설치
    pip install -r requirements.txt
    ```

3.  **프론트엔드 설정:**
    ```bash
    # frontend 디렉토리로 이동
    cd frontend

    # 의존성 설치
    npm install
    ```

4.  **.env 파일 설정:**
    프로젝트 루트(`CS-Agent/`)에 `.env` 파일을 생성하고 다음 내용을 추가합니다. `YOUR_DB_PASSWORD`, `YOUR_OPENAI_API_KEY`는 실제 값으로 대체해야 합니다.

    ```dotenv
    DB_HOST=127.0.0.1
    DB_PORT=5433 # Cloud SQL Auth Proxy 포트와 일치
    DB_NAME=postgres
    DB_USER=postgres
    DB_PASSWORD=YOUR_DB_PASSWORD

    OPENAI_API_KEY=YOUR_OPENAI_API_KEY
    ```

### ▶️ 애플리케이션 실행

애플리케이션을 실행하려면 **3개의 터미널**이 필요합니다.

1.  **터미널 1: Cloud SQL 인증 프록시 실행**
    *   Google Cloud SQL 인증 프록시를 다운로드합니다: [Cloud SQL Auth Proxy 다운로드](https://cloud.google.com/sql/docs/postgres/connect-external-app#gcloud-sql-proxy)
    *   `YOUR_PROJECT_ID`, `YOUR_REGION`, `YOUR_INSTANCE_NAME`을 실제 값으로 대체하여 실행합니다.
    ```bash
    # 예시: C:\path\to\cloud_sql_proxy.exe -instances=YOUR_PROJECT_ID:YOUR_REGION:YOUR_INSTANCE_NAME=tcp:5433
    ```
    > "Ready for new connections!" 메시지가 출력되면 성공입니다.

2.  **터미널 2: 백엔드 서버 실행**
    *   프로젝트 루트(`CS-Agent/`)에서 실행합니다.
    ```bash
    uvicorn main:app --host 127.0.0.1 --port 8000 --reload
    ```

3.  **터미널 3: 프론트엔드 서버 실행**
    *   `frontend` 디렉터리에서 실행합니다.
    ```bash
    cd frontend
    npm run dev
    ```

4.  **브라우저에서 확인:**
    *   프론트엔드 서버가 실행되면 터미널에 표시되는 주소(보통 `http://localhost:5173`)를 웹 브라우저에서 열어주세요.

## 🧪 자기 진화 기능 테스트

웹 UI의 채팅창에서 다음 과정을 통해 자기 진화 기능을 테스트할 수 있습니다.

1.  **첫 번째 문의:** "배송이 너무 늦어요. 언제 오나요?" 라고 질문합니다.
    *   AI의 답변과 함께 나타난 `log_id`를 확인합니다. (실제 UI에서는 보이지 않지만, 백엔드에서 관리됨)

2.  **"실패" 피드백 전송:** AI 답변 메시지 아래의 **싫어요(👎)** 아이콘을 클릭합니다.
    *   나타나는 `prompt` 창에 올바른 답변(예: "고객님, 배송 지연으로 불편을 드려 죄송합니다. 현재 주문하신 상품은 2일 이내에 도착할 예정입니다.")을 입력하고 확인을 누릅니다.

3.  **동일한 문의 재전송:** 다시 "배송이 너무 늦어요. 언제 오나요?" 라고 질문합니다.

4.  **로그 확인:** 백엔드 서버(터미널 2) 로그에서 `-> ⚙️ 자기진화: ...` 메시지가 출력되는지 확인합니다.

5.  **AI 답변 확인:** 두 번째 답변이 피드백으로 제공한 내용에 더 가깝게 개선되었는지 확인합니다.

## 📁 프로젝트 구조

```
.
├── frontend/                 # React 프론트엔드 소스 코드
├── data/
│   └── cs_manuals.json       # CS 매뉴얼 데이터 (RAG 지식 베이스)
├── chroma_data/              # ChromaDB 데이터 저장 폴더
├── config.py                 # 설정 파일
├── db_connector.py           # DB 연결 및 데이터 처리 로직
├── evolution_agent.py        # 오프라인 학습 에이전트
├── llm_agent.py              # LLM 상호작용 및 자기 진화 로직
├── main.py                   # FastAPI 애플리케이션 메인
├── models.py                 # Pydantic 데이터 모델
├── rag_connector.py          # RAG (ChromaDB) 연결 로직
├── requirements.txt          # Python 의존성 목록
├── README.md                 # 프로젝트 문서
└── .env                      # 환경 변수 파일
```
