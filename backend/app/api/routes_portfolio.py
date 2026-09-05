"""
기술2 - 심플홈, 포트폴리오 최적화, 국면분류 API 라우트
"""

import json

from fastapi import APIRouter, HTTPException, Query

from app.services.simple_home import build_simple_home
from app.services.optimizer import optimize_portfolio
from app.services.regime.domestic import get_current_domestic_regime
from app.services.regime.overseas import get_current_overseas_regime

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


def _parse_allocation(raw: str) -> dict:
    """
    쿼리파라미터로 넘어온 JSON 문자열 배분을 dict로 변환
    예: '{"국내주식":50,"해외주식":20,"채권":20,"현금":10}'
    """
    try:
        return json.loads(raw)
    except Exception:
        raise HTTPException(status_code=422, detail="current_allocation은 유효한 JSON 형식이어야 합니다.")


@router.get("/simple-home")
def get_simple_home(
    risk_profile: str = Query("위험중립형"),
    current_allocation: str = Query(
        '{"국내주식":50,"해외주식":20,"채권":20,"현금":10}',
        description='JSON 문자열, 예: {"국내주식":50,"해외주식":20,"채권":20,"현금":10}',
    ),
    user_profile: str = Query("위험중립형"),
):
    """
    심플홈 카드 통합 (기술2-4)
    """
    try:
        allocation = _parse_allocation(current_allocation)
        return build_simple_home(
            risk_profile=risk_profile,
            current_allocation=allocation,
            user_profile=user_profile,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/optimize")
def get_optimize(
    risk_profile: str = Query("위험중립형"),
    current_allocation: str = Query(
        '{"국내주식":50,"해외주식":20,"채권":20,"현금":10}',
        description='JSON 문자열, 예: {"국내주식":50,"해외주식":20,"채권":20,"현금":10}',
    ),
):
    """
    리밸런싱 배분 산출 (기술2-3)
    """
    try:
        allocation = _parse_allocation(current_allocation)
        return optimize_portfolio(risk_profile=risk_profile, current_allocation=allocation)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regime")
def get_regime():
    """
    국내/해외 시장 국면분류 결과 (기술2-1)
    """
    try:
        domestic = get_current_domestic_regime("코스피")
        overseas = get_current_overseas_regime("나스닥")
        return {"domestic": domestic, "overseas": overseas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))