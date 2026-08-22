"""
기술1-1 - 변동성 지표 계산 및 급변 이벤트 감지
"""

import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.data_sources.kis_client import KISClient


def calculate_volatility_from_current(index_data: dict) -> dict:
    """
    당일 현재가 조회 결과로 일중 변동성 지표 계산
    KIS get_index_price() 결과의 output을 그대로 받음
    """
    output = index_data["output"]

    current = float(output["bstp_nmix_prpr"])
    open_price = float(output["bstp_nmix_oprc"])
    high = float(output["bstp_nmix_hgpr"])
    low = float(output["bstp_nmix_lwpr"])
    change_rate = float(output["bstp_nmix_prdy_ctrt"])  # 전일대비 등락률(%)

    # 일중 고저폭 비율
    intraday_range_ratio = (high - low) / open_price if open_price else 0

    return {
        "current": current,
        "open": open_price,
        "high": high,
        "low": low,
        "change_rate_pct": change_rate,
        "intraday_range_ratio": round(intraday_range_ratio, 4),
    }


def detect_volatility_event(volatility: dict, threshold_pct: float = 3.0) -> dict:
    """
    급변 이벤트 감지: 전일대비 등락률 절댓값이 임계치(기본 3%) 이상이면 이벤트 발생
    """
    change_rate = volatility["change_rate_pct"]
    is_event = abs(change_rate) >= threshold_pct

    return {
        **volatility,
        "is_event": is_event,
        "threshold_pct": threshold_pct,
        "direction": "상승" if change_rate > 0 else "하락" if change_rate < 0 else "보합",
    }


if __name__ == "__main__":
    client = KISClient()

    for index_name in ["코스피", "코스닥"]:
        print(f"\n{'=' * 50}")
        print(f"{index_name} 변동성 분석")
        print("=" * 50)

        raw_data = client.get_index_price(index_name)
        volatility = calculate_volatility_from_current(raw_data)
        result = detect_volatility_event(volatility, threshold_pct=3.0)

        print(f"현재가: {result['current']}")
        print(f"전일대비: {result['change_rate_pct']}% ({result['direction']})")
        print(f"일중 고저폭 비율: {result['intraday_range_ratio']}")
        print(f"급변 이벤트 발생 여부: {result['is_event']} (임계치 {result['threshold_pct']}%)")

        time.sleep(1)  # KIS API 초당 호출 제한 대응