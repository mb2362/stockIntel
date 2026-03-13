// Market-related types
export interface MarketIndex {
    symbol: string;
    name: string;
    value: number;
    change: number;
    changePercent: number;
}

export interface MarketOverview {
    indices: MarketIndex[];
    marketStatus: 'open' | 'closed' | 'pre-market' | 'after-hours';
    lastUpdated: string;
}

export interface TrendingStock {
    symbol: string;
    name: string;
    price: number;
    changePercent: number;
    volume: number;
    sparkline?: number[];
}

export interface SectorPerformance {
    sector: string;
    changePercent: number;
    marketCap: number;
}
