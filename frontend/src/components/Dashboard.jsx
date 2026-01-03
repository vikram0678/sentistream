import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import DistributionChart from './DistributionChart';
import SentimentChart from './SentimentChart';
import { MessageSquare } from 'lucide-react';

const Dashboard = () => {
  const [metrics, setMetrics] = useState({ total: 0, positive: 0, negative: 0, neutral: 0 });
  const [trendData, setTrendData] = useState([]);
  const [recentPosts, setRecentPosts] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('connecting');

  useEffect(() => {
    let socket;
    const loadInitialData = async () => {
      try {
        const dist = await apiService.fetchDistribution(24);
        const agg = await apiService.fetchAggregateData('hour');
        const posts = await apiService.fetchPosts(10);

        setMetrics({
          total: dist.total,
          positive: dist.distribution.positive || 0,
          negative: dist.distribution.negative || 0,
          neutral: dist.distribution.neutral || 0
        });

        const formattedTrend = agg.data.map(item => ({
          timestamp: item.timestamp,
          positive: item.positive_count,
          negative: item.negative_count,
          neutral: item.neutral_count
        }));
        setTrendData(formattedTrend);
        setRecentPosts(posts.posts);

        // Small delay for WebSocket prevents race condition error
        setTimeout(() => {
          socket = apiService.connectWebSocket(
            (message) => {
              if (message.type === 'connected') setConnectionStatus('connected');
              if (message.type === 'new_post') {
                setRecentPosts(prev => [message.data, ...prev].slice(0, 10));
                setMetrics(prev => ({
                  ...prev,
                  total: prev.total + 1,
                  [message.data.sentiment_label]: (prev[message.data.sentiment_label] || 0) + 1
                }));
              }
            },
            () => setConnectionStatus('disconnected'),
            () => setConnectionStatus('disconnected')
          );
        }, 500);
      } catch (err) { console.error("Initial fetch failed", err); }
    };

    loadInitialData();
    return () => { if (socket) socket.close(); };
  }, []);

  return (
    <div className="min-h-screen bg-gray-950 text-slate-100 p-8">
      <header className="flex justify-between items-center mb-8 border-b border-gray-800 pb-6">
        <h1 className="text-2xl font-bold tracking-tight">SentiStream Live Dashboard</h1>
        <div className={`px-4 py-2 rounded-lg border text-sm font-bold transition-colors ${
          connectionStatus === 'connected' ? 'border-green-500 text-green-500' : 'border-red-500 text-red-500'
        }`}>
          Status: ● {connectionStatus.toUpperCase()}
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-4 h-[400px]">
          <DistributionChart data={metrics} />
        </div>
        <div className="lg:col-span-8 bg-gray-900 p-6 rounded-xl border border-gray-800 flex flex-col h-[400px]">
          <h3 className="flex items-center gap-2 text-lg font-semibold mb-4 text-white">
            <MessageSquare size={20} className="text-purple-400" /> Recent Posts Feed
          </h3>
          <div className="space-y-3 overflow-y-auto flex-1 pr-2">
            {recentPosts.map((post, i) => (
              <div key={i} className="p-3 bg-gray-800 rounded border-l-4 border-blue-500 text-sm">
                <span className="text-blue-400 font-bold mr-2">
                    [{(post.sentiment_label || post.sentiment?.label || 'INFO').toUpperCase()}]</span> 
                <span className="text-gray-200">{post.content}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="lg:col-span-12">
          <SentimentChart data={trendData} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;