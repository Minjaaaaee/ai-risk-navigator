"""
기술2-1 - GARCH(1,1) 기반 변동성 클러스터링 피처
"""

import numpy as np
from arch import arch_model


def calculate_garch_volatility(returns: np.ndarray) -> np.ndarray:
    """
    일간수익률(%) 배열로 GARCH(1,1) 조건부변동성 추정
    returns: 소수(0.01=1%)가 아니라 퍼센트 단위(1.0=1%)로 스케일링해서 입력 (GARCH 수렴 안정성)
    """
    returns_pct = returns * 100  # 소수 -> 퍼센트 스케일

    model = arch_model(returns_pct, vol="GARCH", p=1, q=1, rescale=False)
    result = model.fit(disp="off")

    conditional_volatility = result.conditional_volatility
    return conditional_volatility