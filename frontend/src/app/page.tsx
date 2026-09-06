"use client";

import { useEffect, useState } from "react";
import {
  getSimpleHome,
  getRegime,
  type HomeCard,
  type AllocationMap,
} from "@/lib/api";
import RegimeGauge from "@/components/RegimeGauge";
import RebalancingPanel from "@/components/RebalancingPanel";
import EducationPanel from "@/components/EducationPanel";

const DEFAULT_ALLOCATION: AllocationMap = {
  국내주식: 50,
  해외주식: 20,
  채권: 20,
  현금: 10,
};

export default function HomePage() {
  const [cards, setCards] = useState<HomeCard[] | null>(null);
  const [regime, setRegime] = useState<Awaited<ReturnType<typeof getRegime>> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      getSimpleHome("위험중립형", DEFAULT_ALLOCATION),
      getRegime(),
    ])
      .then(([homeRes, regimeRes]) => {
        setCards(homeRes.cards);
        setRegime(regimeRes);
      })
      .catch((e) => setError(e.message));
  }, []);

  return (
    <main className="mx-auto w-full max-w-3xl px-6 py-12">
      <header className="mb-10">
        <p className="font-mono text-xs tracking-wide text-ink-soft">
          AI 리스크 내비게이터
        </p>
        <h1 className="mt-2 text-2xl font-semibold">현재 항로</h1>
      </header>

      {error && (
        <div className="border border-coral/30 bg-coral/5 px-4 py-3 text-sm text-coral">
          데이터를 불러오지 못했습니다: {error}
        </div>
      )}

      {!error && !regime && (
        <div className="animate-pulse space-y-3">
          <div className="h-24 bg-line/40" />
          <div className="h-40 bg-line/40" />
        </div>
      )}

      {regime && <RegimeGauge regime={regime} />}

      <section className="mt-10 space-y-4">
        {cards?.map((card, i) =>
          card.type === "rebalancing" ? (
            <RebalancingPanel key={i} card={card} />
          ) : (
            <EducationPanel key={i} card={card} />
          )
        )}
      </section>
    </main>
  );
}