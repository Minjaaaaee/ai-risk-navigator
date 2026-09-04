"""
기술2-1(국내) 국면분류 예측 래퍼
ml_training의 학습 로직을 재사용해 현재 국면 예측만 간단히 호출
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)
sys.path.append(PROJECT_ROOT)

from ml_training.train_lightgbm_regime import build_dataset, train_regime_model, predict_current_regime


def get_current_domestic_regime(index_name: str = "코스피") -> dict:
    """
    현재 국내 시장 국면과 확률 반환
    """
    df = build_dataset(index_name)
    model, feature_cols = train_regime_model(df)
    result = predict_current_regime(model, feature_cols, df)
    return result