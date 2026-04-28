import React, { useState, useEffect, useMemo } from 'react';
import { useWatchlist } from '../context/WatchlistContext';
import { Card } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { formatPrice, formatPercentage } from '../utils/formatters';
import { Trash2, TrendingUp, TrendingDown, ChevronLeft, ChevronRight, Search, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';

const PAGE_SIZE = 10;

export default function Watchlist() {
    const { watchlist, loading, removeStock } = useWatchlist();
    const navigate = useNavigate();
    const [currentPage, setCurrentPage] = useState(1);
    const [searchQuery, setSearchQuery] = useState('');

    // Reset to page 1 whenever the watchlist length or search changes
    useEffect(() => {
        setCurrentPage(1);
    }, [watchlist.length, searchQuery]);

    // Filter watchlist based on search query
    const filteredWatchlist = useMemo(() => {
        if (!searchQuery.trim()) return watchlist;
        const q = searchQuery.toLowerCase();
        return watchlist.filter(stock =>
            stock.symbol.toLowerCase().includes(q) ||
            stock.name.toLowerCase().includes(q)
        );
    }, [watchlist, searchQuery]);

    const totalPages = Math.max(1, Math.ceil(filteredWatchlist.length / PAGE_SIZE));
    const startIndex = (currentPage - 1) * PAGE_SIZE;
    const pageItems = filteredWatchlist.slice(startIndex, startIndex + PAGE_SIZE);

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
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                        My Watchlist
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-1">
                        {watchlist.length} {watchlist.length === 1 ? 'stock' : 'stocks'} tracked
                    </p>
                </div>

                <div className="flex items-center gap-4">
                    {/* Page indicator */}
                    {totalPages > 1 && (
                        <p className="text-sm text-gray-500 dark:text-gray-400 shrink-0">
                            Page {currentPage} of {totalPages}
                        </p>
                    )}

                    {/* Search bar */}
                    {watchlist.length > 0 && (
                        <div className="relative w-full md:w-72">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Search watchlist..."
                                className="w-full pl-10 pr-9 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                            />
                            {searchQuery && (
                                <button
                                    onClick={() => setSearchQuery('')}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            )}
                        </div>
                    )}
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
            ) : filteredWatchlist.length === 0 ? (
                <Card>
                    <div className="text-center py-12">
                        <p className="text-gray-600 dark:text-gray-400 text-lg">
                            No stocks found matching "{searchQuery}"
                        </p>
                        <button
                            onClick={() => setSearchQuery('')}
                            className="text-primary-600 dark:text-primary-400 text-sm mt-2 hover:underline"
                        >
                            Clear search
                        </button>
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

                    {/* Pagination controls */}
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