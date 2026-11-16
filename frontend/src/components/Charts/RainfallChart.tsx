import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import type { DataRecord } from '../../types';
import { format, parseISO } from 'date-fns';

interface RainfallChartProps {
  data: DataRecord[];
  title?: string;
  days?: number;
}

export default function RainfallChart({ data, title = 'Rainfall (mm)', days = 30 }: RainfallChartProps) {
  const chartData = data.slice(-days).map(d => ({
    date: format(parseISO(d.date), 'dd MMM'),
    rainfall: Number(d.rainfall_mm.toFixed(2)),
    farm: d.farm_id,
  }));

  return (
    <div className="w-full">
      <div className="mb-3">
        <h4 className="text-sm font-semibold text-sk-text">{title}</h4>
        <p className="text-xs text-sk-text-secondary">Last {days} days · Source: IMD / NASA POWER · Unit: mm/day</p>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 20 }}>
          <defs>
            <linearGradient id="rainGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#52B788" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#52B788" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5EDE8" />
          <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#4A6B50' }} tickLine={false} interval="preserveStartEnd" />
          <YAxis tick={{ fontSize: 10, fill: '#4A6B50' }} tickLine={false} axisLine={false} unit=" mm" width={45} />
          <Tooltip
            contentStyle={{ background: '#fff', border: '1px solid #D8E8DC', borderRadius: 8, fontSize: 12 }}
            formatter={(v: number) => [`${v} mm`, 'Rainfall']}
          />
          <Area type="monotone" dataKey="rainfall" stroke="#2D6A4F" strokeWidth={2} fill="url(#rainGrad)" name="Rainfall (mm)" />
        </AreaChart>
      </ResponsiveContainer>
      <p className="text-center text-xs text-gray-400 mt-1">Source: IMD Daily Rainfall Records + NASA POWER API · Measurement (Observed Data)</p>
    </div>
  );
}
