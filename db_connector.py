import os
import psycopg2
from dotenv import load_dotenv
import json
from typing import List, Dict, Any
from rag_connector import RAGConnector
from models import FailureLog

# 환경 변수 로드
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

# JSON 파일 경로 (cs_manuals만 로컬에서 로드)
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

def get_customers_from_db() -> List[Dict[str, Any]]:
    """DB에서 고객 데이터를 조회합니다."""
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT customer_id, name, segment, total_spend, total_orders, last_order_date, main_category, avg_rating, total_claims FROM customers")
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except Exception as e:
        print(f"⚠️ 고객 데이터 조회 중 오류 발생: {e}")
        return []
    finally:
        conn.close()

def get_products_from_db() -> List[Dict[str, Any]]:
    """DB에서 상품 데이터를 조회합니다."""
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT origin_product_no, product_name, category_name, sale_price, cost_price, stock_quantity, status FROM products")
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except Exception as e:
        print(f"⚠️ 상품 데이터 조회 중 오류 발생: {e}")
        return []
    finally:
        conn.close()

def get_orders_from_db() -> List[Dict[str, Any]]:
    """DB에서 주문 데이터를 조회합니다."""
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT product_order_id, order_id, origin_product_no, product_name, quantity, total_amount, customer_id, order_status, payment_date, delivery_complete_date, claim_type, claim_reason FROM orders")
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except Exception as e:
        print(f"⚠️ 주문 데이터 조회 중 오류 발생: {e}")
        return []
    finally:
        conn.close()

def get_qnas_from_db() -> List[Dict[str, Any]]:
    """DB에서 Q&A 데이터를 조회합니다."""
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT question_id, origin_product_no, customer_id, question_type, question_text, is_answered, answer_text FROM qnas")
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except Exception as e:
        print(f"⚠️ Q&A 데이터 조회 중 오류 발생: {e}")
        return []
    finally:
        conn.close()

def get_reviews_from_db() -> List[Dict[str, Any]]:
    """DB에서 리뷰 데이터를 조회합니다."""
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT review_id, customer_id, product_id, rating, review_text, created_at FROM reviews")
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except Exception as e:
        print(f"⚠️ 리뷰 데이터 조회 중 오류 발생: {e}")
        return []
    finally:
        conn.close()

from datetime import datetime, timedelta

def calculate_product_margins(period_days: int = 7) -> List[Dict[str, Any]]:
    """
    지정된 기간 동안 상품별 총 판매액, 총 마진, 마진율을 계산합니다.
    :param period_days: 계산할 기간(일 수)
    :return: 상품별 마진 정보 리스트
    """
    conn = get_db_connection()
    if not conn: return []

    try:
        with conn.cursor() as cur:
            # 기간 필터링을 위한 기준 날짜 계산
            cutoff_date = datetime.now() - timedelta(days=period_days)

            # 상품 정보 (원가 포함)와 주문 정보를 조인하여 마진 계산
            cur.execute(
                """
                SELECT
                    p.origin_product_no,
                    p.product_name,
                    p.cost_price,
                    o.quantity,
                    o.total_amount,
                    o.payment_date
                FROM
                    products p
                JOIN
                    orders o ON p.origin_product_no = o.origin_product_no
                WHERE
                    o.payment_date >= %s
                """,
                (cutoff_date,)
            )
            
            results = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            
            product_sales_data = {}
            for row in results:
                item = dict(zip(columns, row))
                product_no = item['origin_product_no']
                
                if product_no not in product_sales_data:
                    product_sales_data[product_no] = {
                        'origin_product_no': product_no,
                        'product_name': item['product_name'],
                        'total_sales_amount': 0,
                        'total_cost_amount': 0,
                        'total_margin': 0,
                        'total_quantity_sold': 0
                    }
                
                product_sales_data[product_no]['total_sales_amount'] += item['total_amount']
                product_sales_data[product_no]['total_cost_amount'] += item['cost_price'] * item['quantity']
                product_sales_data[product_no]['total_quantity_sold'] += item['quantity']
            
            final_margins = []
            for product_no, data in product_sales_data.items():
                data['total_margin'] = data['total_sales_amount'] - data['total_cost_amount']
                data['margin_percentage'] = (data['total_margin'] / data['total_sales_amount'] * 100) if data['total_sales_amount'] > 0 else 0
                final_margins.append(data)
            
            # 마진이 높은 순서대로 정렬
            final_margins.sort(key=lambda x: x['total_margin'], reverse=True)
            
            return final_margins

    except Exception as e:
        print(f"⚠️ 상품 마진 계산 중 오류 발생: {e}")
        return []
    finally:
        conn.close()

def get_customers_by_segment(segment: str) -> List[Dict[str, Any]]:
    """
    특정 세그먼트에 속하는 고객 목록을 조회합니다.
    :param segment: 조회할 고객 세그먼트 (예: 'VIP', '이탈 위험 고객')
    :return: 해당 세그먼트의 고객 목록
    """
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT customer_id, name, segment, total_spend, total_orders, last_order_date, main_category, avg_rating, total_claims FROM customers WHERE segment = %s",
                (segment,)
            )
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except Exception as e:
        print(f"⚠️ 고객 세그먼트 조회 중 오류 발생: {e}")
        return []
    finally:
        conn.close()

def get_settlement_data_from_db() -> List[Dict[str, Any]]:
    """DB에서 정산 데이터를 조회합니다."""
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT settle_date, total_payment_amount, total_commission, total_settlement_amount FROM settlement ORDER BY settle_date ASC")
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except Exception as e:
        print(f"⚠️ 정산 데이터 조회 중 오류 발생: {e}")
        return []
    finally:
        conn.close()

def get_unanswered_qnas_count() -> int:
    """미답변 문의 수를 조회합니다."""
    conn = get_db_connection()
    if not conn: return 0
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM qnas WHERE is_answered = FALSE")
            return cur.fetchone()[0]
    except Exception as e:
        print(f"⚠️ 미답변 문의 수 조회 중 오류 발생: {e}")
        return 0
    finally:
        conn.close()

def get_pending_claims_count() -> int:
    """처리 대기 중인 클레임 수를 조회합니다."""
    conn = get_db_connection()
    if not conn: return 0
    try:
        with conn.cursor() as cur:
            # claim_type이 null이 아니고, order_status가 'RETURN' 또는 'EXCHANGE'인 경우를 처리 대기로 간주
            # 또는 claimData가 있으나 status가 'APPROVED'가 아닌 건수
            cur.execute("SELECT COUNT(*) FROM orders WHERE claim_type IS NOT NULL AND (order_status = 'RETURN' OR order_status = 'EXCHANGE')")
            return cur.fetchone()[0]
    except Exception as e:
        print(f"⚠️ 처리 대기 클레임 수 조회 중 오류 발생: {e}")
        return 0
    finally:
        conn.close()

def get_low_stock_products_count(threshold: int = 50) -> int:
    """재고 위험 상품 수를 조회합니다."""
    conn = get_db_connection()
    if not conn: return 0
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM products WHERE stock_quantity < %s", (threshold,))
            return cur.fetchone()[0]
    except Exception as e:
        print(f"⚠️ 재고 위험 상품 수 조회 중 오류 발생: {e}")
        return 0
    finally:
        conn.close()

def get_low_stock_products(threshold: int = 50) -> List[Dict[str, Any]]:
    """재고 위험 상품 목록을 조회합니다."""
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT origin_product_no, product_name, stock_quantity FROM products WHERE stock_quantity < %s", (threshold,))
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except Exception as e:
        print(f"⚠️ 재고 위험 상품 목록 조회 중 오류 발생: {e}")
        return []
    finally:
        conn.close()

def get_recent_negative_reviews(hours: int = 24, rating_threshold: int = 2) -> List[Dict[str, Any]]:
    """최근 부정적인 리뷰 목록을 조회합니다."""
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            # created_at이 TIMESTAMP WITH TIME ZONE 타입일 경우, 타임존 고려
            cur.execute(
                "SELECT review_id, product_id, review_text, rating, created_at FROM reviews WHERE created_at >= NOW() - INTERVAL '%s hours' AND rating <= %s",
                (hours, rating_threshold)
            )
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except Exception as e:
        print(f"⚠️ 최근 부정적인 리뷰 조회 중 오류 발생: {e}")
        return []
    finally:
        conn.close()

def initialize_db_and_data():
    """DB 테이블 생성 및 CS 매뉴얼 데이터를 로드하고 반환합니다."""
    
    # 1. PostgreSQL 테이블 생성 (inquiry_logs와 cs_manuals만 여기서 생성)
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

    # 2. CS 매뉴얼 데이터 로드 및 DB 삽입 (로컬 JSON에서)
    manuals = load_manuals_from_json()
    if not manuals:
        return []
    
    conn = get_db_connection()
    if conn:
        print("--- PostgreSQL에 CS 매뉴얼 메타데이터 저장 시작 ---")
        try:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE cs_manuals RESTART IDENTITY;")
                
                for item in manuals:
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
            
    # 3. ChromaDB (벡터 콘텐츠) 로드 (CS 매뉴얼만 여기서 로드)
    rag_connector = RAGConnector()
    try:
        rag_connector.add_manuals(manuals)
        print("✅ ChromaDB: CS 매뉴얼 RAG 콘텐츠 로드 및 벡터화 완료.")

        # 제품, Q&A, 리뷰 데이터 벡터화
        rag_connector.add_products(get_products_from_db())
        print("✅ ChromaDB: 제품 정보 RAG 콘텐츠 로드 및 벡터화 완료.")
        
        rag_connector.add_qnas(get_qnas_from_db())
        print("✅ ChromaDB: Q&A RAG 콘텐츠 로드 및 벡터화 완료.")
        
        rag_connector.add_reviews(get_reviews_from_db())
        print("✅ ChromaDB: 리뷰 RAG 콘텐츠 로드 및 벡터화 완료.")

    except Exception as e:
        print(f"⚠️ ChromaDB 저장 오류: {e}")
        
    return manuals

def save_inquiry_log(log_id: str, customer_id: str, input_text: str, ai_action_failed: str) -> None:
    """새로운 문의 로그를 DB에 저장합니다."""
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO inquiry_logs (log_id, customer_id, input_text, ai_action_failed)
                VALUES (%s, %s, %s, %s)
                """,
                (log_id, customer_id, input_text, ai_action_failed)
            )
        conn.commit()
    except Exception as e:
        print(f"⚠️ 문의 로그 저장 중 오류 발생: {e}")
        conn.rollback()
    finally:
        conn.close()

def update_inquiry_log_feedback(log_id: str, feedback: str, final_resolution: str = None) -> None:
    """문의 로그에 사용자의 피드백을 업데이트합니다."""
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE inquiry_logs
                SET resolution_feedback = %s, final_resolution = %s, is_learned = TRUE
                WHERE log_id = %s
                """,
                (feedback, final_resolution, log_id)
            )
        conn.commit()
    except Exception as e:
        print(f"⚠️ 피드백 업데이트 중 오류 발생: {e}")
        conn.rollback()
    finally:
        conn.close()

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