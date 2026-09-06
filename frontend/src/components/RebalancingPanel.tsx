"use client";

import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";
import type { RebalancingCard } from "@/lib/api";

export default function RebalancingPanel({ card }: { card: RebalancingCard }) {
  const { current_allocation, recommended_allocation } = card.detail;

  const data = Object.keys(current_allocation).map((key) => ({
    name: key,
    현재: current_allocation[key as keyof typeof current_allocation],
    권장: recommended_allocation[key as keyof typeof recommended_allocation],
  }));

  return (
    <article className="border border-line border-l-2 border-l-amber bg-panel px-6 py-5">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">{card.title}</h2>
        <span className="font-mono text-xs text-amber">
          괴리 {card.max_diff_pp}%p
        </span>
      </div>

      <div className="mt-4 h-40">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 8 }}>
            <XAxis type="number" hide domain={[0, 100]} />
            <YAxis
              type="category"
              dataKey="name"
              width={56}
              tick={{ fontSize: 12, fill: "#5B6472" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              formatter={(v) => `${v}%`}
              contentStyle={{ fontSize: 12, borderRadius: 0 }}
              itemStyle={{ color: "#101826" }}
            />
            <Bar dataKey="현재" fill="#B9C2CD" barSize={8} />
            <Bar dataKey="권장" fill="#D98C2B" barSize={8} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <p className="mt-4 text-sm leading-relaxed text-ink-soft">
        {card.explanation}
      </p>
    </article>
  );
}