import React from 'react';
import clsx from 'clsx';

interface CardProps {
    children: React.ReactNode;
    className?: string;
    variant?: 'elevated' | 'outlined';
    onClick?: () => void;
}

export function Card({ children, className, variant = 'elevated', onClick }: CardProps) {
    const baseClasses = 'rounded-lg p-4 transition-all';
    const variantClasses = {
        elevated: 'bg-white dark:bg-gray-800 shadow-md hover:shadow-lg',
        outlined: 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700',
    };

    return (
        <div
            className={clsx(
                baseClasses,
                variantClasses[variant],
                onClick && 'cursor-pointer',
                className
            )}
            onClick={onClick}
        >
            {children}
        </div>
    );
}
