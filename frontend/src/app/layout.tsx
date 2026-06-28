import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "TaxStox — File ITR in 2 Minutes. Master Your Stocks.",
  description:
    "Upload Form 16 + AIS. Answer 5 yes/no questions. Download validated, regime-optimized ITR JSON. Built by a 30-year CA and 25-year software engineer.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-gradient-to-b from-white to-emerald-50/30">
        {/* Header */}
        <header className="border-b border-emerald-100 bg-white/80 backdrop-blur">
          <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
            <a href="/" className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight text-emerald-700">
                Tax<span className="text-gray-900">Stox</span>
              </span>
            </a>
            <span className="text-xs text-gray-400 font-medium">
              ITR · Stocks · Portfolio
            </span>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1">{children}</main>

        {/* Footer */}
        <footer className="border-t border-gray-100 py-6 text-center text-xs text-gray-400">
          TaxStox &copy; {new Date().getFullYear()} &mdash; Built with 30+ years of CA &amp; software engineering experience.
        </footer>
      </body>
    </html>
  );
}
