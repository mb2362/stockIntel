import React from 'react';
import { useWatchlist } from '../context/WatchlistContext';
import { Card } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { formatPrice, formatPercentage } from '../utils/formatters';
import { Trash2, TrendingUp, TrendingDown } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';

export default function Watchlist() {
    const { watchlist, loading, removeStock, refreshWatchlist } = useWatchlist();
    const navigate = useNavigate();

    const handleRemove = async (symbol: string, e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            await removeStock(symbol);
        } catch (error) {
            console.error('Error removing stock:', error);
        }
    };

    if (loading && watchlist.length === 0) {
        return <LoadingSpinner />;
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                        My Watchlist
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-1">
                        {watchlist.length} {watchlist.length === 1 ? 'stock' : 'stocks'} tracked
                    </p>
                </div>
            </div>

            {watchlist.length === 0 ? (
                <Card>
                    <div className="text-center py-12">
                        <p className="text-gray-600 dark:text-gray-400 text-lg">
                            Your watchlist is empty
                        </p>
                        <p className="text-gray-500 dark:text-gray-500 text-sm mt-2">
                            Search for stocks and add them to your watchlist to track them here
                        </p>
                    </div>
                </Card>
            ) : (
                <div className="grid grid-cols-1 gap-4">
                    {watchlist.map((stock) => (
                        <Card
                            key={stock.symbol}
                            className="cursor-pointer hover:shadow-xl transition-all"
                            onClick={() => navigate(`/stock/${stock.symbol}`)}
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center gap-3">
                                        <div>
                                            <h3 className="font-bold text-lg text-gray-900 dark:text-gray-100">
                                                {stock.symbol}
                                            </h3>
                                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                                {stock.name}
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-6">
                                    <div className="text-right">
                                        <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                                            {formatPrice(stock.price)}
                                        </div>
                                        <div className={clsx(
                                            'flex items-center justify-end gap-1 text-sm font-semibold mt-1',
                                            stock.changePercent >= 0 ? 'text-success-600' : 'text-danger-600'
                                        )}>
                                            {stock.changePercent >= 0 ? (
                                                <TrendingUp className="w-4 h-4" />
                                            ) : (
                                                <TrendingDown className="w-4 h-4" />
                                            )}
                                            <span>{formatPercentage(stock.changePercent)}</span>
                                        </div>
                                    </div>

                                    <button
                                        onClick={(e) => handleRemove(stock.symbol, e)}
                                        className="p-2 text-gray-400 hover:text-danger-600 hover:bg-danger-50 dark:hover:bg-danger-900 rounded transition-colors"
                                    >
                                        <Trash2 className="w-5 h-5" />
                                    </button>
                                </div>
                            </div>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}
