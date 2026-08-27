"""
기술1-2 - 선별종목 AI 코멘터리
초과수익률 스캐닝 결과 중 임계치 초과 종목만 뉴스기반 코멘터리 생성
"""

import torch

import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.services.excess_return import scan_stocks, SAMPLE_STOCKS
from app.data_sources.naver_news_client import search_news
from app.services.relevance_filter import filter_relevant_news
from app.services.news_sentiment.domestic import classify_articles
from app.services.llm_explain import _call_llm


def generate_selected_stock_commentary(
    threshold_pct: float = 1.0,
    top_n: int = 5,
    index_name: str = "코스피",
) -> list:
    """
    초과수익률 스캐닝 -> 임계치 초과 종목 필터링 -> 종목별 뉴스기반 코멘터리 생성
    """
    scan_results = scan_stocks(stock_dict=SAMPLE_STOCKS, index_name=index_name)

    filtered = [r for r in scan_results if abs(r["excess_return_pct"]) >= threshold_pct]
    filtered.sort(key=lambda x: abs(x["excess_return_pct"]), reverse=True)
    target_stocks = filtered[:top_n]

    if not target_stocks:
        return []

    commentaries = []
    for stock in target_stocks:
        stock_name = stock["stock_name"]

        articles = search_news(stock_name, display=20)
        relevant = filter_relevant_news(stock_name, articles, threshold=0.3)
        top_articles = relevant[:5]

        if not top_articles:
            commentaries.append({
                **stock,
                "commentary": f"{stock_name} 관련 뉴스가 확인되지 않음, 시장/업종 전반 흐름 영향으로 추정됨",
            })
            continue

        classified = classify_articles(top_articles)
        news_summary = "\n".join(
            f"- [{c['sentiment']}] {c['title']}: {c['description'][:100]}"
            for c in classified
        )

        direction = "상승" if stock["excess_return_pct"] > 0 else "하락"

        prompt = f"""당신은 금융시장을 분석해 투자자에게 설명하는 애널리스트입니다.

{stock_name}이(가) 오늘 {stock['stock_return_pct']}% {direction}했습니다.
{index_name} 지수는 {stock['index_return_pct']}% 움직였고, 베타({stock['beta']})를 감안한 예상 움직임은 {stock['expected_return_pct']}%였습니다.
즉 지수 요인을 제외한 순수 종목 고유 초과수익률은 {stock['excess_return_pct']}%p 입니다.

관련 뉴스 및 감성분류 결과:
{news_summary}

위 정보를 바탕으로, {stock_name}이(가) 지수 대비 왜 초과로 {direction}했는지 2~3문장으로 설명하세요.
지수 요인이 아닌 종목 고유 이슈에 초점을 맞추세요. 근거자료에 명확한 이유가 없으면 그렇다고 밝히세요."""

        commentary = _call_llm(prompt)

        commentaries.append({
            **stock,
            "related_news": classified,
            "commentary": commentary,
        })

        time.sleep(0.5)

    return commentaries


if __name__ == "__main__":
    print("선별종목 AI 코멘터리 생성 중...\n")
    results = generate_selected_stock_commentary(threshold_pct=1.0, top_n=5)

    if not results:
        print("임계치를 초과한 종목이 없습니다.")
    else:
        for r in results:
            print(f"\n{'=' * 60}")
            print(f"[{r['stock_name']}] {r['stock_return_pct']}% (지수대비 {r['excess_return_pct']}%p)")
            print("=" * 60)
            print(r["commentary"])