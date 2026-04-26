import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { watchlistService } from '../services/watchlistService';
import { stockService } from '../services/stockService';
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
    // Keep a ref to the current symbol list so the price-refresh interval always
    // has access to the latest symbols without needing to be recreated.
    const symbolsRef = useRef<string[]>([]);

    /** Fetch the watchlist from the DB, then enrich each item with a live quote. */
    const fetchWatchlist = async (isInitial = false) => {
        try {
            if (isInitial) setLoading(true);

            // 1. Load list of symbols from the DB
            const items = await watchlistService.getWatchlist();
            symbolsRef.current = items.map((i) => i.symbol);

            // 2. Fetch live quotes for every symbol concurrently
            const enriched = await Promise.all(
                items.map(async (item) => {
                    try {
                        const quote = await stockService.getStockQuote(item.symbol);
                        return {
                            ...item,
                            name: quote.name || item.name,
                            price: quote.price,
                            change: quote.change,
                            changePercent: quote.changePercent,
                            volume: quote.volume,
                            marketCap: quote.marketCap,
                        } as WatchlistItem;
                    } catch {
                        return item; // keep the old data if the quote fails
                    }
                })
            );

            setWatchlist(enriched);
        } catch (error) {
            console.error('Error fetching watchlist:', error);
        } finally {
            if (isInitial) setLoading(false);
        }
    };

    const addStock = async (symbol: string) => {
        setLoading(true);
        try {
            const item = await watchlistService.addToWatchlist(symbol);
            // Enrich with a live quote right away
            try {
                const quote = await stockService.getStockQuote(symbol);
                const enrichedItem: WatchlistItem = {
                    ...item,
                    name: quote.name || item.name,
                    price: quote.price,
                    change: quote.change,
                    changePercent: quote.changePercent,
                    volume: quote.volume,
                    marketCap: quote.marketCap,
                };
                setWatchlist((prev) => [...prev, enrichedItem]);
                symbolsRef.current = [...symbolsRef.current, symbol];
            } catch {
                setWatchlist((prev) => [...prev, item]);
            }
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
            symbolsRef.current = symbolsRef.current.filter((s) => s !== symbol);
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
        await fetchWatchlist(true);
    };

    // Initial fetch, then refresh only the live prices on each POLLING_INTERVAL tick
    useEffect(() => {
        fetchWatchlist(true);

        const interval = setInterval(async () => {
            const symbols = symbolsRef.current;
            if (symbols.length === 0) return;
            // Quietly refresh prices without touching loading state
            try {
                const quotes = await Promise.all(
                    symbols.map((sym) => stockService.getStockQuote(sym).catch(() => null))
                );
                setWatchlist((prev) =>
                    prev.map((item) => {
                        const quote = quotes.find((q) => q?.symbol === item.symbol);
                        if (!quote) return item;
                        return {
                            ...item,
                            price: quote.price,
                            change: quote.change,
                            changePercent: quote.changePercent,
                            volume: quote.volume,
                        };
                    })
                );
            } catch {
                // silently suppress polling errors
            }
        }, POLLING_INTERVAL);

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
