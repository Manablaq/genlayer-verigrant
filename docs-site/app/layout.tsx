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
  title: "VeriGrant Documentation",
  description:
    "Developer documentation for VeriGrant, a GenLayer Intelligent Contract for AI-reviewed milestone grants and escrow-safe payouts.",
  openGraph: {
    title: "VeriGrant Documentation",
    description:
      "AI-reviewed milestone grants for GenLayer builders, with escrow accounting and Bradbury-tested payout paths.",
    images: ["/og.png"],
  },
  twitter: {
    card: "summary_large_image",
    title: "VeriGrant Documentation",
    description:
      "AI-reviewed milestone grants for GenLayer builders, with escrow accounting and Bradbury-tested payout paths.",
    images: ["/og.png"],
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
