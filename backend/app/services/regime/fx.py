"""
기술4-2 국면분류 예측 래퍼
ml_training의 학습 로직을 재사용해 현재 환변동성 국면 예측만 간단히 호출
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)
sys.path.append(PROJECT_ROOT)

from ml_training.train_lightgbm_fx_regime import (
    build_dataset_fx,
    train_fx_regime_model,
    predict_current_fx_regime,
    predict_percentile_based_regime,
)


def get_current_fx_regime(use_percentile_fallback: bool = False) -> dict:
    """
    현재 환변동성 국면과 확률 반환
    use_percentile_fallback=True면 LightGBM 대신 백분위수 방식 사용
    """
    df = build_dataset_fx()

    if use_percentile_fallback:
        return predict_percentile_based_regime(df)

    model, feature_cols = train_fx_regime_model(df)
    return predict_current_fx_regime(model, feature_cols, df)