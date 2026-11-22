from datetime import date, timedelta

from models.mood import (
    PERIODS,
    Mood,
    today_iso,
    validate_note,
    validate_score,
)

PERIOD_DAYS = {'week': 7, 'month': 30}


class MoodService:
    '''Сервис записей настроения.'''
    def __init__(self, repository):
        self.repository = repository

    def initialize(self):
        '''Готовит хранилище записей.'''
        self.repository.initialize()

    def record_mood(self, score, note='', entry_date=None):
        '''Сохраняет настроение за дату.'''
        entry = Mood(
            entry_date=entry_date or today_iso(),
            score=validate_score(score),
            note=validate_note(note),
        )
        self.repository.save(entry)
        return entry

    def get_entry(self, entry_date=None):
        '''Возвращает запись за дату.'''
        return self.repository.get_entry(entry_date or today_iso())

    def get_entries_for_period(self, period):
        '''Возвращает записи за выбранный период.'''
        if period not in PERIODS:
            raise ValueError('Unknown period')
        if period == 'all':
            return self.repository.get_entries()
        days = PERIOD_DAYS[period]
        start_date = (date.today() - timedelta(days=days - 1)).isoformat()
        return self.repository.get_entries(start_date)

    def get_language(self):
        '''Возвращает сохранённый язык интерфейса.'''
        language = self.repository.get_setting('language')
        return language if language in ('ru', 'en') else None

    def set_language(self, language):
        '''Сохраняет язык интерфейса.'''
        if language not in ('ru', 'en'):
            raise ValueError('Unknown language')
        self.repository.save_setting('language', language)

    def get_theme(self):
        '''Возвращает сохранённую тему оформления.'''
        theme = self.repository.get_setting('theme')
        return theme if theme in ('dark', 'light') else None

    def set_theme(self, theme):
        '''Сохраняет тему оформления.'''
        if theme not in ('dark', 'light'):
            raise ValueError('Unknown theme')
        self.repository.save_setting('theme', theme)

    def build_chart_data(self, period):
        '''Готовит точки и подписи для графика.'''
        entries = self.get_entries_for_period(period)
        if period == 'all':
            return self.group_by_month(entries)
        return (
            [entry.score for entry in entries],
            [entry.entry_date for entry in entries],
        )

    def group_by_month(self, entries):
        '''Группирует записи по месяцам.'''
        grouped = {}
        for entry in entries:
            month_key = entry.entry_date[:7]
            grouped.setdefault(month_key, []).append(entry.score)
        months = sorted(grouped)
        values = [
            sum(grouped[month]) / len(grouped[month])
            for month in months
        ]
        return values, months
