import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';

export function MainLayout() {
    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <Header />
            <main className="container mx-auto px-4 py-6">
                <Outlet />
            </main>
        </div>
    );
}
