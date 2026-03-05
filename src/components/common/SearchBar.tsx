import React, { useState, useRef, useEffect } from 'react';
import { Search, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useDebounce } from '../../hooks/useDebounce';
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
            }
        }

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleSelect = (symbol: string) => {
        setQuery('');
        setShowResults(false);
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
                    onFocus={() => results.length > 0 && setShowResults(true)}
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
        </div>
    );
}
