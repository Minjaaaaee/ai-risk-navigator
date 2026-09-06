const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail || `API 오류 (${res.status}): ${path}`);
  }
  return res.json();
}

async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => null);
    throw new Error(errBody?.detail || `API 오류 (${res.status}): ${path}`);
  }
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

export interface StockCommentary {
  stock_code: string;
  stock_name: string;
  stock_return_pct: number;
  index_return_pct: number;
  beta: number;
  excess_return_pct: number;
  commentary: string;
}

export function getStockCommentary(code: string, name?: string) {
  const query = name ? `?name=${encodeURIComponent(name)}` : "";
  return apiGet<StockCommentary>(`/api/stock/${code}/commentary${query}`);
}

export interface TermsChunk {
  id: number;
  rcept_no: string;
  corp_name: string;
  report_nm: string;
  chunk_index: number;
  content: string;
  similarity: number;
}

export interface TermsSummarizeResult {
  question: string;
  chunks_found: number;
  chunks?: TermsChunk[];
  answer: string;
}

export function summarizeTerms(question: string, matchCount = 3) {
  return apiPost<TermsSummarizeResult>("/api/terms/summarize", {
    question,
    match_count: matchCount,
  });
}

export interface IndexCommentary {
  index_name: string;
  change_rate_pct: number;
  is_event: boolean;
  direction: string;
  commentary: string;
  // 국내
  current?: number;
  open?: number;
  high?: number;
  low?: number;
  threshold_pct?: number;
  intraday_range_ratio?: number;
  // 해외
  current_close?: number;
  prev_close?: number;
}

export interface TopMoverStock {
  stock_code: string;
  stock_name: string;
  stock_return_pct: number;
  index_return_pct: number;
  beta: number;
  excess_return_pct: number;
  commentary: string;
}

export function getIndexCommentary(market: "domestic" | "overseas") {
  return apiGet<IndexCommentary>(`/api/index/commentary?market=${market}`);
}

export function getTopMovers(limit = 5) {
  return apiGet<TopMoverStock[]>(`/api/index/top-movers?limit=${limit}`);
}