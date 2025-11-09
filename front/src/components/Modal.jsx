import React from 'react';
import { X } from 'lucide-react';

/**
 * Простой компонент Модального окна
 */
export const Modal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) {
    return null;
  }

  return (
    // Backdrop (фон)
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 backdrop-blur-sm"
      onClick={onClose}
    >
      {/* Окно */}
      <div
        className="relative w-full max-w-lg p-6 bg-white rounded-lg shadow-xl"
        onClick={(e) => e.stopPropagation()} // Предотвращает закрытие при клике внутри
      >
        {/* Хедер окна */}
        <div className="flex items-center justify-between pb-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            {title}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 rounded-full hover:bg-gray-100 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Контент окна */}
        <div className="mt-4">
          {children}
        </div>
      </div>
    </div>
  );
};