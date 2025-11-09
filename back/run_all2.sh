#!/bin/bash
#
# "Золотой Скрипт" для полного запуска бэкенда "под ключ".
# 1. Проверяет права
# 2. Проверяет наличие нужных файлов
# 3. Полностью чистит Docker и "зомби"-процессы
# 4. (Пропускаем) Генерирует poetry.lock
# 5. Запускает ollama/postgres
# 6. Выполняет "боковую загрузку" (sideloading) модели
# 7. Запускает backend/chroma
#

# --- 1. ПРОВЕРКИ ---

echo "--- 1. Проверка прав и файлов ---"
# ... existing code ...
if [ ! -f llama3-8b.gguf ]; then
  echo "Ошибка: Файл модели 'llama3-8b.gguf' не найден в этой папке."
# ... existing code ...
  exit 1
fi

# --- Добавлена проверка Modelfile ---
if [ ! -f Modelfile ]; then
  echo "Ошибка: Файл 'Modelfile' не найден."
  echo "Пожалуйста, создай Modelfile перед запуском."
  exit 1
fi

echo "Проверки пройдены."
# ... existing code ...
systemctl stop postgresql || true

echo "Очистка завершена."
sleep 1

# --- 3. ГЕНЕРАЦИЯ POETRY.LOCK (ПРОПУЩЕНО) ---

# echo "--- 3. Генерируем poetry.lock (нужен для Dockerfile)... ---"
# docker run --rm \
#   -v "$(pwd)":/app \
#   -w /app \
#   python:3.11-slim \
#   bash -c "pip install poetry && poetry lock"
#
# if [ ! -f poetry.lock ]; then
#   echo "Ошибка: Не удалось создать poetry.lock. Сборка 'backend' упадет."
#   exit 1
# fi
# echo "poetry.lock успешно создан."

echo "--- 3. Пропускаем генерацию poetry.lock (предполагаем, что он существует) ---"


# --- 4. ЗАПУСК БД И OLLAMA ---
# ... existing code ...
echo "Пауза 10 секунд, пока сервисы стартуют..."
sleep 10

# --- 5. "БОКОВАЯ ЗАГРУЗКА" (SIDELOADING) МОДЕЛИ ---

echo "--- 5. Начинаем 'боковую загрузку' 16ГБ модели в Ollama... ---"

# 5.1. Создаем Modelfile (ПРОПУЩЕНО)
# echo "Создаем Modelfile..."
# cat <<EOT > Modelfile
# # Этот файл говорит Ollama, что нужно взять локальный .gguf файл
# # и зарегистрировать его под именем 'llama3:8b-instruct'
# FROM /llama3-8b.gguf
# EOT
echo "--- 5.1. Пропускаем создание Modelfile (предполагаем, что он существует) ---"


# 5.2. Копируем файлы внутрь контейнера ollama
echo "Копируем 16ГБ GGUF-файл внутрь контейнера (это займет время)..."
# ... existing code ...
docker-compose cp Modelfile ollama:/Modelfile

# 5.3. Создаем модель внутри ollama
# ... existing code ...