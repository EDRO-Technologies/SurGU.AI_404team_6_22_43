import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../../api/api';
import { UserPlus, Trash2, Copy, Check } from 'lucide-react';
import { Modal } from '../../components/Modal';

/**
 * Вкладка "Настройки" (Управление пользователями и Код виджета)
 */
export const WorkspaceSettings = () => {
  const { workspaceId } = useParams();

  // Управление пользователями
  const [users, setUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [userError, setUserError] = useState(null);

  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('Editor');
  const [isInviting, setIsInviting] = useState(false);

  // Код виджета
  const [widgetCode, setWidgetCode] = useState('');
  const [isCopied, setIsCopied] = useState(false);

  // При загрузке получаем пользователей и генерируем код
  useEffect(() => {
    fetchUsers();

    // Генерируем код виджета.
    // API_V1_STR берется из .env бэкенда, виджет.js отдается по /api/v1/widget.js
    const code = `<script 
  src="${window.location.origin}/api/v1/widget.js" 
  data-workspace-id="${workspaceId}"
  async 
  defer
></script>`;
    setWidgetCode(code);

  }, [workspaceId]);

  // Загрузка пользователей
  const fetchUsers = async () => {
    try {
      setLoadingUsers(true);
      setUserError(null);
      const response = await api.get(`/workspaces/${workspaceId}/users`);
      setUsers(response.data);
    } catch (err) {
      console.error("Failed to fetch users:", err);
      setUserError("Не удалось загрузить список пользователей.");
    } finally {
      setLoadingUsers(false);
    }
  };

  // Приглашение пользователя
  const handleInviteUser = async (e) => {
    e.preventDefault();
    setIsInviting(true);
    setUserError(null);
    try {
      const response = await api.post(`/workspaces/${workspaceId}/users`, {
        email: inviteEmail,
        role: inviteRole
      });
      setUsers([...users, response.data]);
      setIsInviteModalOpen(false);
      setInviteEmail('');
    } catch (err) {
      console.error("Failed to invite user:", err);
      setUserError(err.response?.data?.detail || "Ошибка при приглашении.");
    } finally {
      setIsInviting(false);
    }
  };

  // Удаление пользователя
  const handleRemoveUser = async (userId) => {
     if (!window.confirm("Вы уверены, что хотите удалить этого пользователя из воркспейса?")) {
      return;
    }
    try {
      await api.delete(`/workspaces/${workspaceId}/users/${userId}`);
      setUsers(users.filter(u => u.user_id !== userId));
    } catch (err) {
      console.error("Failed to remove user:", err);
      alert("Не удалось удалить пользователя.");
    }
  }

  // Копирование кода виджета
  const copyToClipboard = () => {
    navigator.clipboard.writeText(widgetCode).then(() => {
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    });
  }

  return (
    <div className="space-y-8">
      {/* 1. Управление пользователями */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">
            Управление доступом
          </h2>
          <button
            onClick={() => setIsInviteModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md shadow-sm hover:bg-indigo-700"
          >
            <UserPlus className="w-5 h-5" />
            Пригласить
          </button>
        </div>

        {loadingUsers && <p>Загрузка...</p>}
        {userError && !isInviting && (
          <p className="text-sm text-red-600">{userError}</p>
        )}

        <ul className="divide-y divide-gray-200">
          {users.map(user => (
            <li key={user.user_id} className="flex items-center justify-between py-3">
              <div>
                <p className="text-sm font-medium text-gray-900">{user.full_name}</p>
                <p className="text-sm text-gray-500">{user.email}</p>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-700 bg-gray-100 px-3 py-1 rounded-full font-medium">
                  {user.role}
                </span>
                <button
                  onClick={() => handleRemoveUser(user.user_id)}
                  className="text-gray-400 hover:text-red-600"
                  title="Удалить"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* 2. Код виджета */}
      <div className="bg-white p-6 rounded-lg shadow-md">
         <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Код виджета
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            Вставьте этот код в head или body вашего сайта,
            чтобы активировать чат-бот.
          </p>
          <div className="relative">
            <pre className="p-4 overflow-x-auto text-sm bg-gray-900 text-gray-100 rounded-md">
              <code>
                {widgetCode}
              </code>
            </pre>
            <button
              onClick={copyToClipboard}
              className="absolute top-3 right-3 flex items-center gap-1.5 px-3 py-1 text-xs font-medium bg-gray-700 text-white rounded-md hover:bg-gray-600"
            >
              {isCopied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
              {isCopied ? 'Скопировано!' : 'Копировать'}
            </button>
          </div>
      </div>

      {/* 3. Опасная зона */}
      <div className="bg-white p-6 rounded-lg shadow-md border border-red-200">
        <h2 className="text-xl font-semibold text-red-700 mb-4">
          Опасная зона
        </h2>
        <p className="text-sm text-gray-600 mb-4">
          Удаление воркспейса приведет к безвозвратному удалению
          всей базы знаний, истории чатов и аналитики.
        </p>
         <button
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md shadow-sm hover:bg-red-700"
          >
            <Trash2 className="w-5 h-5" />
            Удалить это рабочее пространство
          </button>
      </div>

      {/* Модальное окно Приглашения */}
      <Modal
        isOpen={isInviteModalOpen}
        onClose={() => setIsInviteModalOpen(false)}
        title="Пригласить пользователя"
      >
        <form onSubmit={handleInviteUser} className="space-y-4">
          <div>
            <label htmlFor="invite-email" className="block text-sm font-medium text-gray-700">
              Email пользователя
            </label>
            <input
              id="invite-email"
              type="email"
              required
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="editor@company.com"
            />
          </div>
           <div>
            <label htmlFor="invite-role" className="block text-sm font-medium text-gray-700">
              Роль
            </label>
            <select
              id="invite-role"
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              className="w-full px-3 py-2 mt-1 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="Editor">Редактор (может управлять Базой Знаний)</option>
              <option value="Admin">Администратор (может управлять всем)</option>
            </select>
          </div>
          {userError && isInviting && (
            <p className="text-sm text-red-600">{userError}</p>
          )}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={() => setIsInviteModalOpen(false)}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50"
            >
              Отмена
            </button>
            <button
              type="submit"
              disabled={isInviting}
              className="flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 disabled:opacity-50"
            >
              {isInviting ? 'Отправка...' : 'Пригласить'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};