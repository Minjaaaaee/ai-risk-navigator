import type { Metadata } from "next";
import "./globals.css";
import { pretendard, plexMono } from "./fonts";

export const metadata: Metadata = {
  title: "AI 리스크 내비게이터",
  description: "청년 투자자를 위한 AI 기반 금융 리스크 내비게이터",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="ko"
      className={`${pretendard.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-base text-ink font-sans">
        {children}
      </body>
    </html>
  );
}