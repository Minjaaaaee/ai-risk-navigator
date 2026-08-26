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


if __name__ == "__main__":
    for index_name in ["나스닥", "S&P500"]:
        data = get_index_data(index_name)
        print(f"{index_name}: {data['current_close']} ({data['change_rate_pct']}%)")