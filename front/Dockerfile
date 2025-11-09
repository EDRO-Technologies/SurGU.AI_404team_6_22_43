# --- ЭТАП 1: Сборка React-приложения ---
# Используем Node.js 20-alpine как базовый образ для сборки
FROM node:20-alpine AS build

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем package.json
COPY package.json ./

# Устанавливаем зависимости
RUN npm install

# Копируем остальной код фронтенда
COPY . .

# --- ИСПРАВЛЕНИЕ ---
# Vite ожидает, что index.html будет в корне (/app),
# а не в /app/public.
# Перемещаем его в корень перед сборкой.
RUN mv /app/public/index.html /app/index.html

# Собираем production-билд
# Это создаст папку /app/dist
RUN npm run build

# --- ЭТАП 2: Обслуживание (Serve) через Nginx ---
# Используем легкий образ Nginx
FROM nginx:1.27-alpine

# Копируем production-билд из этапа "build" в директорию Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Копируем кастомную конфигурацию Nginx
# Эта конфигурация настроит прокси для API
COPY nginx.conf /etc/nginx/nginx.conf

# Открываем порт 80 (стандартный порт Nginx)
EXPOSE 80

# Команда для запуска Nginx
CMD ["nginx", "-g", "daemon off;"]