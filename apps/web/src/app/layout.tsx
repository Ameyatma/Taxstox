import type { Metadata } from "next";
import { Inter, Hanken_Grotesk, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

const hankenGrotesk = Hanken_Grotesk({
  variable: "--font-hanken-grotesk",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  weight: ["500"],
});

export const metadata: Metadata = {
  title: "TaxStox — File ITR in 2 Minutes. Master Your Stocks.",
  description:
    "Upload Form 16 + AIS. Answer 5 yes/no questions. Download validated, regime-optimized ITR JSON. Built by a 30-year CA and 25-year software engineer.",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${hankenGrotesk.variable} ${jetbrainsMono.variable} h-full antialiased light`}
    >
      <body className="min-h-full flex flex-col bg-[#F8FAFC]">
        {/* Header — matches design system TopAppBar */}
        <header className="sticky top-0 z-50 flex justify-between items-center h-16 bg-white border-b border-[#E2E8F0] px-6 md:px-10">
          <div className="flex items-center gap-6">
            <a href="/" className="flex items-center gap-2">
              <span
                className="text-xl font-bold tracking-tight text-[#003366]"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}
              >
                Tax<span className="text-[#F57C00]">Stox</span>
              </span>
            </a>
            <nav className="hidden md:flex gap-6 ml-4">
              <a
                href="/"
                className="text-sm font-medium text-[#0b1c30] border-b-2 border-[#003366]"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}
              >
                Home
              </a>
              <a
                href="#"
                className="text-sm font-medium text-[#434652] hover:text-[#003366] transition-colors"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}
              >
                How it Works
              </a>
              <a
                href="#"
                className="text-sm font-medium text-[#434652] hover:text-[#003366] transition-colors"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}
              >
                Pricing
              </a>
            </nav>
          </div>
          <div className="flex items-center gap-4">
            {/* Security badge */}
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 bg-[#eff4ff] rounded-full">
              <span className="material-symbols-outlined text-[#166534] text-sm">security</span>
              <span
                className="text-[11px] font-bold text-[#003366] tracking-wider uppercase"
                style={{ fontFamily: "var(--font-hanken-grotesk)" }}
              >
                256-bit SSL
              </span>
            </div>
            <button
              className="bg-[#003366] text-white px-5 py-2 rounded text-sm font-semibold hover:opacity-90 transition-all active:scale-95"
              style={{ fontFamily: "var(--font-hanken-grotesk)" }}
            >
              Start Filing
            </button>
          </div>
        </header>

        {/* Main */}
        <main className="flex-1">{children}</main>

        {/* Footer */}
        <footer className="border-t border-[#E2E8F0] py-5 text-center text-xs text-[#434652] bg-white">
          <div className="max-w-3xl mx-auto px-6 flex flex-col sm:flex-row justify-between items-center gap-3">
            <span
              className="font-bold text-[#003366] tracking-wide uppercase"
              style={{ fontFamily: "var(--font-hanken-grotesk)" }}
            >
              TaxStox
            </span>
            <span>
              &copy; {new Date().getFullYear()} TaxStox. Secured with 256-bit encryption. Licensed by Income Tax Dept.
            </span>
            <div className="flex gap-4">
              <a href="#" className="hover:text-[#003366] transition-colors">Security</a>
              <a href="#" className="hover:text-[#003366] transition-colors">Privacy</a>
              <a href="#" className="hover:text-[#003366] transition-colors">Support</a>
            </div>
          </div>
        </footer>

        {/* Material Symbols */}
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
      </body>
    </html>
  );
}
