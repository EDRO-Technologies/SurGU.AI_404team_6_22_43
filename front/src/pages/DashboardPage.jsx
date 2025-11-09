import React, { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/api';
import { AuthContext } from '../context/AuthContext';
import { Plus, BrainCircuit } from 'lucide-react';
import { Header } from '../layouts/Header';
import { Modal } from '../components/Modal';

/**
 * Страница "Панель управления"
 * Показывает список воркспейсов
 */
export const DashboardPage = () => {
  const [workspaces, setWorkspaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newWsName, setNewWsName] = useState('');
  const [newWsDesc, setNewWsDesc] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    fetchWorkspaces();
  }, []);

  const fetchWorkspaces = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/workspaces');
      setWorkspaces(response.data);
    } catch (err) {
      console.error("Failed to fetch workspaces:", err);
      setError('Не удалось загрузить рабочие пространства.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWorkspace = async (e) => {
    e.preventDefault();
    setIsCreating(true);
    setError(null);
    try {
      const response = await api.post('/workspaces', {
        name: newWsName,
        description: newWsDesc
      });
      setWorkspaces([response.data, ...workspaces]);
      setIsModalOpen(false);
      setNewWsName('');
      setNewWsDesc('');
    } catch (err) {
      console.error("Failed to create workspace:", err);
      setError('Ошибка при создании. Попробуйте снова.');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Header />
      <main className="container max-w-6xl px-4 py-8 mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900">
            Рабочие пространства
          </h1>
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 font-medium text-white bg-indigo-600 rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            <Plus className="w-5 h-5" />
            Создать пространство
          </button>
        </div>

        {loading && (
           <div className="flex justify-center mt-10">
            <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        )}
        {error && !loading && (
          <p className="text-center text-red-600 bg-red-100 p-4 rounded-md">{error}</p>
        )}

        {!loading && !error && (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {workspaces.map((ws) => (
              <Link
                to={`/workspace/${ws.id}`}
                key={ws.id}
                className="flex flex-col justify-between block p-6 bg-white rounded-lg shadow-md transition-shadow hover:shadow-lg"
              >
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">{ws.name}</h3>
                  <p className="mt-2 text-sm text-gray-600">
                    {ws.description || 'Нет описания'}
                  </p>
                </div>
                <span className="inline-block mt-4 text-sm font-medium text-indigo-600">
                  Управлять &rarr;
                </span>
              </Link>
            ))}
          </div>
        )}
         {!loading && workspaces.length === 0 && (
          <div className="text-center bg-white p-10 rounded-lg shadow-md">
            <BrainCircuit className="w-16 h-16 mx-auto text-gray-400" />
            <h3 className="mt-4 text-xl font-semibold text-gray-800">У вас пока нет воркспейсов</h3>
            <p className="mt-2 text-gray-500">
              Начните с создания своего первого AI-ассистента.
            </p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 mx-auto mt-6 font-medium text-white bg-indigo-600 rounded-md shadow-sm hover:bg-indigo-700"
            >
              <Plus className="w-5 h-5" />
              Создать
            </button>
          </div>
        )}
      </main>

      {/* Модальное окно создания */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Новое рабочее пространство"
      >
        <form onSubmit={handleCreateWorkspace} className="space-y-4">
          <div>
            <label
              htmlFor="ws-name"
              className="block text-sm font-medium text-gray-700"
            >
              Название
            </label>
            <input
              id="ws-name"
              type="text"
              required
              value={newWsName}
              onChange={(e) => setNewWsName(e.target.value)}
              className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Например, 'Бот для HR-отдела'"
            />
          </div>
          <div>
            <label
              htmlFor="ws-desc"
              className="block text-sm font-medium text-gray-700"
            >
              Описание (опционально)
            </label>
            <textarea
              id="ws-desc"
              rows="3"
              value={newWsDesc}
              onChange={(e) => setNewWsDesc(e.target.value)}
              className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Отвечает на вопросы по отпускам и больничным"
            ></textarea>
          </div>
          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50"
            >
              Отмена
            </button>
            <button
              type="submit"
              disabled={isCreating}
              className="flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 disabled:opacity-50"
            >
              {isCreating ? 'Создание...' : 'Создать'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};