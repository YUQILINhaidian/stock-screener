import React from 'react';

interface ProgressBarProps {
  progress: number; // 0-100
  message: string;
  found?: number;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ progress, message, found }) => {
  return (
    <div className="w-full">
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="text-gray-700 dark:text-gray-300">{message}</span>
        {found !== undefined && (
          <span className="font-medium text-blue-600 dark:text-blue-400">
            已找到 {found} 只
          </span>
        )}
      </div>
      <div className="h-2.5 w-full rounded-full bg-gray-200 dark:bg-gray-700">
        <div
          className="h-2.5 rounded-full bg-blue-600 transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
      <div className="mt-1 text-right text-xs text-gray-500">
        {progress.toFixed(1)}%
      </div>
    </div>
  );
};

export default ProgressBar;
