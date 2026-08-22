"""
기술1-1(국내) - 뉴스 호재/악재/중립 감성분류
1차 버전: Gemini 제로샷 프롬프트 분류
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.services.llm_explain import _call_llm


def classify_sentiment(article: dict) -> dict:
    """
    뉴스 1건을 호재/악재/중립으로 분류
    """
    prompt = f"""당신은 금융시장 뉴스를 분석하는 애널리스트입니다.

다음 뉴스가 주식시장에 호재인지 악재인지 중립인지 판단하세요.

제목: {article['title']}
내용: {article['description']}

반드시 아래 형식 중 하나로만 답하세요 (다른 설명 없이):
호재
악재
중립"""

    result = _call_llm(prompt).strip()

    # 모델이 형식을 안 지킬 경우를 대비한 정규화
    if "호재" in result:
        label = "호재"
    elif "악재" in result:
        label = "악재"
    else:
        label = "중립"

    return {**article, "sentiment": label}


def classify_articles(articles: list) -> list:
    """
    여러 뉴스를 일괄 분류
    """
    results = []
    for article in articles:
        classified = classify_sentiment(article)
        results.append(classified)
    return results


if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "app"))
    from app.data_sources.naver_news_client import search_news
    from app.services.relevance_filter import filter_relevant_news

    keyword = "코스피"
    print(f"'{keyword}' 뉴스 수집 중...")
    articles = search_news(keyword, display=10)

    print("관련성 필터링 중...")
    filtered = filter_relevant_news(keyword, articles, threshold=0.3)
    print(f"필터링된 뉴스: {len(filtered)}건\n")

    print("감성분류 중...\n")
    classified = classify_articles(filtered[:5])  # 테스트로 상위 5건만

    for c in classified:
        print(f"[{c['sentiment']}] (관련도 {c['relevance_score']}) {c['title']}")