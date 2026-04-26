import React from 'react';
import { Loader2 } from 'lucide-react';
import clsx from 'clsx';

interface LoadingSpinnerProps {
    size?: 'sm' | 'md' | 'lg';
    className?: string;
}

export function LoadingSpinner({ size = 'md', className }: LoadingSpinnerProps) {
    const sizeClasses = {
        sm: 'w-4 h-4',
        md: 'w-8 h-8',
        lg: 'w-12 h-12',
    };

    return (
        <div className={clsx('flex items-center justify-center', className)}>
            <Loader2 className={clsx('animate-spin text-primary-600', sizeClasses[size])} />
        </div>
    );
}
