"use client";

import { useEffect, useState } from "react";
import {
  getIndexCommentary,
  getTopMovers,
  type IndexCommentary,
  type TopMoverStock,
} from "@/lib/api";
import IndexCard from "@/components/IndexCard";
import Link from "next/link";

export default function ScanPage() {
  // 1. 코스피 / 나스닥 지수 데이터 state
  const [domestic, setDomestic] = useState<IndexCommentary | null>(null);
  const [overseas, setOverseas] = useState<IndexCommentary | null>(null);

  // 2. 국내 / 해외 이상 움직임 TOP 5 state (기존 movers 제거 후 분리)
  const [domesticMovers, setDomesticMovers] = useState<TopMoverStock[] | null>(null);
  const [overseasMovers, setOverseasMovers] = useState<TopMoverStock[] | null>(null);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;

    Promise.all([
      getIndexCommentary("domestic"),
      getIndexCommentary("overseas"),
      getTopMovers(5, "domestic"),
      getTopMovers(5, "overseas"),
    ])
      .then(([d, o, dm, om]) => {
        if (ignore) return;
        setDomestic(d);
        setOverseas(o);
        setDomesticMovers(dm);
        setOverseasMovers(om);
        setError(null);
      })
      .catch((e) => {
        if (ignore) return;
        setError(e.message);
      });

    return () => {
      ignore = true;
    };
  }, []);

  return (
    <main className="mx-auto w-full max-w-3xl px-6 py-12">
      <header className="mb-10">
        <p className="font-mono text-xs tracking-wide text-ink-soft">
          AI 리스크 내비게이터
        </p>
        <h1 className="mt-2 text-2xl font-semibold">마켓 브리핑</h1>
      </header>

      {error && (
        <div className="border border-coral/30 bg-coral/5 px-4 py-3 text-sm text-coral">
          데이터를 불러오지 못했습니다: {error}
        </div>
      )}

      {!error && (!domestic || !overseas) && (
        <div className="animate-pulse space-y-3">
          <div className="h-32 bg-line/40" />
          <div className="h-32 bg-line/40" />
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {domestic && <IndexCard label="코스피" data={domestic} />}
        {overseas && <IndexCard label="나스닥" data={overseas} />}
      </div>

      {/* 국내 및 해외 TOP 5 섹션 분리 렌더링 */}
      {[
        { label: "국내 이상 움직임 TOP 5", data: domesticMovers },
        { label: "해외 이상 움직임 TOP 5", data: overseasMovers },
      ].map(
        ({ label, data }) =>
          data &&
          data.length > 0 && (
            <section key={label} className="mt-6 border border-line bg-panel">
              <p className="border-b border-line px-6 py-3 font-mono text-xs text-ink-soft">
                {label}
              </p>
              {data.map((m) => (
                <Link
                  key={m.stock_code}
                  href={`/stock/${m.stock_code}?name=${encodeURIComponent(m.stock_name)}`}
                  className="flex items-center justify-between border-b border-line/60 px-6 py-3 text-sm last:border-b-0 hover:bg-line/20"
                >
                  <span>{m.stock_name}</span>
                  <span
                    className={`font-mono text-xs ${
                      m.excess_return_pct >= 0 ? "text-teal" : "text-coral"
                    }`}
                  >
                    {m.excess_return_pct >= 0 ? "+" : ""}
                    {m.excess_return_pct}%p
                  </span>
                </Link>
              ))}
            </section>
          )
      )}
    </main>
  );
}