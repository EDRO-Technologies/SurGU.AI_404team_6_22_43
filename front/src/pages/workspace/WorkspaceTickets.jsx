import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../../api/api';
import { Modal } from '../../components/Modal';
import { HelpCircle, Archive, Check, Send } from 'lucide-react';

/**
 * Вкладка "Тикеты (HITL)"
 */
export const WorkspaceTickets = () => {
  const { workspaceId } = useParams();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedTicket, setSelectedTicket] = useState(null);
  const [resolveAnswer, setResolveAnswer] = useState('');
  const [addToKb, setAddToKb] = useState(true);
  const [isResolving, setIsResolving] = useState(false);

  useEffect(() => {
    fetchTickets();
  }, [workspaceId]);

  const fetchTickets = async () => {
    try {
      setLoading(true);
      setError(null);
      // Запрашиваем только ОТКРЫТЫЕ тикеты
      const response = await api.get(`/workspaces/${workspaceId}/tickets`, {
        params: { status: 'OPEN' }
      });
      setTickets(response.data);
    } catch (err) {
      console.error("Failed to fetch tickets:", err);
      setError("Не удалось загрузить тикеты.");
    } finally {
      setLoading(false);
    }
  };

  const openResolveModal = (ticket) => {
    setSelectedTicket(ticket);
    setResolveAnswer('');
    setAddToKb(true);
  };

  const closeResolveModal = () => {
    setSelectedTicket(null);
    setIsResolving(false);
  };

  const handleResolveSubmit = async (e) => {
    e.preventDefault();
    if (!selectedTicket || !resolveAnswer) return;

    setIsResolving(true);
    setError(null);

    try {
      await api.post(`/workspaces/${workspaceId}/tickets/${selectedTicket.id}/resolve`, {
        answer: resolveAnswer,
        add_to_knowledge_base: addToKb
      });

      // Удаляем тикет из списка в UI
      setTickets(tickets.filter(t => t.id !== selectedTicket.id));
      closeResolveModal();

    } catch (err) {
       console.error("Failed to resolve ticket:", err);
       setError("Ошибка при решении тикета."); // (Показываем ошибку в модалке)
    } finally {
      setIsResolving(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">
        Тикеты (Human-in-the-Loop)
      </h2>
      <p className="text-sm text-gray-600 mb-6">
        Здесь появляются вопросы, на которые бот не смог найти ответ.
        Ответьте на них, чтобы обучить бота.
      </p>

      {loading && <p>Загрузка...</p>}
      {error && !loading && !selectedTicket && (
        <p className="text-center text-red-600 bg-red-100 p-4 rounded-md">{error}</p>
      )}

      {/* Список тикетов */}
      {!loading && !error && (
        <ul className="divide-y divide-gray-200">
          {tickets.map((ticket) => (
            <li key={ticket.id} className="flex flex-col sm:flex-row items-start sm:items-center justify-between py-4 gap-4">
              <div className="flex items-start gap-3">
                <HelpCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {ticket.question}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(ticket.created_at).toLocaleString()} | ID сессии: ...{ticket.session_id.slice(-6)}
                  </p>
                </div>
              </div>
              <button
                onClick={() => openResolveModal(ticket)}
                className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-md shadow-sm hover:bg-indigo-700 w-full sm:w-auto justify-center"
              >
                <Check className="w-4 h-4" />
                Ответить
              </button>
            </li>
          ))}
        </ul>
      )}

      {!loading && tickets.length === 0 && (
        <div className="text-center bg-gray-50 p-10 rounded-lg">
          <Archive className="w-12 h-12 mx-auto text-gray-400" />
          <h3 className="mt-4 text-lg font-semibold text-gray-800">
            Нет открытых тикетов
          </h3>
          <p className="mt-1 text-gray-500">
            Бот успешно отвечает на все вопросы.
          </p>
        </div>
      )}

      {/* Модальное окно Решения Тикета */}
      <Modal
        isOpen={!!selectedTicket}
        onClose={closeResolveModal}
        title="Ответить на тикет"
      >
        <form onSubmit={handleResolveSubmit} className="space-y-4">
          <div className="p-3 bg-gray-50 rounded-md">
            <label className="block text-xs font-medium text-gray-500">
              Вопрос от пользователя:
            </label>
            <p className="text-sm font-medium text-gray-800 mt-1">
              {selectedTicket?.question}
            </p>
          </div>
          <div>
            <label htmlFor="resolve-answer" className="block text-sm font-medium text-gray-700">
              Ваш эталонный ответ:
            </label>
            <textarea
              id="resolve-answer"
              rows="4"
              required
              value={resolveAnswer}
              onChange={(e) => setResolveAnswer(e.target.value)}
              className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Напишите здесь правильный ответ..."
            ></textarea>
          </div>

          <div className="flex items-center">
            <input
              id="add-to-kb"
              type="checkbox"
              checked={addToKb}
              onChange={(e) => setAddToKb(e.target.checked)}
              className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
            />
            <label htmlFor="add-to-kb" className="ml-2 block text-sm text-gray-900">
              Добавить этот Q&A в Базу Знаний
            </label>
          </div>

           {error && isResolving && (
            <p className="text-sm text-red-600">{error}</p>
          )}

          <div className="flex justify-end gap-3 pt-4">
             <button
              type="button"
              onClick={closeResolveModal}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50"
            >
              Отмена
            </button>
            <button
              type="submit"
              disabled={isResolving}
              className="flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 disabled:opacity-50"
            >
              <Send className="w-4 h-4 mr-2" />
              {isResolving ? 'Отправка...' : 'Ответить и Закрыть'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};