import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import type { DataRecord } from '../../types';
import { format, parseISO } from 'date-fns';

interface TemperatureChartProps { data: DataRecord[]; title?: string; days?: number; }

export default function TemperatureChart({ data, title = 'Temperature (°C)', days = 30 }: TemperatureChartProps) {
  const chartData = data.slice(-days).map(d => ({
    date: format(parseISO(d.date), 'dd MMM'),
    temp: Number(d.temperature_c.toFixed(1)),
  }));

  return (
    <div className="w-full">
      <div className="mb-3">
        <h4 className="text-sm font-semibold text-sk-text">{title}</h4>
        <p className="text-xs text-sk-text-secondary">Last {days} days · Source: OpenWeatherMap / IMD · Unit: °C</p>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5EDE8" />
          <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#4A6B50' }} tickLine={false} interval="preserveStartEnd" />
          <YAxis tick={{ fontSize: 10, fill: '#4A6B50' }} tickLine={false} axisLine={false} unit="°C" width={42} />
          <Tooltip
            contentStyle={{ background: '#fff', border: '1px solid #D8E8DC', borderRadius: 8, fontSize: 12 }}
            formatter={(v: number) => [`${v}°C`, 'Temperature']}
          />
          <Line type="monotone" dataKey="temp" stroke="#F4A261" strokeWidth={2} dot={false} name="Temperature (°C)" />
        </LineChart>
      </ResponsiveContainer>
      <p className="text-center text-xs text-gray-400 mt-1">Source: OpenWeatherMap + IMD · Measurement (Observed)</p>
    </div>
  );
}
