# VPN Panel — CLAUDE.md

## Обзор проекта
FastAPI-панель для управления VPN-серверами (Happ/V2Ray/Xray).
Администратор добавляет серверы вручную или импортирует из внешних подписок, управляет их статусом.
Клиенты (приложение Happ) подключаются к `/sub` для получения списка серверов.

## Tech Stack
- **Backend**: FastAPI + SQLAlchemy (sync) + SQLite
- **Frontend**: Jinja2 + Bootstrap 5 + Bootstrap Icons
- **Auth**: Cookie-сессия (itsdangerous) через SessionMiddleware
- **HTTP client**: httpx (для загрузки внешних подписок)
- **Deploy**: Docker + Docker Compose + Nginx

## Запуск

```bash
# Локально
uvicorn app.main:app --reload

# Docker
docker compose up --build
```

База данных: `./data/vpn_configs.db` (персистентный volume в Docker).

## Структура файлов

```
app/
  api/
    admin.py          # Все admin-роуты + auth (cookie-сессия)
    subscription.py   # GET /sub — endpoint для Happ-клиентов
  core/
    database.py       # SQLAlchemy engine, SessionLocal, get_db
  domain/
    models.py         # ORM-модели: VpnConfig, SubscriptionSettings, ExternalSubscription, ExternalConfig
    schemas.py        # Pydantic-схемы
  repository/
    vpn_repository.py           # CRUD для VpnConfig и SubscriptionSettings
    external_vpn_repository.py  # CRUD для ExternalSubscription и ExternalConfig
  services/
    vpn_service.py           # Бизнес-логика: generate_subscription объединяет все активные конфиги
    external_vpn_service.py  # Загрузка и парсинг внешних подписок
  templates/
    login.html   # Страница входа
    admin.html   # Админ-панель
  main.py        # FastAPI app + SessionMiddleware + роутеры
```

## Аутентификация
- Учётные данные задаются в `.env`: `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `SECRET_KEY`
- `GET /login` — форма входа
- `POST /login` — проверка, установка cookie-сессии
- `GET /logout` — выход, очистка сессии
- Все `/admin/*` роуты защищены dependency `get_current_user` (редирект на `/login` если нет сессии)

## Happ API — формат ответа подписки

Endpoint `GET /sub` должен возвращать:

### HTTP-заголовки (обязательно для Happ):
```
profile-title: <название подписки>
support-url: <ссылка поддержки / Telegram>
profile-update-interval: 12
content-type: text/plain; charset=utf-8
```

### Тело ответа:
Base64-кодированный список конфигов, по одному на строку:
```
vless://...#Название сервера
vmess://...#Название сервера
trojan://...#Название сервера
```

### Поддерживаемые протоколы:
`vless://`, `vmess://`, `trojan://`, `ss://`, `hysteria2://`, `hy2://`, `tuic://`

### Фрагмент (#) в ссылке = отображаемое имя сервера в Happ.

## Внешние подписки

### Поток:
1. Admin вставляет URL подписки → `POST /admin/external-subs/fetch` → список конфигов (JSON, без сохранения)
2. Admin редактирует имена, выбирает нужные → `POST /admin/external-subs/save`
3. Сохранённые конфиги попадают в таблицу `external_configs`
4. Активные external configs включаются в `/sub` вместе с ручными

### Парсинг подписок:
- Сначала проверяется plain-текст (ссылки по одной на строку)
- Потом попытка base64 decode
- Из фрагмента `#` извлекается имя сервера

## Модели БД

| Таблица | Поля |
|---------|------|
| `vpn_configs` | id, name, config_url, is_active |
| `subscription_settings` | id (singleton), sub_name, sub_description |
| `external_subscriptions` | id, name, url, created_at |
| `external_configs` | id, subscription_id (FK), name, raw_link, is_active |

## Важные замечания
- `SubscriptionSettings` — singleton (всегда один ряд с id=1)
- `generate_subscription()` объединяет `vpn_configs` + `external_configs` (оба фильтруются по `is_active=True`)
- Заголовок `#` в ссылке определяет отображаемое имя в Happ — всегда включать его
- При URL-encode в фрагменте: `urllib.parse.unquote()` для декодирования имени
