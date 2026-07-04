"use client";

import { useAuth } from "@/lib/auth";
import Link from "next/link";

export default function Header() {
  const { isAuthenticated, user, signOut } = useAuth();

  return (
    <header className="sticky top-0 z-50 flex justify-between items-center h-16 bg-white border-b border-[#E2E8F0] px-6 md:px-10">
      <div className="flex items-center gap-6">
        <Link href="/" className="flex items-center gap-2">
          <span
            className="text-xl font-bold tracking-tight text-[#003366]"
            style={{ fontFamily: "var(--font-hanken-grotesk)" }}
          >
            Tax<span className="text-[#F57C00]">Stox</span>
          </span>
        </Link>
        <nav className="hidden md:flex gap-6 ml-4">
          <Link
            href="/"
            className="text-sm font-medium text-[#0b1c30] border-b-2 border-[#003366]"
            style={{ fontFamily: "var(--font-hanken-grotesk)" }}
          >
            Home
          </Link>
          {isAuthenticated && (
            <Link
              href="/dashboard"
              className="text-sm font-medium text-[#434652] hover:text-[#003366] transition-colors"
              style={{ fontFamily: "var(--font-hanken-grotesk)" }}
            >
              Dashboard
            </Link>
          )}
          <Link
            href="/#how-it-works"
            className="text-sm font-medium text-[#434652] hover:text-[#003366] transition-colors"
            style={{ fontFamily: "var(--font-hanken-grotesk)" }}
          >
            How it Works
          </Link>
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

        {isAuthenticated ? (
          <div className="flex items-center gap-3">
            <Link
              href="/settings"
              className="material-symbols-outlined text-[#434652] hover:text-[#003366] transition-colors"
              title="Settings"
            >
              settings
            </Link>
            <span className="text-sm font-medium text-[#0b1c30] hidden md:inline" style={{ fontFamily: "var(--font-hanken-grotesk)" }}>
              {user?.name?.split(" ")[0]}
            </span>
            <button
              onClick={signOut}
              className="text-[11px] font-bold text-[#434652] uppercase tracking-wider hover:text-[#991B1B] transition-colors"
              style={{ fontFamily: "var(--font-hanken-grotesk)" }}
            >
              Sign Out
            </button>
          </div>
        ) : (
          <Link
            href="/auth"
            className="bg-[#003366] text-white px-5 py-2 rounded-lg text-sm font-bold hover:opacity-90 transition-all"
            style={{ fontFamily: "var(--font-hanken-grotesk)" }}
          >
            Sign In
          </Link>
        )}
      </div>
    </header>
  );
}
