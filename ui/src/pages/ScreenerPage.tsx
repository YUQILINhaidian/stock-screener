import React, { useState, useEffect, useRef } from 'react';
import { screenAPI, createScreenWebSocket } from '../services/api';
import type { Strategy, ScreenResult, ProgressMessage } from '../types';
import StrategyCard from '../components/StrategyCard';
import ProgressBar from '../components/ProgressBar';
import StockTable from '../components/StockTable';

const ScreenerPage: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [screening, setScreening] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [foundCount, setFoundCount] = useState(0);
  const [results, setResults] = useState<ScreenResult[]>([]);
  const [error, setError] = useState<string>('');

  const wsRef = useRef<WebSocket | null>(null);

  // 加载策略列表
  useEffect(() => {
    loadStrategies();
  }, []);

  const loadStrategies = async () => {
    try {
      setLoading(true);
      const data = await screenAPI.getStrategies();
      setStrategies(data);
      // 默认选中第一个策略
      if (data.length > 0) {
        setSelectedStrategy(data[0].id);
      }
    } catch (err) {
      setError('加载策略列表失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // 执行选股
  const handleRunScreen = async () => {
    if (!selectedStrategy) {
      setError('请选择一个策略');
      return;
    }

    try {
      setScreening(true);
      setError('');
      setProgress(0);
      setProgressMessage('正在提交选股任务...');
      setResults([]);

      // 提交选股任务
      const task = await screenAPI.runScreen({
        strategy_id: selectedStrategy,
        top_n: 50,
      });

      // 连接 WebSocket 监听进度
      wsRef.current = createScreenWebSocket(
        task.task_id,
        (data: ProgressMessage) => {
          setProgress(data.progress);
          setProgressMessage(data.current);
          setFoundCount(data.found);

          // 如果完成，获取结果
          if (data.status === 'completed') {
            loadResults(task.task_id);
          } else if (data.status === 'error') {
            setError('选股失败：' + data.current);
            setScreening(false);
          }
        },
        (error) => {
          console.error('WebSocket error:', error);
          // WebSocket 失败时轮询结果
          pollResults(task.task_id);
        }
      );
    } catch (err: any) {
      setError('执行选股失败：' + (err.message || '未知错误'));
      setScreening(false);
    }
  };

  // 加载选股结果
  const loadResults = async (taskId: string) => {
    try {
      const response = await screenAPI.getScreenResult(taskId);
      if (response.status === 'completed') {
        setResults(response.results);
        setScreening(false);
        wsRef.current?.close();
      }
    } catch (err: any) {
      setError('获取结果失败：' + (err.message || '未知错误'));
      setScreening(false);
    }
  };

  // 轮询结果（WebSocket 失败时的备选方案）
  const pollResults = async (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await screenAPI.getScreenResult(taskId);
        if (response.status === 'completed') {
          setResults(response.results);
          setProgress(100);
          setProgressMessage('选股完成！');
          setScreening(false);
          clearInterval(interval);
        } else if (response.status === 'error') {
          setError('选股失败');
          setScreening(false);
          clearInterval(interval);
        } else {
          // 更新进度（估算）
          setProgress((prev) => Math.min(prev + 5, 95));
        }
      } catch (err) {
        console.error('轮询结果失败:', err);
      }
    }, 2000);
  };

  // 清理 WebSocket
  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  const selectedStrategyInfo = strategies.find((s) => s.id === selectedStrategy);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* 标题 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            选股中心 📈
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            选择策略，一键筛选强势股票
          </p>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="mb-6 rounded-lg bg-red-50 p-4 dark:bg-red-900/20">
            <p className="text-sm text-red-800 dark:text-red-200">❌ {error}</p>
          </div>
        )}

        {/* 策略选择 */}
        <div className="mb-8">
          <h2 className="mb-4 text-xl font-semibold text-gray-900 dark:text-white">
            1. 选择策略
          </h2>
          {loading ? (
            <div className="text-gray-600 dark:text-gray-400">加载策略中...</div>
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {strategies.map((strategy) => (
                <StrategyCard
                  key={strategy.id}
                  strategy={strategy}
                  selected={selectedStrategy === strategy.id}
                  onClick={() => setSelectedStrategy(strategy.id)}
                />
              ))}
            </div>
          )}
        </div>

        {/* 执行选股 */}
        <div className="mb-8">
          <h2 className="mb-4 text-xl font-semibold text-gray-900 dark:text-white">
            2. 执行选股
          </h2>
          <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
            {selectedStrategyInfo && (
              <div className="mb-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  当前策略：
                  <span className="ml-2 font-semibold text-gray-900 dark:text-white">
                    {selectedStrategyInfo.name}
                  </span>
                </p>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-500">
                  {selectedStrategyInfo.description}
                </p>
              </div>
            )}
            
            <button
              onClick={handleRunScreen}
              disabled={screening || !selectedStrategy}
              className="rounded-lg bg-blue-600 px-6 py-3 text-white hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {screening ? '选股中...' : '🚀 开始选股'}
            </button>

            {screening && (
              <div className="mt-6">
                <ProgressBar
                  progress={progress}
                  message={progressMessage}
                  found={foundCount}
                />
              </div>
            )}
          </div>
        </div>

        {/* 选股结果 */}
        {results.length > 0 && (
          <div>
            <h2 className="mb-4 text-xl font-semibold text-gray-900 dark:text-white">
              3. 选股结果 ({results.length} 只)
            </h2>
            <StockTable results={results} />
          </div>
        )}
      </div>
    </div>
  );
};

export default ScreenerPage;
