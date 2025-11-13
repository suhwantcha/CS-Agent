import chromadb
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Any
import config # config 모듈 임포트

# OpenAI API 키 로드 (임베딩 모델 사용을 위함)
load_dotenv()
openai_client = OpenAI()

class RAGConnector:
    def __init__(self):
        # ChromaDB 클라이언트 초기화
        self.client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
        
        # 콜렉션 생성 또는 기존 콜렉션 가져오기
        self.collection = self.client.get_or_create_collection(
            name=config.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"✅ RAG: ChromaDB 컬렉션 '{config.COLLECTION_NAME}' 준비 완료.")

    def get_embedding(self, text: str) -> List[float]:
        """텍스트를 OpenAI 임베딩 API로 벡터화"""
        response = openai_client.embeddings.create(input=[text], model="text-embedding-3-small")
        return response.data[0].embedding

    def retrieve_context(self, query: str, n_results: int = 5) -> str:
        """쿼리를 사용하여 ChromaDB에서 관련성 높은 컨텍스트를 검색합니다."""
        try:
            query_vector = self.get_embedding(query)
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=n_results
            )
            context = "\n".join([doc for doc in results['documents'][0]])
            return context
        except Exception as e:
            print(f"⚠️ RAG 컨텍스트 검색 중 오류 발생: {e}")
            return ""

    def _add_documents(self, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]]):
        """공통 로직을 사용하여 문서를 ChromaDB에 추가"""
        if not ids:
            return
        
        embeddings = [self.get_embedding(doc) for doc in documents]
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def add_manuals(self, manuals_data: List[Dict[str, Any]]):
        """CS 매뉴얼 데이터를 ChromaDB에 저장"""
        ids = [item['manual_id'] for item in manuals_data]
        documents = [item['content_for_rag'] for item in manuals_data]
        metadatas = [
            {"doc_type": "manual", "domain": item['domain'], "urgency": item['urgency']}
            for item in manuals_data
        ]
        self._add_documents(ids, documents, metadatas)
        print(f"✅ RAG: {len(ids)}개의 CS 매뉴얼이 ChromaDB에 추가되었습니다.")

    def add_products(self, products_data: List[Dict[str, Any]]):
        """제품 데이터를 ChromaDB에 저장"""
        ids = [f"prod_{item['origin_product_no']}" for item in products_data]
        documents = [
            f"상품명: {item['product_name']}, 카테고리: {item['category_name']}"
            for item in products_data
        ]
        metadatas = [
            {"doc_type": "product", "product_no": item['origin_product_no']}
            for item in products_data
        ]
        self._add_documents(ids, documents, metadatas)
        print(f"✅ RAG: {len(ids)}개의 제품 정보가 ChromaDB에 추가되었습니다.")

    def add_qnas(self, qnas_data: List[Dict[str, Any]]):
        """Q&A 데이터를 ChromaDB에 저장"""
        ids = [item['question_id'] for item in qnas_data]
        documents = [
            f"질문: {item['question_text']}, 답변: {item.get('answer_text', '아직 답변이 없습니다.')}"
            for item in qnas_data
        ]
        metadatas = [
            {"doc_type": "qna", "product_no": item.get('origin_product_no'), "is_answered": item['is_answered']}
            for item in qnas_data
        ]
        self._add_documents(ids, documents, metadatas)
        print(f"✅ RAG: {len(ids)}개의 Q&A가 ChromaDB에 추가되었습니다.")

    def add_reviews(self, reviews_data: List[Dict[str, Any]]):
        """리뷰 데이터를 ChromaDB에 저장"""
        ids = [item['review_id'] for item in reviews_data]
        documents = [item['review_text'] for item in reviews_data]
        metadatas = [
            {"doc_type": "review", "product_id": item['product_id'], "rating": item['rating']}
            for item in reviews_data
        ]
        self._add_documents(ids, documents, metadatas)
        print(f"✅ RAG: {len(ids)}개의 리뷰가 ChromaDB에 추가되었습니다.")


if __name__ == '__main__':
    # RAGConnector 테스트
    rag_connector = RAGConnector()

    # 기존 컬렉션의 모든 데이터를 삭제하고 새로 시작 (테스트용)
    try:
        rag_connector.client.delete_collection(name=COLLECTION_NAME)
        rag_connector.collection = rag_connector.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        print("🧹 기존 컬렉션을 삭제하고 새로 시작합니다.")
    except Exception as e:
        print(f"컬렉션 삭제 중 오류 (무시 가능): {e}")

    # 더미 데이터
    dummy_manuals = [{"manual_id": "CS-DEL-002", "domain": "배송", "urgency": "medium", "content_for_rag": "배송 지연 4일 이상 시, 고객에게 지연 상황을 사과하고 보상 쿠폰을 즉시 발급한다."}]
    dummy_products = [{"origin_product_no": 1000001, "product_name": "순살 왕갈비탕 밀키트 650g", "category_name": "한식/탕류"}]
    dummy_qnas = [{"question_id": "QNA-2002", "question_text": "어제 주문했는데 오늘 출발 안했네요.", "answer_text": "고객님, 저희 오늘출발 마감은 오후 2시입니다.", "origin_product_no": 1000004, "is_answered": True}]
    dummy_reviews = [{"review_id": "REV-1002", "product_id": 1000016, "rating": 1, "review_text": "뚜껑 여니까 바로 시큼한 냄새가 나고 곰팡이가 피어있습니다."}]

    # 데이터 추가
    rag_connector.add_manuals(dummy_manuals)
    rag_connector.add_products(dummy_products)
    rag_connector.add_qnas(dummy_qnas)
    rag_connector.add_reviews(dummy_reviews)
    
    # 검색 테스트
    query = "반품 정책 알려줘"
    context = rag_connector.retrieve_context(query, n_results=2)
    print(f"\n--- 검색 테스트 ---")
    print(f"쿼리: {query}")
    print(f"검색된 컨텍스트:\n{context}")
    print("-" * 20)

    query_2 = "갈비탕"
    context_2 = rag_connector.retrieve_context(query_2, n_results=1)
    print(f"쿼리: {query_2}")
    print(f"검색된 컨텍스트:\n{context_2}")
    print("-" * 20)