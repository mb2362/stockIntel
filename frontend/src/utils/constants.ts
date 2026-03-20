// Application constants
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api/v1';

export const POLLING_INTERVAL = 30000; // 30 seconds — balances live feel with Yahoo Finance rate limits

export const TIME_RANGES = {
    '1D': { label: '1 Day', days: 1 },
    '1W': { label: '1 Week', days: 7 },
    '1M': { label: '1 Month', days: 30 },
    '3M': { label: '3 Months', days: 90 },
    '1Y': { label: '1 Year', days: 365 },
    '5Y': { label: '5 Years', days: 1825 },
} as const;

export const CHART_COLORS = [
    '#3b82f6', // blue
    '#10b981', // green
    '#f59e0b', // amber
    '#ef4444', // red
    '#8b5cf6', // purple
    '#ec4899', // pink
];

export const MAJOR_INDICES = [
    { symbol: '^GSPC', name: 'S&P 500' },
    { symbol: '^IXIC', name: 'NASDAQ' },
    { symbol: '^DJI', name: 'DOW JONES' },
];

export const POPULAR_STOCKS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
    'META', 'NVDA', 'JPM', 'V', 'WMT'
];

export const SECTORS = [
    'Technology',
    'Healthcare',
    'Financial',
    'Consumer Cyclical',
    'Industrials',
    'Energy',
    'Real Estate',
    'Consumer Defensive',
    'Utilities',
    'Communication Services',
    'Basic Materials',
];
