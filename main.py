# main.py

from fastapi import FastAPI
import os 
from dotenv import load_dotenv

# .env 파일을 로드하여 API 키를 사용할 준비를 합니다.
load_dotenv() 

app = FastAPI()

# API 키 로드 여부를 확인하는 테스트 엔드포인트
@app.get("/")
def read_root():
    # os.getenv()를 통해 환경 변수를 읽습니다.
    api_key_status = "Loaded" if os.getenv("OPENAI_API_KEY") else "Not Found"
    return {
        "message": "CS Agent Backend is Running!",
        "api_key_status": api_key_status
    }