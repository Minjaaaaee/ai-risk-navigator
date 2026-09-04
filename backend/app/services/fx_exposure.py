"""
기술4-1 - 환노출 비중 계산 (규칙기반)
보유종목 리스트에서 비원화자산 비중을 계산하고 임계치 초과 여부를 판정
"""

FX_EXPOSURE_THRESHOLD = 0.30  # 총자산의 30% 초과 시 경고 플래그


def classify_currency(ticker: str) -> str:
    """
    티커 패턴으로 통화 판별 (MVP 규칙기반)
    .KS(코스피)/.KQ(코스닥)로 끝나면 원화, 그 외는 달러로 간주
    """
    if ticker.upper().endswith(".KS") or ticker.upper().endswith(".KQ"):
        return "KRW"
    return "USD"


def calculate_fx_exposure(holdings: list) -> dict:
    """
    holdings: [{"ticker": str, "value_krw": float}, ...] 형태
    (value_krw: 원화환산 평가액. 외화자산도 이미 환산된 값으로 입력)

    반환: 통화별 합계, 환노출비중(%), 임계치 초과 여부
    """
    if not holdings:
        raise ValueError("보유종목 리스트가 비어 있습니다")

    total_value = sum(h["value_krw"] for h in holdings)
    if total_value <= 0:
        raise ValueError("총 평가액이 0 이하입니다")

    currency_totals = {}
    for h in holdings:
        currency = classify_currency(h["ticker"])
        currency_totals[currency] = currency_totals.get(currency, 0) + h["value_krw"]

    foreign_value = sum(v for c, v in currency_totals.items() if c != "KRW")
    fx_exposure_ratio = foreign_value / total_value

    breakdown = {
        currency: {
            "value_krw": round(value, 0),
            "ratio_pct": round(value / total_value * 100, 1),
        }
        for currency, value in currency_totals.items()
    }

    return {
        "total_value_krw": round(total_value, 0),
        "currency_breakdown": breakdown,
        "fx_exposure_pct": round(fx_exposure_ratio * 100, 1),
        "threshold_pct": round(FX_EXPOSURE_THRESHOLD * 100, 1),
        "exceeds_threshold": fx_exposure_ratio > FX_EXPOSURE_THRESHOLD,
    }


if __name__ == "__main__":
    sample_holdings = [
        {"ticker": "005930.KS", "value_krw": 5_000_000},   # 삼성전자
        {"ticker": "069500.KS", "value_krw": 3_000_000},   # KODEX 200
        {"ticker": "AAPL", "value_krw": 4_000_000},        # 애플
        {"ticker": "QQQ", "value_krw": 3_000_000},         # 나스닥100 ETF
    ]

    result = calculate_fx_exposure(sample_holdings)

    print("=" * 60)
    print(f"총 평가액: {result['total_value_krw']:,.0f}원")
    print("=" * 60)
    for currency, info in result["currency_breakdown"].items():
        print(f"{currency}: {info['value_krw']:,.0f}원 ({info['ratio_pct']}%)")

    print()
    print(f"환노출비중: {result['fx_exposure_pct']}% (임계치 {result['threshold_pct']}%)")
    print(f"임계치 초과: {'예' if result['exceeds_threshold'] else '아니오'}")