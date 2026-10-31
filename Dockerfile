# Python уже включён в образ, отдельно устанавливать его через Ubuntu не нужно.
FROM python:3.12-slim

# Не создаём pyc-файлы; вывод сразу попадает в журнал контейнера.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Все следующие команды выполняются из /app внутри контейнера.
WORKDIR /app

# Зависимости копируем отдельно, чтобы использовать кеш при изменении кода.
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# Копируем проект, кроме файлов, перечисленных в .dockerignore.
COPY . .

# Документируем порт Django внутри контейнера.
EXPOSE 8000

# 0.0.0.0 позволяет открыть сервер с компьютера через проброшенный порт.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
