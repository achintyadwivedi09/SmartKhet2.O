import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell
} from 'recharts';
import type { MLModel } from '../../types';

interface ModelComparisonChartProps {
  models: MLModel[];
  metric?: 'mae' | 'rmse' | 'r2' | 'median_ae';
}

const metricLabels = { mae: 'MAE', rmse: 'RMSE', r2: 'R² Score', median_ae: 'Median AE' };
const COLORS = ['#2D6A4F', '#52B788', '#74C69D', '#B7E4C7'];

export default function ModelComparisonChart({ models, metric = 'r2' }: ModelComparisonChartProps) {
  const data = models.map((m, i) => ({
    name: m.algorithm,
    value: Number(m.metrics[metric].toFixed(4)),
    color: COLORS[i % COLORS.length],
  }));

  return (
    <div className="w-full">
      <div className="mb-3">
        <h4 className="text-sm font-semibold text-sk-text">Model Comparison — {metricLabels[metric]}</h4>
        <p className="text-xs text-sk-text-secondary">All models trained on same dataset split (70/15/15)</p>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5EDE8" />
          <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#4A6B50' }} tickLine={false} />
          <YAxis tick={{ fontSize: 10, fill: '#4A6B50' }} tickLine={false} axisLine={false} width={50} />
          <Tooltip
            contentStyle={{ background: '#fff', border: '1px solid #D8E8DC', borderRadius: 8, fontSize: 12 }}
            formatter={(v: number) => [v, metricLabels[metric]]}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]} name={metricLabels[metric]}>
            {data.map((entry, index) => (
              <Cell key={index} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
