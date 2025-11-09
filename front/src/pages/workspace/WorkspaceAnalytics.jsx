import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../../api/api';
import { StatCard } from '../../components/StatCard';
import { MessageSquare, Check, X, HelpCircle, TrendingUp } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

/**
 * Вкладка "Аналитика"
 */
export const WorkspaceAnalytics = () => {
  const { workspaceId } = useParams();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [period, setPeriod] = useState('7d');

  useEffect(() => {
    fetchAnalytics();
  }, [workspaceId, period]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get(`/workspaces/${workspaceId}/analytics`, {
        params: { period }
      });
      setStats(response.data);
    } catch (err) {
      console.error("Failed to fetch analytics:", err);
      setError("Не удалось загрузить аналитику.");
    } finally {
      setLoading(false);
    }
  };

  const getSuccessRate = () => {
    if (!stats || stats.total_queries === 0) return 0;
    return ((stats.answered_queries / stats.total_queries) * 100).toFixed(1);
  };

  const chartData = stats?.top_questions.map(q => ({
    name: q.question.length > 30 ? q.question.slice(0, 30) + '...' : q.question,
    fullQuestion: q.question,
    count: q.count
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-gray-900">
          Аналитика
        </h2>
        {/* Селектор периода (упрощенный) */}
        <select
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          className="px-3 py-2 text-sm bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500"
        >
          <option value="24h">24 часа</option>
          <option value="7d">7 дней</option>
          <option value="30d">30 дней</option>
        </select>
      </div>

      {loading && <p>Загрузка...</p>}
      {error && !loading && (
        <p className="text-center text-red-600 bg-red-100 p-4 rounded-md">{error}</p>
      )}

      {stats && !loading && (
        <>
          {/* 1. Карточки статистики */}
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-4">
            <StatCard
              title="Всего запросов"
              value={stats.total_queries}
              icon={<MessageSquare className="w-8 h-8 text-blue-500" />}
            />
            <StatCard
              title="Отвечено"
              value={stats.answered_queries}
              icon={<Check className="w-8 h-8 text-green-500" />}
            />
            <StatCard
              title="Без ответа (Тикеты)"
              value={stats.unanswered_queries}
              icon={<X className="w-8 h-8 text-red-500" />}
            />
             <StatCard
              title="Успешность (%)"
              value={`${getSuccessRate()}%`}
              icon={<TrendingUp className="w-8 h-8 text-indigo-500" />}
            />
          </div>

          {/* 2. График "Топ вопросов" */}
          <div className="p-6 bg-white rounded-lg shadow-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Топ 5 популярных вопросов
            </h3>
            <div style={{ width: '100%', height: 300 }}>
              <ResponsiveContainer>
                <BarChart
                  data={chartData}
                  margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" fontSize={12} />
                  <YAxis allowDecimals={false} />
                  <Tooltip
                    formatter={(value) => [value, 'Запросов']}
                    labelFormatter={(label, payload) => payload[0]?.payload.fullQuestion}
                    wrapperClassName="rounded-md shadow-lg"
                  />
                  <Legend />
                  <Bar dataKey="count" fill="#4f46e5" name="Кол-во запросов" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 3. Список "Топ вопросов без ответа" */}
          <div className="p-6 bg-white rounded-lg shadow-md">
             <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Топ вопросов без ответа (Тикеты)
            </h3>
            <ul className="divide-y divide-gray-200">
              {stats.top_unanswered_questions.map((q) => (
                <li key={q.ticket_id} className="flex items-center justify-between py-3">
                  <div className="flex items-center gap-3">
                    <HelpCircle className="w-5 h-5 text-yellow-600" />
                    <span className="text-sm text-gray-800">{q.question}</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900">{q.count}</span>
                </li>
              ))}
               {stats.top_unanswered_questions.length === 0 && (
                <p className="text-center text-gray-500 py-5">
                  Отлично! Вопросов без ответа нет.
                </p>
               )}
            </ul>
          </div>
        </>
      )}
    </div>
  );
};