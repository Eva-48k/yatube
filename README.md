[![Built with Django](https://img.shields.io/badge/Built_with-Django-32CD32.svg)](https://www.djangoproject.com/)
[![Built with Django REST framework](https://img.shields.io/badge/Built_with-Django_REST_framework-green.svg)](https://www.django-rest-framework.org/)

## Yatube

**Yatube** - это cоциальная сеть блогеров. Пользователь может создать собственную страницу для публикации записей, а также заходить на страницы других пользователей, подписываться на авторов и комментировать их записи. Проект содержит REST API.

### Как запустить проект:

1. Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:Eva-48k/yatube.git
```

```
cd yatube
```

2. Cоздать и активировать виртуальное окружение:

```
python -m venv env
```

```
venv/scripts/activate
```

3. Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

4. Выполнить миграции:

```
python manage.py makemigrations
python manage.py migrate
```

5. Запустить проект:

```
python manage.py runserver
```

**Документация к API** после запуска проекта доступна по ссылке: http://127.0.0.1:8000/redoc/
