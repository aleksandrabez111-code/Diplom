# Дипломный проект: страница приема заявок + панель обработки

Проект состоит из backend на FastAPI, страницы приема заявок и внутренней HTML-панели без сборки. Его можно запустить одним файлом из корня проекта.

## Быстрый запуск на Windows

Откройте консоль в папке проекта и выполните:

```powershell
.\start_app.ps1
```

Также можно запустить файл `start_app.bat` двойным кликом.

Скрипт сам:

- создаст `.env`, если его нет;
- создаст виртуальное окружение для backend;
- установит зависимости;
- применит миграции базы;
- добавит демо-данные;
- запустит backend, панель сотрудников и страницу приема заявок.

После запуска:

- Backend: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Панель администратора и специалиста: `http://localhost:5500/frontend/panel.html`
- Страница приема заявок: `http://localhost:5500/frontend/embed-widget-snippet.html`

Если порты `8000` или `5500` уже заняты, скрипт автоматически выберет ближайшие свободные порты, например `8001` и `5501`. В этом случае используйте адреса, которые напечатаны в консоли после запуска.

Если открыть адрес backend, который напечатан в консоли, отображается стартовая страница со ссылками на Swagger, панель и страницу приема заявок. Сами пользовательские страницы открываются через локальный HTML-сервер на порту, который также указан в консоли.

## Демо-доступы

- Администратор: `admin / admin12345`
- Специалист: `spec1 / spec12345`
- Специалист: `spec2 / spec12345`

## Письма при закрытии заявок

Когда заявка закрывается, backend формирует стандартное письмо клиенту. Для реальной отправки заполните SMTP-поля в `.env` или `backend/.env`:

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-login
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=support@example.com
SMTP_FROM_NAME=Служба поддержки
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

Если SMTP не настроен, письмо сохраняется как `.eml` в `backend/data/outbox`, чтобы его можно было проверить во время демонстрации.

## Что внутри

- `backend` - API на FastAPI, база SQLite, миграции Alembic, JWT-авторизация.
- `frontend/panel.html` - панель администратора и специалиста для заявок, тем и пользователей.
- `frontend/embed-widget-snippet.html` - страница приема заявок с HTML-виджетом обращения.
- `frontend/assets/logo.jpg` - логотип на странице приема заявок.
- `start_app.ps1` и `start_app.bat` - простой запуск проекта.

## Основные возможности API

Публичная часть:

- `GET /api/public/topics` - список активных тем.
- `POST /api/public/tickets` - создание заявки из виджета.

Внутренняя часть:

- `POST /api/auth/login` - вход.
- `GET /api/auth/me` - текущий пользователь.
- `GET /api/tickets` - список заявок.
- `POST /api/tickets/{id}/take` - взять заявку специалистом.
- `POST /api/tickets/{id}/status` - сменить статус.
- `GET /api/topics`, `POST /api/topics`, `PATCH /api/topics/{id}`, `DELETE /api/topics/{id}` - темы, активность и назначение одного или нескольких специалистов.
- `GET /api/users`, `POST /api/users`, `PATCH /api/users/{id}` - пользователи.

## Запуск через Docker

```powershell
docker compose up --build
```

Docker запускает backend на `http://localhost:8000`. Панель и страницу приема заявок удобнее открывать через `start_app.ps1`, потому что он дополнительно запускает локальный HTML-сервер на `http://localhost:5500`.

## Запуск backend вручную

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
