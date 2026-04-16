import React from 'react';
import type { ScreenResult } from '../types';

interface StockTableProps {
  results: ScreenResult[];
  onViewChart?: (symbol: string) => void;
}

const StockTable: React.FC<StockTableProps> = ({ results, onViewChart }) => {
  const formatNumber = (num: number | undefined, decimals = 2) => {
    if (num === undefined || num === null) return '-';
    return num.toFixed(decimals);
  };

  const getRpsColor = (rps: number | undefined) => {
    if (!rps) return 'text-gray-500';
    if (rps >= 95) return 'text-red-600 dark:text-red-400 font-bold';
    if (rps >= 90) return 'text-orange-600 dark:text-orange-400 font-semibold';
    if (rps >= 80) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-gray-700 dark:text-gray-300';
  };

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
              排名
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
              代码
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
              名称
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
              收盘价
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
              涨幅%
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
              RPS50
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
              RPS120
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
              RPS250
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
              量比
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
              评分
            </th>
            <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
              操作
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-900">
          {results.map((result, idx) => (
            <tr
              key={result.stock_info.symbol}
              className="hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                {result.rank}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm font-mono text-gray-700 dark:text-gray-300">
                {result.stock_info.code}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">
                {result.stock_info.name}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-900 dark:text-gray-100">
                {formatNumber(result.technical.close)}
              </td>
              <td
                className={`whitespace-nowrap px-4 py-3 text-right text-sm font-medium ${
                  result.technical.change_pct > 0
                    ? 'text-red-600 dark:text-red-400'
                    : result.technical.change_pct < 0
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-gray-500'
                }`}
              >
                {result.technical.change_pct > 0 ? '+' : ''}
                {formatNumber(result.technical.change_pct)}%
              </td>
              <td
                className={`whitespace-nowrap px-4 py-3 text-right text-sm ${getRpsColor(
                  result.technical.rps_50
                )}`}
              >
                {formatNumber(result.technical.rps_50, 0)}
              </td>
              <td
                className={`whitespace-nowrap px-4 py-3 text-right text-sm ${getRpsColor(
                  result.technical.rps_120
                )}`}
              >
                {formatNumber(result.technical.rps_120, 0)}
              </td>
              <td
                className={`whitespace-nowrap px-4 py-3 text-right text-sm ${getRpsColor(
                  result.technical.rps_250
                )}`}
              >
                {formatNumber(result.technical.rps_250, 0)}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-700 dark:text-gray-300">
                {formatNumber(result.technical.volume_ratio, 1)}x
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-sm font-semibold text-blue-600 dark:text-blue-400">
                {formatNumber(result.score, 1)}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-center text-sm">
                {onViewChart && (
                  <button
                    onClick={() => onViewChart(result.stock_info.symbol)}
                    className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                  >
                    📈 K线
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default StockTable;
