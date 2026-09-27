import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AURA CYBER-GLASS | Speech Emotion & Behavioral Intelligence Studio",
  description:
    "Spatial neural speech emotion recognition & clinical prosody telemetry platform built with futuristic cyber-glass aesthetics and multi-layer foundation models.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}
    >
      <body className="min-h-full flex flex-col font-sans bg-[#06080d] text-slate-100 selection:bg-[#ccff00] selection:text-black">
        {children}
      </body>
    </html>
  );
}
