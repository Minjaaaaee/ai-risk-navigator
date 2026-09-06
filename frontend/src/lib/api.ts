const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API 오류 (${res.status}): ${path}`);
  return res.json();
}

async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API 오류 (${res.status}): ${path}`);
  return res.json();
}

export interface AllocationMap {
  국내주식: number;
  해외주식: number;
  채권: number;
  현금: number;
}

export interface RebalancingCard {
  priority: number;
  type: "rebalancing";
  title: string;
  max_diff_pp: number;
  detail: {
    risk_profile: string;
    recommended_allocation: AllocationMap;
    current_allocation: AllocationMap;
    allocation_diff: AllocationMap;
    expected_annual_return: number;
    annual_volatility: number;
  };
  explanation: string;
}

export interface EducationCard {
  priority: number;
  type: "education";
  title: string;
  content: string;
}

export type HomeCard = RebalancingCard | EducationCard;

export function getSimpleHome(riskProfile: string, currentAllocation: AllocationMap) {
  const query = new URLSearchParams({
    risk_profile: riskProfile,
    current_allocation: JSON.stringify(currentAllocation),
    user_profile: riskProfile,
  });
  return apiGet<{ cards: HomeCard[] }>(`/api/portfolio/simple-home?${query}`);
}

export function getRegime() {
  return apiGet<{
    domestic: { predicted_regime: string; probabilities: Record<string, number> };
    overseas: { predicted_regime: string; probabilities: Record<string, number> };
  }>("/api/portfolio/regime");
}