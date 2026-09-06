"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { STOCK_DIRECTORY } from "@/lib/stockDirectory";

export default function StockSearchBar() {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  const results =
    query.length > 0
      ? STOCK_DIRECTORY.filter(
          (s) => s.name.includes(query) || s.code.includes(query)
        ).slice(0, 8)
      : [];

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  function handleSelect(code: string, name: string) {
    router.push(`/stock/${code}?name=${encodeURIComponent(name)}`);
    setQuery("");
    setOpen(false);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.nativeEvent.isComposing) return; // 한글 조합 중 Enter는 무시

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, results.length - 1));
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
      return;
    }
    if (e.key === "Enter") {
      e.preventDefault();
      const currentValue = e.currentTarget.value; // state 말고 실제 input의 현재 값
      const freshResults = STOCK_DIRECTORY.filter(
        (s) => s.name.includes(currentValue) || s.code.includes(currentValue)
      ).slice(0, 8);
      const pick = freshResults[activeIndex] ?? freshResults[0];
      if (pick) handleSelect(pick.code, pick.name);
    }
  }

  return (
    <div ref={containerRef} className="relative w-full max-w-sm">
      <input
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setActiveIndex(0);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={handleKeyDown}
        placeholder="종목명 또는 코드 검색"
        className="w-full border border-line bg-panel px-4 py-2 text-sm outline-none focus:border-amber"
      />

      {open && results.length > 0 && (
        <div className="absolute left-0 right-0 top-full z-40 mt-1 border border-line bg-panel shadow-lg">
          {results.map((s, i) => (
            <button
              key={s.code}
              onClick={() => handleSelect(s.code, s.name)}
              onMouseEnter={() => setActiveIndex(i)}
              className={`flex w-full items-center justify-between px-4 py-2.5 text-left text-sm ${
                i === activeIndex ? "bg-amber/10" : ""
              }`}
            >
              <span className="flex items-center gap-2">
                <span className="font-mono text-[10px] text-ink-soft/70">
                  {s.exchange}
                </span>
                <span>{s.name}</span>
              </span>
              <span className="font-mono text-xs text-ink-soft">{s.code}</span>
            </button>
          ))}
        </div>
      )}

      {open && query.length > 0 && results.length === 0 && (
        <div className="absolute left-0 right-0 top-full z-40 mt-1 border border-line bg-panel px-4 py-3 text-sm text-ink-soft shadow-lg">
          검색 결과가 없습니다
        </div>
      )}
    </div>
  );
}