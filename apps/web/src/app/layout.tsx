import type { Metadata } from "next";
import { Inter, Hanken_Grotesk, JetBrains_Mono } from "next/font/google";
import Header from "@/components/Header";
import Providers from "@/components/Providers";
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
        <Providers>
          <Header />

          {/* Main */}
          <main className="flex-1">{children}</main>
        </Providers>

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
