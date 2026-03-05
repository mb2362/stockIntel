import api from './api';
import { mockApi } from './mockApi';
import type { WatchlistItem } from '../types/stock';

const USE_MOCK_API = true;

export const watchlistService = {
    // Get watchlist
    async getWatchlist(): Promise<WatchlistItem[]> {
        if (USE_MOCK_API) {
            return mockApi.getWatchlist();
        }
        const response = await api.get('/watchlist');
        return response.data;
    },

    // Add to watchlist
    async addToWatchlist(symbol: string): Promise<WatchlistItem> {
        if (USE_MOCK_API) {
            return mockApi.addToWatchlist(symbol);
        }
        const response = await api.post('/watchlist', { symbol });
        return response.data;
    },

    // Remove from watchlist
    async removeFromWatchlist(symbol: string): Promise<void> {
        if (USE_MOCK_API) {
            return mockApi.removeFromWatchlist(symbol);
        }
        await api.delete(`/watchlist/${symbol}`);
    },
};
