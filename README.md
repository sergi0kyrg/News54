# News54

News54 — автоматический агрегатор новостей по Новосибирску и Новосибирской области.

## Что есть в проекте
- автоматический сбор новостей из RSS-источников;
- фильтрация по категориям и источникам;
- поиск и сортировка;
- современный адаптивный интерфейс;
- светлая и тёмная тема с сохранением выбора пользователя;
- подготовка к публикации онлайн на Render;
- blueprint `render.yaml` для веб-сервиса, PostgreSQL и cron-задачи обновления новостей.

## Локальный запуск
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_sources
python manage.py fetch_news
python manage.py runserver
```

## Публикация онлайн на Render
1. Создай новый репозиторий на GitHub и загрузи туда содержимое проекта.
2. На Render выбери **New → Blueprint** и подключи репозиторий.
3. Render прочитает `render.yaml` и предложит создать:
   - web service `news54-web`;
   - PostgreSQL `news54-db`;
   - cron job `news54-fetcher`.
4. После первого деплоя открой Shell у web service и выполни:
   ```bash
   python manage.py createsuperuser
   python manage.py fetch_news
   ```
5. После этого сайт станет доступен по публичному адресу `https://<имя-сервиса>.onrender.com`.

## Как работает автообновление
В `render.yaml` уже добавлена cron-задача:
```yaml
schedule: "*/30 * * * *"
```
Она запускает:
```bash
python manage.py fetch_news
```
То есть новости будут автоматически обновляться каждые 30 минут.

## Важные замечания
- у Render бесплатные web services и Postgres доступны, но cron jobs не относятся к free-типу;
- если не нужен платный cron job, обновление можно запускать вручную или через планировщик задач Windows;
- при переносе на другой хостинг нужно обновить `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS`.
