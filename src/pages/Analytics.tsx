import React from 'react';
import { Card } from '../components/common/Card';

export default function Analytics() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                    Analytics Dashboard
                </h1>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                    Portfolio performance and insights
                </p>
            </div>

            <Card>
                <div className="text-center py-12">
                    <p className="text-gray-600 dark:text-gray-400 text-lg">
                        Analytics dashboard coming soon...
                    </p>
                    <p className="text-gray-500 dark:text-gray-500 text-sm mt-2">
                        Track your portfolio performance and get insights
                    </p>
                </div>
            </Card>
        </div>
    );
}
