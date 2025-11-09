import axios from 'axios';

// Создаем экземпляр axios
const api = axios.create({
  // Базовый URL для всех запросов
  // В production это будет /api/v1 (обрабатывается Nginx)
  // В dev это /api/v1 (обрабатывается Vite proxy)
  baseURL: '/api/v1',
});

// --- Interceptor (Перехватчик) ---
// Этот interceptor будет автоматически добавлять
// JWT токен в заголовок Authorization для каждого запроса,
// если токен существует в localStorage.

api.interceptors.request.use(
  (config) => {
    // Получаем токен из localStorage
    const token = localStorage.getItem('access_token');

    // Если токен есть, добавляем его в заголовки
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    // Обрабатываем ошибку запроса
    return Promise.reject(error);
  }
);

// --- Обработка 401 (Unauthorized) ---
// Если API возвращает 401, это значит, что токен истек
// или невалиден. Мы "разлогиниваем" пользователя.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Очищаем localStorage
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      // Перезагружаем страницу (чтобы React-роутер перекинул на /login)
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);


export default api;