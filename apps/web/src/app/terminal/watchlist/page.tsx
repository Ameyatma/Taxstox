'use client';

import { useEffect, useState, useMemo } from 'react';
import { useAuth } from "@/lib/auth";
import { getSessionId } from "@/lib/store";
import { getTaxHarvesting, type TaxHarvestingData, type PortfolioItem, fetchPortfolio, fetchRecommendations, type HoldingPosition, type Recommendation } from "@/lib/api";
import { ErrorBoundary } from '@/components/market/ErrorBoundary';
import Link from 'next/link';
import axios from "axios";

// Types are imported from "@/lib/api"

interface MergedPosition extends HoldingPosition {
  rating?: string;
  composite_score?: number;
  catalyst?: string;
  added_at?: string;
  isWatchlistOnly?: boolean;
  opportunity?: boolean; // flagged as a loss-harvesting opportunity
}

export default function WatchlistPage() {
  const { isAuthenticated } = useAuth();
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>([]);
  const [recommendationsMap, setRecommendationsMap] = useState<Record<string, Recommendation>>({});
  const [harvesting, setHarvesting] = useState<TaxHarvestingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [harvestError, setHarvestError] = useState<string | null>(null);
  const [addSymbol, setAddSymbol] = useState('');
  const [adding, setAdding] = useState(false);
  const [activeTab, setActiveTab] = useState<'all' | 'losses' | 'watchlist'>('all');

  // ── Phase 10: load tax session harvesting data (cross-domain bridge) ──
  // Normalize symbols for case-insensitive joining (e.g. "RELIANCE", "RELIANCE.NS").
const normalize = (s: string) => s.replace('.NS', '').replace('.BO', '').toLowerCase();

const sessionId = useMemo(() => getSessionId(), []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!isAuthenticated) return;
      setLoading(true);
      try {
        // Portfolio + recommendations (unchanged from prior phase)
        await Promise.all([fetchPortfolio(), fetchRecommendations()]);
        // Cross-domain: ingested broker holdings + live prices + harvesting
        if (sessionId) {
          const data = await getTaxHarvesting(sessionId);
          setHarvesting(data);
        }
      } catch (err) {
        if (err instanceof Error && err.message.includes('harvesting')) {
          setHarvestError(err.message);
        } else {
          console.error('Watchlist load failed:', err);
          setError('Failed to load watchlist');
        }
      } finally {
        setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [isAuthenticated, sessionId, fetchPortfolio, fetchRecommendations]);

  const mergedPositions = useMemo<MergedPosition[]>(() => {
    if (!harvesting) return [];
    const map = new Map<string, MergedPosition>();

    // 1. Ingested broker holdings from the tax session (live prices from yfinance)
    for (const h of harvesting.holdings) {
      const key = normalize(h.symbol);
      map.set(key, { ...h, opportunity: true });
    }

    // 2. Overlay manual watchlist items (rating, catalyst, added date)
    for (const item of portfolio) {
      const key = normalize(item.symbol);
      if (!map.has(key)) {
        // Watchlist-only symbol: not in the tax session — mark explicitly.
        map.set(key, {
          symbol: item.symbol,
          isin: item.symbol,
          quantity: 0,
          buy_price: 0,
          current_price: 0,
          day_change_pct: 0,
          unrealized_pnl: 0,
          added_at: item.added_at,
          isWatchlistOnly: true,
        });
      }
      const rec = recommendationsMap[item.symbol];
      const existing = map.get(key);
      if (rec && existing) {
        existing.rating = rec.rating;
        existing.composite_score = rec.composite_score;
        existing.catalyst = rec.catalyst;
      }
    }

    // 3. Overlay recommendations on tax-session holdings
    for (const key of map.keys()) {
      const pos = map.get(key);
      if (!pos?.isWatchlistOnly) {
        const symbol = pos!.symbol.replace('.NS', '').replace('.BO', '');
        let rec = recommendationsMap[symbol];
        if (!rec && pos?.isin) {
          const isin = pos!.isin;
          rec = recommendationsMap[isin];
        }
        if (rec) {
          pos!.rating = rec.rating;
          pos!.composite_score = rec.composite_score;
          pos!.catalyst = rec.catalyst;
        }
      }
    }

    return Array.from(map.values());
  }, [harvesting, portfolio, recommendationsMap]);

  const filteredPositions = useMemo(() => {
    switch (activeTab) {
      case 'losses':
        return mergedPositions.filter((p) => (p.unrealized_pnl ?? 0) < 0);
      case 'watchlist':
        return mergedPositions.filter((p) => p.isWatchlistOnly);
      default:
        return mergedPositions;
    }
  }, [mergedPositions, activeTab]);

  const harvestSummary = useMemo(() => {
    if (!harvesting) return null;
    return {
      realizedSTCG: harvesting.realized_stcg,
      potentialSavings: harvesting.total_potential_savings,
      count: harvesting.opportunities?.length ?? 0,
    };
  }, [harvesting]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    const symbol = addSymbol.trim().toUpperCase();
    if (!symbol) return;
    setAdding(true);
    try {
      await axios.post(`/api/v1/market/users/portfolio/${symbol}`);
      setPortfolio((prev) => [
        ...prev,
        { symbol, name: symbol, quantity: 0, added_at: new Date().toISOString() },
      ]);
      setAddSymbol('');
    } catch (err: any) {
      if (err.response && err.response.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Failed to add symbol');
      }
    } finally {
      setAdding(false);
    }
  };

  const removeSymbol = async (symbol: string) => {
    try {
      await axios.delete(`/api/v1/market/users/portfolio/${symbol}`);
      setPortfolio((prev) => prev.filter((item) => item.symbol !== symbol));
    } catch (err: any) {
      if (err.response && err.response.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Failed to remove symbol');
      }
    }
  };

  const ratingColor = (rating?: string) => {
    if (!rating) return 'text-muted-foreground';
    switch (rating) {
      case 'STRONG_BUY':
      case 'BUY':
        return 'text-success-green';
      case 'HOLD':
        return 'text-warning-amber';
      case 'SELL':
      case 'STRONG_SELL':
        return 'text-error-red';
      default:
        return 'text-muted-foreground';
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center bg-slate-950 p-6">
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-bold text-slate-100">Watchlist</h2>
          <p className="text-slate-400">Please log in to access your watchlist.</p>
          <a
            href="/login"
            className="inline-block px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-md transition-colors"
          >
            Login
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[60vh] bg-background text-foreground p-6">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Markets & Watchlist</h1>
          <p className="text-muted-foreground mt-1">
            Live prices (yfinance) · Unrealized P&L · Tax-Loss Harvesting
          </p>
        </div>
        {error && <p className="text-error-red">{error}</p>}
      </div>

      {/* ── Add Symbol Form (unchanged) ────────────────────────────────── */}
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:gap-4">
        <form onSubmit={handleAdd} className="flex-1 sm:max-w-sm">
          <div className="flex space-x-2">
            <input
              type="text"
              value={addSymbol}
              onChange={(e) => setAddSymbol(e.target.value)}
              placeholder="Enter symbol (e.g., RELIANCE.NS)"
              className="flex-1 px-4 py-2 bg-muted border border-border rounded-md text-foreground focus:ring-2 focus:ring-primary focus:border-transparent"
              disabled={adding}
            />
            <button
              type="submit"
              disabled={adding || !addSymbol.trim()}
              className="px-4 py-2 bg-secondary text-secondary-foreground hover:bg-secondary/90 font-medium rounded-md transition-colors disabled:opacity-50"
            >
              {adding ? 'Adding...' : 'Add'}
            </button>
          </div>
        </form>
      </div>

      {/* ── Tax-Loss Harvesting Hero Card (Phase 10) ───────────────────── */}
      {!harvestSummary && !harvesting && sessionId && (
        <div className="mb-6 p-4 rounded-xl bg-card border border-border">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-semibold text-foreground">Tax-Loss Harvesting</h3>
              <p className="text-muted-foreground text-sm mt-1">
                A tax session ({sessionId.slice(0, 8)}…) exists but no harvesting
                data is available yet. Compute your taxes (upload Form 16 / AIS /
                Broker P&L and run the analyzer) to unlock loss-harvesting
                recommendations for your holdings.
              </p>
            </div>
            <Link
              href="/dashboard"
              className="px-3 py-1.5 text-sm font-medium rounded-md bg-emerald-600 text-white hover:bg-emerald-700 transition-colors"
            >
              Go to Dashboard
            </Link>
          </div>
        </div>
      )}

      {harvestSummary && harvestSummary.count > 0 && (
        <div className="mb-6 p-5 rounded-xl bg-gradient-to-br from-emerald-900/40 to-slate-900/60 border border-emerald-700/50">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                  TAX OPTIMIZATION
                </span>
                <h3 className="text-lg font-bold text-foreground">
                  Tax-Loss Harvesting Alert
                </h3>
              </div>
              <p className="text-foreground">
                You can save up to{' '}
                <span className="font-bold text-emerald-400">
                  ₹{(harvestSummary?.potentialSavings ?? 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </span>{' '}
                in capital gains tax by harvesting the{' '}
                <span className="font-bold text-emerald-400">{harvestSummary.count}</span> losing
                position{harvestSummary.count !== 1 ? 's' : ''} identified below,
                before the March 31 year-end.
              </p>
              <p className="text-sm text-muted-foreground">
                Realized STCG (FY2025-26, Section 111A @15%):{' '}
                <span className="text-foreground font-medium">
                  ₹{(harvestSummary?.realizedSTCG ?? 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </span>{' '}
                · Positions shown with live prices and unrealized P&L.
              </p>
            </div>
            <Link
              href="#holdings-table"
              className="px-4 py-2 text-sm font-medium rounded-md bg-emerald-600 text-white hover:bg-emerald-700 transition-colors text-center whitespace-nowrap"
            >
              Review Opportunities
            </Link>
          </div>
        </div>
      )}

      {/* ── Holdings & Watchlist Table ─────────────────────────────────── */}
      <ErrorBoundary fallback={
        <div className="p-6 text-center text-error-red">
          <h2 className="text-xl font-bold">Something went wrong.</h2>
          <p className="mt-2">There was an error rendering the watchlist. Please try refreshing the page.</p>
          <button onClick={() => window.location.reload()} className="mt-4 px-4 py-2 bg-secondary text-secondary-foreground hover:bg-secondary/90 font-medium rounded-md transition-colors">
            Refresh Page
          </button>
        </div>
      }>
        <div className="overflow-x-auto rounded-xl border border-border bg-card">
          {/* Tabs */}
          <div className="flex items-center gap-2 border-b border-border px-2 pt-2 overflow-x-auto">
            {(['all', 'losses', 'watchlist'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors whitespace-nowrap ${
                  activeTab === tab
                    ? 'bg-secondary text-secondary-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
                {tab === 'all' && mergedPositions.length > 0 && (
                  <span className="ml-1.5 px-1.5 py-0.5 text-xs rounded-full bg-border text-foreground">
                    {mergedPositions.length}
                  </span>
                )}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="p-8 text-center text-muted-foreground">Loading positions…</div>
          ) : filteredPositions.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              {activeTab === 'losses'
                ? 'No positions are currently in loss. Keep an eye on the market for opportunities.'
                : activeTab === 'watchlist'
                ? 'Your watchlist is empty. Add symbols above to get started.'
                : 'No holdings to display. Ingest your broker P&L in the dashboard and compute your taxes to see live positions.'}
            </div>
          ) : (
            <table className="min-w-full" id="holdings-table">
              <thead>
                <tr className="bg-muted">
                  <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Symbol</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-muted-foreground">Quantity</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-muted-foreground">Buy Price</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-muted-foreground">Current Price (Live)</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-muted-foreground">Day Change %</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-muted-foreground">Unrealized P&L</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Rating</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredPositions.map((pos) => {
                  const pnl = Number(pos.unrealized_pnl ?? 0);
                  const dayChange = Number(pos.day_change_pct ?? 0);
                  const isLoss = pnl < 0;
                  const isGain = pnl > 0;
                  const isWatchlistOnly = !!pos.isWatchlistOnly;
                  return (
                    <tr
                      key={pos.isin}
                      className={`hover:bg-muted/50 transition-colors cursor-pointer ${
                        isLoss ? 'bg-error-red/5' : isGain ? 'bg-success-green/5' : ''
                      }`}
                    >
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div>
                          <Link
                            href={`/terminal/asset/${encodeURIComponent(pos.symbol)}`}
                            className="font-medium text-foreground hover:underline focus:outline-none focus:ring-2 focus:ring-primary rounded px-1 -mx-1"
                          >
                            {pos.symbol}
                          </Link>
                          {isWatchlistOnly && (
                            <span className="ml-2 inline-flex items-center px-1.5 py-0.5 text-[10px] font-medium rounded bg-border text-muted-foreground">
                              Watchlist
                            </span>
                          )}
                          {pos.opportunity && (
                            <span className="ml-2 inline-flex items-center px-1.5 py-0.5 text-[10px] font-medium rounded bg-emerald-600/20 text-emerald-400 border border-emerald-600/30">
                              Loss to Harvest
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-foreground">
                        {pos.quantity > 0 ? pos.quantity.toLocaleString('en-IN') : '—'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-foreground">
                        {pos.buy_price > 0 ? `₹${pos.buy_price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-foreground">
                        {pos.current_price > 0 ? `₹${pos.current_price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right">
                        {pos.day_change_pct !== undefined && (
                          <span className={
                            dayChange > 0
                              ? 'text-success-green'
                              : dayChange < 0
                              ? 'text-error-red'
                              : 'text-foreground'
                          }>
                            {dayChange > 0 ? '+' : ''}{dayChange.toFixed(2)}%
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right">
                        {pnl !== 0 ? (
                          <span className={`font-medium ${
                            isLoss ? 'text-error-red' : isGain ? 'text-success-green' : 'text-foreground'
                          }`}>
                            {isLoss ? '-' : '+'}₹{Math.abs(pnl).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                            {isLoss && (
                              <span className="ml-1.5 text-[10px] text-error-red/80">
                                (harvestable)
                              </span>
                            )}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {pos.rating ? (
                          <span className={ratingColor(pos.rating)}>{pos.rating}</span>
                        ) : (
                          <span className="text-muted-foreground">N/A</span>
                        )}
                        {pos.catalyst && (
                          <div className="text-xs text-muted-foreground mt-0.5 truncate">
                            {pos.catalyst}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <Link
                          href={`/terminal/asset/${encodeURIComponent(pos.symbol)}`}
                          className="px-3 py-1 bg-secondary hover:bg-secondary/90 text-xs font-medium rounded text-secondary-foreground transition-colors"
                        >
                          View
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </ErrorBoundary>

      {/* ── Note for watchlist-only rows ──────────────────────────────── */}
      {filteredPositions.some((p) => p.isWatchlistOnly) && (
        <p className="mt-3 text-xs text-muted-foreground">
          Symbols marked Watchlist only are not yet in your computed tax session. Upload your
          broker P&L in the dashboard and compute your taxes to see live prices, day changes,
          and unrealized P&L for all holdings.
        </p>
      )}
    </div>
  );
}
