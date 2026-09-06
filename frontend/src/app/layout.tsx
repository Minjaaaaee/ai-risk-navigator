import type { Metadata } from "next";
import "./globals.css";
import { pretendard, plexMono } from "./fonts";
import ZoneNav from "@/components/ZoneNav";
import TickerBar from "@/components/TickerBar";
import StockSearchBar from "@/components/StockSearchBar";

export const metadata: Metadata = {
  title: "AI 리스크 내비게이터",
  description: "투자자를 위한 AI 기반 금융 리스크 분석 플랫폼",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="ko"
      className={`${pretendard.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-base text-ink font-sans">
        <TickerBar />
        <div className="md:flex">
          <ZoneNav />
          <div className="flex-1">
            <div className="flex justify-end px-6 py-3">
              <StockSearchBar />
            </div>
            {children}
          </div>
        </div>
      </body>
    </html>
  );
}