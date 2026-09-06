"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { AllocationMap } from "@/lib/api";

const RISK_PROFILES = ["안정형", "안정추구형", "위험중립형", "적극투자형", "공격투자형"];

const ASSET_KEYS: (keyof AllocationMap)[] = ["국내주식", "해외주식", "채권", "현금"];

export default function OnboardingPage() {
  const router = useRouter();
  const [riskProfile, setRiskProfile] = useState("위험중립형");
  const [allocation, setAllocation] = useState<AllocationMap>({
    국내주식: 50,
    해외주식: 20,
    채권: 20,
    현금: 10,
  });

  function updateAllocation(key: keyof AllocationMap, value: string) {
    setAllocation((prev) => ({ ...prev, [key]: Number(value) || 0 }));
  }

  const total = Object.values(allocation).reduce((a, b) => a + b, 0);

  function handleSubmit() {
    localStorage.setItem(
      "riskProfile",
      JSON.stringify({ riskProfile, allocation })
    );
    router.push("/portfolio");
  }

  return (
    <main className="mx-auto w-full max-w-2xl px-6 py-12">
      <header className="mb-8">
        <p className="font-mono text-xs tracking-wide text-ink-soft">
          투자 프로필 설정
        </p>
        <h1 className="mt-2 text-2xl font-semibold">
          투자 성향을 알려주세요
        </h1>
      </header>

      <div className="border border-line bg-panel px-6 py-5">
        <p className="font-mono text-xs text-ink-soft">리스크 프로필</p>
        <div className="mt-3 grid grid-cols-5 gap-2">
          {RISK_PROFILES.map((profile) => (
            <button
              key={profile}
              onClick={() => setRiskProfile(profile)}
              className={`border px-2 py-2.5 text-xs transition-colors ${
                riskProfile === profile
                  ? "border-amber bg-amber/10 font-medium text-amber"
                  : "border-line text-ink-soft hover:bg-line/20"
              }`}
            >
              {profile}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-4 border border-line bg-panel px-6 py-5">
        <div className="flex items-baseline justify-between">
          <p className="font-mono text-xs text-ink-soft">현재 보유 배분 (%)</p>
          <p
            className={`font-mono text-xs ${
              total === 100 ? "text-teal" : "text-coral"
            }`}
          >
            합계 {total}%
          </p>
        </div>
        <div className="mt-3 space-y-3">
          {ASSET_KEYS.map((key) => (
            <div key={key} className="flex items-center justify-between">
              <span className="text-sm text-ink-soft">{key}</span>
              <input
                type="number"
                value={allocation[key]}
                onChange={(e) => updateAllocation(key, e.target.value)}
                className="w-24 border border-line px-3 py-1.5 text-right font-mono text-sm outline-none focus:border-amber"
              />
            </div>
          ))}
        </div>
      </div>

      <button
        onClick={handleSubmit}
        disabled={total !== 100}
        className="mt-4 w-full border border-ink bg-ink py-2.5 text-sm font-medium text-base disabled:opacity-40"
      >
        저장하고 포트폴리오 보기
      </button>
    </main>
  );
}