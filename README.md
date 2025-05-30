
# 📝 ApplicantForm

**ApplicantForm** — это Django-приложение для создания, редактирования и отправки динамических форм. Включает административную панель для просмотра заявок и управление формами.

## 🚀 Быстрый запуск

Убедитесь, что у вас установлен [**uv**](https://github.com/astral-sh/uv) и Python 3.12.

### 1. Клонируйте проект:

```bash
git clone <URL-репозитория>
cd ApplicantForm/src
```

### 2. Установите зависимости:

```bash
uv venv
source .venv/bin/activate
uv sync
```

### 3. Примените миграции и создайте суперпользователя:

```bash
uv run manage.py migrate
uv run manage.py createsuperuser
```

### 4. Запустите сервер:

```bash
uv run manage.py runserver
```

Приложение будет доступно по адресу: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🗂️ Архитектура проекта

```
src/
├── config/                  # Конфигурация Django (settings, urls, wsgi/asgi)
├── form/                    # Основное приложение
│   ├── models.py            # Модели для форм, заявок и значений полей
│   ├── views.py             # Обработчики представлений
│   ├── urls.py              # URL-маршруты
│   ├── admin.py             # Админ-панель
│   ├── templates/           # Шаблоны HTML
│   ├── static/              # Статика (CSS и др.)
│   └── migrations/          # Миграции базы данных
├── uploads/                 # Загруженные пользователями файлы
├── manage.py                # Скрипт управления Django
└── db.sqlite3               # SQLite база данных (для разработки)
```

---

## 🌿 Работа с Git

### Создание новой ветки:

```bash
git checkout -b имя-ветки
```

### Сохранение изменений:

```bash
git add .
git commit -m "Краткое описание изменений"
```

### Отправка ветки:

```bash
git push origin имя-ветки
```

Затем создайте Pull Request через интерфейс GitHub или GitLab для слияния изменений.

---
