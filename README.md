## Лабораторная работа №2: Создание справочника

Выполнил Олешко В.Ю., 4гр

http://dranikpg.com:8000

### Детали реализации

#### БД

В качестве БД используется SQLite, сохраняющая данные в локальном файле. Данные хранятся в двух таблицах:

```sql

CREATE TABLE IF NOT EXISTS airlines (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    foundation_date TEXT,
    country TEXT
)

CREATE TABLE IF NOT EXISTS airplanes (
    id INTEGER PRIMARY KEY,
    call_sign TEXT NOT NULL,
    model TEXT NOT NULL,
    capacity INTEGER,
    year_of_manufacture TEXT,
    airline_id INTEGER,
    FOREIGN KEY(airline_id) REFERENCES airlines(id)
)

```

#### Приложение

Веб-приложение написано на ЯП Python с использованием библиотеки FastAPI. Все исходники в `main.py`
