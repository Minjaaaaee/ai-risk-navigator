import localFont from "next/font/local";
import { IBM_Plex_Mono } from "next/font/google";

// Pretendard는 로컬 폰트 파일이 필요합니다.
// https://github.com/orioncactus/pretendard 에서 PretendardVariable.woff2를 받아
// frontend/src/app/fonts/PretendardVariable.woff2 에 저장하세요.
export const pretendard = localFont({
  src: "./fonts/PretendardVariable.woff2",
  variable: "--font-pretendard",
  weight: "45 920",
});

export const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-plex-mono",
});