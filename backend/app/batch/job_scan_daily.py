"""
기술1-2 - 전종목 스캐닝 배치 잡
장마감 후 1일 1회 실행: 국내+해외 초과수익률 계산 -> 선별종목 AI코멘터리 생성 -> 캐시 저장
"""

import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.services.selected_stock_commentary import (
    generate_selected_stock_commentary,
    generate_overseas_selected_commentary,
)
from app.db.vectordb import save_top_movers_cache

DEFAULT_TOP_N = 5


def run_scan_daily(top_n: int = DEFAULT_TOP_N):
    trade_date = datetime.now().strftime("%Y%m%d")

    print(f"[{trade_date}] 국내 전종목 스캐닝 배치 시작 (top_n={top_n})")
    domestic_movers = generate_selected_stock_commentary(top_n=top_n)
    save_top_movers_cache(trade_date, top_n, domestic_movers, market="domestic")
    print(f"[{trade_date}] 국내 스캐닝 결과 캐시 저장 완료 ({len(domestic_movers)}건)")

    print(f"[{trade_date}] 해외 전종목 스캐닝 배치 시작 (top_n={top_n})")
    overseas_movers = generate_overseas_selected_commentary(top_n=top_n)
    save_top_movers_cache(trade_date, top_n, overseas_movers, market="overseas")
    print(f"[{trade_date}] 해외 스캐닝 결과 캐시 저장 완료 ({len(overseas_movers)}건)")

    return {"domestic": domestic_movers, "overseas": overseas_movers}


if __name__ == "__main__":
    run_scan_daily()