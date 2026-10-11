'use client';

import { useEffect, useState } from 'react';
import axios from "axios";
import { ErrorBoundary } from '@/components/market/ErrorBoundary';
import TradingViewChart from '@/components/market/TradingViewChart';
import StockSearchBar from '@/components/market/StockSearchBar';
import Link from 'next/link';

interface AssetData {
  symbol: string;
  company_name: string;
  current_price: number;
  currency: string;
  day_change_pct: number;
  market_cap: number;
  pe_ratio: number;
  dividend_yield: number;
  fifty_two_week_high: number;
  fifty_two_week_low: number;
  performance: {
    '1W': number | null;
    '1M': number | null;
    '6M': number | null;
    '1Y': number | null;
  };
  analyst_consensus: {
    consensus: string; // 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL'
    target_price: number | null;
    total_analysts: number | null;
  };
}

interface Props {
  params: {
    symbol: string;
  };
}

export default function AssetDetailPage({ params }: Props) {
  const { symbol } = params;
  const [assetData, setAssetData] = useState<AssetData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAssetData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Normalize symbol: if it doesn't contain a dot, we assume it's an Indian stock and add .NS
        // But note: the backend already does normalization, so we can send the symbol as is.
        // However, to be safe, we'll send the symbol as provided (which might be without suffix).
        const response = await axios.get(`/api/v1/market/asset/${symbol}`);
        const data: AssetData = response.data;
        setAssetData(data);
      } catch (err: any) {
        console.error(err);
        if (err.response && err.response.data?.detail) {
          setError(err.response.data.detail);
        } else {
          setError('Failed to load asset data');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchAssetData();
  }, [symbol]);

  if (loading && !assetData) {
    return (
      <div className="min-h-[60vh] bg-background text-foreground p-6">
        <div className="flex flex-col items-center justify-center">
          <h2 className="text-2xl font-bold text-slate-100 mb-4">Loading asset data...</h2>
          <Link href="/terminal" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">
            ← Back to Terminal
          </Link>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-[60vh] bg-background text-foreground p-6">
        <div className="flex flex-col items-center justify-center">
          <h2 className="text-2xl font-bold text-slate-100 mb-4">Error loading asset data</h2>
          <p className="text-slate-400 mb-4">{error}</p>
          <Link href="/terminal" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">
            ← Back to Terminal
          </Link>
        </div>
      </div>
    );
  }

  if (!assetData) {
    return (
      <div className="min-h-[60vh] bg-background text-foreground p-6">
        <div className="flex flex-col items-center justify-center">
          <h2 className="text-2xl font-bold text-slate-100 mb-4">No asset data</h2>
          <Link href="/terminal" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">
            ← Back to Terminal
          </Link>
        </div>
      </div>
    );
  }

  // Helper to format change percentage with color
  const getChangeClass = (change: number) => {
    return change >= 0 ? 'text-success-green' : 'text-error-red';
  };

  // Helper to format large numbers (market cap)
  const formatMarketCap = (cap: number) => {
    if (cap >= 1e12) {
      return (cap / 1e12).toFixed(2) + 'T';
    } else if (cap >= 1e9) {
      return (cap / 1e9).toFixed(2) + 'B';
    } else if (cap >= 1e6) {
      return (cap / 1e6).toFixed(2) + 'M';
    } else {
      return cap.toString();
    }
  };

  // Helper to format P/E ratio
  const formatPERatio = (pe: number) => {
    return isFinite(pe) ? pe.toFixed(2) : 'N/A';
  };

  return (
    <div className="min-h-[60vh] bg-background text-foreground p-6">
      {/* Navigation link to Terminal */}
      <div className="mb-4">
        <Link href="/terminal" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">
          ← Terminal
        </Link>
      </div>

      {/* Global Search Bar (in navigation header of child view) */}
      <div className="mb-4">
        <StockSearchBar />
      </div>

      {/* Asset Header */}
      <div className="mb-6 flex flex-col items-center gap-4">
        <div className="text-2xl font-bold text-foreground">
          {assetData.symbol} - {assetData.company_name}
        </div>
        <div className="flex flex-col items-center gap-2">
          <div className="text-3xl font-bold text-foreground">
            {assetData.currency}{assetData.current_price.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </div>
          <div className={`text-lg font-medium ${getChangeClass(assetData.day_change_pct)}`}>
            {assetData.day_change_pct >= 0 ? '+' : ''}{assetData.day_change_pct.toFixed(2)}%
          </div>
        </div>
      </div>

      {/* TradingView Chart */}
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-foreground mb-4">Technical Chart</h3>
        <div className="bg-card border border-border rounded-xl p-4">
          <TradingViewChart symbol={assetData.symbol} />
        </div>
      </div>

      {/* Performance Grid */}
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-foreground mb-4">Performance</h3>
        <div className="grid grid-cols-4 gap-4">
          {[ '1W', '1M', '6M', '1Y' ].map((period) => {
            const change = assetData.performance[period as keyof typeof assetData.performance];
            const isValid = change !== null;
            return (
              <div key={period} className="bg-card border border-border rounded-xl p-4 text-center">
                <h4 className="text-xs font-medium text-muted-foreground mb-2">{period}</h4>
                <p className={`${isValid ? (change >= 0 ? 'text-success-green' : 'text-error-red') : 'text-muted-foreground'} font-bold text-foreground`}>
                  {isValid ? (change >= 0 ? '+' : '') + change.toFixed(2) + '%' : 'N/A'}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Analyst Consensus Card */}
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-foreground mb-4">Analyst Consensus</h3>
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="flex flex-col items-center gap-2">
            <div className="text-lg font-bold text-foreground">
              {assetData.analyst_consensus.consensus}
            </div>
            {assetData.analyst_consensus.target_price !== null && (
              <div className="text-sm text-muted-foreground">
                Target Price: {assetData.currency}{assetData.analyst_consensus.target_price.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </div>
            )}
            {assetData.analyst_consensus.total_analysts !== null && (
              <div className="text-sm text-muted-foreground">
                Based on {assetData.analyst_consensus.total_analysts} analyst{assetData.analyst_consensus.total_analysts === 1 ? '' : 's'}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Key Fundamentals Table */}
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-foreground mb-4">Key Fundamentals</h3>
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="text-xs font-medium text-muted-foreground mb-2">Market Cap</h4>
              <p className="text-lg font-bold text-foreground">{formatMarketCap(assetData.market_cap)}</p>
            </div>
            <div>
              <h4 className="text-xs font-medium text-muted-foreground mb-2">P/E Ratio</h4>
              <p className="text-lg font-bold text-foreground">{formatPERatio(assetData.pe_ratio)}</p>
            </div>
            <div>
              <h4 className="text-xs font-medium text-muted-foreground mb-2">52W High</h4>
              <p className="text-lg font-bold text-foreground">
                {assetData.currency}{assetData.fifty_two_week_high.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </p>
            </div>
            <div>
              <h4 className="text-xs font-medium text-muted-foreground mb-2">52W Low</h4>
              <p className="text-lg font-bold text-foreground">
                {assetData.currency}{assetData.fifty_two_week_low.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}