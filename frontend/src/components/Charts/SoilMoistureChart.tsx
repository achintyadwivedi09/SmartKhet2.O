import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts';
import type { DataRecord } from '../../types';
import { format, parseISO } from 'date-fns';

interface SoilMoistureChartProps {
  data: DataRecord[];
  title?: string;
  days?: number;
  threshold?: number;
  cropLabel?: string;
}

export default function SoilMoistureChart({
  data, title = 'Soil Moisture', days = 30, threshold, cropLabel
}: SoilMoistureChartProps) {
  const chartData = data.slice(-days).map(d => ({
    date: format(parseISO(d.date), 'dd MMM'),
    moisture: Number((d.soil_moisture * 100).toFixed(1)),
    isPredicted: d.is_predicted,
  }));

  return (
    <div className="w-full">
      <div className="mb-3">
        <h4 className="text-sm font-semibold text-sk-text">{title}</h4>
        <p className="text-xs text-sk-text-secondary">
          Last {days} days · Source: ICAR Field Sensors · Unit: % volumetric
          {cropLabel && ` · Crop: ${cropLabel}`}
        </p>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5EDE8" />
          <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#4A6B50' }} tickLine={false} interval="preserveStartEnd" />
          <YAxis tick={{ fontSize: 10, fill: '#4A6B50' }} tickLine={false} axisLine={false} unit="%" width={40} domain={[0, 100]} />
          <Tooltip
            contentStyle={{ background: '#fff', border: '1px solid #D8E8DC', borderRadius: 8, fontSize: 12 }}
            formatter={(v: number) => [`${v}%`, 'Soil Moisture']}
          />
          {threshold && (
            <ReferenceLine y={threshold * 100} stroke="#F4A261" strokeDasharray="4 4" label={{ value: 'Threshold', fontSize: 10, fill: '#F4A261' }} />
          )}
          <Line type="monotone" dataKey="moisture" stroke="#52B788" strokeWidth={2} dot={false} name="Soil Moisture (%)" />
        </LineChart>
      </ResponsiveContainer>
      <p className="text-center text-xs text-gray-400 mt-1">Source: ICAR Soil Data + Field Sensors · Measurement (Observed Data)</p>
    </div>
  );
}
