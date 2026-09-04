"""
기술2-1(해외) 국면분류 예측 래퍼
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)
sys.path.append(PROJECT_ROOT)

from ml_training.train_lightgbm_regime_overseas import build_dataset_overseas, train_regime_model, predict_current_regime


def get_current_overseas_regime(index_name: str = "나스닥") -> dict:
    """
    현재 해외 시장 국면과 확률 반환
    """
    df = build_dataset_overseas(index_name)
    model, feature_cols = train_regime_model(df)
    result = predict_current_regime(model, feature_cols, df)
    return result