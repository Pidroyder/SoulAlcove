import sqlite3
from contextlib import closing
from pathlib import Path

SCHEMA = '''
CREATE TABLE IF NOT EXISTS moods (
    entry_date TEXT PRIMARY KEY,
    score INTEGER NOT NULL,
    note TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS settings (
    name TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
'''


def create_database(database_path):
    '''Создаёт файл базы данных и таблицы.'''
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(str(path))) as connection:
        with connection:
            connection.executescript(SCHEMA)
