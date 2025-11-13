import os
import psycopg2
from dotenv import load_dotenv
import json
from typing import List, Dict, Any

# .env 파일에서 환경 변수 로드
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

# JSON 파일 경로
DATA_DIR = "data"
CUSTOMERS_FILE_PATH = os.path.join(DATA_DIR, "customers.json")
ORDERS_FILE_PATH = os.path.join(DATA_DIR, "orders.json")
PRODUCTS_FILE_PATH = os.path.join(DATA_DIR, "products.json")
QNAS_FILE_PATH = os.path.join(DATA_DIR, "qnas.json")
REVIEWS_FILE_PATH = os.path.join(DATA_DIR, "reviews.json")
SETTLEMENT_FILE_PATH = os.path.join(DATA_DIR, "settlement.json") # 추가

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

def load_json_data(file_path: str) -> List[Dict[str, Any]]:
    """JSON 파일을 로드하여 데이터를 반환합니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ 오류: {file_path} 파일을 찾을 수 없습니다. 데이터 파일을 확인하세요.")
        return []
    except json.JSONDecodeError:
        print(f"⚠️ 오류: {file_path} JSON 형식이 올바르지 않습니다.")
        return []

def seed_database():
    """Cloud SQL 데이터베이스에 테이블을 생성하고 로컬 JSON 데이터로 채웁니다."""
    
    conn = get_db_connection()
    if conn is None:
        print("DB 연결 실패로 시딩을 중단합니다.")
        return

    # 1. 테이블 생성
    CREATE_TABLE_QUERIES = [
        """
        DROP TABLE IF EXISTS customers CASCADE;
        CREATE TABLE IF NOT EXISTS customers (
            customer_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(50),
            segment VARCHAR(50),
            total_spend INT,
            total_orders INT,
            last_order_date DATE,
            main_category VARCHAR(50),
            avg_rating NUMERIC(3, 2),
            total_claims INT
        );
        """,
        """
        DROP TABLE IF EXISTS products CASCADE;
        CREATE TABLE IF NOT EXISTS products (
            origin_product_no INT PRIMARY KEY,
            product_name VARCHAR(255),
            category_name VARCHAR(100),
            sale_price INT,
            cost_price INT, -- 추가
            stock_quantity INT,
            status VARCHAR(50)
        );
        """,
        """
        DROP TABLE IF EXISTS orders CASCADE;
        CREATE TABLE IF NOT EXISTS orders (
            product_order_id VARCHAR(50) PRIMARY KEY,
            order_id VARCHAR(50),
            origin_product_no INT,
            product_name VARCHAR(255),
            quantity INT,
            total_amount INT,
            customer_id VARCHAR(50),
            order_status VARCHAR(50),
            payment_date TIMESTAMP,
            delivery_complete_date TIMESTAMP,
            claim_type VARCHAR(50),
            claim_reason VARCHAR(50)
        );
        """,
        """
        DROP TABLE IF EXISTS qnas CASCADE;
        CREATE TABLE IF NOT EXISTS qnas (
            question_id VARCHAR(50) PRIMARY KEY,
            origin_product_no INT,
            customer_id VARCHAR(50),
            question_type VARCHAR(50),
            question_text TEXT,
            is_answered BOOLEAN,
            answer_text TEXT
        );
        """,
        """
        DROP TABLE IF EXISTS reviews CASCADE;
        CREATE TABLE IF NOT EXISTS reviews (
            review_id VARCHAR(50) PRIMARY KEY,
            customer_id VARCHAR(50),
            product_id INT,
            rating INT,
            review_text TEXT,
            created_at TIMESTAMP
        );
        """,
        """
        DROP TABLE IF EXISTS settlement CASCADE;
        CREATE TABLE IF NOT EXISTS settlement (
            settle_date DATE PRIMARY KEY,
            total_payment_amount INT,
            total_commission INT,
            total_settlement_amount INT
        );
        """
    ]

    try:
        with conn.cursor() as cur:
            print("--- 테이블 생성 시작 ---")
            for query in CREATE_TABLE_QUERIES:
                cur.execute(query)
            print("✅ 테이블 생성이 완료되었습니다.")
        conn.commit()
    except Exception as e:
        print(f"⚠️ 테이블 생성 중 오류 발생: {e}")
        conn.rollback()
        conn.close()
        return

    # 2. 데이터 로드 및 삽입
    data_to_load = {
        "customers": (CUSTOMERS_FILE_PATH, "customers"),
        "products": (PRODUCTS_FILE_PATH, "products"),
        "orders": (ORDERS_FILE_PATH, "orders"),
        "qnas": (QNAS_FILE_PATH, "qnas"),
        "reviews": (REVIEWS_FILE_PATH, "reviews"),
        "settlement": (SETTLEMENT_FILE_PATH, "settlement") # 추가
    }
    
    all_data = {key: load_json_data(path) for key, (path, _) in data_to_load.items()}

    try:
        with conn.cursor() as cur:
            print("--- 데이터 삽입 시작 ---")
            
            # 기존 데이터 삭제 (멱등성을 위해)
            for _, table_name in data_to_load.values():
                cur.execute(f"TRUNCATE {table_name} RESTART IDENTITY CASCADE;")

            # 데이터 삽입
            for item in all_data["customers"]:
                cur.execute("INSERT INTO customers VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (item['customerId'], item['name'], item['segment'], item['totalSpend'], item['totalOrders'], item.get('lastOrderDate'), item['mainCategory'], item.get('avgRating'), item['totalClaims']))

            for item in all_data["products"]:
                cur.execute("INSERT INTO products VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (item['originProductNo'], item['productName'], item['category']['categoryName'], item['price']['salePrice'], item['price']['costPrice'], item['stockQuantity'], item['status'])) # cost_price 추가

            for item in all_data["orders"]:
                cur.execute("INSERT INTO orders VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (item['productOrderId'], item['orderId'], item['productInfo']['originProductNo'], item['productInfo']['productName'], item['productInfo']['quantity'], item['productInfo']['totalAmount'], item['orderer']['id'], item['orderStatus'], item.get('paymentDate'), item.get('deliveryCompleteDate'), (item.get('claimData') or {}).get('claimType'), (item.get('claimData') or {}).get('reason')))

            for item in all_data["qnas"]:
                cur.execute("INSERT INTO qnas VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (item['questionId'], item.get('originProductNo'), item['customerId'], item['questionType'], item['questionText'], item['isAnswered'], (item.get('answer') or {}).get('answerText')))

            for item in all_data["reviews"]:
                cur.execute("INSERT INTO reviews VALUES (%s, %s, %s, %s, %s, %s)",
                            (item['review_id'], item['customer_id'], item['product_id'], item['rating'], item['review_text'], item['created_at']))

            for item in all_data["settlement"]: # 추가
                cur.execute("INSERT INTO settlement VALUES (%s, %s, %s, %s)",
                            (item['settleDate'], item['totalPaymentAmount'], item['totalCommission'], item['totalSettlementAmount']))

            print("✅ 모든 데이터가 성공적으로 삽입되었습니다.")
        conn.commit()
    except Exception as e:
        print(f"⚠️ 데이터 삽입 중 오류 발생: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    seed_database()
