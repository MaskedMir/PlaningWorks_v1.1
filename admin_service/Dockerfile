# Используем базовый образ Python
FROM python:3.9

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы приложения
COPY database.py .
COPY main.py .
COPY models.py .
COPY schemas.py .
COPY statistics_collection_service.py .

# Запускаем FastAPI приложение с помощью uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
