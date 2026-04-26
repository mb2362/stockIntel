// Stock-related types
export interface Stock {
    symbol: string;
    name: string;
    price: number;
    change: number;
    changePercent: number;
    volume: number;
    marketCap: number;
    sector?: string;
    industry?: string;
}

export interface StockQuote extends Stock {
    open: number;
    high: number;
    low: number;
    previousClose: number;
    fiftyTwoWeekHigh: number;
    fiftyTwoWeekLow: number;
    peRatio?: number;
    dividendYield?: number;
    beta?: number;
}

export interface StockDetails extends StockQuote {
    description?: string;
    ceo?: string;
    employees?: number;
    headquarters?: string;
    founded?: string;
    website?: string;
}

export interface HistoricalDataPoint {
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

export interface TechnicalIndicators {
    symbol: string;
    ma50: number;
    ma200: number;
    rsi: number;
    macd: {
        value: number;
        signal: number;
        histogram: number;
    };
}

export interface NewsArticle {
    id: string;
    title: string;
    source: string;
    url: string;
    publishedAt: string;
    summary?: string;
    imageUrl?: string;
    sentiment?: 'positive' | 'negative' | 'neutral';
}

export type TimeRange = '1D' | '1W' | '1M' | '3M' | '1Y' | '5Y';

export interface WatchlistItem extends Stock {
    addedAt: string;
}

export interface PaginatedStocks {
    data: StockQuote[];
    total: number;
    page: number;
    pages: number;
}
