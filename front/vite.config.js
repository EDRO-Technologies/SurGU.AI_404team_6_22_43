import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Запускаем dev-сервер на порту 3000
    port: 3000,
    // Настройка прокси для локальной разработки
    // (когда вы запускаете 'npm run dev')
    proxy: {
      // Все запросы к /api/v1/...
      '/api/v1': {
        // ...будут перенаправлены на ваш бэкенд,
        // запущенный на localhost:8000
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})