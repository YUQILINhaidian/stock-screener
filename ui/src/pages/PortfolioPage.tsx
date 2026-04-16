import { useState, useEffect } from 'react';
import { ClipboardDocumentListIcon, PlusIcon, TrashIcon } from '@heroicons/react/24/outline';
import { portfolioAPI } from '../services/api';

export default function PortfolioPage() {
  const [portfolios, setPortfolios] = useState<any[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newPortfolioName, setNewPortfolioName] = useState('');

  useEffect(() => {
    loadPortfolios();
  }, []);

  const loadPortfolios = async () => {
    try {
      const summary = await portfolioAPI.getSummary();
      setPortfolios(summary.portfolios || []);
    } catch (error) {
      console.error('加载股票池失败:', error);
    }
  };

  const handleCreatePortfolio = async () => {
    if (!newPortfolioName.trim()) {
      alert('请输入股票池名称');
      return;
    }

    setLoading(true);
    try {
      await portfolioAPI.createPortfolio({
        name: newPortfolioName,
        description: '',
        stocks: [],
      });
      setNewPortfolioName('');
      setShowCreateModal(false);
      loadPortfolios();
    } catch (error) {
      console.error('创建股票池失败:', error);
      alert('创建失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPortfolio = async (portfolioId: string) => {
    setLoading(true);
    try {
      const portfolio = await portfolioAPI.getPortfolio(portfolioId);
      setSelectedPortfolio(portfolio);
    } catch (error) {
      console.error('获取股票池详情失败:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center">
              <ClipboardDocumentListIcon className="h-8 w-8 mr-3 text-indigo-600" />
              股票池管理
            </h1>
            <p className="mt-2 text-gray-600">
              管理和跟踪您的股票池
            </p>
          </div>
          
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            创建股票池
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 股票池列表 */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow">
              <div className="p-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold">我的股票池</h2>
              </div>
              
              <div className="divide-y divide-gray-200">
                {portfolios.length === 0 ? (
                  <div className="p-8 text-center text-gray-500">
                    <ClipboardDocumentListIcon className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                    <p>暂无股票池</p>
                    <p className="text-sm mt-1">点击"创建股票池"开始</p>
                  </div>
                ) : (
                  portfolios.map((portfolio) => (
                    <div
                      key={portfolio.id}
                      onClick={() => handleSelectPortfolio(portfolio.id)}
                      className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                        selectedPortfolio?.id === portfolio.id ? 'bg-indigo-50 border-l-4 border-indigo-600' : ''
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-medium text-gray-900">{portfolio.name}</h3>
                          <p className="text-sm text-gray-500 mt-1">
                            {portfolio.stock_count || 0} 只股票
                          </p>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (confirm('确定要删除这个股票池吗？')) {
                              // TODO: 实现删除
                            }
                          }}
                          className="text-red-600 hover:text-red-800"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* 股票池详情 */}
          <div className="lg:col-span-2">
            {!selectedPortfolio ? (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <ClipboardDocumentListIcon className="h-16 w-16 mx-auto text-gray-300 mb-4" />
                <p className="text-gray-500">选择一个股票池查看详情</p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* 基本信息 */}
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h2 className="text-2xl font-bold text-gray-900">{selectedPortfolio.name}</h2>
                      <p className="text-gray-600 mt-1">{selectedPortfolio.description || '暂无描述'}</p>
                    </div>
                    <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium">
                      {selectedPortfolio.stocks?.length || 0} 只股票
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-4 mt-6">
                    <div className="bg-red-50 rounded-lg p-4">
                      <p className="text-sm text-red-600 mb-1">总收益率</p>
                      <p className="text-2xl font-bold text-red-700">
                        {(selectedPortfolio.total_return || 0).toFixed(2)}%
                      </p>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-4">
                      <p className="text-sm text-blue-600 mb-1">平均涨幅</p>
                      <p className="text-2xl font-bold text-blue-700">
                        {(selectedPortfolio.avg_change || 0).toFixed(2)}%
                      </p>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4">
                      <p className="text-sm text-green-600 mb-1">胜率</p>
                      <p className="text-2xl font-bold text-green-700">
                        {(selectedPortfolio.win_rate || 0).toFixed(2)}%
                      </p>
                    </div>
                  </div>
                </div>

                {/* 股票列表 */}
                <div className="bg-white rounded-lg shadow overflow-hidden">
                  <div className="p-4 border-b border-gray-200">
                    <h3 className="text-lg font-semibold">持仓股票</h3>
                  </div>
                  
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            代码
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            名称
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            买入价
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            当前价
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            涨跌幅
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            持有天数
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {selectedPortfolio.stocks?.length === 0 ? (
                          <tr>
                            <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                              暂无持仓股票
                            </td>
                          </tr>
                        ) : (
                          selectedPortfolio.stocks?.map((stock: any, idx: number) => (
                            <tr key={idx} className="hover:bg-gray-50">
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                {stock.code}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {stock.name}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                ¥{stock.entry_price?.toFixed(2)}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                ¥{stock.current_price?.toFixed(2)}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm">
                                <span className={`font-medium ${
                                  (stock.change_pct || 0) >= 0 ? 'text-red-600' : 'text-green-600'
                                }`}>
                                  {(stock.change_pct || 0) >= 0 ? '+' : ''}
                                  {(stock.change_pct || 0).toFixed(2)}%
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {stock.holding_days || 0} 天
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 创建股票池弹窗 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-semibold mb-4">创建股票池</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  股票池名称
                </label>
                <input
                  type="text"
                  value={newPortfolioName}
                  onChange={(e) => setNewPortfolioName(e.target.value)}
                  placeholder="例如：月线反转股票池"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  autoFocus
                />
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleCreatePortfolio}
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 transition-colors"
                >
                  {loading ? '创建中...' : '创建'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
