import axios from 'axios';
import type {
  Strategy,
  ScreenRequest,
  ScreenTask,
  ScreenResponse,
} from '../types';

// API 基础 URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 选股 API
export const screenAPI = {
  // 获取策略列表
  async getStrategies(): Promise<Strategy[]> {
    const response = await apiClient.get('/api/strategies');
    return response.data;
  },

  // 执行选股
  async runScreen(request: ScreenRequest): Promise<ScreenTask> {
    const response = await apiClient.post('/api/screen/run', request);
    return response.data;
  },

  // 获取选股结果
  async getScreenResult(taskId: string): Promise<ScreenResponse> {
    const response = await apiClient.get(`/api/screen/result/${taskId}`);
    return response.data;
  },

  // 删除选股任务
  async deleteScreenResult(taskId: string): Promise<void> {
    await apiClient.delete(`/api/screen/result/${taskId}`);
  },
};

// WebSocket 连接工厂
export function createScreenWebSocket(
  taskId: string,
  onMessage: (data: any) => void,
  onError?: (error: Event) => void
): WebSocket {
  const wsUrl = API_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://');
  const ws = new WebSocket(`${wsUrl}/ws/screen/${taskId}`);

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    onError?.(error);
  };

  return ws;
}

// AI API
export const aiAPI = {
  analyzeMarket: async (index: string = 'SSE', period: string = '1M') => {
    const response = await apiClient.post('/api/ai/market-analysis', { index, period });
    return response.data;
  },

  analyzeStock: async (symbol: string, strategy?: string) => {
    const response = await apiClient.post('/api/ai/stock-analysis', { symbol, strategy });
    return response.data;
  },

  nlScreen: async (query: string) => {
    const response = await apiClient.post('/api/ai/nl-screen', { query });
    return response.data;
  },
};

// Backtest API
export const backtestAPI = {
  createBacktest: async (params: {
    strategy_id: string;
    start_date: string;
    end_date: string;
    initial_capital: number;
  }) => {
    const response = await apiClient.post('/api/backtest/create', params);
    return response.data;
  },

  getBacktestResult: async (taskId: string) => {
    const response = await apiClient.get(`/api/backtest/result/${taskId}`);
    return response.data;
  },
};

// Portfolio API
export const portfolioAPI = {
  createPortfolio: async (params: {
    name: string;
    description: string;
    stocks: any[];
  }) => {
    const response = await apiClient.post('/api/portfolio/create', params);
    return response.data;
  },

  getPortfolio: async (portfolioId: string) => {
    const response = await apiClient.get(`/api/portfolio/${portfolioId}`);
    return response.data;
  },

  updatePortfolio: async (portfolioId: string, stocks: any[]) => {
    const response = await apiClient.post(`/api/portfolio/${portfolioId}/update`, { stocks });
    return response.data;
  },

  getSummary: async () => {
    const response = await apiClient.get('/api/portfolio/summary');
    return response.data;
  },
};

// 导出 API 客户端
export default apiClient;
