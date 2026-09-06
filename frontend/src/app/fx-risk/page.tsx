"use client";

import { useState } from "react";
import { getFxScenario, type Holding, type FxScenarioResult } from "@/lib/api";
import LedgerRow from "@/components/LedgerRow";

const DEFAULT_HOLDINGS: Holding[] = [
  { ticker: "005930.KS", value_krw: 5000000 },
  { ticker: "069500.KS", value_krw: 3000000 },
  { ticker: "AAPL", value_krw: 4000000 },
  { ticker: "QQQ", value_krw: 3000000 },
];

export default function FxRiskPage() {
  const [holdings, setHoldings] = useState<Holding[]>(DEFAULT_HOLDINGS);
  const [result, setResult] = useState<FxScenarioResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateHolding(index: number, field: keyof Holding, value: string) {
    setHoldings((prev) =>
      prev.map((h, i) =>
        i === index
          ? { ...h, [field]: field === "value_krw" ? Number(value) : value }
          : h
      )
    );
  }

  function addHolding() {
    setHoldings((prev) => [...prev, { ticker: "", value_krw: 0 }]);
  }

  function removeHolding(index: number) {
    setHoldings((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleAnalyze() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await getFxScenario(holdings.filter((h) => h.ticker));
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
          해외주식 환노출 리스크
        </p>
        <h1 className="mt-2 text-2xl font-semibold">보유종목 환노출 진단</h1>
      </header>

      <div className="border border-line bg-panel">
        <div className="border-b border-line px-6 py-3">
          <p className="font-mono text-xs text-ink-soft">보유종목 입력</p>
        </div>
        {holdings.map((h, i) => (
          <div
            key={i}
            className="flex items-center gap-2 border-b border-line/60 px-6 py-3 last:border-b-0"
          >
            <input
              value={h.ticker}
              onChange={(e) => updateHolding(i, "ticker", e.target.value)}
              placeholder="티커 (예: AAPL, 005930.KS)"
              className="flex-1 border border-line px-3 py-1.5 text-sm outline-none focus:border-amber"
            />
            <input
              type="number"
              value={h.value_krw || ""}
              onChange={(e) => updateHolding(i, "value_krw", e.target.value)}
              placeholder="평가액(원)"
              className="w-32 border border-line px-3 py-1.5 text-right font-mono text-sm outline-none focus:border-amber"
            />
            <button
              onClick={() => removeHolding(i)}
              className="px-2 text-ink-soft hover:text-coral"
            >
              ✕
            </button>
          </div>
        ))}
        <div className="px-6 py-3">
          <button
            onClick={addHolding}
            className="font-mono text-xs text-amber hover:underline"
          >
            + 종목 추가
          </button>
        </div>
      </div>

      <button
        onClick={handleAnalyze}
        disabled={loading || holdings.length === 0}
        className="mt-4 w-full border border-ink bg-ink py-2.5 text-sm font-medium text-base disabled:opacity-40"
      >
        {loading ? "분석 중" : "환노출 분석하기"}
      </button>

      {error && (
        <div className="mt-6 border border-coral/30 bg-coral/5 px-4 py-3 text-sm text-coral">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-4">
          <div
            className={`border bg-panel px-6 py-5 ${
              result.exposure.exceeds_threshold
                ? "border-coral/40 border-l-2 border-l-coral"
                : "border-line"
            }`}
          >
            <div className="flex items-center justify-between">
              <p className="font-semibold">환노출 비중</p>
              {result.exposure.exceeds_threshold && (
                <span className="font-mono text-xs text-coral">임계치 초과</span>
              )}
            </div>
            <LedgerRow
              label="환노출 비중"
              value={`${result.exposure.fx_exposure_pct}%`}
              tone={result.exposure.exceeds_threshold ? "coral" : "teal"}
            />
            <LedgerRow
              label="관리 임계치"
              value={`${result.exposure.threshold_pct}%`}
            />
            <LedgerRow
              label="환변동성 국면"
              value={result.fx_regime.predicted_regime}
              tone={
                result.fx_regime.predicted_regime === "안정" ? "teal" : "amber"
              }
            />
          </div>

          <div className="border border-line bg-panel px-6 py-5">
            <p className="font-semibold">
              원/달러 ±{result.scenario.shift_pct}% 시나리오
            </p>
            <LedgerRow
              label={`+${result.scenario.shift_pct}% 시`}
              value={`${result.scenario.impact_up_pct_of_total > 0 ? "+" : ""}${
                result.scenario.impact_up_pct_of_total
              }%`}
              tone="teal"
            />
            <LedgerRow
              label={`-${result.scenario.shift_pct}% 시`}
              value={`${result.scenario.impact_down_pct_of_total}%`}
              tone="coral"
            />
          </div>

          {result.hedge_recommendations && result.hedge_recommendations.length > 0 && (
            <div className="border border-line bg-panel px-6 py-5">
              <p className="font-semibold">환헤지 ETF 대안</p>
              <div className="mt-3 space-y-2">
                {result.hedge_recommendations.map((etf, i) => (
                  <div key={i} className="text-sm">
                    <span className="font-medium">{etf.name}</span>
                    <span className="ml-2 text-ink-soft">{etf.note}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="border border-line border-l-2 border-l-amber bg-panel px-6 py-5">
            <p className="text-sm leading-relaxed text-ink-soft">
              {result.explanation}
            </p>
          </div>
        </div>
      )}
    </main>
  );
}