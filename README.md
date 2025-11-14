# 🚀 자영업자를 위한 AI 기반 CRM 매니저 (AI-Powered CRM Manager for Small Business Owners)

> **Note:** 이 프로젝트는 1인 사업자나 소규모 비즈니스 오너가 고객 서비스(CS), 리뷰 관리, 고객 관계 관리(CRM) 및 비즈니스 데이터 분석을 자동화하고 지능화하여 비즈니스 성장에 집중할 수 있도록 돕는 AI 매니저 솔루션입니다.

## 👥 두 가지 사용자 유형

이 시스템은 내부 사용자인 **관리자/CEO**와 **상담원**이라는 두 가지 역할에 따라 맞춤형 기능을 제공하여 효율적인 업무 분담을 지원합니다.

1.  **관리자/CEO (Admin/CEO):**
    -   **역할:** 비즈니스 오너 또는 총괄 관리자
    -   **주요 기능:** 전용 어드민 대시보드를 통해 비즈니스의 모든 핵심 지표(KPI), 매출 동향, 고객 세그먼트 분석 등 **전략적 의사결정에 필요한 데이터**를 한눈에 파악합니다. CRM 기능을 활용해 타겟 마케팅을 기획하고 비즈니스 리스크를 사전에 관리합니다.

2.  **상담원 (Agent):**
    -   **역할:** 고객 응대를 담당하는 실무자
    -   **주요 기능:** AI가 자동으로 처리하지 못하거나, 고객이 상담원 연결을 요청한 **복잡한 CS 문의를 전달받아 처리**합니다. 또한, AI가 생성한 부정 리뷰 답변 초안을 검토, 수정하고 최종 승인하는 등 **CS 품질 관리에 집중**합니다. AI의 답변에 피드백을 제공하여 시스템의 정확도를 높이는 역할도 수행합니다.

---

## ✨ 관리자(CEO)를 위한 주요 기능 (Admin Dashboard)

-   **AI 어드민 대시보드:**
    -   **핵심성과지표(KPI) 모니터링:** 미답변 Q&A, 처리 중인 클레임, 재고 부족 상품 수, 최신 정산 금액 등 핵심 비즈니스 지표를 실시간으로 추적합니다.
    -   **리스크 경고:** 재고 부족, 특정 상품에 대한 부정 리뷰 급증 등 잠재적인 비즈니스 리스크를 사전에 알려줍니다.
    -   **데이터 시각화:** 일별 매출 추이와 같은 중요한 데이터를 시각적인 차트로 제공하여 직관적인 이해를 돕습니다.
-   **CRM 기능:**
    -   **고객 세분화:** 전체 고객을 '충성 고객', '이탈 위험 고객' 등으로 자동 분류하여 타겟 마케팅을 지원합니다.
    -   **액션 제안:** 특정 고객 세그먼트(예: 이탈 위험 고객)에게 쿠폰을 발송하는 등 맞춤형 액션을 제안하고 실행할 수 있습니다.

## 💬 상담원을 위한 주요 기능 (Agent Tools)

-   **3단 레이아웃 기반의 효율적인 상담 환경:** Slack 또는 Intercom과 유사한 3단 레이아웃을 통해 상담원이 고객과 소통하며 필요한 모든 정보를 한눈에 파악할 수 있도록 설계되었습니다.
    -   **[왼쪽 열] 문의 대기열:** 신규, 처리 중, 완료된 문의 목록을 실시간으로 확인하고 선택하여 상담을 시작합니다.
    -   **[가운데 열] 실시간 대화창:** 고객과의 채팅이 이루어지며, AI가 답변을 제안하고 상담원은 이를 활용하거나 직접 응대할 수 있습니다. AI 답변 사용, 피드백, 파일 첨부 등의 기능을 제공합니다.
    -   **[오른쪽 열] 고객 프로필:** 선택된 고객의 기본 정보, 최근 주문 내역, 과거 클레임, 과거 리뷰, 그리고 AI가 추천하는 관련 CS 매뉴얼을 한눈에 제공합니다.
-   **AI 기반 리뷰 관리:** 부정적인 고객 리뷰를 자동으로 감지하고, AI가 생성한 답변 초안을 검토 및 승인하여 게시할 수 있습니다.
-   **지능형 CS 챗봇 및 자기 진화:** RAG 기반으로 고객 문의에 정확한 답변을 생성하며, 상담원의 피드백을 통해 AI가 스스로 학습하고 답변 품질을 개선합니다.

## 🛠️ 기술 스택

-   **백엔드:** FastAPI, Python
-   **프론트엔드:** React, Vite, Recharts, Axios
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

### ⚙️ 설치 및 실행

1.  **저장소 클론 및 이동:**
    ```bash
    git clone https://github.com/suhwantcha/CS-Agent.git
    cd your-repo
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
    cd frontend
    npm install
    cd .. 
    ```

4.  **환경 변수 설정:**
    프로젝트 루트에 `.env` 파일을 생성하고 GCP 및 OpenAI에서 발급받은 키와 설정 정보를 입력합니다.
    ```env
    DB_HOST=127.0.0.1
    DB_PORT=5433 # 로컬 Cloud SQL Auth Proxy 포트
    DB_NAME=postgres
    DB_USER=postgres
    DB_PASSWORD=YOUR_DB_PASSWORD
    OPENAI_API_KEY=YOUR_OPENAI_API_KEY
    ```

5.  **애플리케이션 실행 (3~4개의 터미널 필요):**

    -   **터미널 1: Cloud SQL 인증 프록시 실행**
        Google Cloud SDK를 사용하여 GCP와 로컬 컴퓨터를 연결합니다.
        ```bash
        # cloud_sql_proxy -instances=PROJECT_ID:REGION:INSTANCE_NAME=tcp:5433
        ```

    -   **터미널 2: 데이터베이스 시딩 (최초 1회 실행)**
        초기 데이터를 데이터베이스에 입력합니다.
        ```bash
        python seed_cloud_sql.py
        ```

    -   **터미널 3: 백엔드 서버 실행**
        ```bash
        uvicorn api:app --host 127.0.0.1 --port 8000 --reload
        ```

    -   **터미널 4: 프론트엔드 서버 실행**
        ```bash
        cd frontend
        npm run dev
        ```

6.  **접속:**
    브라우저에서 `http://localhost:5173`으로 접속하여 어드민 대시보드를 확인합니다.

### 📸 프로그램 실행 화면

<img width="300" height="150" alt="1" src="https://github.com/user-attachments/assets/b5337714-6af9-41ff-8874-929c59e882a4" />
<img width="150" height="150" alt="3" src="https://github.com/user-attachments/assets/aa8c0528-6f82-4e0d-8e0c-0eaefdf778ce" />
<img width="150" height="150" alt="4" src="https://github.com/user-attachments/assets/e469479d-0b94-4cc4-b1a1-92ca9e89f464" />
<img width="300" height="150" alt="2" src="https://github.com/user-attachments/assets/9cab787e-d7c2-42e0-bd97-f97216f1ecbc" />


## 📁 프로젝트 구조

```
.
├── frontend/                 # React 프론트엔드 (어드민 대시보드, 챗봇 UI)
│   ├── src/
│   │   ├── AdminDashboard.jsx
│   │   ├── App.jsx
│   │   ├── Chat.jsx
│   │   ├── CSAgentHub.jsx
│   │   ├── CustomerInfoPanel.jsx   # 고객 정보 패널
│   │   └── WorklistPanel.jsx       # 문의 대기열 패널
├── data/                     # 초기 데이터셋 (JSON 형식)
├── chroma_data/              # ChromaDB 벡터 데이터 저장소
|
├── api.py                    # FastAPI 메인 애플리케이션 (API 엔드포인트)
├── llm_agent.py              # LLM 상호작용 (답변 생성, 자기 진화)
├── review_analyzer.py        # 부정 리뷰 분석 및 답변 초안 생성
├── db_connector.py           # DB 연결 및 데이터 CRUD 로직
├── rag_connector.py          # RAG (ChromaDB) 연결 로직
├── seed_cloud_sql.py         # DB 테이블 생성 및 데이터 시딩
|
├── requirements.txt          # Python 의존성 목록
└── README.md                 # 프로젝트 문서
```
