'use client';

import { useEffect, useState, useRef } from 'react';
import {
  createChart,
  CandlestickSeries,
  HistogramSeries,
  IChartApi,
  ISeriesApi,
} from 'lightweight-charts';
import axios from "axios";

interface Candle {
  time: number; // UNIX timestamp in seconds
  open: number;
  high: number;
  low: number;
  close: number;
}

interface Volume {
  time: number; // UNIX timestamp in seconds
  value: number;
}

interface Marker {
  time: number; // UNIX timestamp in seconds
  position: 'aboveBar' | 'belowBar';
  color: string;
  shape: 'circle' | 'square' | 'arrowUp' | 'arrowDown';
  text?: string;
}

interface Props {
  symbol: string;
}

export default function TradingViewChart({ symbol }: Props) {
  const chartRef = useRef<HTMLDivElement | null>(null);
  const [chart, setChart] = useState<IChartApi | null>(null);
  const [candleSeries, setCandleSeries] = useState<any>(null);
  const [volumeSeries, setVolumeSeries] = useState<any>(null);
  const [data, setData] = useState<any>(null); // raw backend response
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    // Initialize chart
    const newChart = createChart(chartRef.current, {
      width: chartRef.current.clientWidth,
      height: chartRef.current.clientHeight,
      layout: {
        background: { type: 'solid', color: '#0d1117' } as any,
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#1f2937' },
        horzLines: { color: '#1f2937' },
      },
    });

    const candleSeriesInstance = newChart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    });

    const volumeSeriesInstance = newChart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: '', // overlay
    });
    volumeSeriesInstance.priceScale().applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    setChart(newChart);
    setCandleSeries(candleSeriesInstance);
    setVolumeSeries(volumeSeriesInstance);

    // Resize observer
    const resizeObserver = new ResizeObserver(() => {
      if (newChart) {
        const width = chartRef.current?.clientWidth || 0;
        const height = chartRef.current?.clientHeight || 0;
        newChart.resize(width, height);
      }
    });
    resizeObserver.observe(chartRef.current);

    // Fetch data
    fetchData();

    return () => {
      resizeObserver.disconnect();
      if (newChart) {
        newChart.remove();
      }
    };
  }, [symbol]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`/api/v1/market/stocks/${symbol}/chart`);
      const backendData: any = response.data;
      setData(backendData);

      // Helper to parse time string from backend format "YYYY-MM-DD HH:mm:ss" to UNIX seconds
      const parseTimeString = (timeStr: string) => {
        const [datePart, timePart] = timeStr.split(' ');
        const [year, month, day] = datePart.split('-').map(Number);
        const [hour, minute, second] = timePart.split(':').map(Number);
        // month is 1-based, so subtract 1 for Date
        const date = new Date(Date.UTC(year, month - 1, day, hour, minute, second));
        return date.getTime() / 1000; // seconds
      };

      if (candleSeries && backendData.candles && backendData.candles.length > 0) {
        // Convert backend candles to two series: candlesticks (OHLC) and volume
        const candleData: Candle[] = backendData.candles.map((c: any) => ({
          time: parseTimeString(c.time),
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        }));
        candleSeries.setData(candleData);

        const volumeData: Volume[] = backendData.candles.map((c: any) => ({
          time: parseTimeString(c.time),
          value: c.volume,
        }));
        volumeSeries.setData(volumeData);
      }

      if (candleSeries && backendData.markers && backendData.markers.length > 0) {
        const markerData: Marker[] = backendData.markers.map((m: any) => ({
          time: parseTimeString(m.time),
          position: m.position as 'aboveBar' | 'belowBar',
          color: m.color,
          shape: m.shape as 'circle' | 'square' | 'arrowUp' | 'arrowDown',
          text: m.text,
        }));
        candleSeries.setMarkers(markerData);
      }
    } catch (err: any) {
      console.error(err);
      setError('Failed to load chart data');
    } finally {
      setLoading(false);
    }
  };

  // Refetch when symbol changes
  useEffect(() => {
    if (chart && candleSeries && volumeSeries) {
      fetchData();
    }
  }, [symbol]);

  if (loading && !data) {
    return <div className="h-full flex items-center justify-center text-slate-400">Loading chart...</div>;
  }

  if (error) {
    return <div className="h-full flex items-center justify-center text-red-500">{error}</div>;
  }

  return <div ref={chartRef} className="w-full h-full" />;
}