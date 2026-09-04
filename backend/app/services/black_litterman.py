"""
기술2-2 - Black-Litterman 기대수익률/공분산 추정
4자산군(국내주식/해외주식/채권/현금) 프록시 기반, 뉴스감성+국면분류를 view로 반영
MVP 단순화: 자산군은 대표 ETF/지수로 프록시, 시가총액은 가정치 사용 (주석 참고)
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np
import pandas as pd
from pypfopt import BlackLittermanModel, risk_models

from app.data_sources.yahoo_finance_client import get_asset_history
from app.services.regime.domestic import get_current_domestic_regime
from app.services.regime.overseas import get_current_overseas_regime

ASSET_CLASSES = ["국내주식", "해외주식", "채권", "현금"]

ASSET_PROXY_TICKERS = {
    "국내주식": "069500.KS",  # KODEX 200
    "해외주식": "QQQ",         # 나스닥100 ETF
    "채권": "TLT",             # 미국 장기국채 ETF
    "현금": "SHY",             # 단기국채(현금성 근사)
}

# MVP 단순화: 실제 시가총액 대신 가정치 사용 (단위: 조원, 추후 정교화 필요)
ASSUMED_MARKET_CAPS = {
    "국내주식": 1000,
    "해외주식": 3000,
    "채권": 1500,
    "현금": 500,
}

# 국면별 연환산 기대수익률 룩업테이블 (MVP 단순화)
REGIME_EXPECTED_RETURN = {
    "상승장": 0.15,
    "하락장": -0.10,
    "횡보장": 0.0,
    "고변동장": -0.05,
}


def get_asset_returns_matrix(period: str = "1y") -> pd.DataFrame:
    """
    4자산군 프록시의 일별 수익률 매트릭스 생성 (공분산 계산용)
    """
    returns_dict = {}
    for asset, ticker in ASSET_PROXY_TICKERS.items():
        history = get_asset_history(ticker, period=period)
        closes = np.array(history["closes"])
        dates = history["dates"]
        returns = pd.Series(closes, index=pd.to_datetime(dates, format="%Y%m%d")).pct_change().dropna()
        returns_dict[asset] = returns

    df = pd.DataFrame(returns_dict).dropna()
    return df


def compute_prior_returns(returns_df: pd.DataFrame) -> tuple:
    """
    시장균형수익률(prior) + 공분산행렬 계산
    """
    cov_matrix = risk_models.sample_cov(returns_df, returns_data=True, frequency=252)

    market_caps = pd.Series(ASSUMED_MARKET_CAPS)

    # PyPortfolioOpt의 market_implied_prior_returns는 risk_aversion 파라미터 필요
    from pypfopt.black_litterman import market_implied_prior_returns

    prior = market_implied_prior_returns(market_caps, risk_aversion=2.5, cov_matrix=cov_matrix)

    return prior, cov_matrix


def build_views() -> tuple:
    """
    View1(뉴스감성) + View2(국면조건부)를 결합해 국내주식/해외주식에 대한 view 생성
    채권/현금은 view 없이 prior만 사용
    반환: (viewdict, confidences) - PyPortfolioOpt idzip 형식
    """
    domestic_regime = get_current_domestic_regime("코스피")
    overseas_regime = get_current_overseas_regime("나스닥")

    domestic_regime_name = domestic_regime["predicted_regime"]
    domestic_confidence = domestic_regime["probabilities"][domestic_regime_name]

    overseas_regime_name = overseas_regime["predicted_regime"]
    overseas_confidence = overseas_regime["probabilities"][overseas_regime_name]

    domestic_view_return = REGIME_EXPECTED_RETURN[domestic_regime_name]
    overseas_view_return = REGIME_EXPECTED_RETURN[overseas_regime_name]

    viewdict = {
        "국내주식": domestic_view_return,
        "해외주식": overseas_view_return,
    }

    confidences = [domestic_confidence, overseas_confidence]

    return viewdict, confidences, {
        "국내주식": {"regime": domestic_regime_name, "confidence": domestic_confidence},
        "해외주식": {"regime": overseas_regime_name, "confidence": overseas_confidence},
    }


def run_black_litterman() -> dict:
    """
    전체 파이프라인 실행: prior 계산 -> view 구성 -> posterior 산출
    """
    print("자산군 수익률 데이터 수집 중...")
    returns_df = get_asset_returns_matrix(period="1y")

    print("시장균형수익률(prior) 계산 중...")
    prior, cov_matrix = compute_prior_returns(returns_df)

    print("국면분류 기반 View 생성 중...")
    viewdict, confidences, view_detail = build_views()

    print("Black-Litterman 모델 적용 중...")
    bl = BlackLittermanModel(
        cov_matrix,
        pi=prior,
        absolute_views=viewdict,
        omega="idzorek",
        view_confidences=confidences,
    )

    posterior_returns = bl.bl_returns()
    posterior_cov = bl.bl_cov()

    return {
        "prior_returns": prior,
        "posterior_returns": posterior_returns,
        "posterior_cov": posterior_cov,
        "view_detail": view_detail,
    }


if __name__ == "__main__":
    result = run_black_litterman()

    print("\n" + "=" * 60)
    print("View 상세")
    print("=" * 60)
    for asset, detail in result["view_detail"].items():
        print(f"{asset}: 국면={detail['regime']}, 신뢰도={detail['confidence']:.2%}")

    print("\n" + "=" * 60)
    print("Prior(사전) vs Posterior(사후) 기대수익률 비교 (연환산)")
    print("=" * 60)
    for asset in ASSET_CLASSES:
        prior_val = result["prior_returns"][asset]
        posterior_val = result["posterior_returns"][asset]
        print(f"{asset}: prior={prior_val:.2%} -> posterior={posterior_val:.2%}")