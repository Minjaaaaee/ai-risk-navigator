export default function LedgerRow({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: "default" | "amber" | "teal" | "coral";
}) {
  const toneClass = {
    default: "text-ink",
    amber: "text-amber",
    teal: "text-teal",
    coral: "text-coral",
  }[tone];

  return (
    <div className="flex items-baseline justify-between border-b border-line/60 py-2 last:border-b-0">
      <span className="text-sm text-ink-soft">{label}</span>
      <span className={`font-mono text-sm ${toneClass}`}>{value}</span>
    </div>
  );
}