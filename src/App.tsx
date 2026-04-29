import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
// Lazy load pages for code splitting
const Landing = React.lazy(() => import('./pages/Landing'));

function App() {
  return (
  
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
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </React.Suspense>
        </BrowserRouter>
  );
}

export default App;
