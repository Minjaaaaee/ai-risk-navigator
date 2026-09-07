"""
기술1-4 - 종목페이지 온디맨드 AI 코멘터리 + 캐싱
사용자가 조회한 어떤 종목이든, 3% 미만이어도 무조건 코멘터리 생성.
같은 날 같은 종목은 캐시에서 즉시 응답.
국내(6자리 숫자코드)/해외(알파벳 티커) 종목을 자동 판별해 각각 다른 데이터소스 사용.
"""

import torch  # noqa: F401 - MKL(statsmodels)보다 먼저 로드해 DLL 충돌 방지

import os
import re
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.data_sources.kis_client import KISClient
from app.data_sources.yahoo_finance_client import get_index_history, get_asset_history
from app.services.excess_return import get_aligned_returns, estimate_beta, SAMPLE_STOCKS
from app.data_sources.naver_news_client import search_news
from app.services.relevance_filter import filter_relevant_news
from app.services.news_sentiment.domestic import classify_articles
from app.services.llm_explain import _call_llm
from app.db.vectordb import get_cached_commentary, save_commentary_cache


def is_overseas_ticker(stock_code: str) -> bool:
    """
    종목코드가 국내(6자리 숫자)인지 해외(알파벳 포함 티커)인지 판별
    """
    return not re.fullmatch(r"\d{6}", stock_code)


def align_yahoo_returns(index_hist: dict, stock_hist: dict):
    """
    yahoo_finance_client의 dates/closes 배열 2개를 날짜 기준으로 정렬해
    공통 날짜의 일별 수익률(pct change) 시퀀스를 계산
    """
    index_map = dict(zip(index_hist["dates"], index_hist["closes"]))
    stock_map = dict(zip(stock_hist["dates"], stock_hist["closes"]))

    common_dates = sorted(set(index_map) & set(stock_map))
    if len(common_dates) < 2:
        return [], [], []

    index_closes = [index_map[d] for d in common_dates]
    stock_closes = [stock_map[d] for d in common_dates]

    index_returns = [
        (index_closes[i] - index_closes[i - 1]) / index_closes[i - 1]
        for i in range(1, len(index_closes))
    ]
    stock_returns = [
        (stock_closes[i] - stock_closes[i - 1]) / stock_closes[i - 1]
        for i in range(1, len(stock_closes))
    ]

    return common_dates[1:], index_returns, stock_returns


def get_stock_commentary(stock_code: str, stock_name: str, index_name: str = "코스피") -> dict:
    """
    종목 코멘터리 조회 (캐시 우선, 없으면 온디맨드 생성)
    """
    trade_date = datetime.now().strftime("%Y%m%d")

    # 1. 캐시 확인
    cached = get_cached_commentary(stock_code, trade_date)
    if cached:
        print(f"[캐시 히트] {stock_name}({stock_code}) - {trade_date}")
        return cached["commentary"]

    overseas = is_overseas_ticker(stock_code)

    # 해외 종목인데 지수명이 기본값(코스피)이면 나스닥으로 자동 전환
    if overseas and index_name == "코스피":
        index_name = "나스닥"

    print(f"[캐시 미스] {stock_name}({stock_code}) - 온디맨드 생성 중... (해외종목: {overseas})")

    # 2. 온디맨드 생성 - 국내/해외 데이터소스 분기
    if overseas:
        index_hist = get_index_history(index_name, period="6mo")
        stock_hist = get_asset_history(stock_code, period="6mo")
        common_dates, index_returns, stock_returns = align_yahoo_returns(index_hist, stock_hist)
    else:
        client = KISClient()
        index_chart = client.get_index_daily_chart(index_name, period_days=90)
        stock_chart = client.get_stock_daily_chart(stock_code, period_days=90)
        common_dates, index_returns, stock_returns = get_aligned_returns(index_chart, stock_chart)

    if len(common_dates) < 10:
        result = {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "commentary": "데이터가 부족하여 분석할 수 없습니다.",
        }
        save_commentary_cache(stock_code, trade_date, stock_name, result)
        return result

    beta = estimate_beta(stock_returns, index_returns)
    stock_today_return = stock_returns[-1]
    index_today_return = index_returns[-1]
    expected_return = beta * index_today_return
    excess_return = stock_today_return - expected_return

    # 3. 뉴스 수집 + 필터링 + 감성분류
    articles = search_news(stock_name, display=20)
    relevant = filter_relevant_news(stock_name, articles, threshold=0.3)
    top_articles = relevant[:5]

    if not top_articles:
        commentary_text = f"{stock_name} 관련 뉴스가 확인되지 않음, 시장/업종 전반 흐름 영향으로 추정됨"
    else:
        classified = classify_articles(top_articles)
        news_summary = "\n".join(
            f"- [{c['sentiment']}] {c['title']}: {c['description'][:100]}"
            for c in classified
        )

        performance_desc = (
            "선방(초과수익)" if excess_return > 0
            else "부진(초과손실)" if excess_return < 0
            else "예상과 유사한 흐름"
        )
        actual_direction = "상승" if stock_today_return > 0 else "하락" if stock_today_return < 0 else "보합"

        prompt = f"""당신은 금융시장을 분석해 투자자에게 설명하는 애널리스트입니다.

{stock_name}은(는) 오늘 실제로 {round(stock_today_return * 100, 2)}% {actual_direction}했습니다.
{index_name} 지수는 {round(index_today_return * 100, 2)}% 움직였고, 베타({round(beta, 3)})를 감안한 예상 움직임은 {round(expected_return * 100, 2)}%였습니다.
즉 지수 요인을 감안했을 때 예상보다 {performance_desc}했으며, 순수 종목 고유 초과수익률은 {round(excess_return * 100, 2)}%p 입니다.

관련 뉴스 및 감성분류 결과:
{news_summary}

위 정보를 바탕으로, {stock_name}의 실제 주가 움직임({actual_direction})과, 지수 대비 {performance_desc}한 이유를 2~3문장으로 설명하세요.
근거자료에 명확한 이유가 없으면 그렇다고 밝히세요."""

        commentary_text = _call_llm(prompt)

    result = {
        "stock_code": stock_code,
        "stock_name": stock_name,
        "stock_return_pct": round(stock_today_return * 100, 2),
        "index_return_pct": round(index_today_return * 100, 2),
        "beta": round(beta, 3),
        "excess_return_pct": round(excess_return * 100, 2),
        "commentary": commentary_text,
    }

    # 4. 캐시 저장
    save_commentary_cache(stock_code, trade_date, stock_name, result)

    return result


if __name__ == "__main__":
    # 이슈 #13 완료 기준 테스트:
    # 최초 조회(캐시 미스) -> 재조회(캐시 히트) 순서로 확인
    test_stock_code = "005930"
    test_stock_name = "삼성전자"

    print("=== 1차 조회 (캐시 미스 예상) ===")
    result1 = get_stock_commentary(test_stock_code, test_stock_name)
    print(f"\n{result1['stock_name']} 코멘터리:")
    print(result1["commentary"])

    print("\n\n=== 2차 조회 (캐시 히트 예상) ===")
    result2 = get_stock_commentary(test_stock_code, test_stock_name)
    print(f"\n{result2['stock_name']} 코멘터리:")
    print(result2["commentary"])

    print("\n\n=== 해외종목 테스트 (NVDA) ===")
    result3 = get_stock_commentary("NVDA", "엔비디아")
    print(f"\n{result3['stock_name']} 코멘터리:")
    print(result3.get("commentary"))