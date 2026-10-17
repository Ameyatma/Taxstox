'use client';

import Link from 'next/link';

export interface AssetData {
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
  performance: Record<string, number>;
  analyst_consensus: {
    consensus: string;
    target_price: number;
    total_analysts: number;
  };
}

function formatCurrency(value: number): string {
  if (!Number.isFinite(value)) return 'N/A';
  if (Math.abs(value) >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return `$${value.toLocaleString()}`;
}

export default function AssetDetail({ data, symbol }: { data: AssetData; symbol: string }) {
  const change = data.day_change_pct ?? 0;
  const isUp = change >= 0;

  return (
    <div className="min-h-[60vh] bg-background text-foreground">
      <div className="max-w-5xl mx-auto px-6 py-8">
        {/* Breadcrumb */}
        <nav className="mb-6 flex items-center gap-2 text-sm text-muted-foreground">
          <Link href="/terminal" className="hover:text-foreground transition-colors">
            Market Terminal
          </Link>
          <span aria-hidden>/</span>
          <span className="text-foreground font-medium">{symbol}</span>
        </nav>

        {/* Header row: name + price + day change */}
        <div className="flex flex-wrap items-end gap-4 mb-6">
          <h1 className="text-3xl font-bold text-foreground">
            {data.company_name || symbol}
          </h1>
          <div className="text-4xl font-bold text-foreground">
            {data.current_price?.toLocaleString() ?? 'N/A'}
          </div>
          <div
            className={`text-sm font-medium ${isUp ? 'text-success-green' : 'text-error-red'}`}
          >
            {isUp ? '+' : ''}{change}% {data.currency}
          </div>
        </div>

        {/* Key metrics */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 mb-8">
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground">Market Cap</p>
            <p className="mt-1 text-lg font-semibold text-foreground">
              {formatCurrency(data.market_cap)}
            </p>
          </div>
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground">P/E Ratio</p>
            <p className="mt-1 text-lg font-semibold text-foreground">
              {data.pe_ratio && data.pe_ratio > 0 ? data.pe_ratio.toFixed(2) : 'N/A'}
            </p>
          </div>
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground">Dividend Yield</p>
            <p className="mt-1 text-lg font-semibold text-foreground">
              {data.dividend_yield && data.dividend_yield > 0
                ? (data.dividend_yield * 100).toFixed(2) + '%'
                : '0.00%'}
            </p>
          </div>
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground">52-Week Range</p>
            <p className="mt-1 text-lg font-semibold text-foreground">
              {data.fifty_two_week_low?.toLocaleString() ?? 'N/A'} –{' '}
              {data.fifty_two_week_high?.toLocaleString() ?? 'N/A'}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Performance */}
          <div className="rounded-xl border border-border bg-card p-6">
            <h2 className="text-lg font-semibold text-foreground mb-4">Performance</h2>
            <div className="grid grid-cols-2 gap-4">
              {(['1W', '1M', '6M', '1Y'] as const).map((period) => {
                const value = data.performance?.[period];
                const pct = value != null ? value : 0;
                const up = pct >= 0;
                return (
                  <div key={period} className="rounded-lg bg-muted p-4">
                    <p className="text-xs text-muted-foreground">{period}</p>
                    <p
                      className={`mt-1 text-lg font-semibold ${
                        up ? 'text-success-green' : 'text-error-red'
                      }`}
                    >
                      {up ? '+' : ''}{pct}%
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Analyst consensus */}
          <div className="rounded-xl border border-border bg-card p-6">
            <h2 className="text-lg font-semibold text-foreground mb-4">Analyst Consensus</h2>
            <div className="flex items-center gap-3">
              <span className="rounded-full bg-primary px-3 py-1 text-xs font-bold text-primary-foreground">
                {data.analyst_consensus?.consensus ?? 'HOLD'}
              </span>
              <div className="text-sm text-muted-foreground">
                Target price:{' '}
                <span className="font-medium text-foreground">
                  {data.analyst_consensus?.target_price?.toLocaleString() ?? 'N/A'}
                </span>
                <br />
                Analysts covering:{' '}
                <span className="font-medium text-foreground">
                  {data.analyst_consensus?.total_analysts ?? 0}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}