"use client";

import { useEffect, useState } from "react";
import { getIndexCommentary, type IndexCommentary } from "@/lib/api";

export default function TickerBar() {
  const [domestic, setDomestic] = useState<IndexCommentary | null>(null);
  const [overseas, setOverseas] = useState<IndexCommentary | null>(null);

  useEffect(() => {
    let ignore = false;
    Promise.all([
      getIndexCommentary("domestic"),
      getIndexCommentary("overseas"),
    ])
      .then(([d, o]) => {
        if (ignore) return;
        setDomestic(d);
        setOverseas(o);
      })
      .catch(() => {});
    return () => {
      ignore = true;
    };
  }, []);

  function fmt(label: string, data: IndexCommentary | null) {
    if (!data) return `${label} —`;
    const price = data.current ?? data.current_close ?? 0;
    const sign = data.change_rate_pct >= 0 ? "+" : "";
    return `${label} ${price.toLocaleString()} (${sign}${data.change_rate_pct}%)`;
  }

  return (
    <div className="overflow-hidden border-b border-line bg-ink py-1.5">
      <div className="animate-ticker whitespace-nowrap font-mono text-xs text-base/90">
        <span className="mx-8">{fmt("KOSPI", domestic)}</span>
        <span className="mx-8">{fmt("NASDAQ", overseas)}</span>
        <span className="mx-8">{fmt("KOSPI", domestic)}</span>
        <span className="mx-8">{fmt("NASDAQ", overseas)}</span>
      </div>
    </div>
  );
}