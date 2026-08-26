"""
기술1-1(해외) - 나스닥/S&P500 "간밤 미국장 브리핑" 통합 파이프라인
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.data_sources.yahoo_finance_client import get_index_data
from app.data_sources.rss_client import fetch_rss_articles
from app.services.news_sentiment.overseas import classify_articles_overseas
from app.services.llm_explain import _call_llm


def generate_overseas_commentary(
    index_name: str = "나스닥",
    threshold_pct: float = 3.0,
    top_n_news: int = 5,
) -> dict:
    """
    해외 지수 "간밤 시황 브리핑" 생성
    """
    data = get_index_data(index_name)
    change_rate = data["change_rate_pct"]
    is_event = abs(change_rate) >= threshold_pct
    direction = "상승" if change_rate > 0 else "하락" if change_rate < 0 else "보합"

    if not is_event:
        return {
            **data,
            "is_event": False,
            "direction": direction,
            "commentary": f"{index_name} {change_rate}% 변동, 특이사항 없음",
        }

    articles = fetch_rss_articles("reuters_business", max_items=top_n_news)
    classified = classify_articles_overseas(articles)

    news_summary = "\n".join(
        f"- [{c['sentiment']}] {c['title']}: {c['description'][:100]}"
        for c in classified
    )

    prompt = f"""당신은 미국 증시를 분석해 한국 투자자에게 브리핑하는 애널리스트입니다.

{index_name} 지수가 간밤 {change_rate}% {direction}했습니다.
현재 종가: {data['current_close']}, 전일 종가: {data['prev_close']}

관련 뉴스 및 감성분류 결과:
{news_summary}

위 정보를 바탕으로 "간밤 미국장 {direction} 원인 top3"를 정리해주세요.
한국 출근길/기상 직후 투자자가 읽는다는 점을 고려해 간결하게, 번호를 매겨 작성하세요."""

    commentary = _call_llm(prompt)

    return {
        **data,
        "is_event": True,
        "direction": direction,
        "related_news": classified,
        "commentary": commentary,
    }


if __name__ == "__main__":
    for index_name in ["나스닥", "S&P500"]:
        print(f"\n{'=' * 60}")
        print(f"{index_name} 간밤 시황 브리핑")
        print("=" * 60)

        result = generate_overseas_commentary(index_name=index_name, threshold_pct=3.0)

        print(f"등락률: {result['change_rate_pct']}% ({result['direction']})")
        print(f"이벤트 발생: {result['is_event']}")
        print(f"\n[코멘터리]\n{result['commentary']}")