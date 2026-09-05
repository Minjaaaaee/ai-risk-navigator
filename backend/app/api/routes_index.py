"""
기술1 - 지수/종목 코멘터리, 브리핑 API 라우트
"""

from fastapi import APIRouter, HTTPException, Query

from datetime import datetime
from app.db.vectordb import get_cached_top_movers
from app.services.commentary import generate_index_commentary
from app.services.commentary_overseas import generate_overseas_commentary
from app.services.selected_stock_commentary import generate_selected_stock_commentary
from app.services.ondemand_stock_commentary import get_stock_commentary
from app.services.excess_return import SAMPLE_STOCKS

router = APIRouter(prefix="/api", tags=["index"])


@router.get("/index/commentary")
def get_index_commentary(market: str = Query("domestic", enum=["domestic", "overseas"])):
    """
    지수레벨 코멘터리 (기술1-1)
    """
    try:
        if market == "domestic":
            return generate_index_commentary()
        else:
            return generate_overseas_commentary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index/top-movers")
def get_top_movers(limit: int = Query(5, ge=1, le=30)):
    """
    전종목 스캐닝 이상 움직임 종목 TOP N (기술1-2) - 배치 캐시 조회 전용
    """
    trade_date = datetime.now().strftime("%Y%m%d")
    try:
        cached = get_cached_top_movers(trade_date, limit)
        if cached is None:
            raise HTTPException(
                status_code=503,
                detail="오늘자 스캐닝 결과가 아직 준비되지 않았습니다. 배치 작업(job_scan_daily.py) 실행 후 다시 시도해주세요."
            )
        return cached
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{code}/commentary")
def get_stock_commentary_route(code: str, name: str = Query(None)):
    """
    종목페이지 온디맨드 코멘터리 (기술1-4, 캐싱 포함)
    """
    try:
        stock_name = name or SAMPLE_STOCKS.get(code, f"종목({code})")
        return get_stock_commentary(stock_code=code, stock_name=stock_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))