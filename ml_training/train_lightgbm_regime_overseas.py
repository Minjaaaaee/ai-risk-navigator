"""
기술2-1(해외) - 나스닥/S&P500 국면분류 모델 학습
국내와 동일 구조, 데이터소스만 Yahoo Finance로 교체
"""

import os
import sys
import pickle

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, "backend"))

import numpy as np
import pandas as pd
import lightgbm as lgb

from app.data_sources.yahoo_finance_client import get_index_history
from ml_training.feature_engineering.ta_features import calculate_ta_features
from ml_training.feature_engineering.garch_features import calculate_garch_volatility

REGIME_LABELS = {0: "상승장", 1: "하락장", 2: "횡보장", 3: "고변동장"}


def build_dataset_overseas(index_name: str = "나스닥") -> pd.DataFrame:
    """
    해외 지수 과거 데이터로부터 피처 + 라벨 데이터셋 생성 (국내와 동일 로직)
    """
    history = get_index_history(index_name, period="6mo")

    dates = history["dates"]
    closes = np.array(history["closes"])
    volumes = np.array(history["volumes"])

    returns = np.diff(closes) / closes[:-1]
    returns = np.concatenate([[0], returns])

    ta_features = calculate_ta_features(closes, volumes)

    garch_vol = calculate_garch_volatility(returns[1:])
    garch_vol = np.concatenate([[np.nan], garch_vol])

    df = pd.DataFrame({
        "date": dates,
        "close": closes,
        "return": returns,
        **ta_features,
        "garch_vol": garch_vol,
    })

    future_window = 5
    df["future_return"] = df["close"].shift(-future_window) / df["close"] - 1
    df["future_vol"] = df["return"].rolling(future_window).std().shift(-future_window)

    def assign_regime(row):
        if pd.isna(row["future_return"]) or pd.isna(row["future_vol"]):
            return np.nan
        vol_threshold = df["return"].std() * 1.5
        if row["future_vol"] > vol_threshold:
            return 3
        elif row["future_return"] > 0.02:
            return 0
        elif row["future_return"] < -0.02:
            return 1
        else:
            return 2

    df["regime"] = df.apply(assign_regime, axis=1)
    df = df.dropna()

    return df


def train_regime_model(df: pd.DataFrame):
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
    latest = df[feature_cols].iloc[[-1]]
    proba = model.predict(latest)[0]
    predicted_class = int(np.argmax(proba))

    return {
        "predicted_regime": REGIME_LABELS[predicted_class],
        "probabilities": {REGIME_LABELS[i]: round(float(p), 4) for i, p in enumerate(proba)},
    }


if __name__ == "__main__":
    for index_name in ["나스닥", "S&P500"]:
        print(f"\n{'=' * 50}")
        print(f"{index_name} 국면분류")
        print("=" * 50)

        df = build_dataset_overseas(index_name)
        print(f"데이터셋 크기: {len(df)}행")

        model, feature_cols = train_regime_model(df)

        result = predict_current_regime(model, feature_cols, df)
        print(f"예측 국면: {result['predicted_regime']}")
        for regime, prob in result["probabilities"].items():
            print(f"  {regime}: {prob}")

        weights_dir = os.path.join(PROJECT_ROOT, "backend", "app", "models", "weights")
        os.makedirs(weights_dir, exist_ok=True)
        safe_name = "nasdaq" if index_name == "나스닥" else "sp500"
        model_path = os.path.join(weights_dir, f"lightgbm_regime_overseas_{safe_name}.pkl")
        with open(model_path, "wb") as f:
            pickle.dump({"model": model, "feature_cols": feature_cols}, f)
        print(f"모델 저장 완료: {model_path}")