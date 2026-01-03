import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';
// const WS_BASE_URL = 'ws://localhost:8000/ws/sentiment';
const WS_BASE_URL = 'ws://127.0.0.1:8000/ws/sentiment';

// 5.3 Required Functions
export const apiService = {
    // 1. Fetch posts with pagination and filters
    fetchPosts: async (limit = 50, offset = 0, filters = {}) => {
        const params = new URLSearchParams({ limit, offset, ...filters });
        const response = await axios.get(`${API_BASE_URL}/posts?${params}`);
        return response.data; // Expected structure: { posts: [], total: N }
    },

    // 2. Get sentiment distribution (Pie Chart data)
    fetchDistribution: async (hours = 24) => {
        const response = await axios.get(`${API_BASE_URL}/sentiment/distribution?hours=${hours}`);
        return response.data; // Expected structure: { distribution: {positive: X, ...} }
    },

    // 3. Get time-series aggregated data (Trend Chart data)
    fetchAggregateData: async (period = 'hour') => {
        const response = await axios.get(`${API_BASE_URL}/sentiment/aggregate?period=${period}`);
        return response.data; // Expected structure: { data: [{timestamp, positive_count, ...}] }
    },

    // 4. Create WebSocket connection with callbacks
    connectWebSocket: (onMessage, onError, onClose) => {
        const socket = new WebSocket(WS_BASE_URL);
        
        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            onMessage(data);
        };

        socket.onerror = (error) => onError(error);
        socket.onclose = () => onClose();

        return socket; // Return for cleanup
    }
};