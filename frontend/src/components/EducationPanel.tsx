import type { EducationCard } from "@/lib/api";

export default function EducationPanel({ card }: { card: EducationCard }) {
  return (
    <article className="border border-line bg-panel px-6 py-5">
      <h2 className="font-semibold text-ink-soft">{card.title}</h2>
      <p className="mt-2 text-sm leading-relaxed text-ink-soft">{card.content}</p>
    </article>
  );
}