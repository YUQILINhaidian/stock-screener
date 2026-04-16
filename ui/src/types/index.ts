// 策略信息
export interface Strategy {
  id: string;
  name: string;
  description: string;
  category: string;
  params: Record<string, any>;
  last_run?: string;
  avg_return?: number;
  win_rate?: number;
}

// 股票基本信息
export interface StockInfo {
  symbol: string;
  code: string;
  name: string;
  exchange: string;
  industry?: string;
  market_cap?: number;
}

// 股票技术指标
export interface StockTechnical {
  symbol: string;
  close: number;
  change_pct: number;
  volume: number;
  turnover: number;
  volume_ratio?: number;
  rps_50?: number;
  rps_120?: number;
  rps_250?: number;
  ma_20?: number;
  ma_60?: number;
  ma_120?: number;
  max_dd?: number;
  distance_from_high?: number;
}

// 选股结果（单只股票）
export interface ScreenResult {
  stock_info: StockInfo;
  technical: StockTechnical;
  score: number;
  rank: number;
  reason: string;
}

// 选股任务
export interface ScreenTask {
  task_id: string;
  strategy_id: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  progress: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error?: string;
}

// 选股响应
export interface ScreenResponse {
  task_id: string;
  strategy_id: string;
  status: string;
  results: ScreenResult[];
  summary: {
    total: number;
    strategy: string;
    avg_rps: number;
  };
  created_at: string;
  completed_at?: string;
}

// WebSocket 进度消息
export interface ProgressMessage {
  progress: number;
  current: string;
  found: number;
  total: number;
  status: string;
}

// 选股请求
export interface ScreenRequest {
  strategy_id: string;
  params?: Record<string, any>;
  top_n?: number;
  parallel?: boolean;
  update_data?: boolean;
}
