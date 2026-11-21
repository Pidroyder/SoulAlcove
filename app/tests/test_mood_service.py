import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from models.mood import MAX_NOTE_LENGTH
from repositories.mood_repository import MoodRepository
from services.mood_service import MoodService


class MoodServiceTest(unittest.TestCase):
    '''Тесты сервиса записей настроения.'''
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.service = MoodService(
            MoodRepository(Path(self.directory.name) / 'database')
        )
        self.service.initialize()

    def tearDown(self):
        self.directory.cleanup()

    def test_record_mood_rejects_invalid_score(self):
        '''Оценка вне шкалы отклоняется.'''
        with self.assertRaises(ValueError):
            self.service.record_mood(0)
        with self.assertRaises(ValueError):
            self.service.record_mood(6)

    def test_record_mood_trims_note(self):
        '''Заметка очищается от лишних пробелов.'''
        entry = self.service.record_mood(4, '  good day  ', '2026-01-01')
        self.assertEqual(entry.note, 'good day')

    def test_record_mood_rejects_long_note(self):
        '''Слишком длинная заметка отклоняется.'''
        with self.assertRaises(ValueError):
            self.service.record_mood(3, 'x' * (MAX_NOTE_LENGTH + 1))

    def test_get_entries_for_period_week(self):
        '''Неделя включает последние семь дней.'''
        today = date.today()
        old_date = (today - timedelta(days=7)).isoformat()
        self.service.record_mood(2, '', old_date)
        self.service.record_mood(5, '', today.isoformat())
        entries = self.service.get_entries_for_period('week')
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].score, 5)

    def test_build_chart_data_groups_all_time_by_month(self):
        '''За всё время записи группируются по месяцам.'''
        self.service.record_mood(2, '', '2026-01-10')
        self.service.record_mood(4, '', '2026-01-20')
        self.service.record_mood(5, '', '2026-02-01')
        values, labels = self.service.build_chart_data('all')
        self.assertEqual(labels, ['2026-01', '2026-02'])
        self.assertEqual(values, [3.0, 5.0])

    def test_language_is_saved(self):
        '''Выбранный язык сохраняется.'''
        self.assertIsNone(self.service.get_language())
        self.service.set_language('en')
        self.assertEqual(self.service.get_language(), 'en')

    def test_theme_is_saved(self):
        '''Выбранная тема сохраняется.'''
        self.assertIsNone(self.service.get_theme())
        self.service.set_theme('light')
        self.assertEqual(self.service.get_theme(), 'light')


if __name__ == '__main__':
    unittest.main()
