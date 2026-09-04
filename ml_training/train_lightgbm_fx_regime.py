"""
기술4-2 - 환율 변동성 국면분류 모델 학습
원/달러 환율의 향후 변동성이 "확대국면"인지 "안정국면"인지 이진분류
기술2-1(시장국면분류)과 동일한 피처엔지니어링/학습 구조 재사용, 라벨만 2-class로 축소
"""

import numpy as np
import pandas as pd
import yfinance as yf
from lightgbm import LGBMClassifier

FX_TICKER = "KRW=X"  # 원/달러 환율 (yfinance)


def build_dataset_fx(period: str = "3y") -> pd.DataFrame:
    """
    원/달러 환율 데이터 + 변동성 피처 + 라벨 생성
    """
    fx = yf.Ticker(FX_TICKER)
    hist = fx.history(period=period)

    if len(hist) < 100:
        raise ValueError("환율 데이터가 부족합니다")

    df = pd.DataFrame({"close": hist["Close"].values}, index=hist.index)
    df["return"] = df["close"].pct_change()

    # 변동성 피처
    df["vol_5d"] = df["return"].rolling(5).std()
    df["vol_20d"] = df["return"].rolling(20).std()
    df["vol_60d"] = df["return"].rolling(60).std()
    df["vol_ratio_5_20"] = df["vol_5d"] / df["vol_20d"]

    # TODO(확장): 한미 금리차, 무역수지 피처 — 안정적인 무료 API 확보 후 추가
    # TODO(확장): 환율 관련 뉴스 감성스코어 — 기술1의 감성분류 파이프라인을 "환율 키워드" 필터로 재사용

    # 라벨: 향후 20일 변동성이 과거 1년 평균 변동성의 1.5배 초과 시 "변동확대"(1), 아니면 "안정"(0)
    future_vol_20d = df["return"].shift(-20).rolling(20).std().shift(-19)
    rolling_avg_vol_1y = df["vol_20d"].rolling(252, min_periods=60).mean()
    df["label"] = (future_vol_20d > rolling_avg_vol_1y * 1.5).astype(int)

    df = df.dropna()
    return df


FEATURE_COLS = ["vol_5d", "vol_20d", "vol_60d", "vol_ratio_5_20"]


def train_fx_regime_model(df: pd.DataFrame):
    """
    LightGBM 이진분류 학습 (변동확대=1, 안정=0)
    """
    X = df[FEATURE_COLS]
    y = df["label"]

    model = LGBMClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        random_state=42,
        verbose=-1,
    )
    model.fit(X, y)

    return model, FEATURE_COLS


def predict_current_fx_regime(model, feature_cols: list, df: pd.DataFrame) -> dict:
    """
    가장 최근 시점 기준 환변동성 국면 예측
    """
    latest = df[feature_cols].iloc[[-1]]
    proba = model.predict_proba(latest)[0]  # [안정확률, 확대확률]

    regime_name = "변동확대" if proba[1] > proba[0] else "안정"

    return {
        "predicted_regime": regime_name,
        "probabilities": {
            "안정": round(float(proba[0]), 4),
            "변동확대": round(float(proba[1]), 4),
        },
    }


def predict_percentile_based_regime(df: pd.DataFrame, lookback_days: int = 252) -> dict:
    """
    시간부족 대안: LightGBM 없이, 최근 20일 변동성이 과거 1년 변동성 분포에서
    상위 몇 %에 위치하는지로 국면 판정 (상위 30% 이내면 "변동확대")
    """
    recent_window = df["vol_20d"].tail(lookback_days)
    current_vol = df["vol_20d"].iloc[-1]

    percentile = (recent_window < current_vol).mean() * 100
    regime_name = "변동확대" if percentile >= 70 else "안정"

    return {
        "predicted_regime": regime_name,
        "current_vol_20d": round(float(current_vol), 5),
        "percentile_rank": round(float(percentile), 1),
    }


if __name__ == "__main__":
    print("환율 데이터 수집 및 피처 생성 중...")
    df = build_dataset_fx()

    print("LightGBM 국면분류 모델 학습 중...")
    model, feature_cols = train_fx_regime_model(df)
    lgbm_result = predict_current_fx_regime(model, feature_cols, df)

    print("백분위수 기반 대안 계산 중...")
    percentile_result = predict_percentile_based_regime(df)

    print("=" * 60)
    print("[LightGBM 모델] 현재 환변동성 국면")
    print("=" * 60)
    print(f"국면: {lgbm_result['predicted_regime']}")
    print(f"확률: 안정 {lgbm_result['probabilities']['안정']:.1%}, "
          f"변동확대 {lgbm_result['probabilities']['변동확대']:.1%}")

    print()
    print("=" * 60)
    print("[백분위수 대안] 현재 환변동성 국면")
    print("=" * 60)
    print(f"국면: {percentile_result['predicted_regime']}")
    print(f"최근 20일 변동성: {percentile_result['current_vol_20d']}")
    print(f"과거 1년 대비 백분위: 상위 {100 - percentile_result['percentile_rank']:.1f}%")