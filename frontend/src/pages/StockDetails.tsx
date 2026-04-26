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
import AreaStockChart from "../components/charts/AreaStockChart";
import clsx from 'clsx';
import { stockService } from '../services/stockService';
import type { HistoricalDataPoint, TimeRange } from '../types/stock';

const TIME_RANGES: TimeRange[] = ['1D', '1W', '1M', '3M', '1Y', '5Y'];

export default function StockDetails() {
    const { symbol } = useParams<{ symbol: string }>();
    const { data: stockData, loading, error, refetch } = useStockDetails(symbol || null, true);
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
            <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6 px-2">
                <div className="flex-1">
                    <div className="flex items-center gap-4 mb-2">
                        <h1 className="text-4xl md:text-5xl font-extrabold text-gray-900 dark:text-gray-50 tracking-tight">
                            {stockData.symbol}
                        </h1>

                        <Button
                            variant="secondary"
                            onClick={handleWatchlistToggle}
                            className="rounded-full shadow-sm hover:shadow-md transition-shadow dark:bg-gray-800"
                        >
                            <Star
                                className={clsx(
                                    'w-5 h-5 transition-colors',
                                    isInWatchlist(stockData.symbol) ? 'fill-yellow-400 text-yellow-400' : 'text-gray-400'
                                )}
                            />
                            <span className="ml-2 font-medium">
                                {isInWatchlist(stockData.symbol) ? 'Saved' : 'WatchList'}
                            </span>
                        </Button>
                    </div>

                    <p className="text-xl text-gray-600 dark:text-gray-400 font-medium tracking-wide">
                        {stockData.name}
                    </p>
                </div>

                <div className="text-left md:text-right flex flex-col items-start md:items-end">
                    <div className="text-5xl md:text-6xl font-black text-gray-900 dark:text-gray-50 tabular-nums">
                        {formatPrice(stockData.price)}
                    </div>

                    <div
                        className={clsx(
                            'flex items-center gap-2 text-xl font-bold mt-2 px-3 py-1 rounded-md backdrop-blur-sm bg-opacity-10',
                            isPositive ? 'text-success-600 bg-success-500/10' : 'text-danger-600 bg-danger-500/10'
                        )}
                    >
                        {isPositive
                            ? <TrendingUp className="w-6 h-6" />
                            : <TrendingDown className="w-6 h-6" />
                        }

                        <span>
                            {isPositive ? '+' : ''}{formatPrice(stockData.change)} ({formatPercentage(stockData.changePercent)})
                        </span>
                    </div>
                </div>
            </div>

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
            <Card className="p-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 border-b border-gray-200 dark:border-gray-800 pb-4">
                    <h3 className="font-semibold text-xl text-gray-900 dark:text-gray-100">
                        Price Chart
                    </h3>

                    <div className="flex items-center p-1 bg-gray-100 dark:bg-gray-800/50 rounded-full border border-gray-200 dark:border-gray-700/50">
                        {TIME_RANGES.map((range) => (
                            <button
                                key={range}
                                onClick={() => setSelectedRange(range)}
                                className={clsx(
                                    'px-4 py-1.5 text-sm font-semibold rounded-full transition-all duration-200',
                                    selectedRange === range
                                        ? 'bg-white dark:bg-gray-700 text-primary-600 dark:text-primary-400 shadow-md transform scale-105'
                                        : 'text-gray-500 hover:text-gray-900 dark:hover:text-gray-200'
                                )}
                            >
                                {range}
                            </button>
                        ))}
                    </div>
                </div>

                {chartLoading ? (
                    <div className="h-96 flex items-center justify-center bg-gray-50 dark:bg-gray-800/20 rounded-xl">
                        <LoadingSpinner />
                    </div>
                ) : historicalData.length > 0 ? (
                    <div className="h-96 -ml-4">
                        <AreaStockChart data={historicalData} />
                    </div>
                ) : (
                    <div className="h-96 flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-800/20 rounded-xl text-center border border-dashed border-gray-300 dark:border-gray-700">
                        <p className="text-gray-500 dark:text-gray-400 mb-4">
                            No historical data available for this range
                        </p>
                        <Button
                            variant="secondary"
                            onClick={() => fetchHistorical(selectedRange)}
                        >
                            Retry Loading
                        </Button>
                    </div>
                )}
            </Card>

            {/* About Company Section */}
            {(stockData.description || stockData.sector || stockData.ceo) && (
                <div className="mt-8">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6 px-2">About {stockData.name}</h2>
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                        <Card className="lg:col-span-2 p-6 shadow-sm hover:shadow-md transition-shadow duration-300">
                            <h3 className="font-semibold text-lg text-gray-900 dark:text-gray-100 mb-3 border-b border-gray-200 dark:border-gray-800 pb-2">Description</h3>
                            <p className="text-gray-600 dark:text-gray-300 leading-relaxed text-base">
                                {stockData.description || "No company description available."}
                            </p>
                        </Card>

                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-4">
                            <Card className="p-5 shadow-sm hover:shadow-md transition-shadow duration-300">
                                <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">CEO</div>
                                <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">{stockData.ceo || "N/A"}</div>
                            </Card>

                            <Card className="p-5 shadow-sm hover:shadow-md transition-shadow duration-300">
                                <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Sector</div>
                                <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">{stockData.sector || "N/A"}</div>
                            </Card>

                            <Card className="p-5 shadow-sm hover:shadow-md transition-shadow duration-300">
                                <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Industry</div>
                                <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">{stockData.industry || "N/A"}</div>
                            </Card>

                            <Card className="p-5 shadow-sm hover:shadow-md transition-shadow duration-300">
                                <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Employees</div>
                                <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                                    {stockData.employees ? stockData.employees.toLocaleString() : "N/A"}
                                </div>
                            </Card>

                            {stockData.website && (
                                <Card className="p-5 shadow-sm hover:shadow-md transition-shadow duration-300 sm:col-span-2 lg:col-span-1">
                                    <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Website</div>
                                    <a
                                        href={stockData.website}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-lg font-semibold text-primary-600 hover:text-primary-500 dark:text-primary-400 break-all"
                                    >
                                        {stockData.website.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '')}
                                    </a>
                                </Card>
                            )}
                        </div>
                    </div>
                </div>
            )}

        </div>
    );
}