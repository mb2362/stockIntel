import { useState, useEffect, useCallback } from 'react';
import { stockService } from '../services/stockService';
import type { StockQuote, StockDetails, HistoricalDataPoint, TechnicalIndicators, NewsArticle, TimeRange, PaginatedStocks } from '../types/stock';
import type { ApiError } from '../types/api';
import { POLLING_INTERVAL } from '../utils/constants';

interface UseStockDataResult<T> {
    data: T | null;
    loading: boolean;
    error: ApiError | null;
    refetch: () => Promise<void>;
}

// Hook for fetching stock quote
export function useStockQuote(symbol: string | null, autoRefresh: boolean = false): UseStockDataResult<StockQuote> {
    const [data, setData] = useState<StockQuote | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<ApiError | null>(null);

    const fetchData = useCallback(async (isInitial: boolean = true) => {
        if (!symbol) return;

        if (isInitial) setLoading(true);
        setError(null);

        try {
            const quote = await stockService.getStockQuote(symbol);
            setData(quote);
        } catch (err) {
            setError(err as ApiError);
        } finally {
            if (isInitial) setLoading(false);
        }
    }, [symbol]);

    useEffect(() => {
        fetchData(true);

        if (autoRefresh) {
            const interval = setInterval(() => fetchData(false), POLLING_INTERVAL);
            return () => clearInterval(interval);
        }
    }, [fetchData, autoRefresh]);

    return { data, loading, error, refetch: () => fetchData(true) };
}

// Hook for fetching stock details
export function useStockDetails(symbol: string | null, autoRefresh: boolean = false): UseStockDataResult<StockDetails> {
    const [data, setData] = useState<StockDetails | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<ApiError | null>(null);

    const fetchData = useCallback(async (isInitial: boolean = true) => {
        if (!symbol) return;

        if (isInitial) setLoading(true);
        setError(null);

        try {
            const details = await stockService.getStockDetails(symbol);
            setData(details);
        } catch (err) {
            setError(err as ApiError);
        } finally {
            if (isInitial) setLoading(false);
        }
    }, [symbol]);

    useEffect(() => {
        fetchData(true);

        if (autoRefresh) {
            const interval = setInterval(() => fetchData(false), POLLING_INTERVAL);
            return () => clearInterval(interval);
        }
    }, [fetchData, autoRefresh]);

    return { data, loading, error, refetch: () => fetchData(true) };
}

// Hook for fetching historical data
export function useHistoricalData(
    symbol: string | null,
    range: TimeRange
): UseStockDataResult<HistoricalDataPoint[]> {
    const [data, setData] = useState<HistoricalDataPoint[] | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<ApiError | null>(null);

    const fetchData = useCallback(async () => {
        if (!symbol) return;

        setLoading(true);
        setError(null);

        try {
            const historical = await stockService.getHistoricalData(symbol, range);
            setData(historical);
        } catch (err) {
            setError(err as ApiError);
        } finally {
            setLoading(false);
        }
    }, [symbol, range]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return { data, loading, error, refetch: fetchData };
}

// Hook for fetching technical indicators
export function useTechnicalIndicators(symbol: string | null): UseStockDataResult<TechnicalIndicators> {
    const [data, setData] = useState<TechnicalIndicators | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<ApiError | null>(null);

    const fetchData = useCallback(async () => {
        if (!symbol) return;

        setLoading(true);
        setError(null);

        try {
            const indicators = await stockService.getTechnicalIndicators(symbol);
            setData(indicators);
        } catch (err) {
            setError(err as ApiError);
        } finally {
            setLoading(false);
        }
    }, [symbol]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return { data, loading, error, refetch: fetchData };
}

// Hook for fetching stock news
export function useStockNews(symbol: string | null): UseStockDataResult<NewsArticle[]> {
    const [data, setData] = useState<NewsArticle[] | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<ApiError | null>(null);

    const fetchData = useCallback(async () => {
        if (!symbol) return;

        setLoading(true);
        setError(null);

        try {
            const news = await stockService.getStockNews(symbol);
            setData(news);
        } catch (err) {
            setError(err as ApiError);
        } finally {
            setLoading(false);
        }
    }, [symbol]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return { data, loading, error, refetch: fetchData };
}

// Hook for fetching paginated stocks
export function usePaginatedStocks(page: number, limit: number, autoRefresh: boolean = false): UseStockDataResult<PaginatedStocks> {
    const [data, setData] = useState<PaginatedStocks | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<ApiError | null>(null);

    const fetchData = useCallback(async (isInitial: boolean = true) => {
        if (isInitial) setLoading(true);
        setError(null);

        try {
            const stocks = await stockService.getPaginatedStocks(page, limit);
            setData(stocks);
        } catch (err) {
            setError(err as ApiError);
        } finally {
            if (isInitial) setLoading(false);
        }
    }, [page, limit]);

    useEffect(() => {
        fetchData(true);

        if (autoRefresh) {
            const interval = setInterval(() => fetchData(false), POLLING_INTERVAL);
            return () => clearInterval(interval);
        }
    }, [fetchData, autoRefresh]);

    return { data, loading, error, refetch: () => fetchData(true) };
}

// Hook for detailed search
export function useDetailedSearch(query: string, autoRefresh: boolean = false): UseStockDataResult<StockQuote[]> {
    const [data, setData] = useState<StockQuote[] | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<ApiError | null>(null);

    const fetchData = useCallback(async (isInitial: boolean = true) => {
        if (!query) {
            setData(null);
            return;
        }

        if (isInitial) setLoading(true);
        setError(null);

        try {
            const stocks = await stockService.getDetailedSearchResults(query);
            setData(stocks);
        } catch (err) {
            setError(err as ApiError);
        } finally {
            if (isInitial) setLoading(false);
        }
    }, [query]);

    useEffect(() => {
        const timeoutId = setTimeout(() => {
            fetchData(true);
        }, 500); // 500ms debounce

        return () => clearTimeout(timeoutId);
    }, [fetchData]);

    useEffect(() => {
        if (autoRefresh && query) {
            const interval = setInterval(() => fetchData(false), POLLING_INTERVAL);
            return () => clearInterval(interval);
        }
    }, [fetchData, autoRefresh, query]);

    return { data, loading, error, refetch: () => fetchData(true) };
}
