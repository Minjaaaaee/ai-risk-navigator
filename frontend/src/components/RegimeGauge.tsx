const REGIME_POSITION: Record<string, number> = {
  상승장: 90,
  횡보장: 50,
  고변동장: 30,
  하락장: 10,
};

const REGIME_COLOR: Record<string, string> = {
  상승장: "#1E9E8B",
  횡보장: "#D98C2B",
  고변동장: "#D6473C",
  하락장: "#D6473C",
};

function Needle({ label, regimeName }: { label: string; regimeName: string }) {
  const pos = REGIME_POSITION[regimeName] ?? 50;
  const color = REGIME_COLOR[regimeName] ?? "#5B6472";

  return (
    <div className="flex-1">
      <div className="flex items-baseline justify-between font-mono text-xs text-ink-soft">
        <span>{label}</span>
        <span style={{ color }}>{regimeName}</span>
      </div>
      <div className="relative mt-2 h-1.5 w-full bg-line">
        <div
          className="absolute -top-1 h-3.5 w-0.5 -translate-x-1/2 transition-all duration-700"
          style={{ left: `${pos}%`, backgroundColor: color }}
        />
      </div>
      <div className="mt-1 flex justify-between font-mono text-[10px] text-ink-soft/70">
        <span>하락</span>
        <span>횡보</span>
        <span>상승</span>
      </div>
    </div>
  );
}

export default function RegimeGauge({
  regime,
}: {
  regime: {
    domestic: { predicted_regime: string };
    overseas: { predicted_regime: string };
  };
}) {
  return (
    <div className="border border-line bg-panel px-6 py-5">
      <div className="flex gap-8">
        <Needle label="국내" regimeName={regime.domestic.predicted_regime} />
        <Needle label="해외" regimeName={regime.overseas.predicted_regime} />
      </div>
    </div>
  );
}