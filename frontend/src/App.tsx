import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './components/Layout/AppLayout';
import ErrorBoundary from './components/UI/ErrorBoundary';

import OverviewPage from './pages/OverviewPage';
import FarmMonitoringPage from './pages/FarmMonitoringPage';
import BigDataAnalyticsPage from './pages/BigDataAnalyticsPage';
import MLLabPage from './pages/MLLabPage';
import FogNodeMonitorPage from './pages/FogNodeMonitorPage';
import CloudMonitoringPage from './pages/CloudMonitoringPage';
import ExperimentLabPage from './pages/ExperimentLabPage';
import DataAuditPage from './pages/DataAuditPage';

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AppLayout>
          <Routes>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/farms" element={<FarmMonitoringPage />} />
            <Route path="/bigdata" element={<BigDataAnalyticsPage />} />
            <Route path="/ml" element={<MLLabPage />} />
            <Route path="/fog" element={<FogNodeMonitorPage />} />
            <Route path="/cloud" element={<CloudMonitoringPage />} />
            <Route path="/experiments" element={<ExperimentLabPage />} />
            <Route path="/audit" element={<DataAuditPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AppLayout>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

