import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Label
} from 'recharts';
import type { ActualVsPredicted } from '../../types';

interface ActualVsPredictedChartProps {
  data: ActualVsPredicted[];
  title?: string;
}

export default function ActualVsPredictedChart({ data, title = 'Actual vs Predicted — Test Set' }: ActualVsPredictedChartProps) {
  const chartData = data.map(d => ({ x: d.actual, y: d.predicted }));
  const allVals = data.flatMap(d => [d.actual, d.predicted]);
  const minVal = Math.min(...allVals);
  const maxVal = Math.max(...allVals);

  return (
    <div className="w-full">
      <div className="mb-3">
        <h4 className="text-sm font-semibold text-sk-text">{title}</h4>
        <p className="text-xs text-sk-text-secondary">
          Scatter plot of model predictions vs observed values · Perfect model = diagonal line
        </p>
        <span className="inline-block mt-1 px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full border border-blue-200">
          ⚠ Prediction (ML Model) — Not an Observation
        </span>
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <ScatterChart margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5EDE8" />
          <XAxis type="number" dataKey="x" domain={[minVal - 0.02, maxVal + 0.02]} tick={{ fontSize: 10, fill: '#4A6B50' }}>
            <Label value="Actual Moisture" offset={-10} position="insideBottom" style={{ fontSize: 10, fill: '#4A6B50' }} />
          </XAxis>
          <YAxis type="number" dataKey="y" domain={[minVal - 0.02, maxVal + 0.02]} tick={{ fontSize: 10, fill: '#4A6B50' }} axisLine={false} tickLine={false}>
            <Label value="Predicted Moisture" angle={-90} position="insideLeft" style={{ fontSize: 10, fill: '#4A6B50' }} />
          </YAxis>
          <Tooltip
            contentStyle={{ background: '#fff', border: '1px solid #D8E8DC', borderRadius: 8, fontSize: 12 }}
            formatter={(v: number) => [v.toFixed(4), '']}
          />
          <ReferenceLine segment={[{ x: minVal, y: minVal }, { x: maxVal, y: maxVal }]} stroke="#F4A261" strokeDasharray="4 4" label="Ideal" />
          <Scatter data={chartData} fill="#2D6A4F" opacity={0.7} />
        </ScatterChart>
      </ResponsiveContainer>
      <p className="text-center text-xs text-gray-400 mt-1">Source: ML Model Test-Set Evaluation · ML Prediction (not measured)</p>
    </div>
  );
}
