import React, { useState, useRef, useEffect } from 'react';
import { Search, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useDebounce } from '../../hooks/useDebounce';
import { useTrendingStocks } from '../../hooks/useMarketData';
import { TrendingUp } from 'lucide-react';
import { stockService } from '../../services/stockService';
import type { SearchResult } from '../../types/api';
import { LoadingSpinner } from './LoadingSpinner';

interface SearchBarProps {
    className?: string;
    placeholder?: string;
}

export function SearchBar({ className, placeholder = 'Search stocks...' }: SearchBarProps) {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<SearchResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [showResults, setShowResults] = useState(false);
    const [isFocused, setIsFocused] = useState(false);
    const { data: trendingData } = useTrendingStocks();
    const debouncedQuery = useDebounce(query, 500);
    const navigate = useNavigate();
    const wrapperRef = useRef<HTMLDivElement>(null);

    // Search when debounced query changes
    useEffect(() => {
        const search = async () => {
            if (debouncedQuery.trim().length < 1) {
                setResults([]);
                return;
            }

            setLoading(true);
            try {
                const data = await stockService.searchStocks(debouncedQuery);
                setResults(data);
                setShowResults(true);
            } catch (error) {
                console.error('Search error:', error);
                setResults([]);
            } finally {
                setLoading(false);
            }
        };

        search();
    }, [debouncedQuery]);

    // Close dropdown when clicking outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
                setShowResults(false);
                setIsFocused(false);
            }
        }

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleSelect = (symbol: string) => {
        setQuery('');
        setShowResults(false);
        setIsFocused(false);
        navigate(`/app/stock/${symbol}`);
    };

    const handleClear = () => {
        setQuery('');
        setResults([]);
        setShowResults(false);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Escape') {
            setShowResults(false);
            setIsFocused(false);
        }
    };

    return (
        <div ref={wrapperRef} className={`relative ${className || ''}`}>
            <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onFocus={() => { setIsFocused(true); results.length > 0 && setShowResults(true); }}
                    onKeyDown={handleKeyDown}
                    placeholder={placeholder}
                    className="w-full pl-10 pr-10 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                {query && (
                    <button
                        onClick={handleClear}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                        <X className="w-5 h-5" />
                    </button>
                )}
            </div>

            {/* Results dropdown */}
            {showResults && (query.length > 0) && (
                <div className="absolute z-50 w-full mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-96 overflow-y-auto">
                    {loading ? (
                        <div className="p-4">
                            <LoadingSpinner size="sm" />
                        </div>
                    ) : results.length > 0 ? (
                        <ul>
                            {results.map((result) => (
                                <li
                                    key={result.symbol}
                                    onClick={() => handleSelect(result.symbol)}
                                    className="px-4 py-3 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-100 dark:border-gray-700 last:border-b-0"
                                >
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <div className="font-semibold text-gray-900 dark:text-gray-100">
                                                {result.symbol}
                                            </div>
                                            <div className="text-sm text-gray-600 dark:text-gray-400">
                                                {result.name}
                                            </div>
                                        </div>
                                        <div className="text-xs text-gray-500 dark:text-gray-500">
                                            {result.type}
                                        </div>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <div className="p-4 text-center text-gray-500 dark:text-gray-400">
                            No results found
                        </div>
                    )}
                </div>
            )}

            {/* Recommendations dropdown when empty and focused */}
            {isFocused && query.length === 0 && trendingData && trendingData.length > 0 && (
                <div className="absolute z-50 w-full mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
                    <div className="p-3 text-xs font-bold text-gray-500 uppercase tracking-widest bg-gray-50/80 dark:bg-gray-800/90 backdrop-blur-sm border-b border-gray-100 dark:border-gray-700 sticky top-0 flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-primary-500" />
                        Trending Recommendations
                    </div>
                    <ul className="max-h-80 overflow-y-auto">
                        {trendingData.slice(0, 5).map((stock) => (
                            <li
                                key={stock.symbol}
                                onClick={() => handleSelect(stock.symbol)}
                                className="px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer border-b border-gray-50 dark:border-gray-700/50 last:border-b-0 transition-colors group"
                            >
                                <div className="flex items-center justify-between">
                                    <div>
                                        <div className="font-semibold text-gray-900 dark:text-gray-100 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                                            {stock.symbol}
                                        </div>
                                        <div className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-[180px]">
                                            {stock.name}
                                        </div>
                                    </div>
                                    <div className={`text-xs font-semibold px-2 py-1 rounded-md shadow-sm ${stock.changePercent >= 0 ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 border border-green-200 dark:border-green-800/50' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 border border-red-200 dark:border-red-800/50'}`}>
                                        {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%
                                    </div>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}
