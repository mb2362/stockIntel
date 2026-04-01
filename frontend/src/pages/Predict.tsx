import React, { useState, useEffect, useRef } from 'react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { ArrowUpRight, ArrowDownRight, Sparkles, TrendingUp, Activity, Search, X } from 'lucide-react';
import { useDebounce } from '../hooks/useDebounce';
import { stockService } from '../services/stockService';
import type { SearchResult } from '../types/api';

interface Prediction {
    symbol: string;
    currentPrice: number;
    predictedPrice: number;
    percentageChange: number;
    trend: 'up' | 'down';
    date: string;
}

export default function Predict() {
    const [symbol, setSymbol] = useState('');
    const [loading, setLoading] = useState(false);
    const [prediction, setPrediction] = useState<Prediction | null>(null);

    // Search autocomplete state
    const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
    const [searchLoading, setSearchLoading] = useState(false);
    const [showResults, setShowResults] = useState(false);
    const debouncedSymbol = useDebounce(symbol, 300);
    const wrapperRef = useRef<HTMLDivElement>(null);

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

    // Search effect
    useEffect(() => {
        const search = async () => {
            if (debouncedSymbol.trim().length === 0) {
                setSearchResults([]);
                return;
            }
            setSearchLoading(true);
            try {
                const data = await stockService.searchStocks(debouncedSymbol);
                setSearchResults(data);
                setShowResults(true);
            } catch (error) {
                console.error('Search error:', error);
                setSearchResults([]);
            } finally {
                setSearchLoading(false);
            }
        };

        // Don't search if the symbol perfectly matches what we just predicted, unless they type again
        search();
    }, [debouncedSymbol]);

    const handleSelectResult = (selectedSymbol: string) => {
        setSymbol(selectedSymbol);
        setShowResults(false);
        // Optionally auto-predict:
        // doPredict(selectedSymbol); 
    };

    const handlePredict = () => {
        if (!symbol.trim()) return;
        doPredict(symbol);
    };

    const doPredict = (targetSymbol: string) => {
        setLoading(true);
        setPrediction(null);
        setShowResults(false);

        // Simulate API call to prediction model
        setTimeout(() => {
            const currentPrice = 145.20 + Math.random() * 50;
            const change = (Math.random() * 10) - 3; // Skewed slightly positive
            const predictedPrice = currentPrice * (1 + change / 100);
            
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);

            setPrediction({
                symbol: targetSymbol.toUpperCase(),
                currentPrice,
                predictedPrice,
                percentageChange: Math.abs(change),
                trend: change >= 0 ? 'up' : 'down',
                date: tomorrow.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })
            });
            setLoading(false);
        }, 1500);
    };

    return (
        <div className="space-y-8 max-w-4xl mx-auto pb-12">
            {/* Header Section */}
            <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-600 via-primary-600 to-purple-800 p-8 sm:p-12 text-white shadow-2xl">
                <div className="absolute top-0 right-0 -mt-16 -mr-16 opacity-20 pointer-events-none">
                    <TrendingUp className="w-64 h-64" />
                </div>
                <div className="relative z-10">
                    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/20 backdrop-blur-md text-sm font-medium mb-6">
                        <Sparkles className="w-4 h-4 text-amber-300" />
                        <span>AI-Powered Forecasting</span>
                    </div>
                    <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-4">
                        Next-Day Price Predictor
                    </h1>
                    <p className="text-lg sm:text-xl text-indigo-100 max-w-2xl leading-relaxed">
                        Harness the power of our advanced machine learning models to predict the closing price of your favorite stocks for tomorrow.
                    </p>
                </div>
            </div>

            {/* Input Section */}
            <Card className="p-2 shadow-xl border border-gray-100 dark:border-gray-800 bg-white/60 dark:bg-gray-900/60 backdrop-blur-xl rounded-3xl">
                <div className="flex flex-col sm:flex-row items-center gap-4 p-4">
                    <div ref={wrapperRef} className="relative flex-1 w-full group">
                        <Search className="absolute left-5 top-1/2 transform -translate-y-1/2 w-6 h-6 text-gray-400 group-focus-within:text-primary-500 transition-colors" />
                        <input
                            type="text"
                            value={symbol}
                            onChange={(e) => {
                                setSymbol(e.target.value);
                                setShowResults(true);
                            }}
                            onFocus={() => {
                                if (searchResults.length > 0 && symbol.length > 0) setShowResults(true);
                            }}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') handlePredict();
                                if (e.key === 'Escape') setShowResults(false);
                            }}
                            placeholder="Enter stock ticker (e.g., AAPL, TSLA)"
                            className="w-full pl-14 pr-12 py-4 bg-gray-50/80 dark:bg-gray-800/80 border border-transparent rounded-2xl text-xl font-medium text-gray-900 dark:text-gray-100 focus:outline-none focus:border-primary-500/50 focus:ring-4 focus:ring-primary-500/10 focus:bg-white dark:focus:bg-gray-800 transition-all placeholder:text-gray-400"
                        />
                        {symbol && (
                            <button
                                onClick={() => { setSymbol(''); setShowResults(false); }}
                                className="absolute right-5 top-1/2 transform -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        )}
                        
                        {/* Autocomplete Dropdown */}
                        {showResults && symbol.length > 0 && (
                            <div className="absolute z-50 w-full mt-2 bg-white/95 dark:bg-gray-800/95 backdrop-blur-xl border border-gray-200 dark:border-gray-700 rounded-2xl shadow-2xl max-h-80 overflow-y-auto animate-in fade-in slide-in-from-top-2 duration-200">
                                {searchLoading ? (
                                    <div className="p-6 text-center text-gray-500">
                                        <div className="animate-pulse flex items-center justify-center gap-2">
                                            <Search className="w-4 h-4" />
                                            Searching market data...
                                        </div>
                                    </div>
                                ) : searchResults.length > 0 ? (
                                    <ul>
                                        {searchResults.map((result) => (
                                            <li
                                                key={result.symbol}
                                                onClick={() => handleSelectResult(result.symbol)}
                                                className="px-6 py-4 hover:bg-gray-100/80 dark:hover:bg-gray-700/80 cursor-pointer border-b border-gray-100 dark:border-gray-700/50 last:border-b-0 transition-colors group"
                                            >
                                                <div className="flex items-center justify-between">
                                                    <div>
                                                        <div className="text-xl font-bold text-gray-900 dark:text-gray-100 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                                                            {result.symbol}
                                                        </div>
                                                        <div className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate max-w-[220px] sm:max-w-[400px]">
                                                            {result.name}
                                                        </div>
                                                    </div>
                                                    <div className="text-xs font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest pl-4">
                                                        {result.type || 'EQUITY'}
                                                    </div>
                                                </div>
                                            </li>
                                        ))}
                                    </ul>
                                ) : (
                                    <div className="p-6 text-center text-gray-500">
                                        No exact matches found for "{symbol}"
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                    <Button 
                        onClick={handlePredict} 
                        loading={loading}
                        disabled={!symbol.trim()}
                        className="w-full sm:w-auto px-8 py-4 text-lg rounded-2xl shadow-lg shadow-primary-500/20 hover:shadow-primary-500/40 transition-all font-semibold"
                    >
                        {loading ? 'Analyzing...' : 'Predict Price'}
                    </Button>
                </div>
            </Card>

            {/* Prediction Result Section */}
            {prediction && (
                <div className="animate-in fade-in slide-in-from-bottom-8 duration-700 ease-out fill-mode-both">
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Summary Card */}
                        <div className="lg:col-span-2">
                            <Card className="h-full p-8 border border-gray-200 dark:border-gray-800 shadow-xl rounded-3xl relative overflow-hidden group hover:border-primary-500/30 transition-colors">
                                <div className="absolute inset-0 bg-gradient-to-br from-gray-50/50 to-white dark:from-gray-800/50 dark:to-gray-900 -z-10" />
                                
                                <div className="flex justify-between items-start mb-8">
                                    <div>
                                        <p className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
                                            Predicted Close &bull; {prediction.date}
                                        </p>
                                        <h2 className="text-5xl font-bold text-gray-900 dark:text-white flex items-center gap-4">
                                            {prediction.symbol}
                                            <span className={`flex items-center text-lg px-3 py-1.5 rounded-xl font-semibold shadow-sm ${
                                                prediction.trend === 'up' 
                                                ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400 border border-green-200 dark:border-green-800/50' 
                                                : 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400 border border-red-200 dark:border-red-800/50'
                                            }`}>
                                                {prediction.trend === 'up' ? <ArrowUpRight className="w-5 h-5 mr-1" /> : <ArrowDownRight className="w-5 h-5 mr-1" />}
                                                {prediction.percentageChange.toFixed(2)}%
                                            </span>
                                        </h2>
                                    </div>
                                    <div className="p-4 bg-primary-50 dark:bg-primary-900/30 rounded-2xl border border-primary-100 dark:border-primary-800/50">
                                        <Activity className="w-8 h-8 text-primary-600 dark:text-primary-400" />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-8 mt-10">
                                    <div className="p-5 rounded-2xl bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700/50">
                                        <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Current/Last Close</p>
                                        <p className="text-3xl font-semibold text-gray-900 dark:text-gray-100">
                                            ${prediction.currentPrice.toFixed(2)}
                                        </p>
                                    </div>
                                    <div className={`p-5 rounded-2xl border ${
                                            prediction.trend === 'up' ? 'bg-green-50/50 dark:bg-green-900/10 border-green-100 dark:border-green-900/30' : 'bg-red-50/50 dark:bg-red-900/10 border-red-100 dark:border-red-900/30'
                                    }`}>
                                        <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 flex items-center gap-1.5">
                                            <Sparkles className="w-4 h-4" />
                                            Predicted Close
                                        </p>
                                        <p className={`text-4xl font-bold ${
                                            prediction.trend === 'up' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                                        }`}>
                                            ${prediction.predictedPrice.toFixed(2)}
                                        </p>
                                    </div>
                                </div>
                                
                                <div className="mt-8 pt-6 border-t border-gray-100 dark:border-gray-800/80">
                                    <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-2">
                                        <span className="relative flex h-2.5 w-2.5">
                                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-400 opacity-75"></span>
                                          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary-500"></span>
                                        </span>
                                        Model confidence is exceptionally high based on recent volume momentum.
                                    </p>
                                </div>
                            </Card>
                        </div>

                        {/* Model Insight Card */}
                        <div className="lg:col-span-1">
                            <Card className="h-full p-6 sm:p-8 border border-gray-200 dark:border-gray-800 bg-gray-50/80 dark:bg-gray-800/40 shadow-lg rounded-3xl">
                                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
                                    <Activity className="w-5 h-5 text-indigo-500" />
                                    Signals
                                </h3>
                                <ul className="space-y-5">
                                    <li className="flex items-start gap-4">
                                        <div className="p-2.5 bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 rounded-xl shadow-sm">
                                            <TrendingUp className="w-5 h-5" />
                                        </div>
                                        <div>
                                            <p className="font-semibold text-gray-900 dark:text-gray-100 leading-none mb-1.5">Momentum</p>
                                            <p className="text-sm text-gray-600 dark:text-gray-400 leading-snug">Short-term MAs indicate strong trend continuation.</p>
                                        </div>
                                    </li>
                                    <li className="flex items-start gap-4">
                                        <div className="p-2.5 bg-purple-100 dark:bg-purple-900/40 text-purple-600 dark:text-purple-400 rounded-xl shadow-sm">
                                            <Activity className="w-5 h-5" />
                                        </div>
                                        <div>
                                            <p className="font-semibold text-gray-900 dark:text-gray-100 leading-none mb-1.5">Volatility</p>
                                            <p className="text-sm text-gray-600 dark:text-gray-400 leading-snug">RSI levels suggest normal expected fluctuations.</p>
                                        </div>
                                    </li>
                                </ul>
                                <div className="mt-8 p-4 bg-amber-50/80 dark:bg-amber-900/20 border border-amber-200/60 dark:border-amber-700/50 rounded-2xl">
                                    <p className="text-sm text-amber-800 dark:text-amber-500 leading-relaxed font-medium">
                                        <strong className="block mb-1">Disclaimer</strong>
                                        Predictions are generated by an AI model and should not be considered financial advice.
                                    </p>
                                </div>
                            </Card>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
