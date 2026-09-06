"use client";

import { useState } from "react";
import { summarizeTerms, type TermsSummarizeResult } from "@/lib/api";

export default function TermsPage() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<TermsSummarizeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openChunk, setOpenChunk] = useState<number | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await summarizeTerms(question);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "알 수 없는 오류");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto w-full max-w-2xl px-6 py-12">
      <header className="mb-8">
        <p className="font-mono text-xs tracking-wide text-ink-soft">
          약관·공시 쉬운말 번역
        </p>
        <h1 className="mt-2 text-2xl font-semibold">뭐가 궁금하세요?</h1>
      </header>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="예: 이 상품 위험등급이 어떻게 되나요?"
          className="flex-1 border border-line bg-panel px-4 py-2.5 text-sm outline-none focus:border-amber"
        />
        <button
          type="submit"
          disabled={loading}
          className="border border-ink bg-ink px-5 py-2.5 text-sm font-medium text-base disabled:opacity-40"
        >
          {loading ? "검색 중" : "질문하기"}
        </button>
      </form>

      {loading && (
        <div className="mt-6 border border-line bg-panel px-6 py-8 text-center">
          <p className="font-mono text-xs text-ink-soft">
            관련 공시를 검색하고 답변을 생성하는 중입니다
          </p>
        </div>
      )}

      {error && (
        <div className="mt-6 border border-coral/30 bg-coral/5 px-4 py-3 text-sm text-coral">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-4">
          <article className="border border-line border-l-2 border-l-amber bg-panel px-6 py-5">
            <p className="text-sm leading-relaxed text-ink">{result.answer}</p>
          </article>

          {result.chunks && result.chunks.length > 0 && (
            <div className="border border-line bg-panel">
              <p className="border-b border-line px-6 py-3 font-mono text-xs text-ink-soft">
                근거자료 {result.chunks_found}건
              </p>
              {result.chunks.map((chunk) => (
                <div key={chunk.id} className="border-b border-line/60 last:border-b-0">
                  <button
                    onClick={() =>
                      setOpenChunk(openChunk === chunk.id ? null : chunk.id)
                    }
                    className="flex w-full items-center justify-between px-6 py-3 text-left text-sm"
                  >
                    <span>
                      {chunk.corp_name} · {chunk.report_nm}
                    </span>
                    <span className="font-mono text-xs text-ink-soft">
                      유사도 {chunk.similarity.toFixed(2)}
                    </span>
                  </button>
                  {openChunk === chunk.id && (
                    <p className="px-6 pb-4 text-xs leading-relaxed text-ink-soft">
                      {chunk.content}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </main>
  );
}