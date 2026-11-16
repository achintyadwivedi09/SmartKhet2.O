import React, { useState } from 'react';
import {
  BrainCircuit,
  BarChart3,
  TrendingUp,
  Cpu,
  Layers,
  HelpCircle,
  AlertCircle,
  Sparkles,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';
import ActualVsPredictedChart from '../components/Charts/ActualVsPredictedChart';
import ModelComparisonChart from '../components/Charts/ModelComparisonChart';
import { runPrediction, predictForFarm } from '../services/api';

export default function MLLabPage() {
  const [selectedFarm, setSelectedFarm] = useState<string>('TN001');
  const [currentMoisture, setCurrentMoisture] = useState<number>(0.24);
  const [rainfall, setRainfall] = useState<number>(0.0);
  const [temperature, setTemperature] = useState<number>(31.0);
  const [humidity, setHumidity] = useState<number>(62.0);

  const [predictionResult, setPredictionResult] = useState<any>({
    predicted_moisture: 0.2312,
    prediction_label: 'Mild Deficit',
    confidence: 0.912,
    recommendation:
      'WARNING: Moisture level (0.231) projected below optimal target (0.35) for Rice. Schedule irrigation within the next 24-36 hours.',
    urgency: 'medium',
    model_version: '2.0.0',
  });

  const [predicting, setPredicting] = useState<boolean>(false);

  const modelMetrics = [
    {
      model: 'Baseline (Persistence)',
      mae: 0.0044,
      rmse: 0.0103,
      r2: 0.7946,
      medianAe: 0.0000,
      samples: 822,
      note: 'Assumes next-day = today. Reference standard.',
    },
    {
      model: 'Random Forest Regressor (Deployed)',
      mae: 0.0040,
      rmse: 0.0082,
      r2: 0.8722,
      medianAe: 0.0012,
      samples: 822,
      note: '200 estimators, max depth 14, MDI-optimized.',
      highlight: true,
    },
    {
      model: 'XGBoost Regressor',
      mae: 0.0042,
      rmse: 0.0086,
      r2: 0.8582,
      medianAe: 0.0013,
      samples: 822,
      note: '250 rounds, learning rate 0.05, early stopping.',
    },
  ];

  const featureImportances = [
    { feature: 'soil_moisture_lag1', importance: 0.4852, desc: 'Previous-day moisture observation' },
    { feature: 'soil_moisture_ma3', importance: 0.2140, desc: '3-day trailing moving average' },
    { feature: 'soil_moisture_ma7', importance: 0.1215, desc: '7-day trailing moving average' },
    { feature: 'rainfall_mm', importance: 0.0654, desc: 'Current daily rainfall' },
    { feature: 'temperature_c', importance: 0.0381, desc: 'Surface air temperature' },
    { feature: 'relative_humidity_pct', importance: 0.0245, desc: 'Relative humidity' },
    { feature: 'rainfall_cum3', importance: 0.0210, desc: '3-day cumulative rainfall' },
    { feature: 'day_of_year', importance: 0.0152, desc: 'Annual solar seasonality' },
    { feature: 'daily_et_estimate_mm', importance: 0.0151, desc: 'Hargreaves evapotranspiration' },
  ];

  const handlePredict = async () => {
    try {
      setPredicting(true);
      const res = await runPrediction({
        soil_moisture: currentMoisture,
        rainfall: rainfall,
        temperature: temperature,
        humidity: humidity,
      });
      if (res) {
        setPredictionResult(res);
      }
    } catch (err) {
      console.error('Prediction request failed:', err);
    } finally {
      setPredicting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
        <div>
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
            Phase 2 Deliverable
          </span>
          <h1 className="text-2xl font-bold text-[#1B2D1E] mt-1">Machine Learning Laboratory & Model Evaluation</h1>
          <p className="text-sm text-[#4A6B50]">
            Empirical benchmark of next-day volumetric soil moisture prediction (m³/m³) on chronological test partitions.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-[#F8FAF5] px-4 py-2 rounded-xl border border-gray-200 text-right">
            <div className="text-[11px] text-gray-500 uppercase font-semibold">Deployed Model</div>
            <div className="text-sm font-bold text-[#2D6A4F]">Random Forest v2.0</div>
          </div>
          <div className="bg-[#F8FAF5] px-4 py-2 rounded-xl border border-gray-200 text-right">
            <div className="text-[11px] text-gray-500 uppercase font-semibold">Test R² Score</div>
            <div className="text-sm font-bold text-emerald-600">0.8722</div>
          </div>
        </div>
      </div>

      {/* Benchmark Comparison Table */}
      <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm space-y-4">
        <h3 className="font-bold text-base text-[#1B2D1E] flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-emerald-600" />
          Model Evaluation & Performance Benchmarking (Chronological Test Set: N=822)
        </h3>
        <p className="text-xs text-gray-500">
          Strict chronological test set evaluation (April 2023 – December 2023). Preprocessing was fitted exclusively on training data.
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-emerald-50 text-emerald-900 border-b border-emerald-100">
                <th className="p-3 font-semibold">Model Architecture</th>
                <th className="p-3 font-semibold">MAE (m³/m³)</th>
                <th className="p-3 font-semibold">RMSE (m³/m³)</th>
                <th className="p-3 font-semibold">R² Score</th>
                <th className="p-3 font-semibold">Median AE (m³/m³)</th>
                <th className="p-3 font-semibold">Sample Size</th>
                <th className="p-3 font-semibold">Hyperparameters & Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {modelMetrics.map((m) => (
                <tr
                  key={m.model}
                  className={`${m.highlight ? 'bg-emerald-50/50 font-medium' : 'hover:bg-gray-50/50'}`}
                >
                  <td className="p-3 font-bold text-[#1B2D1E] flex items-center gap-2">
                    {m.model}
                    {m.highlight && (
                      <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-600 text-white font-semibold">
                        PRIMARY
                      </span>
                    )}
                  </td>
                  <td className="p-3 font-mono">{m.mae.toFixed(4)}</td>
                  <td className="p-3 font-mono">{m.rmse.toFixed(4)}</td>
                  <td className="p-3 font-mono text-emerald-700 font-bold">{m.r2.toFixed(4)}</td>
                  <td className="p-3 font-mono">{m.medianAe.toFixed(4)}</td>
                  <td className="p-3">{m.samples}</td>
                  <td className="p-3 text-gray-500">{m.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Feature Importance & Explainability */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm space-y-4">
          <h3 className="font-bold text-base text-[#1B2D1E] flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-emerald-600" />
            Top Feature Importance (Mean Decrease in Impurity)
          </h3>
          <p className="text-xs text-gray-500">
            Soil moisture inertia (lag-1 and rolling 3d/7d averages) accounts for &gt;80% of predictive power.
          </p>

          <div className="space-y-3 mt-3">
            {featureImportances.map((f) => (
              <div key={f.feature} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-mono text-gray-800 font-medium">{f.feature}</span>
                  <span className="font-bold text-emerald-700">{(f.importance * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-[#2D6A4F] h-full rounded-full transition-all duration-500"
                    style={{ width: `${f.importance * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Live Interactive Inference Simulator */}
        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-base text-[#1B2D1E] flex items-center gap-2">
              <Cpu className="w-5 h-5 text-emerald-600" />
              Live Next-Day Soil Moisture Inference
            </h3>
            <span className="text-[11px] bg-amber-100 text-amber-800 font-semibold px-2.5 py-0.5 rounded-full">
              ML Prediction Engine
            </span>
          </div>
          <p className="text-xs text-gray-500">
            Simulate current environmental inputs to generate next-day soil moisture predictions and irrigation decisions.
          </p>

          <div className="grid grid-cols-2 gap-4 mt-2">
            <div>
              <label className="text-xs text-gray-600 font-medium">Target Farm</label>
              <select
                value={selectedFarm}
                onChange={(e) => setSelectedFarm(e.target.value)}
                className="w-full text-xs p-2 border border-gray-200 rounded-lg mt-1 bg-white"
              >
                <option value="TN001">TN001 — Thanjavur (Rice, trigger 0.28)</option>
                <option value="TN002">TN002 — Coimbatore (Cotton, trigger 0.18)</option>
                <option value="TN003">TN003 — Madurai (Groundnut, trigger 0.14)</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-gray-600 font-medium">Current Moisture (m³/m³)</label>
              <input
                type="number"
                step="0.01"
                min="0.10"
                max="0.50"
                value={currentMoisture}
                onChange={(e) => setCurrentMoisture(parseFloat(e.target.value))}
                className="w-full text-xs p-2 border border-gray-200 rounded-lg mt-1"
              />
            </div>

            <div>
              <label className="text-xs text-gray-600 font-medium">Precipitation (mm)</label>
              <input
                type="number"
                step="0.5"
                min="0"
                max="150"
                value={rainfall}
                onChange={(e) => setRainfall(parseFloat(e.target.value))}
                className="w-full text-xs p-2 border border-gray-200 rounded-lg mt-1"
              />
            </div>

            <div>
              <label className="text-xs text-gray-600 font-medium">Air Temperature (°C)</label>
              <input
                type="number"
                step="0.5"
                min="15"
                max="45"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full text-xs p-2 border border-gray-200 rounded-lg mt-1"
              />
            </div>
          </div>

          <button
            onClick={handlePredict}
            disabled={predicting}
            className="w-full bg-[#2D6A4F] text-white py-2.5 rounded-xl text-xs font-bold hover:bg-[#1B4332] transition-colors mt-2 shadow-sm disabled:opacity-50"
          >
            {predicting ? 'Evaluating Model Inference...' : 'Predict Next-Day Soil Moisture & Advice'}
          </button>

          {/* Prediction Result Display */}
          {predictionResult && (
            <div className="p-4 rounded-xl border border-emerald-200 bg-[#F0FDF4] space-y-2 mt-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-emerald-900 uppercase">
                  Prediction Result ({predictionResult.model_version})
                </span>
                <span className="text-[11px] bg-emerald-200 text-emerald-900 px-2 py-0.5 rounded font-bold">
                  Confidence: {(predictionResult.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-emerald-900">
                  {predictionResult.predicted_moisture?.toFixed(3)} m³/m³
                </span>
                <span className="text-xs text-emerald-700 font-semibold">
                  ({predictionResult.prediction_label})
                </span>
              </div>
              <p className="text-xs text-[#2D6A4F] leading-relaxed font-medium">
                {predictionResult.recommendation}
              </p>
              <div className="pt-2 text-[10px] text-gray-500 border-t border-emerald-200/60">
                ⚠️ Academic Disclosure: Value is an ML estimation derived from historical training data. Not a real physical sensor reading.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

