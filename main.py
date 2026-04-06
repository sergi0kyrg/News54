import os
import subprocess

# Порт для запуска (Replit автоматически передает PORT)
port = os.environ.get("PORT", "8000")

# Команда запуска Django проекта
command = (
    "python manage.py migrate && "
    "python manage.py collectstatic --noinput && "
    f"gunicorn news_aggregator.wsgi:application --bind 0.0.0.0:{port}"
)

# Запуск команды
subprocess.run(command, shell=True, check=True)