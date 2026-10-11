'use client';

import { useEffect, useState } from 'react';
import axios from "axios";
import { ErrorBoundary } from '@/components/market/ErrorBoundary';
import TradingViewChart from '@/components/market/TradingViewChart';
import { useAuth } from "@/lib/auth";
import Link from 'next/link';
import StockSearchBar from '@/components/market/StockSearchBar';

interface Recommendation {
  symbol: string;
  rating: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL';
  composite_score: number;
  catalyst: string;
  catalyst_confidence: number;
  catalyst_rationale: string;
  entry_price: number | null;
  stop_loss_price: number | null;
  target_price: number | null;
}

interface Props {}

export default function TerminalPage() {
  const { isAuthenticated } = useAuth();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [addingToWatchlist, setAddingToWatchlist] = useState(false);

  if (!isAuthenticated) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center bg-slate-950 p-6">
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-bold text-slate-100">Market Intelligence</h2>
          <p className="text-slate-400">
            Please log in to access the Next-Day Catalyst Radar and other features.
          </p>
          <Link href="/login" className="inline-block px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-md transition-colors">
            Login
          </Link>
        </div>
      </div>
    );
  }

  // Simplified version - in a real implementation, these would fetch data
  const fetchRecommendations = async () => {
    setLoading(true);
    setError(null);
    try {
      // In a real app, this would call the API
      // For now, we'll use mock data or empty array
      setRecommendations([]);
    } catch (err: any) {
      console.error(err);
      setError('Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, []);

  // Compute summary metrics
  const universeSize = recommendations.length;
  const strongBuyCount = recommendations.filter((r) => r.rating === 'STRONG_BUY').length;
  const avgCompositeScore =
    recommendations.reduce((sum, r) => sum + r.composite_score, 0) / universeSize || 0;

  const addToWatchlist = async () => {
    if (!selectedSymbol) return;
    setAddingToWatchlist(true);
    try {
      // In a real app, this would call the API
      // await axios.post(`/api/v1/market/users/portfolio/${selectedSymbol}`);
    } catch (err: any) {
      if (err.response && err.response.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Failed to add to watchlist');
      }
    } finally {
      setAddingToWatchlist(false);
    }
  };

  return (
    <div className="min-h-[60vh] bg-background text-foreground p-6">
      {/* Navigation link to Tax Filing */}
      <div className="mb-4">
        <Link href="/" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">
          ← Tax Workspace
        </Link>
      </div>

      {/* Global Search Bar */}
      <div className="mb-4">
        <StockSearchBar />
      </div>

      {/* Header */}
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-foreground">Next-Day Catalyst Radar</h1>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <div>Universe Size: <span className="font-medium">{universeSize}</span></div>
          <div>
            Strong Buys Today: <span className="font-medium text-success-green">{strongBuyCount}</span>
          </div>
          <div>
            Market Sentiment: <span className="font-medium">{avgCompositeScore.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-card border border-border rounded-xl p-4">
          <h3 className="text-xs font-medium text-muted-foreground mb-2">Universe Size</h3>
          <p className="text-2xl font-bold text-foreground">{universeSize}</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <h3 className="text-xs font-medium text-muted-foreground mb-2">Strong Buys Today</h3>
          <p className="text-2xl font-bold text-success-green">{strongBuyCount}</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <h3 className="text-xs font-medium text-muted-foreground mb-2">Market Sentiment</h3>
          <p className="text-2xl font-bold text-foreground">{avgCompositeScore.toFixed(2)}</p>
        </div>
      </div>

      {/* Error & Loading */}
      {error && <p className="mb-4 text-error-red text-center">{error}</p>}
      {loading && recommendations.length === 0 && (
        <p className="mb-4 text-center text-muted-foreground">Loading recommendations...</p>
      )}

      {/* Main Content - Simplified for stability */}
      <div className="space-y-6">
        {/* Watchlist Button */}
        <div className="flex justify-center">
          <button
            onClick={addToWatchlist}
            disabled={addingToWatchlist}
            className={`w-full max-w-xs px-4 py-2 bg-secondary text-secondary-foreground hover:bg-secondary/90 font-medium rounded-md transition-colors ${addingToWatchlist ? 'opacity-50' : ''}`}
          >
            {addingToWatchlist ? 'Adding...' : 'Add to Watchlist'}
          </button>
        </div>

        {/* Status Info */}
        <div className="text-center text-sm text-muted-foreground">
          {loading ? 'Loading market data...' : recommendations.length > 0 ?
            `Showing ${recommendations.length} market recommendations` :
            'No market data available'}
        </div>
      </div>
    </div>
  );
}