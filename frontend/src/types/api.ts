// API response types
export interface ApiResponse<T> {
    data: T;
    status: number;
    message?: string;
}

export interface ApiError {
    message: string;
    code?: string;
    status?: number;
}

export interface SearchResult {
    symbol: string;
    name: string;
    type: string;
    region: string;
    currency: string;
}

export interface ComparisonData {
    symbols: string[];
    data: {
        [symbol: string]: {
            name: string;
            price: number;
            change: number;
            changePercent: number;
            marketCap: number;
            peRatio?: number;
            volume: number;
            historical: Array<{
                date: string;
                close: number;
            }>;
        };
    };
}
