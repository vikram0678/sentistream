import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function SentimentTrendChart({ data }) {
    /**
     * Requirement Check:
     * - Line chart showing trends over time
     * - Color scheme: Positive (#10b981), Negative (#ef4444)
     * - Handles empty data gracefully
     */

    if (!data || data.length === 0) {
        return (
            <div className="bg-gray-800 rounded-lg p-6 h-64 flex items-center justify-center border border-gray-700">
                <p className="text-gray-500 italic">No trend data available yet...</p>
            </div>
        );
    }

    return (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold mb-6 text-white text-left">Sentiment Trend Over Time</h3>
            <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                        <XAxis 
                            dataKey="timestamp" 
                            stroke="#9ca3af" 
                            fontSize={12}
                            tickLine={false}
                            axisLine={false}
                        />
                        <YAxis 
                            stroke="#9ca3af" 
                            fontSize={12}
                            tickLine={false}
                            axisLine={false}
                        />
                        <Tooltip 
                            contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px', color: '#fff' }}
                        />
                        <Legend verticalAlign="top" align="right" height={36}/>
                        <Line 
                            type="monotone" 
                            dataKey="positive" 
                            name="Positive"
                            stroke="#10b981" 
                            strokeWidth={3}
                            dot={{ r: 4 }}
                            activeDot={{ r: 6 }}
                        />
                        <Line 
                            type="monotone" 
                            dataKey="negative" 
                            name="Negative"
                            stroke="#ef4444" 
                            strokeWidth={3}
                            dot={{ r: 4 }}
                            activeDot={{ r: 6 }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}

export default SentimentTrendChart;