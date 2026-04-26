import type {
    Stock,
    StockQuote,
    StockDetails,
    HistoricalDataPoint,
    TechnicalIndicators,
    NewsArticle,
    TimeRange,
    WatchlistItem,
} from '../types/stock';
import type { MarketIndex, MarketOverview, TrendingStock } from '../types/market';
import type { SearchResult, ComparisonData } from '../types/api';
import { POPULAR_STOCKS, SECTORS, MAJOR_INDICES } from '../utils/constants';

// Mock data generator for realistic stock market data
class MockApiService {
    private basePrice = new Map<string, number>();
    private watchlist: WatchlistItem[] = [];

    constructor() {
        // Initialize base prices for popular stocks
        POPULAR_STOCKS.forEach((symbol, index) => {
            this.basePrice.set(symbol, 100 + index * 50);
        });

        MAJOR_INDICES.forEach((index) => {
            if (index.symbol === '^GSPC') this.basePrice.set(index.symbol, 4500);
            if (index.symbol === '^IXIC') this.basePrice.set(index.symbol, 14000);
            if (index.symbol === '^DJI') this.basePrice.set(index.symbol, 35000);
        });
    }

    // Simulate API delay
    private delay(ms: number = 300): Promise<void> {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }

    // Generate random price fluctuation
    private getFluctuation(basePrice: number): number {
        const fluctuation = (Math.random() - 0.5) * 0.05; // ±2.5%
        return basePrice * (1 + fluctuation);
    }

    // Generate stock quote
    async getStockQuote(symbol: string): Promise<StockQuote> {
        await this.delay();

        const basePrice = this.basePrice.get(symbol) || 100 + Math.random() * 200;
        this.basePrice.set(symbol, basePrice);

        const currentPrice = this.getFluctuation(basePrice);
        const previousClose = basePrice;
        const change = currentPrice - previousClose;
        const changePercent = (change / previousClose) * 100;

        return {
            symbol,
            name: this.getCompanyName(symbol),
            price: currentPrice,
            change,
            changePercent,
            volume: Math.floor(Math.random() * 100000000),
            marketCap: currentPrice * (Math.random() * 10000000000),
            open: basePrice * (1 + (Math.random() - 0.5) * 0.02),
            high: currentPrice * (1 + Math.random() * 0.03),
            low: currentPrice * (1 - Math.random() * 0.03),
            previousClose,
            fiftyTwoWeekHigh: basePrice * 1.3,
            fiftyTwoWeekLow: basePrice * 0.7,
            peRatio: 15 + Math.random() * 30,
            dividendYield: Math.random() * 3,
            beta: 0.8 + Math.random() * 0.8,
            sector: SECTORS[Math.floor(Math.random() * SECTORS.length)],
            industry: 'Software',
        };
    }

    // Generate company details
    async getStockDetails(symbol: string): Promise<StockDetails> {
        await this.delay();
        const quote = await this.getStockQuote(symbol);

        return {
            ...quote,
            description: `${quote.name} is a leading company in the ${quote.sector} sector, providing innovative solutions and services to customers worldwide.`,
            ceo: 'John Doe',
            employees: Math.floor(Math.random() * 100000) + 1000,
            headquarters: 'Cupertino, CA',
            founded: String(1970 + Math.floor(Math.random() * 50)),
            website: `https://www.${symbol.toLowerCase()}.com`,
        };
    }

    // Generate historical data
    async getHistoricalData(symbol: string, range: TimeRange): Promise<HistoricalDataPoint[]> {
        await this.delay();

        const basePrice = this.basePrice.get(symbol) || 100;
        const days = this.getDaysFromRange(range);
        const data: HistoricalDataPoint[] = [];

        let currentPrice = basePrice;
        const now = new Date();

        for (let i = days; i >= 0; i--) {
            const date = new Date(now);
            date.setDate(date.getDate() - i);

            // Random walk
            const change = (Math.random() - 0.48) * 0.02; // Slight upward bias
            currentPrice = currentPrice * (1 + change);

            const open = currentPrice * (1 + (Math.random() - 0.5) * 0.01);
            const close = currentPrice;
            const high = Math.max(open, close) * (1 + Math.random() * 0.02);
            const low = Math.min(open, close) * (1 - Math.random() * 0.02);

            data.push({
                date: date.toISOString().split('T')[0],
                open,
                high,
                low,
                close,
                volume: Math.floor(Math.random() * 50000000) + 10000000,
            });
        }

        return data;
    }

    // Generate technical indicators
    async getTechnicalIndicators(symbol: string): Promise<TechnicalIndicators> {
        await this.delay();

        const currentPrice = this.basePrice.get(symbol) || 100;

        return {
            symbol,
            ma50: currentPrice * (0.95 + Math.random() * 0.1),
            ma200: currentPrice * (0.9 + Math.random() * 0.2),
            rsi: 30 + Math.random() * 40, // RSI between 30-70
            macd: {
                value: (Math.random() - 0.5) * 2,
                signal: (Math.random() - 0.5) * 1.8,
                histogram: (Math.random() - 0.5) * 0.5,
            },
        };
    }

    // Generate news articles
    async getStockNews(symbol: string): Promise<NewsArticle[]> {
        await this.delay();

        const companyName = this.getCompanyName(symbol);
        const headlines = [
            `${companyName} Reports Strong Q4 Earnings`,
            `${companyName} Announces New Product Launch`,
            `Analysts Upgrade ${companyName} Stock Rating`,
            `${companyName} CEO Discusses Future Strategy`,
            `${companyName} Expands Into New Markets`,
            `${companyName} Stock Reaches New High`,
        ];

        return headlines.slice(0, 5).map((title, index) => ({
            id: `news-${symbol}-${index}`,
            title,
            source: ['Reuters', 'Bloomberg', 'CNBC', 'WSJ', 'Financial Times'][index],
            url: `https://example.com/news/${symbol.toLowerCase()}-${index}`,
            publishedAt: new Date(Date.now() - index * 3600000).toISOString(),
            summary: `${title}. Read more about the latest developments and market analysis.`,
            imageUrl: `https://picsum.photos/seed/${symbol}${index}/400/200`,
            sentiment: ['positive', 'neutral', 'positive', 'neutral', 'positive'][index] as any,
        }));
    }

    // Search stocks
    async searchStocks(query: string): Promise<SearchResult[]> {
        await this.delay(200);

        const allSymbols = [...POPULAR_STOCKS, 'NFLX', 'DIS', 'BA', 'GE', 'F', 'GM', 'T', 'VZ'];
        const results = allSymbols
            .filter((symbol) => symbol.toLowerCase().includes(query.toLowerCase()))
            .slice(0, 10)
            .map((symbol) => ({
                symbol,
                name: this.getCompanyName(symbol),
                type: 'Equity',
                region: 'United States',
                currency: 'USD',
            }));

        return results;
    }

    // Get market overview
    async getMarketOverview(): Promise<MarketOverview> {
        await this.delay();

        const indices: MarketIndex[] = await Promise.all(
            MAJOR_INDICES.map(async (index) => {
                const baseValue = this.basePrice.get(index.symbol) || 10000;
                const value = this.getFluctuation(baseValue);
                const change = value - baseValue;
                const changePercent = (change / baseValue) * 100;

                return {
                    symbol: index.symbol,
                    name: index.name,
                    value,
                    change,
                    changePercent,
                };
            })
        );

        const hour = new Date().getHours();
        let marketStatus: MarketOverview['marketStatus'] = 'closed';
        if (hour >= 9 && hour < 16) marketStatus = 'open';
        else if (hour >= 4 && hour < 9) marketStatus = 'pre-market';
        else if (hour >= 16 && hour < 20) marketStatus = 'after-hours';

        return {
            indices,
            marketStatus,
            lastUpdated: new Date().toISOString(),
        };
    }

    // Get trending stocks
    async getTrendingStocks(): Promise<TrendingStock[]> {
        await this.delay();

        return POPULAR_STOCKS.slice(0, 10).map((symbol) => {
            const basePrice = this.basePrice.get(symbol) || 100;
            const price = this.getFluctuation(basePrice);
            const changePercent = ((price - basePrice) / basePrice) * 100;

            // Generate sparkline data (last 7 days)
            const sparkline = Array.from({ length: 7 }, (_, i) => {
                return basePrice * (1 + (Math.random() - 0.5) * 0.1);
            });

            return {
                symbol,
                name: this.getCompanyName(symbol),
                price,
                changePercent,
                volume: Math.floor(Math.random() * 100000000),
                sparkline,
            };
        });
    }

    // Get top gainers
    async getTopGainers(): Promise<TrendingStock[]> {
        await this.delay();
        // Simulate high gainers
        return ['NVDA', 'TSLA', 'META', 'AMZN', 'NFLX'].map(symbol => {
            const basePrice = this.basePrice.get(symbol) || 100;
            const price = basePrice * (1.05 + Math.random() * 0.05); // 5-10% gain
            return {
                symbol,
                name: this.getCompanyName(symbol),
                price,
                changePercent: ((price - basePrice) / basePrice) * 100,
                volume: Math.floor(Math.random() * 50000000) + 10000000,
                sparkline: Array.from({ length: 7 }, () => basePrice * (1 + Math.random() * 0.1))
            };
        });
    }

    // Get top losers
    async getTopLosers(): Promise<TrendingStock[]> {
        await this.delay();
        // Simulate high losers
        return ['JPM', 'V', 'WMT', 'BA', 'DIS'].map(symbol => {
            const basePrice = this.basePrice.get(symbol) || 100;
            const price = basePrice * (0.90 + Math.random() * 0.05); // 5-10% loss
            return {
                symbol,
                name: this.getCompanyName(symbol),
                price,
                changePercent: ((price - basePrice) / basePrice) * 100,
                volume: Math.floor(Math.random() * 50000000) + 10000000,
                sparkline: Array.from({ length: 7 }, () => basePrice * (0.9 + Math.random() * 0.1))
            };
        });
    }

    // Get all stocks
    async getAllStocks(): Promise<StockQuote[]> {
        await this.delay();

        const allSymbols = [...POPULAR_STOCKS, 'NFLX', 'DIS', 'BA', 'GE', 'F', 'GM', 'T', 'VZ'];
        return Promise.all(allSymbols.map(symbol => this.getStockQuote(symbol)));
    }

    // Compare stocks
    async compareStocks(symbols: string[]): Promise<ComparisonData> {
        await this.delay();

        const data: ComparisonData['data'] = {};

        for (const symbol of symbols) {
            const quote = await this.getStockQuote(symbol);
            const historical = await this.getHistoricalData(symbol, '1M');

            data[symbol] = {
                name: quote.name,
                price: quote.price,
                change: quote.change,
                changePercent: quote.changePercent,
                marketCap: quote.marketCap,
                peRatio: quote.peRatio,
                volume: quote.volume,
                historical: historical.map((h) => ({
                    date: h.date,
                    close: h.close,
                })),
            };
        }

        return {
            symbols,
            data,
        };
    }

    // Watchlist operations
    async getWatchlist(): Promise<WatchlistItem[]> {
        await this.delay(200);

        // Update prices for watchlist items
        const updated = await Promise.all(
            this.watchlist.map(async (item) => {
                const quote = await this.getStockQuote(item.symbol);
                return {
                    ...quote,
                    addedAt: item.addedAt,
                };
            })
        );

        return updated;
    }

    async addToWatchlist(symbol: string): Promise<WatchlistItem> {
        await this.delay(200);

        const quote = await this.getStockQuote(symbol);
        const item: WatchlistItem = {
            ...quote,
            addedAt: new Date().toISOString(),
        };

        this.watchlist.push(item);
        return item;
    }

    async removeFromWatchlist(symbol: string): Promise<void> {
        await this.delay(200);
        this.watchlist = this.watchlist.filter((item) => item.symbol !== symbol);
    }

    // Helper methods
    private getCompanyName(symbol: string): string {
        const names: Record<string, string> = {
            AAPL: 'Apple Inc.',
            MSFT: 'Microsoft Corporation',
            GOOGL: 'Alphabet Inc.',
            AMZN: 'Amazon.com Inc.',
            TSLA: 'Tesla Inc.',
            META: 'Meta Platforms Inc.',
            NVDA: 'NVIDIA Corporation',
            JPM: 'JPMorgan Chase & Co.',
            V: 'Visa Inc.',
            WMT: 'Walmart Inc.',
            NFLX: 'Netflix Inc.',
            DIS: 'The Walt Disney Company',
            BA: 'Boeing Company',
            GE: 'General Electric',
            F: 'Ford Motor Company',
            GM: 'General Motors',
            T: 'AT&T Inc.',
            VZ: 'Verizon Communications',
            '^GSPC': 'S&P 500',
            '^IXIC': 'NASDAQ Composite',
            '^DJI': 'Dow Jones Industrial Average',
        };

        return names[symbol] || `${symbol} Corporation`;
    }

    private getDaysFromRange(range: TimeRange): number {
        const ranges: Record<TimeRange, number> = {
            '1D': 1,
            '1W': 7,
            '1M': 30,
            '3M': 90,
            '1Y': 365,
            '5Y': 1825,
        };
        return ranges[range];
    }
}

// Export singleton instance
export const mockApi = new MockApiService();
