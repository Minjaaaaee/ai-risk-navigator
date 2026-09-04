"""
기술4-3 - 환노출 시나리오 시뮬레이션 + LLM 설명
기술4-1(환노출비중) + 기술4-2(환변동성국면) 결과를 결합해
원/달러 ±5% 변동 시나리오와 자연어 설명, 헤지ETF 대안을 산출
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.services.fx_exposure import calculate_fx_exposure
from app.services.regime.fx import get_current_fx_regime
from app.services.llm_explain import explain_fx_scenario_card

SCENARIO_SHIFT_PCT = 0.05  # ±5% 시나리오

# MVP 단순화: 정적 헤지ETF 후보 리스트 (보유종목별 정교매칭은 범위 밖, TODO로 남김)
HEDGE_ETF_CANDIDATES = [
    {"name": "KODEX 미국S&P500선물(H)", "note": "환헤지형 미국 대형주 ETF"},
    {"name": "TIGER 미국나스닥100선물(H)", "note": "환헤지형 나스닥100 ETF"},
]


def simulate_fx_scenario(holdings: list) -> dict:
    """
    보유종목 리스트를 받아 환노출비중 + 환변동성국면 + ±5% 시나리오 영향을 종합 계산
    """
    exposure_result = calculate_fx_exposure(holdings)
    regime_result = get_current_fx_regime()

    total_value = exposure_result["total_value_krw"]
    foreign_value = sum(
        info["value_krw"]
        for currency, info in exposure_result["currency_breakdown"].items()
        if currency != "KRW"
    )

    # 원/달러 +5% (원화가치 하락, 외화자산 원화환산액 상승)
    impact_up = foreign_value * SCENARIO_SHIFT_PCT
    # 원/달러 -5% (원화가치 상승, 외화자산 원화환산액 하락)
    impact_down = -foreign_value * SCENARIO_SHIFT_PCT

    scenario = {
        "shift_pct": round(SCENARIO_SHIFT_PCT * 100, 1),
        "impact_up_krw": round(impact_up, 0),
        "impact_up_pct_of_total": round(impact_up / total_value * 100, 2),
        "impact_down_krw": round(impact_down, 0),
        "impact_down_pct_of_total": round(impact_down / total_value * 100, 2),
    }

    result = {
        "exposure": exposure_result,
        "fx_regime": regime_result,
        "scenario": scenario,
    }

    if exposure_result["exceeds_threshold"]:
        result["hedge_recommendations"] = HEDGE_ETF_CANDIDATES

    result["explanation"] = explain_fx_scenario_card(result)

    return result


if __name__ == "__main__":
    sample_holdings = [
        {"ticker": "005930.KS", "value_krw": 5_000_000},
        {"ticker": "069500.KS", "value_krw": 3_000_000},
        {"ticker": "AAPL", "value_krw": 4_000_000},
        {"ticker": "QQQ", "value_krw": 3_000_000},
    ]

    result = simulate_fx_scenario(sample_holdings)

    print("=" * 60)
    print(f"환노출비중: {result['exposure']['fx_exposure_pct']}% "
          f"(임계치 {result['exposure']['threshold_pct']}%, "
          f"초과: {'예' if result['exposure']['exceeds_threshold'] else '아니오'})")
    print(f"환변동성국면: {result['fx_regime']['predicted_regime']}")
    print("=" * 60)
    print(f"원/달러 +{result['scenario']['shift_pct']}% 시: "
          f"{result['scenario']['impact_up_krw']:+,.0f}원 "
          f"(총자산 대비 {result['scenario']['impact_up_pct_of_total']:+}%)")
    print(f"원/달러 -{result['scenario']['shift_pct']}% 시: "
          f"{result['scenario']['impact_down_krw']:+,.0f}원 "
          f"(총자산 대비 {result['scenario']['impact_down_pct_of_total']:+}%)")

    if "hedge_recommendations" in result:
        print()
        print("[환헤지 대안]")
        for etf in result["hedge_recommendations"]:
            print(f"- {etf['name']}: {etf['note']}")

    print()
    print("[AI 설명]")
    print(result["explanation"])