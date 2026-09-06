"""
AI 리스크 내비게이터 - FastAPI 앱 진입점
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_index import router as index_router
from app.api.routes_portfolio import router as portfolio_router
from app.api.routes_terms import router as terms_router
from app.api.routes_fx import router as fx_router
from app.batch.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup 시 실행
    start_scheduler()
    print("서버 시작: 스케줄러 등록 완료")

    yield  # 여기서 서버가 실제로 요청을 받기 시작함

    # shutdown 시 실행
    print("서버 종료")


app = FastAPI(title="AI 리스크 내비게이터 API", lifespan=lifespan)

# 프론트엔드(Next.js, 로컬 개발 포트)에서 호출 허용
# 개발 환경에선 Dev Tunnels 및 로컬 접속을 모두 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://txnc2w05-3000.jpe1.devtunnels.ms",
    ],
    allow_origin_regex=r"https://.*\.devtunnels\.ms",
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


# 약관·공시 쉬운말 번역 RAG API 라우트
app.include_router(terms_router)


# 해외주식 환노출 리스크 경고 API
app.include_router(fx_router)