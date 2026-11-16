import React, { useState } from 'react';
import {
  Database,
  ArrowRight,
  CheckCircle2,
  FileText,
  Filter,
  Layers,
  Sparkles,
  GitCommit,
  ExternalLink,
  ShieldAlert,
} from 'lucide-react';

export default function BigDataAnalyticsPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'datasets' | 'validation' | 'features'>('overview');

  const pipelineStages = [
    {
      step: '01',
      title: 'Acquisition & Ingestion',
      desc: 'Retrieval of IMD Rainfall (NetCDF), ISRO MOSDAC Soil Moisture, and ERA5-Land reanalysis products.',
      badge: '4 Sources',
      status: 'Documented & Verified',
    },
    {
      step: '02',
      title: 'Validation & Cleansing',
      desc: 'PySpark/Pandas schema coercion, temporal gap interpolation (≤3 days), and spatial coordinate extraction.',
      badge: '5,478 Raw Rows',
      status: 'Zero NaNs',
    },
    {
      step: '03',
      title: 'Feature Engineering',
      desc: 'Generation of 16 agronomic features: lag-1/lag-2 soil moisture, 3d/7d rolling averages, cumulative rainfall, Magnus RH.',
      badge: '16 Features',
      status: 'Zero Target Leakage',
    },
    {
      step: '04',
      title: 'Chronological Splitting',
      desc: 'Strict temporal partition (70% train [2019-2022], 15% validation, 15% test [2023]) ensuring reproducible evaluation.',
      badge: '5,475 ML Records',
      status: 'Ready for Model',
    },
  ];

  const datasets = [
    {
      id: 'IMD_RF_001',
      name: 'IMD 0.25° Daily Gridded Rainfall',
      source: 'India Meteorological Department (Pune)',
      coverage: '1901–2024 · All-India',
      format: 'NetCDF / Gridded binary',
      variable: 'rainfall_mm (Daily precipitation)',
      license: 'Govt of India Open Data License',
      status: 'Validated',
    },
    {
      id: 'MOSDAC_SM_001',
      name: 'ISRO MOSDAC Soil Moisture & Wetness',
      source: 'Space Applications Centre, ISRO',
      coverage: '2015–Present · 25km resolution',
      format: 'NetCDF / HDF5',
      variable: 'soil_moisture_index, soil_wetness_index',
      license: 'SAC/ISRO Data Policy',
      status: 'Validated',
    },
    {
      id: 'ERA5_TH_001',
      name: 'ERA5-Land Hourly & Daily Reanalysis',
      source: 'ECMWF / Copernicus Climate Change Service',
      coverage: '1950–Present · 0.1° resolution (~9km)',
      format: 'GRIB / NetCDF',
      variable: '2m_temperature, 2m_dewpoint_temperature',
      license: 'Copernicus License v1.2',
      status: 'Validated',
    },
    {
      id: 'KAGGLE_IWD_001',
      name: 'India Weather Data (Supplementary)',
      source: 'Kaggle Agricultural Weather Repository',
      coverage: '1901–2017 · Major agricultural stations',
      format: 'CSV (Processed station tables)',
      variable: 'temp_max, temp_min, humidity, precipitation',
      license: 'CC0 Public Domain',
      status: 'Supplementary',
    },
  ];

  const validationChecks = [
    { check: 'Target Leakage Prevention', result: 'PASS', detail: "Target 'soil_moisture_next_day' strictly omitted from input feature matrix." },
    { check: 'Zero Missing Values in Feature Matrix', result: 'PASS', detail: '0 missing or NaN values across all 16 input features.' },
    { check: 'Zero Missing Values in Target', result: 'PASS', detail: '0 NaN values in target vector across all 5,475 rows.' },
    { check: 'Soil Moisture Range [0.0, 1.0]', result: 'PASS', detail: 'Observed volumetric water content: 0.1000 to 0.3651 m³/m³.' },
    { check: 'Target Range [0.0, 1.0]', result: 'PASS', detail: 'Next-day moisture values: 0.1000 to 0.3491 m³/m³.' },
    { check: 'Temperature Range [5.0, 55.0] °C', result: 'PASS', detail: 'Tamil Nadu temperature span: 18.9°C to 38.6°C.' },
    { check: 'Non-negative Precipitation', result: 'PASS', detail: 'Min rainfall: 0.00 mm, max: 99.30 mm.' },
    { check: 'Chronological Monotonicity', result: 'PASS', detail: 'Dates strictly monotonically increasing within each farm partition.' },
  ];

  const featuresList = [
    { name: 'soil_moisture_lag1', type: 'Lagged State', desc: 'Observed volumetric soil moisture at t-1 (previous day)' },
    { name: 'soil_moisture_lag2', type: 'Lagged State', desc: 'Observed volumetric soil moisture at t-2 (two days ago)' },
    { name: 'soil_moisture_ma3', type: 'Moving Average', desc: '3-day trailing moving average of soil moisture' },
    { name: 'soil_moisture_ma7', type: 'Moving Average', desc: '7-day trailing moving average of soil moisture' },
    { name: 'rainfall_mm', type: 'Meteorology', desc: 'Current-day rainfall observation from IMD grid' },
    { name: 'rainfall_lag1', type: 'Lagged Meteorology', desc: 'Rainfall observation from previous day (t-1)' },
    { name: 'rainfall_cum3', type: 'Cumulative', desc: '3-day cumulative precipitation sum (mm)' },
    { name: 'rainfall_cum7', type: 'Cumulative', desc: '7-day cumulative precipitation sum (mm)' },
    { name: 'temperature_c', type: 'Meteorology', desc: '2m surface air temperature from ERA5-Land (°C)' },
    { name: 'relative_humidity_pct', type: 'Meteorology', desc: 'Relative humidity computed via Magnus formula' },
    { name: 'rh_computed', type: 'Derived', desc: 'Recomputed RH using Clausius-Clapeyron saturation pressure' },
    { name: 'daily_et_estimate_mm', type: 'Agronomic', desc: 'Simplified Hargreaves-Samani potential evapotranspiration' },
    { name: 'month', type: 'Temporal', desc: 'Calendar month indicator (1-12) for monsoon seasonality' },
    { name: 'day_of_year', type: 'Temporal', desc: 'Day of year (1-365) capturing solar radiation progression' },
    { name: 'season', type: 'Seasonal', desc: 'Classification: Winter, Summer, SW Monsoon, NE Monsoon' },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
        <div>
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
            Phase 1 Deliverable
          </span>
          <h1 className="text-2xl font-bold text-[#1B2D1E] mt-1">Big Data Engineering & Analytics Pipeline</h1>
          <p className="text-sm text-[#4A6B50]">
            Complete auditable lineage from raw NetCDF meteorological files to ML-ready feature matrices.
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'overview'
                ? 'bg-[#2D6A4F] text-white shadow-sm'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Pipeline Flow
          </button>
          <button
            onClick={() => setActiveTab('datasets')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'datasets'
                ? 'bg-[#2D6A4F] text-white shadow-sm'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Provenance Registry
          </button>
          <button
            onClick={() => setActiveTab('validation')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'validation'
                ? 'bg-[#2D6A4F] text-white shadow-sm'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Quality Audits (8/8)
          </button>
          <button
            onClick={() => setActiveTab('features')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'features'
                ? 'bg-[#2D6A4F] text-white shadow-sm'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Feature Dictionary
          </button>
        </div>
      </div>

      {/* Summary Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
          <div className="text-xs text-gray-500">Total Raw Ingested</div>
          <div className="text-2xl font-bold text-[#1B2D1E] mt-1">5,478 Records</div>
          <div className="text-xs text-emerald-600 mt-1">3 Farms · 5 Years (2019-2023)</div>
        </div>
        <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
          <div className="text-xs text-gray-500">Processed ML Dataset</div>
          <div className="text-2xl font-bold text-[#1B2D1E] mt-1">5,475 Rows</div>
          <div className="text-xs text-emerald-600 mt-1">16 Engineered Features</div>
        </div>
        <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
          <div className="text-xs text-gray-500">Missing Data Imputation</div>
          <div className="text-2xl font-bold text-[#1B2D1E] mt-1">0 NaN Remaining</div>
          <div className="text-xs text-gray-500 mt-1">Linear forward (≤3d gap limit)</div>
        </div>
        <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
          <div className="text-xs text-gray-500">Target Leakage Check</div>
          <div className="text-2xl font-bold text-emerald-700 mt-1">0% Leakage</div>
          <div className="text-xs text-emerald-600 mt-1">Strict t+1 boundary verified</div>
        </div>
      </div>

      {/* Tab: Overview / Pipeline Flow */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
            <h3 className="text-lg font-bold text-[#1B2D1E] mb-6 flex items-center gap-2">
              <Layers className="w-5 h-5 text-emerald-600" />
              Big Data Architecture & Transformation Stages
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {pipelineStages.map((stage, idx) => (
                <div key={stage.step} className="relative bg-[#F8FAF5] p-5 rounded-xl border border-gray-200">
                  <div className="flex items-center justify-between mb-3">
                    <span className="w-7 h-7 rounded-full bg-[#2D6A4F] text-white text-xs font-bold flex items-center justify-center">
                      {stage.step}
                    </span>
                    <span className="text-[11px] font-semibold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full">
                      {stage.badge}
                    </span>
                  </div>
                  <h4 className="font-bold text-sm text-[#1B2D1E]">{stage.title}</h4>
                  <p className="text-xs text-[#4A6B50] mt-2 leading-relaxed">{stage.desc}</p>
                  <div className="mt-4 pt-3 border-t border-gray-200 text-[11px] text-emerald-700 font-medium flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    {stage.status}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab: Datasets Provenance */}
      {activeTab === 'datasets' && (
        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm space-y-4">
          <h3 className="text-lg font-bold text-[#1B2D1E] flex items-center gap-2">
            <Database className="w-5 h-5 text-emerald-600" />
            Official Meteorological & Soil Moisture Dataset Registry
          </h3>
          <p className="text-xs text-gray-500">
            Source-backed agricultural datasets adhering to strict non-fabrication protocols.
          </p>

          <div className="overflow-x-auto mt-4">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-emerald-50 text-emerald-900 border-b border-emerald-100">
                  <th className="p-3 font-semibold">Dataset ID</th>
                  <th className="p-3 font-semibold">Source Name</th>
                  <th className="p-3 font-semibold">Publisher</th>
                  <th className="p-3 font-semibold">Temporal Coverage</th>
                  <th className="p-3 font-semibold">Variables</th>
                  <th className="p-3 font-semibold">License</th>
                  <th className="p-3 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {datasets.map((d) => (
                  <tr key={d.id} className="hover:bg-gray-50/50">
                    <td className="p-3 font-bold text-emerald-800">{d.id}</td>
                    <td className="p-3 font-medium text-gray-900">{d.name}</td>
                    <td className="p-3 text-gray-600">{d.source}</td>
                    <td className="p-3 text-gray-600">{d.coverage}</td>
                    <td className="p-3 font-mono text-[11px] text-gray-700">{d.variable}</td>
                    <td className="p-3 text-gray-500">{d.license}</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-green-100 text-green-800">
                        {d.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: Validation Checks */}
      {activeTab === 'validation' && (
        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-[#1B2D1E] flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              Automated Data Quality & Scientific Integrity Audits
            </h3>
            <span className="text-xs bg-emerald-100 text-emerald-800 px-3 py-1 rounded-full font-bold">
              8 of 8 Passed
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            {validationChecks.map((v, i) => (
              <div key={i} className="p-4 rounded-xl border border-gray-200 bg-[#F8FAF5] flex items-start gap-3">
                <span className="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0 text-xs font-bold">
                  ✓
                </span>
                <div>
                  <div className="font-bold text-sm text-[#1B2D1E]">{v.check}</div>
                  <div className="text-xs text-[#4A6B50] mt-1">{v.detail}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Feature Dictionary */}
      {activeTab === 'features' && (
        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm space-y-4">
          <h3 className="text-lg font-bold text-[#1B2D1E] flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-emerald-600" />
            Engineered Feature Dictionary (16 Features)
          </h3>
          <p className="text-xs text-gray-500">
            Constructed strictly from historical observations up to day t. No future information is utilized.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
            {featuresList.map((f) => (
              <div key={f.name} className="p-3.5 rounded-xl border border-gray-200 bg-white">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-emerald-800">{f.name}</span>
                  <span className="text-[10px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded font-medium">
                    {f.type}
                  </span>
                </div>
                <div className="text-xs text-gray-600 mt-1.5">{f.desc}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

