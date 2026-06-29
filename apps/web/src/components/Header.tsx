export default function Header() {
  return (
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
      </div>
    </header>
  );
}
