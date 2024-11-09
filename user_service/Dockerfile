    # Базовый образ Python
FROM python:3.9

# Установка рабочей директории
WORKDIR /app

# Копирование файлов приложения
COPY main.py .
COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
        pkg-config default-libmysqlclient-dev build-essential python3-dev bash
# Установка зависимостей
RUN pip install -r requirements.txt

# Запуск приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
