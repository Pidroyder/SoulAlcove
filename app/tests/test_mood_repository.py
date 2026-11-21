import tempfile
import unittest
from pathlib import Path

from models.mood import Mood
from repositories.mood_repository import MoodRepository


class MoodRepositoryTest(unittest.TestCase):
    '''Тесты хранилища записей настроения.'''
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.repository = MoodRepository(
            Path(self.directory.name) / 'database'
        )
        self.repository.initialize()

    def tearDown(self):
        self.directory.cleanup()

    def test_save_replaces_entry_for_same_date(self):
        '''Повторная запись за дату заменяет прежнюю.'''
        self.repository.save(Mood('2026-01-01', 2, 'first'))
        self.repository.save(Mood('2026-01-01', 4, 'second'))
        entry = self.repository.get_entry('2026-01-01')
        self.assertEqual(entry.score, 4)
        self.assertEqual(entry.note, 'second')

    def test_get_entries_filters_by_start_date(self):
        '''Выборка учитывает начальную дату.'''
        self.repository.save(Mood('2025-12-31', 3, 'old'))
        self.repository.save(Mood('2026-01-01', 5, 'new'))
        entries = self.repository.get_entries('2026-01-01')
        self.assertEqual(
            [entry.entry_date for entry in entries],
            ['2026-01-01'],
        )

    def test_settings_are_persisted(self):
        '''Настройки сохраняются и обновляются.'''
        self.repository.save_setting('language', 'en')
        self.assertEqual(self.repository.get_setting('language'), 'en')
        self.repository.save_setting('language', 'ru')
        self.assertEqual(self.repository.get_setting('language'), 'ru')
        self.assertEqual(
            self.repository.get_setting('missing', 'fallback'),
            'fallback',
        )


if __name__ == '__main__':
    unittest.main()
