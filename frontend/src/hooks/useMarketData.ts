import { useState, useEffect, useCallback } from 'react';
import { marketService } from '../services/marketService';
import type { MarketOverview, TrendingStock } from '../types/market';
import type { ApiError } from '../types/api';
import { POLLING_INTERVAL } from '../utils/constants';

interface UseMarketDataResult<T> {
    data: T | null;
    loading: boolean;
    error: ApiError | null;
    refetch: () => Promise<void>;
}

// Hook for fetching market overview with auto-refresh
export function useMarketOverview(autoRefresh: boolean = false): UseMarketDataResult<MarketOverview> {
    const [data, setData] = useState<MarketOverview | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<ApiError | null>(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const overview = await marketService.getMarketOverview();
            setData(overview);
        } catch (err) {
            setError(err as ApiError);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();

        if (autoRefresh) {
            const interval = setInterval(fetchData, POLLING_INTERVAL);
            return () => clearInterval(interval);
        }
    }, [fetchData, autoRefresh]);

    return { data, loading, error, refetch: fetchData };
}

// Hook for fetching trending stocks
export function useTrendingStocks(): UseMarketDataResult<TrendingStock[]> {
    const [data, setData] = useState<TrendingStock[] | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<ApiError | null>(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const trending = await marketService.getTrendingStocks();
            setData(trending);
        } catch (err) {
            setError(err as ApiError);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return { data, loading, error, refetch: fetchData };
}

// Hook for fetching top gainers
export function useTopGainers(): UseMarketDataResult<TrendingStock[]> {
    const [data, setData] = useState<TrendingStock[] | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<ApiError | null>(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const gainers = await marketService.getTopGainers();
            setData(gainers);
        } catch (err) {
            setError(err as ApiError);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return { data, loading, error, refetch: fetchData };
}

// Hook for fetching top losers
export function useTopLosers(): UseMarketDataResult<TrendingStock[]> {
    const [data, setData] = useState<TrendingStock[] | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<ApiError | null>(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const losers = await marketService.getTopLosers();
            setData(losers);
        } catch (err) {
            setError(err as ApiError);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return { data, loading, error, refetch: fetchData };
}
