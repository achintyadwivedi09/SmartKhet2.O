import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import type { DataRecord } from '../../types';
import { format, parseISO } from 'date-fns';

interface HumidityChartProps { data: DataRecord[]; title?: string; days?: number; }

export default function HumidityChart({ data, title = 'Relative Humidity (%)', days = 30 }: HumidityChartProps) {
  const chartData = data.slice(-days).map(d => ({
    date: format(parseISO(d.date), 'dd MMM'),
    humidity: Number(d.humidity_pct.toFixed(1)),
  }));

  return (
    <div className="w-full">
      <div className="mb-3">
        <h4 className="text-sm font-semibold text-sk-text">{title}</h4>
        <p className="text-xs text-sk-text-secondary">Last {days} days · Source: OpenWeatherMap · Unit: %</p>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5EDE8" />
          <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#4A6B50' }} tickLine={false} interval="preserveStartEnd" />
          <YAxis tick={{ fontSize: 10, fill: '#4A6B50' }} tickLine={false} axisLine={false} unit="%" width={38} domain={[0, 100]} />
          <Tooltip
            contentStyle={{ background: '#fff', border: '1px solid #D8E8DC', borderRadius: 8, fontSize: 12 }}
            formatter={(v: number) => [`${v}%`, 'Humidity']}
          />
          <Line type="monotone" dataKey="humidity" stroke="#74C69D" strokeWidth={2} dot={false} name="Humidity (%)" />
        </LineChart>
      </ResponsiveContainer>
      <p className="text-center text-xs text-gray-400 mt-1">Source: OpenWeatherMap API · Measurement (Observed)</p>
    </div>
  );
}
