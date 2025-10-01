import sqlite3
import requests
from datetime import datetime
from cryptography.fernet import Fernet
import threading
import time

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.properties import BooleanProperty
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

# Константы
BASE_URL = "https://login.emaktab.uz"
KEY = Fernet.generate_key()
cipher = Fernet(KEY)

class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior,
                                 RecycleBoxLayout):
    ''' Adds selection and focus behaviour to the view. '''

class SelectableLabel(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            print("selection changed to {0}".format(rv.data[index]))
        else:
            print("selection removed for {0}".format(rv.data[index]))

class RV(RecycleView):
    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.data = []

class AccountManagerPopup(Popup):
    def __init__(self, main_app, **kwargs):
        super(AccountManagerPopup, self).__init__(**kwargs)
        self.main_app = main_app
        self.title = "Управление аккаунтами"
        self.size_hint = (0.8, 0.7)
        self.auto_dismiss = False
        
        # Создаем основной layout
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Заголовок
        title_label = Label(
            text='Список аккаунтов:',
            size_hint_y=0.1,
            font_size='18sp',
            bold=True
        )
        main_layout.add_widget(title_label)
        
        # RecycleView для списка аккаунтов
        self.rv = RV()
        self.rv.viewclass = 'SelectableLabel'
        self.rv.size_hint_y = 0.7
        
        # Layout для RecycleView
        layout = SelectableRecycleBoxLayout(
            default_size=(None, 40),
            default_size_hint=(1, None),
            size_hint_y=None,
            orientation='vertical'
        )
        layout.bind(minimum_height=layout.setter('height'))
        self.rv.add_widget(layout)
        
        main_layout.add_widget(self.rv)
        
        # Кнопки управления
        buttons_layout = BoxLayout(size_hint_y=0.2, spacing=10)
        
        delete_btn = Button(
            text='🗑️ Удалить выбранный',
            on_press=self.delete_selected,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        
        refresh_btn = Button(
            text='Обновить список',
            on_press=self.load_accounts,
            background_color=(0.2, 0.5, 0.8, 1)
        )
        
        close_btn = Button(
            text='Закрыть',
            on_press=self.dismiss,
            background_color=(0.5, 0.5, 0.5, 1)
        )
        
        buttons_layout.add_widget(delete_btn)
        buttons_layout.add_widget(refresh_btn)
        buttons_layout.add_widget(close_btn)
        
        main_layout.add_widget(buttons_layout)
        
        self.content = main_layout
        
        # Загружаем аккаунты при создании
        self.load_accounts()
    
    def load_accounts(self, *args):
        """Загрузка списка аккаунтов"""
        users = self.main_app.get_all_users()
        self.rv.data = []
        
        for user in users:
            status_icon = "[OK]" if user['is_active'] else "[NO]"
            self.rv.data.append({
                'text': f"{status_icon} {user['login']}",
                'login': user['login'],
                'is_active': user['is_active']
            })
    
    def delete_selected(self, *args):
        """Удаление выбранного аккаунта"""
        try:
            # Получаем layout manager из RecycleView
            layout_manager = None
            for child in self.rv.children:
                if hasattr(child, 'selected_nodes'):
                    layout_manager = child
                    break
            
            if layout_manager and layout_manager.selected_nodes:
                selected_index = layout_manager.selected_nodes[0]
                if selected_index < len(self.rv.data):
                    login = self.rv.data[selected_index]['login']
                    self.main_app.delete_user(login)
                    self.load_accounts()  # Обновляем список
                    self.main_app.update_stats()
                else:
                    self.main_app.log("ОШИБКА: Выберите аккаунт для удаления")
            else:
                self.main_app.log("ОШИБКА: Выберите аккаунт для удаления")
        except Exception as e:
            self.main_app.log(f"ОШИБКА удаления: {e}")

class EmaktabAutoApp(App):
    def build(self):
        self.title = "Emaktab Auto"
        self.is_running = False
        self.countdown_time = 0
        
        # Главный layout с красивым фоном
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        main_layout.canvas.before.clear()
        with main_layout.canvas.before:
            Color(0.95, 0.98, 1.0, 1)  # Светло-голубой фон
            Rectangle(pos=main_layout.pos, size=main_layout.size)
        
        # Заголовок с градиентом
        title = Label(
            text="Emaktab Auto",
            size_hint=(1, 0.08),
            font_size='28sp',
            bold=True,
            color=(0.2, 0.4, 0.8, 1)  # Синий цвет
        )
        main_layout.add_widget(title)
        
        # 1. БОЛЬШАЯ КНОПКА В ЦЕНТРЕ
        self.main_button = Button(
            text='Запустить',
            size_hint=(1, 0.15),
            font_size='22sp',
            bold=True,
            background_color=(0.0, 0.6, 1.0, 1),  # Ярко-синий
            background_normal='',
            background_down=''
        )
        self.main_button.bind(on_press=self.toggle_activity)
        main_layout.add_widget(self.main_button)
        
        # 2. ПОЛЯ ДЛЯ ДОБАВЛЕНИЯ АККАУНТОВ
        add_section = BoxLayout(orientation='vertical', spacing=10, size_hint=(1, 0.2))
        
        # Поля ввода
        input_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.6))
        
        self.login_input = TextInput(
            hint_text='Логин',
            size_hint=(0.5, 1),
            multiline=False,
            font_size='16sp',
            background_color=(1, 1, 1, 0.9),
            foreground_color=(0.2, 0.2, 0.2, 1),
            hint_text_color=(0.5, 0.5, 0.5, 1)
        )
        
        self.password_input = TextInput(
            hint_text='Пароль',
            size_hint=(0.5, 1),
            password=True,
            multiline=False,
            font_size='16sp',
            background_color=(1, 1, 1, 0.9),
            foreground_color=(0.2, 0.2, 0.2, 1),
            hint_text_color=(0.5, 0.5, 0.5, 1)
        )
        
        input_layout.add_widget(self.login_input)
        input_layout.add_widget(self.password_input)
        
        # Кнопка добавления
        self.add_btn = Button(
            text='Добавить аккаунт',
            size_hint=(1, 0.4),
            font_size='16sp',
            bold=True,
            background_color=(0.2, 0.8, 0.4, 1),  # Ярко-зеленый
            background_normal='',
            background_down=''
        )
        self.add_btn.bind(on_press=self.register_user)
        
        add_section.add_widget(input_layout)
        add_section.add_widget(self.add_btn)
        main_layout.add_widget(add_section)
        
        # 3. СПИСОК АККАУНТОВ
        accounts_section = BoxLayout(orientation='vertical', spacing=5, size_hint=(1, 0.25))
        
        accounts_title = Label(
            text="Список аккаунтов:",
            size_hint=(1, 0.2),
            font_size='16sp',
            bold=True,
            color=(0.3, 0.3, 0.3, 1)
        )
        accounts_section.add_widget(accounts_title)
        
        # ScrollView для списка аккаунтов
        self.accounts_scroll = ScrollView(size_hint=(1, 0.8))
        self.accounts_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None)
        self.accounts_layout.bind(minimum_height=self.accounts_layout.setter('height'))
        self.accounts_scroll.add_widget(self.accounts_layout)
        accounts_section.add_widget(self.accounts_scroll)
        
        main_layout.add_widget(accounts_section)
        
        # 4. ЛОГИ
        logs_section = BoxLayout(orientation='vertical', spacing=5, size_hint=(1, 0.32))
        
        logs_title = Label(
            text="Логи:",
            size_hint=(1, 0.15),
            font_size='16sp',
            bold=True,
            color=(0.3, 0.3, 0.3, 1)
        )
        logs_section.add_widget(logs_title)
        
        # ScrollView для логов
        self.logs_scroll = ScrollView(size_hint=(1, 0.85))
        self.log_label = Label(
            text='Добро пожаловать! Добавьте аккаунты и нажмите "Запустить".\n',
            size_hint_y=None,
            text_size=(None, None),
            halign='left',
            valign='top',
            font_size='14sp',
            color=(0.2, 0.2, 0.2, 1)
        )
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        self.logs_scroll.add_widget(self.log_label)
        logs_section.add_widget(self.logs_scroll)
        
        main_layout.add_widget(logs_section)
        
        # Инициализация БД
        self.init_db()
        self.update_accounts_list()
        
        return main_layout
    
    def init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect('emaktab_users.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                login TEXT UNIQUE,
                password_encrypted TEXT,
                session_cookies TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        self.log("База данных готова")
    
    def log(self, message):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        current_text = self.log_label.text
        new_text = f"[{timestamp}] {message}\n{current_text}"
        self.log_label.text = new_text
        
        # Автоматически прокручиваем логи вниз
        Clock.schedule_once(self.scroll_logs_to_bottom, 0.1)
    
    def scroll_logs_to_bottom(self, dt):
        """Прокрутка логов вниз"""
        try:
            self.logs_scroll.scroll_y = 0
        except:
            pass
    
    def update_accounts_list(self):
        """Обновление списка аккаунтов"""
        # Очищаем текущий список
        self.accounts_layout.clear_widgets()
        
        users = self.get_all_users()
        
        if not users:
            no_accounts_label = Label(
                text="Нет добавленных аккаунтов",
                size_hint_y=None,
                height=40,
                font_size='14sp',
                color=(0.7, 0.7, 0.7, 1)
            )
            self.accounts_layout.add_widget(no_accounts_label)
            return
        
        for user in users:
            account_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40)
            
            # Статус и логин
            status_icon = "[OK]" if user['is_active'] else "[NO]"
            account_label = Label(
                text=f"{status_icon} {user['login']}",
                size_hint_x=0.8,
                text_size=(None, None),
                halign='left',
                font_size='14sp'
            )
            
            # Кнопка удаления
            delete_btn = Button(
                text="X",
                size_hint_x=0.2,
                background_color=(1.0, 0.3, 0.3, 1),  # Ярко-красный
                font_size='14sp',
                bold=True
            )
            delete_btn.bind(on_press=lambda x, login=user['login']: self.delete_user_from_list(login))
            
            account_layout.add_widget(account_label)
            account_layout.add_widget(delete_btn)
            
            self.accounts_layout.add_widget(account_layout)
    
    def encrypt_data(self, data):
        return cipher.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data):
        return cipher.decrypt(encrypted_data.encode()).decode()
    
    def register_user(self, instance):
        """Регистрация пользователя"""
        try:
            login = self.login_input.text.strip()
            password = self.password_input.text.strip()
            
            if not login or not password:
                self.log("ОШИБКА: Введите логин и пароль")
                return
            
            # Проверяем, нет ли уже такого логина
            existing_users = self.get_all_users()
            if any(user['login'] == login for user in existing_users):
                self.log(f"ОШИБКА: Аккаунт {login} уже существует")
                return
            
            self.log(f"🔐 Проверяю {login}...")
            
            # Проверяем логин на emaktab
            if self.test_login(login, password):
                self.save_user(login, password)
                self.log(f"УСПЕХ: Аккаунт {login} добавлен!")
                self.login_input.text = ""
                self.password_input.text = ""
                self.update_accounts_list()
            else:
                self.log(f"ОШИБКА: Неверный логин или пароль для {login}")
                
        except Exception as e:
            self.log(f"ОШИБКА при добавлении аккаунта: {e}")
            # Очищаем поля ввода при ошибке
            self.login_input.text = ""
            self.password_input.text = ""
    
    def test_login(self, login, password):
        """Проверка логина/пароля и сохранение сессии"""
        try:
            self.log(f"🔗 Подключаюсь к {BASE_URL}...")
            
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': BASE_URL,
                'Referer': f"{BASE_URL}/",
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # Получаем главную страницу
            self.log("📄 Загружаю главную страницу...")
            main_page = session.get(BASE_URL, timeout=10)
            self.log(f"Главная страница загружена (статус: {main_page.status_code})")
            
            # Пробуем разные варианты данных для входа
            self.log("🔐 Отправляю данные для входа...")
            
            # Вариант 1: Стандартные поля
            login_data_variants = [
                {'login': login, 'password': password},
                {'username': login, 'password': password},
                {'email': login, 'password': password},
                {'user': login, 'pass': password},
                {'login': login, 'pass': password},
            ]
            
            # Пробуем разные эндпоинты
            endpoints = ['/auth', '/login', '/signin']
            
            for endpoint in endpoints:
                for i, login_data in enumerate(login_data_variants):
                    try:
                        self.log(f"🔄 Пробую вариант {i+1} на {endpoint}...")
                        response = session.post(f"{BASE_URL}{endpoint}", data=login_data, timeout=10, allow_redirects=True)
                        self.log(f"📤 Ответ: статус {response.status_code}, URL: {response.url}")
                        
                        # Проверяем успешность входа
                        if response.status_code == 200:
                            response_text = response.text.lower()
                            final_url = response.url.lower()
                            
                            # Проверяем, что мы не на странице входа
                            if 'login' in final_url or 'auth' in final_url or 'signin' in final_url:
                                self.log(f"ОШИБКА: Вариант {i+1} - остался на странице входа")
                                continue
                            
                            # Проверяем содержимое на ошибки
                            if any(word in response_text for word in ['error', 'неверный', 'ошибка', 'invalid', 'incorrect']):
                                self.log(f"ОШИБКА: Вариант {i+1} - ошибка в ответе")
                                continue
                            
                            # Если дошли сюда - успешный вход!
                            self.log(f"ЗАШЕЛ! Вариант {i+1} сработал!")
                            self.save_session(login, session.cookies)
                            self.log("💾 Сессия сохранена успешно")
                            return True
                            
                    except Exception as e:
                        self.log(f"⚠️ Ошибка варианта {i+1}: {e}")
                        continue
            
            self.log("НЕ ЗАШЕЛ - все варианты не сработали")
            return False
            
        except Exception as e:
            self.log(f"НЕ ЗАШЕЛ - ошибка подключения: {e}")
            return False
    
    def save_session(self, login, cookies):
        """Сохранение сессии пользователя"""
        try:
            conn = sqlite3.connect('emaktab_users.db')
            cursor = conn.cursor()
            
            # Конвертируем cookies в строку
            cookies_str = '; '.join([f"{c.name}={c.value}" for c in cookies])
            
            cursor.execute('''
                UPDATE users SET session_cookies = ? WHERE login = ?
            ''', (cookies_str, login))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.log(f"⚠️ Ошибка сохранения сессии: {e}")
    
    def get_session(self, login):
        """Получение сохраненной сессии пользователя"""
        try:
            conn = sqlite3.connect('emaktab_users.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT session_cookies FROM users WHERE login = ?', (login,))
            result = cursor.fetchone()
            
            conn.close()
            
            if result and result[0]:
                return result[0]
            return None
            
        except Exception as e:
            self.log(f"⚠️ Ошибка получения сессии: {e}")
            return None
    
    def save_user(self, login, password):
        """Сохранение пользователя в БД"""
        try:
            conn = sqlite3.connect('emaktab_users.db')
            cursor = conn.cursor()
            
            password_encrypted = self.encrypt_data(password)
            
            # Используем INSERT OR REPLACE для избежания дубликатов
            cursor.execute('''
                INSERT OR REPLACE INTO users (login, password_encrypted, is_active, created_at)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            ''', (login, password_encrypted))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.log(f"ОШИБКА сохранения пользователя: {e}")
            raise
    
    def get_all_users(self):
        """Получение всех пользователей"""
        conn = sqlite3.connect('emaktab_users.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT login, password_encrypted, is_active FROM users')
        users = cursor.fetchall()
        
        result = []
        for login, pass_enc, is_active in users:
            try:
                password = self.decrypt_data(pass_enc)
                result.append({
                    'login': login, 
                    'password': password,
                    'is_active': is_active
                })
            except:
                continue
        
        conn.close()
        return result
    
    def delete_user(self, login):
        """Удаление пользователя"""
        conn = sqlite3.connect('emaktab_users.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM users WHERE login = ?', (login,))
        conn.commit()
        conn.close()
        
        self.log(f"🗑️ Аккаунт {login} удален")
        self.update_accounts_list()
    
    def delete_user_from_list(self, login):
        """Удаление пользователя из списка"""
        self.delete_user(login)
    
    def show_account_manager(self, instance):
        """Показать менеджер аккаунтов"""
        users = self.get_all_users()
        
        if not users:
            self.log("📝 Нет сохраненных аккаунтов")
            return
        
        # Создаем простой popup без RecycleView
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        title_label = Label(
            text="📋 Управление аккаунтами",
            size_hint_y=0.1,
            font_size='18sp',
            bold=True
        )
        content.add_widget(title_label)
        
        # Список аккаунтов в ScrollView
        scroll = ScrollView(size_hint_y=0.7)
        accounts_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None)
        accounts_layout.bind(minimum_height=accounts_layout.setter('height'))
        
        for user in users:
            account_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40)
            
            status_icon = "[OK]" if user['is_active'] else "[NO]"
            account_label = Label(
                text=f"{status_icon} {user['login']}",
                size_hint_x=0.6,
                text_size=(None, None),
                halign='left'
            )
            
            delete_btn = Button(
                text="🗑️",
                size_hint_x=0.2,
                background_color=(0.8, 0.2, 0.2, 1)
            )
            delete_btn.bind(on_press=lambda x, login=user['login']: self.delete_user_from_simple_popup(login, popup))
            
            toggle_btn = Button(
                text="🔄" if user['is_active'] else "▶️",
                size_hint_x=0.2,
                background_color=(0.2, 0.6, 0.2, 1) if user['is_active'] else (0.6, 0.6, 0.2, 1)
            )
            toggle_btn.bind(on_press=lambda x, login=user['login']: self.toggle_user_status_simple(login, popup))
            
            account_layout.add_widget(account_label)
            account_layout.add_widget(toggle_btn)
            account_layout.add_widget(delete_btn)
            
            accounts_layout.add_widget(account_layout)
        
        scroll.add_widget(accounts_layout)
        content.add_widget(scroll)
        
        # Кнопка закрытия
        close_btn = Button(
            text="Закрыть",
            size_hint_y=0.1,
            background_color=(0.5, 0.5, 0.5, 1)
        )
        content.add_widget(close_btn)
        
        popup = Popup(
            title="",
            content=content,
            size_hint=(0.8, 0.7),
            auto_dismiss=False
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def delete_user_from_simple_popup(self, login, popup):
        """Удаление пользователя из простого popup"""
        self.delete_user(login)
        popup.dismiss()
        self.show_account_manager(None)  # Обновляем список
    
    def toggle_user_status_simple(self, login, popup):
        """Переключение статуса пользователя в простом popup"""
        conn = sqlite3.connect('emaktab_users.db')
        cursor = conn.cursor()
        
        # Получаем текущий статус
        cursor.execute('SELECT is_active FROM users WHERE login = ?', (login,))
        current_status = cursor.fetchone()[0]
        new_status = not current_status
        
        # Обновляем статус
        cursor.execute('UPDATE users SET is_active = ? WHERE login = ?', (new_status, login))
        conn.commit()
        conn.close()
        
        status_text = "активирован" if new_status else "деактивирован"
        self.log(f"🔄 Аккаунт {login} {status_text}")
        
        popup.dismiss()
        self.show_account_manager(None)  # Обновляем список
        self.update_stats()
    
    
    def toggle_activity(self, instance):
        """Запуск активности (новая логика)"""
        if not self.is_running:
            self.start_activity()
    
    def start_activity(self):
        """Запуск активности"""
        users = self.get_all_users()
        active_users = [user for user in users if user['is_active']]
        
        if not active_users:
            self.log("ОШИБКА: Нет активных аккаунтов для запуска")
            return
        
        self.is_running = True
        self.main_button.text = "Подключение..."
        self.main_button.background_color = (1.0, 0.6, 0.0, 1)  # Оранжевый
        self.main_button.disabled = True
        
        self.log(f"Запуск входа для {len(active_users)} аккаунтов")
        
        # Запускаем в отдельном потоке
        self.activity_thread = threading.Thread(target=self.run_activity, args=(active_users,))
        self.activity_thread.daemon = True
        self.activity_thread.start()
    
    def finish_activity(self):
        """Завершение активности"""
        self.is_running = False
        self.main_button.text = "Завершено"
        self.main_button.background_color = (0.0, 0.8, 0.2, 1)  # Ярко-зеленый
        self.main_button.disabled = False
        
        self.log("Процесс завершен успешно")
        
        # Через 3 секунды возвращаем кнопку в исходное состояние
        Clock.schedule_once(self.reset_button, 3)
    
    def reset_button(self, dt):
        """Сброс кнопки в исходное состояние"""
        self.main_button.text = "Запустить"
        self.main_button.background_color = (0.0, 0.6, 1.0, 1)  # Ярко-синий
    
    def show_countdown_on_button(self, total_seconds):
        """Показать обратный отсчет на кнопке"""
        self.countdown_time = total_seconds
        
        def update_countdown(dt):
            self.countdown_time -= dt
            if self.countdown_time > 0:
                # Показываем целые числа: 3, 2, 1
                countdown_number = int(self.countdown_time) + 1
                if countdown_number > 0:
                    self.main_button.text = f"{countdown_number}"
                else:
                    self.main_button.text = "1"
                return True  # Продолжить отсчет
            else:
                self.main_button.text = "Завершено"
                self.main_button.background_color = (0.0, 0.8, 0.2, 1)  # Ярко-зеленый
                return False  # Остановить отсчет
        
        # Запускаем обратный отсчет
        Clock.schedule_interval(update_countdown, 0.1)
    
    def run_activity(self, users):
        """Основной цикл активности"""
        while self.is_running:
            for i, user in enumerate(users):
                if not self.is_running:
                    break
                
                try:
                    self.log(f"🔄 Обработка {user['login']}...")
                    
                    # Проверяем сессию пользователя
                    session_cookies = self.get_session(user['login'])
                    
                    if session_cookies:
                        # Используем сохраненную сессию
                        success = self.perform_activity_with_session(user['login'], session_cookies)
                        if success:
                            self.log(f"Активность для {user['login']} выполнена")
                        else:
                            self.log(f"⚠️ Сессия {user['login']} устарела, требуется повторный вход")
                            # Здесь можно добавить автоматический повторный вход
                    else:
                        self.log(f"⚠️ Нет сохраненной сессии для {user['login']}")
                        # Показываем секундомер для повторного входа
                        self.show_countdown_on_button(3)
                    
                    # Прогресс больше не нужен в новом интерфейсе
                    # progress_value = ((i + 1) / len(users)) * 100
                    # self.progress.value = progress_value
                    
                    # Пауза между пользователями (1-3 секунды)
                    if i < len(users) - 1:  # Не делаем паузу после последнего пользователя
                        import random
                        pause = random.uniform(1, 3)
                        self.log(f"⏸️ Пауза {pause:.1f} сек перед следующим аккаунтом...")
                        time.sleep(pause)
                    
                except Exception as e:
                    self.log(f"⚠️ Ошибка для {user['login']}: {e}")
            
            if self.is_running:
                self.log("Цикл активности завершен")
                # Завершаем процесс
                Clock.schedule_once(lambda dt: self.finish_activity(), 0.1)
                break
    
    def perform_activity_with_session(self, login, session_cookies):
        """Выполнение активности с использованием сохраненной сессии"""
        try:
            self.log(f"🔄 Проверяю сессию для {login}...")
            
            session = requests.Session()
            
            # Восстанавливаем cookies
            self.log("🍪 Восстанавливаю cookies...")
            for cookie in session_cookies.split('; '):
                if '=' in cookie:
                    name, value = cookie.split('=', 1)
                    session.cookies.set(name, value)
            
            # Выполняем активность - заходим на главную страницу
            self.log("🌐 Захожу на emaktab.uz...")
            response = session.get("https://emaktab.uz", timeout=10)
            self.log(f"📊 Ответ: статус {response.status_code}")
            
            # Проверяем, что сессия еще действительна
            if response.status_code == 200:
                if 'login' in response.url.lower():
                    self.log(f"ОШИБКА: {login} - СЕССИЯ ИСТЕКЛА (перенаправлен на логин)")
                    return False
                else:
                    self.log(f"УСПЕХ: {login} - АКТИВНОСТЬ ВЫПОЛНЕНА (зашел в систему)")
                    
                    # Имитируем реальное поведение пользователя - остаемся на сайте 3 секунды
                    delay = 3  # Ровно 3 секунды
                    import datetime
                    start_time = datetime.datetime.now()
                    self.log(f"Имитирую активность на сайте {delay} сек... (начало: {start_time.strftime('%H:%M:%S')})")
                    
                    # Показываем обратный отсчет на кнопке
                    self.show_countdown_on_button(delay)
                    
                    # Показываем детальный прогресс каждой секунды
                    for i in range(int(delay)):
                        remaining = delay - i
                        self.log(f"  -> Осталось {remaining:.0f} сек на сайте...")
                        time.sleep(1)
                    
                    end_time = datetime.datetime.now()
                    total_time = (end_time - start_time).total_seconds()
                    self.log(f"  -> Время на сайте истекло! (потрачено: {total_time:.1f} сек)")
                    
                    # Дополнительная активность - просмотр страниц
                    try:
                        # Просматриваем несколько страниц
                        pages = ['/userfeed', '/profile', '/notifications']
                        num_pages = random.randint(1, 2)  # 1-2 страницы
                        selected_pages = pages[:num_pages]
                        
                        self.log(f"  -> Начинаю просмотр {num_pages} дополнительных страниц...")
                        for page in selected_pages:
                            self.log(f"  -> Просматриваю страницу: {page}")
                            response = session.get(f'https://emaktab.uz{page}', timeout=5)
                            page_delay = random.uniform(1, 2)
                            self.log(f"  -> На странице {page} {page_delay:.1f} сек...")
                            time.sleep(page_delay)
                        
                        self.log(f"  -> Активность завершена для {login}")
                    except Exception as e:
                        self.log(f"  -> Ошибка дополнительной активности: {e}")
                    
                    return True
            else:
                self.log(f"ОШИБКА: {login} - ОШИБКА СЕРВЕРА (статус {response.status_code})")
                return False
                
        except Exception as e:
            self.log(f"ОШИБКА: {login} - ОШИБКА ПОДКЛЮЧЕНИЯ: {e}")
            return False

if __name__ == '__main__':
    EmaktabAutoApp().run()
