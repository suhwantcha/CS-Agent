import chromadb
import os
from openai import OpenAI
from dotenv import load_dotenv

# config.py 파일을 만들었다면 해당 파일에서 경로를 가져오도록 수정 가능
CHROMA_PERSIST_DIR = "./chroma_data" 
COLLECTION_NAME = "naver_cs_manuals"

# OpenAI API 키 로드 (임베딩 모델 사용을 위함)
load_dotenv()
openai_client = OpenAI()

class RAGConnector:
    def __init__(self):
        # ChromaDB 클라이언트 초기화 (데이터가 CHROMA_PERSIST_DIR에 저장됨)
        self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        
        # 콜렉션 생성 또는 기존 콜렉션 가져오기
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            # AI의 지식 검색을 위한 벡터 모델 (OpenAI의 text-embedding-ada-002 사용을 가정)
            # 여기서는 모델 이름을 문자열로만 지정합니다.
            metadata={"hnsw:space": "cosine"}
        )
        print(f"✅ RAG: ChromaDB 컬렉션 '{COLLECTION_NAME}' 준비 완료.")

    def get_embedding(self, text):
        """텍스트를 OpenAI 임베딩 API로 벡터화"""
        # 실제 API 호출 코드는 비용이 발생하므로 생략하고, 
        # 임베딩 모델을 사용하는 함수가 여기 들어갑니다.
        # 프로젝트 시연을 위해 실제 임베딩 모델을 호출하는 코드를 작성해야 합니다.
        
        # 실제 구현 코드 예시 (추후 GPT-4o 사용을 위해 필요):
        # response = openai_client.embeddings.create(input=[text], model="text-embedding-ada-002")
        # return response.data[0].embedding
        
        return [0.1] * 1536 # 더미 벡터 반환 (테스트용)

    def add_manuals(self, manuals_data):
        """JSON 데이터에서 RAG 콘텐츠를 추출하여 ChromaDB에 저장"""
        ids = []
        documents = []
        metadatas = []
        embeddings = []
        
        for item in manuals_data:
            doc_id = item['manual_id']
            # RAG 검색 대상이 될 콘텐츠를 content_for_rag에서 가져옴
            content = item['content_for_rag'] 
            
            ids.append(doc_id)
            documents.append(content)
            # 메타데이터도 같이 저장하여 검색 결과를 필터링할 때 사용
            metadatas.append({"domain": item['domain'], "urgency": item['urgency']})
            
            # 임베딩 생성 (실제 구현 시 self.get_embedding(content) 사용)
            embeddings.append(self.get_embedding(content)) 

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        print(f"✅ RAG: {len(ids)}개의 CS 매뉴얼이 ChromaDB에 벡터화되어 저장되었습니다.")


if __name__ == '__main__':
    # ChromaDB 연결 테스트 및 초기 매뉴얼 데이터 로드 시뮬레이션
    
    # 문과 팀이 제공할 JSON 데이터를 여기에 로드했다고 가정 (실제로는 JSON 파일을 읽어와야 함)
    dummy_manuals = [
        {"manual_id": "CS-PAY-001", "domain": "결제", "urgency": "high", "content_for_rag": "결제 오류 XA-101 발생 시 앱 재설치를 안내 후, 실패하면 수동 결제 링크를 보낸다."},
        {"manual_id": "CS-DEL-002", "domain": "배송", "urgency": "medium", "content_for_rag": "배송 지연 4일 이상 시, 고객에게 지연 상황을 사과하고 보상 쿠폰을 즉시 발급한다."}
    ]
    
    rag_connector = RAGConnector()
    rag_connector.add_manuals(dummy_manuals)
    
    # 검색 테스트
    query = "냉동 식품이 다 녹아서 클레임 걸고 싶어요."
    query_vector = rag_connector.get_embedding(query)
    
    # 실제 검색을 실행하는 코드는 추후 LLM_Agent 모듈에서 구현됩니다.
    # print("검색 결과:", rag_connector.collection.query(query_embeddings=[query_vector], n_results=1))