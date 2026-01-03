import React from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const DistributionChart = ({ data }) => {
  const chartData = [
    { name: 'Positive', value: data?.positive || 0, color: '#10b981' },
    { name: 'Negative', value: data?.negative || 0, color: '#ef4444' },
    { name: 'Neutral', value: data?.neutral || 0, color: '#6b7280' },
  ].filter(item => item.value > 0);

  const total = chartData.reduce((sum, item) => sum + item.value, 0);

  const renderLegend = (value, entry) => {
    if (!entry || !entry.payload) return value;
    const percentage = total > 0 ? ((entry.payload.value / total) * 100).toFixed(1) : 0;
    return (
      <span className="text-gray-300 text-sm ml-2">
        {value}: <span className="font-bold text-white">{entry.payload.value}</span> ({percentage}%)
      </span>
    );
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4 h-full flex flex-col border border-gray-700">
      <h3 className="text-lg font-semibold mb-4 text-white">Sentiment Distribution</h3>
      {/* minHeight fixes the 'width(-1)' console error */}
      <div className="flex-1" style={{ minHeight: '300px', width: '100%' }}>
        {total === 0 ? (
          <div className="flex h-full items-center justify-center text-gray-500 italic">No data available</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={85}
                paddingAngle={5}
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', color: '#fff' }} />
              <Legend verticalAlign="bottom" formatter={renderLegend} />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};

export default DistributionChart;