import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

export default function StockSearchBar() {
  const router = useRouter();
  const [symbol, setSymbol] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (symbol.trim()) {
      // Normalize: convert to uppercase and trim
      const normalizedSymbol = symbol.trim().toUpperCase();
      // Navigate to the asset page
      router.push(`/terminal/asset/${normalizedSymbol}`);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-row gap-2">
      <Input
        placeholder="Enter stock symbol (e.g., RELIANCE.NS or AAPL)"
        value={symbol}
        onChange={(e) => setSymbol(e.target.value)}
        onKeyPress={(e) => {
          if (e.key === 'Enter') {
            handleSubmit(e);
          }
        }}
        className="flex-1"
      />
      <Button variant="default" type="submit">
        Search
      </Button>
    </form>
  );
}