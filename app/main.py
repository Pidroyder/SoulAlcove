import locale
import os
import webbrowser
from datetime import date

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty,
    ColorProperty,
    DictProperty,
    ListProperty,
    NumericProperty,
    StringProperty,
)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex, platform
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonIcon, MDButtonText
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.navigationbar import (
    MDNavigationBar,
    MDNavigationItem,
    MDNavigationItemIcon,
    MDNavigationItemLabel,
)
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.segmentedbutton import (
    MDSegmentedButton,
    MDSegmentedButtonItem,
    MDSegmentButtonLabel,
)
from kivymd.uix.textfield import (
    MDTextField,
    MDTextFieldHintText,
    MDTextFieldMaxLengthText,
)

from models.mood import MOOD_LEVELS, get_level, today_iso
from repositories.mood_repository import MoodRepository
from services.mood_service import MoodService

if platform == 'android':
    from jnius import autoclass

GITHUB_URL = 'https://github.com/Pidroyder/SoulAlcove'
FONT_DIRECTORY = os.path.join(os.path.dirname(__file__), 'assets')

LabelBase.register(
    name='Emoji',
    fn_regular=os.path.join(FONT_DIRECTORY, 'NotoEmoji.ttf'),
)

MONTHS_EN = (
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
)

STRINGS = {
    'ru': {
        'today': 'Сегодня',
        'history': 'История',
        'settings': 'Настройки',
        'select_mood': 'Выбери настроение одним касанием',
        'note_hint': 'Короткая заметка',
        'save_note': 'Сохранить заметку',
        'back_to_today': 'Вернуться к сегодня',
        'history_title': 'График настроения',
        'settings_title': 'Настройки',
        'week': 'Неделя',
        'month': 'Месяц',
        'all_time': 'Всё время',
        'no_data': 'Пока нет записей',
        'no_note': 'Без заметки',
        'language_title': 'Язык интерфейса',
        'russian': 'Русский',
        'english': 'English',
        'theme_title': 'Тема оформления',
        'dark': 'Тёмная',
        'light': 'Светлая',
        'github': 'Открыть GitHub проекта',
        'link_error': 'Не удалось открыть ссылку',
        'saved': 'Настроение сохранено',
        'note_saved': 'Заметка сохранена',
        'choose_mood': 'Сначала выбери настроение',
    },
    'en': {
        'today': 'Today',
        'history': 'History',
        'settings': 'Settings',
        'select_mood': 'Pick your mood with one tap',
        'note_hint': 'Short note',
        'save_note': 'Save note',
        'back_to_today': 'Back to today',
        'history_title': 'Mood chart',
        'settings_title': 'Settings',
        'week': 'Week',
        'month': 'Month',
        'all_time': 'All time',
        'no_data': 'No entries yet',
        'no_note': 'No note',
        'language_title': 'Interface language',
        'russian': 'Русский',
        'english': 'English',
        'theme_title': 'Theme',
        'dark': 'Dark',
        'light': 'Light',
        'github': 'Open project GitHub',
        'link_error': 'Could not open the link',
        'saved': 'Mood saved',
        'note_saved': 'Note saved',
        'choose_mood': 'Pick a mood first',
    },
}


def detect_language():
    '''Определяет язык интерфейса по системным настройкам.'''
    if platform == 'android':
        locale_class = autoclass('java.util.Locale')
        system_locale = locale_class.getDefault().getLanguage()
        return 'ru' if system_locale.startswith('ru') else 'en'
    system_locale = locale.getlocale()[0] or locale.getdefaultlocale()[0] or ''
    return 'ru' if system_locale.lower().startswith('ru') else 'en'


class MoodCircle(ButtonBehavior, MDBoxLayout):
    '''Круг с эмодзи для выбора настроения.'''
    score = NumericProperty()
    emoji = StringProperty()
    circle_color = ColorProperty((1, 1, 1, 1))
    selected = BooleanProperty(False)


class MoodEntryItem(ButtonBehavior, MDBoxLayout):
    '''Запись настроения в списке истории.'''
    entry_key = StringProperty()
    entry_date = StringProperty()
    emoji = StringProperty()
    note = StringProperty()


class NavigationItem(MDNavigationItem):
    '''Пункт нижней навигации.'''
    icon_name = StringProperty()
    text_key = StringProperty()
    screen_name = StringProperty()


class MoodChart(Widget):
    '''График настроения, нарисованный на canvas.'''
    values = ListProperty([])
    labels = ListProperty([])

    def update(self, values, labels):
        '''Обновляет точки и подписи графика.'''
        self.values = values
        self.labels = labels
        self.refresh()

    def on_values(self, instance, values):
        '''Перерисовывает график при изменении точек.'''
        self.refresh()

    def on_labels(self, instance, labels):
        '''Перерисовывает график при изменении подписей.'''
        self.refresh()

    def on_size(self, instance, size):
        '''Перерисовывает график при изменении размера.'''
        self.refresh()

    def on_pos(self, instance, position):
        '''Перерисовывает график при изменении позиции.'''
        self.refresh()

    def get_point_position(
        self, index, value, left, bottom, plot_width, plot_height
    ):
        '''Возвращает координаты точки графика.'''
        if len(self.values) == 1:
            point_x = left + plot_width / 2
        else:
            point_x = left + index / (len(self.values) - 1) * plot_width
        point_y = bottom + (value - 1) / 4 * plot_height
        return point_x, point_y

    def format_label(self, label):
        '''Форматирует подпись оси времени.'''
        application = App.get_running_app()
        return application.format_chart_label(label) if application else label

    def refresh(self):
        '''Перерисовывает график.'''
        self.canvas.clear()
        self.clear_widgets()
        application = App.get_running_app()
        background = (
            application.theme_cls.surfaceContainerLowColor
            if application else (0, 0, 0, 1)
        )
        with self.canvas:
            Color(rgba=background)
            Rectangle(pos=self.pos, size=self.size)
        if not self.values:
            application = App.get_running_app()
            message = (
                application.strings['no_data']
                if application else 'Нет данных'
            )
            self.add_widget(MDLabel(text=message, halign='center'))
            return
        left = dp(56)
        right = dp(12)
        bottom = dp(44)
        top = dp(12)
        plot_width = max(self.width - left - right, dp(1))
        plot_height = max(self.height - bottom - top, dp(1))
        self.draw_lines(left, bottom, plot_width, plot_height)
        self.draw_labels(left, bottom, plot_width, plot_height)

    def draw_lines(self, left, bottom, plot_width, plot_height):
        '''Рисует сетку и линию графика.'''
        application = App.get_running_app()
        outline = (
            application.theme_cls.outlineColor
            if application else (0.6, 0.6, 0.6, 0.3)
        )
        primary = (
            application.theme_cls.primaryColor
            if application else (0.2, 0.2, 0.2, 0.8)
        )
        with self.canvas:
            Color(rgba=(outline[0], outline[1], outline[2], 0.35))
            for score in range(1, 6):
                line_y = bottom + (score - 1) / 4 * plot_height
                Line(
                    points=[left, line_y, left + plot_width, line_y],
                    width=dp(1),
                )
            Color(rgba=primary)
            if len(self.values) > 1:
                line_points = []
                for index, value in enumerate(self.values):
                    point_x, point_y = self.get_point_position(
                        index, value, left, bottom, plot_width, plot_height
                    )
                    line_points.extend([point_x, point_y])
                Line(points=line_points, width=dp(2))

    def draw_labels(self, left, bottom, plot_width, plot_height):
        '''Размещает подписи осей.'''
        for score in range(1, 6):
            line_y = bottom + (score - 1) / 4 * plot_height
            self.add_widget(
                MDLabel(
                    text=str(score),
                    halign='center',
                    font_size='9sp',
                    size_hint=(None, None),
                    size=(dp(20), dp(16)),
                    pos=(dp(4), line_y - dp(8)),
                )
            )
        if not self.labels:
            return
        shown_labels = min(len(self.labels), 5)
        step = max(1, len(self.labels) // shown_labels)
        label_width = dp(40)
        minimum_x = left + dp(4)
        maximum_x = max(minimum_x, self.width - label_width - dp(4))
        for index in range(0, len(self.labels), step):
            point_x, _ = self.get_point_position(
                index, 1, left, bottom, plot_width, plot_height
            )
            label_x = max(minimum_x, point_x - label_width / 2)
            label_x = min(label_x, maximum_x)
            self.add_widget(
                MDLabel(
                    text=self.format_label(self.labels[index]),
                    halign='center',
                    font_size='9sp',
                    size_hint=(None, None),
                    size=(label_width, dp(16)),
                    pos=(label_x, bottom + dp(8)),
                )
            )


class SoulAlcoveApp(MDApp):
    '''Приложение трекера настроения.'''
    kv_file = os.path.join(os.path.dirname(__file__), 'soulalcove.kv')

    language = StringProperty('ru')
    strings = DictProperty(STRINGS['ru'])
    selected_date = StringProperty('')
    selected_score = NumericProperty(0)
    selected_period = StringProperty('week')
    theme_mode = StringProperty('dark')

    def build(self):
        '''Создаёт интерфейс приложения.'''
        self.theme_cls.dynamic_scheme_name = 'VIBRANT'
        self.theme_cls.primary_palette = 'DodgerBlue'
        self.service = MoodService(MoodRepository(self.get_database_path()))
        self.service.initialize()
        self.apply_theme(self.service.get_theme() or 'dark')
        self.selected_date = today_iso()
        self.apply_language(self.service.get_language() or detect_language())
        self.populate_moods(self.root)
        return self.root

    def on_start(self):
        '''Загружает данные после появления интерфейса.'''
        self.refresh_today()
        self.refresh_history()
        self.root.ids.russian_segment.active = self.language == 'ru'
        self.root.ids.english_segment.active = self.language == 'en'
        self.root.ids.dark_segment.active = self.theme_mode == 'dark'
        self.root.ids.light_segment.active = self.theme_mode == 'light'
        Clock.schedule_once(self.raise_chart_canvas, 0.1)
        Clock.schedule_once(self.refresh_history_after_theme, 0.3)

    def raise_chart_canvas(self, interval):
        '''Поднимает canvas графика над списком записей.'''
        chart = self.root.ids.mood_chart
        parent = chart.parent
        parent.canvas.remove(chart.canvas)
        parent.canvas.add(chart.canvas)

    def get_database_path(self):
        '''Возвращает путь к файлу базы данных.'''
        if platform == 'android':
            return os.path.join(self.user_data_dir, 'soulalcove.sqlite')
        return os.path.join(os.path.dirname(__file__), 'data_base', 'database')

    def populate_moods(self, root):
        '''Добавляет круги выбора настроения.'''
        container = root.ids.mood_circles
        for level in MOOD_LEVELS:
            container.add_widget(
                MoodCircle(
                    score=level.score,
                    emoji=level.emoji,
                    circle_color=get_color_from_hex(level.color_hex),
                )
            )

    def apply_language(self, language):
        '''Применяет язык интерфейса.'''
        self.language = language
        self.strings = STRINGS[language]
        if self.root:
            self.update_navigation_labels()

    def update_navigation_labels(self):
        '''Обновляет подписи нижней навигации.'''
        navigation = self.root.ids.navigation_bar
        for item in navigation.children:
            item.ids.item_label.text = self.strings.get(
                item.text_key, ''
            )

    def set_language(self, language):
        '''Сохраняет и применяет язык интерфейса.'''
        if language == self.language:
            return
        self.service.set_language(language)
        self.apply_language(language)
        self.refresh_today()
        self.refresh_history()

    def apply_theme(self, theme_mode):
        '''Применяет тему оформления.'''
        self.theme_mode = theme_mode
        self.theme_cls.theme_style = (
            'Dark' if theme_mode == 'dark' else 'Light'
        )

    def set_theme(self, theme_mode):
        '''Сохраняет и применяет тему оформления.'''
        if theme_mode == self.theme_mode:
            return
        self.service.set_theme(theme_mode)
        self.apply_theme(theme_mode)
        Clock.schedule_once(self.refresh_history_after_theme, 0.3)

    def refresh_history_after_theme(self, interval):
        '''Обновляет график после смены темы.'''
        self.refresh_history()

    def format_entry_date(self, entry_date):
        '''Форматирует дату записи.'''
        parsed = date.fromisoformat(entry_date)
        if self.language == 'ru':
            return parsed.strftime('%d.%m.%Y')
        return f'{MONTHS_EN[parsed.month - 1]} {parsed.day}, {parsed.year}'

    def format_chart_label(self, label):
        '''Форматирует подпись оси времени.'''
        if len(label) == 7:
            year, month = label.split('-')
            if self.language == 'ru':
                return f'{month}.{year[2:]}'
            return f'{MONTHS_EN[int(month) - 1]} {year[2:]}'
        parsed = date.fromisoformat(label)
        if self.language == 'ru':
            return parsed.strftime('%d.%m')
        return f'{MONTHS_EN[parsed.month - 1]} {parsed.day}'

    def refresh_today(self):
        '''Обновляет экран сегодняшней записи.'''
        entry = self.service.get_entry(self.selected_date)
        self.selected_score = entry.score if entry else 0
        self.root.ids.today_date.text = (
            self.format_entry_date(self.selected_date)
        )
        self.root.ids.note_field.text = entry.note if entry else ''
        level = get_level(self.selected_score) if self.selected_score else None
        self.root.ids.selected_mood_label.text = (
            level.titles[self.language] if level else ''
        )
        for circle in self.root.ids.mood_circles.children:
            circle.selected = circle.score == self.selected_score

    def refresh_history(self):
        '''Обновляет график и список записей.'''
        values, labels = self.service.build_chart_data(self.selected_period)
        self.root.ids.mood_chart.update(values, labels)
        entries = self.service.get_entries_for_period(self.selected_period)
        container = self.root.ids.entries_list
        container.clear_widgets()
        for entry in reversed(entries):
            container.add_widget(
                MoodEntryItem(
                    entry_key=entry.entry_date,
                    entry_date=self.format_entry_date(entry.entry_date),
                    emoji=get_level(entry.score).emoji,
                    note=entry.note,
                )
            )
        Clock.schedule_once(self.reset_history_scroll, 0.1)

    def reset_history_scroll(self, interval):
        '''Прокручивает список записей к последней записи.'''
        self.root.ids.entries_list.parent.scroll_y = 0.5

    def select_mood(self, score):
        '''Сохраняет настроение одним касанием.'''
        entry = self.service.record_mood(
            score=score,
            note=self.root.ids.note_field.text,
            entry_date=self.selected_date,
        )
        self.selected_score = entry.score
        self.refresh_today()
        self.refresh_history()
        self.show_message(self.strings['saved'])

    def save_note(self):
        '''Сохраняет заметку к выбранному настроению.'''
        if not self.selected_score:
            self.show_message(self.strings['choose_mood'])
            return
        self.service.record_mood(
            score=self.selected_score,
            note=self.root.ids.note_field.text,
            entry_date=self.selected_date,
        )
        self.refresh_history()
        self.show_message(self.strings['note_saved'])

    def reset_to_today(self):
        '''Возвращает экран сегодняшней записи.'''
        self.selected_date = today_iso()
        self.root.ids.screen_manager.current = 'today'
        self.refresh_today()

    def open_entry(self, entry_date):
        '''Открывает запись для редактирования.'''
        self.selected_date = entry_date
        self.root.ids.screen_manager.current = 'today'
        self.refresh_today()

    def select_period(self, period):
        '''Выбирает период графика.'''
        self.selected_period = period
        self.refresh_history()

    def switch_screen(self, bar, item, item_icon, item_text):
        '''Переключает разделы приложения.'''
        self.root.ids.screen_manager.current = item.screen_name

    def open_github(self):
        '''Открывает страницу проекта.'''
        try:
            if platform == 'android':
                intent_class = autoclass('android.content.Intent')
                uri_class = autoclass('android.net.Uri')
                activity_class = autoclass(
                    'org.kivy.android.PythonActivity'
                )
                intent = intent_class(
                    intent_class.ACTION_VIEW,
                    uri_class.parse(GITHUB_URL),
                )
                activity_class.mActivity.startActivity(intent)
            else:
                webbrowser.open(GITHUB_URL)
        except Exception:
            self.show_message(self.strings['link_error'])

    def show_message(self, text):
        '''Показывает краткое уведомление.'''
        application = App.get_running_app()
        background_color = (
            application.theme_cls.surfaceContainerColor
            if application else (0.12, 0.12, 0.12, 0.95)
        )
        text_color = (
            application.theme_cls.onSurfaceColor
            if application else (1, 1, 1, 1)
        )
        overlay = FloatLayout()
        message = MDLabel(
            text=text,
            halign='center',
            color=text_color,
            size_hint=(None, None),
            size=(dp(280), dp(48)),
            pos_hint={'center_x': 0.5, 'y': 0.08},
        )
        with message.canvas.before:
            Color(rgba=background_color)
            background = RoundedRectangle(
                pos=message.pos,
                size=message.size,
                radius=[dp(16)],
            )
        message.bind(
            pos=lambda instance, value: setattr(background, 'pos', value),
            size=lambda instance, value: setattr(background, 'size', value),
        )
        overlay.add_widget(message)
        Window.add_widget(overlay)
        Clock.schedule_once(
            lambda interval: Window.remove_widget(overlay), 2
        )


if __name__ == '__main__':
    SoulAlcoveApp().run()
