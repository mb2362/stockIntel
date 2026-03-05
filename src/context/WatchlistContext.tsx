import React, { createContext, useContext, useState, useEffect } from 'react';
import { watchlistService } from '../services/watchlistService';
import type { WatchlistItem } from '../types/stock';
import { POLLING_INTERVAL } from '../utils/constants';

interface WatchlistContextType {
    watchlist: WatchlistItem[];
    loading: boolean;
    addStock: (symbol: string) => Promise<void>;
    removeStock: (symbol: string) => Promise<void>;
    isInWatchlist: (symbol: string) => boolean;
    refreshWatchlist: () => Promise<void>;
}

const WatchlistContext = createContext<WatchlistContextType | undefined>(undefined);

export function WatchlistProvider({ children }: { children: React.ReactNode }) {
    const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
    const [loading, setLoading] = useState(false);

    const fetchWatchlist = async () => {
        try {
            const data = await watchlistService.getWatchlist();
            setWatchlist(data);
        } catch (error) {
            console.error('Error fetching watchlist:', error);
        }
    };

    const addStock = async (symbol: string) => {
        setLoading(true);
        try {
            const item = await watchlistService.addToWatchlist(symbol);
            setWatchlist((prev) => [...prev, item]);
        } catch (error) {
            console.error('Error adding to watchlist:', error);
            throw error;
        } finally {
            setLoading(false);
        }
    };

    const removeStock = async (symbol: string) => {
        setLoading(true);
        try {
            await watchlistService.removeFromWatchlist(symbol);
            setWatchlist((prev) => prev.filter((item) => item.symbol !== symbol));
        } catch (error) {
            console.error('Error removing from watchlist:', error);
            throw error;
        } finally {
            setLoading(false);
        }
    };

    const isInWatchlist = (symbol: string) => {
        return watchlist.some((item) => item.symbol === symbol);
    };

    const refreshWatchlist = async () => {
        await fetchWatchlist();
    };

    // Initial fetch and polling
    useEffect(() => {
        fetchWatchlist();

        const interval = setInterval(fetchWatchlist, POLLING_INTERVAL);
        return () => clearInterval(interval);
    }, []);

    return (
        <WatchlistContext.Provider
            value={{
                watchlist,
                loading,
                addStock,
                removeStock,
                isInWatchlist,
                refreshWatchlist,
            }}
        >
            {children}
        </WatchlistContext.Provider>
    );
}

export function useWatchlist() {
    const context = useContext(WatchlistContext);
    if (context === undefined) {
        throw new Error('useWatchlist must be used within a WatchlistProvider');
    }
    return context;
}
