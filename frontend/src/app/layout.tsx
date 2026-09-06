import type { Metadata } from "next";
import "./globals.css";
import { pretendard, plexMono } from "./fonts";
import ZoneNav from "@/components/ZoneNav";

export const metadata: Metadata = {
  title: "AI 리스크 내비게이터",
  description: "투자자를 위한 AI 기반 금융 리스크 내비게이터",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="ko"
      className={`${pretendard.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-base text-ink font-sans md:flex">
        <ZoneNav />
        <div className="flex-1">{children}</div>
      </body>
    </html>
  );
}