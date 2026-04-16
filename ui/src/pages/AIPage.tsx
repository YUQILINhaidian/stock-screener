import { useState } from 'react';
import { SparklesIcon, ChartBarIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { aiAPI } from '../services/api';

export default function AIPage() {
  const [loading, setLoading] = useState(false);
  const [marketAnalysis, setMarketAnalysis] = useState<any>(null);
  const [stockAnalysis, setStockAnalysis] = useState<any>(null);
  const [nlQuery, setNlQuery] = useState('');
  const [stockSymbol, setStockSymbol] = useState('');

  const handleMarketAnalysis = async () => {
    setLoading(true);
    try {
      const result = await aiAPI.analyzeMarket('SSE', '1M');
      setMarketAnalysis(result);
    } catch (error) {
      console.error('市场分析失败:', error);
      alert('市场分析失败，请检查 AI 配置');
    } finally {
      setLoading(false);
    }
  };

  const handleStockAnalysis = async () => {
    if (!stockSymbol.trim()) {
      alert('请输入股票代码');
      return;
    }
    setLoading(true);
    try {
      const result = await aiAPI.analyzeStock(stockSymbol);
      setStockAnalysis(result);
    } catch (error) {
      console.error('个股分析失败:', error);
      alert('个股分析失败');
    } finally {
      setLoading(false);
    }
  };

  const handleNLScreen = async () => {
    if (!nlQuery.trim()) {
      alert('请输入选股需求');
      return;
    }
    setLoading(true);
    try {
      const result = await aiAPI.nlScreen(nlQuery);
      alert(`生成的筛选条件：\n${JSON.stringify(result.generated_conditions, null, 2)}`);
    } catch (error) {
      console.error('自然语言选股失败:', error);
      alert('自然语言选股失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <SparklesIcon className="h-8 w-8 mr-3 text-indigo-600" />
            AI 投资助手
          </h1>
          <p className="mt-2 text-gray-600">
            使用 AI 分析市场环境、解读个股、智能选股
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 市场环境分析 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <ChartBarIcon className="h-6 w-6 mr-2 text-blue-600" />
              市场环境分析
            </h2>
            
            <button
              onClick={handleMarketAnalysis}
              disabled={loading}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
            >
              {loading ? '分析中...' : '🔍 分析当前市场'}
            </button>

            {marketAnalysis && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">市场趋势：</span>
                    <span className={`font-semibold ${
                      marketAnalysis.trend === 'bull' ? 'text-red-600' :
                      marketAnalysis.trend === 'bear' ? 'text-green-600' :
                      'text-gray-600'
                    }`}>
                      {marketAnalysis.trend === 'bull' ? '🐂 牛市' :
                       marketAnalysis.trend === 'bear' ? '🐻 熊市' :
                       '📊 震荡市'}
                    </span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">置信度：</span>
                    <span className="font-semibold">
                      {(marketAnalysis.confidence * 100).toFixed(0)}%
                    </span>
                  </div>

                  <div className="pt-3 border-t border-gray-200">
                    <p className="text-sm text-gray-700">{marketAnalysis.reason}</p>
                  </div>

                  <div className="pt-3 border-t border-gray-200">
                    <p className="text-sm font-medium text-gray-700 mb-2">推荐策略：</p>
                    <div className="flex flex-wrap gap-2">
                      {marketAnalysis.recommended_strategies?.map((strategy: string, idx: number) => (
                        <span key={idx} className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm">
                          {strategy}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 个股 AI 解读 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <SparklesIcon className="h-6 w-6 mr-2 text-purple-600" />
              个股 AI 解读
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  股票代码
                </label>
                <input
                  type="text"
                  value={stockSymbol}
                  onChange={(e) => setStockSymbol(e.target.value)}
                  placeholder="例如：300185"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>

              <button
                onClick={handleStockAnalysis}
                disabled={loading}
                className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 transition-colors"
              >
                {loading ? '分析中...' : '🤖 AI 深度解读'}
              </button>
            </div>

            {stockAnalysis && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <div className="space-y-3">
                  <div>
                    <span className="text-lg font-semibold text-gray-900">
                      {stockAnalysis.name} ({stockAnalysis.symbol})
                    </span>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">综合评分：</span>
                    <span className="text-2xl font-bold text-indigo-600">
                      {stockAnalysis.score}
                    </span>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">建议操作：</span>
                    <span className={`font-semibold ${
                      stockAnalysis.action === 'buy' ? 'text-red-600' :
                      stockAnalysis.action === 'sell' ? 'text-green-600' :
                      'text-gray-600'
                    }`}>
                      {stockAnalysis.action === 'buy' ? '📈 买入' :
                       stockAnalysis.action === 'sell' ? '📉 卖出' :
                       '⏸️ 持有'}
                    </span>
                  </div>

                  <div className="pt-3 border-t border-gray-200">
                    <p className="text-sm text-gray-700">{stockAnalysis.summary}</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 自然语言选股 */}
          <div className="bg-white rounded-lg shadow p-6 lg:col-span-2">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <MagnifyingGlassIcon className="h-6 w-6 mr-2 text-green-600" />
              自然语言智能选股
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  描述您的选股需求
                </label>
                <textarea
                  value={nlQuery}
                  onChange={(e) => setNlQuery(e.target.value)}
                  placeholder="例如：找出最近突破的新能源龙头股，RPS120大于90，量比大于1.5"
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
                />
              </div>

              <button
                onClick={handleNLScreen}
                disabled={loading}
                className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 transition-colors"
              >
                {loading ? '分析中...' : '🧠 AI 智能解析'}
              </button>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                  <strong>💡 提示：</strong> 您可以用自然语言描述选股条件，AI 会自动将其转换为结构化的筛选条件。
                  支持描述行业、RPS、量比、市值、涨跌幅、突破等条件。
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
