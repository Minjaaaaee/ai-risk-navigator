"""
기술3 - 약관·공시 쉬운말 번역 RAG API 라우트
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.rag.retrieve import search
from app.services.llm_explain import summarize_chunks
from app.db.vectordb import fetch_chunks_by_rcept_no

router = APIRouter(prefix="/api/terms", tags=["terms"])


class SummarizeRequest(BaseModel):
    question: str
    match_count: int = 3
    rcept_no: Optional[str] = None  # 특정 공시로 검색 범위 좁히고 싶을 때 지정


@router.post("/summarize")
def summarize_terms(payload: SummarizeRequest):
    """
    질문에 관련된 공시 청크를 검색하고 쉬운말로 요약 생성 (기술3)
    rcept_no를 넘기면 해당 공시 내에서만 검색, 안 넘기면 전체 대상 검색
    """
    try:
        chunks = search(
            payload.question,
            match_count=payload.match_count,
            filter_rcept_no=payload.rcept_no,
        )

        if not chunks:
            return {
                "question": payload.question,
                "chunks_found": 0,
                "answer": "검색된 근거자료가 없습니다.",
            }

        answer = summarize_chunks(payload.question, chunks)

        return {
            "question": payload.question,
            "chunks_found": len(chunks),
            "chunks": chunks,
            "answer": answer,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chunks/{rcept_no}")
def get_chunks_by_rcept_no(rcept_no: str):
    """
    특정 공시(rcept_no)의 저장된 청크 목록 조회 (디버깅/확인용)
    """
    try:
        chunks = fetch_chunks_by_rcept_no(rcept_no)
        return {"rcept_no": rcept_no, "chunk_count": len(chunks), "chunks": chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))