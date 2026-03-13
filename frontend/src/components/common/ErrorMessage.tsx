import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import type { ApiError } from '../../types/api';

interface ErrorMessageProps {
    error: ApiError | Error | string;
    onRetry?: () => void;
    className?: string;
}

export function ErrorMessage({ error, onRetry, className }: ErrorMessageProps) {
    const message = typeof error === 'string'
        ? error
        : 'message' in error
            ? error.message
            : 'An unexpected error occurred';

    return (
        <div className={`flex flex-col items-center justify-center p-6 ${className || ''}`}>
            <AlertCircle className="w-12 h-12 text-danger-500 mb-4" />
            <p className="text-gray-700 dark:text-gray-300 text-center mb-4">{message}</p>
            {onRetry && (
                <button
                    onClick={onRetry}
                    className="flex items-center gap-2 btn-primary"
                >
                    <RefreshCw className="w-4 h-4" />
                    Try Again
                </button>
            )}
        </div>
    );
}
