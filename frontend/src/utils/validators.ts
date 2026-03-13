// Validation utilities
export const isValidStockSymbol = (symbol: string): boolean => {
    // Stock symbols are typically 1-5 uppercase letters
    return /^[A-Z]{1,5}$/.test(symbol);
};

export const isValidEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
};

export const isValidNumber = (value: any): boolean => {
    return typeof value === 'number' && !isNaN(value) && isFinite(value);
};

export const isValidDate = (date: any): boolean => {
    return date instanceof Date && !isNaN(date.getTime());
};

export const sanitizeSymbol = (symbol: string): string => {
    return symbol.toUpperCase().trim();
};
