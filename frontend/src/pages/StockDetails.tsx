import React, { useEffect, useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Card } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { useStockDetails } from '../hooks/useStockData';
import { formatPrice, formatPercentage, formatLargeNumber } from '../utils/formatters';
import { TrendingUp, TrendingDown, Star } from 'lucide-react';
import { useWatchlist } from '../context/WatchlistContext';
import { Button } from '../components/common/Button';
import CandlestickChart from "../components/charts/CandlestickChart";
import clsx from 'clsx';
import { stockService } from '../services/stockService';
import type { HistoricalDataPoint, TimeRange } from '../types/stock';

const TIME_RANGES: TimeRange[] = ['1D', '1W', '1M', '3M', '1Y', '5Y'];

export default function StockDetails() {
    const { symbol } = useParams<{ symbol: string }>();
    const { data: stockData, loading, error, refetch } = useStockDetails(symbol || null);
    const { isInWatchlist, addStock, removeStock } = useWatchlist();

    const [historicalData, setHistoricalData] = useState<HistoricalDataPoint[]>([]);
    const [chartLoading, setChartLoading] = useState(false);
    const [selectedRange, setSelectedRange] = useState<TimeRange>('1M');

    const fetchHistorical = useCallback(async (range: TimeRange) => {
        if (!symbol) return;
        try {
            setChartLoading(true);
            const result = await stockService.getHistoricalData(symbol, range);
            setHistoricalData(result);
        } catch (err) {
            console.error("CandleChartError:", err);
        } finally {
            setChartLoading(false);
        }
    }, [symbol]);

    useEffect(() => {
        fetchHistorical(selectedRange);
    }, [symbol, selectedRange, fetchHistorical]);

    const handleWatchlistToggle = async () => {
        if (!symbol) return;

        try {
            if (isInWatchlist(symbol)) {
                await removeStock(symbol);
            } else {
                await addStock(symbol);
            }
        } catch (error) {
            console.error('Watchlist error:', error);
        }
    };

    if (loading) return <div className="flex justify-center py-20"><LoadingSpinner /></div>;
    if (error) return <ErrorMessage error={error} onRetry={refetch} />;
    if (!stockData) return <ErrorMessage error="Stock not found" />;

    const isPositive = stockData.changePercent >= 0;

    return (
        <div className="space-y-6">

            {/* Stock Header */}
            <Card>
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                    <div className="flex-1">
                        <div className="flex items-center gap-3">
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                                {stockData.symbol}
                            </h1>

                            <Button
                                variant="secondary"
                                size="sm"
                                onClick={handleWatchlistToggle}
                            >
                                <Star
                                    className={clsx(
                                        'w-4 h-4',
                                        isInWatchlist(stockData.symbol) && 'fill-current text-yellow-500'
                                    )}
                                />
                                {isInWatchlist(stockData.symbol) ? 'Remove' : 'Add to Watchlist'}
                            </Button>
                        </div>

                        <p className="text-lg text-gray-600 dark:text-gray-400 mt-1">
                            {stockData.name}
                        </p>
                    </div>

                    <div className="text-right">
                        <div className="text-4xl font-bold text-gray-900 dark:text-gray-100">
                            {formatPrice(stockData.price)}
                        </div>

                        <div
                            className={clsx(
                                'flex items-center justify-end gap-2 text-lg font-semibold mt-2',
                                isPositive ? 'text-success-600' : 'text-danger-600'
                            )}
                        >
                            {isPositive
                                ? <TrendingUp className="w-5 h-5" />
                                : <TrendingDown className="w-5 h-5" />
                            }

                            <span>
                                {formatPrice(stockData.change)} ({formatPercentage(stockData.changePercent)})
                            </span>
                        </div>
                    </div>
                </div>
            </Card>

            {/* Key Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Open</div>
                    <div className="text-xl font-bold mt-1">
                        {formatPrice(stockData.open)}
                    </div>
                </Card>

                <Card>
                    <div className="text-sm text-gray-600 dark:text-gray-400">High</div>
                    <div className="text-xl font-bold text-success-600 mt-1">
                        {formatPrice(stockData.high)}
                    </div>
                </Card>

                <Card>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Low</div>
                    <div className="text-xl font-bold text-danger-600 mt-1">
                        {formatPrice(stockData.low)}
                    </div>
                </Card>

                <Card>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Volume</div>
                    <div className="text-xl font-bold mt-1">
                        {formatLargeNumber(stockData.volume)}
                    </div>
                </Card>
            </div>

            {/* 📊 Price Chart */}
            <Card>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                    <h3 className="font-semibold text-lg text-gray-900 dark:text-gray-100">
                        Price Chart ({selectedRange})
                    </h3>

                    <div className="flex items-center p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
                        {TIME_RANGES.map((range) => (
                            <button
                                key={range}
                                onClick={() => setSelectedRange(range)}
                                className={clsx(
                                    'px-3 py-1.5 text-xs font-semibold rounded-md transition-all',
                                    selectedRange === range
                                        ? 'bg-white dark:bg-gray-700 text-primary-600 dark:text-primary-400 shadow-sm'
                                        : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                                )}
                            >
                                {range}
                            </button>
                        ))}
                    </div>
                </div>

                {chartLoading ? (
                    <div className="h-80 flex items-center justify-center">
                        <LoadingSpinner />
                    </div>
                ) : historicalData.length > 0 ? (
                    <CandlestickChart data={historicalData} />
                ) : (
                    <div className="h-80 flex items-center justify-center bg-gray-100 dark:bg-gray-700 rounded text-center">
                        <div>
                            <p className="text-gray-500 dark:text-gray-400">
                                No historical data available for this range
                            </p>
                            <Button
                                variant="secondary"
                                size="sm"
                                className="mt-4"
                                onClick={() => fetchHistorical(selectedRange)}
                            >
                                Retry
                            </Button>
                        </div>
                    </div>
                )}
            </Card>

        </div>
    );
}