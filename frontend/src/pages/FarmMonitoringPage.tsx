import React, { useEffect, useState } from 'react';
import {
  MapPin,
  Calendar,
  Droplets,
  CloudRain,
  Thermometer,
  Wind,
  Cpu,
  Layers,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import SoilMoistureChart from '../components/Charts/SoilMoistureChart';
import RainfallChart from '../components/Charts/RainfallChart';
import TemperatureChart from '../components/Charts/TemperatureChart';
import HumidityChart from '../components/Charts/HumidityChart';
import { getFarms, getFarmData } from '../services/api';
import type { Farm, DataRecord } from '../types';

export default function FarmMonitoringPage() {
  const [farms, setFarms] = useState<Farm[]>([]);
  const [selectedFarmId, setSelectedFarmId] = useState<string>('TN001');
  const [timeRange, setTimeRange] = useState<number>(30);
  const [records, setRecords] = useState<DataRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadFarms() {
      try {
        setLoading(true);
        const data = await getFarms();
        if (data.length > 0) {
          setFarms(data);
          setSelectedFarmId(data[0].farm_id);
          const recs = await getFarmData(data[0].farm_id);
          setRecords(recs);
        }
      } catch (err) {
        console.error('Error fetching farms:', err);
      } finally {
        setLoading(false);
      }
    }
    loadFarms();
  }, []);

  const handleSelectFarm = async (farmId: string) => {
    setSelectedFarmId(farmId);
    try {
      const recs = await getFarmData(farmId);
      setRecords(recs);
    } catch (err) {
      console.error('Error fetching farm data:', err);
    }
  };

  const currentFarm = farms.find((f) => f.farm_id === selectedFarmId);
  const latestRecord = records[records.length - 1];

  const getCropThreshold = (crop?: string) => {
    switch (crop) {
      case 'Rice':
        return 0.35;
      case 'Cotton':
        return 0.25;
      case 'Groundnut':
        return 0.20;
      default:
        return 0.25;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
        <div>
          <h1 className="text-2xl font-bold text-[#1B2D1E]">Farm Telemetry & Field Monitoring</h1>
          <p className="text-sm text-[#4A6B50]">
            Real-time & historical agrometeorological observations across Tamil Nadu agro-ecological zones.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-gray-50 p-1 rounded-xl border border-gray-200">
          {[7, 30, 90].map((days) => (
            <button
              key={days}
              onClick={() => setTimeRange(days)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                timeRange === days
                  ? 'bg-[#2D6A4F] text-white shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {days} Days
            </button>
          ))}
        </div>
      </div>

      {/* Farm Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {farms.map((farm) => {
          const isSelected = farm.farm_id === selectedFarmId;
          const threshold = getCropThreshold(farm.crop);
          return (
            <div
              key={farm.farm_id}
              onClick={() => handleSelectFarm(farm.farm_id)}
              className={`cursor-pointer rounded-2xl p-6 transition-all border ${
                isSelected
                  ? 'bg-gradient-to-br from-green-50/80 to-emerald-50/50 border-[#2D6A4F] shadow-md ring-2 ring-[#2D6A4F]/20'
                  : 'bg-white border-gray-200 hover:border-gray-300 shadow-sm'
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                    {farm.farm_id}
                  </span>
                  <h3 className="font-bold text-lg text-[#1B2D1E] mt-2">{farm.name}</h3>
                  <p className="text-xs text-gray-500 flex items-center gap-1 mt-0.5">
                    <MapPin className="w-3.5 h-3.5 text-gray-400" />
                    {farm.latitude.toFixed(2)}°N, {farm.longitude.toFixed(2)}°E · Tamil Nadu
                  </p>
                </div>
                <div className="w-9 h-9 rounded-xl bg-white border border-gray-200 flex items-center justify-center shadow-sm">
                  <Cpu className="w-5 h-5 text-emerald-600" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mt-4 pt-4 border-t border-gray-100 text-xs">
                <div>
                  <span className="text-gray-400">Crop Cultivated:</span>
                  <div className="font-semibold text-gray-800">{farm.crop}</div>
                </div>
                <div>
                  <span className="text-gray-400">Moisture Target:</span>
                  <div className="font-semibold text-emerald-700">{(threshold * 100).toFixed(0)}% vol</div>
                </div>
                <div>
                  <span className="text-gray-400">Assigned Node:</span>
                  <div className="font-medium text-gray-700">FOG-{farm.farm_id}</div>
                </div>
                <div>
                  <span className="text-gray-400">Telemetry Status:</span>
                  <div className="font-medium text-emerald-600 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Active
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Farm Detailed Overview */}
      {currentFarm && latestRecord && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
            <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
              <Droplets className="w-4 h-4 text-emerald-600" /> Current Soil Moisture
            </div>
            <div className="text-2xl font-bold text-[#1B2D1E]">
              {(latestRecord.soil_moisture * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-emerald-600 mt-1">
              Target: {(getCropThreshold(currentFarm.crop) * 100).toFixed(0)}% volumetric
            </div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
            <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
              <CloudRain className="w-4 h-4 text-blue-500" /> Daily Precipitation
            </div>
            <div className="text-2xl font-bold text-[#1B2D1E]">
              {latestRecord.rainfall_mm.toFixed(1)} mm
            </div>
            <div className="text-xs text-gray-400 mt-1">IMD 0.25° Grid Cell Measurement</div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
            <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
              <Thermometer className="w-4 h-4 text-orange-500" /> Surface Air Temp
            </div>
            <div className="text-2xl font-bold text-[#1B2D1E]">
              {latestRecord.temperature_c.toFixed(1)}°C
            </div>
            <div className="text-xs text-gray-400 mt-1">ERA5-Land 2m Temperature</div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
            <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
              <Wind className="w-4 h-4 text-teal-500" /> Relative Humidity
            </div>
            <div className="text-2xl font-bold text-[#1B2D1E]">
              {latestRecord.humidity_pct.toFixed(0)}%
            </div>
            <div className="text-xs text-gray-400 mt-1">Magnus Dewpoint Derived</div>
          </div>
        </div>
      )}

      {/* Historical Plots */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
          <SoilMoistureChart
            data={records}
            days={timeRange}
            threshold={getCropThreshold(currentFarm?.crop)}
            cropLabel={currentFarm?.crop}
          />
        </div>

        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
          <RainfallChart data={records} days={timeRange} />
        </div>

        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
          <TemperatureChart data={records} days={timeRange} />
        </div>

        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
          <HumidityChart data={records} days={timeRange} />
        </div>
      </div>
    </div>
  );
}

