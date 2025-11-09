import React, { createContext, useState, useEffect } from 'react';
import api from '../api/api';

// Создаем контекст
export const AuthContext = createContext(null);

/**
 * Провайдер аутентификации
 * Управляет состоянием 'user' и 'token'
 */
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // Для проверки токена при запуске

  // При монтировании компонента, проверяем наличие токена
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      // Если токен есть, пробуем получить данные о пользователе
      api.get('/auth/me')
        .then(response => {
          // Сохраняем пользователя в state
          setUser(response.data);
          localStorage.setItem('user', JSON.stringify(response.data));
        })
        .catch(() => {
          // Если токен невалиден, очищаем
          localStorage.removeItem('access_token');
          localStorage.removeItem('user');
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  // Функция для входа
  const login = async (email, password) => {
    try {
      const response = await api.post('/auth/login', { email, password });
      const { access_token, user } = response.data;

      // Сохраняем в localStorage
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify(user));

      // Обновляем state
      setUser(user);
    } catch (error) {
      // Пробрасываем ошибку дальше, чтобы LoginPage мог ее поймать
      throw error;
    }
  };

  // Функция для выхода
  const logout = () => {
    // Очищаем localStorage
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    // Очищаем state
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};