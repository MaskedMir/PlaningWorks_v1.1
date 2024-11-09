# Базовый образ Python
FROM python:3.9

# Установка рабочей директории
WORKDIR /app

# Копирование файлов приложения
COPY main.py .
COPY requirements.txt .


# Установка зависимостей
RUN pip install -r requirements.txt

# Запуск приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
