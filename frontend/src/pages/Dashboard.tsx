import { useState } from 'react';
import { useMarketOverview, useTrendingStocks, useTopGainers, useTopLosers } from '../hooks/useMarketData';
import { Card } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { StockWidget } from '../components/common/StockWidget';
import { TrendingUp, TrendingDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { formatPrice, formatPercentage } from '../utils/formatters';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';

export default function Dashboard() {
    const { data: marketData, loading: marketLoading, error: marketError, refetch: refetchMarket } = useMarketOverview(true);
    const [indicesIndex, setIndicesIndex] = useState(0);
    const { data: trendingData, loading: trendingLoading, error: trendingError, refetch: refetchTrending } = useTrendingStocks(true);
    const { data: gainersData, loading: gainersLoading, error: gainersError, refetch: refetchGainers } = useTopGainers(true);
    const { data: losersData, loading: losersLoading, error: losersError, refetch: refetchLosers } = useTopLosers(true);
    const navigate = useNavigate();

    return (
        <div className="space-y-8">
            {/* Page Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                    Market Dashboard
                </h1>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                    Real-time market overview and technical insights
                </p>
            </div>

            {/* Market Overview */}
            <section>
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-4">
                        Market Indices
                        {marketData && marketData.indices.length > 3 && (
                            <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800/50 rounded-lg p-1 border border-gray-200 dark:border-gray-700/50 hidden md:flex">
                                <button
                                    onClick={() => setIndicesIndex(Math.max(0, indicesIndex - 1))}
                                    disabled={indicesIndex === 0}
                                    className="p-1 rounded-md text-gray-500 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-white dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-all shadow-sm disabled:shadow-none"
                                >
                                    <ChevronLeft className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={() => setIndicesIndex(Math.min(marketData.indices.length - 3, indicesIndex + 1))}
                                    disabled={indicesIndex >= marketData.indices.length - 3}
                                    className="p-1 rounded-md text-gray-500 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-white dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-all shadow-sm disabled:shadow-none"
                                >
                                    <ChevronRight className="w-4 h-4" />
                                </button>
                            </div>
                        )}
                    </h2>
                    {marketData && (
                        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                            <div className={clsx(
                                'w-2 h-2 rounded-full',
                                marketData.marketStatus === 'open' ? 'bg-success-500 animate-pulse' : 'bg-gray-400'
                            )} />
                            <span>Market <span className="font-medium capitalize">{marketData.marketStatus}</span></span>
                        </div>
                    )}
                </div>

                {marketLoading && !marketData ? (
                    <LoadingSpinner />
                ) : marketError && !marketData ? (
                    <ErrorMessage error={marketError} onRetry={refetchMarket} />
                ) : marketData ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 overflow-x-auto snap-x flex-nowrap pb-2 md:pb-0">
                        {marketData.indices.slice(indicesIndex, indicesIndex + 3).map((index) => (
                            <Card key={index.symbol} className="hover:shadow-xl transition-shadow">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
                                            {index.name}
                                        </h3>
                                        <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                                            {formatPrice(index.value)}
                                        </p>
                                    </div>
                                    <div className={clsx(
                                        'flex items-center gap-1 text-sm font-semibold',
                                        index.changePercent >= 0 ? 'text-success-600' : 'text-danger-600'
                                    )}>
                                        {index.changePercent >= 0 ? (
                                            <TrendingUp className="w-5 h-5" />
                                        ) : (
                                            <TrendingDown className="w-5 h-5" />
                                        )}
                                        <span>{formatPercentage(index.changePercent)}</span>
                                    </div>
                                </div>
                                <div className={clsx(
                                    'text-sm mt-2',
                                    index.change >= 0 ? 'text-success-600' : 'text-danger-600'
                                )}>
                                    {index.change >= 0 ? '+' : ''}{formatPrice(index.change)}
                                </div>
                            </Card>
                        ))}
                    </div>
                ) : null}
            </section>

            {/* Trending, Gainers, Losers */}
            <StockWidget
                title="Trending Stocks"
                stocks={trendingData}
                loading={trendingLoading}
                error={trendingError}
                onRetry={refetchTrending}
            />

            <div className="grid grid-cols-1 gap-8">
                <StockWidget
                    title="Top Gainers"
                    stocks={gainersData}
                    loading={gainersLoading}
                    error={gainersError}
                    onRetry={refetchGainers}
                    accentColor="success"
                />

                <StockWidget
                    title="Top Losers"
                    stocks={losersData}
                    loading={losersLoading}
                    error={losersError}
                    onRetry={refetchLosers}
                    accentColor="danger"
                />
            </div>

            {/* Quick Actions */}
            <section>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                    Quick Actions
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card
                        className="cursor-pointer hover:shadow-xl transition-all hover:scale-105 bg-gradient-to-br from-primary-50 to-primary-100 dark:from-primary-900 dark:to-primary-800"
                        onClick={() => navigate('/app/stocks')}
                    >
                        <h3 className="font-semibold text-lg text-primary-900 dark:text-primary-100">
                            Market Explorer
                        </h3>
                        <p className="text-sm text-primary-700 dark:text-primary-300 mt-1">
                            Browse all available stocks
                        </p>
                    </Card>

                    <Card
                        className="cursor-pointer hover:shadow-xl transition-all hover:scale-105 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900 dark:to-purple-800"
                        onClick={() => navigate('/app/watchlist')}
                    >
                        <h3 className="font-semibold text-lg text-purple-900 dark:text-purple-100">
                            Watchlist
                        </h3>
                        <p className="text-sm text-purple-700 dark:text-purple-300 mt-1">
                            Track your favorite stocks
                        </p>
                    </Card>

                    <Card
                        className="cursor-pointer hover:shadow-xl transition-all hover:scale-105 bg-gradient-to-br from-success-50 to-success-100 dark:from-success-900 dark:to-success-800"
                        onClick={() => navigate('/app/comparison')}
                    >
                        <h3 className="font-semibold text-lg text-success-900 dark:text-success-100">
                            Compare Stocks
                        </h3>
                        <p className="text-sm text-success-700 dark:text-success-300 mt-1">
                            Analyze side-by-side
                        </p>
                    </Card>
                </div>
            </section>
        </div>
    );
}
