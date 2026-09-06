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
  const [domestic, setDomestic] = useState<IndexCommentary | null>(null);
  const [overseas, setOverseas] = useState<IndexCommentary | null>(null);
  const [movers, setMovers] = useState<TopMoverStock[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;

    Promise.all([
      getIndexCommentary("domestic"),
      getIndexCommentary("overseas"),
      getTopMovers(5),
    ])
      .then(([d, o, m]) => {
        if (ignore) return;
        setDomestic(d);
        setOverseas(o);
        setMovers(m);
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

      {movers && movers.length > 0 && (
        <section className="mt-6 border border-line bg-panel">
          <p className="border-b border-line px-6 py-3 font-mono text-xs text-ink-soft">
            오늘의 이상 움직임 TOP {movers.length}
          </p>
          {movers.map((m) => (
            <Link
              key={m.stock_code}
              href={`/stock/${m.stock_code}`}
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
      )}
    </main>
  );
}