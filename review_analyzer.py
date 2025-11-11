import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# 환경 변수 및 OpenAI 클라이언트 초기화
load_dotenv()
client = OpenAI()

REVIEWS_FILE_PATH = "data/reviews.json"

def load_reviews():
    """리뷰 JSON 파일을 로드합니다."""
    try:
        with open(REVIEWS_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ 오류: {REVIEWS_FILE_PATH} 파일을 찾을 수 없습니다.")
        return []
    except json.JSONDecodeError:
        print(f"⚠️ 오류: {REVIEWS_FILE_PATH} JSON 형식이 올바르지 않습니다.")
        return []

def analyze_review(review):
    """LLM을 사용하여 개별 리뷰를 분석하고 답변 초안을 생성합니다."""
    
    system_prompt = """당신은 네이버 스마트스토어의 리뷰 관리 AI입니다. 주어진 고객 리뷰를 분석하여, 지정된 JSON 형식으로만 출력해야 합니다. 이미지 URL이 제공되면 이미지 내용까지 함께 분석하세요."""
    
    # LLM에게 전달할 메시지 구성
    user_content = [
        {
            "type": "text",
            "text": f"""다음 고객 리뷰를 분석하고, 아래 지침에 따라 JSON 형식으로 결과를 반환해주세요.

            - 리뷰 텍스트: {review['review_text']}
            - 별점: {review['rating']}/5

            [분석 요청]
            1. `category`: 리뷰를 다음 중 하나로 분류하세요: ["긍정적 피드백", "제품 품질 불만", "배송 불만", "가격 불만", "기타"]
            2. `is_urgent`: 관리자의 즉각적인 개입이 필요한 긴급한 리뷰인지 boolean 값(true/false)으로 판단하세요. (예: 제품 파손, 안전 문제, 심각한 불만)
            3. `summary`: 리뷰의 핵심 내용을 1-2 문장으로 요약하세요.
            4. `draft_reply`: 고객에게 회신할 답변의 초안을 공손하고 전문적인 톤으로 작성하세요.
            
            [출력 형식]
            ```json
            {{
              "category": "...",
              "is_urgent": true/false,
              "summary": "...",
              "draft_reply": "..."
            }}
            ```
            """
        }
    ]
    
    # 멀티모달: 이미지 URL이 있는 경우 메시지에 추가
    if review.get('image_url'):
        user_content.append({
            "type": "image_url",
            "image_url": {"url": review['image_url']}
        })

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"} # JSON 출력 모드 활성화
        )
        
        analysis_result = json.loads(response.choices[0].message.content)
        return analysis_result
        
    except Exception as e:
        print(f"⚠️ 리뷰 분석 중 오류 발생 (Review ID: {review['review_id']}): {e}")
        return None

def main():
    """리뷰 분석을 실행하고 최종 보고서를 출력하며, 학습 대상을 저장합니다."""
    print("--- 🤖 스마트스토어 리뷰 분석기 시작 ---")
    
    reviews = load_reviews()
    if not reviews:
        print("분석할 리뷰가 없습니다.")
        return
        
    print(f"🔍 총 {len(reviews)}개의 리뷰를 분석합니다.\n")
    
    urgent_reviews = []
    category_counts = {}
    new_learning_opportunities = 0

    # 기존 학습 기회 파일 로드 (중복 방지용)
    try:
        with open('data/learning_opportunities.json', 'r', encoding='utf-8') as f:
            learning_ops = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        learning_ops = []
    existing_ids = {op['review_id'] for op in learning_ops}
    
    for review in reviews:
        print(f"--- 분석 중 (Review ID: {review['review_id']}) ---")
        analysis = analyze_review(review)
        
        if analysis:
            print(f"  - 분류: {analysis['category']}")
            print(f"  - 긴급 여부: {'🚨 예' if analysis['is_urgent'] else '아니오'}")
            print(f"  - 요약: {analysis['summary']}")
            print(f"  - 답변 초안: {analysis['draft_reply']}\n")
            
            # 보고서용 데이터 집계
            if analysis['is_urgent']:
                urgent_reviews.append({
                    "review_id": review['review_id'],
                    "summary": analysis['summary']
                })
            
            category_counts[analysis['category']] = category_counts.get(analysis['category'], 0) + 1

            # ❶ 자기진화: 학습 대상 리뷰 식별 및 저장
            if (analysis['category'] in ["제품 품질 불만", "배송 불만"]) and review['rating'] <= 2:
                if review['review_id'] not in existing_ids:
                    learning_ops.append({
                        "review_id": review['review_id'],
                        "category": analysis['category'],
                        "review_text": review['review_text']
                    })
                    existing_ids.add(review['review_id'])
                    new_learning_opportunities += 1
                    print(f"  -> ✨ 자기진화 학습 대상 추가 (ID: {review['review_id']})")

        else:
            print("  -> ❌ 이 리뷰는 분석에 실패했습니다.\n")

    # ❷ 자기진화: 새로운 학습 기회 파일에 저장
    if new_learning_opportunities > 0:
        with open('data/learning_opportunities.json', 'w', encoding='utf-8') as f:
            json.dump(learning_ops, f, indent=2, ensure_ascii=False)
        print(f"\n✅ 총 {new_learning_opportunities}개의 새로운 학습 대상을 `learning_opportunities.json`에 저장했습니다.")

    # 최종 요약 보고서 출력
    print("\n--- 📊 최종 리뷰 분석 보고서 ---")
    print("\n[리뷰 분류 요약]")
    for category, count in category_counts.items():
        print(f"- {category}: {count}건")
        
    print("\n[🚨 긴급 조치 필요 리뷰]")
    if urgent_reviews:
        for item in urgent_reviews:
            print(f"- ID: {item['review_id']}, 내용: {item['summary']}")
    else:
        print("- 해당 없음")
        
    print("\n--- 🤖 리뷰 분석 완료 ---")

if __name__ == '__main__':
    main()
