"""
기술1-1(국내) - 지수 레벨 코멘터리 통합 파이프라인
변동성 이벤트 감지 -> 관련뉴스 수집/필터링/감성분류 -> LLM 요약까지 한번에 처리
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.data_sources.kis_client import KISClient
from app.data_sources.naver_news_client import search_news
from app.services.volatility import calculate_volatility_from_current, detect_volatility_event
from app.services.relevance_filter import filter_relevant_news
from app.services.news_sentiment.domestic import classify_articles
from app.services.llm_explain import _call_llm


def generate_index_commentary(
    index_name: str = "코스피",
    threshold_pct: float = 3.0,
    investment_horizon: str = "장기",  # "장기" or "단기"
    top_n_news: int = 5,
) -> dict:
    """
    지수 레벨 코멘터리 생성 파이프라인
    1. 변동성 이벤트 감지
    2. 이벤트 있으면 관련뉴스 수집+필터링+감성분류
    3. LLM으로 "오늘 원인 top3" 요약 생성 (투자기간별 톤 분기)
    """
    client = KISClient()

    # 1. 변동성 이벤트 감지
    raw_data = client.get_index_price(index_name)
    volatility = calculate_volatility_from_current(raw_data)
    event_result = detect_volatility_event(volatility, threshold_pct=threshold_pct)

    if not event_result["is_event"]:
        return {
            **event_result,
            "index_name": index_name,
            "commentary": f"{index_name} {event_result['change_rate_pct']}% 변동, 특이사항 없음",
        }

    # 2. 관련뉴스 수집 + 필터링 + 감성분류
    articles = search_news(index_name, display=20)
    filtered = filter_relevant_news(index_name, articles, threshold=0.3)
    top_articles = filtered[:top_n_news]
    classified = classify_articles(top_articles)

    # 3. LLM 요약 생성 (투자기간별 톤 분기)
    news_summary = "\n".join(
        f"- [{c['sentiment']}] {c['title']}: {c['description'][:100]}"
        for c in classified
    )

    if investment_horizon == "장기":
        tone_instruction = "장기투자자 관점에서, 단기 변동에 일희일비하지 않도록 차분한 톤으로 작성하세요."
    else:
        tone_instruction = "단기투자자 관점에서, 리스크 관리가 필요한 시점임을 명확히 알리는 톤으로 작성하세요."

    prompt = f"""당신은 금융시장 뉴스를 분석해 투자자에게 브리핑하는 애널리스트입니다.

{index_name} 지수가 오늘 {event_result['change_rate_pct']}% {event_result['direction']}했습니다.
현재가: {event_result['current']}, 시가: {event_result['open']}, 고가: {event_result['high']}, 저가: {event_result['low']}

관련 뉴스 및 감성분류 결과:
{news_summary}

위 정보를 바탕으로 "오늘 {event_result['direction']} 원인 top3"를 정리해주세요.
{tone_instruction}
각 원인은 1줄로 간결하게, 번호를 매겨 작성하세요."""

    commentary = _call_llm(prompt)

    return {
        **event_result,
        "index_name": index_name,
        "related_news": classified,
        "commentary": commentary,
    }


if __name__ == "__main__":
    for index_name in ["코스피", "코스닥"]:
        print(f"\n{'=' * 60}")
        print(f"{index_name} 코멘터리 생성")
        print("=" * 60)

        result = generate_index_commentary(index_name=index_name, threshold_pct=3.0, investment_horizon="장기")

        print(f"등락률: {result['change_rate_pct']}% ({result['direction']})")
        print(f"이벤트 발생: {result['is_event']}")
        print(f"\n[코멘터리]\n{result['commentary']}")

        import time
        time.sleep(1)  # KIS API rate limit 대응