import { cookies } from 'next/headers';
import { notFound } from 'next/navigation';

export default async function AssetPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;
  const cookieStore = await cookies();
  const token = cookieStore.get('taxstox_token')?.value;

  const backendUrl = process.env.NEXT_PUBLIC_API_URL || "https://taxstox-api-435349196142.asia-south1.run.app/api/v1";

  try {
    const res = await fetch(`${backendUrl}/api/v1/market/asset/${symbol}`, {
      headers: {
        'Accept': 'application/json',
        'Cookie': `taxstox_token=${token || ''}`,
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