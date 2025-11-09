import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';

/**
 * Страница Деталей Воркспейса (Заглушка)
 */
export const WorkspaceDetailPage = () => {
  const { workspaceId } = useParams();

  return (
    <div className="min-h-screen bg-gray-100">
      {/* (Здесь должен быть компонент Header) */}

      <main className="container max-w-5xl px-4 py-8 mx-auto">
        <div className="mb-6">
          <Link
            to="/"
            className="flex items-center gap-2 text-sm text-indigo-600 hover:underline"
          >
            <ChevronLeft className="w-4 h-4" />
            Назад ко всем пространствам
          </Link>
        </div>

        <h1 className="mb-4 text-3xl font-bold">
          Настройки Воркспейса (ЗАГЛУШКА)
        </h1>
        <p className="text-lg text-gray-700">
          ID Воркспейса: <code className="px-2 py-1 bg-gray-200 rounded-md">{workspaceId}</code>
        </p>

        <div className="mt-8">
          {/* Здесь будут вкладки "Знания", "Чат", "Настройки", "Аналитика" */}
          <div className="p-8 bg-white rounded-lg shadow-md">
            <h2 className="text-xl font-semibold">Вкладка "Знания"</h2>
            <p className="mt-2 text-gray-600">
              Здесь будет интерфейс для загрузки файлов (PDF, DOCX) и добавления Q&A.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};