import { useState } from 'react';
import { BeakerIcon, ClockIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import { backtestAPI } from '../services/api';

export default function BacktestPage() {
  const [loading, setLoading] = useState(false);
  const [strategyId, setStrategyId] = useState('monthly_reversal');
  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState('2024-12-31');
  const [initialCapital, setInitialCapital] = useState(1000000);
  const [result, setResult] = useState<any>(null);

  const strategies = [
    { id: 'monthly_reversal', name: '月线反转策略' },
    { id: 'pocket_pivot', name: '口袋支点策略' },
    { id: 'train', name: '火车头策略' },
  ];

  const handleBacktest = async () => {
    setLoading(true);
    try {
      const task = await backtestAPI.createBacktest({
        strategy_id: strategyId,
        start_date: startDate,
        end_date: endDate,
        initial_capital: initialCapital,
      });

      // 轮询获取结果
      let attempts = 0;
      const maxAttempts = 30;
      const interval = setInterval(async () => {
        attempts++;
        try {
          const bt_result = await backtestAPI.getBacktestResult(task.task_id);
          if (bt_result.status === 'completed') {
            setResult(bt_result);
            setLoading(false);
            clearInterval(interval);
          } else if (bt_result.status === 'failed' || attempts >= maxAttempts) {
            alert('回测失败或超时');
            setLoading(false);
            clearInterval(interval);
          }
        } catch (error) {
          console.error('获取回测结果失败:', error);
        }
      }, 2000);
    } catch (error) {
      console.error('创建回测任务失败:', error);
      alert('回测失败');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <BeakerIcon className="h-8 w-8 mr-3 text-green-600" />
            回测中心
          </h1>
          <p className="mt-2 text-gray-600">
            验证策略历史表现，优化参数配置
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 配置面板 */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">回测配置</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    选择策略
                  </label>
                  <select
                    value={strategyId}
                    onChange={(e) => setStrategyId(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  >
                    {strategies.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    开始日期
                  </label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    结束日期
                  </label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    初始资金
                  </label>
                  <input
                    type="number"
                    value={initialCapital}
                    onChange={(e) => setInitialCapital(Number(e.target.value))}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>

                <button
                  onClick={handleBacktest}
                  disabled={loading}
                  className="w-full px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 transition-colors font-medium"
                >
                  {loading ? '🔄 回测中...' : '🚀 开始回测'}
                </button>
              </div>
            </div>
          </div>

          {/* 结果面板 */}
          <div className="lg:col-span-2">
            {!result ? (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <BeakerIcon className="h-16 w-16 mx-auto text-gray-300 mb-4" />
                <p className="text-gray-500">配置回测参数后，点击"开始回测"查看结果</p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* 核心指标 */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-lg font-semibold mb-4 flex items-center">
                    <ChartBarIcon className="h-6 w-6 mr-2 text-blue-600" />
                    回测结果
                  </h2>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
                      <p className="text-sm text-blue-600 mb-1">总收益率</p>
                      <p className={`text-2xl font-bold ${
                        (result.metrics?.total_return || 0) >= 0 ? 'text-red-600' : 'text-green-600'
                      }`}>
                        {((result.metrics?.total_return || 0) * 100).toFixed(2)}%
                      </p>
                    </div>

                    <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
                      <p className="text-sm text-green-600 mb-1">年化收益</p>
                      <p className="text-2xl font-bold text-green-700">
                        {((result.metrics?.annual_return || 0) * 100).toFixed(2)}%
                      </p>
                    </div>

                    <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
                      <p className="text-sm text-purple-600 mb-1">夏普比率</p>
                      <p className="text-2xl font-bold text-purple-700">
                        {(result.metrics?.sharpe_ratio || 0).toFixed(2)}
                      </p>
                    </div>

                    <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-4">
                      <p className="text-sm text-orange-600 mb-1">最大回撤</p>
                      <p className="text-2xl font-bold text-orange-700">
                        {((result.metrics?.max_drawdown || 0) * 100).toFixed(2)}%
                      </p>
                    </div>

                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-sm text-gray-600 mb-1">胜率</p>
                      <p className="text-2xl font-bold text-gray-700">
                        {((result.metrics?.win_rate || 0) * 100).toFixed(2)}%
                      </p>
                    </div>

                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-sm text-gray-600 mb-1">总交易次数</p>
                      <p className="text-2xl font-bold text-gray-700">
                        {result.metrics?.total_trades || 0}
                      </p>
                    </div>

                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-sm text-gray-600 mb-1">盈亏比</p>
                      <p className="text-2xl font-bold text-gray-700">
                        {(result.metrics?.profit_factor || 0).toFixed(2)}
                      </p>
                    </div>

                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-sm text-gray-600 mb-1">卡尔玛比率</p>
                      <p className="text-2xl font-bold text-gray-700">
                        {(result.metrics?.calmar_ratio || 0).toFixed(2)}
                      </p>
                    </div>
                  </div>
                </div>

                {/* 时间信息 */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold mb-3 flex items-center">
                    <ClockIcon className="h-5 w-5 mr-2 text-gray-600" />
                    回测信息
                  </h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">回测周期：</span>
                      <span className="ml-2 font-medium">{startDate} ~ {endDate}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">初始资金：</span>
                      <span className="ml-2 font-medium">¥{initialCapital.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">最终资金：</span>
                      <span className="ml-2 font-medium text-blue-600">
                        ¥{(result.metrics?.final_value || initialCapital).toLocaleString()}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">策略：</span>
                      <span className="ml-2 font-medium">
                        {strategies.find(s => s.id === strategyId)?.name}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
