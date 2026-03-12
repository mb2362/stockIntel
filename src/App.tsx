import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { WatchlistProvider } from './context/WatchlistContext';
import { MainLayout } from './components/layout/MainLayout';

// Lazy load pages for code splitting
const Landing = React.lazy(() => import('./pages/Landing'));
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const StockDetails = React.lazy(() => import('./pages/StockDetails'));
const Watchlist = React.lazy(() => import('./pages/Watchlist'));
const Comparison = React.lazy(() => import('./pages/Comparison'));
const Analytics = React.lazy(() => import('./pages/Analytics'));
const StockList = React.lazy(() => import('./pages/StockList'));

function App() {
  return (
    <ThemeProvider>
      <WatchlistProvider>
        <BrowserRouter>
          <React.Suspense
            fallback={
              <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
              </div>
            }
          >
            <Routes>
              {/* Landing Page - No Layout */}
              <Route path="/" element={<Landing />} />

              {/* App Pages - With Layout */}
              <Route path="/app" element={<MainLayout />}>
                <Route index element={<Navigate to="/app/dashboard" replace />} />
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="stocks" element={<StockList />} />
                <Route path="stock/:symbol" element={<StockDetails />} />
                <Route path="watchlist" element={<Watchlist />} />
                <Route path="comparison" element={<Comparison />} />
                <Route path="analytics" element={<Analytics />} />
              </Route>

              {/* Redirect old routes */}
              <Route path="/dashboard" element={<Navigate to="/app/dashboard" replace />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </React.Suspense>
        </BrowserRouter>
      </WatchlistProvider>
    </ThemeProvider>
  );
}

export default App;
