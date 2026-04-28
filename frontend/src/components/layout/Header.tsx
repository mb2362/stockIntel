import { Link, useLocation } from 'react-router-dom';
import { Moon, Sun, TrendingUp, LayoutDashboard, Star, BarChart3, Sparkles, CandlestickChart } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { SearchBar } from '../common/SearchBar';

export function Header() {
    const { theme, toggleTheme } = useTheme();
    const location = useLocation();

    const isActive = (path: string) => {
        return location.pathname === path || location.pathname.startsWith(path);
    };

    const showSearch =
        location.pathname.startsWith('/app/dashboard') ||
        location.pathname.startsWith('/app/stocks');

    const searchPlaceholder =
        location.pathname.startsWith('/app/dashboard')
            ? 'Search dashboard...'
            : 'Search stocks...';

    return (
        <header className="sticky top-0 z-40 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 shadow-sm">
            <div className="container mx-auto px-4">
                <div className="flex items-center justify-between h-16">

                    {/* Logo */}
                    <Link to="/app/dashboard" className="flex items-center gap-2 font-bold text-xl text-primary-600 dark:text-primary-400 shrink-0">
                        <TrendingUp className="w-8 h-8" />
                        <span className="hidden sm:inline">StockIntel</span>
                    </Link>

                    {/* Search Bar - Desktop (only on Dashboard & Market) */}
                    {showSearch && (
                        <div className="hidden md:block flex-1 max-w-md mx-8">
                            <SearchBar placeholder={searchPlaceholder} />
                        </div>
                    )}

                    {/* Navigation — evenly distributed when no search bar */}
                    <nav className={`flex items-center gap-1 sm:gap-2 ${!showSearch ? 'flex-1 justify-around ml-8' : ''}`}>
                        <Link
                            to="/app/dashboard"
                            className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                                isActive('/app/dashboard')
                                    ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                            }`}
                        >
                            <LayoutDashboard className="w-5 h-5" />
                            <span className="hidden sm:inline">Dashboard</span>
                        </Link>

                        <Link
                            to="/app/stocks"
                            className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                                isActive('/app/stocks')
                                    ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                            }`}
                        >
                            <CandlestickChart className="w-5 h-5" />
                            <span className="hidden sm:inline">Market</span>
                        </Link>

                        <Link
                            to="/app/watchlist"
                            className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                                isActive('/app/watchlist')
                                    ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                            }`}
                        >
                            <Star className="w-5 h-5" />
                            <span className="hidden sm:inline">Watchlist</span>
                        </Link>

                        <Link
                            to="/app/predict"
                            className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                                isActive('/app/predict')
                                    ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                            }`}
                        >
                            <Sparkles className="w-5 h-5" />
                            <span className="hidden sm:inline">Predict</span>
                        </Link>

                        <Link
                            to="/app/analytics"
                            className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                                isActive('/app/analytics')
                                    ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                            }`}
                        >
                            <BarChart3 className="w-5 h-5" />
                            <span className="hidden sm:inline">Analytics</span>
                        </Link>

                        {/* Theme Toggle */}
                        <button
                            onClick={toggleTheme}
                            className="p-2 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                            aria-label="Toggle theme"
                        >
                            {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
                        </button>
                    </nav>
                </div>

                {/* Search Bar - Mobile (only on Dashboard & Market) */}
                {showSearch && (
                    <div className="md:hidden pb-3">
                        <SearchBar placeholder={searchPlaceholder} />
                    </div>
                )}
            </div>
        </header>
    );
}