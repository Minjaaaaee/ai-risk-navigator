"""
기술2-1 - 국면분류용 기술적지표 피처 엔지니어링
이동평균이격도, RSI, MACD 계산 (ta-lib 사용)
"""

import numpy as np
import talib


def calculate_ta_features(closes: np.ndarray, volumes: np.ndarray) -> dict:
    """
    종가/거래량 배열로부터 기술적지표 피처 계산
    closes, volumes: 날짜 오름차순 정렬된 numpy 배열
    """
    features = {}

    # 이동평균이격도 (현재가 - 이동평균) / 이동평균 * 100
    for period in [5, 20, 60]:
        ma = talib.SMA(closes, timeperiod=period)
        disparity = (closes - ma) / ma * 100
        features[f"disparity_{period}"] = disparity

    # RSI
    features["rsi"] = talib.RSI(closes, timeperiod=14)

    # MACD
    macd, macd_signal, macd_hist = talib.MACD(closes, fastperiod=12, slowperiod=26, signalperiod=9)
    features["macd"] = macd
    features["macd_signal"] = macd_signal
    features["macd_hist"] = macd_hist

    # 거래량 변화율
    features["volume_change_pct"] = np.diff(volumes, prepend=volumes[0]) / (volumes + 1e-9) * 100

    return features