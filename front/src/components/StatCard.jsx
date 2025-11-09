import React from 'react';

/**
 * Карточка для статистики на дашборде
 */
export const StatCard = ({ title, value, icon }) => {
  return (
    <div className="p-5 bg-white rounded-lg shadow-md">
      <div className="flex items-center justify-between">
        <div className="flex-shrink-0">
          {icon}
        </div>
        <div className="text-right">
          <p className="text-sm font-medium text-gray-500 truncate">
            {title}
          </p>
          <p className="mt-1 text-3xl font-semibold text-gray-900">
            {value}
          </p>
        </div>
      </div>
    </div>
  );
};