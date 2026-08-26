"""
기술1-2 - 전종목 초과수익률 스캐닝
베타(β) 추정(OLS 회귀) 및 초과수익률 계산. AI 아님, 순수 통계.
"""

import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np
import statsmodels.api as sm

from app.data_sources.kis_client import KISClient

# 샘플 종목 (MVP 단계 - 시총 상위 위주, 추후 전종목으로 확장 가능)
SAMPLE_STOCKS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "035420": "NAVER",
    "005380": "현대차",
    "051910": "LG화학",
}


def _extract_date_close_map(chart_data: dict, close_field: str) -> dict:
    """
    일별시세 응답에서 {날짜: 종가} 딕셔너리 생성 (정렬 순서에 의존하지 않음)
    """
    items = chart_data.get("output2", [])
    result = {}
    for item in items:
        date = item.get("stck_bsop_date")
        close = item.get(close_field)
        if date and close:
            result[date] = float(close)
    return result


def _calculate_returns_from_map(date_close_map: dict) -> dict:
    """
    {날짜: 종가} -> {날짜: 수익률} (날짜 오름차순 정렬 후 계산)
    """
    dates = sorted(date_close_map.keys())
    returns = {}
    for i in range(1, len(dates)):
        prev_close = date_close_map[dates[i - 1]]
        curr_close = date_close_map[dates[i]]
        if prev_close != 0:
            returns[dates[i]] = (curr_close - prev_close) / prev_close
    return returns


def get_aligned_returns(index_chart: dict, stock_chart: dict) -> tuple:
    """
    지수와 종목의 수익률을 날짜 기준으로 매칭해서 정렬된 리스트로 반환
    반환: (공통 날짜 리스트, 지수수익률 리스트, 종목수익률 리스트) - 날짜 오름차순
    """
    index_close_map = _extract_date_close_map(index_chart, "bstp_nmix_prpr")
    stock_close_map = _extract_date_close_map(stock_chart, "stck_clpr")

    index_returns = _calculate_returns_from_map(index_close_map)
    stock_returns = _calculate_returns_from_map(stock_close_map)

    common_dates = sorted(set(index_returns.keys()) & set(stock_returns.keys()))

    index_ret_list = [index_returns[d] for d in common_dates]
    stock_ret_list = [stock_returns[d] for d in common_dates]

    return common_dates, index_ret_list, stock_ret_list


def estimate_beta(stock_returns: list, index_returns: list) -> float:
    """
    OLS 회귀로 베타 추정: 종목수익률 = alpha + beta * 지수수익률
    """
    n = min(len(stock_returns), len(index_returns))
    if n < 10:
        raise ValueError("회귀분석을 위한 데이터가 부족합니다 (최소 10개 필요)")

    y = np.array(stock_returns[-n:])
    x = np.array(index_returns[-n:])
    x = sm.add_constant(x)

    model = sm.OLS(y, x).fit()
    beta = model.params[1]
    return float(beta)


def calculate_excess_return(
    stock_code: str,
    stock_name: str,
    index_chart: dict,
    client: KISClient,
) -> dict:
    """
    종목 1개에 대해 베타 추정 + 당일 초과수익률 계산 (날짜 정렬 매칭)
    """
    stock_chart = client.get_stock_daily_chart(stock_code, period_days=90)

    common_dates, index_returns, stock_returns = get_aligned_returns(index_chart, stock_chart)

    if len(common_dates) < 10:
        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "error": f"공통 날짜 데이터 부족 ({len(common_dates)}건)",
        }

    beta = estimate_beta(stock_returns, index_returns)

    stock_today_return = stock_returns[-1]
    index_today_return = index_returns[-1]

    expected_return = beta * index_today_return
    excess_return = stock_today_return - expected_return

    return {
        "stock_code": stock_code,
        "stock_name": stock_name,
        "beta": round(beta, 3),
        "stock_return_pct": round(stock_today_return * 100, 2),
        "index_return_pct": round(index_today_return * 100, 2),
        "expected_return_pct": round(expected_return * 100, 2),
        "excess_return_pct": round(excess_return * 100, 2),
        "matched_date": common_dates[-1],
    }


def scan_stocks(stock_dict: dict = SAMPLE_STOCKS, index_name: str = "코스피") -> list:
    """
    여러 종목에 대해 일괄 초과수익률 스캐닝
    """
    client = KISClient()

    index_chart = client.get_index_daily_chart(index_name, period_days=90)

    results = []
    for code, name in stock_dict.items():
        try:
            result = calculate_excess_return(code, name, index_chart, client)
            results.append(result)
        except Exception as e:
            print(f"[에러] {name}({code}) 처리 실패: {e}")
        time.sleep(0.3)

    valid_results = [r for r in results if "error" not in r]
    valid_results.sort(key=lambda x: abs(x["excess_return_pct"]), reverse=True)

    return valid_results


if __name__ == "__main__":
    print("전종목(샘플) 초과수익률 스캐닝 중...\n")
    results = scan_stocks()

    print(f"{'종목명':<12} {'베타':>6} {'종목수익률':>10} {'지수수익률':>10} {'초과수익률':>10}")
    print("-" * 60)
    for r in results:
        print(f"{r['stock_name']:<12} {r['beta']:>6} {r['stock_return_pct']:>9}% {r['index_return_pct']:>9}% {r['excess_return_pct']:>9}%")