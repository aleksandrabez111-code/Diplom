from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, public, tickets, topics, users
from app.core.config import settings

app = FastAPI(title=settings.app_name, version='2.0.0')

if settings.cors_origins_list == ['*']:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=False,
        allow_methods=['*'],
        allow_headers=['*'],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

app.include_router(public.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(topics.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(tickets.router, prefix=settings.api_prefix)


@app.get('/', response_class=HTMLResponse)
def root() -> str:
    return """
    <!doctype html>
    <html lang="ru">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Панель заявок</title>
        <style>
          body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f3f7fb;
            color: #07192f;
          }
          main {
            max-width: 860px;
            margin: 64px auto;
            padding: 0 24px;
          }
          h1 {
            margin: 0 0 12px;
            font-size: 36px;
          }
          p {
            margin: 0 0 28px;
            color: #607087;
            font-size: 18px;
          }
          .links {
            display: grid;
            gap: 14px;
          }
          a {
            display: block;
            padding: 18px 20px;
            border: 1px solid #d5dde8;
            border-radius: 10px;
            background: #fff;
            color: #07192f;
            text-decoration: none;
            font-weight: 700;
          }
          span {
            display: block;
            margin-top: 6px;
            color: #607087;
            font-size: 14px;
            font-weight: 400;
          }
        </style>
      </head>
      <body>
        <main>
          <h1>Панель заявок</h1>
          <p>Backend FastAPI запущен. Откройте нужный раздел по ссылке ниже.</p>
          <div class="links">
            <a href="/docs">Swagger UI <span>Документация и проверка маршрутов API</span></a>
            <a href="http://localhost:5500/frontend/panel.html">Панель администратора и специалиста <span>Работа с заявками, темами и пользователями</span></a>
            <a href="http://localhost:5500/frontend/embed-widget-snippet.html">Страница приема заявок <span>Публичный виджет для подачи обращения</span></a>
          </div>
        </main>
      </body>
    </html>
    """
