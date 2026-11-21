from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class MoodLevel:
    '''Уровень настроения.'''

    score: int
    emoji: str
    color_hex: str
    titles: dict


@dataclass
class Mood:
    '''Запись настроения за дату.'''

    entry_date: str
    score: int
    note: str = ''


MAX_NOTE_LENGTH = 140
PERIODS = ('week', 'month', 'all')

MOOD_LEVELS = (
    MoodLevel(1, '😢', '#E53935', {'ru': 'Очень плохо', 'en': 'Very bad'}),
    MoodLevel(2, '😕', '#FB8C00', {'ru': 'Плохо', 'en': 'Bad'}),
    MoodLevel(3, '😐', '#FDD835', {'ru': 'Нормально', 'en': 'Okay'}),
    MoodLevel(4, '🙂', '#7CB342', {'ru': 'Хорошо', 'en': 'Good'}),
    MoodLevel(5, '😄', '#2E7D32', {'ru': 'Отлично', 'en': 'Great'}),
)


def get_level(score):
    '''Возвращает уровень настроения по оценке.'''
    for level in MOOD_LEVELS:
        if level.score == score:
            return level
    return MOOD_LEVELS[2]


def validate_score(score):
    '''Проверяет оценку настроения.'''
    if isinstance(score, bool) or not isinstance(score, int):
        raise ValueError('Invalid mood score')
    if score < 1 or score > len(MOOD_LEVELS):
        raise ValueError('Invalid mood score')
    return score


def validate_note(note):
    '''Проверяет длину заметки.'''
    if note is None:
        return ''
    if len(note) > MAX_NOTE_LENGTH:
        raise ValueError('Note is too long')
    return note.strip()


def today_iso():
    '''Возвращает сегодняшнюю дату в формате ISO.'''
    return date.today().isoformat()
