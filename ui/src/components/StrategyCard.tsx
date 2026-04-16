import React from 'react';
import type { Strategy } from '../types';

interface StrategyCardProps {
  strategy: Strategy;
  selected: boolean;
  onClick: () => void;
}

const StrategyCard: React.FC<StrategyCardProps> = ({ strategy, selected, onClick }) => {
  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'RPS':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case '技术':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case '综合':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
    }
  };

  const getReturnColor = (avgReturn?: number) => {
    if (!avgReturn) return 'text-gray-500';
    return avgReturn > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400';
  };

  return (
    <div
      onClick={onClick}
      className={`
        cursor-pointer rounded-lg border-2 p-4 transition-all hover:shadow-lg
        ${
          selected
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-200 bg-white hover:border-blue-300 dark:border-gray-700 dark:bg-gray-800'
        }
      `}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {strategy.name}
          </h3>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            {strategy.description}
          </p>
        </div>
        <span
          className={`ml-2 rounded-full px-2.5 py-0.5 text-xs font-medium ${getCategoryColor(
            strategy.category
          )}`}
        >
          {strategy.category}
        </span>
      </div>

      {(strategy.avg_return !== undefined || strategy.win_rate !== undefined) && (
        <div className="mt-3 flex gap-4 text-sm">
          {strategy.avg_return !== undefined && (
            <div>
              <span className="text-gray-500 dark:text-gray-400">平均收益: </span>
              <span className={`font-semibold ${getReturnColor(strategy.avg_return)}`}>
                {strategy.avg_return > 0 ? '+' : ''}
                {strategy.avg_return.toFixed(2)}%
              </span>
            </div>
          )}
          {strategy.win_rate !== undefined && (
            <div>
              <span className="text-gray-500 dark:text-gray-400">胜率: </span>
              <span className="font-semibold text-gray-900 dark:text-white">
                {strategy.win_rate.toFixed(0)}%
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StrategyCard;
