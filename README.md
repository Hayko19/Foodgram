# Foodgram

**Foodgram** — это онлайн-сервис для публикации, поиска и хранения кулинарных рецептов. Пользователи могут создавать рецепты, добавлять их в избранное, формировать список покупок и подписываться на других авторов.

## Ссылка на работающий сайт
https://foodgram-online.zapto.org

## Стек 

- Python 3.9
- Django, Django REST Framework
- Djoser (авторизация)
- PostgreSQL (или SQLite для локального запуска)
- Docker, Docker Compose
- Nginx
- React (frontend)
- Gunicorn

## CI/CD

Проект использует GitHub Actions для автоматизации тестирования и деплоя.  
Основные этапы:
- Сборка и публикация Docker-образов.
- Автоматический деплой на сервер с помощью Docker Compose.

Файл workflow: [.github/workflows/](.github/workflows/)

## Быстрый старт (локально, через Docker)

### 1. Клонирование репозитория

```sh
git clone git@github.com:Hayko19/foodgram.git
```

### 2. Перейти в папку с docker-compose.yml

```sh
cd foodgram
```

### 3. Создать файл .env

Создайте файл `.env` в папке `foodgram/` на основе примера ниже:

```env
# example.env
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=your_db
DB_NAME=your_postgres_name
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=localhost,127.0.0.1
DEBUG=True
```

### 4. Запуск контейнеров

```sh
docker-compose up -d --build
```

### 5. Подготовка базы данных

```sh
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

### 6. Сборка статики

```sh
docker-compose exec backend python manage.py collectstatic --noinput
```

### 7. Доступ к сайту

- Frontend: http://localhost/
- Админка: http://localhost/admin/

## Примеры запросов

- Получить список рецептов:
  ```
  GET /api/recipes/
  ```
- Добавить рецепт в избранное:
  ```
  POST /api/recipes/{id}/favorite/
  ```
- Скачать список покупок:
  ```
  GET /api/recipes/download_shopping_cart/
  ```

## Используемые библиотеки

- Django, djangorestframework, djoser
- Pillow
- psycopg2-binary
- gunicorn
- React, react-router-dom, react-meta-tags

## Документация API

Swagger/OpenAPI: `/api/docs/`  
ReDoc: [`docs/redoc.html`](docs/redoc.html)

---

**Путь к репозиторию:**  
https://github.com/Hayko19/foodgram#
