import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from db_connector import get_db_connection
from rag_connector import RAGConnector

# 환경 변수 및 OpenAI 클라이언트 초기화
load_dotenv()
openai_client = OpenAI()

# --- 1. CS 실패 로그 기반 학습 함수들 ---

def fetch_failed_logs():
    """학습하지 않은 실패 로그를 DB에서 가져옵니다."""
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT log_id, input_text, ai_action_failed, final_resolution
                FROM inquiry_logs
                WHERE resolution_feedback = 'failure' AND is_learned = FALSE AND final_resolution IS NOT NULL
                """
            )
            logs = cur.fetchall()
            return [{"log_id": r[0], "query": r[1], "failed_answer": r[2], "correct_answer": r[3]} for r in logs]
    except Exception as e:
        print(f"⚠️ 실패 로그 조회 중 오류 발생: {e}")
        return []
    finally:
        conn.close()

def generate_new_knowledge_from_cs(log):
    """(CS실패로그용) LLM을 사용하여 새로운 지식(Golden Q&A)을 생성합니다."""
    system_prompt = "당신은 CS 에이전트의 지식베이스를 개선하는 AI입니다. 고객의 질문, AI의 실패한 답변, 상담원의 올바른 해결책을 바탕으로, 미래에 유사한 질문에 완벽하게 답변할 수 있는 간결하고 명확한 '질문-답변' 형식의 지식 조각 1개를 생성해야 합니다."
    user_prompt = f"다음은 AI가 실패한 상담 기록입니다.\n- 고객 질문: {log['query']}\n- AI의 잘못된 답변: {log['failed_answer']}\n- 올바른 해결책: {log['correct_answer']}\n\n위 정보를 바탕으로, 이 상황에 가장 적합한 '질문-답변' 형식의 새로운 지식 1개를 생성해주세요."
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7, max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ LLM으로 지식 생성 중 오류 발생: {e}")
        return None

def mark_log_as_learned(log_id):
    """해당 로그를 '학습 완료' 상태로 업데이트합니다."""
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE inquiry_logs SET is_learned = TRUE WHERE log_id = %s", (str(log_id),))
        conn.commit()
    except Exception as e:
        print(f"⚠️ 로그 상태 업데이트 중 오류 발생: {e}")
        conn.rollback()
    finally:
        conn.close()

# --- 2. 리뷰 기반 선제적 학습 함수들 ---

def fetch_learning_opportunities_from_reviews():
    """리뷰 기반 학습 대상을 JSON 파일에서 가져오고, 파일은 비웁니다."""
    file_path = 'data/learning_opportunities.json'
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            opportunities = json.load(f)
        # 처리 후 파일 비우기
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return opportunities
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def generate_knowledge_from_review(opportunity):
    """(리뷰용) 부정적 리뷰를 바탕으로 선제적 Q&A 지식을 생성합니다."""
    system_prompt = "당신은 고객 리뷰를 분석하여 잠재적인 고객 질문을 예측하고, 이에 대한 모범 답변을 생성하는 AI입니다. 주어진 리뷰 내용을 바탕으로, 고객들이 궁금해할 만한 질문과 그에 대한 상세하고 친절한 답변을 '질문-답변' 형식의 지식 조각으로 생성해야 합니다."
    user_prompt = f"다음은 고객이 남긴 부정적인 리뷰입니다.\n- 리뷰 분류: {opportunity['category']}\n- 리뷰 내용: {opportunity['review_text']}\n\n이 리뷰를 본 다른 고객이 궁금해할 만한 예상 질문과, 그에 대한 상세하고 친절한 답변을 '질문-답변' 형식으로 생성해주세요. (예: Q: 이 제품 내구성이 어떤가요? A: ...)"
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7, max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ LLM으로 리뷰 기반 지식 생성 중 오류 발생: {e}")
        return None

# --- 3. 메인 실행 로직 ---

def main():
    """자기진화 에이전트의 학습 과정을 실행합니다."""
    print("--- 🧠 자기진화 에이전트 학습 시작 ---")
    rag_connector = RAGConnector()

    # --- 프로세스 1: CS 실패 로그 기반 학습 ---
    print("\n--- [1/2] CS 실패 로그 기반 학습 진행 ---")
    failed_logs = fetch_failed_logs()
    if not failed_logs:
        print("✅ 학습할 새로운 CS 실패 로그가 없습니다.")
    else:
        print(f"🔍 {len(failed_logs)}개의 CS 실패 로그를 발견했습니다.")
        for log in failed_logs:
            print(f"\n--- 학습 진행 중 (Log ID: {log['log_id']}) ---")
            new_knowledge = generate_new_knowledge_from_cs(log)
            if not new_knowledge:
                print("   -> ❌ 지식 생성 실패. 다음 로그로 넘어갑니다.")
                continue
            print(f"   -> ✨ 새로운 지식 생성 완료:\n{new_knowledge}\n")
            try:
                new_manual_item = {'manual_id': f"learned-cs-{log['log_id']}", 'content_for_rag': new_knowledge, 'domain': 'learned-cs', 'urgency': 'medium'}
                rag_connector.add_manuals([new_manual_item])
                print("   -> ✅ 새로운 지식이 RAG 지식베이스에 추가되었습니다.")
                mark_log_as_learned(log['log_id'])
                print("   -> ✅ 해당 로그를 '학습 완료' 처리했습니다.")
            except Exception as e:
                print(f"   -> ❌ RAG 업데이트 또는 DB 상태 변경 중 오류 발생: {e}")

    # --- 프로세스 2: 리뷰 기반 선제적 학습 ---
    print("\n--- [2/2] 리뷰 기반 선제적 학습 진행 ---")
    learning_ops = fetch_learning_opportunities_from_reviews()
    if not learning_ops:
        print("✅ 학습할 새로운 리뷰가 없습니다.")
    else:
        print(f"🔍 {len(learning_ops)}개의 리뷰 기반 학습 대상을 발견했습니다.")
        for op in learning_ops:
            print(f"\n--- 학습 진행 중 (Review ID: {op['review_id']}) ---")
            new_knowledge = generate_knowledge_from_review(op)
            if not new_knowledge:
                print("   -> ❌ 지식 생성 실패. 다음 리뷰로 넘어갑니다.")
                continue
            print(f"   -> ✨ 새로운 지식 생성 완료:\n{new_knowledge}\n")
            try:
                new_manual_item = {'manual_id': f"learned-review-{op['review_id']}", 'content_for_rag': new_knowledge, 'domain': 'learned-review', 'urgency': 'medium'}
                rag_connector.add_manuals([new_manual_item])
                print("   -> ✅ 새로운 지식이 RAG 지식베이스에 추가되었습니다.")
            except Exception as e:
                print(f"   -> ❌ RAG 업데이트 중 오류 발생: {e}")

    print("\n--- 🎉 자기진화 에이전트 학습 완료 ---")

if __name__ == '__main__':
    main()
