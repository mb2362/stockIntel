import api from './api';
import { mockApi } from './mockApi';
import type {
    StockQuote,
    StockDetails,
    HistoricalDataPoint,
    TechnicalIndicators,
    NewsArticle,
    TimeRange,
} from '../types/stock';
import type { SearchResult } from '../types/api';

// Use mock API for now (switch to real API when backend is ready)
const USE_MOCK_API = true;

export const stockService = {
    // Search stocks
    async searchStocks(query: string): Promise<SearchResult[]> {
        if (USE_MOCK_API) {
            return mockApi.searchStocks(query);
        }
        const response = await api.get(`/stocks/search`, { params: { q: query } });
        return response.data;
    },

    // Get stock quote
    async getStockQuote(symbol: string): Promise<StockQuote> {
        if (USE_MOCK_API) {
            return mockApi.getStockQuote(symbol);
        }
        const response = await api.get(`/stocks/${symbol}/quote`);
        return response.data;
    },

    // Get stock details
    async getStockDetails(symbol: string): Promise<StockDetails> {
        if (USE_MOCK_API) {
            return mockApi.getStockDetails(symbol);
        }
        const response = await api.get(`/stocks/${symbol}/info`);
        return response.data;
    },

    // Get historical data
    async getHistoricalData(symbol: string, range: TimeRange): Promise<HistoricalDataPoint[]> {
        if (USE_MOCK_API) {
            return mockApi.getHistoricalData(symbol, range);
        }
        const response = await api.get(`/stocks/${symbol}/historical`, { params: { range } });
        return response.data;
    },

    // Get technical indicators
    async getTechnicalIndicators(symbol: string): Promise<TechnicalIndicators> {
        if (USE_MOCK_API) {
            return mockApi.getTechnicalIndicators(symbol);
        }
        const response = await api.get(`/stocks/${symbol}/indicators`);
        return response.data;
    },

    // Get stock news
    async getStockNews(symbol: string): Promise<NewsArticle[]> {
        if (USE_MOCK_API) {
            return mockApi.getStockNews(symbol);
        }
        const response = await api.get(`/stocks/${symbol}/news`);
        return response.data;
    },

    // Get all stocks
    async getAllStocks(): Promise<StockQuote[]> {
        if (USE_MOCK_API) {
            return mockApi.getAllStocks();
        }
        const response = await api.get(`/stocks`);
        return response.data;
    },
};
