import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function SentimentChart({ data }) {
    // Requirement: Format timestamps as HH:MM
    const formatTime = (isoString) => {
        try {
            const date = new Date(isoString);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
        } catch (e) { return isoString; }
    };

    if (!data || data.length === 0) {
        return (
            <div className="bg-gray-800 rounded-lg p-4 h-64 flex items-center justify-center border border-gray-700 text-gray-500 italic">
                No trend data available
            </div>
        );
    }

    return (
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <h3 className="text-lg font-semibold mb-4 text-white">Sentiment Trend (Last 24 Hours)</h3>
            <div className="w-full" style={{ height: '300px', minHeight: '300px' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                        <XAxis dataKey="timestamp" tickFormatter={formatTime} stroke="#9ca3af" fontSize={12} />
                        <YAxis stroke="#9ca3af" fontSize={12} />
                        <Tooltip labelFormatter={formatTime} contentStyle={{ backgroundColor: '#1f2937', border: 'none', color: '#fff' }} />
                        <Legend />
                        <Line type="monotone" dataKey="positive" stroke="#10b981" strokeWidth={3} dot={{ r: 4 }} />
                        <Line type="monotone" dataKey="negative" stroke="#ef4444" strokeWidth={3} dot={{ r: 4 }} />
                        <Line type="monotone" dataKey="neutral" stroke="#6b7280" strokeWidth={3} dot={{ r: 4 }} />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}

export default SentimentChart;