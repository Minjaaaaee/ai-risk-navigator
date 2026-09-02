"""
기술2-1 - 국내 시장 국면분류 모델 학습
과거 코스피 데이터로 피처 생성 -> 사후 라벨링 -> LightGBM 학습
"""

import os
import sys
import pickle

# 프로젝트 루트(ai-risk-navigator)와 backend를 둘 다 path에 추가
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, "backend"))

import numpy as np
import pandas as pd
import lightgbm as lgb

from app.data_sources.kis_client import KISClient
from ml_training.feature_engineering.ta_features import calculate_ta_features
from ml_training.feature_engineering.garch_features import calculate_garch_volatility

REGIME_LABELS = {0: "상승장", 1: "하락장", 2: "횡보장", 3: "고변동장"}


def build_dataset(index_name: str = "코스피") -> pd.DataFrame:
    """
    지수 과거 데이터로부터 피처 + 라벨 데이터셋 생성
    """
    client = KISClient()
    chart_data = client.get_index_daily_chart(index_name, period_days=90)

    items = chart_data.get("output2", [])
    date_close_map = {}
    date_volume_map = {}
    for item in items:
        date = item.get("stck_bsop_date")
        close = item.get("bstp_nmix_prpr")
        volume = item.get("acml_vol")
        if date and close:
            date_close_map[date] = float(close)
            date_volume_map[date] = float(volume) if volume else 0.0

    dates = sorted(date_close_map.keys())
    closes = np.array([date_close_map[d] for d in dates])
    volumes = np.array([date_volume_map[d] for d in dates])

    if len(closes) < 30:
        raise ValueError("데이터가 부족합니다 (최소 30일 필요)")

    # 일간수익률
    returns = np.diff(closes) / closes[:-1]
    returns = np.concatenate([[0], returns])  # 길이 맞추기

    # 기술적지표 피처
    ta_features = calculate_ta_features(closes, volumes)

    # GARCH 변동성 (수익률 최소 길이 필요)
    garch_vol = calculate_garch_volatility(returns[1:])  # 첫 0 제외
    garch_vol = np.concatenate([[np.nan], garch_vol])

    df = pd.DataFrame({
        "date": dates,
        "close": closes,
        "return": returns,
        **ta_features,
        "garch_vol": garch_vol,
    })

    # 사후 라벨링: 향후 5일 수익률+변동성 기준 (데이터가 90일이라 20일 대신 5일로 축소)
    future_window = 5
    df["future_return"] = df["close"].shift(-future_window) / df["close"] - 1
    df["future_vol"] = df["return"].rolling(future_window).std().shift(-future_window)

    def assign_regime(row):
        if pd.isna(row["future_return"]) or pd.isna(row["future_vol"]):
            return np.nan
        vol_threshold = df["return"].std() * 1.5
        if row["future_vol"] > vol_threshold:
            return 3  # 고변동장
        elif row["future_return"] > 0.02:
            return 0  # 상승장
        elif row["future_return"] < -0.02:
            return 1  # 하락장
        else:
            return 2  # 횡보장

    df["regime"] = df.apply(assign_regime, axis=1)
    df = df.dropna()

    return df


def train_regime_model(df: pd.DataFrame):
    """
    LightGBM 다중분류 모델 학습
    """
    feature_cols = [c for c in df.columns if c not in
                     ["date", "close", "future_return", "future_vol", "regime"]]

    X = df[feature_cols]
    y = df["regime"].astype(int)

    train_data = lgb.Dataset(X, label=y)

    params = {
        "objective": "multiclass",
        "num_class": 4,
        "metric": "multi_logloss",
        "verbosity": -1,
        "num_leaves": 15,
        "learning_rate": 0.05,
    }

    model = lgb.train(params, train_data, num_boost_round=50)

    return model, feature_cols


def predict_current_regime(model, feature_cols, df: pd.DataFrame):
    """
    가장 최근 데이터로 현재 국면 예측
    """
    latest = df[feature_cols].iloc[[-1]]
    proba = model.predict(latest)[0]
    predicted_class = int(np.argmax(proba))

    return {
        "predicted_regime": REGIME_LABELS[predicted_class],
        "probabilities": {REGIME_LABELS[i]: round(float(p), 4) for i, p in enumerate(proba)},
    }


if __name__ == "__main__":
    print("데이터셋 구축 중...")
    df = build_dataset("코스피")
    print(f"데이터셋 크기: {len(df)}행")

    print("\n모델 학습 중...")
    model, feature_cols = train_regime_model(df)
    print("학습 완료")

    print("\n현재 국면 예측:")
    result = predict_current_regime(model, feature_cols, df)
    print(f"예측 국면: {result['predicted_regime']}")
    print("클래스별 확률:")
    for regime, prob in result["probabilities"].items():
        print(f"  {regime}: {prob}")

    # 모델 저장
    weights_dir = os.path.join(os.path.dirname(__file__), "..", "backend", "app", "models", "weights")
    os.makedirs(weights_dir, exist_ok=True)
    model_path = os.path.join(weights_dir, "lightgbm_regime_domestic.pkl")
    with open(model_path, "wb") as f:
        pickle.dump({"model": model, "feature_cols": feature_cols}, f)
    print(f"\n모델 저장 완료: {model_path}")