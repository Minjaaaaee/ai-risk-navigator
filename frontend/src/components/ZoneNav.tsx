"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const ZONES = [
  { code: "01", label: "SCAN", ko: "상황판", href: "/" },
  { code: "02", label: "PORTFOLIO", ko: "포트폴리오", href: "/portfolio" },
  { code: "03", label: "TERMS", ko: "약관", href: "/terms" },
  { code: "04", label: "FX", ko: "환노출", href: "/fx-risk" },
];

export default function ZoneNav() {
  const pathname = usePathname();

  return (
    <nav className="w-full border-b border-line bg-panel md:h-screen md:w-56 md:shrink-0 md:border-b-0 md:border-r">
      <div className="px-6 py-6">
        <p className="font-mono text-[11px] tracking-widest text-ink-soft">
          AI RISK NAVIGATOR
        </p>
      </div>

      <div className="flex md:flex-col">
        {ZONES.map((zone) => {
          const active =
            zone.href === "/"
              ? pathname === "/"
              : pathname.startsWith(zone.href);

          return (
            <Link
              key={zone.code}
              href={zone.href}
              className={[
                "flex-1 border-t border-line px-6 py-4 transition-colors md:border-t-0 md:border-l-2",
                active
                  ? "border-l-amber bg-amber/5"
                  : "border-l-transparent hover:bg-line/20",
              ].join(" ")}
            >
              <p
                className={[
                  "font-mono text-[10px] tracking-wide",
                  active ? "text-amber" : "text-ink-soft",
                ].join(" ")}
              >
                {zone.code} · {zone.label}
              </p>
              <p
                className={[
                  "mt-0.5 text-sm",
                  active ? "font-medium text-ink" : "text-ink-soft",
                ].join(" ")}
              >
                {zone.ko}
              </p>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}