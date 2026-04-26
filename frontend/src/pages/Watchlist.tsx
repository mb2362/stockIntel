import React, { useState, useEffect } from 'react';
import { useWatchlist } from '../context/WatchlistContext';
import { Card } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { formatPrice, formatPercentage } from '../utils/formatters';
import { Trash2, TrendingUp, TrendingDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';

const PAGE_SIZE = 10;

export default function Watchlist() {
    const { watchlist, loading, removeStock } = useWatchlist();
    const navigate = useNavigate();
    const [currentPage, setCurrentPage] = useState(1);

    // Reset to page 1 whenever the watchlist length changes (add/remove)
    useEffect(() => {
        setCurrentPage(1);
    }, [watchlist.length]);

    const totalPages = Math.max(1, Math.ceil(watchlist.length / PAGE_SIZE));
    const startIndex = (currentPage - 1) * PAGE_SIZE;
    const pageItems = watchlist.slice(startIndex, startIndex + PAGE_SIZE);

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
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                        My Watchlist
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-1">
                        {watchlist.length} {watchlist.length === 1 ? 'stock' : 'stocks'} tracked
                    </p>
                </div>

                {/* Page indicator shown in header when list is long enough */}
                {totalPages > 1 && (
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                        Page {currentPage} of {totalPages}
                    </p>
                )}
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
                <>
                    {/* Stock cards for current page */}
                    <div className="grid grid-cols-1 gap-4">
                        {pageItems.map((stock) => (
                            <Card
                                key={stock.symbol}
                                className="cursor-pointer hover:shadow-xl transition-all"
                                onClick={() => navigate(`/app/stock/${stock.symbol}`)}
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

                    {/* Pagination controls — only shown when needed */}
                    {totalPages > 1 && (
                        <div className="flex items-center justify-between pt-2">
                            <button
                                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                                disabled={currentPage === 1}
                                className={clsx(
                                    'flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all',
                                    currentPage === 1
                                        ? 'text-gray-400 dark:text-gray-600 cursor-not-allowed'
                                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                                )}
                            >
                                <ChevronLeft className="w-4 h-4" />
                                Previous
                            </button>

                            {/* Page number pills */}
                            <div className="flex items-center gap-1">
                                {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                                    <button
                                        key={page}
                                        onClick={() => setCurrentPage(page)}
                                        className={clsx(
                                            'w-8 h-8 rounded-full text-sm font-semibold transition-all',
                                            page === currentPage
                                                ? 'bg-primary-600 text-white shadow-sm'
                                                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                                        )}
                                    >
                                        {page}
                                    </button>
                                ))}
                            </div>

                            <button
                                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                                disabled={currentPage === totalPages}
                                className={clsx(
                                    'flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all',
                                    currentPage === totalPages
                                        ? 'text-gray-400 dark:text-gray-600 cursor-not-allowed'
                                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                                )}
                            >
                                Next
                                <ChevronRight className="w-4 h-4" />
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
