"use client";

import { useEffect, useState, use } from "react";
import { useSearchParams } from "next/navigation";
import { getStockCommentary, type StockCommentary } from "@/lib/api";
import LedgerRow from "@/components/LedgerRow";

export default function StockPage({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  const { code } = use(params);
  const searchParams = useSearchParams();
  const nameFromQuery = searchParams.get("name") ?? undefined;

  const [data, setData] = useState<StockCommentary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;
    setData(null);
    setError(null);

    getStockCommentary(code, nameFromQuery)
      .then((res) => {
        if (ignore) return;
        setData(res);
        setError(null);
      })
      .catch((e) => {
        if (ignore) return;
        setError(e.message);
      });

    return () => {
      ignore = true;
    };
  }, [code, nameFromQuery]);

  const excessTone =
    data && data.excess_return_pct > 0
      ? "teal"
      : data && data.excess_return_pct < 0
      ? "coral"
      : "default";

  return (
    <main className="mx-auto w-full max-w-2xl px-6 py-12">
      <header className="mb-8">
        <p className="font-mono text-xs tracking-wide text-ink-soft">
          종목 코드 {code}
        </p>
        <h1 className="mt-2 text-2xl font-semibold">
          {data ? data.stock_name : "조회 중..."}
        </h1>
      </header>

      {error && (
        <div className="border border-coral/30 bg-coral/5 px-4 py-3 text-sm text-coral">
          데이터를 불러오지 못했습니다: {error}
        </div>
      )}

      {!error && !data && (
        <div className="border border-line bg-panel px-6 py-8 text-center">
          <p className="font-mono text-xs text-ink-soft">
            AI가 관련 뉴스와 시세를 분석하는 중입니다
          </p>
          <p className="mt-1 text-xs text-ink-soft/70">
            처음 조회되는 종목은 최대 1분 정도 걸릴 수 있어요
          </p>
        </div>
      )}

      {data && (
        <div className="border border-line bg-panel px-6 py-5">
          <LedgerRow
            label="오늘 등락률"
            value={`${data.stock_return_pct > 0 ? "+" : ""}${data.stock_return_pct}%`}
            tone={data.stock_return_pct >= 0 ? "teal" : "coral"}
          />
          <LedgerRow label="지수 등락률" value={`${data.index_return_pct}%`} />
          <LedgerRow label="베타" value={`${data.beta}`} />
          <LedgerRow
            label="지수대비 초과수익률"
            value={`${data.excess_return_pct > 0 ? "+" : ""}${data.excess_return_pct}%p`}
            tone={excessTone}
          />

          <div className="mt-5 border-t border-line pt-4">
            <p className="font-mono text-[10px] tracking-wide text-amber">
              AI ANALYSIS
            </p>
            <p className="mt-2 text-sm leading-relaxed text-ink-soft">
              {data.commentary}
            </p>
          </div>
        </div>
      )}
    </main>
  );
}