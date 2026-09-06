import type { IndexCommentary } from "@/lib/api";

export default function IndexCard({
  label,
  data,
}: {
  label: string;
  data: IndexCommentary;
}) {
  const positive = data.change_rate_pct >= 0;
  const price = data.current ?? data.current_close ?? 0;

  return (
    <div className="border border-line bg-panel px-6 py-5">
      <div className="flex items-baseline justify-between">
        <p className="font-mono text-xs text-ink-soft">{label}</p>
        {data.is_event && (
          <span className="font-mono text-[10px] text-coral">급변 이벤트</span>
        )}
      </div>
      <div className="mt-1 flex items-baseline gap-3">
        <span className="font-mono text-2xl">{price.toLocaleString()}</span>
        <span
          className={`font-mono text-sm ${positive ? "text-teal" : "text-coral"}`}
        >
          {positive ? "+" : ""}
          {data.change_rate_pct}%
        </span>
      </div>
      <p className="mt-3 text-sm leading-relaxed text-ink-soft">
        {data.commentary}
      </p>
    </div>
  );
}