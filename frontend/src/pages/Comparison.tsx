import React from 'react';
import { Card } from '../components/common/Card';

export default function Comparison() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                    Stock Comparison
                </h1>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                    Compare multiple stocks side-by-side
                </p>
            </div>

            <Card>
                <div className="text-center py-12">
                    <p className="text-gray-600 dark:text-gray-400 text-lg">
                        Comparison tool coming soon...
                    </p>
                    <p className="text-gray-500 dark:text-gray-500 text-sm mt-2">
                        This feature will allow you to compare up to 4 stocks
                    </p>
                </div>
            </Card>
        </div>
    );
}
