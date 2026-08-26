"""
기술1-1(해외) - 해외뉴스 호재/악재/중립 감성분류
자체 파인튜닝 없이 Gemini API 직접 분류
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.services.llm_explain import _call_llm


def classify_sentiment_overseas(article: dict) -> dict:
    """
    영어 뉴스 1건을 호재/악재/중립으로 분류
    """
    prompt = f"""You are a financial market analyst.

Determine whether the following news is positive (호재), negative (악재), or neutral (중립) for the US stock market.

Title: {article['title']}
Content: {article['description']}

Answer with exactly one of these Korean words only (no other text):
호재
악재
중립"""

    result = _call_llm(prompt).strip()

    if "호재" in result:
        label = "호재"
    elif "악재" in result:
        label = "악재"
    else:
        label = "중립"

    return {**article, "sentiment": label}


def classify_articles_overseas(articles: list) -> list:
    results = []
    for article in articles:
        classified = classify_sentiment_overseas(article)
        results.append(classified)
    return results


if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "app"))
    from app.data_sources.rss_client import fetch_rss_articles

    articles = fetch_rss_articles("나스닥", max_items=5)
    print("감성분류 중...\n")
    classified = classify_articles_overseas(articles)

    for c in classified:
        print(f"[{c['sentiment']}] {c['title']}")