"""
AI 리스크 내비게이터 - FastAPI 앱 진입점
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_index import router as index_router
from app.api.routes_portfolio import router as portfolio_router

app = FastAPI(title="AI 리스크 내비게이터 API")

# 프론트엔드(Next.js, 로컬 개발 포트)에서 호출 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 나중에 배포 URL 추가
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "message": "AI 리스크 내비게이터 API"}


# 지수/종목 코멘터리 라우터 등록
app.include_router(index_router)


# 심플홈, 포트폴리오 최적화, 국면분류 API
app.include_router(portfolio_router)