import api from './api';
import { mockApi } from './mockApi';
import type { MarketOverview, TrendingStock } from '../types/market';
import type { ComparisonData } from '../types/api';

const USE_MOCK_API = true;

export const marketService = {
    // Get market overview
    async getMarketOverview(): Promise<MarketOverview> {
        if (USE_MOCK_API) {
            return mockApi.getMarketOverview();
        }
        const response = await api.get('/market/overview');
        return response.data;
    },

    // Get trending stocks
    async getTrendingStocks(): Promise<TrendingStock[]> {
        if (USE_MOCK_API) {
            return mockApi.getTrendingStocks();
        }
        const response = await api.get('/market/trending');
        return response.data;
    },

    // Get top gainers
    async getTopGainers(): Promise<TrendingStock[]> {
        if (USE_MOCK_API) {
            return mockApi.getTopGainers();
        }
        const response = await api.get('/market/gainers');
        return response.data;
    },

    // Get top losers
    async getTopLosers(): Promise<TrendingStock[]> {
        if (USE_MOCK_API) {
            return mockApi.getTopLosers();
        }
        const response = await api.get('/market/losers');
        return response.data;
    },

    // Compare stocks
    async compareStocks(symbols: string[]): Promise<ComparisonData> {
        if (USE_MOCK_API) {
            return mockApi.compareStocks(symbols);
        }
        const response = await api.post('/stocks/compare', { symbols });
        return response.data;
    },
};
