# Используем официальный легкий образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir python-multipart

# Копируем весь наш код в контейнер
COPY ./app ./app

# Указываем команду для запуска (host 0.0.0.0 нужен, чтобы Docker выпустил трафик наружу)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]