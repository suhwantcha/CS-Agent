import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# .env 파일에서 DB 정보를 가져옵니다.
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

def get_db_connection():
    """데이터베이스 연결 객체를 반환합니다."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        return conn
    except psycopg2.Error as e:
        print(f"PostgreSQL 연결 실패: {e}")
        return None

def initialize_db_tables():
    """필수 테이블 (CS 매뉴얼, 로그)을 생성합니다."""
    conn = get_db_connection()
    if conn is None:
        return

    # SQL 쿼리: AI 실패 로그를 저장할 테이블 (PostgreSQL의 핵심 역할)
    # 이 테이블에 AI의 잘못된 행동과 피드백을 기록하여 진화의 기반을 만듭니다.
    CREATE_INQUIRY_LOGS_TABLE = """
    CREATE TABLE IF NOT EXISTS inquiry_logs (
        log_id UUID PRIMARY KEY,
        customer_id VARCHAR(50),
        input_text TEXT,
        ai_action_failed TEXT,
        resolution_feedback VARCHAR(10),
        final_resolution TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """
    
    # CS 매뉴얼의 메타데이터를 저장할 테이블
    CREATE_MANUALS_TABLE = """
    CREATE TABLE IF NOT EXISTS cs_manuals (
        manual_id VARCHAR(20) PRIMARY KEY,
        domain VARCHAR(50),
        difficulty VARCHAR(10),
        urgency VARCHAR(10)
    );
    """

    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_INQUIRY_LOGS_TABLE)
            cur.execute(CREATE_MANUALS_TABLE)
        conn.commit()
        print("✅ DB: 필수 테이블 생성이 완료되었습니다.")
    except Exception as e:
        print(f"⚠️ DB: 테이블 생성 중 오류 발생: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    # 이 파일만 실행하여 DB 연결 및 테이블 생성을 테스트합니다.
    initialize_db_tables()