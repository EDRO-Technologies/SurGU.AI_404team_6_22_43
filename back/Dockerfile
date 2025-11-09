# Dockerfile для 'back'
# УДАЛЕНА установка PyTorch, т.к. AI-логика переехала

FROM python:3.11-slim

RUN pip install --upgrade pip setuptools wheel

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

# --- УДАЛЕНО ---
# Установка PyTorch больше не нужна
# RUN pip install torch torchvision torchaudio
# --- КОНЕЦ УДАЛЕНИЯ ---

WORKDIR /app

COPY pyproject.toml ./

# Устанавливаем зависимости (без AI-библиотек)
RUN poetry config virtualenvs.create false && poetry install --no-root --without dev --no-interaction

COPY ./app /app/app

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]