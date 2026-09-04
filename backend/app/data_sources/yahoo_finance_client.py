"""
Yahoo Finance API 클라이언트 (yfinance 라이브러리)
기술1-1(해외) - 나스닥/S&P500 지수 시세 조회
"""

import yfinance as yf

INDEX_TICKERS = {
    "나스닥": "^IXIC",
    "S&P500": "^GSPC",
}


def get_index_data(index_name: str = "나스닥", period_days: int = 5) -> dict:
    """
    지수 최근 일별 시세 조회 (전일 대비 등락률 계산용)
    """
    ticker_symbol = INDEX_TICKERS.get(index_name)
    if not ticker_symbol:
        raise ValueError(f"알 수 없는 지수명: {index_name}")

    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period=f"{period_days}d")

    if len(hist) < 2:
        raise ValueError(f"{index_name} 데이터가 충분하지 않습니다.")

    latest = hist.iloc[-1]
    prev = hist.iloc[-2]

    current_close = float(latest["Close"])
    prev_close = float(prev["Close"])
    change_rate = ((current_close - prev_close) / prev_close) * 100

    return {
        "index_name": index_name,
        "current_close": round(current_close, 2),
        "prev_close": round(prev_close, 2),
        "open": round(float(latest["Open"]), 2),
        "high": round(float(latest["High"]), 2),
        "low": round(float(latest["Low"]), 2),
        "change_rate_pct": round(change_rate, 2),
    }


def get_index_history(index_name: str = "나스닥", period: str = "6mo") -> dict:
    """
    지수 과거 일별 시세 조회 (국면분류 학습용, 더 긴 기간)
    period: yfinance 기간 문자열 (예: "3mo", "6mo", "1y")
    """
    ticker_symbol = INDEX_TICKERS.get(index_name)
    if not ticker_symbol:
        raise ValueError(f"알 수 없는 지수명: {index_name}")

    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period=period)

    if len(hist) < 30:
        raise ValueError(f"{index_name} 데이터가 부족합니다 (최소 30일 필요)")

    dates = [d.strftime("%Y%m%d") for d in hist.index]
    closes = hist["Close"].values
    volumes = hist["Volume"].values

    return {
        "dates": dates,
        "closes": closes,
        "volumes": volumes,
    }


def get_asset_history(ticker: str, period: str = "1y") -> dict:
    """
    임의 티커의 과거 일별 시세 조회 (자산배분용 범용 함수)
    """
    t = yf.Ticker(ticker)
    hist = t.history(period=period)

    if len(hist) < 30:
        raise ValueError(f"{ticker} 데이터가 부족합니다")

    dates = [d.strftime("%Y%m%d") for d in hist.index]
    closes = hist["Close"].values

    return {"dates": dates, "closes": closes}


if __name__ == "__main__":
    for index_name in ["나스닥", "S&P500"]:
        data = get_index_data(index_name)
        print(f"{index_name}: {data['current_close']} ({data['change_rate_pct']}%)")