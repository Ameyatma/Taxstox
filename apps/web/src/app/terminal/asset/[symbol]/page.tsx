import { headers } from 'next/headers';
import { notFound } from 'next/navigation';
import { Suspense } from 'react';
import Link from 'next/link';
import AssetDetail from '@/components/market/AssetDetail';
import type { AssetData } from '@/components/market/AssetDetail';

// Build an absolute same-origin URL. Node's fetch (used in server components)
// cannot parse relative URLs, so we resolve against the incoming request's own
// origin. Staying same-origin is also required for cookie-based auth: the /api/*
// rewrite in next.config.ts proxies to the backend and forwards the session
// cookie, which a cross-origin *.run.app URL would never receive.
async function fetchAsset(symbol: string): Promise<AssetData | null> {
  const headersList = await headers();
  const host = headersList.get('host') || 'taxstox.com';
  const proto =
    headersList.get('x-forwarded-proto') ||
    (process.env.NODE_ENV === 'production' ? 'https' : 'http');
  const baseUrl = `${proto}://${host}`;

  const res = await fetch(`${baseUrl}/api/v1/market/asset/${symbol}`, {
    headers: { Accept: 'application/json' },
    cache: 'no-store',
  });

  if (res.status === 404) notFound();
  if (!res.ok) {
    throw new Error(`Failed to fetch asset data: ${res.status}`);
  }

  const data: AssetData = await res.json();
  return data;
}

export default async function AssetPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;

  let data: AssetData | null = null;
  let fetchError: Error | null = null;

  try {
    data = await fetchAsset(symbol);
  } catch (error) {
    // notFound() throws internally and is re-thrown past this catch by Next.js;
    // anything reaching here is a genuine fetch failure.
    fetchError = error instanceof Error ? error : new Error(String(error));
    console.error('Error loading asset page:', fetchError);
  }

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

        {fetchError ? (
          <ErrorState symbol={symbol} />
        ) : data ? (
          <Suspense fallback={<Skeleton />}>
            <AssetDetail data={data} symbol={symbol} />
          </Suspense>
        ) : (
          <Skeleton />
        )}
      </div>
    </div>
  );
}

function ErrorState({ symbol }: { symbol: string }) {
  return (
    <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-8 text-center">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="h-6 w-6 text-destructive"
          aria-hidden
        >
          <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2Zm1 15h-2v-6h2Zm0-8h-2V7h2Z" />
        </svg>
      </div>
      <h2 className="text-xl font-semibold text-foreground">Could not load asset data</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        We couldn't retrieve details for symbol &ldquo;{symbol}&rdquo;. This may be a
        temporary upstream issue. Please try again in a moment.
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-3">
        <Link
          href="/terminal"
          className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 transition-opacity"
        >
          Back to Market Terminal
        </Link>
        <Link
          href={`/terminal/asset/${symbol}`}
          className="inline-flex items-center rounded-md border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-muted transition-colors"
        >
          Try again
        </Link>
      </div>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="space-y-6" aria-busy="true">
      <div className="h-24 w-full animate-pulse rounded-xl bg-muted" />
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-20 animate-pulse rounded-xl bg-muted" />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-40 animate-pulse rounded-xl bg-muted" />
        ))}
      </div>
    </div>
  );
}