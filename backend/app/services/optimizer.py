"""
기술2-3 - 포트폴리오 최적화 (PyPortfolioOpt EfficientFrontier)
기술2-2(Black-Litterman)의 posterior 기대수익률/공분산을 입력받아
사용자 리스크허용도에 맞는 4자산군 최종 배분(%) 산출
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from pypfopt import EfficientFrontier

from app.services.black_litterman import run_black_litterman, ASSET_CLASSES

# MVP 단순화: 설문(계좌유형×투자기간×시드머니) 결과를 5단계 리스크프로필로 매핑했다고 가정
# 프로필별 "감내 가능한 연간 변동성 상한"을 지정 (실제 매핑 로직은 온보딩 설문 완성 후 정교화)
RISK_PROFILE_VOL_CAP = {
    "안정형": 0.08,
    "안정추구형": 0.12,
    "위험중립형": 0.16,
    "적극투자형": 0.22,
    "공격투자형": 0.30,
}

# 자산군별 최소/최대 비중 제약 (MVP 단순화: 극단적 쏠림 방지용 최소한의 가드레일)
ASSET_WEIGHT_BOUNDS = {
    "국내주식": (0.0, 0.6),
    "해외주식": (0.0, 0.6),
    "채권": (0.0, 0.7),
    "현금": (0.05, 1.0),  # 현금은 최소 5% 유지
}


def optimize_portfolio(risk_profile: str = "위험중립형", current_allocation: dict = None) -> dict:
    """
    Black-Litterman posterior를 입력으로 리스크프로필별 최적 배분 산출
    """
    if risk_profile not in RISK_PROFILE_VOL_CAP:
        raise ValueError(f"알 수 없는 리스크프로필: {risk_profile}")

    bl_result = run_black_litterman()
    posterior_returns = bl_result["posterior_returns"]
    posterior_cov = bl_result["posterior_cov"]

    bounds = [ASSET_WEIGHT_BOUNDS[asset] for asset in ASSET_CLASSES]

    ef = EfficientFrontier(posterior_returns, posterior_cov, weight_bounds=bounds)

    target_vol = RISK_PROFILE_VOL_CAP[risk_profile]

    try:
        ef.efficient_risk(target_volatility=target_vol)
    except Exception:
        # 목표 변동성이 달성 불가능한 범위일 경우 max Sharpe로 폴백
        ef = EfficientFrontier(posterior_returns, posterior_cov, weight_bounds=bounds)
        ef.max_sharpe()

    cleaned_weights = ef.clean_weights()
    performance = ef.portfolio_performance(verbose=False)

    recommended = {asset: round(cleaned_weights[asset] * 100, 1) for asset in ASSET_CLASSES}

    result = {
        "risk_profile": risk_profile,
        "target_volatility_cap": target_vol,
        "recommended_allocation": recommended,
        "expected_annual_return": round(performance[0] * 100, 2),
        "annual_volatility": round(performance[1] * 100, 2),
        "sharpe_ratio": round(performance[2], 2),
    }

    if current_allocation:
        result["current_allocation"] = current_allocation
        result["allocation_diff"] = {
            asset: round(recommended.get(asset, 0) - current_allocation.get(asset, 0), 1)
            for asset in ASSET_CLASSES
        }

    return result


if __name__ == "__main__":
    # MVP 테스트용 임의 현재배분 (실제로는 사용자 계좌 연동 데이터 사용 예정)
    sample_current = {"국내주식": 50, "해외주식": 20, "채권": 20, "현금": 10}

    result = optimize_portfolio(risk_profile="위험중립형", current_allocation=sample_current)

    print("=" * 60)
    print(f"리스크프로필: {result['risk_profile']} (변동성 상한 {result['target_volatility_cap']:.0%})")
    print("=" * 60)
    print(f"기대수익률(연): {result['expected_annual_return']}%")
    print(f"변동성(연): {result['annual_volatility']}%")
    print(f"샤프비율: {result['sharpe_ratio']}")
    print()
    print(f"{'자산군':<8}{'현재':>8}{'권장':>8}{'차이':>8}")
    for asset in ASSET_CLASSES:
        cur = result["current_allocation"][asset]
        rec = result["recommended_allocation"][asset]
        diff = result["allocation_diff"][asset]
        sign = "+" if diff >= 0 else ""
        print(f"{asset:<8}{cur:>7}%{rec:>7}%{sign}{diff:>6}%p")