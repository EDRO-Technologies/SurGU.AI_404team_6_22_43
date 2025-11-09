# (НОВЫЙ ФАЙЛ)
# Dockerfile для 'back-ai'. Копия оригинального Dockerfile из 'back' v1.
# Ему нужен PyTorch и GPU
FROM python:3.11-slim

RUN pip install --upgrade pip setuptools wheel

# --- ИСПРАВЛЕНИЕ: Добавляем 'wget' для скачивания wait-for-it ---
RUN apt-get update && apt-get install -y build-essential wget && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

# --- ИСПРАВЛЕНИЕ: Скачиваем и делаем исполняемым скрипт wait-for-it ---
RUN wget -O /usr/local/bin/wait-for-it.sh https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh
RUN chmod +x /usr/local/bin/wait-for-it.sh
# --- Конец ИСПРАВЛЕНИЯ ---

# (ВАЖНО) Устанавливаем PyTorch с поддержкой CUDA 12.1
# (Взят из оригинального Dockerfile v1)
# (ИСПРАВЛЕНИЕ v1) Используем CPU-версию для совместимости
RUN pip install torch torchvision torchaudio

WORKDIR /app

COPY ./all-MiniLM-L6-v2 /app/all-MiniLM-L6-v2

COPY pyproject.toml ./

# Устанавливаем AI-зависимости
RUN poetry config virtualenvs.create false && poetry install --no-root --without dev --no-interaction

COPY ./app /app/app

# Этот сервис слушает порт 8001
EXPOSE 8001

# --- ИСПРАВЛЕНИЕ: Используем wait-for-it.sh перед запуском uvicorn ---
# Мы ждем 60 секунд, пока хост 'chroma' (имя сервиса из docker-compose)
# не начнет отвечать на порту 8000 (внутренний порт chroma).
# Только после этого запускаем uvicorn.
CMD ["sh", "-c", "wait-for-it.sh chroma:8000 --timeout=60 --strict -- echo 'ChromaDB is up! Starting AI service...' && poetry run uvicorn app.main:app --host 0.0.0.0 --port 8001"]