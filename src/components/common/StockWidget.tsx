import { Card } from './Card';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorMessage } from './ErrorMessage';
import { formatPrice, formatPercentage } from '../../utils/formatters';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import type { TrendingStock } from '../../types/market';
import type { ApiError } from '../../types/api';

interface StockWidgetProps {
    title: string;
    stocks: TrendingStock[] | null;
    loading: boolean;
    error: ApiError | null;
    onRetry: () => void;
    accentColor?: 'success' | 'danger' | 'primary';
}

export function StockWidget({
    title,
    stocks,
    loading,
    error,
    onRetry,
    accentColor = 'primary'
}: StockWidgetProps) {
    const navigate = useNavigate();

    return (
        <section>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                {title}
            </h2>

            {loading ? (
                <LoadingSpinner />
            ) : error ? (
                <ErrorMessage error={error} onRetry={onRetry} />
            ) : stocks ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                    {stocks.map((stock) => (
                        <Card
                            key={stock.symbol}
                            className="cursor-pointer hover:shadow-xl transition-all hover:scale-105"
                            onClick={() => navigate(`/app/stock/${stock.symbol}`)}
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <h3 className="font-bold text-lg text-gray-900 dark:text-gray-100">
                                        {stock.symbol}
                                    </h3>
                                    <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                                        {stock.name}
                                    </p>
                                </div>
                                <div className={clsx(
                                    'text-xs font-semibold px-2 py-1 rounded',
                                    stock.changePercent >= 0
                                        ? 'bg-success-100 dark:bg-success-900 text-success-700 dark:text-success-300'
                                        : 'bg-danger-100 dark:bg-danger-900 text-danger-700 dark:text-danger-300'
                                )}>
                                    {formatPercentage(stock.changePercent)}
                                </div>
                            </div>

                            <div className="mt-2">
                                <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
                                    {formatPrice(stock.price)}
                                </p>
                            </div>

                            {/* Mini sparkline */}
                            {stock.sparkline && stock.sparkline.length > 0 && (
                                <div className="mt-3 h-8 flex items-end gap-0.5">
                                    {stock.sparkline.map((value, index) => {
                                        const max = Math.max(...stock.sparkline!);
                                        const min = Math.min(...stock.sparkline!);
                                        const height = ((value - min) / (max - min)) * 100;

                                        return (
                                            <div
                                                key={index}
                                                className={clsx(
                                                    'flex-1 rounded-t',
                                                    stock.changePercent >= 0 ? 'bg-success-400' : 'bg-danger-400'
                                                )}
                                                style={{ height: `${Math.max(height, 10)}%` }}
                                            />
                                        );
                                    })}
                                </div>
                            )}
                        </Card>
                    ))}
                </div>
            ) : null}
        </section>
    );
}
