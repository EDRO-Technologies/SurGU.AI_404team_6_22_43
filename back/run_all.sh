#!/bin/bash
#
# "Золотой Скрипт" для полного запуска бэкенда "под ключ".
# 1. Проверяет права
# 2. Проверяет наличие нужных файлов
# 3. Полностью чистит Docker и "зомби"-процессы
# 4. Генерирует poetry.lock
# 5. Запускает ollama/postgres
# 6. Выполняет "боковую загрузку" (sideloading) модели
# 7. Запускает backend/chroma
#

# --- 1. ПРОВЕРКИ ---

echo "--- 1. Проверка прав и файлов ---"

# 1.1. Проверка, что скрипт запущен от sudo
if [ "$EUID" -ne 0 ]; then
  echo "Ошибка: Пожалуйста, запустите этот скрипт с правами sudo."
  echo "Пример: sudo ./run_all.sh"
  exit 1
fi

# 1.2. Проверка .env файла
if [ ! -f .env ]; then
  echo "Ошибка: Файл .env не найден."
  echo "Пожалуйста, создай .env (можно скопировать из .env.example) перед запуском."
  exit 1
fi

# 1.3. Проверка файла модели (16ГБ)
if [ ! -f llama3-8b.gguf ]; then
  echo "Ошибка: Файл модели 'llama3-8b.gguf' не найден в этой папке."
  echo "Пожалуйста, скачай или скопируй 16ГБ F16-версию модели сюда."
  exit 1
fi

echo "Проверки пройдены."

# --- 2. ПОЛНАЯ ОЧИСТКА ---

echo "--- 2. Полная очистка системы... ---"

# 2.1. Остановка хостовой службы ollama (ГЛАВНАЯ ПРИЧИНА КОНФЛИКТОВ)
echo "Останавливаем и отключаем хост-сервис 'ollama.service', чтобы освободить порт 11434..."
systemctl stop ollama || true
systemctl disable ollama || true

# 2.2. Остановка docker-compose
docker-compose down -v

# 2.3. Пауза, чтобы ОС успела "отпустить" контейнеры
sleep 2

# 2.4. Убийство "зомби" на портах
PORTS_TO_CHECK=("5432" "11434" "8000" "8001")
for PORT in "${PORTS_TO_CHECK[@]}"; do
  PID_ON_PORT=$(lsof -t -i :$PORT || true)
  if [ -n "$PID_ON_PORT" ]; then
    echo "ВНИМАНИЕ: Найден 'зомби' процесс (PID $PID_ON_PORT) на порту $PORT. 'Убиваем'..."
    kill -9 $PID_ON_PORT
    echo "Порт $PORT освобожден."
  else
    echo "Порт $PORT свободен."
  fi
done

# 2.5. (Запасной) Остановка хостового postgresql
systemctl stop postgresql || true

echo "Очистка завершена."
sleep 1

# --- 3. ГЕНЕРАЦИЯ POETRY.LOCK ---

echo "--- 3. Генерируем poetry.lock (нужен для Dockerfile)... ---"
docker run --rm \
  -v "$(pwd)":/app \
  -w /app \
  python:3.11-slim \
  bash -c "pip install poetry && poetry lock"

if [ ! -f poetry.lock ]; then
  echo "Ошибка: Не удалось создать poetry.lock. Сборка 'backend' упадет."
  exit 1
fi
echo "poetry.lock успешно создан."

# --- 4. ЗАПУСК БД И OLLAMA ---

echo "--- 4. Запускаем ollama (на RTX 3090) и postgres... ---"
docker-compose up -d ollama postgres

echo "Пауза 10 секунд, пока сервисы стартуют..."
sleep 10

# --- 5. "БОКОВАЯ ЗАГРУЗКА" (SIDELOADING) МОДЕЛИ ---

echo "--- 5. Начинаем 'боковую загрузку' 16ГБ модели в Ollama... ---"

# 5.1. Создаем Modelfile
echo "Создаем Modelfile..."
cat <<EOT > Modelfile
# Этот файл говорит Ollama, что нужно взять локальный .gguf файл
# и зарегистрировать его под именем 'llama3:8b-instruct'
FROM /llama3-8b.gguf
EOT

# 5.2. Копируем файлы внутрь контейнера ollama
echo "Копируем 16ГБ GGUF-файл внутрь контейнера (это займет время)..."
docker-compose cp llama3-8b.gguf ollama:/llama3-8b.gguf

echo "Копируем Modelfile..."
docker-compose cp Modelfile ollama:/Modelfile

# 5.3. Создаем модель внутри ollama
echo "Импортируем модель в Ollama (команда 'create')..."
docker-compose exec ollama ollama create llama3:8b-instruct -f /Modelfile

# 5.4. Проверяем
docker-compose exec ollama ollama list | grep "llama3:8b-instruct"
if [ $? -ne 0 ]; then
  echo "Ошибка: Модель 'llama3:8b-instruct' не появилась в 'ollama list'."
  exit 1
fi
echo "Модель 16ГБ (F16) успешно импортирована в Ollama!"

# 5.5. Очистка (удаляем временные файлы из контейнера)
echo "Очищаем временные файлы из контейнера..."
docker-compose exec ollama rm /llama3-8b.gguf
docker-compose exec ollama rm /Modelfile

# --- 6. ЗАПУСК БЭКЕНДА И CHROMA ---

echo "--- 6. Запускаем backend (на RTX 3060) и chroma... ---"
# --build нужен, чтобы собрать Dockerfile v2 (с --without dev)
docker-compose up -d --build backend chroma

echo "--- 7. ВСЕ ГОТОВО! ---"
echo "Все 4 контейнера должны быть запущены."
docker-compose ps

echo -e "\n\033[0;32mБэкенд запущен! API и Swagger UI доступны по адресу:\033[0m"
echo -e "\033[1;33mhttp://$(hostname -I | awk '{print $1'}):8000/docs\033[0m"