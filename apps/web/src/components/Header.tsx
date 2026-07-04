"use client";

import { useAuth } from "@/lib/auth";
import Link from "next/link";

export default function Header() {
  const { isAuthenticated, user, signOut } = useAuth();

  return (
    <>
      {/* Flip animation for logo */}
      <style>{`
        @keyframes logoFlip {
          0%, 28%, 100% { transform: rotateY(0deg); }
          33%, 61% { transform: rotateY(120deg); }
          66%, 94% { transform: rotateY(240deg); }
        }
      `}</style>
      <header className="sticky top-0 z-50 flex justify-between items-center h-16 bg-white border-b border-[#E2E8F0] px-6 md:px-10">
      <div className="flex items-center gap-6">
        <Link href="/" className="flex items-center gap-2">
          {/* Flipping logo — alternates between TaxStox and licensed badge every 3s */}
          <span className="inline-block [perspective:200px] w-[180px] h-7">
            <span
              className="relative inline-flex w-full h-full text-center transition-transform duration-500"
              style={{
                transformStyle: "preserve-3d",
                animation: "logoFlip 9s ease-in-out infinite",
                fontFamily: "var(--font-hanken-grotesk)",
              }}
            >
              {/* Front — TaxStox */}
              <span
                className="absolute inset-0 flex items-center justify-center text-xl font-bold tracking-tight text-[#003366]"
                style={{ backfaceVisibility: "hidden" }}
              >
                Tax<span className="text-[#F57C00]">Stox</span>
              </span>
              {/* Face 2 — Licensed badge (120deg) */}
              <span
                className="absolute inset-0 flex items-center justify-center gap-1.5 text-[10px] tracking-wider font-bold text-[#166534] uppercase bg-[#eff4ff] rounded-full px-2"
                style={{
                  backfaceVisibility: "hidden",
                  transform: "rotateY(120deg)",
                  fontFamily: "var(--font-hanken-grotesk)",
                }}
              >
                <span className="material-symbols-outlined text-xs">verified_user</span>
                Licensed by IT Dept.
              </span>
              {/* Face 3 — Bank-Grade Security (240deg) */}
              <span
                className="absolute inset-0 flex items-center justify-center gap-1.5 text-[10px] tracking-wider font-bold text-[#003366] uppercase bg-[#e5eeff] rounded-full px-2"
                style={{
                  backfaceVisibility: "hidden",
                  transform: "rotateY(240deg)",
                  fontFamily: "var(--font-hanken-grotesk)",
                }}
              >
                <span className="material-symbols-outlined text-xs">shield_with_heart</span>
                Bank-Grade Security
              </span>
            </span>
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
    </>
  );
}
