import type { Metadata } from "next";
import { JetBrains_Mono, Outfit } from "next/font/google";
import Link from "next/link";
import { REPO } from "@/lib/data";
import "./globals.css";

const sans = Outfit({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  variable: "--font-sans",
  display: "swap",
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Pattern Bank · Core Algorithms for LeetCode",
  description:
    "1,170 coding-interview problems organised by pattern. Every solution runs, " +
    "every solution is reached, and a sample is checked against independent references.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable}`}>
      <body>
        <header className="masthead">
          <div className="shell">
            <Link href="/" className="wordmark">
              <span className="dotmark" aria-hidden="true" />
              Pattern Bank
            </Link>
            <nav>
              <a href={`${REPO}#testing`}>How it&rsquo;s verified</a>
              <a href={REPO}>Source</a>
            </nav>
          </div>
        </header>
        <main>{children}</main>
        <footer className="foot shell">
          <span>Built by Shivani Bokka</span>
          <span>
            Generated from the notebooks in{" "}
            <a href={REPO}>Core-algorithms-for-Leetcode</a>
          </span>
        </footer>
      </body>
    </html>
  );
}
