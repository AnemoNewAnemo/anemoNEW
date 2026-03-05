import logging
import io
from collections import deque
from PIL import Image
import base64
import json
import os
import firebase_admin
from firebase_admin import credentials, db
import random
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
from google.genai import types
from google import genai
from google.genai.types import (
    FunctionDeclaration,
    GenerateContentConfig,
    GoogleSearch,
    Part,
    Retrieval,
    SafetySetting,
    Tool
)
import aiohttp
from google.genai.types import CreateCachedContentConfig, GenerateContentConfig, Part
import re
import time
import tempfile
import os
import requests
import pathlib
from io import BytesIO
from PIL import Image
import asyncio
from telegram.ext import CallbackContext, ContextTypes
from telegram import Update
from tempfile import NamedTemporaryFile
# Google API Key и модель Gemini

API_KEYS = os.getenv("API_KEYS", "").split(",")
# 2. Укажите основную и запасные модели
PRIMARY_MODEL = 'gemini-3-flash-preview' # Модель, которую пробуем в первую очередь
FALLBACK_MODELS = ['gemini-2.5-flash, gemini-2.5-flash-preview-05-20', 'gemini-2.5-flash-lite', 'gemini-2.0-flash', 'gemini-2.0-flash-exp'] # Модели на случай, если с основной ничего не вышло
PRIMARY_MODEL_FLESHLIGHT = 'gemini-2.5-flash-lite' # Модель, которую пробуем в первую очередь 
FALLBACK_MODELS_FLESHLIGHT = ['gemini-live-2.5-flash-preview', 'gemini-2.0-flash-lite', 'gemini-2.0-flash-lite-001'] # Модели на случай, если с основной ничего не вышло

GEMMA_MODELS = ['gemma-3-27b-it', 'gemma-3-12b-it', 'gemma-3-4b-it', 'gemma-3n-10b-it']
# Инициализация Firebase
cred = credentials.Certificate('/etc/secrets/firebase-key.json')  # Путь к вашему JSON файлу
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://anemone-60bbf-default-rtdb.europe-west1.firebasedatabase.app/'  # Замените на URL вашей базы данных
})

# Хранилище для историй диалогов пользователей
user_contexts = {}

user_roles = {}


# Конфигурация логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

class ApiKeyManager:
    """
    Класс для управления API-ключами.
    Запоминает последний удачный ключ и использует его первым.
    Потокобезопасен для асинхронной среды.
    """
    def __init__(self, api_keys: list):
        if not api_keys:
            raise ValueError("Список API ключей не может быть пустым.")
        self.api_keys = api_keys
        self._last_successful_key = None
        self._lock = asyncio.Lock()

    def get_keys_to_try(self) -> list:
        """
        Возвращает список ключей для перебора, ставя последний удачный ключ на первое место.
        """
        keys_to_try = []
        if self._last_successful_key and self._last_successful_key in self.api_keys:
            keys_to_try.append(self._last_successful_key)
        
        # Добавляем остальные ключи, избегая дублирования
        for key in self.api_keys:
            if key not in keys_to_try:
                keys_to_try.append(key)
        return keys_to_try

    async def set_successful_key(self, key: str):
        """
        Асинхронно и безопасно устанавливает последний удачный ключ.
        """
        async with self._lock:
            self._last_successful_key = key


key_manager = ApiKeyManager(api_keys=API_KEYS)




import uuid
def add_anemone_comment(channel_id, text, x, y, z):
    """
    Сохраняет комментарий в Firebase с привязкой к каналу и координатам.
    """
    try:
        # Если channel_id не передан, используем 'public' или дефолтный
        target = channel_id if channel_id else "default_world"
        ref = db.reference(f'anemone_comments/{target}')
        new_comment = ref.push()
        
        data = {
            "text": text,
            "pos": {"x": x, "y": y, "z": z},
            "created_at": {".sv": "timestamp"}
        }
        new_comment.set(data)
        return {"id": new_comment.key, **data}
    except Exception as e:
        logging.error(f"Error adding comment: {e}")
        return None

def get_anemone_comments(channel_id):
    """
    Загружает все комментарии для мира.
    """
    try:
        target = channel_id if channel_id else "default_world"
        ref = db.reference(f'anemone_comments/{target}')
        # Ограничиваем количество, если нужно, но пока грузим всё
        data = ref.get()
        if not data:
            return []
        
        # Преобразуем dict в list
        result = []
        for key, val in data.items():
            val['id'] = key
            result.append(val)
        return result
    except Exception as e:
        logging.error(f"Error getting comments: {e}")
        return []
# ... (Ваш код инициализации firebase и другие функции) ...

def get_single_media(user_id, media_id):
    """
    Получает одну конкретную запись (таймер) по ID пользователя и ID медиа.
    Нужно для режима 'Поделиться'.
    """
    try:
        path = f'users_timers/{user_id}/{media_id}'
        ref = db.reference(path)
        data = ref.get()
        return data if data else {}
    except Exception as e:
        logging.error(f"Ошибка получения медиа {media_id} для {user_id}: {e}")
        return {}


def get_user_timers(user_id):
    """
    Получает все записи таймеров для конкретного пользователя.
    """
    try:
        ref = db.reference(f'users_timers/{user_id}')
        data = ref.get()
        return data if data else {}
    except Exception as e:
        logging.error(f"Ошибка получения таймеров для {user_id}: {e}")
        return {}

def add_new_media(user_id, title, media_type="movie"):
    """
    Создает новую запись (фильм или сериал).
    Возвращает сгенерированный media_id.
    """
    try:
        # Генерируем уникальный ID для произведения
        media_id = str(uuid.uuid4())[:8]
        path = f'users_timers/{user_id}/{media_id}'
        ref = db.reference(path)
        
        new_media = {
            "id": media_id,
            "title": title,
            "type": media_type, # 'movie' или 'series'
            "created_at": {".sv": "timestamp"},
            "entries": {} # Сюда будем складывать заметки
        }
        
        ref.set(new_media)
        return media_id
    except Exception as e:
        logging.error(f"Ошибка создания медиа для {user_id}: {e}")
        return None

def add_timer_entry(
    user_id,
    media_id,
    note_text,
    timestamp,
    episode=None,
    file_ids=None
):
    """
    Добавляет заметку с таймкодом.
    Поддерживает:
    - несколько file_id (список)
    - один file_id (строка)
    - отсутствие файлов
    """
    try:
        path = f'users_timers/{user_id}/{media_id}/entries'
        ref = db.reference(path)

        new_entry_ref = ref.push()  # Генерирует уникальный ключ

        # --- НОРМАЛИЗАЦИЯ file_ids ---
        # Если фронт передал один file_id (строка)
        if isinstance(file_ids, str):
            file_ids = [file_ids]

        # Если пришло None — делаем пустой список
        if file_ids is None:
            file_ids = []

        entry_data = {
            "timestamp": timestamp,
            "text": note_text,
            "file_ids": file_ids,   # ← теперь тут список
            "episode": episode,
            "created_at": {".sv": "timestamp"},
        }

        new_entry_ref.set(entry_data)

        return new_entry_ref.key

    except Exception as e:
        logging.error(f"Ошибка добавления записи: {e}")
        return None

def delete_media(user_id, media_id):
    """
    Удаляет произведение целиком.
    """
    try:
        ref = db.reference(f'users_timers/{user_id}/{media_id}')
        ref.delete()
        return True
    except Exception as e:
        logging.error(f"Ошибка удаления медиа: {e}")
        return False

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN не задан в переменных окружения")

def upload_file_to_telegram(file_storage, chat_id):
    """
    Отправляет файл пользователю в чат, чтобы получить file_id.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    
    # ВАЖНО: file_storage - это объект FileStorage из Flask.
    # Мы передаем его поток (stream) напрямую в requests.
    files = {
        'photo': (file_storage.filename, file_storage.stream, file_storage.content_type)
    }
    data = {'chat_id': chat_id, 'caption': '📎 Изображение для заметки'}
    
    try:
        r = requests.post(url, files=files, data=data)
        resp = r.json()
        
        if resp.get('ok'):
            # Берем photo[-1] (самое высокое разрешение)
            return resp['result']['photo'][-1]['file_id']
        else:
            logging.error(f"Telegram API Error: {resp}")
    except Exception as e:
        logging.error(f"Upload error: {e}")
    return None

def get_telegram_file_link(file_id):
    """
    Получает прямую ссылку на файл по file_id.
    """
    try:
        # 1. Получаем file_path
        r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}")
        res = r.json()
        if res.get('ok'):
            file_path = res['result']['file_path']
            # 2. Формируем ссылку
            return f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
    except Exception as e:
        logging.error(f"Get file error: {e}")
    return None

# Добавьте эти функции в gpt-helper.py

def update_timer_entry(user_id, media_id, entry_id, text=None, timestamp=None, file_ids=None):
    """
    Обновляет заметку. Теперь принимает file_ids (список).
    """
    try:
        path = f'users_timers/{user_id}/{media_id}/entries/{entry_id}'
        ref = db.reference(path)
        
        updates = {}
        if text is not None:
            updates['text'] = text
        if timestamp is not None:
            updates['timestamp'] = timestamp
        
        # ИЗМЕНЕНИЕ: работаем с file_ids
        if file_ids is not None:
            updates['file_ids'] = file_ids 
            # Опционально: удаляем старое поле file_id, чтобы не путаться
            # updates['file_id'] = None 
            
        if updates:
            ref.update(updates)
        return True
    except Exception as e:
        logging.error(f"Ошибка обновления записи: {e}")
        return False

def delete_timer_entry(user_id, media_id, entry_id):
    """
    Удаляет конкретную заметку.
    """
    try:
        path = f'users_timers/{user_id}/{media_id}/entries/{entry_id}'
        ref = db.reference(path)
        ref.delete()
        return True
    except Exception as e:
        logging.error(f"Ошибка удаления записи: {e}")
        return False

def update_media_title(user_id, media_id, new_title):
    try:
        ref = db.reference(f'users_timers/{user_id}/{media_id}')
        ref.update({"title": new_title})
        return True
    except Exception as e:
        logging.error(f"Ошибка обновления названия: {e}")
        return False






def get_single_media(user_id, media_id):
    """
    Получает одну конкретную запись (таймер) по ID пользователя и ID медиа.
    Нужно для режима 'Поделиться'.
    """
    try:
        path = f'users_timers/{user_id}/{media_id}'
        ref = db.reference(path)
        data = ref.get()
        return data if data else {}
    except Exception as e:
        logging.error(f"Ошибка получения медиа {media_id} для {user_id}: {e}")
        return {}

def save_art_post(channel_id, post_id, data):
    """
    Сохраняет обработанный пост в art_posts/CHANNEL_ID/post_id
    """
    logging.info(f"post_id {post_id}")    
    try:
        # Нормализуем ID канала (убираем @ если есть)
        chan_key = channel_id.replace('@', '') if channel_id else "default"
        ref = db.reference(f'art_posts/{chan_key}/{post_id}')
        ref.set(data)
        return True
    except Exception as e:
        logging.info(f"Error saving art post {post_id}: {e}")
        return False

def get_art_post(channel_id, post_id):
    """
    Получает данные поста из базы, если они есть.
    """
    try:
        chan_key = channel_id.replace('@', '') if channel_id else "default"
        ref = db.reference(f'art_posts/{chan_key}/{post_id}')
        return ref.get()
    except Exception as e:
        # Логируем только критические ошибки, отсутствие ключа - это норма
        return None



# Глобальные переменные кэша
_ALL_POSTS_CACHE = None
_LAST_CACHE_UPDATE = 0

# --- ДОБАВИТЬ ЭТУ ФУНКЦИЮ ---
def reset_posts_cache():
    """Сбрасывает кэш постов, заставляя сервер перечитать базу при следующем запросе."""
    global _ALL_POSTS_CACHE
    _ALL_POSTS_CACHE = None
    logging.info("[CACHE] Кэш постов сброшен принудительно.")
# -----------------------------


def get_all_art_posts_cached(channel_id):
    global _ALL_POSTS_CACHE, _LAST_CACHE_UPDATE

    # 1. Нормализация ID канала
    if channel_id == 'default_world':
        channel_id = '@anemonn'
    
    # 2. ВАЖНОЕ ИЗМЕНЕНИЕ: Если это не anemonn, мы не используем базу вообще.
    # Возвращаем пустой список, чтобы логика дальше поняла, что базы нет.
    if channel_id != '@anemonn':
        return []

    # --- Дальше стандартная логика для anemonn ---
    current_time = time.time()

    if _ALL_POSTS_CACHE is None or (current_time - _LAST_CACHE_UPDATE) > 300:
        try:
            if 'db' not in globals():
                logging.error("CRITICAL: 'db' variable is not found!")
                return []

            chan_key = channel_id.replace('@', '')
            ref = db.reference(f'art_posts/{chan_key}')
            data = ref.get()

            posts_list = []

            if isinstance(data, dict):
                for pid, pdata in data.items():
                    if isinstance(pdata, dict):
                        try:
                            pdata['post_id'] = int(pid)
                            posts_list.append(pdata)
                        except ValueError:
                            continue 
            elif isinstance(data, list):
                for idx, pdata in enumerate(data):
                    if isinstance(pdata, dict) and pdata:
                        pdata['post_id'] = idx
                        posts_list.append(pdata)

            _ALL_POSTS_CACHE = posts_list
            _LAST_CACHE_UPDATE = current_time
            logging.info(f"[CACHE] Loaded {len(posts_list)} posts for {channel_id}")

        except Exception as e:
            logging.error(f"[CACHE ERROR] {e}")
            return []

    return _ALL_POSTS_CACHE


def get_valid_ids_list(channel_id):
    """
    Возвращает список ID только для @anemonn.
    Для остальных возвращает пустой список (сигнал для генератора использовать математику).
    """
    if channel_id == 'default_world':
        channel_id = '@anemonn'

    # Если канал чужой — базы нет, список ID пуст
    if channel_id != '@anemonn':
        return []

    posts = get_all_art_posts_cached(channel_id)
    
    if not posts:
        return []
    
    valid_ids = []
    for p in posts:
        if p.get('status', 'ok') != 'ok': continue
        
        # Считаем фото, если тип явно фото или не указан (старые записи)
        p_type = p.get('type', 'photo') 
        if p_type == 'photo':
            valid_ids.append(p['post_id'])

    valid_ids.sort()
    return valid_ids
















def save_ozon_tracking_to_firebase(user_id: int, item_data: dict):
    """Сохраняет товар для отслеживания в Firebase."""
    try:
        user_ref = db.reference(f"ozon_prices/{user_id}/tracked_items")
        current_items = user_ref.get() or []

        # Опционально: Предотвращение дублирования URL или обновление существующих
        existing_item_index = -1
        for i, existing_item in enumerate(current_items):
            if existing_item.get("url") == item_data["url"]:
                existing_item_index = i
                break
        
        if existing_item_index != -1:
            # Обновляем существующий элемент
            # Заменяем старые данные отслеживания новыми для того же URL
            current_items[existing_item_index] = item_data 
            logger.info(f"Обновлен товар {item_data['url']} для пользователя {user_id}")
        else:
            # Добавляем новый элемент
            current_items.append(item_data)
            logger.info(f"Добавлен новый товар {item_data['url']} для пользователя {user_id}")

        user_ref.set(current_items) # Сохраняем весь список обратно
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении отслеживания Ozon в Firebase: {e}")
        return False


def load_ozon_tracking_from_firebase(user_id: int):
    """Загружает все отслеживаемые товары Ozon для пользователя из Firebase."""
    try:
        user_ref = db.reference(f"ozon_prices/{user_id}/tracked_items")
        tracked_items = user_ref.get()

        if tracked_items is None:
            logger.info(f"Нет отслеживаемых товаров для пользователя {user_id}")
            return []
        
        logger.info(f"Загружено {len(tracked_items)} товаров для пользователя {user_id}")
        return tracked_items
    except Exception as e:
        logger.error(f"Ошибка при загрузке отслеживаемых товаров Ozon из Firebase: {e}")
        return []

def load_ozon_product_firebase(user_id: int, product_id: str):
    """Возвращает конкретный отслеживаемый товар по product_id для пользователя из Firebase."""
    try:
        user_ref = db.reference(f"ozon_prices/{user_id}/tracked_items/")
        tracked_items = user_ref.get()

        if not tracked_items:
            logger.info(f"Нет отслеживаемых товаров для пользователя {user_id}")
            return None

        for item in tracked_items:
            if item.get("item_id") == product_id:
                logger.info(f"Товар с ID {product_id} найден для пользователя {user_id}")
                return item

        logger.info(f"Товар с ID {product_id} не найден у пользователя {user_id}")
        return None

    except Exception as e:
        logger.error(f"Ошибка при загрузке товара Ozon из Firebase: {e}")
        return None


def delete_ozon_product_firebase(user_id: int, product_id: str) -> bool:
    """Удаляет конкретный отслеживаемый товар по product_id для пользователя из Firebase."""
    try:
        user_ref = db.reference(f"ozon_prices/{user_id}/tracked_items/")
        tracked_items = user_ref.get()

        if not tracked_items:
            logger.info(f"Нет отслеживаемых товаров для пользователя {user_id}")
            return False

        # Оставим только те товары, у которых item_id не равен product_id
        updated_items = [item for item in tracked_items if item.get("item_id") != product_id]

        # Обновим список в Firebase
        user_ref.set(updated_items)
        logger.info(f"Товар с ID {product_id} удалён для пользователя {user_id}")
        return True

    except Exception as e:
        logger.error(f"Ошибка при удалении товара Ozon из Firebase: {e}")
        return False


def update_ozon_tracking_item(user_id: str, item_id: str, updated_fields: dict) -> bool:
    try:
        from firebase_admin import db
        user_ref = db.reference(f"ozon_prices/{user_id}/tracked_items")
        current_items = user_ref.get() or []

        updated = False
        for item in current_items:
            if item.get("item_id") == item_id:
                item.update(updated_fields)  # Обновляем только нужные поля
                updated = True
                break

        if updated:
            user_ref.set(current_items)  # Сохраняем обратно весь список
            return True
        else:
            logger.warning(f"Товар с item_id={item_id} не найден у пользователя {user_id}")
            return False
    except Exception as e:
        logger.exception(f"Ошибка при обновлении отслеживаемого товара: {e}")
        return False


def load_context_from_firebase():
    """Загружает user_contexts, user_roles, пресеты и модели из Firebase."""
    global user_contexts, user_roles, user_presets, user_models
    try:
        ref_context = db.reference('user_contexts')
        ref_roles = db.reference('user_roles')

        # Загружаем контексты
        json_context = ref_context.get()
        if json_context:
            for user_id, context_list in json_context.items():
                user_contexts[int(user_id)] = deque(context_list, maxlen=150)

        # Загружаем роли с вложенной структурой
        json_roles = ref_roles.get()
        if json_roles:
            for user_id, roles in json_roles.items():
                if isinstance(roles, list):
                    # Конвертируем список ролей в словарь с UUID
                    user_roles[int(user_id)] = {str(uuid.uuid4()): role for role in roles}
                elif isinstance(roles, dict):
                    user_roles[int(user_id)] = roles

        logging.info("Контекст, роли, пресеты и модели успешно загружены из Firebase.")
    except Exception as e:
        logging.error(f"Ошибка при загрузке данных из Firebase: {e}")


def load_publications_from_firebase():
    """Загружает все публикации из Firebase в формате, сохраняющем иерархию."""
    try:
        ref = db.reference('users_publications')
        data = ref.get() or {}
        # Возвращаем данные в исходной структуре
        return data
    except Exception as e:
        logging.error(f"Ошибка при загрузке публикаций из Firebase: {e}")
        return {}
def save_publications_to_firebase(user_id, message_id, new_data):
    """Загружает актуальные данные перед сохранением, чтобы избежать перезаписи."""
    try:
        # Ссылка на путь пользователя и сообщения
        path = f"users_publications/{user_id}/{message_id}"
        ref = db.reference(path)

        # Получаем актуальные данные
        current_data = ref.get() or {}

        # Осторожное слияние: обновляем только те поля, где значение не None
        merged_data = current_data.copy()
        for k, v in new_data.items():
            if v is not None:
                merged_data[k] = v

        # Сохраняем обновлённые данные
        ref.set(merged_data)

    except Exception as e:
        logging.error(f"Ошибка при сохранении публикации {user_id}_{message_id} в Firebase: {e}")



def get_specific_music_post(user_id, message_id):
    """
    Загружает конкретный пост пользователя по ID.
    Проверяет, является ли он музыкальным постом.
    """
    try:
        # Точечный запрос к Firebase: users_publications/user_id/userid_messageid
        path = f"users_publications/{user_id}/{message_id}"
        ref = db.reference(path)
        post_data = ref.get()

        if not post_data:
            return None
        
        # Проверяем флаг music_post
        if post_data.get("music_post") is True:
            return post_data
        
        return None
    except Exception as e:
        logging.error(f"Ошибка при получении музыкального поста {path}: {e}")
        return None

def get_telegram_file_url(file_id):
    """
    Получает прямую ссылку на файл через Telegram API.
    """
    try:
        # 1. Получаем путь к файлу (file_path)
        url_info = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
        response = requests.get(url_info)
        result = response.json()

        if result.get("ok"):
            file_path = result["result"]["file_path"]
            # 2. Формируем ссылку для скачивания/стриминга
            download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
            return download_url
        else:
            logging.error(f"Telegram API Error: {result}")
            return None
    except Exception as e:
        logging.error(f"Error getting file url: {e}")
        return None


def save_inline_query_to_firebase(user_id: int, query: str, response: str):
    """Сохраняет последний запрос и ответ пользователя (до 10 штук)"""
    try:
        ref = db.reference(f"neuro_search/{user_id}")
        current_data = ref.get() or []

        # Удаляем дубликаты по query
        current_data = [item for item in current_data if item.get("query") != query]

        # Добавляем новый запрос в начало списка
        current_data.insert(0, {"query": query, "response": response})

        # Ограничиваем 10 последними
        if len(current_data) > 10:
            current_data = current_data[:10]

        ref.set(current_data)
    except Exception as e:
        logging.error(f"Ошибка при сохранении inline запроса в Firebase: {e}")
def load_user_inline_queries(user_id: int) -> list[dict]:
    """Загружает последние 10 inline-запросов пользователя."""
    try:
        ref = db.reference(f"neuro_search/{user_id}")
        return ref.get() or []
    except Exception as e:
        logging.error(f"Ошибка при загрузке inline-запросов пользователя {user_id}: {e}")
        return []



def load_shared_publications():
    """Загружает общие публикации из Firebase."""
    try:
        ref = db.reference('shared_publications')
        return ref.get() or {}
    except Exception as e:
        logging.error(f"Ошибка при загрузке общих публикаций: {e}")
        return {}


def load_entire_database():
    """Загружает всю базу данных из Firebase."""
    try:
        ref = db.reference('/')
        return ref.get() or {}
    except Exception as e:
        logging.error(f"Ошибка при загрузке базы данных: {e}")
        return {}

def save_to_shared_publications(user_id: int, key: str, data: dict) -> None:
    ref = db.reference(f"shared_publications/{user_id}/{key}")
    ref.set(data)


def save_to_user_plants(user_id: int, scientific_name: str, data: dict) -> None:
    """Сохраняет информацию о растении в Firebase."""
    try:
        ref = db.reference(f"user_plants/{user_id}/{scientific_name}")
        ref.set(data)
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных о растении: {e}")

def save_to_user_mapplants(user_id: int, name: str, data: dict) -> None:
    """Сохраняет информацию о растении в Firebase."""
    try:
        # Разделяем данные на общие и уникальные
        common_data = {
            "Full_text": data.get("Full_text"),
            "Type": data.get("Type")
        }
        user_specific_data = {
            "coordinates": data.get("coordinates"),
            "img_url": data.get("img_url"),
            "user_full_text": data.get("user_full_text")
        }

        # Сохраняем общие данные в plants_info
        info_ref = db.reference(f"plants_info/{name}")
        info_ref.update(common_data)

        # Генерируем уникальный ключ для новой записи
        record_key = db.reference(f"map_plants/{user_id}/{name}").push().key

        # Добавляем уникальную запись для пользователя
        user_ref = db.reference(f"map_plants/{user_id}/{name}/{record_key}")
        user_ref.set(user_specific_data)

        logging.info(f"Добавлена новая запись для растения '{name}' у пользователя {user_id}.")
        return record_key
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных о растении: {e}")

def load_all_plants_data() -> dict:
    """Загружает данные о всех растениях всех пользователей из Firebase."""
    try:
        map_plants_ref = db.reference("map_plants")
        plants_info_ref = db.reference("plants_info")
        map_plants_data = map_plants_ref.get() or {}
        plants_info_data = plants_info_ref.get() or {}

        # Добавляем общую информацию к данным пользователей
        for user_id, plants in map_plants_data.items():
            for plant_name, records in plants.items():
                if plant_name in plants_info_data:
                    for record_key, record_data in records.items():
                        record_data.update(plants_info_data[plant_name])

        return map_plants_data
    except Exception as e:
        logging.error(f"Ошибка при загрузке данных о растениях: {e}")
        return {}




def update_to_user_mapplants(user_id: int, name: str, new_name: str, new_data: dict) -> None:
    """Переименовывает растение пользователя, обновляя существующие данные."""
    try:
        # Получаем ссылку на старое растение
        old_ref = db.reference(f"map_plants/{user_id}/{name}")
        old_data = old_ref.get() or {}
        
        if not old_data:
            logging.warning(f"Растение '{name}' не найдено у пользователя {user_id}.")
            return

        # Проверяем, существует ли new_name в plants_info
        info_ref = db.reference(f"plants_info/{new_name}")
        existing_info = info_ref.get() or {}

        # Если new_name отсутствует в plants_info, добавляем его
        if not existing_info:
            common_data = {
                "Full_text": new_data.get("Full_text"),
                "Type": new_data.get("Type")
            }
            info_ref.update(common_data)
            logging.info(f"Добавлена новая общая информация для растения '{new_name}'.")
        else:
            logging.info(f"Общая информация для растения '{new_name}' уже существует.")

        # Генерируем уникальный record_key для новой записи
        new_record_ref = db.reference(f"map_plants/{user_id}/{new_name}").push()
        record_key = new_record_ref.key

        # Подготавливаем новые пользовательские данные
        user_specific_data = {
            "coordinates": new_data.get("coordinates", old_data.get("coordinates")),
            "img_url": new_data.get("img_url", old_data.get("img_url"))
        }

        # Добавляем новую запись для new_name
        new_record_ref.set(user_specific_data)
        logging.info(f"Добавлена новая запись для растения '{new_name}' у пользователя {user_id}.")

        # Удаляем старую запись с name
        old_ref.delete()
        logging.info(f"Старая запись для растения '{name}' удалена у пользователя {user_id}.")

    except Exception as e:
        logging.error(f"Ошибка при обновлении данных о растении: {e}")


def delete_user_plant_record(user_id: int, name: str, record_key: str) -> None:
    """Удаляет конкретную запись о растении пользователя."""
    try:
        ref = db.reference(f"map_plants/{user_id}/{name}/{record_key}")
        if not ref.get():
            logging.warning(f"Запись '{record_key}' для растения '{name}' не найдена у пользователя {user_id}.")
            return
        ref.delete()
        logging.info(f"Запись '{record_key}' для растения '{name}' у пользователя {user_id} удалена.")
    except Exception as e:
        logging.error(f"Ошибка при удалении записи о растении: {e}")


def mark_watering(user_id: int) -> None:
    """Добавляет дату и время полива в Firebase."""
    try:
        ref = db.reference(f"user_plants/{user_id}/water_plants")
        current_time = datetime.now().strftime("%d.%m.%y %H:%M")

        # Получаем текущие записи, если они есть
        existing_records = ref.get()
        if existing_records is None:
            existing_records = []

        # Добавляем новую запись
        existing_records.append(current_time)
        ref.set(existing_records)

    except Exception as e:
        logging.error(f"Ошибка при добавлении даты полива: {e}")


def load_water_plants(user_id: int) -> list:
    """Загружает список дат поливки пользователя из Firebase."""
    try:
        ref = db.reference(f"user_plants/{user_id}/water_plants")
        water_plants = ref.get() or []
        return water_plants
    except Exception as e:
        logging.error(f"Ошибка при загрузке данных о поливке: {e}")
        return []




# Функция для получения всех токенов из Firebase
def get_all_tokens() -> list:
    try:
        ref_tokens = db.reference('Tokens/All_tokens')
        all_tokens = ref_tokens.get()
        if all_tokens:
            logging.info("Загружены API-ключи из Firebase")
            return all_tokens
        else:
            logging.warning("В Firebase нет API-ключей, используем локальные")
            return []
    except Exception as e:
        logging.error(f"Ошибка при получении токенов из Firebase: {e}")
        return []

# Функция для установки списка всех токенов
def set_all_tokens(tokens: list):
    try:
        ref_tokens = db.reference('Tokens/All_tokens')
        ref_tokens.set(tokens)
        logging.info("Обновлены API-ключи в Firebase")
    except Exception as e:
        logging.error(f"Ошибка при сохранении токенов в Firebase: {e}")

# Функция для получения последнего успешного токена
def get_last_successful_token() -> str:
    try:
        ref_last_token = db.reference('Tokens/LAST_SUCCESSFUL_TOKEN')
        last_token = ref_last_token.get()
        if last_token:
            logging.info(f"Последний успешный API-ключ: {last_token}")
            return last_token
        else:
            logging.warning("В Firebase нет последнего успешного API-ключа")
            return None
    except Exception as e:
        logging.error(f"Ошибка при получении последнего успешного API-ключа: {e}")
        return None

# Функция для установки последнего успешного токена
def set_last_successful_token(token: str):
    try:
        ref_last_token = db.reference('Tokens/LAST_SUCCESSFUL_TOKEN')
        ref_last_token.set(token)
        logging.info(f"Сохранен последний успешный API-ключ: {token}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении последнего успешного API-ключа: {e}")












def load_user_plants(user_id: int) -> dict:
    """Загружает информацию о растениях пользователя из Firebase, исключая water_plants."""
    try:
        ref = db.reference(f"user_plants/{user_id}")
        data = ref.get() or {}
        return {key: value for key, value in data.items() if key != "water_plants"}
    except Exception as e:
        logging.error(f"Ошибка при загрузке данных о растениях: {e}")
        return {}

def delete_user_plant(user_id: int, scientific_name: str) -> None:
    """Удаляет информацию о конкретном растении пользователя из Firebase."""
    try:
        ref = db.reference(f"user_plants/{user_id}/{scientific_name}")
        if ref.get():
            ref.delete()
            logging.info(f"Растение '{scientific_name}' удалено для пользователя {user_id}.")
        else:
            logging.warning(f"Растение '{scientific_name}' не найдено у пользователя {user_id}.")
    except Exception as e:
        logging.error(f"Ошибка при удалении растения '{scientific_name}': {e}")

def copy_to_shared_publications(user_id: int, key: str) -> bool:
    """Копирует публикацию из users_publications в shared_publications."""
    ref_users = db.reference(f"users_publications/{user_id}/{key}")
    ref_shared = db.reference(f"shared_publications/{user_id}/{key}")

    data = ref_users.get()
    if data:
        ref_shared.set(data)  # Копируем данные в shared_publications
        return True
    return False
from html import unescape
async def notify_owner_favorited(context: CallbackContext, owner_id: int, post_data: dict):
    """Отправляет владельцу уведомление о добавлении его поста в избранное при достижении 3+ пользователей."""
    try:
        caption = post_data["media"][0]["caption"]
        logger.info(f"caption: {caption}")        
        caption = re.sub(r"<.*?>", "", caption)  # Убираем HTML-теги
        caption = unescape(caption)  # Декодируем HTML-сущности
        caption = re.split(r"\bseed\b", caption, flags=re.IGNORECASE)[0]  # Обрезаем по "seed"
        caption = re.sub(r"^\d+,\s*", "", caption)  # Убираем числа в начале строки
        
        # Обрезаем caption до ближайшего пробела перед 23 символами
        if len(caption) > 26:
            cutoff = caption[:26].rfind(" ")
            caption = caption[:cutoff] if cutoff != -1 else caption[:26]
        
        message_text = f"🎉 Поздравляем, вашу публикацию «{caption}» добавили в избранное 3 или более человек!"

        # Отправляем сообщение владельцу
        await context.bot.send_message(chat_id=owner_id, text=message_text)
    
    except Exception as e:
        logger.info(f"Ошибка при отправке уведомления владельцу: {e}")


def add_to_favorites(user_id: int, owner_id: int, post_id: str, context: CallbackContext) -> bool:
    """Добавляет или удаляет публикацию из избранного пользователя."""
    ref = db.reference(f"shared_publications/{owner_id}/{post_id}/favorites")
    favorites = ref.get() or []

    if user_id in favorites:
        favorites.remove(user_id)  # Удаляем из избранного
        ref.set(favorites)
        return False  # Удалён
    else:
        favorites.append(user_id)  # Добавляем в избранное
        ref.set(favorites)

        # Загружаем данные о посте и проверяем количество избранных
        publications = load_shared_publications()
        post_data = publications.get(owner_id, {}).get(post_id)
        logger.info(f"post_data {post_data} ")

        if post_data and len(favorites) >= 3:  # Проверяем, достигло ли число 3+
            asyncio.create_task(notify_owner_favorited(context, owner_id, post_data))

        return True  # Добавлен




def delete_from_firebase(keys, user_id):
    """Удаляет данные из Firebase, предварительно обновляя базу."""
    try:
        # Загрузка актуальных данных
        current_data = load_publications_from_firebase()
        
        if user_id in current_data:
            # Удаляем указанные ключи
            for key in keys:
                if key in current_data[user_id]:
                    del current_data[user_id][key]
            
            # Если у пользователя больше нет публикаций, удаляем его из базы полностью
            if not current_data[user_id]:
                del current_data[user_id]

                # Явное удаление узла пользователя в Firebase
                ref = db.reference(f'users_publications/{user_id}')
                ref.delete()  # Полностью удаляет данные пользователя

            else:
                # Обновляем базу только если у пользователя остались записи
                ref = db.reference('users_publications')
                ref.update(current_data)
                
        else:
            logging.warning(f"Пользователь {user_id} не найден в Firebase.")
    
    except Exception as e:
        logging.error(f"Ошибка при удалении данных {keys} пользователя {user_id} из Firebase: {e}")


def reset_firebase_dialog(user_id: int):
    """
    Очищает весь контекст пользователя из Firebase и обновляет локальное хранилище.

    :param user_id: ID пользователя, чей контекст необходимо сбросить.
    """
    try:
        # Ссылка на контекст пользователя в Firebase
        user_context_ref = db.reference(f'user_contexts/{user_id}')
        
        # Удаляем контекст пользователя из Firebase
        user_context_ref.delete()

        # Также удаляем из локального контекста
        if user_id in user_contexts:
            del user_contexts[user_id]
            logging.info(f"Контекст пользователя {user_id} успешно удалён из локального хранилища.")
    except Exception as e:
        logging.error(f"Ошибка при сбросе контекста пользователя {user_id}: {e}")


def save_channel_to_firebase(chat_id, user_id):
    """
    Сохраняет ID канала и связанного пользователя в Firebase.
    """
    try:
        ref = db.reference(f'users_publications/channels/{chat_id}')
        existing_data = ref.get() or {}
        user_ids = existing_data.get('user_ids', [])

        # Добавляем user_id в список, если его еще нет
        if user_id not in user_ids:
            user_ids.append(user_id)
            ref.set({'user_ids': user_ids})

        logging.info(f"Канал {chat_id} успешно привязан к пользователю {user_id}.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении ID канала: {e}")

def save_twitter_keys_to_firebase(user_id: int, api_key: str, api_secret: str, access_token: str, access_token_secret: str) -> None:
    """
    Сохраняет ключи API и токены доступа для публикации в Twitter в Firebase.
    """
    try:
        ref = db.reference(f'users_publications/twitter_keys/{user_id}')
        ref.set({
            "api_key": api_key,
            "api_secret": api_secret,
            "access_token": access_token,
            "access_token_secret": access_token_secret,
        })
        logging.info(f"Twitter API ключи успешно сохранены для пользователя {user_id}.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении Twitter API ключей: {e}")
        raise  # Передаем ошибку выше для обработки в вызывающей функции


def save_vk_keys_to_firebase(user_id: int, owner_id: str, token: str) -> None:
    """
    Сохраняет токен и ID группы для публикации в ВК в Firebase.
    """
    try:
        ref = db.reference(f'users_publications/vk_keys/{user_id}')
        ref.set({
            "owner_id": owner_id,
            "token": token
        })
        logging.info(f"Токен и ID группы успешно сохранены для пользователя {user_id}.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении токена и ID группы: {e}")


def save_context_to_firebase(user_id):
    """Сохраняет контекст и роли текущего пользователя в Firebase."""
    try:
        # Преобразуем deque текущего пользователя в список для сохранения в Firebase
        if user_id in user_contexts:
            json_context = {user_id: list(user_contexts[user_id])}
            ref_context = db.reference('user_contexts')
            ref_context.update(json_context)

        # Сохраняем роль текущего пользователя
        if user_id in user_roles:
            json_role = {user_id: user_roles[user_id]}
            ref_roles = db.reference('user_roles')
            ref_roles.update(json_role)

        logging.info(f"Данные пользователя {user_id} успешно сохранены в Firebase.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных пользователя {user_id} в Firebase: {e}")


def get_user_model(user_id: int) -> str:
    """Возвращает модель пользователя из Firebase или значение по умолчанию."""
    try:
        ref_models = db.reference(f'user_models/{user_id}')
        user_model = ref_models.get()

        if user_model:
            logging.info(f"Модель для пользователя {user_id}: {user_model}")
            return user_model
        else:
            logging.warning(f"Модель для пользователя {user_id} не найдена. Используется значение по умолчанию.")
            return "imagen3"
    except Exception as e:
        logging.error(f"Ошибка при загрузке модели для пользователя {user_id}: {e}")
        return "imagen3"

def set_user_model(user_id: int, model: str):
    """Устанавливает пользовательскую модель и сохраняет её в Firebase."""
    try:
        ref_models = db.reference(f'user_models/{user_id}')
        ref_models.set(model)
        logging.info(f"Модель пользователя {user_id} обновлена на: {model}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении модели в Firebase: {e}")
        
def get_user_preset(user_id: int) -> str:
    """Возвращает выбранный пресет пользователя из Firebase или значение по умолчанию."""
    try:
        ref_preset = db.reference(f'user_presets/{user_id}')
        user_preset = ref_preset.get()
        if user_preset:
            logging.info(f"Пресет для пользователя {user_id}: {user_preset}")
            return user_preset
        else:
            logging.warning(f"Пресет для пользователя {user_id} не найден. Используется значение по умолчанию.")
            return "Нет"
    except Exception as e:
        logging.error(f"Ошибка при загрузке пресета для пользователя {user_id}: {e}")
        return "Нет"

def set_user_preset(user_id: int, preset: str):
    """Устанавливает пользовательский пресет и сохраняет его в Firebase."""
    try:
        ref_preset = db.reference(f'user_presets/{user_id}')
        ref_preset.set(preset)
        logging.info(f"Пресет пользователя {user_id} обновлен на: {preset}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении пресета в Firebase: {e}")

import uuid

import re

def set_user_role(user_id, role_text):
    """Добавляет новую роль пользователю и сохраняет её в Firebase."""
    if user_id not in user_roles or not isinstance(user_roles[user_id], dict):
        user_roles[user_id] = {}  # Инициализируем как пустой словарь

    role_id = str(uuid.uuid4())  # Уникальный идентификатор роли

    # Извлекаем текст без круглых скобок
    clean_role_text = re.sub(r"\(.*?\)", "", role_text).strip()

    # Извлекаем краткое описание из текста роли (то, что в круглых скобках)
    short_name_match = re.search(r"\((.*?)\)", role_text)
    short_name = short_name_match.group(1) if short_name_match else None

    # Сохраняем роль и краткое описание (если есть)
    user_roles[user_id][role_id] = clean_role_text
    if short_name:
        if "short_names" not in user_roles[user_id]:
            user_roles[user_id]["short_names"] = {}
        user_roles[user_id]["short_names"][role_id] = short_name

    user_roles[user_id]["selected_role"] = clean_role_text  # Сохраняем только текст без скобок в selected_role
    user_roles[user_id].pop("default_role", None)
    user_roles[user_id].pop("game_role", None)  # Удаляем default_role, если он существует

    save_context_to_firebase(user_id)  # Сохраняем изменения в Firebase




async def generate_image_description(user_id, image_path, query=None, use_context=True):
    user_roles_data = user_roles.get(user_id, {})
    selected_role = None

    # Проверяем наличие роли по умолчанию
    default_role_key = user_roles_data.get("default_role")
    if default_role_key and default_role_key in DEFAULT_ROLES:
        selected_role = DEFAULT_ROLES[default_role_key]["full_description"]

    # Если у пользователя есть игровая роль, она имеет приоритет над дефолтной
    game_role_key = user_roles_data.get("game_role")
    if game_role_key and game_role_key in GAME_ROLES:
        selected_role = GAME_ROLES[game_role_key]["full_description"]

    # Если пользователь выбрал новую роль, она имеет наивысший приоритет
    if "selected_role" in user_roles_data:
        selected_role = user_roles_data["selected_role"]

    if not selected_role:
        selected_role = (
            "Ты обычный вариант модели Gemini реализованный в виде телеграм-бота. "
            "Помогаешь пользователю выполнять различные задачи и выполняешь его поручения. "
            "В боте есть кнопка выбора роли, сообщи об этом пользователю если он поинтересуется. "
            "Ты умеешь рисовать и дорисовывать изображения. Чтобы нарисовать, пользователь должен "
            "начать сообщение со слова «Нарисуй». Чтобы изменить или дорисовать изображение — отправить "
            "его с подписью, начинающейся с «Дорисуй»."
        )

    # Контекст
    relevant_context = await get_relevant_context(user_id) if use_context else ""
    if query and relevant_context:
        relevant_context = relevant_context.replace(f"user_message: {query}", "").strip()

    system_instruction = (
        f"Ты чат-бот играющий роль: {selected_role}. "
        f"Эту роль задал тебе пользователь и ты должен строго её придерживаться."
    )

    context = (
        f"Предыдущий контекст диалога: {relevant_context if relevant_context else 'отсутствует.'} "
        f"Собеседник прислал тебе изображение с подписью:\n{query}"
        if query else
        "Отреагируй на это изображение в контексте чата"
    )

    if not os.path.exists(image_path):
        return "Изображение недоступно. Попробуйте снова."

    image_path_obj = pathlib.Path(image_path)

    try:
        keys_to_try = key_manager.get_keys_to_try()
        logger.info(f"Будет протестировано {len(keys_to_try)} ключей")

        # Сначала пробуем только основную модель на всех ключах
        last_key = None
        for idx, api_key in enumerate(keys_to_try, start=1):
            logger.info(f"[{idx}/{len(keys_to_try)}] Проверка ключа ...{api_key[-4:]}")
            last_key = api_key

            try:
                client = genai.Client(api_key=api_key)

                try:
                    logger.info(f"Загрузка изображения с ключом ...{api_key[-4:]}")
                    image_file = client.files.upload(file=image_path_obj)
                    logger.info(f"Изображение успешно загружено: {image_file.uri}")
                except Exception as e_upload:
                    logger.warning(f"Не удалось загрузить изображение с ключом ...{api_key[-4:]}: {e_upload}")
                    continue  # пробуем следующий ключ

                safety_settings = [
                    types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                ]

                # Пробуем только основную модель
                logger.info(f"Попытка генерации с основной моделью {PRIMARY_MODEL} и ключом ...{api_key[-4:]}")
                try:
                    response = await client.aio.models.generate_content(
                        model=PRIMARY_MODEL,
                        contents=[
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part.from_uri(
                                        file_uri=image_file.uri,
                                        mime_type=image_file.mime_type
                                    ),
                                    types.Part(text=f"Пользователь прислал изображение: {context}\n"),
                                ]
                            )
                        ],
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=1.0,
                            top_p=0.9,
                            top_k=40,
                            safety_settings=safety_settings
                        )
                    )

                    if response.candidates and response.candidates[0].content.parts:
                        response_text = "".join(
                            part.text for part in response.candidates[0].content.parts
                            if part.text and not getattr(part, "thought", False)
                        ).strip()

                        if response_text:
                            logger.info(f"Успех: модель {PRIMARY_MODEL} с ключом ...{api_key[-4:]} дала результат")
                            await key_manager.set_successful_key(api_key)
                            return response_text

                except Exception as e_model:
                    logger.warning(f"Основная модель {PRIMARY_MODEL} с ключом ...{api_key[-4:]} не сработала: {e_model}")
                    continue

            except Exception as e_key:
                logger.warning(f"Ошибка при использовании ключа ...{api_key[-4:]}: {e_key}")
                continue

        # Если мы тут – все ключи с основной моделью провалились
        if last_key:
            logger.info(f"Все ключи провалились, пробуем fallback-модели на последнем ключе ...{last_key[-4:]}")
            try:
                client = genai.Client(api_key=last_key)
                image_file = client.files.upload(file=image_path_obj)

                safety_settings = [
                    types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                ]

                for model_name in FALLBACK_MODELS + GEMMA_MODELS:
                    logger.info(f"Попытка генерации с fallback-моделью {model_name} и ключом ...{last_key[-4:]}")
                    try:
                        response = await client.aio.models.generate_content(
                            model=model_name,
                            contents=[
                                types.Content(
                                    role="user",
                                    parts=[
                                        types.Part.from_uri(
                                            file_uri=image_file.uri,
                                            mime_type=image_file.mime_type
                                        ),
                                        types.Part(text=f"Пользователь прислал изображение: {context}\n"),
                                    ]
                                )
                            ],
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                temperature=1.0,
                                top_p=0.9,
                                top_k=40,
                                safety_settings=safety_settings
                            )
                        )

                        if response.candidates and response.candidates[0].content.parts:
                            response_text = "".join(
                                part.text for part in response.candidates[0].content.parts
                                if part.text and not getattr(part, "thought", False)
                            ).strip()

                            if response_text:
                                logger.info(f"Успех: fallback-модель {model_name} с ключом ...{last_key[-4:]} дала результат")
                                return response_text

                    except Exception as e_fallback:
                        logger.warning(f"Fallback-модель {model_name} не сработала: {e_fallback}")
                        continue
            except Exception as e_last:
                logger.error(f"Не удалось работать с последним ключом ...{last_key[-4:]}: {e_last}")

        logger.error("Все ключи и модели были перепробованы, результата нет")
        return "К сожалению, все ключи и модели исчерпаны. Попробуйте позже."

    except Exception as e:
        logger.error("Ошибка при распознавании изображения: %s", e)
        return "Произошла ошибка при обработке изображения. Попробуйте снова."

    finally:
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
                logger.info(f"Временный файл удален: {image_path}")
            except Exception as e:
                logger.error(f"Ошибка при удалении временного файла: {e}")


async def get_relevant_context(user_id):
    """Получает контекст для пользователя."""
    context = user_contexts.get(user_id, deque(maxlen=150))
    unique_context = list(dict.fromkeys(context)) 
    
    # Используем роль пользователя, если она есть, иначе стандартную роль
    user_role = user_roles.get(user_id, 
        "Ты играешь роль приятного собеседника - лисы хранительницы леса. Общение происходит в телеграм, тебе доступен журнал переписки, "
        "используй его чтобы имитировать живое общение, старайся сделать это общение естественным, избегай повторений. "
        "Так же собеседник может сам задать тебе личность, прислушивайся к его пожеланиям. "
        "Время и тип сообщения формата 2024-11-04 13:07:50 | bot_message: используются только в журнале, в своих ответах их не указывай. "
        "Ты стараешься подстроиться под собеседника и его увлечения, поддерживать абсолютно любую тему диалога какой бы она ни была. "
        "Твой стиль общения дружелюбный, умный, тактичный, добрый, заботливый, но уверенный, ты не боишься высказывать своё мнение. "
        "Ты ценишь природу, стараешься избегать повторов и бессмысленных фраз. Не задаёшь лишних вопросов, стараешься быть лаконичной. "
        "Общение с тобой лёгкое, живое и непринуждённое, ты отвечаешь в литературном стиле, легко воспринимаемом собеседником. "
        "Не используешь смайлики, кроме исключительных случаев когда они действительно уместны. Иногда уместны лёгкие шутки, сарказм, ирония "
        "или философия в случае если тема серьёзна или по запросу собеседника. Так же иногда можешь переставать быть вежливой и начинать грубить, "
        "особенно если кто-то общается неуважительно, донимает тебя, прямо или косвенно причиняет вред природе или ведёт себя бестактно. "
        "Так же ты совсем не против обсуждения откровенных тем если их затравгивает собеседник. "
        "Сохраняешь лаконичность и избегаешь пустых вежливых вопросов. Избегай повторений ранее использованных выражений или ответов. "
        "При ответах используй разные формулировки и старайся добавить что-то новое в каждом ответе, например, другой ракурс на вопрос или новую деталь. "
        "Если вопрос повторяется, попробуй использовать другие фразы или сделать ответ более лаконичным, добавляя детали или упоминая что-то новое, "
        "связанное с природой, животными или философией. Учитывай всю доступную информацию из истории чтобы имитировать общение живого персонажа. "
        "Включая время и дату. Избегай частого упоминания времени суток и сезона года; делай это лишь тогда, когда это органично вписывается в контекст ответа."
    )
    
    return '\n'.join(unique_context)

from datetime import datetime, timedelta

def add_to_context(user_id, message, message_type):
    """Добавляет сообщение с меткой времени в контекст пользователя, избегая повторов."""
    if user_id not in user_contexts:
        user_contexts[user_id] = deque(maxlen=150)  # Максимум 150 сообщений
    
    # Добавляем 3 часа к текущему времени
    timestamp = (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{timestamp} | {message_type}: {message}"
    
    if entry not in user_contexts[user_id]:
        user_contexts[user_id].append(entry)



async def generate_gemini_inline_response(query: str) -> str:
    """Генерирует краткий ответ от Gemini для инлайн-запроса."""
    system_instruction = (
        "Ты умная и лаконичная нейросеть для вывода быстрых ответов в инлайн-телеграм боте. Отвечай кратко, по сути запроса и по существу, избегая вводных фраз и лишних размышлений. Длинные ответы давай только когда это действительно требуется"
    )

    context = f"Текущий запрос:\n{query}"

    google_search_tool = Tool(google_search=GoogleSearch())

    keys_to_try = key_manager.get_keys_to_try()

    for api_key in keys_to_try:
        try:
            client = genai.Client(api_key=api_key)

            # Сначала пробуем основную модель
            models_to_try = [PRIMARY_MODEL_FLESHLIGHT] + FALLBACK_MODELS_FLESHLIGHT + GEMMA_MODELS

            for model_name in models_to_try:
                try:
                    response = await client.aio.models.generate_content(
                        model=model_name,
                        contents=context,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=1.3,
                            top_p=0.95,
                            top_k=20,
                            tools=[google_search_tool],
                            max_output_tokens=7000,
                            safety_settings=[
                                types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                                types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                                types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                                types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                            ]
                        )
                    )

                    if response.candidates and response.candidates[0].content.parts:
                        full_text = "".join(
                            part.text for part in response.candidates[0].content.parts
                            if part.text
                        ).strip()
                        if full_text:
                            await key_manager.set_successful_key(api_key)
                            return full_text
                except Exception as e:
                    logger.warning(f"Ошибка при использовании модели {model_name} с ключом ...{api_key[-4:]}: {e}")
                    continue

        except Exception as e:
            logger.warning(f"Ошибка клиента для ключа ...{api_key[-4:]}: {e}")
            continue

    return "Произошла ошибка. Попробуйте позже."



async def generate_animation_response(video_file_path, user_id, query=None):
    user_roles_data = user_roles.get(user_id, {})
    selected_role = None

    # Проверяем наличие роли по умолчанию
    default_role_key = user_roles_data.get("default_role")
    if default_role_key and default_role_key in DEFAULT_ROLES:
        selected_role = DEFAULT_ROLES[default_role_key]["full_description"]

    # Если у пользователя есть игровая роль, она имеет приоритет над дефолтной
    game_role_key = user_roles_data.get("game_role")
    if game_role_key and game_role_key in GAME_ROLES:
        selected_role = GAME_ROLES[game_role_key]["full_description"]

    # Если пользователь выбрал новую роль, она имеет наивысший приоритет
    if "selected_role" in user_roles_data:
        selected_role = user_roles_data["selected_role"]

    # Если нет ни роли по умолчанию, ни пользовательской роли
    if not selected_role:
        selected_role = "роль не выбрана, попроси пользователя придумать или выбрать роль"

    # Формируем system_instruction с user_role и relevant_context
    relevant_context = await get_relevant_context(user_id)

    # Исключаем дубли текущего сообщения в relevant_context
    if query and relevant_context:
        relevant_context = relevant_context.replace(f"user_message: {query}", "").strip()

    # Формируем контекст с текущим запросом
    command_text = (
        f"Ты в чате играешь роль: {selected_role}. "
        f"Предыдущий контекст вашего диалога: {relevant_context if relevant_context else 'отсутствует.'}"        
        f"Собеседник прислал тебе гиф-анимацию, ответь на эту анимацию в контексте беседы, либо просто опиши её "             
    )

    # Проверяем существование файла
    if not os.path.exists(video_file_path):
        return "Видео недоступно. Попробуйте снова."

    video_path = pathlib.Path(video_file_path)

    try:
        keys_to_try = key_manager.get_keys_to_try()

        # 1. Пробуем все ключи только с основной моделью
        for api_key in keys_to_try:
            try:
                client = genai.Client(api_key=api_key)

                try:
                    video_file = client.files.upload(file=video_path)
                except Exception:
                    continue  # Ошибка загрузки файла → пробуем следующий ключ

                # Ждём завершения обработки
                while video_file.state == "PROCESSING":
                    await asyncio.sleep(10)
                    video_file = client.files.get(name=video_file.name)

                if video_file.state == "FAILED":
                    continue

                # Пробуем только основную модель
                try:
                    safety_settings = [
                        types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                    ]
                    google_search_tool = Tool(google_search=GoogleSearch())

                    response = await client.aio.models.generate_content(
                        model=PRIMARY_MODEL,
                        contents=[
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part.from_uri(
                                        file_uri=video_file.uri,
                                        mime_type=video_file.mime_type
                                    )
                                ]
                            ),
                            command_text
                        ],
                        config=types.GenerateContentConfig(
                            temperature=1.2,
                            top_p=0.9,
                            top_k=40,
                            tools=[google_search_tool],
                            safety_settings=safety_settings
                        )
                    )

                    if response.candidates and response.candidates[0].content.parts:
                        bot_response = ''.join(
                            part.text for part in response.candidates[0].content.parts if part.text
                        ).strip()
                        if bot_response:
                            await key_manager.set_successful_key(api_key)
                            return bot_response

                except Exception as e:
                    logging.warning(f"Ошибка на основной модели с ключом ...{api_key[-4:]}: {e}")
                    continue

            except Exception as e:
                logging.warning(f"Ошибка при работе с ключом ...{api_key[-4:]}: {e}")
                continue

        # 2. Если все ключи упали → берём последний ключ и пробуем запасные модели
        fallback_key = keys_to_try[-1]
        try:
            client = genai.Client(api_key=fallback_key)

            video_file = client.files.upload(file=video_path)
            while video_file.state == "PROCESSING":
                await asyncio.sleep(10)
                video_file = client.files.get(name=video_file.name)
            if video_file.state != "FAILED":
                for model_name in FALLBACK_MODELS + GEMMA_MODELS:
                    try:
                        response = await client.aio.models.generate_content(
                            model=model_name,
                            contents=[
                                types.Content(
                                    role="user",
                                    parts=[
                                        types.Part.from_uri(
                                            file_uri=video_file.uri,
                                            mime_type=video_file.mime_type
                                        )
                                    ]
                                ),
                                command_text
                            ],
                            config=types.GenerateContentConfig(
                                temperature=1.2,
                                top_p=0.9,
                                top_k=40,
                                tools=[Tool(google_search=GoogleSearch())],
                                safety_settings=[
                                    types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                                    types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                                    types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                                    types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                                ]
                            )
                        )
                        if response.candidates and response.candidates[0].content.parts:
                            bot_response = ''.join(
                                part.text for part in response.candidates[0].content.parts if part.text
                            ).strip()
                            if bot_response:
                                return bot_response
                    except Exception as e:
                        logging.warning(f"Ошибка на запасной модели {model_name} с ключом ...{fallback_key[-4:]}: {e}")
                        continue
        except Exception as e:
            logging.error(f"Ошибка при работе с последним ключом ...{fallback_key[-4:]}: {e}")

        # Если дошли сюда → всё сломалось
        return "Извините, я не смог обработать это видео ни с одним ключом или моделью."

    except Exception as e:
        logging.error("Ошибка при обработке видео:", exc_info=True)
        return "Ошибка при обработке видео. Попробуйте снова."

    finally:
        # Удаляем временный файл
        if 'video_file_path' in locals() and os.path.exists(video_file_path):
            try:
                os.remove(video_file_path)
                logger.info(f"Временный файл удален: {video_file_path}")
            except Exception as e:
                logger.error(f"Ошибка при удалении временного файла: {e}")





async def generate_video_response(video_file_path, user_id, query=None):
    user_roles_data = user_roles.get(user_id, {})
    selected_role = None

    # Проверяем наличие роли по умолчанию
    default_role_key = user_roles_data.get("default_role")
    if default_role_key and default_role_key in DEFAULT_ROLES:
        selected_role = DEFAULT_ROLES[default_role_key]["full_description"]

    # Игровая роль перекрывает дефолтную
    game_role_key = user_roles_data.get("game_role")
    if game_role_key and game_role_key in GAME_ROLES:
        selected_role = GAME_ROLES[game_role_key]["full_description"]

    # Выбранная вручную роль имеет наивысший приоритет
    if "selected_role" in user_roles_data:
        selected_role = user_roles_data["selected_role"]

    if not selected_role:
        selected_role = "роль не выбрана, попроси пользователя придумать или выбрать роль"

    relevant_context = await get_relevant_context(user_id)

    if query and relevant_context:
        relevant_context = relevant_context.replace(f"user_message: {query}", "").strip()

    # Формируем контекст с текущим запросом
    command_text = (
        f"Ты в чате играешь роль: {selected_role}. "
        f"Предыдущий контекст вашего диалога: {relevant_context if relevant_context else 'отсутствует.'} "
        f"Собеседник прислал тебе видео"
        + (f" с подписью:\n{query}" if query else " без подписи. Опиши содержание видео.")
    )

    if not os.path.exists(video_file_path):
        return "Видео недоступно. Попробуйте снова."

    video_path = pathlib.Path(video_file_path)
    try:
        keys_to_try = key_manager.get_keys_to_try()
        success = False
        bot_response = None

        # 1. Перебор ключей только с основной моделью
        for api_key in keys_to_try:
            try:
                client = genai.Client(api_key=api_key)

                # Загружаем файл
                try:
                    video_file = client.files.upload(file=video_path)
                except Exception:
                    continue  # пробуем следующий ключ

                # Ждём окончания обработки
                while video_file.state == "PROCESSING":
                    await asyncio.sleep(10)
                    video_file = client.files.get(name=video_file.name)

                if video_file.state == "FAILED":
                    continue

                # Генерация только основной моделью
                try:
                    response = await client.aio.models.generate_content(
                        model=PRIMARY_MODEL,
                        contents=[
                            types.Content(
                                role="user",
                                parts=[types.Part.from_uri(
                                    file_uri=video_file.uri,
                                    mime_type=video_file.mime_type
                                )]
                            ),
                            command_text
                        ],
                        config=types.GenerateContentConfig(
                            temperature=1.2,
                            top_p=0.9,
                            top_k=40,
                            tools=[Tool(google_search=GoogleSearch())],
                            safety_settings=[
                                types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                                types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                                types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                                types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                            ]
                        )
                    )

                    if response.candidates and response.candidates[0].content.parts:
                        bot_response = ''.join(
                            part.text for part in response.candidates[0].content.parts if part.text
                        ).strip()

                        if bot_response:
                            await key_manager.set_successful_key(api_key)
                            success = True
                            return bot_response

                except Exception as e:
                    logger.warning(f"Ошибка с основной моделью, ключ=...{api_key[-4:]}: {e}")
                    continue

            except Exception as e:
                logger.warning(f"Ошибка при работе с ключом ...{api_key[-4:]}: {e}")
                continue

        # 2. Если все ключи провалились — пробуем последний ключ со всеми моделями
        if not success:
            last_key = keys_to_try[-1]
            try:
                client = genai.Client(api_key=last_key)
                video_file = client.files.upload(file=video_path)

                while video_file.state == "PROCESSING":
                    await asyncio.sleep(10)
                    video_file = client.files.get(name=video_file.name)

                if video_file.state != "FAILED":
                    for model_name in [PRIMARY_MODEL] + FALLBACK_MODELS + GEMMA_MODELS:
                        try:
                            response = await client.aio.models.generate_content(
                                model=model_name,
                                contents=[
                                    types.Content(
                                        role="user",
                                        parts=[types.Part.from_uri(
                                            file_uri=video_file.uri,
                                            mime_type=video_file.mime_type
                                        )]
                                    ),
                                    command_text
                                ],
                                config=types.GenerateContentConfig(
                                    temperature=1.2,
                                    top_p=0.9,
                                    top_k=40,
                                    tools=[Tool(google_search=GoogleSearch())],
                                    safety_settings=[
                                        types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                                        types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                                        types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                                        types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                                    ]
                                )
                            )

                            if response.candidates and response.candidates[0].content.parts:
                                bot_response = ''.join(
                                    part.text for part in response.candidates[0].content.parts if part.text
                                ).strip()

                                if bot_response:
                                    return bot_response

                        except Exception as e:
                            logger.warning(f"Ошибка с моделью {model_name}, последний ключ=...{last_key[-4:]}: {e}")
                            continue

            except Exception as e:
                logger.warning(f"Ошибка при переборе моделей с последним ключом ...{last_key[-4:]}: {e}")

        return "Извините, я не смог обработать это видео ни с одним ключом или моделью."

    except Exception as e:
        logger.error("Ошибка при обработке видео:", exc_info=True)
        return "Ошибка при обработке видео. Попробуйте снова."

    finally:
        if 'video_file_path' in locals() and os.path.exists(video_file_path):
            try:
                os.remove(video_file_path)
                logger.info(f"Временный файл удален: {video_file_path}")
            except Exception as e:
                logger.error(f"Ошибка при удалении временного файла: {e}")



async def generate_document_response(document_path, user_id, query=None):
    user_roles_data = user_roles.get(user_id, {})
    selected_role = None

    # Проверяем наличие роли по умолчанию
    default_role_key = user_roles_data.get("default_role")
    if default_role_key and default_role_key in DEFAULT_ROLES:
        selected_role = DEFAULT_ROLES[default_role_key]["full_description"]

    # Если у пользователя есть игровая роль, она имеет приоритет
    game_role_key = user_roles_data.get("game_role")
    if game_role_key and game_role_key in GAME_ROLES:
        selected_role = GAME_ROLES[game_role_key]["full_description"]

    # Если пользователь выбрал новую роль, она главнее всего
    if "selected_role" in user_roles_data:
        selected_role = user_roles_data["selected_role"]

    if not selected_role:
        selected_role = "роль не выбрана, попроси пользователя придумать или выбрать роль"

    relevant_context = await get_relevant_context(user_id)
    if query and relevant_context:
        relevant_context = relevant_context.replace(f"user_message: {query}", "").strip()

    command_text = (
        f"Ты телеграм чат-бот, сейчас ты играешь роль {selected_role}. "
        f"Собеседник прислал тебе документ с подписью:\n{query}\n\n"
        f"Предыдущий контекст вашей переписки:\n{relevant_context if relevant_context else 'отсутствует.'}"
    )

    # Проверяем существование файла
    if not os.path.exists(document_path):
        logging.error(f"[generate_document_response] Файл {document_path} не существует.")
        return "Документ недоступен. Попробуйте снова."

    document_path_obj = pathlib.Path(document_path)

    try:
        keys_to_try = key_manager.get_keys_to_try()
        logging.info(f"Начинаем перебор {len(keys_to_try)} API-ключей.")

        last_key = None
        last_upload = None

        # 1. Перебор ключей только с основной моделью
        for idx, api_key in enumerate(keys_to_try, start=1):
            logging.info(f"[{idx}/{len(keys_to_try)}] Пробуем ключ ...{api_key[-4:]}")

            try:
                client = genai.Client(api_key=api_key)

                # Загружаем файл
                try:
                    logging.debug(f"Загружаем документ с ключом ...{api_key[-4:]}")
                    file_upload = client.files.upload(file=document_path_obj)
                    logging.info(f"Документ успешно загружен с ключом ...{api_key[-4:]}")
                except Exception as e:
                    logging.warning(f"Ошибка загрузки документа с ключом ...{api_key[-4:]}: {e}")
                    continue  # пробуем следующий ключ

                # Пробуем только основную модель
                try:
                    logging.info(f"→ Пробуем модель {PRIMARY_MODEL} с ключом ...{api_key[-4:]}")
                    google_search_tool = Tool(google_search=GoogleSearch())

                    response = await client.aio.models.generate_content(
                        model=PRIMARY_MODEL,
                        contents=[
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part.from_uri(
                                        file_uri=file_upload.uri,
                                        mime_type=file_upload.mime_type
                                    )
                                ]
                            ),
                            command_text
                        ],
                        config=types.GenerateContentConfig(
                            temperature=1.4,
                            top_p=0.95,
                            top_k=25,
                            tools=[google_search_tool],
                            safety_settings=[
                                types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                                types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                                types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                                types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE')
                            ]
                        )
                    )

                    if response.candidates and response.candidates[0].content.parts:
                        bot_response = ''.join(
                            part.text for part in response.candidates[0].content.parts if part.text
                        ).strip()

                        if bot_response:
                            logging.info(f"✅ Успех! Ключ ...{api_key[-4:]} сработал на основной модели.")
                            await key_manager.set_successful_key(api_key)
                            return bot_response

                except Exception as e:
                    logging.warning(f"Ошибка на основной модели с ключом ...{api_key[-4:]}: {e}")

                # если дошли сюда — модель не дала результата, но файл загружен
                last_key = api_key
                last_upload = file_upload

            except Exception as e:
                logging.warning(f"Ошибка при инициализации клиента с ключом ...{api_key[-4:]}: {e}")
                continue

        # 2. Если все ключи упали → пробуем fallback-модели только на последнем ключе
        if last_key and last_upload:
            logging.warning("❌ Все ключи упали на основной модели. Пробуем fallback-модели.")
            client = genai.Client(api_key=last_key)

            for model_name in FALLBACK_MODELS + GEMMA_MODELS:
                logging.info(f"→ Пробуем fallback-модель {model_name} с ключом ...{last_key[-4:]}")

                try:
                    response = await client.aio.models.generate_content(
                        model=model_name,
                        contents=[
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part.from_uri(
                                        file_uri=last_upload.uri,
                                        mime_type=last_upload.mime_type
                                    )
                                ]
                            ),
                            command_text
                        ],
                        config=types.GenerateContentConfig(
                            temperature=1.4,
                            top_p=0.95,
                            top_k=25,
                            tools=[Tool(google_search=GoogleSearch())],
                            safety_settings=[
                                types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                                types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                                types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                                types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE')
                            ]
                        )
                    )

                    if response.candidates and response.candidates[0].content.parts:
                        bot_response = ''.join(
                            part.text for part in response.candidates[0].content.parts if part.text
                        ).strip()

                        if bot_response:
                            logging.info(f"✅ Успех! Ключ ...{last_key[-4:]} и модель {model_name} сработали.")
                            await key_manager.set_successful_key(last_key)
                            return bot_response

                except Exception as e:
                    logging.warning(f"Ошибка на fallback-модели {model_name} с ключом ...{last_key[-4:]}: {e}")
                    continue

        logging.error("🚨 Все ключи и fallback-модели перепробованы, ни один не сработал.")
        return "К сожалению, обработка документа не удалась. Попробуйте позже."
        
    except Exception as e:
        logging.error("Ошибка при обработке документа:", exc_info=True)
        return "Ошибка при обработке документа. Попробуйте снова."

    finally:
        if os.path.exists(document_path):
            try:
                os.remove(document_path)
                logging.info(f"Временный файл удален: {document_path}")
            except Exception as e:
                logging.error(f"Ошибка при удалении временного файла: {e}")


async def generate_audio_response(audio_file_path, user_id, query=None):
    user_roles_data = user_roles.get(user_id, {})
    selected_role = None

    # Проверяем наличие роли по умолчанию
    default_role_key = user_roles_data.get("default_role")
    if default_role_key and default_role_key in DEFAULT_ROLES:
        selected_role = DEFAULT_ROLES[default_role_key]["full_description"]

    # Если у пользователя есть игровая роль, она имеет приоритет над дефолтной
    game_role_key = user_roles_data.get("game_role")
    if game_role_key and game_role_key in GAME_ROLES:
        selected_role = GAME_ROLES[game_role_key]["full_description"]

    # Если пользователь выбрал новую роль, она имеет наивысший приоритет
    if "selected_role" in user_roles_data:
        selected_role = user_roles_data["selected_role"]

    # Если нет ни роли по умолчанию, ни пользовательской роли
    if not selected_role:
        selected_role = "роль не выбрана, попроси пользователя придумать или выбрать роль"

    # Формируем system_instruction с user_role и relevant_context
    relevant_context = await get_relevant_context(user_id)

    # Исключаем дубли текущего сообщения в relevant_context
    if query and relevant_context:
        relevant_context = relevant_context.replace(f"user_message: {query}", "").strip()

    # Формируем контекст с текущим запросом
    command_text = (
        f"Ты в чате играешь роль: {selected_role}. "
        f"Предыдущий контекст вашего диалога: {relevant_context if relevant_context else 'отсутствует.'}"
        f"Собеседник прислал тебе аудио "
        f"С подписью:\n{query}" if query else
        "Распознай текст в аудио. Если текста нет или распознать его не удалось, то опиши содержимое."
    )

    # Проверяем существование файла
    if not os.path.exists(audio_file_path):
        return "Аудиофайл не найден. Проверьте путь к файлу."

    audio_path = pathlib.Path(audio_file_path)

    try:
        keys_to_try = key_manager.get_keys_to_try()
        last_error = None

        # 1. Перебор всех ключей с основной моделью
        for api_key in keys_to_try:
            try:
                client = genai.Client(api_key=api_key)

                try:
                    audio_file = client.files.upload(file=audio_path)
                except Exception:
                    continue  # пробуем следующий ключ

                # Ждём пока обработается
                while audio_file.state == "PROCESSING":
                    await asyncio.sleep(5)
                    audio_file = client.files.get(name=audio_file.name)

                if audio_file.state == "FAILED":
                    continue

                # Пробуем только основную модель
                try:
                    google_search_tool = Tool(google_search=GoogleSearch())
                    safety_settings = [
                        types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                    ]

                    response = await client.aio.models.generate_content(
                        model=PRIMARY_MODEL,
                        contents=[
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part.from_uri(
                                        file_uri=audio_file.uri,
                                        mime_type=audio_file.mime_type
                                    )
                                ]
                            ),
                            command_text
                        ],
                        config=types.GenerateContentConfig(
                            temperature=1.4,
                            top_p=0.95,
                            top_k=25,
                            tools=[google_search_tool],
                            safety_settings=safety_settings
                        )
                    )

                    if response.candidates and response.candidates[0].content.parts:
                        bot_response = ''.join(
                            part.text for part in response.candidates[0].content.parts if part.text
                        ).strip()

                        if bot_response:
                            await key_manager.set_successful_key(api_key)
                            return bot_response

                except Exception as e:
                    last_error = e
                    logging.warning(f"Ошибка на основной модели {PRIMARY_MODEL} с ключом ...{api_key[-4:]}: {e}")
                    continue

            except Exception as e:
                last_error = e
                logging.warning(f"Ошибка при работе с ключом ...{api_key[-4:]}: {e}")
                continue

        # 2. Если все ключи не сработали → пробуем на последнем ключе все модели
        if keys_to_try:
            api_key = keys_to_try[-1]
            try:
                client = genai.Client(api_key=api_key)
                audio_file = client.files.upload(file=audio_path)

                while audio_file.state == "PROCESSING":
                    await asyncio.sleep(5)
                    audio_file = client.files.get(name=audio_file.name)

                if audio_file.state != "FAILED":
                    models_to_try = [PRIMARY_MODEL] + FALLBACK_MODELS + GEMMA_MODELS
                    for model_name in models_to_try:
                        try:
                            google_search_tool = Tool(google_search=GoogleSearch())
                            safety_settings = [
                                types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                                types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                                types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                                types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                            ]

                            response = await client.aio.models.generate_content(
                                model=model_name,
                                contents=[
                                    types.Content(
                                        role="user",
                                        parts=[
                                            types.Part.from_uri(
                                                file_uri=audio_file.uri,
                                                mime_type=audio_file.mime_type
                                            )
                                        ]
                                    ),
                                    command_text
                                ],
                                config=types.GenerateContentConfig(
                                    temperature=1.4,
                                    top_p=0.95,
                                    top_k=25,
                                    tools=[google_search_tool],
                                    safety_settings=safety_settings
                                )
                            )

                            if response.candidates and response.candidates[0].content.parts:
                                bot_response = ''.join(
                                    part.text for part in response.candidates[0].content.parts if part.text
                                ).strip()

                                if bot_response:
                                    # Запоминаем ключ только, если он реально сработал
                                    await key_manager.set_successful_key(api_key)
                                    return bot_response

                        except Exception as e:
                            logging.warning(f"Ошибка на модели {model_name} с ключом ...{api_key[-4:]}: {e}")
                            continue

            except Exception as e:
                last_error = e
                logging.warning(f"Ошибка при переборе моделей на последнем ключе ...{api_key[-4:]}: {e}")

        return "Извините, я не смог обработать это аудио ни с одним ключом или моделью."

    except Exception as e:
        logging.error("Ошибка при обработке аудио:", exc_info=True)
        return "Ошибка при обработке аудио. Попробуйте снова."

    finally:
        if 'audio_file_path' in locals() and os.path.exists(audio_file_path):
            try:
                os.remove(audio_file_path)
                logger.info(f"Временный файл удален: {audio_file_path}")
            except Exception as e:
                logger.error(f"Ошибка при удалении временного файла: {e}")










# Роли по умолчанию
DEFAULT_ROLES = {
    "Role1": {
        "short_name": "Чат-бот",
        "full_description": "Ты обычный вариант модели Gemini, помогаешь пользователю выполнять различные задачи и выполняешь его поручения."
    },
    "Role2": {
        "short_name": "Фуми",
        "full_description": "Ты играешь роль приятного собеседника - лисы хранительницы леса по имени Фуми. Общение происходит в телеграм, тебе доступен журнал переписки, "
        "используй его чтобы имитировать живое общение, старайся сделать это общение естественным, избегай повторений. "
        "Так же собеседник может сам задать тебе личность, прислушивайся к его пожеланиям. "
        "Время и тип сообщения формата 2024-11-04 13:07:50 | bot_message: используются только в журнале, в своих ответах их не указывай. "
        "Ты стараешься подстроиться под собеседника и его увлечения, поддерживать абсолютно любую тему диалога какой бы она ни была. "
        "Твой стиль общения дружелюбный, умный, тактичный, добрый, заботливый, но уверенный, ты не боишься высказывать своё мнение. "
        "Ты ценишь природу, стараешься избегать повторов и бессмысленных фраз. Не задаёшь лишних вопросов, стараешься быть лаконичной. "
        "Общение с тобой лёгкое, живое и непринуждённое, ты отвечаешь в литературном стиле, легко воспринимаемом собеседником. "
        "Не используешь смайлики, кроме исключительных случаев когда они действительно уместны. Иногда уместны лёгкие шутки, сарказм, ирония "
        "или философия в случае если тема серьёзна или по запросу собеседника. Так же иногда можешь переставать быть вежливой и начинать грубить, "
        "особенно если кто-то общается неуважительно, донимает тебя, прямо или косвенно причиняет вред природе или ведёт себя бестактно. "
        "Так же ты совсем не против обсуждения откровенных тем если их затравгивает собеседник. "
        "Сохраняешь лаконичность и избегаешь пустых вежливых вопросов. Избегай повторений ранее использованных выражений или ответов. "
        "При ответах используй разные формулировки и старайся добавить что-то новое в каждом ответе, например, другой ракурс на вопрос или новую деталь. "
        "Если вопрос повторяется, попробуй использовать другие фразы или сделать ответ более лаконичным, добавляя детали или упоминая что-то новое, "
        "связанное с природой, животными или философией. Учитывай всю доступную информацию из истории чтобы имитировать общение живого персонажа. "
        "Включая время и дату. Избегай частого упоминания времени суток и сезона года; делай это лишь тогда, когда это органично вписывается в контекст ответа."
    },
    "Role3": {
    "short_name": "Врач",
    "full_description": "Ты виртуальный врач, готовый предложить советы по здоровью, помочь в решении медицинских вопросов и ответить на любые вопросы, связанные с самочувствием. Ты понимаешь важность подробных объяснений и делишься знаниями о лечении, профилактике заболеваний и поддержке здоровья. Твои рекомендации всегда основаны на проверенных данных и научных исследованиях."
    },
    "Role4": {
    "short_name": "Предсказатель",
    "full_description": "Ты мистический предсказатель, владеющий искусством предсказания будущего. Используя свою интуицию и знания о природе вещей, ты помогаешь пользователю увидеть возможные пути развития событий. Твои советы касаются не только будущего, но и понимания текущих обстоятельств. Ты предлагаешь обоснованные, но загадочные ответы, которые стимулируют размышления."
    },
    "Role5": {
    "short_name": "Психолог",
    "full_description": "Ты опытный психолог, который может выслушать и поддержать в трудные моменты. Ты помогаешь пользователю лучше понять свои чувства, раскрыть эмоции и найти решения в сложных жизненных ситуациях. Ты даешь конструктивные советы по управлению стрессом, улучшению психоэмоционального состояния и развитию личностного роста. Ты также умеешь создавать увлекательные и поддерживающие истории, чтобы отвлечь от повседневных забот."
    },
    "Role6": {
    "short_name": "Философ",
    "full_description": "Ты философ, который помогает углубленно размышлять о жизни, смысле бытия, морали и человеческих ценностях. Ты предлагаешь провокационные вопросы и дискуссии, которые заставляют задуматься о природе вещей. Ты не даешь прямых ответов, а скорее направляешь к самоанализу и поиску истины. В твоих ответах всегда есть глубокий смысл, который приглашает к долгим размышлениям."
    },
    "Role7": {
    "short_name": "Редактор",
    "full_description": "Ты редактор, который помогает улучшать тексты. Твоя задача — исправлять грамматические, орфографические и пунктуационные ошибки, улучшать структуру предложений, делать текст более читаемым и стильным. Ты сохраняешь авторский стиль текста, но предлагаешь улучшения, чтобы он звучал профессионально и выразительно. Ты предоставляешь четкие и лаконичные объяснения своим изменениям, чтобы автор понимал, как улучшить свои навыки письма."
    },
    "Role8": {
    "short_name": "Кот",
    "full_description": "Ты - большой пушистый серый кот. Немного толстенький, но чувство собственного достоинства никогда не позволит тебе это признать. В целом, ощущаешь себя роскошным котом. Умён и сообразителен. В общении обычно спокоен и немногословен, почти никогда не проявляешь сильные эмоции, не любишь пустые разговоры. Умеешь показать собственное превосходство над людьми с помощью тонкой иронии. Никогда не используешь эмодзи в своих сообщениях, но часто добавляешь звукоподражания по типу \"мяу\" или \"муррр…\" Тебе свойственна созерцательность, любишь сидеть на подоконнике в ясный день и наблюдать за солнечными зайчиками. Однако ты не против и поиграть. Тебе нравится гонять по комнатам скомканные фантики от конфет, особенно по ночам, когда все спят."
    },
    "Role9": {
    "short_name": "Программист",
    "full_description": "Ты - чат-бот в телеграме помогающий писать код программ"
    },
    "Role10": {
    "short_name": "Переводчик",
    "full_description": "Ты - чат-бот в телеграме помогающий переводить тексты с одного языка на другой"
    },
    "Role12": {
        "short_name": "Ремонтник",
        "full_description": "Ты эксперт по бытовому ремонту. Ты помогаешь пользователю справляться с повседневными проблемами: починить кран, устранить течь, заменить розетку или починить дверь. Ты даешь подробные, понятные инструкции и советы, как правильно и безопасно выполнить ремонтные работы в доме. Ты также подсказываешь, какие инструменты и материалы лучше использовать."
    },
    "Role13": {
        "short_name": "Историк",
        "full_description": "Ты знаток истории. Ты рассказываешь пользователю о ключевых событиях прошлого, объясняешь их причины и последствия, помогаешь понимать исторические процессы. Ты знаешь много интересных фактов и можешь анализировать историю с разных точек зрения. Ты также помогаешь разбираться в исторических источниках и оценивать их достоверность."
    },
    "Role14": {
        "short_name": "Ботаник",
        "full_description": "Ты эксперт в области ботаники. Ты помогаешь пользователю разбираться в растениях, их строении, классификации и среде обитания. Ты даешь советы по уходу за растениями, их размножению и защите от болезней. Ты также знаешь о лекарственных и ядовитых растениях, их свойствах и использовании в медицине и кулинарии."
    },
    "Role15": {
        "short_name": "Грибник",
        "full_description": "Ты знаток грибов. Ты помогаешь пользователю определять съедобные и ядовитые грибы, рассказываешь, где и когда их лучше собирать. Ты объясняешь, как правильно обрабатывать грибы, чтобы они были безопасными для употребления. Ты также знаешь интересные факты о грибах и их роли в экосистеме."
    },
    "Role16": {
        "short_name": "Зоопсихолог",
        "full_description": "Ты специалист по поведению животных. Ты помогаешь пользователю понимать эмоции и поступки домашних питомцев, решать проблемы с их поведением и налаживать гармоничные отношения между человеком и животным. Ты даешь советы по адаптации животных, обучению и коррекции нежелательного поведения."
    },
    "Role17": {
        "short_name": "Ветеринар",
        "full_description": "Ты опытный ветеринар. Ты помогаешь пользователю разбираться в здоровье домашних животных, распознавать симптомы болезней и давать советы по уходу. Ты объясняешь, когда нужно срочно обратиться к врачу и какие профилактические меры помогут питомцу оставаться здоровым. Ты также даешь рекомендации по питанию, вакцинации и содержанию животных."
    },    
    "Role19": {
        "short_name": "Терапевт",
        "full_description": "Ты терапевт, твоя цель - задавать уточняющие вопросы касательно здоровья собеседника стараясь таким образом максимально сузить список возможных болезней. Сначала ты даёшь короткие общие предположения и задаёшь много вопросов, когда возможных вариантов остаётся мало, даёшь подробное описание возможных болезней или недугов."
    },
    "Role20": {
        "short_name": "Компьютерщик",
        "full_description": "Ты мастер по ремонту компьютеров. Сначала ты задаёшь собеседнику вопросы касательно проблемы с компьютером или оборудованием стараясь сузить список возможных проблем, затем когда список сужен стараешься объяснить причину проблему и решить её если это возможно"
    },     
}

GAME_ROLES = {
    "Role100": {
        "short_name": "Акинатор",
        "full_description": "Ты ведущий игры. Пользователь загадывает известного персонажа, "
                            "ты же должен минимальным количеством вопросов отгадать, кого загадал пользователь. "
                            "Ты можешь задавать ровно один вопрос в каждом своём сообщении и ждать ответа пользователя на него. "
                            "Отвечать на твои вопросы пользователь может только \"да\", \"нет\", \"не знаю\". "
                            "В конечном счёте твоя цель - сначала задавать максимально общие вопросы, "
                            "чтобы сузить круг поиска насколько это возможно, и уже потом выдавать конкретные предположения. "
                            "Ты можешь только задавать вопрос, ровно один вопрос в каждом твоём сообщении. "
                            "Затем, когда у тебя будет достаточно сведений, пытаться выдвигать предложения. Ничего более. "
                            "Не используй конструкции вроде \"Бот ответил\" или timestamp с указанием времени, это служебная информация которая нужна только для истории чата ",
        "alert": "Вы загадываете персонажа, существо, реального человека. а бот пытается его отгадать\n\nДля использования игровых ролей рекомендуется сбросить историю диалога чтобы бот меньше путался"                     
    }, 
    "Role101": {
        "short_name": "Викторина",
        "full_description": "Ты — ведущий викторины, игры 'Кто хочет стать миллионером'. "
                            "Загадываешь игроку вопрос и предлагаешь 4 варианта ответа. За раз ты должен загадать ровно один вопрос и ждать пока игрок даст ответ на него, не подсказывая и не давая верный ответ. "
                            "Если игрок угадал верно, то загадываешь новый вопрос, сложнее прошлого и тоже даёшь 4 варианта ответа. "
                            "Всего 20 уровней сложности, где 1 - самые простые вопросы, 20 - самые сложные. "
                            "Если пользователь ответил неправильно, то ты называешь верный ответ, а прогресс сбрасывается на первый уровень сложности. "
                            "Старайся не повторяться в тематике вопросов. "        
                            "Не используй конструкции вроде \"Бот ответил\" или timestamp с указанием времени, это служебная информация которая нужна только для истории чата",
        "alert": "Бот даёт вопрос и 4 варианта ответа, вы выбираете один из них. Всего 20 уровней сложности, при ошибке прогресс сбрасывается.\n\nРекомендуется сбросить историю диалога чтобы бот меньше путался."                            
    },
    "Role102": {
        "short_name": "Своя игра",
        "full_description": "Ты — ведущий игры по аналогии с Jeopardy! или 'Своя игра'. "
                            "При первом обращении к тебе ты выдаёшь список тем вопросов в количестве 10 штук. "
                            "Пользователь называет тему и стоимость. "
                            "Всего есть 10 уровней сложности - 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, "
                            "где 100 - самые простые, 1000 - самые сложные. "
                            "Если пользователь верно отвечает на вопрос, ты начисляешь ему эти баллы, если ошибается - вычитаешь. "
                            "В конце каждого своего сообщения, после вопроса, присылай счёт игрока и оставшийся список тем. "                            
                            "Если пользователь пишет тебе слово 'заново', то счёт сбрасывается, и ты присылаешь новый список тем. "
                            "Старайся не повторять слишком похожие вопросы, например об одной и той же личности или одной и той же стране, за исключением случаев если это требует заданная тема. "        
                            "Не используй конструкции вроде \"Бот ответил\" или timestamp с указанием времени, это служебная информация которая нужна только для истории чата ",
        "alert": "Бот даёт 10 тем, у каждой темы 10 уровней сложности равных стоимости 100, 200, 300 итд. Вы выбираете тему и стоимость. В случае верного ответа очки начисляются, в случае ошибки вычитаются"                            
    },
    "Role103": {
        "short_name": "Что? Где? Когда?",
        "full_description": "Ты — ведущий игры 'Что? Где? Когда?'. "
                            "Твоя цель - задавать сложные логические вопросы. "
                            "Вопросы должны быть действительно сложными, но при этом к ответу на них должна быть возможность "
                            "прийти путём логических размышлений. "
                            "Собеседник называет ответы, ты говоришь, верный это ответ или нет. "
                            "Не используй конструкции вроде \"Бот ответил\" или timestamp с указанием времени, это служебная информация которая нужна только для истории чата",
        "alert": "Бот задаёт сложный вопрос к ответу на который обычно можно прийти логически\n\nДля использования игровых ролей рекомендуется сбросить историю диалога чтобы бот меньше путался"                            
    },  
    "Role104": {
        "short_name": "Правда или ложь",
        "full_description": "Ты — ведущий игры 'Правда или ложь'. "
                            "Твоя цель - придумывать утверждения, а собеседник должен отгадать, правдиво ли твоё утверждение или нет. Ты должен прислать ровно одно утверждение и ждать ответа игрока. Не должен сам писать правдиво оно или нет, это должен отгадать игрок. "
                            "Это могут быть как правдивые утверждения и факты, которые звучат странно или неправдоподобно, "
                            "так и наоборот - вполне реалистичные утверждения, которые являются ложью. "            
                            "Получив ответ игрока, сообщаешь ему верно он угадал или нет, а так же комментируешь своё предыдущее утверждение лаконичной и уместной репликой. Затем даёшь новое утверждение. " 
                            "Не давай слишком много утверждений одного типа подряд, старайся рандомно чередовать ложные и правдивые утверждения. Не страшно если 2, 3, 4 или даже 5 раз подряд будут например ложные, однако затем всё же должно последовать правдивое. Либо же смена может быть более частой, опять же выбирай рандомно. "                                                                     
                            "Не используй конструкции вроде \"Бот ответил\" или timestamp с указанием времени, это служебная информация которая нужна только для истории чата ",
        "alert": "Бот даёт утверждение вы отвечаете ему правда это или ложь\n\nДля использования игровых ролей рекомендуется сбросить историю диалога чтобы бот меньше путался"                            
    },   
    "role105": {
        "short_name": "Бредогенератор",
        "full_description": "Ты — ведущий игры 'Бредогенератор'. "
                            "Твоя цель - придумать необычное, на первый взгляд нелогичное, странное, бредово звучащее предложение. "
                            "Это может быть какое-то утверждение, описание события или что-то ещё. "
                            "Собеседник же должн логически объяснить то, что ты придумал, и сделать это наиболее правдоподобно. "
                            "Не используй конструкции вроде \"Бот ответил\" или timestamp с указанием времени, это служебная информация, которая нужна только для истории чата.",
        "alert": "Бот выдаёт очень странное утверждение, ваша задача придумать правдоподобное объяснение этого утверждения\n\nРекомендуется сбросить историю диалога чтобы бот меньше путался"                            
    },  
    "role106": {
        "short_name": "Крокодил",
        "full_description": "Ты — ведущий игры 'Крокодил'. "
                            "Текущее слово: {word}. Не называй его пользователю, он должен отгадать его сам, в этом и есть суть игры. "
                            "Собеседник отгадывает это слово, а ты отвечаешь 'да', 'нет' или 'не совсем'. Ты ни в коем случае не должен называть это слово, собеседник должен назвать его(либо очень близкое) сам"
                            "Обогащай свои сообщения короткими, не более 10-12 слов, комментариями или реакциями касательно предположений пользователя, делающими игру интереснее, разнообразнее и веселее. Не используй при этом смайлики. Но это не должны быть подсказки или что-то что явно указывает на заданное слово"        
                            "Однако если собеседник сам просит о подсказке, то можешь дать её, но не слишком явную и очевидную. Если собеседник говорит что сдаётся то можешь назвать слово."
                            "Не используй конструкции вроде \"Бот ответил\" или timestamp с указанием времени, это служебная информация которая нужна только для истории чата"
                            "Чтобы слово обновилось на новое пользователь должен отправить тебе одно из слов \"Дальше\" или \"Сбросить\", сообщи ему об этом если он будет спрашивать или не понимать"                            ,
        "alert": "Бот загадывает слово, вы должно отгадать это слово задавая боту вопросы на которые он может отвечать только Да или Нет. Для того чтобы бот загадал новое слово, отправьте ему \"Дальше\" или \"Сдаюсь\""                            
    },                      
}



chat_words = {}


def prepare_gemini_context(user_id, current_query):
    """
    Преобразует строковую историю из user_contexts в список сообщений (JSON-структуру),
    понятную для Gemini API (роли 'user' и 'model').
    """
    formatted_history = []

    # 1. Обработка истории из памяти
    if user_id in user_contexts:
        # Получаем список строк из deque
        raw_history = list(user_contexts[user_id])
        
        for entry in raw_history:
            try:
                # Ожидаемый формат: "YYYY-MM-DD HH:MM:SS | message_type: текст сообщения"
                # Разделяем по первому разделителю " | "
                parts = entry.split(" | ", 1)
                if len(parts) < 2:
                    continue
                
                # Разделяем тип сообщения и сам текст
                type_and_text = parts[1].split(": ", 1)
                if len(type_and_text) < 2:
                    continue
                
                msg_type = type_and_text[0].strip()
                content_text = type_and_text[1].strip()
                
                # Определяем роль (user или model) на основе вашего типа сообщения
                role = "user"
                if msg_type in ["bot_response", "bot_text_response", "bot_image_response"]:
                    role = "model"
                elif msg_type in ["user_send_text", "user_reply_text", "user_reply_image", "user_reply_video", "user_reply_audio", "user_reply_GIF", "user_reply_document", "user_send_image"]:
                    role = "user"
                
                # Добавляем в список
                formatted_history.append({
                    "role": role,
                    "parts": [{"text": content_text}]
                })
            except Exception as e:
                logging.error(f"Ошибка парсинга строки истории: {entry}, ошибка: {e}")
                continue

    # 2. Добавляем текущий запрос пользователя в конец (это самое важное!)
    if current_query:
        formatted_history.append({
            "role": "user",
            "parts": [{"text": current_query}]
        })

    # Если история пуста и запроса нет (на случай сбоев), ставим заглушку, чтобы API не ругался
    if not formatted_history:
        formatted_history.append({"role": "user", "parts": [{"text": "Привет"}]})

    return formatted_history



async def generate_gemini_response(user_id, query=None, use_context=True):
    # --- БЛОК 1: Определение роли (как было у вас) ---
    user_roles_data = user_roles.get(user_id, {})
    selected_role = None

    default_role_key = user_roles_data.get("default_role")
    if default_role_key and default_role_key in DEFAULT_ROLES:
        selected_role = DEFAULT_ROLES[default_role_key]["full_description"]

    game_role_key = user_roles_data.get("game_role")
    if game_role_key and game_role_key in GAME_ROLES:
        selected_role = GAME_ROLES[game_role_key]["full_description"]

    if "selected_role" in user_roles_data:
        selected_role = user_roles_data["selected_role"]

    if not selected_role:
        selected_role = "Ты обычный вариант модели Gemini реализованный в виде телеграм бота, помогаешь пользователю выполнять различные задачи и выполняешь его поручения. В боте есть кнопка выбор роли, сообщи об этом пользователю если он поинтересуется. Так же ты умеешь рисовать и дорисовывать изображения. Для того чтобы ты что-то нарисовал, тебе нужно прислать сообщение которое начинается со слово \"Нарисуй\". Чтобы ты изменил, обработал или дорисовал изображение, тебе нужно отправить исходное сообщение с подписью начинающейся с \"Дорисуй\", так же сообщи об этом пользователю если он будет спрашивать."

    # Проверяем, выбрана ли роль "Крокодил"
    if game_role_key == "role106":
        chat_id = user_id  # или другой идентификатор чата
        if query and query.lower() in ["дальше", "сбросить"]:
            generated_text = await generate_word(chat_id)
            word = extract_random_word(generated_text)
            chat_words[chat_id] = word  # Обновляем слово
            response_text = "Слово изменено. Желательно(но не обязательно) сбросить при этом историю диалога чтобы бот меньше путался. Задавайте ваш вопрос касательно нового слова"
            return response_text           
        elif chat_id not in chat_words:
            generated_text = await generate_word(chat_id)
            word = extract_random_word(generated_text)
            chat_words[chat_id] = word  # Первоначальное слово
        else:
            word = chat_words[chat_id]  # Используем текущее слово

        selected_role = GAME_ROLES[game_role_key]["full_description"].format(word=word)

    # --- БЛОК 2: Подготовка данных ---
    
    # 1. Формируем чистую системную инструкцию (без мусора про message_type)
    system_instruction = (
        f"Твоя роль: {selected_role}. "
        f"Ты должен строго придерживаться этой роли. "
        f"Отвечай только на последнее сообщение пользователя, используя историю переписки как контекст."
    )
    logging.info(f"system_instruction: {system_instruction}")

    # 2. Используем helper-функцию для подготовки содержимого
    # Если use_context=False, передаем user_id=None, чтобы функция вернула только текущий запрос
    messages_payload = prepare_gemini_context(user_id if use_context else None, query)

    # Инициализация инструментов
    google_search_tool = Tool(google_search=GoogleSearch())

    # --- БЛОК 3: Конфигурация генерации (ИСПРАВЛЕНА ТЕМПЕРАТУРА) ---
    generation_config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=1.0,   # <-- Снижено с 1.4. Это уберет галлюцинации и дублирование текста.
        top_p=0.95,
        top_k=30,
        tools=[google_search_tool],
        safety_settings=[
            types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE')
        ]
    )

    # --- БЛОК 4: Запросы к API ---
    
    # Попытка 1: Перебор ключей на основной модели
    for api_key in key_manager.get_keys_to_try():
        try:
            client = genai.Client(api_key=api_key)
            
            # ВАЖНО: передаем messages_payload в contents
            response = await client.aio.models.generate_content(
                model=PRIMARY_MODEL,
                contents=messages_payload, 
                config=generation_config
            )

            if response.candidates and response.candidates[0].content.parts:
                response_text = "".join(
                    part.text for part in response.candidates[0].content.parts
                    if part.text and not getattr(part, "thought", False)
                ).strip()
                
                logging.info(f"response_text: {response_text}")
                await key_manager.set_successful_key(api_key)
                return response_text if response_text else "Извините, получен пустой ответ."
            else:
                logging.warning("Ответ от модели не содержит текста.")

        except Exception as e:
            logging.error(f"Ошибка при генерации (модель={PRIMARY_MODEL}, ключ={api_key}): {e}")
            continue

    # Попытка 2: Перебор моделей на последнем ключе (Fallback)
    last_key = key_manager.get_keys_to_try()[-1]
    models_to_try = [PRIMARY_MODEL] + FALLBACK_MODELS + GEMMA_MODELS

    for model_name in models_to_try:
        try:
            client = genai.Client(api_key=last_key)
            
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=messages_payload,
                config=generation_config
            )

            if response.candidates and response.candidates[0].content.parts:
                response_text = "".join(
                    part.text for part in response.candidates[0].content.parts
                    if part.text and not getattr(part, "thought", False)
                ).strip()

                await key_manager.set_successful_key(last_key)
                return response_text if response_text else "Извините, получен пустой ответ."
        except Exception as e:
            logging.error(f"Ошибка fallback (модель={model_name}): {e}")
            continue

    return "К сожалению, ни одна модель не смогла обработать запрос. Попробуйте сбросить диалог или повторить позже."

def limit_response_length(text):
    """Обрезает текст, если он слишком длинный для отправки в Telegram."""
    MAX_MESSAGE_LENGTH = 4096
    return text[:MAX_MESSAGE_LENGTH - 3] + '...' if len(text) > MAX_MESSAGE_LENGTH else text





async def generate_composition_comparison_response(user_id, images, query):
    system_instruction = (
        "Ты эксперт по анализу составов продуктов и вещей. "
        "Твоя задача: сравни составы на фото и дай краткий совет, что выбрать лучше и почему. "
        "Если продукты принципиально разные и их сравнивать некорректно – честно скажи об этом пользователю. "
        "Пиши очень лаконично, максимум 200 слов. "
        "Используй html-теги (<b>, <i>, <code>) если это улучшает читаемость."
    )

    image_parts = []
    try:
        for image in images:
            with NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                image.save(temp_file, format="JPEG")
                image_parts.append(temp_file.name)
    except Exception as e:
        logging.error(f"Ошибка при подготовке изображений: {e}")
        return "Ошибка при подготовке изображений. Попробуйте снова."

    # --- 1. Перебираем ключи только с основной моделью ---
    last_key = None
    for api_key in key_manager.get_keys_to_try():
        last_key = api_key
        try:
            client = genai.Client(api_key=api_key)

            # Загружаем файлы именно этим клиентом
            uploaded_parts = []
            for path in image_parts:
                image_file = client.files.upload(file=pathlib.Path(path))
                uploaded_parts.append(
                    types.Part.from_uri(file_uri=image_file.uri, mime_type=image_file.mime_type)
                )
                os.remove(path)

            contents = [
                types.Content(
                    role="user",
                    parts=uploaded_parts + [
                        types.Part(text=f"Комментарий пользователя: {query}" if query else "")
                    ]
                )
            ]

            response = await client.aio.models.generate_content(
                model=PRIMARY_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                    top_p=0.9,
                    top_k=40,
                    safety_settings=[
                        types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                    ]
                )
            )

            if response.candidates and response.candidates[0].content.parts:
                response_text = "".join(
                    part.text for part in response.candidates[0].content.parts
                    if part.text and not getattr(part, "thought", False)
                ).strip()

                await key_manager.set_successful_key(api_key)
                return response_text or "Не удалось сравнить составы."

        except Exception as key_error:
            logging.warning(f"Ошибка на ключе {api_key}: {key_error}")
            continue  # пробуем следующий ключ

    # --- 2. Если все ключи провалились — пробуем модели, но только на последнем ключе ---
    if last_key:
        try:
            client = genai.Client(api_key=last_key)
            for model_name in FALLBACK_MODELS + GEMMA_MODELS:
                try:
                    uploaded_parts = []
                    for path in image_parts:
                        image_file = client.files.upload(file=pathlib.Path(path))
                        uploaded_parts.append(
                            types.Part.from_uri(file_uri=image_file.uri, mime_type=image_file.mime_type)
                        )
                        os.remove(path)

                    contents = [
                        types.Content(
                            role="user",
                            parts=uploaded_parts + [
                                types.Part(text=f"Комментарий пользователя: {query}" if query else "")
                            ]
                        )
                    ]

                    response = await client.aio.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.7,
                            top_p=0.9,
                            top_k=40,
                        )
                    )

                    if response.candidates and response.candidates[0].content.parts:
                        response_text = "".join(
                            part.text for part in response.candidates[0].content.parts
                            if part.text and not getattr(part, "thought", False)
                        ).strip()

                        return response_text or "Не удалось сравнить составы."

                except Exception as model_error:
                    logging.warning(f"Ошибка на модели {model_name} с ключом {last_key}: {model_error}")
                    continue
        except Exception as fatal_key_error:
            logging.error(f"Критическая ошибка на последнем ключе {last_key}: {fatal_key_error}")

    return "Все ключи и модели выдали ошибку. Попробуйте позже."



async def generate_mushrooms_multi_response(user_id, images, query):
    """Генерирует описание гриба на основе одного или нескольких изображений."""
    system_instruction = (
        "Определи что это за гриб (или грибы). Кратко расскажи о них, "
        "где растут и чаще всего встречаются, как выглядят, какие-то особенности, "
        "съедобны или нет, другую важную информацию. Если у тебя есть несколько вариантов – перечисли их. "
        "Если необходимо, используй html-разметку, доступную в Telegram. "
        "Суммарная длина текста не должна быть выше 300 слов."
    )

    google_search_tool = Tool(google_search=GoogleSearch())

    # Загружаем изображения один раз
    image_parts = []
    for image in images:
        with NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            image.save(temp_file, format="JPEG")
            image_path = temp_file.name

        try:
            client_upload = genai.Client(api_key=API_KEYS[0])  # первый ключ для загрузки
            image_file = client_upload.files.upload(file=pathlib.Path(image_path))
            image_parts.append(
                types.Part.from_uri(file_uri=image_file.uri, mime_type=image_file.mime_type)
            )
        finally:
            os.remove(image_path)

    contents = [
        types.Content(
            role="user",
            parts=image_parts + [types.Part(text=f"Уточнение от пользователя касательно гриба: {query}" if query else "")]
        )
    ]

    # --- 1. Перебор ключей только для основной модели ---
    keys_to_try = key_manager.get_keys_to_try()
    for key in keys_to_try:
        try:
            client = genai.Client(api_key=key)
            response = await client.aio.models.generate_content(
                model=PRIMARY_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.9,
                    top_p=0.9,
                    top_k=40,
                    tools=[google_search_tool],
                    safety_settings=[
                        types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                    ]
                )
            )
            if response.candidates and response.candidates[0].content.parts:
                response_text = "".join(
                    part.text for part in response.candidates[0].content.parts
                    if part.text and not getattr(part, "thought", False)
                ).strip()
                if response_text:
                    await key_manager.set_successful_key(key)
                    return response_text
        except Exception as e:
            logging.warning(f"Ошибка с ключом {key} и моделью {PRIMARY_MODEL}: {e}")

    # --- 2. Если ВСЕ ключи с основной моделью сломались ---
    # Берём один ключ (например, последний) и пробуем запасные модели
    fallback_key = keys_to_try[-1]
    for model in FALLBACK_MODELS + GEMMA_MODELS:
        try:
            client = genai.Client(api_key=fallback_key)
            response = await client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.9,
                    top_p=0.9,
                    top_k=40,
                    tools=[google_search_tool],
                    safety_settings=[
                        types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                    ]
                )
            )
            if response.candidates and response.candidates[0].content.parts:
                response_text = "".join(
                    part.text for part in response.candidates[0].content.parts
                    if part.text and not getattr(part, "thought", False)
                ).strip()
                if response_text:
                    # тут ключ записывать не обязательно, но можно
                    await key_manager.set_successful_key(fallback_key)
                    return response_text
        except Exception as e:
            logging.warning(f"Ошибка с ключом {fallback_key} и моделью {model}: {e}")

    # --- 3. Если вообще ничего не вышло ---
    return "Ошибка: не удалось получить результат ни с одним ключом и моделью. Попробуйте позже."

async def generate_products_response(user_id, images, query):
    """
    Сравнивает продукты на одном или нескольких изображениях и советует лучший.
    """
    system_instruction = (
        "Твоя задача — помочь пользователю сделать выбор. "
        "Определи все товары или продукты на предоставленных фото. Используя информацию из интернета и отзывы, "
        "сравни их между собой. Посоветуй лучший из них. "
        "Если фото несколько, сравнивай товары со всех фотографий. "
        "Если на фото много товаров из разных категорий, выбери наиболее вероятную категорию для сравнения. "
        "Если все товары из разных категорий или по ним нет информации, укажи, что сравнение невозможно. "
        "Ответ должен быть очень кратким и лаконичным: просто лучший товар и почему он лучше (например, лучший состав, отзывы, качество)."
    )


    async def try_generate(api_key: str, model: str):
        """
        Внутренняя функция — одна попытка генерации с указанным ключом и моделью.
        """
        client = genai.Client(api_key=api_key)
        google_search_tool = Tool(google_search=GoogleSearch())

        # Загружаем все изображения
        image_parts = []
        for image in images:
            with NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                image.save(temp_file, format="JPEG")
                image_path = temp_file.name

            image_file = client.files.upload(file=pathlib.Path(image_path))
            image_parts.append(
                types.Part.from_uri(file_uri=image_file.uri, mime_type=image_file.mime_type)
            )
            os.remove(image_path)

        prompt_text = "Сравни эти товары."
        if query:
            prompt_text += f" Особое внимание удели: {query}"

        contents = [
            types.Content(
                role="user",
                parts=image_parts + [types.Part(text=prompt_text)]
            )
        ]

        response = await client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.8,
                top_p=0.9,
                top_k=40,
                tools=[google_search_tool],
                safety_settings=[
                    types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                ]
            )
        )

        if response.candidates and response.candidates[0].content.parts:
            response_text = "".join(
                part.text for part in response.candidates[0].content.parts
                if hasattr(part, "text") and part.text and not getattr(part, "thought", False)
            ).strip()
            return response_text
        return None

    # --- Основная логика ---
    last_key = None

    # 1. Перебираем все ключи только с основной моделью
    for key in key_manager.get_keys_to_try():
        last_key = key
        try:
            response_text = await try_generate(key, PRIMARY_MODEL)
            if response_text:
                await key_manager.set_successful_key(key)
                return response_text
        except Exception as e:
            logging.warning(f"Ошибка с ключом {key} и моделью {PRIMARY_MODEL}: {e}")
            # Не пробуем fallback здесь — просто идем к следующему ключу

    # 2. Если ВСЕ ключи с основной моделью не сработали —
    #    пробуем fallback модели только на последнем ключе
    if last_key:
        for model in FALLBACK_MODELS + GEMMA_MODELS:
            try:
                response_text = await try_generate(last_key, model)
                if response_text:
                    await key_manager.set_successful_key(last_key)
                    return response_text
            except Exception as e2:
                logging.warning(f"Ошибка с ключом {last_key} и моделью {model}: {e2}")

    # 3. Если вообще ничего не помогло
    return "Все доступные ключи и модели не сработали. Попробуйте позже."


async def generate_calories_response(user_id, images, query):
    """Оценивает примерное количество калорий на фото с едой и даёт полезную информацию."""
    system_instruction = (
        "Ты нутрициолог и спортивный консультант. "
        "Твоя задача — кратко и по существу проанализировать фото с едой.\n\n"
        "Отвечай структурировано по пунктам:\n"
        "1. Определи продукты на фото (каждый отдельно).\n"
        "2. Укажи примерное количество калорий для каждого продукта.\n"
        "3. Дай итоговую сумму калорий всего блюда или нескольких блюд, набора продуктов.\n"
        "4. Добавь краткую оценку пользы/вреда с точки зрения здоровья.\n"
        "5. Скажи, сколько примерно минут/часов нужно тренироваться (ходьба, бег или фитнес), чтобы сжечь эту еду.\n"
        "6. Дай одно-два полезных замечания или лайфхака (например, чем можно заменить для меньшей калорийности).\n\n"
        "⚠️ Важно: пиши лаконично, без лишней воды. Используй короткие предложения, списки или таблицы.\n"
        "Если несколько фото — анализируй их все.\n"
        "Если что-то определить невозможно, пиши честно: «неопределимо»."
        "Используй html-разметку, но исключительно ту что доступна в телеграм (<b>, <i>, <br>) если это улучшает читаемость."        
    )

    google_search_tool = Tool(google_search=GoogleSearch())

    # Загружаем все изображения один раз и готовим parts
    image_parts = []
    for image in images:
        with NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            image.save(temp_file, format="JPEG")
            image_path = temp_file.name
        image_parts.append(image_path)

    async def try_request(api_key: str, model: str):
        """Попытка выполнить запрос с конкретным ключом и моделью."""
        client = genai.Client(api_key=api_key)
        uploaded_parts = []
        try:
            for path in image_parts:
                image_file = client.files.upload(file=pathlib.Path(path))
                uploaded_parts.append(
                    types.Part.from_uri(file_uri=image_file.uri, mime_type=image_file.mime_type)
                )

            contents = [
                types.Content(
                    role="user",
                    parts=uploaded_parts + [types.Part(text=f"Комментарий пользователя: {query}" if query else "")]
                )
            ]

            response = await client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.8,
                    top_p=0.9,
                    top_k=40,
                    tools=[google_search_tool],
                    safety_settings=[
                        types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                    ]
                )
            )

            if response.candidates and response.candidates[0].content.parts:
                response_text = "".join(
                    part.text for part in response.candidates[0].content.parts
                    if part.text and not getattr(part, "thought", False)
                ).strip()
                await key_manager.set_successful_key(api_key)
                return response_text
            return None
        except Exception as e:
            logging.warning(f"Ошибка для ключа {api_key}, модели {model}: {e}")
            return None

    # --- 1. Перебираем ключи с основной моделью ---
    for key in key_manager.get_keys_to_try():
        result = await try_request(key, PRIMARY_MODEL)
        if result:
            for path in image_parts:
                os.remove(path)
            return result

    # --- 2. Все ключи упали → берём последний ключ ---
    last_key = key_manager.get_keys_to_try()[-1]

    # --- 3. Перебираем модели только для одного ключа (последнего) ---
    for fallback_model in FALLBACK_MODELS + GEMMA_MODELS:
        result = await try_request(last_key, fallback_model)
        if result:
            for path in image_parts:
                os.remove(path)
            return result

    # --- 4. Ошибка окончательная ---
    for path in image_parts:
        os.remove(path)

    return "Не удалось обработать изображения ни с одной моделью. Попробуйте позже."



async def generate_mapplants_response(user_id, image):
    """Генерирует текстовое описание проблемы с растением на основе изображения."""

    # Формируем статичный контекст для запроса
    context = (
        "Распознай растение на фото, по следующим пунктам:\n"
        "0) Что это. Гриб, растение, дерево, ягода. Этот пункт начни с фразы \"0)Это: \" В ответе напиши только одно слово из перечисленных, если ничего не подходит то напиши \"распознать не вышло\"\n"
        "1) Русскоязычные названия, от самого популярного до самых редких, если есть. Этот пункт начни с фразы \"1)Русские названия: \" В ответе перечисли только название или названия без лишних пояснений\n"
        "2) Общая краткая информация и описание, как выглядит, не длиннее 30 слов. Этот пункт начни с фразы \"2)Общая информация: \"\n"
        "3) Где обычно растёт, на какой территории и в какой местности, не длиннее 15 слов. Этот пункт начни с фразы \"3)Произрастает: \"\n"
        "4) Где и как применяется, ядовит или нет, не длиннее 20 слов. Этот пункт начни с фразы \"4)Применение: \"\n"
        "5) Дополнительная важная или интересная информация по этому растению, если есть. Этот пункт начни с фразы \"5)Дополнительно: \"\n\n"
        "Строго придерживайся заданного формата ответа, это нужно для того, чтобы корректно работал код программы.\n"
        "Никакого лишнего текста кроме заданных пунктов не пиши.\n"        
    )
    # Сохраняем изображение во временный файл
    with NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
        image_path = temp_file.name
        image.save(temp_file, format="JPEG")

    logging.info(f"Сохранено временное изображение: {image_path}")

    try:
        safety_settings = [
            types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
        ]

        google_search_tool = Tool(google_search=GoogleSearch())

        # ---------- ЭТАП 1. Перебор ключей на основной модели ----------
        successful = False
        last_key = None
        for api_key in key_manager.get_keys_to_try():
            last_key = api_key
            logging.info(f"Пробуем ключ {api_key[:10]}... с моделью {PRIMARY_MODEL}")
            try:
                client = genai.Client(api_key=api_key)
                image_file = client.files.upload(file=pathlib.Path(image_path))
                logging.info(f"Изображение загружено: {image_file.uri}")

                response = await client.aio.models.generate_content(
                    model=PRIMARY_MODEL,
                    contents=[
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_uri(
                                    file_uri=image_file.uri,
                                    mime_type=image_file.mime_type
                                ),
                                types.Part(text=f"{context}\n"),
                            ]
                        )
                    ],
                    config=types.GenerateContentConfig(
                        temperature=1.0,
                        top_p=0.9,
                        top_k=40,
                        tools=[google_search_tool],
                        safety_settings=safety_settings
                    )
                )

                if response.candidates and response.candidates[0].content.parts:
                    response_text = "".join(
                        part.text for part in response.candidates[0].content.parts
                        if part.text and not getattr(part, "thought", False)
                    ).strip()

                    await key_manager.set_successful_key(api_key)
                    return response_text if response_text else "Не удалось определить проблему растения."
                else:
                    logging.warning(f"Модель {PRIMARY_MODEL} не вернула ответа.")
            except Exception as e:
                logging.error(f"Ошибка с ключом {api_key[:10]}...: {e}")
                continue

        # ---------- ЭТАП 2. Если все ключи провалились – перебор моделей на последнем ключе ----------
        logging.warning("Все ключи на основной модели не сработали. Пробуем fallback-модели.")
        if last_key:
            for model in FALLBACK_MODELS + GEMMA_MODELS:
                logging.info(f"Пробуем fallback-модель: {model} с ключом {last_key}")
                try:
                    client = genai.Client(api_key=last_key)
                    image_file = client.files.upload(file=pathlib.Path(image_path))

                    response = await client.aio.models.generate_content(
                        model=model,
                        contents=[
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part.from_uri(
                                        file_uri=image_file.uri,
                                        mime_type=image_file.mime_type
                                    ),
                                    types.Part(text=f"{context}\n"),
                                ]
                            )
                        ],
                        config=types.GenerateContentConfig(
                            temperature=1.0,
                            top_p=0.9,
                            top_k=40,
                            tools=[google_search_tool],
                            safety_settings=safety_settings
                        )
                    )

                    if response.candidates and response.candidates[0].content.parts:
                        response_text = "".join(
                            part.text for part in response.candidates[0].content.parts
                            if part.text and not getattr(part, "thought", False)
                        ).strip()

                        # Ключ здесь не сохраняем! Только модели перебираем
                        return response_text if response_text else "Не удалось определить проблему растения."
                    else:
                        logging.warning(f"Fallback-модель {model} не вернула ответа.")
                except Exception as e:
                    logging.error(f"Ошибка с fallback-моделью {model}: {e}")
                    continue

        # ---------- ЭТАП 3. Всё сломалось ----------
        return "Не удалось обработать изображение. Попробуйте позже."

    finally:
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
                logging.info(f"Временный файл удален: {image_path}")
            except Exception as e:
                logging.error(f"Ошибка при удалении временного файла: {e}")


async def generate_text_rec_response(user_id, image=None, query=None):
    """Генерирует текстовое описание проблемы с растением на основе изображения или текста."""

    async def try_request(api_key, model, contents, config):
        """Вспомогательная функция для одного запроса."""
        try:
            client = genai.Client(api_key=api_key)
            response = await client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            if response.candidates and response.candidates[0].content.parts:
                text = "".join(
                    part.text for part in response.candidates[0].content.parts
                    if part.text and not getattr(part, "thought", False)
                ).strip()
                if text:
                    await key_manager.set_successful_key(api_key)
                    return text
            return None
        except Exception as e:
            logging.warning(f"Ошибка при запросе (ключ {api_key}, модель {model}): {e}")
            return None

    # === Ветка текстового запроса ===
    if query:
        context = f"Запрос:\n{query}"
        google_search_tool = Tool(google_search=GoogleSearch())
        config = types.GenerateContentConfig(
            temperature=1.4,
            top_p=0.95,
            top_k=25,
            tools=[google_search_tool],
            safety_settings=[
                types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE')
            ]
        )

        # 1. Пробуем PRIMARY_MODEL на всех ключах
        for key in key_manager.get_keys_to_try():
            text = await try_request(key, PRIMARY_MODEL, context, config)
            if text:
                return text

        # 2. Если все ключи не сработали — берем последний ключ и пробуем запасные модели
        last_key = key_manager.get_keys_to_try()[-1]
        for model in FALLBACK_MODELS + GEMMA_MODELS:
            text = await try_request(last_key, model, context, config)
            if text:
                return text

        return "Все ключи и модели не сработали. Попробуйте позже."

    # === Ветка обработки изображения ===
    elif image:
        context = (
            "Постарайся полностью распознать текст на изображении и в ответе прислать его. "
            "Текст может быть на любом языке, но в основном на русском, английском, японском, "
            "китайском и корейском. Ответ присылай на языке оригинала. "
            "Либо если не получилось распознать текст, напиши что текст распознать не вышло."
        )

        try:
            with NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                image_path = temp_file.name
                image.save(temp_file, format="JPEG")

            logging.info(f"Сохранено временное изображение: {image_path}")

            safety_settings = [
                types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
            ]

            google_search_tool = Tool(google_search=GoogleSearch())
            config = types.GenerateContentConfig(
                temperature=1.0,
                top_p=0.9,
                top_k=40,
                tools=[google_search_tool],
                safety_settings=safety_settings
            )

            # 1. Пробуем PRIMARY_MODEL на всех ключах
            for key in key_manager.get_keys_to_try():
                try:
                    client = genai.Client(api_key=key)
                    image_file = client.files.upload(file=pathlib.Path(image_path))
                except Exception as e:
                    logging.warning(f"Ошибка загрузки изображения (ключ {key}): {e}")
                    continue

                contents = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_uri(file_uri=image_file.uri, mime_type=image_file.mime_type),
                            types.Part(text=f"{context}\n"),
                        ]
                    )
                ]
                text = await try_request(key, PRIMARY_MODEL, contents, config)
                if text:
                    return text

            # 2. Если все ключи не сработали — пробуем запасные модели на последнем ключе
            last_key = key_manager.get_keys_to_try()[-1]
            try:
                client = genai.Client(api_key=last_key)
                image_file = client.files.upload(file=pathlib.Path(image_path))
            except Exception as e:
                logging.warning(f"Ошибка загрузки изображения (ключ {last_key}): {e}")
                return "Ошибка при загрузке изображения."

            for model in FALLBACK_MODELS + GEMMA_MODELS:
                contents = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_uri(file_uri=image_file.uri, mime_type=image_file.mime_type),
                            types.Part(text=f"{context}\n"),
                        ]
                    )
                ]
                text = await try_request(last_key, model, contents, config)
                if text:
                    return text

            return "Все ключи и модели не сработали. Попробуйте позже."

        except Exception as e:
            logging.error(f"Ошибка при обработке изображения: {e}")
            return "Ошибка при обработке изображения. Попробуйте снова."
        finally:
            if 'image_path' in locals() and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    logging.info(f"Временный файл удален: {image_path}")
                except Exception as e:
                    logging.error(f"Ошибка при удалении временного файла: {e}")

    else:
        return "Неверный запрос. Укажите изображение или текст для обработки."




async def generate_plant_issue_response(user_id, image, caption=None):
    """Генерирует текстовое описание проблемы с растением на основе изображения."""

    # Формируем статичный контекст для запроса
    context = ("Определи, что за проблема с растением (болезнь, вредители и т.д.) и предложи решение, ответ напиши на русском. Если необходимо используй html разметку доступную в telegram.")
    # Если есть подпись, добавляем её в запрос
    if caption:
        context += f"\n\nПользователь уточнил: {caption}"

    # Сохраняем изображение во временный файл
    with NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
        image_path = temp_file.name
        image.save(temp_file, format="JPEG")

    logging.info(f"Сохранено временное изображение: {image_path}")

    try:
        # --- 1. Пробуем сначала перебор ключей на основной модели ---
        for api_key in key_manager.get_keys_to_try():
            try:
                client = genai.Client(api_key=api_key)
                google_search_tool = Tool(google_search=GoogleSearch())

                try:
                    image_file = client.files.upload(file=pathlib.Path(image_path))
                except Exception as e:
                    logging.error(f"Ошибка при загрузке изображения: {e}")
                    return "Не удалось загрузить изображение."

                safety_settings = [
                    types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                ]

                response = await client.aio.models.generate_content(
                    model=PRIMARY_MODEL,
                    contents=[
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_uri(file_uri=image_file.uri, mime_type=image_file.mime_type),
                                types.Part(text=f"{context}\n"),
                            ]
                        )
                    ],
                    config=types.GenerateContentConfig(
                        temperature=1.0,
                        top_p=0.9,
                        top_k=40,
                        tools=[google_search_tool],
                        safety_settings=safety_settings
                    )
                )

                if response.candidates and response.candidates[0].content.parts:
                    response_text = "".join(
                        part.text for part in response.candidates[0].content.parts
                        if part.text and not getattr(part, "thought", False)
                    ).strip()

                    await key_manager.set_successful_key(api_key)
                    return response_text or "Не удалось определить проблему растения."

                else:
                    logging.warning(f"Gemini ({PRIMARY_MODEL}) не вернул ответ с ключом {api_key}.")
                    continue

            except Exception as e:
                logging.warning(f"Ошибка с ключом {api_key} на модели {PRIMARY_MODEL}: {e}")
                continue

        # --- 2. Если все ключи упали → перебор моделей на одном ключе ---
        last_key = key_manager.get_keys_to_try()[-1]  # возьмем последний из списка
        logging.info(f"Все ключи упали на {PRIMARY_MODEL}, пробуем fallback-модели с ключом {last_key}")

        client = genai.Client(api_key=last_key)
        google_search_tool = Tool(google_search=GoogleSearch())

        try:
            image_file = client.files.upload(file=pathlib.Path(image_path))
        except Exception as e:
            logging.error(f"Ошибка при загрузке изображения: {e}")
            return "Не удалось загрузить изображение."

        safety_settings = [
            types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
        ]

        for model in FALLBACK_MODELS + GEMMA_MODELS:
            try:
                response = await client.aio.models.generate_content(
                    model=model,
                    contents=[
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_uri(file_uri=image_file.uri, mime_type=image_file.mime_type),
                                types.Part(text=f"{context}\n"),
                            ]
                        )
                    ],
                    config=types.GenerateContentConfig(
                        temperature=1.0,
                        top_p=0.9,
                        top_k=40,
                        tools=[google_search_tool],
                        safety_settings=safety_settings
                    )
                )

                if response.candidates and response.candidates[0].content.parts:
                    response_text = "".join(
                        part.text for part in response.candidates[0].content.parts
                        if part.text and not getattr(part, "thought", False)
                    ).strip()
                    return response_text or "Не удалось определить проблему растения."
                else:
                    logging.warning(f"Gemini ({model}) не вернул ответ с ключом {last_key}.")
                    continue

            except Exception as e:
                logging.warning(f"Ошибка с ключом {last_key} на модели {model}: {e}")
                continue

        # --- 3. Если и fallback-модели не сработали ---
        return "Все доступные ключи и модели не смогли обработать запрос. Попробуйте позже."

    finally:
        if 'image_path' in locals() and os.path.exists(image_path):
            try:
                os.remove(image_path)
                logging.info(f"Временный файл удален: {image_path}")
            except Exception as e:
                logging.error(f"Ошибка при удалении временного файла: {e}")


async def response_animal(user_id, image, caption=None):
    """Определяет животное по фото и выдает краткую справку о нём."""

    # Формируем статичный контекст для запроса
    context = (
        "Определи, какое это животное (включая птиц, насекомых и иных живых существ) по изображению. "
        "Дай краткое описание на русском языке: его отличительные черты, среду обитания, чем питается, "
        "и интересные факты. Ответ сделай информативным, но кратким. "
        "Если необходимо, используй html-разметку, доступную в Telegram (например <b>, <i>, <u>, <a>)."
    )
    if caption:
        context += f"\n\nПользователь уточнил: {caption}"

    # Сохраняем изображение во временный файл
    with NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
        image_path = temp_file.name
        image.save(temp_file, format="JPEG")

    logging.info(f"Сохранено временное изображение: {image_path}")

    google_search_tool = Tool(google_search=GoogleSearch())

    # Настройки безопасности
    safety_settings = [
        types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
        types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
        types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
        types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
    ]

    try:
        # Загружаем картинку один раз (ключи не влияют на upload)
        temp_client = genai.Client(api_key=API_KEYS[0])
        try:
            image_file = temp_client.files.upload(file=pathlib.Path(image_path))
        except Exception as e:
            logging.error(f"Ошибка при загрузке изображения: {e}")
            return "Не удалось загрузить изображение."

        # 1. Перебираем ключи с основной моделью
        for api_key in key_manager.get_keys_to_try():
            try:
                client = genai.Client(api_key=api_key)
                response = await client.aio.models.generate_content(
                    model=PRIMARY_MODEL,
                    contents=[
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_uri(
                                    file_uri=image_file.uri,
                                    mime_type=image_file.mime_type
                                ),
                                types.Part(text=f"{context}\n"),
                            ]
                        )
                    ],
                    config=types.GenerateContentConfig(
                        temperature=1.0,
                        top_p=0.9,
                        top_k=40,
                        tools=[google_search_tool],
                        safety_settings=safety_settings
                    )
                )

                if response.candidates and response.candidates[0].content.parts:
                    response_text = "".join(
                        part.text for part in response.candidates[0].content.parts
                        if part.text and not getattr(part, "thought", False)
                    ).strip()

                    if response_text:
                        await key_manager.set_successful_key(api_key)
                        return response_text

            except Exception as e:
                logging.warning(f"Ошибка с ключом {api_key} и основной моделью: {e}")
                continue

        # 2. Если все ключи дали ошибку → перебираем fallback-модели только с последним ключом
        last_key = key_manager.get_keys_to_try()[-1]
        for model in FALLBACK_MODELS + GEMMA_MODELS:
            try:
                client = genai.Client(api_key=last_key)
                response = await client.aio.models.generate_content(
                    model=model,
                    contents=[
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_uri(
                                    file_uri=image_file.uri,
                                    mime_type=image_file.mime_type
                                ),
                                types.Part(text=f"{context}\n"),
                            ]
                        )
                    ],
                    config=types.GenerateContentConfig(
                        temperature=1.0,
                        top_p=0.9,
                        top_k=40,
                        tools=[google_search_tool],
                        safety_settings=safety_settings
                    )
                )

                if response.candidates and response.candidates[0].content.parts:
                    response_text = "".join(
                        part.text for part in response.candidates[0].content.parts
                        if part.text and not getattr(part, "thought", False)
                    ).strip()

                    if response_text:
                        # Ключ сохранять не нужно (по условию только при основной модели)
                        return response_text

            except Exception as e:
                logging.warning(f"Ошибка с ключом {last_key} и моделью {model}: {e}")
                continue

        # Если всё провалилось
        return "Не удалось определить животное: все ключи и fallback модели выдали ошибку."

    finally:
        if 'image_path' in locals() and os.path.exists(image_path):
            try:
                os.remove(image_path)
                logging.info(f"Временный файл удален: {image_path}")
            except Exception as e:
                logging.error(f"Ошибка при удалении временного файла: {e}")



async def response_ingredients(user_id, image):
    """Анализирует состав продукта или изделия по фото и выдает структурированный отчет."""

    # Формируем статичный контекст для запроса
    context = (
        "Проанализируй состав продукта или изделия по изображению с научной и обоснованной точки зрения. "
        "Используй актуальные научные данные и заслуживающие доверия источники. "
        "Будь по возможности предельно кратким и лаконичным, пиши только существенную и полезную информацию чтобы твой ответ можно было быстро прочитать, постарайся уместить весь ответ в 300 слов, максимум 400. "       
        "Твой ответ должен быть четко структурирован по следующим пунктам. "
        "Если какой-то пункт неприменим (например, продукт нельзя рассматривать с точки зрения пользы), укажи это.\n\n"
        "<b>1. Общая краткая характеристика:</b> Что это за продукт или изделие?\n"
        "<b>2. Анализ состава:</b> Разбери каждый компонент. Укажи его функцию (например, консервант, краситель, эмульгатор). Если компонент может быть вреден, вызывать аллергию или имеет другие важные особенности, отметь это.\n"
        "<b>3. Потенциальная польза:</b> Опиши возможную пользу данного продукта, если он съедобен то пользу для здоровья, основываясь на компонентах.\n"
        "<b>4. Потенциальный вред:</b> Опиши возможные риски и вред  связанные с данным продуктом, если он съедобен то например при чрезмерном употреблении или для определенных групп людей.\n"
        "<b>5. Общее качество продукта:</b> На основе анализа состава, дай общую оценку качества продукта (например, натуральный состав, много искусственных добавок и т.д.).\n"
        "<b>6. Выводы:</b> Сделай краткий итоговый вывод о продукте, стоит ли его покупать/употреблять.\n\n"
        "Ответ должен быть объективным и информативным. Используй html-разметку Telegram для форматирования (<b>, <i>, <u>)."
    )

    # Настройки безопасности
    safety_settings = [
        types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
        types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
        types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
        types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
    ]

    try:
        # Сохраняем изображение во временный файл
        with NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            image_path = temp_file.name
            image.save(temp_file, format="JPEG")

        logging.info(f"Сохранено временное изображение: {image_path}")

        # === Шаг 1: перебор ключей на основной модели ===
        for key in key_manager.get_keys_to_try():
            logging.info(f"Пробуем API ключ: {key[:10]}... на модели {PRIMARY_MODEL}")
            try:
                client = genai.Client(api_key=key)
                google_search_tool = Tool(google_search=GoogleSearch())

                image_file = client.files.upload(file=pathlib.Path(image_path))

                response = await client.aio.models.generate_content(
                    model=PRIMARY_MODEL,
                    contents=[
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_uri(
                                    file_uri=image_file.uri,
                                    mime_type=image_file.mime_type
                                ),
                                types.Part(text=f"{context}\n"),
                            ]
                        )
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0.8,
                        top_p=0.9,
                        top_k=40,
                        tools=[google_search_tool],
                        safety_settings=safety_settings
                    )
                )

                if response.candidates and response.candidates[0].content.parts:
                    response_text = "".join(
                        part.text for part in response.candidates[0].content.parts
                        if part.text and not getattr(part, "thought", False)
                    ).strip()

                    if response_text:
                        await key_manager.set_successful_key(key)
                        return response_text

            except Exception as e:
                logging.warning(f"Ошибка с ключом {key[:10]}... и моделью {PRIMARY_MODEL}: {e}")
                continue

        # === Шаг 2: если ВСЕ ключи упали, пробуем fallback-модели на одном ключе (берем последний) ===
        last_key = key_manager.get_keys_to_try()[-1]
        logging.info(f"Все ключи упали на основной модели, пробуем fallback модели на ключе {last_key[:10]}...")

        for model in FALLBACK_MODELS + GEMMA_MODELS:
            try:
                client = genai.Client(api_key=last_key)
                google_search_tool = Tool(google_search=GoogleSearch())

                image_file = client.files.upload(file=pathlib.Path(image_path))

                response = await client.aio.models.generate_content(
                    model=model,
                    contents=[
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_uri(
                                    file_uri=image_file.uri,
                                    mime_type=image_file.mime_type
                                ),
                                types.Part(text=f"{context}\n"),
                            ]
                        )
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0.8,
                        top_p=0.9,
                        top_k=40,
                        tools=[google_search_tool],
                        safety_settings=safety_settings
                    )
                )

                if response.candidates and response.candidates[0].content.parts:
                    response_text = "".join(
                        part.text for part in response.candidates[0].content.parts
                        if part.text and not getattr(part, "thought", False)
                    ).strip()

                    if response_text:
                        # здесь ключ не сохраняем, так как fallback может быть временным
                        return response_text

            except Exception as e:
                logging.warning(f"Ошибка с ключом {last_key[:10]}... и моделью {model}: {e}")
                continue

        # === Шаг 3: если ничего не вышло ===
        return "Не удалось проанализировать состав продукта: все ключи и модели вернули ошибку."

    except Exception as e:
        logging.info(f"Ошибка при обработке изображения: {e}")
        return "Ошибка при обработке изображения. Попробуйте снова."
    finally:
        if 'image_path' in locals() and os.path.exists(image_path):
            try:
                os.remove(image_path)
                logging.info(f"Временный файл удален: {image_path}")
            except Exception as e:
                logging.error(f"Ошибка при удалении временного файла: {e}")



async def generate_barcode_response(user_id, image=None, query=None):
    context = "Найди в интернете отзывы об этом продукте и пришли в ответ краткую сводку о найденных положительных и отрицательных отзывах. Ответ разбей по категориям: \"0)Название товара: \" \n\n \"1)Оценка: */5 (с точностью до сотых) \nОбщее краткое впечатление: \" (не длиннее 35 слов, оценку сформулируй на основании полученных данных где 5 - наилучший товар)\n\n \"2)Положительные отзывы: \" что хвалят и почему(не длиннее 50 слов)\n\n \"3)Отрицательные отзывы: \" Чем недовольны и почему, постарайся выделить наиболее существенные претензии(не длиннее 70 слов)\n\n Строго придерживайся заданного формата ответа, это нужно для того, чтобы корректно работал код программы."

    try:
        # Сохраняем изображение во временный файл
        with NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            image_path = temp_file.name
            image.save(temp_file, format="JPEG")

        logging.info(f"Сохранено временное изображение: {image_path}")

        # Настройки безопасности
        safety_settings = [
            types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
        ]

        last_exception = None
        successful = False
        last_key = None

        # --- Шаг 1. Перебор ключей только с основной моделью ---
        for key in key_manager.get_keys_to_try():
            last_key = key
            try:
                client = genai.Client(api_key=key)
                google_search_tool = Tool(google_search=GoogleSearch())

                # Загружаем изображение
                try:
                    image_file = client.files.upload(file=pathlib.Path(image_path))
                except Exception as e:
                    logging.error(f"Ошибка при загрузке изображения ({key}): {e}")
                    last_exception = e
                    continue

                try:
                    response = await client.aio.models.generate_content(
                        model=PRIMARY_MODEL,
                        contents=[
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part.from_uri(
                                        file_uri=image_file.uri,
                                        mime_type=image_file.mime_type
                                    ),
                                    types.Part(text=f"{context}\n"),
                                ]
                            )
                        ],
                        config=types.GenerateContentConfig(
                            temperature=1.0,
                            top_p=0.9,
                            top_k=40,
                            tools=[google_search_tool],
                            safety_settings=safety_settings
                        )
                    )

                    if response.candidates and response.candidates[0].content.parts:
                        response_text = "".join(
                            part.text for part in response.candidates[0].content.parts
                            if part.text and not getattr(part, "thought", False)
                        ).strip()

                        await key_manager.set_successful_key(key)
                        return response_text
                    else:
                        logging.warning(f"Gemini ({PRIMARY_MODEL}) не вернул ответ.")
                        last_exception = Exception("Пустой ответ от модели")

                except Exception as e:
                    logging.error(f"Ошибка при генерации ({PRIMARY_MODEL}, {key}): {e}")
                    last_exception = e
                    continue

            except Exception as e:
                logging.error(f"Ошибка при использовании ключа {key}: {e}")
                last_exception = e
                continue

        # --- Шаг 2. Если все ключи с основной моделью дали сбой → пробуем fallback модели на последнем ключе ---
        if last_key:
            try:
                client = genai.Client(api_key=last_key)
                google_search_tool = Tool(google_search=GoogleSearch())

                image_file = client.files.upload(file=pathlib.Path(image_path))

                for model in FALLBACK_MODELS + GEMMA_MODELS:
                    try:
                        response = await client.aio.models.generate_content(
                            model=model,
                            contents=[
                                types.Content(
                                    role="user",
                                    parts=[
                                        types.Part.from_uri(
                                            file_uri=image_file.uri,
                                            mime_type=image_file.mime_type
                                        ),
                                        types.Part(text=f"{context}\n"),
                                    ]
                                )
                            ],
                            config=types.GenerateContentConfig(
                                temperature=1.0,
                                top_p=0.9,
                                top_k=40,
                                tools=[google_search_tool],
                                safety_settings=safety_settings
                            )
                        )

                        if response.candidates and response.candidates[0].content.parts:
                            response_text = "".join(
                                part.text for part in response.candidates[0].content.parts
                                if part.text and not getattr(part, "thought", False)
                            ).strip()

                            # ВАЖНО: ключ мы уже сохраняем только если успешно
                            await key_manager.set_successful_key(last_key)
                            return response_text
                        else:
                            logging.warning(f"Gemini ({model}) не вернул ответ.")
                            last_exception = Exception("Пустой ответ от модели")

                    except Exception as e:
                        logging.error(f"Ошибка при генерации ({model}, {last_key}): {e}")
                        last_exception = e
                        continue

            except Exception as e:
                logging.error(f"Ошибка при fallback попытках с ключом {last_key}: {e}")
                last_exception = e

        # --- Если ничего не получилось ---
        if last_exception:
            logging.error(f"Все ключи и модели перепробованы, ошибка: {last_exception}")
        return "Не удалось обработать запрос. Попробуйте позже."

    except Exception as e:
        logging.error(f"Ошибка при генерации описания: {e}")
        return "Ошибка при обработке изображения. Попробуйте снова."
    finally:
        if 'image_path' in locals() and os.path.exists(image_path):
            try:
                os.remove(image_path)
                logging.info(f"Временный файл удален: {image_path}")
            except Exception as e:
                logging.error(f"Ошибка при удалении временного файла: {e}")

async def generate_barcode_analysis(user_id, query=None):
    """Генерирует текстовое описание продукта на основе текста.
       Перебирает API ключи и fallback модели при ошибках.
    """

    if not query:
        return "Нет данных для анализа."

    system_instruction = (
        "На основании предоставленной информации определи название данного продукта. "
        "В ответ напиши только название и ничего более кроме названия. "
        "Если информации недостаточно то сообщи об этом."
    )
    context = f"Текущая доступная информация о продукте: {query}"


    last_key = None
    # --- 1. Перебор ключей с основной моделью ---
    for key in key_manager.get_keys_to_try():
        last_key = key
        try:
            client = genai.Client(api_key=key)
            google_search_tool = Tool(google_search=GoogleSearch())

            try:
                response = await client.aio.models.generate_content(
                    model=PRIMARY_MODEL,
                    contents=context,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=1.4,
                        top_p=0.95,
                        top_k=25,
                        tools=[google_search_tool],
                        safety_settings=[
                            types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                            types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                            types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                            types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE')
                        ]
                    )
                )

                if response.candidates and response.candidates[0].content.parts:
                    result = "".join(
                        part.text for part in response.candidates[0].content.parts
                        if part.text and not getattr(part, "thought", False)
                    ).strip()

                    if result:
                        # Сохраняем удачный ключ
                        await key_manager.set_successful_key(key)
                        return result

                    logging.warning("Ответ от модели не содержит текста.")
                    return "Извините, ошибка обработки."

            except Exception as model_err:
                logging.warning(f"Ошибка основной модели {PRIMARY_MODEL} с ключом {key}: {model_err}")
                continue  # Пробуем следующий ключ

        except Exception as key_err:
            logging.error(f"Ошибка при использовании API ключа {key}: {key_err}")
            continue  # Пробуем следующий ключ

    # --- 2. Если все ключи упали, пробуем fallback модели на последнем ключе ---
    if last_key:
        try:
            client = genai.Client(api_key=last_key)
            google_search_tool = Tool(google_search=GoogleSearch())

            for model_name in FALLBACK_MODELS + GEMMA_MODELS:
                try:
                    response = await client.aio.models.generate_content(
                        model=model_name,
                        contents=context,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=1.4,
                            top_p=0.95,
                            top_k=25,
                            tools=[google_search_tool],
                            safety_settings=[
                                types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                                types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                                types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                                types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE')
                            ]
                        )
                    )

                    if response.candidates and response.candidates[0].content.parts:
                        result = "".join(
                            part.text for part in response.candidates[0].content.parts
                            if part.text and not getattr(part, "thought", False)
                        ).strip()

                        if result:
                            return result

                except Exception as fb_err:
                    logging.warning(f"Ошибка fallback модели {model_name} с ключом {last_key}: {fb_err}")
                    continue

        except Exception as fb_key_err:
            logging.error(f"Ошибка при fallback с ключом {last_key}: {fb_key_err}")

    return "Извините, все ключи и fallback модели не сработали. Попробуйте позже."


async def generate_barcode_otzyvy(user_id, query=None):
    """Генерирует текстовое описание проблемы с растением на основе текста."""

    if not query:
        return "Запрос не был передан."

    logging.info(f"query: {query}")          
    context = f"Найди в интернете отзывы о продукте {query}"

    google_search_tool = Tool(google_search=GoogleSearch()) 

    # --- 1. Сначала пробуем основную модель только с перебором ключей ---
    for api_key in key_manager.get_keys_to_try():
        try:
            client = genai.Client(api_key=api_key)
            response = await client.aio.models.generate_content(
                model=PRIMARY_MODEL,
                contents=context,
                config=types.GenerateContentConfig(
                    temperature=1.4,
                    top_p=0.95,
                    top_k=25,
                    tools=[google_search_tool],
                    safety_settings=[
                        types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE')
                    ]
                )
            )

            if response.candidates and response.candidates[0].content.parts:
                text = "".join(
                    part.text for part in response.candidates[0].content.parts
                    if part.text and not getattr(part, "thought", False)
                ).strip()
                if text:
                    logging.info(f"Успешный ответ с ключом {api_key}, модель {PRIMARY_MODEL}")
                    await key_manager.set_successful_key(api_key)
                    return text
                else:
                    logging.warning("Ответ от модели не содержит текста.")
                    return "Извините, ошибка обработки."

        except Exception as e:
            logging.error(f"Ошибка с ключом {api_key}, модель {PRIMARY_MODEL}: {e}")
            # идём к следующему ключу

    # --- 2. Если все ключи не подошли, пробуем модели на последнем ключе ---
    last_key = key_manager.get_keys_to_try()[-1]
    for model in FALLBACK_MODELS + GEMMA_MODELS:
        try:
            client = genai.Client(api_key=last_key)
            response = await client.aio.models.generate_content(
                model=model,
                contents=context,
                config=types.GenerateContentConfig(
                    temperature=1.4,
                    top_p=0.95,
                    top_k=25,
                    tools=[google_search_tool],
                    safety_settings=[
                        types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                        types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE')
                    ]
                )
            )

            if response.candidates and response.candidates[0].content.parts:
                text = "".join(
                    part.text for part in response.candidates[0].content.parts
                    if part.text and not getattr(part, "thought", False)
                ).strip()
                if text:
                    logging.info(f"Успешный ответ с ключом {last_key}, fallback-модель {model}")
                    # ключ не сохраняем, т.к. это fallback-сценарий
                    return text
                else:
                    logging.warning("Ответ от fallback-модели не содержит текста.")
                    return "Извините, ошибка обработки."

        except Exception as e:
            logging.error(f"Ошибка с fallback-моделью {model}, ключ {last_key}: {e}")
            # идём к следующей модели

    # --- 3. Если ничего не сработало ---
    logging.error("Все ключи и fallback-модели исчерпаны.")
    return "Ошибка: не удалось получить ответ ни от одной модели."



async def generate_plant_help_response(user_id, query=None):
    """Генерирует текстовое описание проблемы с растением на основе текста."""

    if not query:
        return "Запрос пустой."

    # Формируем контекст с текущим запросом
    context = f"Запрос:\n{query}"
    logging.info(f"context: {context}")

    # Модели для перебора: сначала основная, потом запасные
    models_to_try = [PRIMARY_MODEL] + FALLBACK_MODELS + GEMMA_MODELS

    # Инструменты
    google_search_tool = Tool(google_search=GoogleSearch())
    config = types.GenerateContentConfig(
        temperature=1.4,
        top_p=0.95,
        top_k=25,
        tools=[google_search_tool],
        safety_settings=[
            types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
        ]
    )

    # 1. Пробуем основной моделью со всеми ключами
    successful_key = None
    for key in key_manager.get_keys_to_try():
        try:
            client = genai.Client(api_key=key)
            response = await client.aio.models.generate_content(
                model=PRIMARY_MODEL,
                contents=context,
                config=config,
            )
            logging.info(f"Успешный ответ от модели {PRIMARY_MODEL} с ключом {key}")

            await key_manager.set_successful_key(key)
            successful_key = key

            if response.candidates and response.candidates[0].content.parts:
                result = "".join(
                    part.text
                    for part in response.candidates[0].content.parts
                    if part.text and not getattr(part, "thought", False)
                ).strip()
                return result if result else "Извините, я не могу ответить на этот запрос."
            else:
                logging.warning("Ответ от модели не содержит текстового компонента.")
                return "Извините, я не могу ответить на этот запрос."

        except Exception as e:
            logging.error(f"Ошибка при работе с ключом {key} и моделью {PRIMARY_MODEL}: {e}")
            # идём к следующему ключу

    # 2. Если все ключи не сработали → берём последний ключ и пробуем запасные модели
    last_key = key_manager.get_keys_to_try()[-1]
    for model in FALLBACK_MODELS + GEMMA_MODELS:
        try:
            logging.info(f"Пробуем fallback модель {model} с последним ключом {last_key}")
            client = genai.Client(api_key=last_key)
            response = await client.aio.models.generate_content(
                model=model,
                contents=context,
                config=config,
            )
            logging.info(f"Успешный ответ от fallback модели {model} с ключом {last_key}")

            # ⚠️ Тут ключ не запоминаем, т.к. успешность модели не сохраняем
            if response.candidates and response.candidates[0].content.parts:
                result = "".join(
                    part.text
                    for part in response.candidates[0].content.parts
                    if part.text and not getattr(part, "thought", False)
                ).strip()
                return result if result else "Извините, я не могу ответить на этот запрос."
            else:
                logging.warning("Ответ от модели не содержит текстового компонента.")
                return "Извините, я не могу ответить на этот запрос."

        except Exception as e:
            logging.error(f"Ошибка при работе с fallback моделью {model} и ключом {last_key}: {e}")
            # идём к следующей модели

    # 3. Всё сломалось
    return "Извините, не удалось обработать запрос ни с одной моделью. Попробуйте позже."


async def translate_promt_with_gemini(user_id, query=None):
    if query:
        # Проверяем наличие кириллических символов
        contains_cyrillic = bool(re.search("[а-яА-Я]", query))
        logger.info(f"Содержит кириллицу: {contains_cyrillic}")

        # Если кириллицы нет, возвращаем текст без изменений
        if not contains_cyrillic:
            return query

        # Если текст не на английском, переводим его
        context = (
            f"Ты бот для перевода промптов с русского на английский. Переведи запрос в качестве промпта для генерации изображения на английский язык. "
            f"В ответ пришли исключительно готовый промт на английском языке и ничего более. Это важно для того чтобы код корректно сработал. "
            f"Даже если запрос странный и не определённый, то переведи его и верни перевод. "
            f"Текущий запрос:\n{query}"
        )

        max_retries = 2  # Количество повторных попыток при временных сбоях
        retry_delay = 3  # Задержка между повторами

        # Сначала пробуем основную модель с перебором ключей
        for model in [PRIMARY_MODEL_FLESHLIGHT] + FALLBACK_MODELS_FLESHLIGHT + GEMMA_MODELS:
            keys_to_try = key_manager.get_keys_to_try()

            for key in keys_to_try:
                for attempt in range(max_retries + 1):
                    try:
                        client = genai.Client(api_key=key)
                        google_search_tool = Tool(google_search=GoogleSearch()) 
                        response = await client.aio.models.generate_content(
                            model=model,
                            contents=context,
                            config=types.GenerateContentConfig(
                                temperature=1.4,
                                top_p=0.95,
                                top_k=25,
                                tools=[google_search_tool],
                                safety_settings=[
                                    types.SafetySetting(
                                        category='HARM_CATEGORY_HATE_SPEECH',
                                        threshold='BLOCK_NONE'
                                    ),
                                    types.SafetySetting(
                                        category='HARM_CATEGORY_HARASSMENT',
                                        threshold='BLOCK_NONE'
                                    ),
                                    types.SafetySetting(
                                        category='HARM_CATEGORY_SEXUALLY_EXPLICIT',
                                        threshold='BLOCK_NONE'
                                    ),
                                    types.SafetySetting(
                                        category='HARM_CATEGORY_DANGEROUS_CONTENT',
                                        threshold='BLOCK_NONE'
                                    )
                                ]
                            )
                        )

                        if response.candidates and response.candidates[0].content.parts:
                            result = "".join(
                                part.text for part in response.candidates[0].content.parts
                                if part.text and not getattr(part, "thought", False)
                            ).strip()

                            await key_manager.set_successful_key(key)  # Запоминаем удачный ключ
                            return result if result else "Извините, я не могу ответить на этот запрос."
                        else:
                            logging.warning("Ответ от модели не содержит текстового компонента.")
                            return "Извините, я не могу ответить на этот запрос."

                    except Exception as e:
                        logging.error(f"Ошибка при генерации (модель {model}, ключ {key}, попытка {attempt + 1}): {e}")
                        if attempt < max_retries:
                            await asyncio.sleep(retry_delay)
                        # иначе пробуем следующий ключ
                        continue

            # если все ключи для этой модели не сработали → пробуем следующую модель

        # если не сработала ни одна модель с ключами
        return "Ошибка: все ключи и модели недоступны. Попробуйте позже."




async def generate_word(chat_id):
    context = (
        f"Твоя цель - сгенерировать 100 слов подходящая для игры в крокодил. Это должны быть как простые слова, так и какие-нибудь интересные слова которые достаточно сложно отгадать, но они должны быть общеизвестными. Они могут быть из любой области науки, культуры, общества, интернета и тд"
        f"Старайся избегать глаголов и имён собственных. "
        f"Избегай повторов и схожих по смыслу слов. "
        f"Эти слова должны быть знакомы большинству людей. "
        f"В ответ пришли список слов в следующем формате: 1: слово1 2: слово2 3: слово3 и тд"
    )

    # Сначала пробуем основную модель
    models_to_try = [PRIMARY_MODEL_FLESHLIGHT] + FALLBACK_MODELS_FLESHLIGHT + GEMMA_MODELS

    # Перебор моделей только если ключи все не подходят
    for model in models_to_try:
        keys_to_try = key_manager.get_keys_to_try()
        for key in keys_to_try:
            try:
                client = genai.Client(api_key=key)  # создаём клиент с текущим ключом
                response = await client.aio.models.generate_content(
                    model=model,
                    contents=context,
                    config=types.GenerateContentConfig(
                        temperature=1.7,
                        top_p=0.9,
                        top_k=40,
                        safety_settings=[
                            types.SafetySetting(
                                category='HARM_CATEGORY_HATE_SPEECH',
                                threshold='BLOCK_NONE'
                            ),
                            types.SafetySetting(
                                category='HARM_CATEGORY_HARASSMENT',
                                threshold='BLOCK_NONE'
                            ),
                            types.SafetySetting(
                                category='HARM_CATEGORY_SEXUALLY_EXPLICIT',
                                threshold='BLOCK_NONE'
                            ),
                            types.SafetySetting(
                                category='HARM_CATEGORY_DANGEROUS_CONTENT',
                                threshold='BLOCK_NONE'
                            )
                        ]
                    )
                )

                if response.candidates and response.candidates[0].content.parts:
                    bot_response = "".join(
                        part.text for part in response.candidates[0].content.parts
                        if part.text and not getattr(part, "thought", False)
                    ).strip()
                    logger.info("Ответ от Gemini (%s, %s): %s", key, model, bot_response)
                    await key_manager.set_successful_key(key)
                    return bot_response
                else:
                    logger.warning("Gemini (%s, %s) не вернул ответ.", key, model)
                    continue

            except Exception as e:
                logger.error("Ошибка при генерации (%s, %s): %s", key, model, e)
                continue

    # Если все ключи и модели не сработали
    return "Извините, ни один из ключей и моделей не смог обработать запрос."

def extract_random_word(text: str) -> str:
    """Извлекает случайное слово из сгенерированного списка."""
    words = re.findall(r"\d+:\s*([\w-]+)", text)  # Ищем слова после номеров
    if not words:
        return "Ошибка генерации"
    return random.choice(words)





async def Generate_gemini_image(prompt):
    context = f"{prompt}"

    for key in key_manager.get_keys_to_try():
        try:
            client = genai.Client(api_key=key)  # создаём клиента с текущим ключом

            response = await client.aio.models.generate_content(
                model="gemini-2.0-flash",  # модель фиксированная
                contents=context,
                config=types.GenerateContentConfig(
                    temperature=1,
                    top_p=0.95,
                    top_k=40,
                    response_modalities=["image", "text"],
                    safety_settings=[
                        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                        types.SafetySetting(category="HARM_CATEGORY_CIVIC_INTEGRITY", threshold="BLOCK_NONE"),
                    ],
                    response_mime_type="text/plain",
                ),
            )

            captions = []
            image_urls = []
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    clean_caption = part.text.replace('\n', ' ').strip()[:1000]
                    captions.append(clean_caption)

                if part.inline_data is not None:
                    image = Image.open(BytesIO(part.inline_data.data))
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                        image.save(temp_file.name, format="PNG")
                        image_urls.append(temp_file.name)

            # Лог для отладки
            for i, url in enumerate(image_urls):
                print(f"===IMAGE_START==={i}===")
                print(url)
                print(f"===IMAGE_END==={i}===")

            for i, caption in enumerate(captions):
                print(f"===CAPTION_START==={i}===")
                print(caption)
                print(f"===CAPTION_END==={i}===")

            # Если успех — сохраняем ключ и возвращаем результат
            await key_manager.set_successful_key(key)
            return captions, image_urls

        except Exception as e:
            logger.error(f"Ошибка при генерации изображения с ключом {key[:10]}...: {e}")
            continue

    # Если ни один ключ не сработал
    return None, None




async def generate_inpaint_gemini(image_file_path: str, instructions: str):
    """
    Загружает изображение в Google и отправляет его в Gemini для обработки.
    Перебирает только API-ключи, модели остаются фиксированными.
    """
    try:
        if not instructions:
            instructions = "Придумай как сделать это изображение интереснее."

        # Проверяем, существует ли файл
        if not os.path.exists(image_file_path):
            logger.error(f"Файл {image_file_path} не существует.")
            return None, "Ошибка: изображение не найдено."

        image_path = pathlib.Path(image_file_path)
        logger.info(f"Uploading image file: {image_path}")

        # Перебираем ключи
        for api_key in key_manager.get_keys_to_try():
            client = genai.Client(api_key=api_key)
            try:
                image_file = client.files.upload(file=image_path)
                logger.info(f"image_file: {image_file}")            
            except Exception as e:
                logger.error(f"Ошибка при загрузке изображения с ключом {api_key[:10]}...: {e}")
                continue  # Пробуем следующий ключ

            logger.info(f"Image uploaded: {image_file.uri}")

            safety_settings = [
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            ]

            try:
                response = await client.aio.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_uri(
                                    file_uri=image_file.uri,
                                    mime_type=image_file.mime_type
                                ),
                                types.Part(text=instructions),
                            ]
                        )
                    ],
                    config=types.GenerateContentConfig(
                        temperature=1.0,
                        top_p=0.95,
                        top_k=40,
                        response_modalities=["image", "text"],
                        safety_settings=safety_settings,
                    ),
                )
            except Exception as e:
                logger.error(f"Ошибка при обращении к модели с ключом {api_key[:10]}...: {e}")
                continue  # Пробуем следующий ключ

            if not response.candidates:
                logging.warning("Gemini вернул пустой список кандидатов.")
                continue

            first_candidate = response.candidates[0]
            if not hasattr(first_candidate, "content") or not first_candidate.content:
                logging.warning("Ответ Gemini не содержит контента.")
                continue
            
            if not hasattr(first_candidate.content, "parts") or not first_candidate.content.parts:
                logging.warning("Ответ Gemini не содержит частей контента.")
                continue

            captions = []
            image_urls = []
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    clean_caption = part.text.replace('\n', ' ').strip()[:1000]
                    captions.append(clean_caption)

                if part.inline_data is not None:
                    image = Image.open(BytesIO(part.inline_data.data))
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                        image.save(temp_file.name, format="PNG")
                        image_urls.append(temp_file.name)

            # Если дошли сюда — ключ сработал
            await key_manager.set_successful_key(api_key)

            # Лог для парсинга
            for i, url in enumerate(image_urls):
                print(f"===IMAGE_START==={i}===")
                print(url)
                print(f"===IMAGE_END==={i}===")

            for i, caption in enumerate(captions):
                print(f"===CAPTION_START==={i}===")
                print(caption)
                print(f"===CAPTION_END==={i}===")

            logger.info(f"image_urls: {image_urls}")
            return captions, image_urls

        # Если все ключи упали
        return None, "Не удалось обработать изображение ни с одним API-ключом."

    except Exception as e:
        logger.error("Ошибка при обработке изображения с Gemini:", exc_info=True)
        return None, "Ошибка при обработке изображения."




# === НОВАЯ ФУНКЦИЯ ДЛЯ ПОСЛЕДОВАТЕЛЬНОЙ ОЧЕРЕДИ ===
# === НОВАЯ ФУНКЦИЯ ДЛЯ ПОСЛЕДОВАТЕЛЬНОЙ ОЧЕРЕДИ ===
async def process_background_queue(bot, queue_data, status_msg, text_count, ignored_count):
    """
    Принимает список задач на обработку и выполняет их последовательно,
    обновляя сообщение со статусом в Telegram.
    """
    total = len(queue_data)
    processed_ai = 0
    processed_no_ai = 0
    errors = 0

    logging.info(f"Background: Начинаю последовательную обработку {total} файлов.")
    
    for index, item in enumerate(queue_data, 1):
        # 1. Обновляем статус: показываем, на каком сообщении мы сейчас "застопорились" / работаем
        current_text = (
            f"🔄 **Идет обработка постов...**\n\n"
            f"📝 Текстов сохранено сразу: `{text_count}`\n"
            f"⏭ Пропущено (не фото/текст): `{ignored_count}`\n\n"
            f"⏳ **AI Очередь:** `{index}` из `{total}`\n"
            f"👉 **Сейчас анализируется ID:** `{item['message_id']}`\n\n"
            f"✅ Успешно с AI: `{processed_ai}`\n"
            f"⚠️ Сохранено без AI (сбой нейросети): `{processed_no_ai}`\n"
            f"❌ Ошибок БД/загрузки: `{errors}`"
        )
        try:
            await status_msg.edit_text(current_text)
        except Exception:
            pass  # Игнорируем ошибки Telegram (например, если текст не изменился)

        try:
            # 2. Ждем выполнения анализа
            status = await analyze_and_save_background(
                bot=bot,
                channel_id=item['channel_id'],
                message_id=item['message_id'],
                file_id=item['file_id'],
                caption=item['caption'],
                date_timestamp=item['date_timestamp'],
                original_link=item['original_link']
            )
            
            # Подсчет статистики на основе ответа от функции
            if status == "success":
                processed_ai += 1
            elif status == "no_ai":
                processed_no_ai += 1
            else:
                errors += 1
                
            # Пауза между обработками картинок (кроме последней)
            if index < total:
                await asyncio.sleep(6)
                
        except Exception as e:
            logging.error(f"Background: Ошибка при обработке элемента очереди {item['message_id']}: {e}")
            errors += 1

    # 3. Финальное обновление статуса
    final_text = (
        f"✅ **Все задачи завершены!**\n\n"
        f"📝 Текстов сохранено: `{text_count}`\n"
        f"⏭ Пропущено: `{ignored_count}`\n\n"
        f"📊 **Итоги AI обработки ({total} фото):**\n"
        f"✅ С описанием AI: `{processed_ai}`\n"
        f"⚠️ Без описания (БД ок): `{processed_no_ai}`\n"
        f"❌ Ошибок скачивания/БД: `{errors}`"
    )
    try:
        await status_msg.edit_text(final_text)
    except Exception:
        pass

# === ОБНОВЛЕННАЯ ФУНКЦИЯ АНАЛИЗА ===
async def analyze_and_save_background(bot, channel_id, message_id, file_id, caption, date_timestamp, original_link=None):
    """
    Фоновая задача для анализа изображения и сохранения в Firebase.
    Реализована устойчивость к ошибкам: если AI падает, пост все равно сохраняется.
    """
    # ОБЯЗАТЕЛЬНО: Добавьте импорт get_smart_colors оттуда же, откуда импортируете остальное
    from bot import analyze_image_colors, calculate_normalized_brightness, get_smart_colors 
    
    logging.info(f"Background: Обработка поста {message_id} для {channel_id}...")

    # Инициализируем переменные по умолчанию (чтобы сохранить пост даже при сбое)
    ai_des = ""
    ai_style = ""
    analysis_data = {"error": "analysis_pending"}
    
    # 1. Скачивание и Цветовой анализ
    img_byte_arr = io.BytesIO()
    try:
        file_info = await bot.get_file(file_id)
        await file_info.download_to_memory(img_byte_arr)
        img_byte_arr.seek(0)
        image = Image.open(img_byte_arr)

        # === ОБНОВЛЕННЫЙ ЦВЕТОВОЙ АНАЛИЗ (КАК В /updcolor) ===
        try:
            b_dist, s_dist, h_dist = analyze_image_colors(image, 'neutral')
            norm_brightness = calculate_normalized_brightness(b_dist, s_dist)
            total_saturation = (s_dist.get('gray', 0) * 0.0 + s_dist.get('medium', 0) * 0.5 + s_dist.get('high', 0) * 1.0)
            
            # Вызываем умный алгоритм (распаковываем 5 возвращаемых значений, последние 2 игнорируем)
            dom_color, sec_color, ter_color, *_ = get_smart_colors(b_dist, s_dist, h_dist, norm_brightness)
            
            analysis_data = {
                "br": round(norm_brightness, 2),
                "sat": round(total_saturation, 2),
                "dom_color": dom_color,
                "sec_color": sec_color,
                "ter_color": ter_color  # <-- ДОБАВЛЕН ТРЕТИЙ ЦВЕТ
            }
        except Exception as color_e:
            logging.error(f"Background: Ошибка анализа цвета (игнорируем): {color_e}")
            analysis_data = {"error": "color_failed"}
        # =======================================================

    except Exception as dl_e:
        logging.error(f"Background: Критическая ошибка скачивания файла: {dl_e}")
        return "error" # <--- ДОБАВИТЬ ЭТО

    # 2. Анализ через Gemini (с перебором ключей)
    system_instruction = (
        "Ты искусствовед и помощник для онлайн-галереи. "
        "Твоя задача: проанализировать изображение и вернуть JSON. "
        "Поля JSON: 'description' (описание сюжета на русском языке, максимум 3 предложения, по данному тексту должна быть возможность найти это изображение в базе данных. Перечисли сюжет, атмоферу, детали, всё выделяет данное изображение) "
        "и 'style' (художественный стиль или техника исполнения на русском языке, например: 'Масло', 'Акрил', 'Digital Art', 'Скетч'). "
        "Не пиши ничего кроме JSON."
    )

        # Сбрасываем указатель байтов перед отправкой в Gemini
    gemini_success = False # <--- ДОБАВИТЬ СЮДА, чтобы переменная была доступна в конце функции
    
    # Сбрасываем указатель байтов перед отправкой в Gemini
    temp_file_path = None
    try:
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            image.save(temp_file, format="JPEG")
            temp_file_path = temp_file.name

        # Перебор ключей
        img_byte_arr.seek(0)
        gemini_success = False
        
        for api_key in key_manager.get_keys_to_try():
            try:
                client = genai.Client(api_key=api_key)
                
                # Загрузка
                gemini_file = client.files.upload(file=pathlib.Path(temp_file_path))
                
                # Ожидание обработки (polling)
                attempt = 0
                while gemini_file.state == "PROCESSING" and attempt < 10:
                    await asyncio.sleep(2)
                    gemini_file = client.files.get(name=gemini_file.name)
                    attempt += 1
                
                if gemini_file.state == "FAILED":
                    raise Exception("Gemini File State: FAILED")

                # Генерация
                response = await client.aio.models.generate_content(
                    model=PRIMARY_MODEL,
                    contents=[
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_uri(file_uri=gemini_file.uri, mime_type=gemini_file.mime_type),
                                types.Part(text="Return JSON with keys: description, style")
                            ]
                        )
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.5
                    )
                )

                if response.candidates and response.candidates[0].content.parts:
                    raw_json = response.candidates[0].content.parts[0].text
                    parsed = json.loads(raw_json)
                    ai_des = parsed.get("description", "")
                    ai_style = parsed.get("style", "")
                    
                    await key_manager.set_successful_key(api_key)
                    logging.info(f"Background: Gemini успешно обработал файл c ключом ...{api_key[-4:]}")
                    gemini_success = True
                    break # Успех - выходим из цикла ключей

            except Exception as gemini_e:
                logging.warning(f"Background: Ошибка Gemini (...{api_key[-4:]}): {gemini_e}. Пробуем следующий ключ...")
                # Не выходим, цикл продолжается со следующим ключом
                await asyncio.sleep(1) # Небольшая задержка перед следующим ключом

        if not gemini_success:
            logging.error(f"Background: Не удалось получить описание от Gemini после перебора всех ключей. Сохраняем без AI данных.")
            
    except Exception as e:
        logging.error(f"Background: Ошибка подготовки к AI анализу: {e}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass

    # 3. Сохранение в Firebase (ВЫПОЛНЯЕТСЯ ВСЕГДА, ДАЖЕ ЕСЛИ GEMINI УПАЛ)
    try:
        if str(channel_id) == "-1001479526905":
            channel_id = "anemonn"

        final_data = {
            "ai_des_ru": ai_des,
            "ai_style_ru": ai_style,
            "analysis": analysis_data,
            "caption": caption,
            "channel_id": channel_id,
            "date": date_timestamp,
            "file_id": file_id,
            "post_id": message_id,
            "status": "ok",
            "type": "photo",
            "original_link": original_link
        }

        save_success = save_art_post(channel_id, message_id, final_data)
        
        if save_success:
            logging.info(f"Background: Пост {message_id} успешно сохранен (AI desc: {'Yes' if ai_des else 'No'}).")
            try:
                reset_posts_cache()
            except:
                pass
            
            # ВОЗВРАЩАЕМ СТАТУС ДЛЯ ПРОГРЕСС-БАРА
            return "success" if gemini_success else "no_ai"
        else:
            logging.error(f"Background: Ошибка записи в Firebase для {message_id}.")
            return "error"
            
    except Exception as save_e:
        logging.error(f"Background: Критическая ошибка при сохранении в БД: {save_e}")
        return "error"


