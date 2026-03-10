FROM python:3.12-slim

WORKDIR /app

# Зависимости отдельным слоем — кэшируются если requirements не менялся
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Миграции + запуск
CMD alembic upgrade head && python run.py