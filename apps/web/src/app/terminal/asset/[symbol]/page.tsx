import { notFound } from 'next/navigation';

export default async function AssetPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;

  try {
    const res = await fetch(`/api/v1/market/asset/${symbol}`, {
      headers: {
        'Accept': 'application/json',
      },
      cache: 'no-store',
    });

    if (!res.ok) {
      if (res.status === 404) notFound();
      throw new Error(`Failed to fetch asset data: ${res.status}`);
    }

    const data = await res.json();

    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold">Asset: {symbol}</h1>
        {/* Render asset details here */}
      </div>
    );
  } catch (error) {
    console.error('Error loading asset page:', error);
    return (
      <div className="p-6 text-center text-red-600">
        <h2 className="text-xl font-semibold">Error loading asset data</h2>
        <p>Could not retrieve details for symbol '{symbol}'. Please try again later.</p>
      </div>
    );
  }
}