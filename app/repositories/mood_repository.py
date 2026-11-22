import sqlite3
from contextlib import closing

from data_base.init_db import create_database
from models.mood import Mood


class MoodRepository:
    '''Хранилище записей настроения.'''
    def __init__(self, database_path):
        self.database_path = str(database_path)

    def connect(self):
        '''Открывает соединение с базой данных.'''
        return sqlite3.connect(self.database_path)

    def initialize(self):
        '''Готовит базу данных к работе.'''
        create_database(self.database_path)

    def save(self, mood):
        '''Сохраняет запись настроения.'''
        with closing(self.connect()) as connection:
            with connection:
                connection.execute(
                    '''INSERT INTO moods (entry_date, score, note)
                    VALUES (?, ?, ?)
                    ON CONFLICT(entry_date) DO UPDATE SET
                    score = excluded.score,
                    note = excluded.note''',
                    (mood.entry_date, mood.score, mood.note),
                )

    def get_entry(self, entry_date):
        '''Возвращает запись за дату.'''
        with closing(self.connect()) as connection:
            row = connection.execute(
                'SELECT entry_date, score, note '
                'FROM moods WHERE entry_date = ?',
                (entry_date,),
            ).fetchone()
        return Mood(*row) if row else None

    def get_entries(self, start_date=None):
        '''Возвращает записи в хронологическом порядке.'''
        query = 'SELECT entry_date, score, note FROM moods'
        parameters = ()
        if start_date:
            query += ' WHERE entry_date >= ?'
            parameters = (start_date,)
        query += ' ORDER BY entry_date ASC'
        with closing(self.connect()) as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [Mood(*row) for row in rows]

    def get_setting(self, name, default=None):
        '''Возвращает значение настройки.'''
        with closing(self.connect()) as connection:
            row = connection.execute(
                'SELECT value FROM settings WHERE name = ?',
                (name,),
            ).fetchone()
        return row[0] if row else default

    def save_setting(self, name, value):
        '''Сохраняет значение настройки.'''
        with closing(self.connect()) as connection:
            with connection:
                connection.execute(
                    '''INSERT INTO settings (name, value) VALUES (?, ?)
                    ON CONFLICT(name) DO UPDATE SET value = excluded.value''',
                    (name, value),
                )
