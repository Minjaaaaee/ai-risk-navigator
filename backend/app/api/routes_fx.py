"""
기술4 - 해외주식 환노출 리스크 경고 API 라우트
"""

from typing import List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.fx_exposure import calculate_fx_exposure
from app.services.regime.fx import get_current_fx_regime
from app.services.fx_scenario import simulate_fx_scenario

router = APIRouter(prefix="/api/fx", tags=["fx"])


class Holding(BaseModel):
    ticker: str
    value_krw: float


class HoldingsRequest(BaseModel):
    holdings: List[Holding]


@router.post("/exposure")
def get_fx_exposure(payload: HoldingsRequest):
    """
    보유종목 리스트 기반 환노출비중 계산 (기술4-1)
    """
    try:
        holdings = [h.model_dump() for h in payload.holdings]
        return calculate_fx_exposure(holdings)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regime")
def get_fx_regime(use_percentile_fallback: bool = Query(False)):
    """
    환율 변동성 국면분류 (기술4-2)
    """
    try:
        return get_current_fx_regime(use_percentile_fallback=use_percentile_fallback)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scenario")
def get_fx_scenario(payload: HoldingsRequest):
    """
    환노출 시나리오 시뮬레이션 + LLM 설명 + 헤지ETF 추천 (기술4-3)
    """
    try:
        holdings = [h.model_dump() for h in payload.holdings]
        return simulate_fx_scenario(holdings)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))