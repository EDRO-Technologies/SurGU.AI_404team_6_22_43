import React, { useState, useEffect } from 'react';
import { Outlet, NavLink, useParams, useNavigate, Link } from 'react-router-dom';
import api from '../api/api';
import { Header } from './Header';
import {
  BookText,
  MessageSquare,
  BarChart3,
  Settings,
  AlertOctagon,
  ChevronLeft
} from 'lucide-react';

// Компонент для вкладки
const TabLink = ({ to, icon, children }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      `flex items-center gap-3 px-4 py-3 rounded-md text-sm font-medium ${
        isActive 
        ? 'bg-indigo-100 text-indigo-700' 
        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
      }`
    }
  >
    {icon}
    <span>{children}</span>
  </NavLink>
);

/**
 * Основной макет для страницы Воркспейса
 * Показывает хедер, название воркспейса, вкладки и
 * рендерит дочерний маршрут (вкладку)
 */
export const WorkspaceLayout = () => {
  const { workspaceId } = useParams();
  const [workspace, setWorkspace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchWorkspace = async () => {
      try {
        setLoading(true);
        const response = await api.get(`/workspaces/${workspaceId}`);
        setWorkspace(response.data);
      } catch (err) {
        console.error("Failed to fetch workspace details:", err);
        setError("Не удалось загрузить воркспейс.");
        if (err.response?.status === 404) {
          navigate('/'); // Если не найдено, уходим на главную
        }
      } finally {
        setLoading(false);
      }
    };

    fetchWorkspace();
  }, [workspaceId, navigate]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="ml-4 text-lg font-medium text-gray-700">Загрузка воркспейса...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <p className="text-red-600">{error}</p>
        <Link to="/" className="ml-4 text-indigo-600 hover:underline">На главную</Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <Header />

      {/* Под-хедер Воркспейса */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="container max-w-6xl px-4 py-4 mx-auto">
          <Link
            to="/"
            className="flex items-center gap-1 mb-3 text-sm text-indigo-600 hover:underline"
          >
            <ChevronLeft className="w-4 h-4" />
            Все пространства
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">
            {workspace?.name}
          </h1>
          <p className="mt-1 text-gray-500">
            {workspace?.description}
          </p>
        </div>
      </div>

      {/* Основной контент с боковым меню */}
      <div className="container max-w-6xl px-4 py-8 mx-auto">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-4">

          {/* Навигация (вкладки) */}
          <aside className="md:col-span-1">
            <nav className="flex flex-col space-y-2">
              <TabLink to="knowledge" icon={<BookText className="w-5 h-5" />}>
                База знаний
              </TabLink>
              <TabLink to="chat" icon={<MessageSquare className="w-5 h-5" />}>
                Тест чата
              </TabLink>
              <TabLink to="analytics" icon={<BarChart3 className="w-5 h-5" />}>
                Аналитика
              </TabLink>
              <TabLink to="tickets" icon={<AlertOctagon className="w-5 h-5" />}>
                Тикеты (HITL)
              </TabLink>
              <TabLink to="settings" icon={<Settings className="w-5 h-5" />}>
                Настройки
              </TabLink>
            </nav>
          </aside>

          {/* Содержимое вкладки */}
          <main className="md:col-span-3">
            {/* <Outlet> рендерит компонент текущей вложенной вкладки */}
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
};