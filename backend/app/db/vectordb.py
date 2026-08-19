"""
Supabase(pgvector) 연결 및 문서 청크 저장/조회 모듈
기술3 - 약관/공시 RAG의 벡터DB 계층
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL / SUPABASE_KEY가 설정되지 않았습니다. backend/.env를 확인하세요.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def insert_chunks(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    청크 리스트를 document_chunks 테이블에 저장
    chunks 각 항목 형태:
    {
        "rcept_no": str,
        "corp_name": str,
        "report_nm": str,
        "chunk_index": int,
        "content": str,
        "embedding": List[float]
    }
    """
    client = get_supabase_client()
    result = client.table("document_chunks").insert(chunks).execute()
    return result.data


def fetch_chunks_by_rcept_no(rcept_no: str) -> List[Dict[str, Any]]:
    """
    특정 공시(rcept_no)의 저장된 청크들을 다시 조회 (저장 확인용)
    """
    client = get_supabase_client()
    result = (
        client.table("document_chunks")
        .select("id, rcept_no, corp_name, chunk_index, content")
        .eq("rcept_no", rcept_no)
        .order("chunk_index")
        .execute()
    )
    return result.data