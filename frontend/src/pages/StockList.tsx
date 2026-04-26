import { useState, useMemo, useEffect } from 'react';
import { usePaginatedStocks, useDetailedSearch } from '../hooks/useStockData';
import { Card } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { TrendingUp, TrendingDown, ArrowUpDown, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { formatPrice, formatPercentage } from '../utils/formatters';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';

type SortConfig = {
    key: 'symbol' | 'price' | 'changePercent' | 'volume';
    direction: 'asc' | 'desc';
};

export default function StockList() {
    const navigate = useNavigate();
    const [searchQuery, setSearchQuery] = useState('');
    const [sortConfig, setSortConfig] = useState<SortConfig>({ key: 'symbol', direction: 'asc' });
    const [page, setPage] = useState(1);
    const limit = 10;

    const { data: paginatedData, loading: paginatedLoading, error: paginatedError, refetch: refetchPaginated } = usePaginatedStocks(page, limit, true);
    const { data: searchData, loading: searchLoading, error: searchError, refetch: refetchSearch } = useDetailedSearch(searchQuery, true);

    const isSearching = searchQuery.trim().length > 0;

    // Reset pagination to page 1 if we're not searching anymore
    useEffect(() => {
        if (!isSearching) {
            // we could reset if needed, but doing nothing keeps them on their last viewed page
        }
    }, [isSearching]);

    const displayStocks = useMemo(() => {
        const sourceData = isSearching ? searchData : paginatedData?.data;
        if (!sourceData) return [];

        let result = [...sourceData];

        result.sort((a, b) => {
            if (a[sortConfig.key] < b[sortConfig.key]) {
                return sortConfig.direction === 'asc' ? -1 : 1;
            }
            if (a[sortConfig.key] > b[sortConfig.key]) {
                return sortConfig.direction === 'asc' ? 1 : -1;
            }
            return 0;
        });

        return result;
    }, [searchData, paginatedData, isSearching, sortConfig]);

    const loading = isSearching ? searchLoading : paginatedLoading;
    const error = isSearching ? searchError : paginatedError;
    const refetch = isSearching ? refetchSearch : refetchPaginated;

    const handleSort = (key: SortConfig['key']) => {
        setSortConfig(prev => ({
            key,
            direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
        }));
    };

    const SortIcon = ({ column }: { column: SortConfig['key'] }) => {
        if (sortConfig.key !== column) return <ArrowUpDown className="w-4 h-4 opacity-50" />;
        return <ArrowUpDown className="w-4 h-4" />;
    };

    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                        Market Explorer
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-1">
                        Browse all tracked stocks and indices
                    </p>
                </div>
                <div className="w-full md:w-96">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Filter stocks by symbol or name..."
                            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                    </div>
                </div>
            </div>

            {loading && displayStocks.length === 0 ? (
                <div className="flex justify-center py-12">
                    <LoadingSpinner />
                </div>
            ) : error && displayStocks.length === 0 ? (
                <ErrorMessage error={error} onRetry={refetch} />
            ) : (
                <div className="space-y-4">
                    <Card className="overflow-hidden p-0">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left">
                                <thead>
                                    <tr className="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
                                        <th
                                            className="px-6 py-4 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                                            onClick={() => handleSort('symbol')}
                                        >
                                            <div className="flex items-center gap-2">
                                                Symbol <SortIcon column="symbol" />
                                            </div>
                                        </th>
                                        <th className="px-6 py-4">Company Name</th>
                                        <th
                                            className="px-6 py-4 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-right"
                                            onClick={() => handleSort('price')}
                                        >
                                            <div className="flex items-center justify-end gap-2">
                                                Price <SortIcon column="price" />
                                            </div>
                                        </th>
                                        <th
                                            className="px-6 py-4 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-right"
                                            onClick={() => handleSort('changePercent')}
                                        >
                                            <div className="flex items-center justify-end gap-2">
                                                Change <SortIcon column="changePercent" />
                                            </div>
                                        </th>
                                        <th
                                            className="px-6 py-4 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-right"
                                            onClick={() => handleSort('volume')}
                                        >
                                            <div className="flex items-center justify-end gap-2">
                                                Volume <SortIcon column="volume" />
                                            </div>
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                    {displayStocks.map((stock) => (
                                        <tr
                                            key={stock.symbol}
                                            className="hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer transition-colors"
                                            onClick={() => navigate(`/app/stock/${stock.symbol}`)}
                                        >
                                            <td className="px-6 py-4 font-bold text-primary-600 dark:text-primary-400">
                                                {stock.symbol}
                                            </td>
                                            <td className="px-6 py-4 text-gray-900 dark:text-gray-100">
                                                {stock.name}
                                            </td>
                                            <td className="px-6 py-4 text-right font-semibold text-gray-900 dark:text-gray-100">
                                                {formatPrice(stock.price)}
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <div className={clsx(
                                                    'inline-flex items-center gap-1 font-semibold px-2 py-1 rounded-full text-xs',
                                                    stock.changePercent >= 0
                                                        ? 'bg-success-100 dark:bg-success-900/30 text-success-700 dark:text-success-400'
                                                        : 'bg-danger-100 dark:bg-danger-900/30 text-danger-700 dark:text-danger-400'
                                                )}>
                                                    {stock.changePercent >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                                                    {formatPercentage(stock.changePercent)}
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-right text-gray-600 dark:text-gray-400 text-sm">
                                                {stock.volume.toLocaleString()}
                                            </td>
                                        </tr>
                                    ))}
                                    {displayStocks.length === 0 && (
                                        <tr>
                                            <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                                                {isSearching ? `No stocks found matching "${searchQuery}"` : "No stocks available"}
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </Card>

                    {!isSearching && paginatedData && paginatedData.pages > 1 && (
                        <div className="flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 mt-4">
                            <div className="text-sm text-gray-700 dark:text-gray-300">
                                Showing <span className="font-medium">{((page - 1) * limit) + 1}</span> to <span className="font-medium">{Math.min(page * limit, paginatedData.total)}</span> of <span className="font-medium">{paginatedData.total}</span> stocks
                            </div>
                            <div className="flex items-center gap-4">
                                <button
                                    onClick={() => setPage(p => Math.max(1, p - 1))}
                                    disabled={page === 1}
                                    className="p-2 border border-gray-300 dark:border-gray-600 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition-colors"
                                >
                                    <ChevronLeft className="w-5 h-5" />
                                </button>
                                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                    Page {page} of {paginatedData.pages}
                                </span>
                                <button
                                    onClick={() => setPage(p => Math.min(paginatedData.pages, p + 1))}
                                    disabled={page >= paginatedData.pages}
                                    className="p-2 border border-gray-300 dark:border-gray-600 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition-colors"
                                >
                                    <ChevronRight className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
