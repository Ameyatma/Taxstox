'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface SearchResult {
  symbol: string;
  company_name: string;
  exchange: string;
  sector: string;
  industry: string;
}

async function searchStocks(query: string): Promise<SearchResult[]> {
  if (!query.trim()) return [];
  const res = await fetch(
    `/api/v1/market/stocks/search?q=${encodeURIComponent(query)}&limit=8`
  );
  if (!res.ok) return [];
  return res.json();
}

export default function StockSearchBar() {
  const router = useRouter();
  const [symbol, setSymbol] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Debounced search — the backend ranks results best-match-first, so typing
  // "MAHINDRA" resolves to "M&M.NS" rather than failing on the raw string.
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const q = symbol.trim();
    if (!q) {
      setResults([]);
      setOpen(false);
      return;
    }
    setLoading(true);
    debounceRef.current = setTimeout(async () => {
      try {
        const hits = await searchStocks(q);
        setResults(hits);
        setActiveIndex(0);
        setOpen(hits.length > 0);
      } catch (err) {
        console.error('Stock search failed:', err);
        setResults([]);
        setOpen(false);
      } finally {
        setLoading(false);
      }
    }, 250);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [symbol]);

  function navigateTo(symbol: string) {
    const normalized = symbol.trim().toUpperCase();
    if (normalized) {
      router.push(`/terminal/asset/${normalized}`);
      setSymbol('');
      setResults([]);
      setOpen(false);
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Prefer the active (highlighted) dropdown result so "MAHINDRA" resolves
    // to its canonical ticker instead of hitting the asset endpoint raw.
    const chosen = results[activeIndex]?.symbol ?? symbol;
    navigateTo(chosen);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!open || results.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((i) => (i + 1) % results.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((i) => (i - 1 + results.length) % results.length);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      navigateTo(results[activeIndex].symbol);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setResults([]);
      setOpen(false);
      inputRef.current?.blur();
    }
  };

  return (
    <div className="relative">
      <form onSubmit={handleSubmit} className="flex flex-row gap-2">
        <Input
          ref={inputRef}
          placeholder="Search by symbol or company name (e.g., MAHINDRA, HDFC)"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (results.length > 0) setOpen(true);
          }}
          className="flex-1"
        />
        <Button variant="default" type="submit">
          Search
        </Button>
      </form>

      {open && (
        <ul
          ref={listRef}
          className="absolute z-50 mt-1 w-full max-w-md rounded-md border border-border bg-card shadow-lg overflow-hidden"
        >
          {loading && (
            <li className="px-4 py-3 text-sm text-muted-foreground">
              Searching…
            </li>
          )}
          {!loading &&
            results.map((r, i) => (
              <li key={r.symbol}>
                <button
                  type="button"
                  className={`w-full text-left px-4 py-2.5 flex items-center justify-between gap-2 hover:bg-muted transition-colors ${
                    i === activeIndex ? 'bg-muted' : ''
                  }`}
                  onMouseEnter={() => setActiveIndex(i)}
                  onClick={() => navigateTo(r.symbol)}
                >
                  <span className="flex flex-col">
                    <span className="font-medium text-foreground">
                      {r.symbol}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {r.company_name}
                    </span>
                  </span>
                  <span className="text-[10px] uppercase tracking-wide text-muted-foreground whitespace-nowrap">
                    {r.exchange} · {r.sector}
                  </span>
                </button>
              </li>
            ))}
          {!loading && results.length === 0 && symbol.trim() && (
            <li className="px-4 py-3 text-sm text-muted-foreground">
              No matches found for &ldquo;{symbol}&rdquo;
            </li>
          )}
        </ul>
      )}
    </div>
  );
}