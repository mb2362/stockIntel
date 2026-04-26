import React, { useState, useEffect, useRef } from 'react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { ArrowUpRight, ArrowDownRight, Sparkles, TrendingUp, Activity, ChevronDown } from 'lucide-react';
import { API_BASE_URL } from '../utils/constants';

const ALLOWED_STOCKS = [
    { symbol: 'NVDA',  name: 'NVIDIA Corporation' },
    { symbol: 'AMZN',  name: 'Amazon.com Inc.' },
    { symbol: 'AXON',  name: 'Axon Enterprise Inc.' },
    { symbol: 'AAPL',  name: 'Apple Inc.' },
    { symbol: 'ORCL',  name: 'Oracle Corporation' },
    { symbol: 'MSFT',  name: 'Microsoft Corporation' },
    { symbol: 'JPM',   name: 'JPMorgan Chase & Co.' },
    { symbol: 'META',  name: 'Meta Platforms Inc.' },
    { symbol: 'TSLA',  name: 'Tesla Inc.' },
    { symbol: 'AMD',   name: 'Advanced Micro Devices' },
];

interface Prediction {
    symbol: string;
    signal: 'BUY' | 'SELL' | 'HOLD';
    confidence: number;
    currentPrice: number;
    predictedPrice: number;
    pctChange: number;
    targetDate: string;      // ISO date e.g. "2026-04-22"
    marketIsOpen: boolean;
    confidenceNote: string;
}

function formatTargetDate(isoDate: string): string {
    const [y, m, d] = isoDate.split('-').map(Number);
    return new Date(y, m - 1, d).toLocaleDateString('en-US', {
        weekday: 'long', month: 'short', day: 'numeric',
    });
}

export default function Predict() {
    const [symbol, setSymbol] = useState('');
    const [loading, setLoading] = useState(false);
    const [prediction, setPrediction] = useState<Prediction | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Lock body scroll while dropdown is open
    useEffect(() => {
        document.body.style.overflow = dropdownOpen ? 'hidden' : '';
        return () => { document.body.style.overflow = ''; };
    }, [dropdownOpen]);

    // Close dropdown on outside click
    useEffect(() => {
        function handleClickOutside(e: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
                setDropdownOpen(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const selectedStock = ALLOWED_STOCKS.find(s => s.symbol === symbol) ?? null;

    const handleSelectStock = (sym: string) => {
        setSymbol(sym);
        setDropdownOpen(false);
        setPrediction(null);
    };

    const handlePredict = () => {
        if (!symbol.trim()) return;
        doPredict(symbol);
    };

    const doPredict = async (targetSymbol: string) => {
        setLoading(true);
        setPrediction(null);
        setError(null);

        try {
            const res = await fetch(
                `${API_BASE_URL}/predict/${targetSymbol}`
            );
            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: res.statusText }));
                throw new Error(err.detail ?? 'Prediction failed');
            }
            const data = await res.json();

            setPrediction({
                symbol:         data.symbol,
                signal:         data.signal,
                confidence:     data.confidence,
                currentPrice:   data.current_price,
                predictedPrice: data.predicted_price,
                pctChange:      data.pct_change,
                targetDate:     data.target_date,
                marketIsOpen:   data.market_is_open,
                confidenceNote: data.confidence_note ?? '',
            });
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    // Signal helpers
    const signalColor = (sig: string) => {
        if (sig === 'BUY')  return 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400 border border-green-200 dark:border-green-800/50';
        if (sig === 'SELL') return 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400 border border-red-200 dark:border-red-800/50';
        return 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400 border border-amber-200 dark:border-amber-800/50';
    };
    const signalIcon = (sig: string) => {
        if (sig === 'BUY')  return <ArrowUpRight className="w-5 h-5 mr-1" />;
        if (sig === 'SELL') return <ArrowDownRight className="w-5 h-5 mr-1" />;
        return <Activity className="w-5 h-5 mr-1" />;
    };
    const priceBoxColor = (sig: string) => {
        if (sig === 'BUY')  return 'bg-green-50/40 dark:bg-green-900/10 border-green-100/60 dark:border-green-900/30';
        if (sig === 'SELL') return 'bg-red-50/40 dark:bg-red-900/10 border-red-100/60 dark:border-red-900/30';
        return 'bg-amber-50/40 dark:bg-amber-900/10 border-amber-100/60 dark:border-amber-900/30';
    };
    const priceTextColor = (sig: string) => {
        if (sig === 'BUY')  return 'text-green-600 dark:text-green-400';
        if (sig === 'SELL') return 'text-red-600 dark:text-red-400';
        return 'text-amber-600 dark:text-amber-500';
    };
    const signalLabel = (sig: string) => {
        if (sig === 'BUY')  return 'Bullish momentum detected.';
        if (sig === 'SELL') return 'Bearish pressure detected.';
        return 'Neutral — model is near threshold.';
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
                        Harness the power of our advanced machine learning models to predict the closing price of your favorite stocks.
                    </p>
                </div>
            </div>

            {/* Stock Picker + Predict */}
            <Card className="p-4 shadow-xl border border-gray-100 dark:border-gray-800 bg-white/60 dark:bg-gray-900/60 backdrop-blur-xl rounded-2xl">
                <div className="flex flex-col sm:flex-row items-center gap-3">

                    {/* Custom dropdown */}
                    <div ref={dropdownRef} className="relative flex-1 w-full">
                        <button
                            onClick={() => setDropdownOpen(prev => !prev)}
                            className="w-full flex items-center justify-between gap-2 px-4 py-3 bg-gray-50/80 dark:bg-gray-800/80 border border-transparent rounded-xl text-sm font-medium text-gray-900 dark:text-gray-100 hover:border-primary-500/40 focus:outline-none focus:border-primary-500/50 focus:ring-2 focus:ring-primary-500/10 transition-all"
                        >
                            {selectedStock ? (
                                <span className="flex items-center gap-2">
                                    <span className="font-bold text-primary-600 dark:text-primary-400">{selectedStock.symbol}</span>
                                    <span className="text-gray-500 dark:text-gray-400 truncate">{selectedStock.name}</span>
                                </span>
                            ) : (
                                <span className="text-gray-400">Select a stock to predict…</span>
                            )}
                            <ChevronDown className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform duration-200 ${dropdownOpen ? 'rotate-180' : ''}`} />
                        </button>

                        {dropdownOpen && (
                            <div className="absolute z-50 w-full mt-1.5 bg-white/95 dark:bg-gray-800/95 backdrop-blur-xl border border-gray-200 dark:border-gray-700 rounded-xl shadow-2xl max-h-44 overflow-y-auto animate-in fade-in slide-in-from-top-1 duration-150">
                                {ALLOWED_STOCKS.map((stock) => (
                                    <button
                                        key={stock.symbol}
                                        onClick={() => handleSelectStock(stock.symbol)}
                                        className={`w-full flex items-center justify-between px-4 py-2.5 text-sm hover:bg-gray-100/80 dark:hover:bg-gray-700/80 transition-colors border-b border-gray-100 dark:border-gray-700/50 last:border-b-0 ${
                                            symbol === stock.symbol ? 'bg-primary-50/60 dark:bg-primary-900/20' : ''
                                        }`}
                                    >
                                        <span className="flex items-center gap-2">
                                            <span className="font-bold text-gray-900 dark:text-gray-100 w-12 text-left">{stock.symbol}</span>
                                            <span className="text-gray-500 dark:text-gray-400">{stock.name}</span>
                                        </span>
                                        {symbol === stock.symbol && (
                                            <span className="text-xs font-semibold text-primary-600 dark:text-primary-400">Selected</span>
                                        )}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    <Button
                        onClick={handlePredict}
                        loading={loading}
                        disabled={!symbol.trim()}
                        className="w-full sm:w-auto px-6 py-3 text-sm rounded-xl shadow-md shadow-primary-500/20 hover:shadow-primary-500/40 transition-all font-semibold"
                    >
                        {loading ? 'Analyzing…' : 'Predict Price'}
                    </Button>
                </div>

                {/* Quick-pick pills */}
                <div className="mt-3 flex flex-wrap gap-1.5">
                    {ALLOWED_STOCKS.map((stock) => (
                        <button
                            key={stock.symbol}
                            onClick={() => handleSelectStock(stock.symbol)}
                            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all border ${
                                symbol === stock.symbol
                                    ? 'bg-primary-600 text-white border-primary-600 shadow-sm'
                                    : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-primary-400 hover:text-primary-600 dark:hover:text-primary-400'
                            }`}
                        >
                            {stock.symbol}
                        </button>
                    ))}
                </div>
            </Card>

            {/* Error Banner */}
            {error && (
                <div className="rounded-2xl border border-red-200 dark:border-red-800/50 bg-red-50 dark:bg-red-900/20 px-5 py-4 text-sm text-red-700 dark:text-red-400 font-medium">
                    ⚠ {error}
                </div>
            )}

            {/* Prediction Result Section */}
            {prediction && (
                <div className="animate-in fade-in slide-in-from-bottom-8 duration-700 ease-out fill-mode-both">
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                        {/* Summary Card */}
                        <div className="lg:col-span-2">
                            <Card className="h-full p-8 border border-gray-200 dark:border-gray-800 shadow-xl rounded-3xl relative overflow-hidden group hover:border-primary-500/30 transition-colors">
                                <div className="absolute inset-0 bg-gradient-to-br from-gray-50/50 to-white dark:from-gray-800/50 dark:to-gray-900 -z-10" />

                                {/* Header row: date + badge + icon */}
                                <div className="flex flex-wrap justify-between items-start gap-3 mb-8">
                                    <div>
                                        {/* Date label + market status badge */}
                                        <div className="flex items-center gap-2 mb-3">
                                            <p className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                                Predicted Close &bull; {formatTargetDate(prediction.targetDate)}
                                            </p>
                                            {prediction.marketIsOpen ? (
                                                <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 border border-green-200 dark:border-green-800/40">
                                                    <span className="relative flex h-1.5 w-1.5">
                                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                                        <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-green-500"></span>
                                                    </span>
                                                    Market Open
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-500 dark:bg-gray-700/50 dark:text-gray-400 border border-gray-200 dark:border-gray-700/50">
                                                    <span className="h-1.5 w-1.5 rounded-full bg-gray-400 dark:bg-gray-500 inline-block"></span>
                                                    Market Closed
                                                </span>
                                            )}
                                        </div>

                                        {/* Symbol + Signal badge */}
                                        <h2 className="text-5xl font-bold text-gray-900 dark:text-white flex items-center gap-4">
                                            {prediction.symbol}
                                            <span className={`flex items-center text-lg px-3 py-1.5 rounded-xl font-semibold shadow-sm ${signalColor(prediction.signal)}`}>
                                                {signalIcon(prediction.signal)}
                                                {prediction.signal}
                                            </span>
                                        </h2>
                                    </div>

                                    <div className="p-4 bg-primary-50 dark:bg-primary-900/30 rounded-2xl border border-primary-100 dark:border-primary-800/50">
                                        <Activity className="w-8 h-8 text-primary-600 dark:text-primary-400" />
                                    </div>
                                </div>

                                {/* Price boxes */}
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mt-10">
                                    <div className="p-6 rounded-3xl bg-gray-50/50 dark:bg-gray-800/50 border border-gray-100/50 dark:border-gray-700/30 flex flex-col justify-between min-h-[130px] group/card hover:bg-white dark:hover:bg-gray-800 transition-all duration-300">
                                        <p className="text-xs font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest">Current / Last Close</p>
                                        <p className="text-4xl font-bold text-gray-900 dark:text-gray-100 mt-2 tracking-tight">
                                            ${prediction.currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                        </p>
                                    </div>
                                    <div className={`p-6 rounded-3xl border flex flex-col justify-between min-h-[130px] transition-all duration-500 ${priceBoxColor(prediction.signal)} shadow-sm hover:shadow-md`}>
                                        <div className="flex justify-between items-start">
                                            <p className="text-xs font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest flex items-center gap-1.5">
                                                <Sparkles className="w-3.5 h-3.5" />
                                                Predicted Close
                                            </p>
                                            <span className={`px-2.5 py-1 rounded-full text-xs font-bold flex items-center gap-1 shadow-sm ${
                                                prediction.pctChange >= 0 
                                                    ? 'bg-green-100/80 text-green-700 dark:bg-green-900/40 dark:text-green-400 border border-green-200/50' 
                                                    : 'bg-red-100/80 text-red-700 dark:bg-red-900/40 dark:text-red-400 border border-red-200/50'
                                            }`}>
                                                {prediction.pctChange >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                                                {Math.abs(prediction.pctChange).toFixed(2)}%
                                            </span>
                                        </div>
                                        <p className={`text-5xl font-black mt-2 ${priceTextColor(prediction.signal)} tracking-tighter`}>
                                            ${prediction.predictedPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                        </p>
                                    </div>
                                </div>

                                {/* Confidence footer */}
                                <div className="mt-8 pt-6 border-t border-gray-100 dark:border-gray-800/80">
                                    <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-2 flex-wrap">
                                        <span className="relative flex h-2.5 w-2.5 flex-shrink-0">
                                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-400 opacity-75"></span>
                                            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary-500"></span>
                                        </span>
                                        Model confidence:&nbsp;<strong>{(prediction.confidence * 100).toFixed(1)}%</strong>&nbsp;—&nbsp;{signalLabel(prediction.signal)}
                                        {prediction.confidenceNote && prediction.confidenceNote !== 'Models agree' && (
                                            <span className="text-xs text-amber-600 dark:text-amber-400">({prediction.confidenceNote})</span>
                                        )}
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
