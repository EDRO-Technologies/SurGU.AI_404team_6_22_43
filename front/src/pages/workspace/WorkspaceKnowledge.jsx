import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../../api/api';
import {
  Plus,
  Upload,
  Type,
  FileText,
  Trash2,
  Loader,
  CheckCircle,
  XCircle,
  File,
  AlertCircle
} from 'lucide-react';
import { Modal } from '../../components/Modal';

// Компонент для отображения статуса
const StatusBadge = ({ status }) => {
  if (status === 'COMPLETED') {
    return <span className="flex items-center gap-1.5 text-xs font-medium text-green-700 bg-green-100 px-2.5 py-0.5 rounded-full">
      <CheckCircle className="w-3.5 h-3.5" />
      Готово
    </span>;
  }
  if (status === 'PROCESSING') {
    return <span className="flex items-center gap-1.5 text-xs font-medium text-yellow-700 bg-yellow-100 px-2.5 py-0.5 rounded-full">
      <Loader className="w-3.5 h-3.5 animate-spin" />
      Обработка
    </span>;
  }
  if (status === 'FAILED') {
    return <span className="flex items-center gap-1.5 text-xs font-medium text-red-700 bg-red-100 px-2.5 py-0.5 rounded-full">
      <XCircle className="w-3.5 h-3.5" />
      Ошибка
    </span>;
  }
  return null;
};

// Компонент для иконки типа
const TypeIcon = ({ type }) => {
  if (type === 'FILE') return <File className="w-5 h-5 text-blue-600" />;
  if (type === 'Q&A') return <Type className="w-5 h-5 text-purple-600" />;
  if (type === 'ARTICLE') return <FileText className="w-5 h-5 text-green-600" />;
  return <File className="w-5 h-5 text-gray-500" />;
}

/**
 * Вкладка "База Знаний"
 */
export const WorkspaceKnowledge = () => {
  const { workspaceId } = useParams();
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isQAModalOpen, setIsQAModalOpen] = useState(false);

  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  const [qaQuestion, setQaQuestion] = useState('');
  const [qaAnswer, setQaAnswer] = useState('');
  const [isCreatingQA, setIsCreatingQA] = useState(false);

  useEffect(() => {
    fetchKnowledgeSources();
  }, [workspaceId]);

  // Загрузка источников
  const fetchKnowledgeSources = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get(`/workspaces/${workspaceId}/knowledge`);
      setSources(response.data);
    } catch (err) {
      console.error("Failed to fetch sources:", err);
      setError("Не удалось загрузить источники знаний.");
    } finally {
      setLoading(false);
    }
  };

  // Обработка загрузки файла
  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      await api.post(`/workspaces/${workspaceId}/knowledge/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      // API возвращает 202, обработка в фоне.
      // Добавляем "ожидающий" источник в список.
      const pseudoSource = {
        id: `temp-${Date.now()}`,
        name: selectedFile.name,
        type: 'FILE',
        status: 'PROCESSING'
      };
      setSources([pseudoSource, ...sources]);
      setIsUploadModalOpen(false);
      setSelectedFile(null);

      // Пере-запрашиваем через 5 секунд, чтобы обновить статус
      setTimeout(fetchKnowledgeSources, 5000);

    } catch (err) {
      console.error("File upload failed:", err);
      setError("Ошибка при загрузке файла.");
    } finally {
      setIsUploading(false);
    }
  };

  // Обработка создания Q&A
  const handleQASubmit = async (e) => {
    e.preventDefault();
    setIsCreatingQA(true);
    setError(null);
    try {
      await api.post(`/workspaces/${workspaceId}/knowledge/qa`, {
        question: qaQuestion,
        answer: qaAnswer
      });
      setIsQAModalOpen(false);
      setQaQuestion('');
      setQaAnswer('');
      // Пере-запрашиваем, чтобы обновить список
      setTimeout(fetchKnowledgeSources, 2000); // Даем время на индексацию (имитация)
    } catch(err) {
       console.error("QA creation failed:", err);
      setError("Ошибка при создании Q&A.");
    } finally {
      setIsCreatingQA(false);
    }
  }

  // Удаление источника
  const handleDeleteSource = async (sourceId) => {
    if (!window.confirm("Вы уверены, что хотите удалить этот источник? Это действие необратимо.")) {
      return;
    }

    try {
      await api.delete(`/workspaces/${workspaceId}/knowledge/${sourceId}`);
      // Удаляем из списка в UI
      setSources(sources.filter(s => s.id !== sourceId));
    } catch (err) {
      console.error("Delete failed:", err);
      alert("Не удалось удалить источник.");
    }
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold text-gray-900">
          База знаний
        </h2>
        <div className="flex gap-3">
          <button
            onClick={() => setIsQAModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-md shadow-sm hover:bg-purple-700"
          >
            <Type className="w-5 h-5" />
            Добавить Q&A
          </button>
          <button
            onClick={() => setIsUploadModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md shadow-sm hover:bg-indigo-700"
          >
            <Upload className="w-5 h-5" />
            Загрузить файл
          </button>
        </div>
      </div>

      {loading && <p>Загрузка...</p>}
      {error && !loading && (
        <p className="text-center text-red-600 bg-red-100 p-4 rounded-md">{error}</p>
      )}

      {/* Список источников */}
      {!loading && !error && (
        <div className="flow-root">
          <ul role="list" className="divide-y divide-gray-200">
            {sources.map((source) => (
              <li key={source.id} className="flex items-center justify-between py-4 gap-4">
                <div className="flex items-center min-w-0 gap-3">
                  <TypeIcon type={source.type} />
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {source.name}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <StatusBadge status={source.status} />
                  <button
                    onClick={() => handleDeleteSource(source.id)}
                    className="text-gray-400 hover:text-red-600"
                    title="Удалить"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </li>
            ))}
          </ul>
           {sources.length === 0 && (
             <p className="text-center text-gray-500 py-10">
               База знаний пуста. Загрузите файлы или добавьте Q&A.
             </p>
           )}
        </div>
      )}

      {/* Модальное окно загрузки файла */}
      <Modal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        title="Загрузить файл"
      >
        <form onSubmit={handleFileUpload} className="space-y-4">
           <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Выберите файл (PDF, DOCX, TXT)
            </label>
            <input
              type="file"
              onChange={(e) => setSelectedFile(e.target.files[0])}
              accept=".pdf,.docx,.txt"
              className="block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-full file:border-0
                file:text-sm file:font-semibold
                file:bg-indigo-50 file:text-indigo-700
                hover:file:bg-indigo-100"
            />
          </div>
          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={() => setIsUploadModalOpen(false)}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50"
            >
              Отмена
            </button>
            <button
              type="submit"
              disabled={isUploading || !selectedFile}
              className="flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 disabled:opacity-50"
            >
              {isUploading ? <Loader className="w-5 h-5 mr-2 animate-spin" /> : <Upload className="w-5 h-5 mr-2" />}
              {isUploading ? 'Загрузка...' : 'Загрузить'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Модальное окно Q&A */}
      <Modal
        isOpen={isQAModalOpen}
        onClose={() => setIsQAModalOpen(false)}
        title="Добавить Q&A"
      >
        <form onSubmit={handleQASubmit} className="space-y-4">
          <div>
            <label htmlFor="qa-q" className="block text-sm font-medium text-gray-700">
              Вопрос
            </label>
            <textarea
              id="qa-q"
              rows="2"
              required
              value={qaQuestion}
              onChange={(e) => setQaQuestion(e.target.value)}
              className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="За сколько дней подавать на отпуск?"
            ></textarea>
          </div>
          <div>
            <label htmlFor="qa-a" className="block text-sm font-medium text-gray-700">
              Эталонный ответ
            </label>
            <textarea
              id="qa-a"
              rows="4"
              required
              value={qaAnswer}
              onChange={(e) => setQaAnswer(e.target.value)}
              className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Заявление на отпуск необходимо подавать за 2 недели."
            ></textarea>
          </div>
           {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}
          <div className="flex justify-end gap-3 pt-4">
             <button
              type="button"
              onClick={() => setIsQAModalOpen(false)}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50"
            >
              Отмена
            </button>
            <button
              type="submit"
              disabled={isCreatingQA}
              className="flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-purple-600 border border-transparent rounded-md shadow-sm hover:bg-purple-700 disabled:opacity-50"
            >
              {isCreatingQA ? 'Добавление...' : 'Добавить'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};