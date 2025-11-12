import os
import psycopg2
from dotenv import load_dotenv
import json
from typing import List
from rag_connector import RAGConnector
from models import FailureLog

# 환경 변수 로드
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

# JSON 파일 경로 (프로젝트 최상단 폴더에 'data' 폴더가 있다고 가정)
MANUALS_FILE_PATH = "data/cs_manuals.json"

def get_db_connection():
    """PostgreSQL 연결 객체를 반환합니다."""
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

def load_manuals_from_json():
    """CS 매뉴얼 JSON 파일을 로드합니다."""
    try:
        with open(MANUALS_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ 오류: {MANUALS_FILE_PATH} 파일을 찾을 수 없습니다. 데이터 파일을 확인하세요.")
        return []
    except json.JSONDecodeError:
        print(f"⚠️ 오류: {MANUALS_FILE_PATH} JSON 형식이 올바르지 않습니다.")
        return []

def initialize_db_and_data():
    """DB 테이블 생성 및 모든 CS 매뉴얼 데이터를 로드하고 반환합니다."""
    
    # 1. PostgreSQL 테이블 생성
    conn = get_db_connection()
    if conn is None: return

    CREATE_INQUIRY_LOGS_TABLE = """
    CREATE TABLE IF NOT EXISTS inquiry_logs (
        log_id UUID PRIMARY KEY,
        customer_id VARCHAR(50),
        input_text TEXT,
        ai_action_failed TEXT,
        resolution_feedback VARCHAR(10),
        final_resolution TEXT,
        created_at TIMESTAMP DEFAULT NOW(),
        is_learned BOOLEAN DEFAULT FALSE
    );
    """
    
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

    # 2. CS 매뉴얼 데이터 로드 및 DB 삽입
    manuals = load_manuals_from_json()
    if not manuals:
        return []
    
    # 2-1. PostgreSQL (메타데이터) 로드
    conn = get_db_connection()
    if conn:
        print("--- PostgreSQL에 CS 매뉴얼 메타데이터 저장 시작 ---")
        try:
            with conn.cursor() as cur:
                # 데이터를 중복 없이 새로 삽입하기 위해 기존 데이터를 삭제 (테스트 환경)
                cur.execute("TRUNCATE cs_manuals RESTART IDENTITY;")
                
                for item in manuals:
                    # JSON에서 메타데이터 필드를 추출하여 PostgreSQL에 맞게 저장
                    cur.execute(
                        "INSERT INTO cs_manuals (manual_id, domain, difficulty, urgency) VALUES (%s, %s, %s, %s)",
                        (item['manual_id'], item['domain'], item['difficulty'], item['urgency'])
                    )
            conn.commit()
            print(f"✅ PGDB: {len(manuals)}개의 매뉴얼 메타데이터 저장 완료.")
        except Exception as e:
            print(f"⚠️ PGDB 저장 오류: {e}")
            conn.rollback()
        finally:
            conn.close()
            
    # 2-2. ChromaDB (벡터 콘텐츠) 로드
    rag_connector = RAGConnector()
    try:
        rag_connector.add_manuals(manuals)
        print("✅ ChromaDB: RAG 콘텐츠 로드 및 벡터화 완료.")
    except Exception as e:
        print(f"⚠️ ChromaDB 저장 오류: {e}")
        
    return manuals

def get_failure_logs_by_customer(customer_id: str, limit: int = 3) -> List[FailureLog]:
    """특정 고객의 최근 실패 로그를 DB에서 조회합니다."""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT log_id, customer_id, input_text, ai_action_failed, resolution_feedback, final_resolution, created_at
                FROM inquiry_logs
                WHERE customer_id = %s AND resolution_feedback = 'failure'
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (customer_id, limit)
            )
            logs = cur.fetchall()
            
            # 결과를 FailureLog 모델 객체 리스트로 변환
            return [
                FailureLog(
                    log_id=row[0],
                    customer_id=row[1],
                    input_text=row[2],
                    ai_action_failed=row[3],
                    resolution_feedback=row[4],
                    final_resolution=row[5],
                    created_at=row[6]
                ) for row in logs
            ]
    except Exception as e:
        print(f"⚠️ 실패 로그 조회 중 오류 발생: {e}")
        return []
    finally:
        conn.close()

if __name__ == '__main__':
    initialize_db_and_data()