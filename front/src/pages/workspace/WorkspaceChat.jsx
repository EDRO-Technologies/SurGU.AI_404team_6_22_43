import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import api from '../../api/api';
import { v4 as uuidv4 } from 'uuid';
import { Send, User, Brain, Loader, Paperclip } from 'lucide-react';

/**
 * Вкладка "Тест чата"
 */
export const WorkspaceChat = () => {
  const { workspaceId } = useParams();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Генерируем ID сессии чата один раз при загрузке
  const [sessionId] = useState(uuidv4());

  const messagesEndRef = useRef(null);

  // Прокрутка вниз при новом сообщении
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = {
      sender: 'user',
      text: input,
    };

    setMessages([...messages, userMessage]);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const response = await api.post(`/workspaces/${workspaceId}/query`, {
        question: input,
        session_id: sessionId,
      });

      const aiMessage = {
        sender: 'ai',
        text: response.data.answer,
        sources: response.data.sources,
        ticket_id: response.data.ticket_id,
      };
      setMessages((prev) => [...prev, aiMessage]);

    } catch (err) {
      console.error("Chat query failed:", err);
      setError("Ошибка при отправке запроса. Попробуйте снова.");
      const errorMessage = {
        sender: 'ai',
        text: "Извините, произошла ошибка при обработке вашего запроса.",
        sources: [],
        error: true
      }
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md flex flex-col" style={{height: '70vh'}}>
      {/* Область сообщений */}
      <div className="flex-1 p-4 space-y-4 overflow-y-auto">
        {messages.map((msg, index) => (
          <div key={index} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex gap-3 max-w-lg ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${msg.sender === 'user' ? 'bg-indigo-500' : 'bg-gray-700'}`}>
                {msg.sender === 'user' ? (
                  <User className="w-5 h-5 text-white" />
                ) : (
                  <Brain className="w-5 h-5 text-white" />
                )}
              </div>
              <div className={`p-3 rounded-lg ${msg.sender === 'user' ? 'bg-indigo-50 text-gray-800' : 'bg-gray-100 text-gray-800'}`}>
                <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
                {/* Отображение источников */}
                {msg.sender === 'ai' && msg.sources && msg.sources.length > 0 && (
                  <div className="mt-3 border-t border-gray-200 pt-2">
                    <h4 className="text-xs font-semibold text-gray-600 mb-1.5">Источники:</h4>
                    <div className="flex flex-col gap-2">
                      {msg.sources.map((source, i) => (
                        <div key={i} className="p-2 text-xs bg-white rounded-md border border-gray-200">
                          <p className="font-medium text-gray-700 truncate">
                            <Paperclip className="w-3 h-3 inline-block mr-1.5" />
                            {source.name} (стр. {source.page || 'N/A'})
                          </p>
                          <p className="mt-1 text-gray-500 line-clamp-2">
                            "...{source.text_chunk}..."
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                 {/* Если создан тикет */}
                 {msg.sender === 'ai' && msg.ticket_id && (
                   <p className="mt-2 text-xs font-medium text-yellow-700">
                     (Создан тикет для администратора: {msg.ticket_id.slice(0, 8)}...)
                   </p>
                 )}
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="flex gap-3 max-w-lg">
              <div className="flex-shrink-0 w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center">
                 <Brain className="w-5 h-5 text-white" />
              </div>
              <div className="p-3 bg-gray-100 rounded-lg">
                <Loader className="w-5 h-5 text-gray-500 animate-spin" />
              </div>
            </div>
          </div>
        )}
        {/* Пустышка для прокрутки */}
        <div ref={messagesEndRef} />
      </div>

      {/* Форма ввода */}
      <div className="p-4 border-t border-gray-200 bg-white rounded-b-lg">
        <form onSubmit={handleSubmit} className="flex items-center gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            className="flex-1 w-full px-4 py-2 text-sm border border-gray-300 rounded-full shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="Спросите что-нибудь..."
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="flex items-center justify-center w-10 h-10 text-white bg-indigo-600 rounded-full shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
         {error && (
            <p className="mt-2 text-xs text-red-600">{error}</p>
          )}
      </div>
    </div>
  );
};