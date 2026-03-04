from telegram import Update, InputMediaPhoto, ReplyKeyboardRemove, InputMediaDocument, InputMediaVideo, InlineKeyboardButton, InlineKeyboardMarkup, Message, InlineKeyboardMarkup, ReplyKeyboardMarkup, WebAppInfo, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler, CallbackQueryHandler, ContextTypes, JobQueue
from PIL import Image
from telegram.constants import ParseMode
from background import keep_alive
import asyncio
import requests
import logging
import os
import shutil
import io
import aiohttp
import tempfile
import re
from requests.exceptions import Timeout
from bs4 import BeautifulSoup
import wikipediaapi
import wikipedia
import gpt_helper
from gpt_helper import (
    add_to_context,
    generate_gemini_response,
    generate_image_description,
    set_user_role,
    limit_response_length,
    user_contexts,
    save_context_to_firebase,
    load_context_from_firebase,
    generate_audio_response,
    load_publications_from_firebase,
    save_publications_to_firebase,
    delete_from_firebase,
    save_channel_to_firebase,
    save_vk_keys_to_firebase,
    generate_plant_issue_response,
    generate_text_rec_response,
    generate_plant_help_response,
    reset_firebase_dialog,
    generate_video_response,
    generate_animation_response,
    generate_mushrooms_multi_response,
    translate_promt_with_gemini,
    get_user_model,
    set_user_model,
    generate_document_response,
    load_shared_publications,
    save_to_shared_publications,
    add_to_favorites,
    copy_to_shared_publications,
    save_twitter_keys_to_firebase,
    save_to_user_plants,
    load_user_plants,
    mark_watering,
    load_water_plants,
    delete_user_plant,
    save_to_user_mapplants,
    generate_mapplants_response,
    load_all_plants_data,
    generate_barcode_response,
    generate_barcode_analysis,
    generate_barcode_otzyvy,
    update_to_user_mapplants,
    get_user_preset,
    set_user_preset,
    Generate_gemini_image,
    generate_inpaint_gemini,
    get_all_tokens,
    set_all_tokens,
    get_last_successful_token,
    set_last_successful_token,
    generate_gemini_inline_response,
    save_inline_query_to_firebase,
    load_user_inline_queries,
    save_ozon_tracking_to_firebase,
    load_ozon_tracking_from_firebase,
    load_ozon_product_firebase,
    delete_ozon_product_firebase,
    update_ozon_tracking_item,
    response_ingredients,
    response_animal,
    load_entire_database,
    generate_calories_response,
    generate_composition_comparison_response,
    generate_products_response,
    get_user_timers
)
from vpn_service import run_vpn_update, create_qr_code, SUB_FILE_PATH
from collections import deque
from aiohttp import ClientSession, ClientTimeout, FormData
import json
import os
from gpt_helper import user_roles, DEFAULT_ROLES, GAME_ROLES
import base64
import random
import firebase_admin
from firebase_admin import credentials, db
import re
import logging
import aiohttp
import wikipediaapi  # Импортируем библиотеку
import wikipedia
from telegram.error import Forbidden, TelegramError, TimedOut
from telegram.helpers import escape, mention_html
from huggingface_hub import AsyncInferenceClient
import os
from dotenv import load_dotenv
import html
from datetime import datetime, timezone, timedelta, time as dt_time
import calendar
import time
import uuid
from io import BytesIO
# Укажите ваши токены и ключ для imgbb
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN не задан в переменных окружения")
TELEGRAPH_TOKEN = 'c244b32be4b76eb082d690914944da14238249bbdd55f6ffd349b9e000c1'
IMGBB_API_KEY = '0f0f15b17c990ae3d20936ec8e614493'
GROUP_CHAT_ID = -1002233281756

# Состояния
ASKING_FOR_ARTIST_LINK, ASKING_FOR_AUTHOR_NAME, ASKING_FOR_IMAGE, EDITING_FRAGMENT, ASKING_FOR_FILE, ASKING_FOR_OCR, RUNNING_GPT_MODE, ASKING_FOR_ROLE, ASKING_FOR_FOLLOWUP,AWAITING_FOR_FORWARD, WAITING_FOR_NEW_CAPTION = range(11)
# Сохранение данных состояния пользователя
user_data = {}
publish_data = {}
users_in_send_mode = {}
media_group_storage = {}
is_search_mode = {}
is_ocr_mode = {}
is_gpt_mode = {}
is_role_mode = {}
is_asking_mode = {}
user_presets = {} 
user_models = {}
waiting_for_forward = {}
waiting_for_vk = {}
waiting_for_caption = {}
waiting_for_twitter = {}
waiting_for_coordinates = {} 
# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4096
# Основные функции
# Загружаем данные при запуске бота
media_group_storage = load_publications_from_firebase()


# Имя файла базы данных (должен лежать рядом с bot.py)
DB_FILENAME = "cat_facts.json"

async def cat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fact = None
    
    # Генерируем случайное число от 0.0 до 1.0
    # Если меньше 0.75 (75%), пытаемся взять из локальной базы
    use_local_db = random.random() < 0.75

    if use_local_db:
        if os.path.exists(DB_FILENAME):
            try:
                with open(DB_FILENAME, "r", encoding="utf-8") as f:
                    local_facts = json.load(f)
                    if local_facts:
                        fact = random.choice(local_facts)
            except Exception as e:
                print(f"Ошибка чтения локальной БД: {e}")
                # Если ошибка, fact останется None, и мы пойдем в API
        else:
            print(f"Файл {DB_FILENAME} не найден. Использую API.")

    # Если факт не был получен (выпали 25% ИЛИ ошибка локальной БД ИЛИ файл пуст)
    if not fact:
        url = "https://meowfacts.herokuapp.com/?lang=rus"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # API возвращает список в поле "data"
                        fact = data.get("data", [None])[0]
                    else:
                        print(f"Ошибка API статус: {resp.status}")
        except Exception as e:
            print("Ошибка при запросе к API:", e)

    # Финальная отправка
    if fact:
        await update.message.reply_text(fact)
    else:
        # Если сломалось вообще всё (и файл, и API)
        await update.message.reply_text("Котики сегодня стесняются и не хотят делиться фактами 😿")


# Функция для сохранения данных в JSON файл
def save_media_group_data(media_group_storage, user_id):
    """Сохраняет данные публикаций для указанного пользователя в Firebase."""
    try:
        logger.info(f"Пользователь {user_id} сохраняет публикацию")

        
        # Приведение типа ключей
        user_publications = media_group_storage.get(
            user_id if user_id in media_group_storage else str(user_id), {}
        )
        
        # Проверка данных
        if not user_publications:
            logger.warning(f"Нет публикаций для user_id={user_id}")
            return
        
        # Сохраняем данные текущего пользователя
        for message_id, data in user_publications.items():
            save_publications_to_firebase(user_id, message_id, data)
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных пользователя ")

async def data_command(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data
    if user_data:
        data_str = json.dumps(user_data, indent=2, ensure_ascii=False)
        with open("user_data.json", "w", encoding="utf-8") as file:
            file.write(data_str)
        await update.message.reply_document(document="user_data.json", filename="user_data.json")
    else:
        await update.message.reply_text("Ваши данные пусты.")
        
ALLOWED_USER_ID = 6217936347

async def userid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    """Обрабатывает команду /userid и выводит все найденные telegram user_id (7-12 цифр)."""
    if update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return
    
    try:
        # Загружаем всю базу
        data = load_entire_database()

        # Превращаем в строку для поиска цифр
        data_str = str(data)

        # Ищем все последовательности из 7–12 цифр
        matches = re.findall(r'(?<!\d)\d{7,12}(?!\d)', data_str)
        # Убираем дубли
        unique_ids = sorted(set(matches))

        if unique_ids:
            result = ", ".join(unique_ids)
        else:
            result = "Не найдено user_id."

        await update.message.reply_text(result)

    except Exception as e:
        logging.error(f"Ошибка при выполнении /userid: {e}")
        await update.message.reply_text("Произошла ошибка при обработке команды.")

USER_IDS = [19029917, 20618514, 25377082, 35194055, 57673989, 68017381, 69314002, 92703779, 92852789, 93192260, 104865552, 130502292, 146351163, 147351371, 190945533, 205900446, 223677807, 242283851, 257112890, 262262816, 264003592, 290031541, 298066779, 300025675, 302379214, 306469709, 326611724, 381379786, 385928103, 393126119, 394159899, 396838917, 419817885, 439506900, 442646559, 459261734, 474195974, 516232486, 577681862, 586787646, 596973027, 611704867, 624317946, 626558159, 631224997, 666993239, 668328654, 676271492, 704874880, 707549030, 739162690, 745120986, 754607983, 775345852, 780334362, 781580201, 789688948, 801586478, 814924951, 815610820, 818026781, 842797437, 860705945, 866648983, 873360980, 873413482, 874134295, 915612655, 919008054, 937801646, 960294998, 972481587, 988873023, 989325372, 1046743582, 1096125853, 1107964479, 1126225257, 1149574816, 1203287768, 1214476327, 1219361456, 1220271061, 1221533002, 1222227099, 1225705380, 1240550482, 1247773844, 1293084893, 1314221656, 1351826504, 1366051623, 1440150049, 1454145687, 1465628473, 1469390426, 1471915085, 1519572343, 1521709699, 1543028708, 1609905164, 1613196589, 1659632043, 1668374416, 1676664165, 1742524654, 1774870861, 1789124483, 1809652677, 1813042277, 1824130766, 1824742804, 1841170415, 1848215295, 1915179934, 1976720451, 2016643148, 2030763957, 2047583108, 2057806777, 2100503597, 2104266399, 2469483415, 5027345967, 5106034281, 5204148826, 5234665650, 5256952624, 5325900170, 5346582203, 5629330385, 5806164256, 5972422679, 6033575010, 6217936347, 6307808189, 6333902342, 6442774124, 6519046474, 6546556436, 6702495691, 7208124838, 7372529001, 7474302646, 7815486514, 11723743486]




from telegram import MessageEntity

# Настройка логирования для отладки
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def sendall(update: Update, context: CallbackContext) -> None:
    """
    Отправляет сообщение (копируя его) указанным пользователям.
    Список пользователей указывается прямо в команде: /send id1,id2,id3
    """
    if update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return
    
    if not update.message or not update.message.reply_to_message:
        await update.message.reply_text(
            "Используйте команду /send в ответ на сообщение, которое нужно разослать."
        )
        return

    if not context.args:  # если не указаны ID
        await update.message.reply_text(
            "Пожалуйста, укажите ID пользователей через запятую. "
            "Пример: /send 12345,67890"
        )
        return

    try:
        user_ids_to_send = [int(uid.strip()) for uid in context.args[0].split(',')]
    except ValueError:
        await update.message.reply_text(
            "Некорректный формат ID. Используйте запятую для разделения: /send 12345,67890"
        )
        return

    if not user_ids_to_send:
        await update.message.reply_text("Список ID пользователей для рассылки пуст.")
        return

    replied_message = update.message.reply_to_message
    success_count = 0
    fail_count = 0

    for user_id in user_ids_to_send:
        try:
            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=replied_message.chat.id,
                message_id=replied_message.message_id,
            )
            success_count += 1
        except Exception as e:
            fail_count += 1
            logger.error(
                f"Ошибка при копировании сообщения пользователю {user_id} "
                f"(ID сообщения: {replied_message.message_id}): {e}",
                exc_info=True
            )

    await update.message.reply_text(
        f"Рассылка завершена. Успешно отправлено: {success_count}. Ошибок: {fail_count}."
    )
    
async def send_reply_with_limit(text, max_length=4096):
    """Обрабатывает текст через escape_gpt_markdown_v2 и разбивает его на части"""
    escaped_text = escape_gpt_markdown_v2(text)
    return split_text_preserving_tags(escaped_text, max_length)



def ts_to_str(ts):
    """Переводит timestamp (ms) → читабельную дату."""
    try:
        return datetime.datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(ts)

def format_user_timers(user_data):
    """Преобразует базу данных пользователя в красивый текст."""
    if not user_data:
        return "У вас пока нет сохранённых таймлайнов."

    out = []

    for timer_id, timer in user_data.items():
        title = timer.get("title", "Без названия")
        created = ts_to_str(timer.get("created_at"))

        out.append(f"==============================")
        out.append(f"📌 **{title}**")
        out.append(f"Создан: {created}")
        out.append(f"==============================\n")

        entries = timer.get("entries", {})

        if not entries:
            out.append("  (нет отметок)\n")
            continue

        for entry_id, entry in entries.items():
            ts = entry.get("timestamp", "??:??")
            text = entry.get("text", "(без текста)")
            created_e = ts_to_str(entry.get("created_at"))
            episode = entry.get("episode")

            out.append(f"▶️ Время: {ts}")
            if episode:
                out.append(f"   Серия: {episode}")
            out.append(f"   Текст: {text}")
            out.append(f"   Добавлено: {created_e}")
            out.append("")  # пустая строка

    return "\n".join(out)


async def send_timer_app_button(update, context):
    user_id = update.effective_user.id

    # 1. Получаем данные
    user_timers = get_user_timers(user_id)

    # 2. Проверка: если данных нет — отправляем ТОЛЬКО кнопку
    if not user_timers:
        webapp_url = "https://anemonne.onrender.com/timer-app/"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Открыть таймер ⏱", web_app=WebAppInfo(url=webapp_url))]
        ])

        await update.message.reply_text(
            "🌸Это приложение для добавление заметок, напоминаний, мыслей во время просотра фильмов, сериалов, аниме, прослушивания аудиокниг и тд. \n\nВ нём вы сможете запустить таймер и параллельно с просмотром делать быстрые заметки с привязкой ко времени. Чтобы не забыть где и на какой секунде вам встретилось что-то интересное.",
            reply_markup=keyboard
        )
        return

    # 3. Если данные есть — формируем красивый текст
    formatted_text = format_user_timers(user_timers)

    # 4. Сохраняем файл
    filename = f"your_timers_{user_id}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(formatted_text)

    # 5. Отправляем файл
    with open(filename, "rb") as file:
        await update.message.reply_document(
            document=file,
            filename=filename,
            caption="Резервная копия ваших заметок и таймлайнов. Вы сможете их посмотреть или куда-то перенести даже если бот перестанет работать."
        )

    # 6. И отправляем кнопку WebApp
    webapp_url = "https://anemonne.onrender.com/timer-app/"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Открыть таймер ⏱", web_app=WebAppInfo(url=webapp_url))]
    ])

    await update.message.reply_text(
        "Открыть приложение:",
        reply_markup=keyboard
    )











import httpx
import logging
import asyncio
import random
import httpx
from urllib.parse import urlparse, parse_qs  # <--- ЭТОГО НЕ ХВАТАЛО
# Ссылка на RAW файл (преобразована из вашей ссылки)
# Настройка логгера (чтобы выводилось в консоль)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

PROXY_URL = "https://raw.githubusercontent.com/Argh94/Proxy-List/main/MTProto.txt"

def normalize_proxy(line):
    """
    Превращает ссылку вида tg://proxy?server=... или https://t.me...
    в формат IP:PORT:SECRET
    """
    line = line.strip()
    if not line:
        return None

    # Если строка уже похожа на ip:port:secret (простая проверка)
    # Проверяем, что нет "http" и есть хотя бы 2 двоеточия
    if "server=" not in line and line.count(':') >= 2 and "://" not in line:
        return line

    try:
        # Пытаемся распарсить как URL
        parsed = urlparse(line)
        query = parse_qs(parsed.query)
        
        # Извлекаем параметры (parse_qs возвращает списки)
        server = query.get('server', [None])[0]
        port = query.get('port', [None])[0]
        secret = query.get('secret', [None])[0]

        if server and port and secret:
            # Иногда в конце домена бывает точка (например .info.), её лучше убрать для чистоты
            server = server.rstrip('.')
            return f"{server}:{port}:{secret}"
        else:
            return None
    except Exception as e:
        # Для отладки можно раскомментировать, чтобы видеть ошибки парсинга
        # logger.error(f"Ошибка парсинга строки {line}: {e}")
        return None

async def fetch_proxies():
    """Скачивает и нормализует список прокси."""
    logger.info(f"🚀 [FETCH] Загрузка списка: {PROXY_URL}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(PROXY_URL, timeout=10.0)
            if response.status_code == 200:
                raw_lines = response.text.splitlines()
                valid_proxies = []
                
                for line in raw_lines:
                    normalized = normalize_proxy(line)
                    if normalized:
                        valid_proxies.append(normalized)

                logger.info(f"✅ [FETCH] Скачано строк: {len(raw_lines)}. Распознано прокси: {len(valid_proxies)}")
                if valid_proxies:
                    logger.info(f"📝 [FETCH] Пример: {valid_proxies[0]}")
                return valid_proxies
            else:
                logger.error(f"❌ [FETCH] Ошибка сервера: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ [FETCH] Ошибка сети: {e}")
    return []

async def check_proxy_tcp(proxy_str, timeout=3.0):
    """
    Проверяет доступность порта (TCP Connect).
    """
    try:
        parts = proxy_str.rsplit(':', 2)
        if len(parts) < 3:
            return None
        
        host = parts[0]
        port = int(parts[1])

        # Убираем скобки IPv6 и лишние точки
        host = host.replace("[", "").replace("]", "").rstrip('.')

        # Пытаемся подключиться к порту
        future = asyncio.open_connection(host, port)
        reader, writer = await asyncio.wait_for(future, timeout=timeout)
        
        # Если подключились — закрываем соединение и возвращаем успех
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        
        logger.info(f"✅ [ALIVE] Живой: {host}:{port}") 
        return proxy_str
        
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return None
    except Exception as e:
        # logger.debug(f"Ошибка проверки {proxy_str}: {e}")
        return None

async def get_working_proxies(target_count=20):
    logger.info("🏁 [START] Поиск рабочих прокси...")
    all_proxies = await fetch_proxies()

    if not all_proxies:
        return []

    random.shuffle(all_proxies)
    
    # Берем с запасом (например, 300 штук), чтобы найти 20 рабочих
    check_queue = all_proxies[:300] 

    working_proxies = []
    batch_size = 50 # Увеличил размер пачки для скорости
    
    # Разбиваем на пачки
    for i in range(0, len(check_queue), batch_size):
        if len(working_proxies) >= target_count:
            break
            
        batch = check_queue[i : i + batch_size]
        logger.info(f"🔄 [BATCH] Проверка {i}..{i+len(batch)} из {len(check_queue)}...")
        
        tasks = [check_proxy_tcp(p) for p in batch]
        results = await asyncio.gather(*tasks)
        
        for res in results:
            if res and len(working_proxies) < target_count:
                if res not in working_proxies:
                    working_proxies.append(res)
    
    logger.info(f"🏁 [FINISH] Найдено: {len(working_proxies)}")
    return working_proxies


def create_keyboard(proxies):
    keyboard = []
    row = []
    
    for i, proxy_str in enumerate(proxies, 1):
        try:
            parts = proxy_str.rsplit(':', 2)
            if len(parts) >= 3:
                ip, port, secret = parts[0], parts[1], parts[2]
                url = f"https://t.me/proxy?server={ip}&port={port}&secret={secret}"
                button = InlineKeyboardButton(f"Proxy {i}", url=url)
                row.append(button)
                
                if len(row) == 3:
                    keyboard.append(row)
                    row = []
        except Exception:
            pass
    
    if row:
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton("🔄 Прислать ещё", callback_data="refresh_proxies")])
    return InlineKeyboardMarkup(keyboard)

async def send_proxies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Хендлер команды /proxy или кнопки"""
    is_callback = False
    message = None
    
    if update.callback_query:
        is_callback = True
        query = update.callback_query
        await query.answer("Загружаю...")
        message = query.message
        await message.edit_text("🔍 Ищу живые прокси (парсинг ссылок)...")
    else:
        message = update.message
        await message.reply_text("🔍 Ищу живые прокси (парсинг ссылок)...")

    proxies = await get_working_proxies(20)

    if not proxies:
        text = "😔 Живых прокси не найдено. Попробуйте позже."
        reply_markup = None
    else:
        text = f"✅ Найдено {len(proxies)} рабочих прокси:"
        reply_markup = create_keyboard(proxies)

    if is_callback:
        await message.edit_text(text=text, reply_markup=reply_markup)
    else:
        await message.reply_text(text=text, reply_markup=reply_markup)












async def send_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Определяем "куда отвечать"
    if update.callback_query:
        await update.callback_query.answer()
        target = update.callback_query.message
    else:
        target = update.message

    await target.reply_text("🔍 Ищу файл подписки...")

    # Если файла еще нет — запускаем обновление
    if not SUB_FILE_PATH.exists():
        await target.reply_text("⚠️ Файл еще не создан — запускаю обновление, подождите...")
        count = await run_vpn_update()

        if count == 0:
            return await target.reply_text("❌ Не удалось собрать рабочие VPN-конфиги. Попробуйте позже.")
        else:
            await target.reply_text(f"✔️ Собрано {count} рабочих конфигов! Формирую ссылку...")

    # Формируем ссылку на подписку
    app_url = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:80')
    sub_url = f"{app_url}/static/sub.txt"

    # Генерируем QR
    qr_bio = create_qr_code(sub_url)

    caption_text = (
        f"🔐 <b>Ваша подписка обновлена!</b>\n\n"
        f"🔗 <b>Ссылка для приложения:</b>\n<code>{sub_url}</code>\n\n"
        f"ℹ️ <i>Вставьте эту ссылку в NekoBox, v2rayNG, Streisand, V2Box и др. как 'Subscription URL'.</i>\n"
        f"📘 Подробная <a href=\"https://telegra.ph/Vpn-Instrukciya-11-26\">инструкция</a> по настройке."
    )

    # Кнопка "Закрыть"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Закрыть", callback_data="close")]
    ])

    # Отправляем QR + текст + кнопку
    await target.reply_photo(
        photo=qr_bio,
        caption=caption_text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )




VPN_BUTTONS = {
    "black": {
        "name": "Чёрные списки",
        "img": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/QR-codes/BLACK_VLESS_RUS-QR.png",
        "txt": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt"
    },
    "black_alt": {
        "name": "Чёрные списки (альтернатива)",
        "img": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/QR-codes/BLACK_SS%2BAll_RUS-QR.png",
        "txt": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_SS%2BAll_RUS.txt"
    },
    "black_mob": {
        "name": "Чёрные списки (мобильные)",
        "img": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/QR-codes/BLACK_VLESS_RUS_mobile_QR.png",
        "txt": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt"
    },
    "white_cable": {
        "name": "Белые списки (кабель)",
        "img": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/QR-codes/WHITE-CIDR-RU-all-QR.png",
        "txt": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-all.txt"
    },
    "white_cable2": {
        "name": "Белые списки (кабель, альтернативный)",
        "img": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/QR-codes/WHITE-CIDR-RU-all-QR.png",
        "txt": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-all.txt"
    },    
    "white_mobile1": {
        "name": "Белые списки (мобильный, вариант 1)",
        "img": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/QR-codes/Vless-Reality-White-Lists-Rus-Mobile-QR.png",
        "txt": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt"
    },
    "white_mobile2": {
        "name": "Белые списки (мобильный, вариант 2)",
        "img": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/QR-codes/Vless-Reality-White-Lists-Rus-Mobile-2-QR.png",
        "txt": "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt"
    }    
}

VPNINSTRUCTION_TEXT = """
<b>Краткая инструкция</b>

<b>1)</b> Выберите основной тип VPN-ключей, который вам нужен (можно подключить несколько подписок).

<b>2)</b> Бот пришлёт вам QR-картинку и ссылку — вы можете использовать любой вариант (QR или ссылку).

<b>3)</b> Скачайте и установите программу для использования ключей. Популярные клиенты:
• NekoBox, v2rayNG, Streisand, V2Box и многие другие.

Ниже бот пришлёт вам установщики для андроид и windows, либо можете скачать их сами:
• <a href="https://github.com/MatsuriDayo/NekoBoxForAndroid/releases">Версия для Android</a>
• <a href="https://github.com/Matsuridayo/nekoray/releases">Версия для PC</a>
Так же по ссылкам есть версия на Линукс

На мак и ios можете поискать что-то сами, напрмиер V2Box, sing-box, Hiddify и др

<b>4)</b> Добавьте в программу подписку по QR-коду или по скопированной ссылке. Можно создать несколько групп/плейлистов и в каждую добавить отдельный набор подписок (например — белые/чёрные списки).

<b>5)</b> В приложении выполните TCP-Ping и URL-тесты, затем выберите «удалить нерабочие» (или аналогичный пункт в вашем клиенте).

<b>6)</b> Из оставшихся серверов подключитесь к любому и пользуйтесь. Если многие сервера перестанут работать — нажмите «Обновить подписку», и список автоматически заменится на актуальный.

Для подробной инструкции со скринами читайте на <a href="https://telegra.ph/Vpn-Instrukciya-11-26">telegra.ph — VPN инструкция</a>.
"""




async def fileid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверьте, что команда — в reply на сообщение
    replied = update.message.reply_to_message
    if not replied:
        await update.message.reply_text("⛔️ Пожалуйста, используйте /fileid в ответ на сообщение с файлом.")
        return

    # Попробуем извлечь file_id из разных типов media
    file_id = None
    if replied.document:
        file_id = replied.document.file_id
    elif replied.photo:
        # photo — список размеров, обычно берем последний (самое большое/качественное)
        file_id = replied.photo[-1].file_id
    elif replied.video:
        file_id = replied.video.file_id
    elif replied.audio:
        file_id = replied.audio.file_id
    elif replied.voice:
        file_id = replied.voice.file_id
    elif replied.video_note:
        file_id = replied.video_note.file_id
    else:
        await update.message.reply_text("⚠️ Не найден файл в replied-сообщении. Это должно быть фото, документ, видео, аудио и т.п.")
        return

    await update.message.reply_text(f"✅ file_id: `{file_id}`")





# ============================== #
#   /vpn — главное меню
# ============================== #



async def vpn_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(b["name"], callback_data=f"vpn_{key}")]
        for key, b in VPN_BUTTONS.items()
    ]

    # Новая кнопка — именно здесь (до старых ключей)
    keyboard += [
        [InlineKeyboardButton("Сгенерировать файл подписки", callback_data="vpn_generate_sub")],
        [InlineKeyboardButton("Старые альтернативные ключи", callback_data="vpn_old")],
        [InlineKeyboardButton("Инструкция", callback_data="vpn_instruction")],
    ]
    
    message_html = (
        "<b>VPN конфигурации</b>\n"
        "Здесь вы можете скачать рабочие VPN ключи и подключиться по ссылке или через QR.\n\n"
        "<b>Выберите один из вариантов:</b>\n\n"
        "1. <b>Основные ключи для обхода чёрных списков</b>\n\n"
        "2. <b>Альтернативные ключи для обхода чёрных списков</b>\n\n"
        "3. <b>Ключи для обхода \"Белых списков\" с кабельного интернета</b>\n\n"
        "4. <b>Ключи для обхода \"Белых списков\" с мобильного</b>\n\n"
        "5. <b>Сгенерировать файл подписки</b>\n"
        "<i>Бот генерирует файл подписки на VPN сервисы, код написан подписчиком бота.</i>\n\n"
        "6. <b>Старый способ получения ключей</b>\n"
        "<i>Если всё что есть выше не работает.</i>\n\n"
        "<b>В инструкции</b> — вся необходимая подробная информация."
    )

    await update.message.reply_text(
        message_html,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )




# ============================== #
#  Обработка кнопок VPN
# ============================== #

async def vpn_show_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    key = query.data.replace("vpn_", "")
    
    # Защита: проверяем, что ключ вообще есть в словаре
    if key not in VPN_BUTTONS:
        return
        
    cfg = VPN_BUTTONS[key]
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Закрыть", callback_data="close")]])

    try:
        # Пытаемся отправить с фото
        await query.message.reply_photo(
            photo=cfg["img"],
            caption=f"<b>{cfg['name']}</b>\n\n<code>{cfg['txt']}</code>",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    except Exception as e:
        # Если фото сломано (например удалено с GitHub), отправляем просто текстом
        print(f"Ошибка отправки фото для {key}: {e}")
        await query.message.reply_text(
            text=f"<b>{cfg['name']}</b>\n\n⚠️ <i>Не удалось загрузить QR-код.</i>\n\nСсылка на подписку:\n<code>{cfg['txt']}</code>",
            parse_mode="HTML",
            reply_markup=keyboard
        )

# ============================== #
#    Инструкция
# ============================== #

async def vpn_instruction(update, context):
    q = update.callback_query
    await q.answer()

    # Отправляем текст инструкции
    await q.message.reply_text(
        VPNINSTRUCTION_TEXT,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Закрыть", callback_data="close")]
        ])
    )

    # Первый файл
    await context.bot.send_document(
        chat_id=q.message.chat_id,
        document="BQACAgIAAxkBAAEBar9pMwdm1ubsbQdF3lVzKCJrihRDIgACoIsAAnZ0mElZiYuMXkseXDYE"
    )

    # Второй файл
    await context.bot.send_document(
        chat_id=q.message.chat_id,
        document="BQACAgIAAxkBAAEBas9pMwtP87XA5Hr9DfH34cO9AAEINfcAAumLAAJ2dJhJkFj8sDNIn942BA"
    )
# ============================== #
#   Вызов твоей функции с ключами
# ============================== #

async def vpn_old(update, context):
    q = update.callback_query
    await q.answer()
    await send_keys(update.callback_query, context, 0)   # index = 0 (меняешь сам)

# ============================== #
#   Кнопка закрыть
# ============================== #

async def close_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.delete()




# Список ваших raw.githubusercontent ссылок
GITHUB_LINKS = [
    "https://raw.githubusercontent.com/sakha1370/OpenRay/refs/heads/main/output/all_valid_proxies.txt",#9
    "https://raw.githubusercontent.com/mehran1404/Sub_Link/refs/heads/main/V2RAY-Sub.txt",#6
    "https://raw.githubusercontent.com/wuqb2i4f/xray-config-toolkit/main/output/base64/mix-uri",#7
    "https://raw.githubusercontent.com/STR97/STRUGOV/refs/heads/main/STR.BYPASS#STR.BYPASS%F0%9F%91%BE",#10
    "https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/refs/heads/main/Config/vless.txt",#random
]

# Словарь для хранения индекса ссылки для каждого пользователя
user_index = {}


def get_repo_name(url: str) -> str:
    """Вытащить название после .com (например: sakha1370, sevcator, yitong2333)"""
    return url.split("githubusercontent.com/")[1].split("/")[0]


async def fetch_keys(url: str):
    """Скачать и распарсить ключи из raw.githubusercontent"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            text = await resp.text()

    keys = re.findall(r"(?:vmess|vless)://[^\s]+", text)
    return keys


async def send_keys(update_or_query, context: ContextTypes.DEFAULT_TYPE, index: int):
    url = GITHUB_LINKS[index]
    repo_name = get_repo_name(url)
    keys = await fetch_keys(url)

    if not keys:
        text = "❌ Ключи не найдены."
        if hasattr(update_or_query, "message") and update_or_query.message:
            await update_or_query.message.reply_text(text)
        else:
            await update_or_query.message.reply_text(text)
        return

    # Проверка: это последняя ссылка?
    if url.endswith("V2RayRoot/V2RayConfig/refs/heads/main/Config/vless.txt"):
        selected_keys = random.sample(keys, min(7, len(keys)))
        msg_text = (
            f"<b>{repo_name}</b>\n\n7 случайных ключей:\n"
            f"<pre>{html.escape('\n\n'.join(selected_keys))}</pre>"
        )
    else:
        # Стандартная логика
        top_keys = keys[:50]
        selected_top = random.sample(top_keys, min(5, len(top_keys)))
        selected_all = random.sample(keys, min(3, len(keys)))

        msg_text = (
            f"<b>{repo_name}</b>\n\n5 новых случайных ключей:\n<pre>{html.escape('\n\n'.join(selected_top))}</pre>\n\n"
            f"\n3 случайных ключа:\n<pre>{html.escape('\n\n'.join(selected_all))}</pre>"
        )

    # Клавиатура с кнопками
    keyboard = [
        [InlineKeyboardButton("📖 Инструкция", callback_data="vpninstruction_show")],
        *[
            [InlineKeyboardButton(f"Ещё ключи из {get_repo_name(url)}", callback_data=f"more_keys_{i}")]
            for i, url in enumerate(GITHUB_LINKS)
        ],
        [InlineKeyboardButton("📥 Скачать файлом", callback_data="download_file")]
    ]

    if hasattr(update_or_query, "message") and update_or_query.message:
        await update_or_query.message.reply_text(
            msg_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    else:
        await update_or_query.message.reply_text(
            msg_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        

async def send_instruction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    instruction_text = """
<b>Инструкция по использованию ключей:</b>\n\n
1) Скачайте NekoBox или любую аналогичную программу поддерживающую vless и vmess ключей:
• <a href="https://github.com/MatsuriDayo/NekoBoxForAndroid/releases">Версия для Android</a>
• <a href="https://github.com/Matsuridayo/nekoray/releases">Версия для PC</a>\n\n
2) Скопируйте 5/3 случайных ключей из сообщения бота или скачайте файлом сразу много ключей.\n\n
3) Откройте NekoBox, нажмите кнопку добавления ключа в правом верхнем углу.
Затем:
• "Импорт из буфера обмена" (если скопировали ключи)
• "Импорт из файла" (если скачали файл)\n\n
4) После появления новых ключей в списке доступных нажмите три точки в правом верхнем углу и поочередно пройдите:
• "TCP тест"
• "URL тест"\n\n
5) В том же меню нажмите "Удалить недоступные".\n\n
Готово ✅ Все оставшиеся ключи (или хотя бы часть из них) должны работать.
Если перестанут – повторите действия ещё раз, очистив перед этим NekoBox.\n\n
<i>Инструкция написана для Android-версии, но на PC процесс похожий, только кнопки расположены иначе.</i>
"""

    # Кнопка "Закрыть окно"
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("❌ Закрыть окно", callback_data="ozondelete_msg")]]
    )

    if update.message:
        await update.message.reply_text(
            instruction_text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=keyboard
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            instruction_text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=keyboard
        )
        await update.callback_query.answer()

async def vpn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_index[user_id] = 0
    await send_keys(update, context, 0)


async def more_keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # Узнаём, по какой кнопке нажали
    data = query.data  # например: "more_keys_1"
    index = int(data.split("_")[-1])

    user_index[user_id] = index
    await send_keys(query, context, index)


async def download_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Собираем ключи по правилам: для обычных ссылок — 40 верхних, 20 нижних и 30 случайных; для последней — 70 случайных"""
    query = update.callback_query
    await query.answer()

    all_keys = []
    for url in GITHUB_LINKS:
        keys = await fetch_keys(url)
        if not keys:
            continue

        if url.endswith("V2RayRoot/V2RayConfig/refs/heads/main/Config/vless.txt"):
            # Спец-логика для последней ссылки
            selected = random.sample(keys, min(70, len(keys)))
        else:
            # Общая логика
            selected = keys[:40] + keys[-20:]
            remaining_keys = list(set(keys) - set(selected))
            if len(remaining_keys) >= 30:
                selected += random.sample(remaining_keys, 30)
            else:
                selected += remaining_keys
        all_keys.extend(selected)

    if not all_keys:
        await query.message.reply_text("❌ Ключи не найдены.")
        return

    file_content = "\n".join(all_keys)
    bio = io.BytesIO(file_content.encode("utf-8"))
    bio.name = "vpn_keys.txt"

    await query.message.reply_document(InputFile(bio))













def split_text_preserving_tags(text, max_length):
    """Разбивает текст, сохраняя последовательность открытых и закрытых тегов"""
    parts = []
    current_part = ""
    open_tags = []

    for line in text.split("\n"):
        if len(current_part) + len(line) + 1 > max_length:
            # Закрываем все открытые теги перед разрывом
            for tag in reversed(open_tags):
                current_part += f"\n{tag}"

            parts.append(current_part)
            current_part = ""

            # Повторяем открытые теги в новом фрагменте
            for tag in open_tags:
                current_part += f"{tag}\n"

        # Обновляем список открытых тегов
        if line.strip().startswith("```"):
            tag = line.strip()
            if tag in open_tags:
                open_tags.remove(tag)  # Закрываем блок
            else:
                open_tags.append(tag)  # Открываем блок

        current_part += line + "\n"

    # Добавляем последний кусок
    if current_part:
        for tag in reversed(open_tags):
            current_part += f"\n{tag}"  # Закрываем оставшиеся теги
        parts.append(current_part)

    return parts





def escape_gpt_markdown_v2(text):
    # Проверка на наличие экранирования и удаление, если оно присутствует
    if re.search(r'\\[\\\*\[\]\(\)\{\}\.\!\?\-\#\@\&\$\%\^\&\+\=\~]', text):
        # Убираем экранирование у всех специальных символов Markdown
        text = re.sub(r'\\([\\\*\[\]\(\)\{\}\.\!\?\-\#\@\&\$\%\^\&\+\=\~])', r'\1', text)

    # Временная замена ** на |TEMP| без экранирования
    text = re.sub(r'\*\*(.*?)\*\*', r'|TEMP|\1|TEMP|', text)
    logger.info(f"text {text}")
    # Временная замена ``` на |CODE_BLOCK| для исключения из экранирования
    text = text.replace('```', '|CODE_BLOCK|')

    # Временная замена ` на |INLINE_CODE| для исключения из экранирования
    text = text.replace('`', '|INLINE_CODE|')

    # Экранируем все специальные символы
    text = re.sub(r'(?<!\\)([\\\*\[\]\(\)\{\}\.\!\?\-\#\@\&\$\%\^\&\+\=\~\<\>])', r'\\\1', text)
    logger.info(f"text2 {text}")
    # Восстанавливаем |TEMP| обратно на *
    text = text.replace('|TEMP|', '*')

    # Восстанавливаем |CODE_BLOCK| обратно на ```
    text = text.replace('|CODE_BLOCK|', '```')

    # Восстанавливаем |INLINE_CODE| обратно на `
    text = text.replace('|INLINE_CODE|', '`')

    # Экранируем символ |
    text = re.sub(r'(?<!\\)\|', r'\\|', text)

    # Экранируем символ _ везде, кроме конца строки
    text = re.sub(r'(?<!\\)_(?!$)', r'\\_', text)

    return text



# Загружаем данные при запуске бота

async def mainhelp_callback(update: Update, context: CallbackContext):
    """Обработчик нажатия на кнопку для вызова mainhelp."""
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие

    # Заранее заготовленный текст с HTML-разметкой
    help_text = """
    В боте есть множество функций, разделённых по кнопкам:

    <b>===Кнопка "Найти автора"===</b>
    Позволяет попытаться найти автора изображения, его ник и страницы в соцсетях. Также может распознать скрин из аниме или мультфильмов с точностью до указания серии и минуты, откуда он сделан. 
    Кроме того может проверить вероятность того, сгенерировано ли изображение нейросетью или же нарисовано вручную.

    <b>===Кнопка "Растения, грибы, текст, поиск"===</b>  
    Позволяет распознать текст или растение по их фотографии. Также с помощью встроенной в функцию нейросети можно сделать различные манипуляции с распознанным текстом или узнать, что с растением (болезни, вредители). Кроме того почитать информацию о распознанном растении или советы по уходу за ним. Ещё можно добавлять растения в список своих растений и сортировать по различных критериям ухода, кроме того можно отмечать и отслеживать даты полива, а так же ставить метки с растенями и грибами на общую карту чтобы не потерять место произрастания

    <b>===Кнопка "Поговорить с ботом"===</b>  
    Переключает в режим диалога с ботом. У этого режима также есть много интересных особенностей вроде распознавания голосовых, музыки, видео, поиск в сети или анализа содержимого веб-страниц. Так же в этом режиме можно генерировать изображения по текстовому запросу. У этого режима есть отдельная кнопка помощи, если необходимо.

    <b>===Основной режим бота==="</b>
    Основной режим бота позволяет создавать, сохранять и публиковать посты. По умолчанию, если загружать вручную, изображения в телеграм загружаются и отображаются в разрешении 1280 пикселей. Если же загружать их через бота (через API telegram), то в таком случае изображение загружается и отображается с разрешением 2560 пикселей, что более чем в 2 раза превышает ручную загрузку и потому даёт лучшее качество отображения.
    Бот принимает сначала текст, который будет служить подписью к посту, затем сами изображения, отправленные как файлы, без сжатия, после чего возвращает готовый пост с изображениями в исходном качестве. Также при вводе подписи доступно указание и оформление ссылок, например на соцсети.

    ▶️Кроме того, бот поддерживает загрузку GIF-файлов. Для этого переименуйте .GIF в .RAR, затем отправьте файл боту во время оформления поста. Это нужно для того, чтобы телеграм не пережимал GIF-файлы. Бот автоматически переименует файл обратно в GIF перед размещением в Telegraph.  

    ▶️Также вы можете отправить что-то администрации напрямую, в режиме прямой связи. Для этого введите команду /send, и после неё все ваши сообщения, отправленные боту, тут же будут пересылаться администрации. Это могут быть как вопросы или оповещения об ошибках, так и просьбы что-то реализовать в боте или улучшить. Для завершения этого режима просто введите /fin, и бот вернётся в свой обычный режим. Просьба не спамить через этот режим, писать или отправлять только нужную информацию.

    ▶️Создаваемые посты видны только вам, до тех пор пока вы их сами не выложите или не поделитесь ими через нажатие кнопок публикации в ТГ, ВК или предложки в Анемон. Так что не бойтесь экспериментировать с ботом.

    Пример:
<pre>https://ссылка_1

https://ссылка_2

рисунок акварелью</pre>
    Даст такой результат:
<pre>рисунок акварелью

ссылка_1 • ссылка_2</pre>
    """

    # Определяем кнопки
    keyboard = [
        [InlineKeyboardButton("🗂 Папки с сохранёнными записями 🗂", callback_data="scheduled_by_tag")],
        [InlineKeyboardButton("🎨 Найти источник или проверить на ИИ 🎨", callback_data='start_search')],
        [InlineKeyboardButton("🌱 Растения, грибы, текст, поиск 🌱", callback_data='start_ocr')],            
        [InlineKeyboardButton("🦊 Поговорить с ботом 🦊", callback_data='run_gpt')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем или обновляем сообщение
    await query.edit_message_text(help_text, parse_mode="HTML", reply_markup=reply_markup)




def format_text_to_html(message):
    # Выбираем текст или подпись, если они есть
    raw_text = message.text or message.caption
    logger.info(f"raw_text: {raw_text}")     
    if not raw_text:
        return ""  # Возвращаем пустую строку, если текст и подпись отсутствуют

    entities = message.entities if message.text else message.caption_entities
    logger.info(f"entities: {entities}")    
    if not entities:
        escaped_text = escape(raw_text.strip())
        return add_plain_links(escaped_text)  # Добавляем ссылки в чистом тексте

    formatted_text = ""
    offset = 0

    for entity in entities:
        start, end = entity.offset, entity.offset + entity.length
        plain_text = escape(raw_text[offset:start])  # Текст до текущей сущности
        formatted_text += add_plain_links(plain_text)  # Обрабатываем ссылки в обычном тексте
        logger.info(f"formatted_text: {formatted_text}")  
        logger.info(f"plain_text: {plain_text}")          
        entity_text = escape(raw_text[start:end])
        if entity.type == "bold":
            formatted_text += f"<b>{entity_text}</b>"
        elif entity.type == "italic":
            formatted_text += f"<i>{entity_text}</i>"
        elif entity.type == "underline":
            formatted_text += f"<u>{entity_text}</u>"
        elif entity.type == "strikethrough":
            formatted_text += f"<s>{entity_text}</s>"
        elif entity.type == "code":
            formatted_text += f"<code>{entity_text}</code>"
        elif entity.type == "pre":
            formatted_text += f"<pre>{entity_text}</pre>"
        elif entity.type == "text_link":
            formatted_text += f'<a href="{entity.url}">{entity_text}</a>'
        elif entity.type == "mention":
            formatted_text += mention_html(entity.user.id, entity_text)
        elif entity.type == "spoiler":
            formatted_text += f'<span class="tg-spoiler">{entity_text}</span>'
        elif entity.type == "url":  # Обработка обычных ссылок
            formatted_text += f'{entity_text}'

        offset = end

    formatted_text += add_plain_links(escape(raw_text[offset:]))  # Обрабатываем оставшийся текст
    return formatted_text

def add_plain_links(text):
    # Регулярное выражение для поиска обычных ссылок
    url_pattern = re.compile(r"(https?://[^\s]+)")
    return url_pattern.sub(r'<a href="\1">\1</a>', text)

def log_user_state(user_id: int):
    logger.info(f"--- User {user_id} Current State ---")
    logger.info(f"user_data: {user_data.get(user_id, 'Not Found')}")
    logger.info(f"is_search_mode: {is_search_mode.get(user_id, False)}")
    logger.info(f"is_ocr_mode: {is_ocr_mode.get(user_id, False)}")
    logger.info(f"is_gpt_mode: {is_gpt_mode.get(user_id, False)}")
    logger.info(f"is_role_mode: {is_role_mode.get(user_id, False)}")
    logger.info(f"is_asking_mode: {is_asking_mode.get(user_id, False)}")
    logger.info(f"waiting_for_vk: {waiting_for_vk.get(user_id, False)}")
    logger.info(f"waiting_for_forward: {waiting_for_forward.get(user_id, False)}")
    logger.info(f"waiting_for_caption: {waiting_for_caption.get(user_id, False)}")
    logger.info(f"users_in_send_mode: {users_in_send_mode.get(user_id, False)}")
    logger.info(f"waiting_for_twitter: {waiting_for_twitter.get(user_id, False)}")
    logger.info(f"waiting_for_coordinates : {waiting_for_coordinates .get(user_id, False)}")
    logger.info("---------------------------------")



async def webapp_command(update: Update, context: CallbackContext) -> None:
    webapps = [
        ("🌐 Гугл", "https://www.google.ru/?hl=ru"),
        ("🌐 Яндекс", "https://ya.ru/"),    
        ("🗺️ Яндекс Карты", "https://yandex.ru/maps/213/moscow/?ll=38.094953%2C55.782537&utm_medium=allapps&utm_source=face&z=12.2"),
        ("🗺️ Старинные Карты", "https://retromap.ru/0719113_0420092_55.956119,37.200393"),
        ("📑 Google Переводчик", "https://translate.google.com/?sl=en&tl=ru&op=translate"),
        ("🧠 DeepL Переводчик", "https://www.deepl.com/en/translator"),        
        ("▶️ YouTube", "https://ricktube.ru/"),
        ("🖼️ img/txt to 3D", "https://huggingface.co/spaces/tencent/Hunyuan3D-2"),
        ("🌪️ Windy", "https://www.windy.com/ru/-%D0%9D%D0%B0%D1%81%D1%82%D1%80%D0%BE%D0%B9%D0%BA%D0%B8/settings?57.111,38.057,5"),        
        ("🌦️ Погода на карте", "https://yandex.ru/pogoda/ru/maps?ll=37.7556_55.810300000000005&z=9"),
    ]

    keyboard = [
        [InlineKeyboardButton(text, web_app=WebAppInfo(url=url)) for text, url in webapps[i:i+2]]
        for i in range(0, len(webapps), 2)
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите веб-приложение:", reply_markup=reply_markup)


# Список каомодзи
KAOMOJI_LIST = [
    "≽^⎚⩊⎚^≼", "/ᐠ˵&gt; ˕ &lt;˵マ", "/ᐠ - ˕ -マ", "≽^• ˕ •^≼", "≽/ᐠ - ˕ -マ≼ Ⳋ", "/ᐠ≽•ヮ•≼マ", "/ᐠ. .ᐟ\\ Ⳋ", "ฅ ฅ", "≽^-⩊-^≼", "/ᐠ_ ꞈ _ᐟ\\ɴʏᴀ~", "≽^- ˕ -^≼", "ฅ≽^- ﻌ - ^≼ฅ", "/ᐠ˵- ᴗ -˵マ ᶻ 𝗓 ", "(=^･ｪ･^=))ﾉ彡☆", "/ᐠ .⑅.ᐟ\\ﾉ"
]



import asyncio
from collections import defaultdict
from uuid import uuid4
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import ContextTypes, InlineQueryHandler

# Словарь для отслеживания задач дебаунса
debounce_tasks = defaultdict(asyncio.Task)
last_query_times = {}
def _remove_task_from_context(task: asyncio.Task, user_data: dict):
    user_tasks_set = user_data.get('user_tasks')
    if user_tasks_set:
        user_tasks_set.discard(task)

async def handle_debounced_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    inline_query = update.inline_query
    user_id = inline_query.from_user.id

    async def background_inline_answer():
        try:
            full_answer_raw = await generate_gemini_inline_response(query)
            escaped_answer = escape(full_answer_raw)
    
            # Всегда сохраняем ответ, даже если ответить не успели
            save_inline_query_to_firebase(user_id, query, full_answer_raw)
    
            truncated = escaped_answer[:4060]
            html_answer = f"<blockquote expandable>{truncated}</blockquote>"
    
            preview_text = (escaped_answer[:100] + '...') if len(escaped_answer) > 100 else escaped_answer
    
            results = [
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title="Ответ от Анемо",
                    description=preview_text,
                    input_message_content=InputTextMessageContent(
                        html_answer,
                        parse_mode=ParseMode.HTML
                    )
                )
            ]
    
            # Пытаемся ответить, если не успеем — не страшно
            try:
                await inline_query.answer(results, cache_time=0, is_personal=True)
            except Exception as e:
                logger.warning(f"Не удалось отправить inline ответ (возможно таймаут): {e}")
        except asyncio.CancelledError:
            logger.info(f"Фоновая задача inline запроса пользователя {user_id} была отменена.")
        except Exception as e:
            logger.error(f"Ошибка при генерации или сохранении inline запроса: {e}")

    task = asyncio.create_task(background_inline_answer())
    user_tasks_set = context.user_data.setdefault('user_tasks', set())
    user_tasks_set.add(task)
    task.add_done_callback(lambda t: _remove_task_from_context(t, context.user_data))

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    user_id = update.inline_query.from_user.id

    if not query:
        saved_queries = load_user_inline_queries(user_id)
    
        results = []
        for item in saved_queries:
            text = item.get("query", "")
            response = item.get("response", "")
            preview = (response[:100] + "...") if len(response) > 100 else response
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=text,
                    description=preview,
                    input_message_content=InputTextMessageContent(
                        f"<blockquote expandable>{escape(response[:4060])}</blockquote>",
                        parse_mode=ParseMode.HTML
                    )
                )
            )
    
        if results:
            await update.inline_query.answer(results, cache_time=0, is_personal=True)
        return

    now = datetime.utcnow()
    last_query_time = last_query_times.get(user_id)
    last_query_times[user_id] = now


    saved_queries = load_user_inline_queries(user_id)
    for item in saved_queries:
        if item.get("query") == query:
            response = item.get("response", "")
            preview = (response[:100] + "...") if len(response) > 100 else response
            results = [
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title="Ранее сгенерированный ответ",
                    description=preview,
                    input_message_content=InputTextMessageContent(
                        f"<blockquote expandable>{escape(response[:4060])}</blockquote>",
                        parse_mode=ParseMode.HTML
                    )
                )
            ]
            await update.inline_query.answer(results, cache_time=0, is_personal=True)
            return
    
    # Отменить предыдущую задачу, если она еще не завершена
    task = debounce_tasks.get(user_id)
    if task and not task.done():
        task.cancel()

    async def delayed_response():
        try:
            # Шаг 1: первая задержка — 4 секунды
            await asyncio.sleep(4)

            while True:
                latest_time = last_query_times.get(user_id)
                if not latest_time:
                    break

                time_since_last_input = (datetime.utcnow() - latest_time).total_seconds()

                if time_since_last_input >= 2:
                    # Пользователь не печатал минимум 2 секунды — можно обрабатывать
                    break
                else:
                    # Ждём ещё 3 секунды и проверим снова
                    await asyncio.sleep(3)

            await handle_debounced_inline_query(update, context, query)
        except asyncio.CancelledError:
            pass

    debounce_tasks[user_id] = asyncio.create_task(delayed_response())



import urllib.parse


async def find_anime_source(update: Update, context: CallbackContext, image_path: str, reply_markup: InlineKeyboardMarkup) -> bool:
    """
    Анализирует изображение через trace.moe по ЛОКАЛЬНОМУ ПУТИ.
    Возвращает True — если найдено (similarity >= 92%), False — иначе.
    """

    # Определяем источник вызова
    if update.callback_query:
        temp_msg = await update.callback_query.message.edit_text("Ищу источник... 🔍")
        chat_id = update.callback_query.message.chat_id

    elif update.message:
        temp_msg = await update.message.reply_text("Ищу источник... 🔍")
        chat_id = update.message.chat_id

    else:
        return False

    try:
        # === trace.moe ===
        with open(image_path, "rb") as f:
            resp = requests.post(
                "https://api.trace.moe/search?anilistInfo&cutBorders",
                data=f,
                headers={"Content-Type": "image/jpeg"}
            )

        data = resp.json()

        if "result" not in data or not data["result"]:
            await temp_msg.edit_text("⚠ Источник не найден. Попробуйте другой кадр.")
            return False

        result = data["result"][0]
        similarity = result.get("similarity", 0) * 100

        if similarity < 92:
            await temp_msg.edit_text(
                f"🤔 Найдено, но точность низкая: {similarity:.2f}%\n"
                f"Попробуйте кадр получше!"
            )
            return False

        await temp_msg.delete()

        # === quota ===
        try:
            me = requests.get("https://api.trace.moe/me").json()
            quota = int(me.get("quota", 0))
            used = int(me.get("quotaUsed", 0))
            left_requests = quota - used
        except:
            left_requests = None

        # === AniList ===
        anilist = result.get("anilist", {})

        title = (
            anilist.get("title", {}).get("english")
            or anilist.get("title", {}).get("romaji")
            or anilist.get("title", {}).get("native")
        )

        genres = anilist.get("genres") or []
        genres_str = ", ".join(genres) if genres else None
        genres_lower = {g.lower() for g in genres}

        # 🔥 СПОЙЛЕР ЛОГИКА
        is_hentai = "hentai" in genres_lower

        fmt = anilist.get("format")

        studios = anilist.get("studios", {}).get("edges", [])
        main_studios = [s["node"]["name"] for s in studios if s.get("isMain")]
        studio_str = ", ".join(main_studios) if main_studios else None

        # Годы
        start_date = anilist.get("startDate")
        end_date = anilist.get("endDate")

        if start_date and start_date.get("year"):
            years_str = (
                f"{start_date['year']}–{end_date['year']}"
                if end_date and end_date.get("year") != start_date['year']
                else str(start_date['year'])
            )
        else:
            years_str = None

        synonyms = anilist.get("synonyms", [])
        synonyms_str = ", ".join(synonyms[:3]) if synonyms else None

        episode = result.get("episode")
        total_episodes = anilist.get("episodes")

        t_from = result.get("from")
        t_to = result.get("to")

        def fmt_time(t):
            return f"{int(t//60):02d}:{int(t%60):02d}"

        time_str = (
            f"{fmt_time(t_from)} — {fmt_time(t_to)}"
            if t_from is not None and t_to is not None
            else None
        )

        video_url = result.get("video")
        if video_url:
            video_url += "?size=l"

        def c(x):
            return f"<code>{html.escape(str(x))}</code>" if x else None

        # === caption ===
        lines = ["<b>Найден источник (Аниме):</b>"]

        if title:        lines.append(f"Название: {c(title)}")
        if genres_str:   lines.append(f"Жанр: {c(genres_str)}")
        if fmt:          lines.append(f"Формат: {c(fmt)}")
        if studio_str:   lines.append(f"Студия: {c(studio_str)}")
        if years_str:    lines.append(f"Годы: {c(years_str)}")
        if synonyms_str: lines.append(f"Варианты: {c(synonyms_str)}")

        if episode:
            ep = f"Эпизод: {c(episode)}"
            if total_episodes:
                ep += f" из {c(total_episodes)}"
            lines.append(ep)

        if time_str:
            lines.append(f"Фрагмент: {c(time_str)}")

        lines.append(f"Точность: <b>{similarity:.2f}%</b>")

        if left_requests is not None:
            lines.append(f"\nОсталось запросов в этом месяце: {c(left_requests)}")

        caption = "\n".join(lines)

        # === отправка ===
        if video_url:
            await context.bot.send_video(
                chat_id=chat_id,
                video=video_url,
                caption=caption,
                parse_mode="HTML",
                reply_markup=reply_markup,
                has_spoiler=is_hentai  # ⭐ ключевая строка
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=caption,
                parse_mode="HTML",
                reply_markup=reply_markup
            )

        return True

    except Exception as e:
        logger.error(f"trace.moe error: {e}")
        await temp_msg.edit_text("❗ Ошибка анализа. Попробуйте ещё раз позже.")
        return False







async def start(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    log_user_state(user_id)

    if update.message:
        message_to_reply = update.message
        user_id = update.message.from_user.id
    elif update.callback_query:
        message_to_reply = update.callback_query.message
        user_id = update.callback_query.from_user.id
    else:
        return ConversationHandler.END
    




    # === Блок режима поиска ===
    if is_search_mode.get(user_id, False):
        if update.message.photo:
            file = await update.message.photo[-1].get_file()
            image_path = 'temp_image.jpg'
        elif update.message.document and update.message.document.mime_type.startswith('image/'):
            file = await update.message.document.get_file()
            image_path = 'temp_image.jpg'
        else:
            await update.message.reply_text("Пожалуйста, отправьте изображение для поиска. /restart")
            return ASKING_FOR_FILE

        await file.download_to_drive(image_path)
        with open(image_path, 'rb') as f:
            context.user_data['image_bytes'] = f.read()
        # Сообщение о загрузке
        loading_message = await update.message.reply_text("Загрузка файла на хостинг и анализ...")

        # Загружаем изображение на Catbox (получаем URL)
        img_url = await upload_catbox(image_path)
        context.user_data['img_url'] = img_url 

        # --- ПОДГОТОВКА КНОПОК ЗАРАНЕЕ ---
        # Нам нужны эти кнопки и для trace.moe (если найдет), и для SauceNAO (если нет)
        search_url = f"https://saucenao.com/search.php?db=999&url={img_url}"
        yandex_search_url = f"https://yandex.ru/images/search?source=collections&rpt=imageview&url={img_url}"
        google_search_url = f"https://lens.google.com/uploadbyurl?url={img_url}"
        bing_search_url = f"https://www.bing.com/images/search?view=detailv2&iss=sbi&form=SBIVSP&sbisrc=UrlPaste&q=imgurl:{img_url}"

        keyboard_search = [
            [InlineKeyboardButton("АИ или нет?", callback_data='ai_or_not')],           
            [
                InlineKeyboardButton("Найти в Yandex Images", url=yandex_search_url),
                InlineKeyboardButton("🔍 Yandex WebApp", web_app=WebAppInfo(url=yandex_search_url))
            ],
            [
                InlineKeyboardButton("Найти в Google Images", url=google_search_url),
                InlineKeyboardButton("🔍 Google WebApp", web_app=WebAppInfo(url=google_search_url))
            ],
            [
                InlineKeyboardButton("Найти в Bing Images", url=bing_search_url),
                InlineKeyboardButton("🔍 Bing WebApp", web_app=WebAppInfo(url=bing_search_url))
            ],
            [
                InlineKeyboardButton("Найти на SauceNAO", url=search_url),
                InlineKeyboardButton("🔍 SauceNAO WebApp", web_app=WebAppInfo(url=search_url))
            ],
            [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]
        ]
        reply_markup_search = InlineKeyboardMarkup(keyboard_search)

        # --- ЭТАП 1: Поиск аниме через trace.moe ---
        try:
            # Передаем URL и подготовленные кнопки
            anime_found = await find_anime_source(update, context, image_path, reply_markup_search) # <--- ИЗМЕНЕНИЕ
            
            if anime_found:
                # Если аниме найдено с высокой точностью, удаляем временные сообщения и файлы и выходим
                await loading_message.delete()
                if os.path.exists(image_path):
                    os.remove(image_path)
                return ASKING_FOR_FILE
        except Exception as e:
            logger.error(f"Error in anime search block: {e}")
            # Не прерываем выполнение, идем к SauceNAO

        # --- ЭТАП 2: Поиск через SauceNAO (если аниме не найдено) ---
        await loading_message.edit_text("Аниме не найдено или низкая точность. Опрашиваю SauceNAO...")
        
        try:
            # Получаем авторов и ссылки через SauceNAO
            authors_text, external_links, jp_name, details_text, ep_name, ep_time, dA_id, full_author_text, pixiv_id, twitter_id = await search_image_saucenao(image_path)
        except Exception as e:
            if str(e) == "Лимит превышен":
                await loading_message.edit_text("Лимит запросов к SauceNAO исчерпан...", reply_markup=reply_markup_search)
            else:
                await loading_message.edit_text(f"Произошла ошибка при обращении к SauceNAO: {str(e)}", reply_markup=reply_markup_search)
            
            if os.path.exists(image_path):
                os.remove(image_path)
            return ASKING_FOR_FILE

        if os.path.exists(image_path):
            os.remove(image_path)

        # Формирование ответа SauceNAO
        links_text = "\n".join(f"{i + 1}. {link}" for i, link in enumerate(external_links)) if isinstance(external_links, list) else None
        
        reply_text = "Результаты поиска:\n"
        if authors_text:    reply_text += f"Название: {authors_text}\n"
        if details_text:    reply_text += f"Детали: {details_text}\n\n"
        if jp_name:         reply_text += f"JP Название: {jp_name}\n"
        if ep_name:         reply_text += f"{ep_name}\n"
        if dA_id:           reply_text += f"dA ID: {dA_id}\n"
        if twitter_id:      reply_text += f"Твиттер:\n{twitter_id}\n"                
        if pixiv_id:        reply_text += f"Pixiv: {pixiv_id}\n"
        if full_author_text: reply_text += f"Автор: {full_author_text}\n"
        if ep_time:         reply_text += f"{ep_time}\n\n"
        if links_text:      reply_text += f"Ссылки:\n{links_text}"

        if not authors_text and not links_text:
            reply_text = (
                "К сожалению, ничего не найдено. "
                "Возможно, изображение сгенерировано (проверьте кнопкой ниже), автор малоизвестен или изображение слишком свежее."
            )

        await loading_message.edit_text(reply_text.strip(), reply_markup=reply_markup_search)

        return ASKING_FOR_FILE



    # Проверяем, если бот в режиме ocr
    if is_ocr_mode.get(user_id, False):
        # Проверяем, отправил ли пользователь фото или документ
        if update.message.photo:
            file = await update.message.photo[-1].get_file()
            image_path = 'temp_image.jpg'
            caption = update.message.caption  # <-- сохраняем подпись
        elif update.message.document and update.message.document.mime_type.startswith('image/'):
            file = await update.message.document.get_file()
            image_path = 'temp_image.jpg'
            caption = update.message.caption  # <-- сохраняем подпись
        else:
            keyboard = [
                [InlineKeyboardButton("🪴 Мои растения 🪴", callback_data='myplants')], 
                [InlineKeyboardButton("🗺 Грибы и растения на карте🗺", callback_data='show_map')],                           
                [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "Пожалуйста, отправьте изображение для распознавания, либо нажмите на кнопки чтобы посмотреть ваши растения если вы их сохраняли. Или чтобы посмотреть или добавить растение на карту",
                reply_markup=reply_markup
            )
            return ASKING_FOR_OCR

        # Загружаем файл и отправляем сообщение о процессе
        loading_message = await update.message.reply_text("Загрузка изображения...")

        await file.download_to_drive(image_path)

        # Загружаем изображение на Catbox и обновляем сообщение
        await loading_message.edit_text("Изображение загружается, подождите немного...")
        img_url = await plants_upload_image(image_path)
        inat_url = "https://www.inaturalist.org/computer_vision_demo"
        bio = BytesIO()
        await file.download_to_memory(out=bio)
        bio.seek(0)


        # Сохраняем в context.user_data
        context.user_data['image_bytes'] = bio.getvalue()
        context.user_data['img_url'] = img_url
        context.user_data['img_caption'] = caption
        context.user_data['img_path'] = image_path
        # Формируем клавиатуру с кнопками для распознавания
        keyboard = [
            [InlineKeyboardButton("🗺Добавить это растение на карту 🗺", callback_data='plantmap_gpt')],  
            [InlineKeyboardButton("🌿 Распознать растение 🌿", callback_data='recognize_plant')],
            [InlineKeyboardButton("🍄‍🟫 Распознать гриб 🍄‍🟫", callback_data='mushrooms_gpt')],                                          
            [InlineKeyboardButton("💬Найти отзывы💬", callback_data='barcode_with_gpt')],
            [InlineKeyboardButton("📋Дополнительные возможности📋", callback_data='plants_and_mushrooms_menu')],                      # Новая кнопка            
            [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]

        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Обновляем сообщение с кнопками после успешной загрузки
        await loading_message.edit_text(
            "/ᐠ - ˕ -マ≼ Ⳋ Изображение успешно загружено!\n "
            "Что именно вы желаете сделать?"
            "Обычно обработка запроса на распознавание занимает до 10-15 секунд.\n\n"
            "Кнопка \"Распознать растение\" работает через специально обученную на растениях нейросеть и потому полученные с её помощью результаты в высокой степени достоверны. \n\n Кнопка \"Распознать гриб\" использует более общую нейросеть и может ошибаться, будьте осторожны\n\n"
            "Кнопка \"Найти отзывы\" автоматически находит в интернете и присылает выжимку отзывов на товар с фотографии.\n\n"
            "Через кнопку \"Дополнительные возможности\" вы можете распознать текст, определить проблемы с растением, добавить его в список своих\n",
            reply_markup=reply_markup
        )

        return ASKING_FOR_OCR
    # === Блок обычного старта (если нет в user_data) ===
    if user_id not in user_data:
        logger.info(f"User {user_id} started the process.")
        
        keyboard = [
            [InlineKeyboardButton("🗂 Папки с сохранёнными записями 🗂", callback_data="scheduled_by_tag")],
            [InlineKeyboardButton("🎨 Найти источник или проверить на ИИ 🎨", callback_data='start_search')],
            [InlineKeyboardButton("🌱 Растения, грибы, текст, поиск 🌱", callback_data='start_ocr')],              
            [InlineKeyboardButton("🦊 Поговорить с ботом 🦊", callback_data='run_gpt')],
            [InlineKeyboardButton("📖 Посмотреть помощь", callback_data="osnhelp")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        random_kaomoji = random.choice(KAOMOJI_LIST)

        await message_to_reply.reply_text(
            f'🌠Привет <code>{random_kaomoji}</code>\n\n'
            f'Если вам нужно что-то распознать или найти отзывы по фото то просто пришлите мне его.\n\n'            
            'Если вы хотите сделать пост для телеграм канала, вк группы или X, то для начала, пожалуйста, отправьте мне текст...\n\n'                        
            'Либо воспользуйтесь одной из кнопок ниже:',                        
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

        user_data[user_id] = {'status': 'awaiting_artist_link'}
        return ASKING_FOR_ARTIST_LINK

    logger.info(f"user_data {user_data}.")
        
    status = user_data[user_id].get('status')
    logger.info(f"status {status}")
    # Проверяем, если бот в режиме поиска
    if users_in_send_mode.get(user_id, False):
        await duplicate_message(update, context)       
    if waiting_for_vk.get(user_id, False):
        return await handle_vk_keys_input(update, context)  
    if waiting_for_twitter.get(user_id, False):
        return await handle_twitter_keys_input(update, context) 

    if waiting_for_coordinates.get(user_id, False):
        return await handle_coordinates(update, context) 

    if waiting_for_forward.get(user_id, False):
        return await handle_forwarded_message(update, context)

    if waiting_for_caption.get(user_id, False):
        key = waiting_for_caption[user_id]
        return await handle_new_caption(update, context, key)

    # Проверяем, если бот в режиме GPT
    if is_gpt_mode.get(user_id, False):
        return await gpt_running(update, context)  # Вызываем функцию gpt_running

    if is_role_mode.get(user_id, False):
        return await receive_role_input(update, context)

    if is_asking_mode.get(user_id, False):
        return await receive_followup_question(update, context)

    # Проверяем, если бот в режиме поиска
    if users_in_send_mode.get(user_id, False):
        await duplicate_message(update, context)  





    if update.message:
        message_to_reply = update.message

        # Проверяем состояние пользователя
        if user_data.get(user_id, {}).get('status') == 'awaiting_artist_link':
            if update.message.media_group_id:
                message = update.message
            
                # Проверка: если это фото (сжатое изображение)
                if message.photo:
                    await fast_group_rec(update, context)
                    return ConversationHandler.END
            
                # Проверка: если это документ, но изображение (не сжатое)
                elif message.document and message.document.mime_type and message.document.mime_type.startswith("image/"):
                    await message_to_reply.reply_text(
                        "Пожалуйста, отправьте сначала текстовую подпись для будущего поста либо \"нет\", если она не нужна"
                    )
                    return ConversationHandler.END
            
                # Иные типы медиа — можно отфильтровать отдельно
                else:
                    await message_to_reply.reply_text("Неподдерживаемый тип медиа.")
                    return ConversationHandler.END
  
              
            # Получаем текст сообщения
            if update.message.text:
                text = format_text_to_html(update.message)  
                twitter_image_regex = re.compile(r"^https://x\.com/\w+/status/\d+/?(\?.*)?$")
                lofter_image_regex = re.compile(r"^https://\w+\.lofter\.com/post/\w+$")
                weibo_image_regex = re.compile(r"^https://www\.weibo\.com/\d+/\w+(\?.*)?$")
                tumblr_image_regex = re.compile(r"^https://\w+\.tumblr\.com/post/\d+(/\S*)?$")

                if (
                    twitter_image_regex.fullmatch(text)
                    or lofter_image_regex.fullmatch(text)
                    or weibo_image_regex.fullmatch(text)
                    or tumblr_image_regex.fullmatch(text)
                ):
                    await post_by_twitter_link(text, update, context)  # Переименовал для универсальности
                    return 'awaiting_image'    

                # Проверка на наличие HTML-ссылок
                html_link_pattern = r'<a\s+href="(https?://[^\s]+)"[^>]*>.*?</a>'
                html_links = re.findall(html_link_pattern, text)

                if html_links:  # Если найдены HTML-ссылки
                    # Считываем весь текст как title
                    title = text.strip()  # Весь текст считывается как заголовок
                    user_data[user_id] = {
                        'status': 'awaiting_image',
                        'artist_link': "",
                        'extra_links': [],
                        'author_name': "",
                        'title': title,  # Сохраняем весь текст как title
                        'media': [],
                        'image_counter': 0,
                    }
                    await update.message.reply_text(
                        "✅ Отлично! ( ´ ω  ) Принято. Теперь отправьте изображения без сжатия, как документы.\n\n Либо если вам нужен текстовый пост, то отправьте \"нет\""
                    )
                    return 'awaiting_image'
                
                # Если нет HTML-ссылок, продолжаем искать обычные ссылки
                link_pattern = r'https?://[^\s]+'
                links = re.findall(link_pattern, text)

                if not links:  # Если ссылки не найдены
                    # Удаляем пробелы и лишние символы из текста
                    author_input = re.sub(r'^\s+|\s+$', '', text)
                    title = author_input            
                    # Проверяем, весь ли текст внутри "^...^"


                    artist_link = ""
                    extra_links = []

                    # Сохраняем данные в user_data
                    user_data[user_id] = {
                        'status': 'awaiting_image',
                        'artist_link': artist_link,
                        'extra_links': extra_links,
                        'author_name': "",
                        'title': title,  # Если нет заголовка, используем имя автора
                        'media': [],
                        'image_counter': 0,
                    }

                    await update.message.reply_text(
                        "✅ Отлично! ( ´ ω ` ) Принято. Теперь отправьте изображения без сжатия, как документы.\n\n Либо если вам нужен текстовый пост, то отправьте \"нет\""
                    )
                    return 'awaiting_image'               
                # Если сообщение не содержит ссылок или не является только ссылкой, выполняем дальнейший код
                if ' ' in text:
                    parts = text.split(maxsplit=1)

                    if len(parts) > 0:
                        # Проверка на формат с "*"
                        if parts[0].startswith('*'):
                            artist_link = ""  # Если начинается с "*", то ссылка пустая
                            author_input = parts[1] if len(parts) > 1 else ''  # Остальная часть - это текст
                        else:
                            artist_link_match = re.match(r'(https?://[^\s]+)', parts[0])
                            artist_link = artist_link_match.group(1) if artist_link_match else ""
                            author_input = parts[1] if len(parts) > 1 else ''  # Остальная часть - это текст

                        # Извлечение дополнительных ссылок
                        all_links = re.findall(r'https?://[^\s,]+', author_input)
                        extra_links = [artist_link] + all_links if artist_link else all_links
                        logger.info(f"extra_links: {extra_links}") 
                        logger.info(f"all_links: {all_links}")                        
                        # Убираем ссылки из текста, чтобы оставить только имя автора
                        author_input = re.sub(r'https?://[^\s,]+', '', author_input).strip()

                        # Удаляем лишние разделители (например, начальные и конечные запятые)
                        author_input = re.sub(r'^[,]+|[,]+$', '', author_input).strip()
                        author_input = author_input.strip()  # На всякий случай окончательно удаляем пробелы
                        # Проверяем, если авторское имя обернуто в "^...^"

                       
                        match_full = re.match(r'^\^(.*)\^$', author_input, re.S)
                        if match_full:
                            # Если весь текст внутри "^...^", используем его как заголовок и убираем авторское имя
                            title = match_full.group(1).strip()
                            user_data[user_id] = {
                                'status': 'awaiting_image',
                                'artist_link': artist_link,
                                'extra_links': extra_links,
                                'author_name': "",
                                'title': title,  # Используем как заголовок
                                'media': [],
                                'image_counter': 0,
                            }

                        else:
                            # Проверка на наличие фразы в начале текста "^...^"
                            match_partial = re.match(r'^\^(.*?)\^\s*(.*)', author_input, re.S)
                            if match_partial:
                                # Извлекаем фразу и имя автора
                                phrase = match_partial.group(1).strip()  # Фраза из "^...^"
                                author_name = match_partial.group(2).strip()  # Остаток текста как автор
                                user_data[user_id] = {
                                    'status': 'awaiting_image',
                                    'artist_link': artist_link,
                                    'extra_links': extra_links,
                                    'author_name': author_name,  # Имя автора
                                    'title': author_name,  # Используем как заголовок
                                    'extra_phrase': phrase,  # Сохраняем фразу
                                    'media': [],
                                    'image_counter': 0,
                                }
                            else:
                                # Если нет фразы в "^...^", сохраняем всё как имя автора
                                author_name = author_input
                                user_data[user_id] = {
                                    'status': 'awaiting_image',
                                    'artist_link': artist_link,
                                    'extra_links': extra_links,
                                    'author_name': author_name,
                                    'title': author_name,  # Заголовок статьи
                                    'media': [],
                                    'image_counter': 0,
                                }

                        # Ответ, что теперь ожидается изображение в виде документа
                        await update.message.reply_text(
                            "Теперь отправьте изображение в формате документа."
                        )

                        return 'awaiting_image'

            # Если ожидаемое изображение пришло как документ
            elif update.message.document and update.message.document.mime_type.startswith('image/'):
                # Обрабатываем caption с разметкой
                caption = (
                    format_text_to_html(update.message)
                    if update.message.caption
                    else ''
                )
                
                # Разделяем текст по запятой, чтобы извлечь все ссылки
                parts = caption.split(',', maxsplit=1)
                if len(parts) > 0:
                    # Первая часть - это либо первая ссылка, либо текст
                    # Ищем все ссылки в тексте
                    links = re.findall(r'https?://[^\s,]+', caption)
                    
                    # Первая ссылка — это artist_link, если она есть
                    artist_link = links[0] if links else ''
                    
                    # Все ссылки добавляются в extra_links
                    extra_links = links
                    
                    # Убираем все ссылки из текста, чтобы оставить только имя автора
                    author_input = re.sub(r'https?://[^\s,]+', '', caption).strip()

                    # Удаляем лишние запятые, пробелы и любые разделители, оставшиеся после удаления ссылок
                    author_input = author_input.strip()  # На всякий случай окончательно удаляем пробелы



                    # Проверяем, если авторское имя обернуто в "^...^"
                    match_full = re.match(r'^\^(.*)\^$', author_input, re.S)
                    if match_full:
                        # Если весь текст внутри "^...^", используем его как заголовок и убираем авторское имя
                        title = match_full.group(1).strip()
                        # Проверяем, есть ли автор в базе

                        user_data[user_id] = {
                            'status': 'awaiting_image',
                            'artist_link': artist_link,
                            'extra_links': extra_links,
                            'author_name': "",
                            'title': title,  # Используем как заголовок
                            'media': [],
                            'image_counter': 0,
                        }

                    else:
                        # Проверка на наличие фразы в начале текста "^...^"
                        match_partial = re.match(r'^\^(.*?)\^\s*(.*)', author_input, re.S)
                        if match_partial:
                            # Извлекаем фразу и имя автора
                            phrase = match_partial.group(1).strip()  # Фраза из "^...^"
                            author_name = match_partial.group(2).strip()  # Остаток текста как автор

                            user_data[user_id] = {
                                'status': 'awaiting_image',
                                'artist_link': artist_link,
                                'extra_links': extra_links,
                                'author_name': author_name,  # Имя автора
                                'title': author_name,  # Используем как заголовок
                                'extra_phrase': phrase,  # Сохраняем фразу
                                'media': [],
                                'image_counter': 0,
                            }
                        else:
                            # Если нет фразы в "^...^", сохраняем всё как имя автора
                            author_name = author_input
                            user_data[user_id] = {
                                'status': 'awaiting_image',
                                'artist_link': artist_link,
                                'extra_links': extra_links,
                                'author_name': author_name,
                                'title': author_name,  # Заголовок статьи
                                'media': [],
                                'image_counter': 0,
                            }

                
                    # Обработка изображения
                    await handle_image(update, context)

                    # Вызов команды /publish после обработки изображения
                    await publish(update, context)

                    # Завершение процесса для данного пользователя
                    if user_id in user_data:
                        del user_data[user_id]  # Очистка данных пользователя, если нужно
                    else:
                        logger.warning(f"Попытка удалить несуществующий ключ: {user_id}")

                    user_data[user_id] = {'status': 'awaiting_artist_link'}

                    return ASKING_FOR_ARTIST_LINK


            # Проверка, если пользователь отправил изображение как фото (photo)
            elif update.message.photo:
                await fast_rec(update, context)
                return ConversationHandler.END
            # Проверка, если пользователь отправил аудио/музыку/голосовое
            #elif update.message.audio or update.message.voice:
             #   await bird_rec(update, context)
              #  return ConversationHandler.END
    # Проверка, если событие пришло от callback_query
    elif update.callback_query:
        message_to_reply = update.callback_query.message
    else:
        return ConversationHandler.END

    # Обработка состояний пользователя
    status = user_data[user_id].get('status')
    if status == 'awaiting_artist_link':
        return await handle_artist_link(update, context)
    elif status == 'awaiting_author_name':
        return await handle_author_name(update, context)
    elif status == 'awaiting_image':
        return await handle_image(update, context)       
    else:
        await message_to_reply.reply_text('🚫Ошибка: некорректное состояние.')

        return ConversationHandler.END



import uuid

async def fast_rec(update, context):
    user_id = update.effective_user.id
    message = update.message    

    # === Очистка перед началом работы ===
    # Удаление временного файла, если он существует
    image_path = 'temp_image.jpg'
    if os.path.exists(image_path):
        try:
            os.remove(image_path)
        except Exception as e:
            print(f"Не удалось удалить {image_path}: {e}")

    # Очистка локальных данных пользователя
    for key in ['image_bytes', 'img_url', 'img_caption', 'img_path']:
        if key in context.user_data:
            del context.user_data[key]
            
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
        image_path = 'temp_image.jpg'
        caption = update.message.caption  # <-- сохраняем подпись
    # Получаем файл

    # Шаг 1: Принятие изображения
    loading_message = await message.reply_text("📸 Фото принято. Загрузка изображения...")

    # Скачивание изображения
    await file.download_to_drive(image_path)


    try:
        img_url = await plants_upload_image(image_path)
    except Exception as e:
        await loading_message.edit_text(f"Ошибка при загрузке изображения: {e}")
        return

    # Сохраняем в user_data
    bio = BytesIO()
    await file.download_to_memory(out=bio)
    bio.seek(0)


    # Сохраняем в context.user_data
    context.user_data['image_bytes'] = bio.getvalue()
    # Сохраняем в user_data
    context.user_data['img_url'] = img_url
    context.user_data['img_caption'] = caption
    context.user_data['img_path'] = image_path  # <-- сохраняем путь к файлу

    # Шаг 3: Успешная загрузка и показ клавиатуры
    keyboard = [
        [InlineKeyboardButton("🌿 Распознать растение 🌿", callback_data='recognize_plant')],
        [InlineKeyboardButton("🍂 Что не так с растением? 🍂", callback_data='text_plant_help_with_gpt')],            
        [InlineKeyboardButton("🍄‍🟫 Распознать гриб 🍄‍🟫", callback_data='mushrooms_gpt')],  
        [InlineKeyboardButton("🐾 Распознать животное/насекомое 🐾", callback_data='recognize_animal_insect')],        
    
        [InlineKeyboardButton("💬 Найти отзывы 💬", callback_data='barcode_with_gpt'),
         InlineKeyboardButton("🥑 Разобрать состав 🥑", callback_data='analyze_ingredients')],
    
        [InlineKeyboardButton("🍎 Калории 🍎", callback_data='calories_gpt'),
         InlineKeyboardButton("🛒 Сравнить продукты 🛒", callback_data='products_gpt')],        
    
        [InlineKeyboardButton("📝 Распознать текст 📝", callback_data='text_rec_with_gpt')],  
        [InlineKeyboardButton("🔍 Найти источник", callback_data='find_image_source')],  # 👈 новая кнопка
        [InlineKeyboardButton("🌌 В главное меню 🌌", callback_data='restart')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await loading_message.edit_text(
        "Если вы хотели сделать пост или предложку, а не распознать содержимое на изображении, то вернитесь в меню и действуйте в соответствии с инструкциями\n\n"
        "Что вы хотите сделать?\n\n"
        "- кнопка 🌿 — распознаёт растения на специально обученной на растениях нейросети, поэтому результаты с высокой степенью достоверны\n\n"
        "- кнопка 🍄‍🟫 — использует более общую нейросеть и может ошибаться, будьте осторожны. Вы можете добавить подпись к фото указав, например запах гриба или где он был найден - это поможет увеличить веротяность верного распознавания. ТАк же вы можете прислать несколько изображений за раз.\n\n"
        "- кнопка 🐾 — попытается распознать животное или насекомое на фото\n\n"
        "- кнопка 💬 — ищет в сети отзывы на товар с фото и выдаёт краткую выжимку, как положительных, так и негативных\n\n"
        "- кнопка 🥑 — разберёт состав с этикетки продукта с научной точки зрения, пользу, вред, практичность.\n\n",
        reply_markup=reply_markup
    )




async def find_image_source(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    image_path = context.user_data.get("img_path")
    image_bytes = context.user_data.get("image_bytes")
    img_url = context.user_data.get("img_url")   # URL уже должен быть загружен catbox ранее

    if not image_path and image_bytes:
        image_path = "temp_image.jpg"
        with open(image_path, "wb") as f:
            f.write(image_bytes)

    if not image_path or not os.path.exists(image_path):
        await query.edit_message_text("❗ Изображение не найдено — отправьте его заново.")
        return

    # === Создаём сообщение о загрузке ===
    loading_message = await query.edit_message_text("🔄 Анализ изображения...")

    # --- Генерируем кнопки заранее (как в start) ---
    search_url = f"https://saucenao.com/search.php?db=999&url={img_url}"
    yandex_search_url = f"https://yandex.ru/images/search?source=collections&rpt=imageview&url={img_url}"
    google_search_url = f"https://lens.google.com/uploadbyurl?url={img_url}"
    bing_search_url = f"https://www.bing.com/images/search?view=detailv2&iss=sbi&form=SBIVSP&sbisrc=UrlPaste&q=imgurl:{img_url}"

    keyboard = [
        [InlineKeyboardButton("🤖 АИ или нет?", callback_data='ai_or_not')],
        [
            InlineKeyboardButton("🔍 Yandex", url=yandex_search_url),
            InlineKeyboardButton("WebApp", web_app=WebAppInfo(url=yandex_search_url))
        ],
        [
            InlineKeyboardButton("🔍 Google", url=google_search_url),
            InlineKeyboardButton("WebApp", web_app=WebAppInfo(url=google_search_url))
        ],
        [
            InlineKeyboardButton("🔍 Bing", url=bing_search_url),
            InlineKeyboardButton("WebApp", web_app=WebAppInfo(url=bing_search_url))
        ],
        [
            InlineKeyboardButton("SauceNAO", url=search_url),
            InlineKeyboardButton("WebApp", web_app=WebAppInfo(url=search_url))
        ],
        [InlineKeyboardButton("🏠 В меню", callback_data='restart')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # ==========================================================
    # 1) ПРОБУЕМ НАЙТИ АНИМЕ ЧЕРЕЗ trace.moe  (как start)
    # ==========================================================
    try:
        await loading_message.edit_text("🕒 Поиск совпадений в trace.moe...")
        anime_found = await find_anime_source(update, context, image_path, reply_markup)

        if anime_found:  # если аниме найдено ≥86% — завершение
            await loading_message.delete()
            if os.path.exists(image_path):
                os.remove(image_path)
            return
    except Exception as e:
        logger.error(f"trace.moe error: {e}")
        # но НЕ прерываем — продолжаем SauceNAO!

    # ==========================================================
    # 2) ЕСЛИ anime не найден -> SauceNAO (как start)
    # ==========================================================
    await loading_message.edit_text("🛰 Поиск источника через SauceNAO...")

    try:
        authors_text, external_links, jp_name, details_text, ep_name, ep_time, dA_id, full_author_text, pixiv_id, twitter_id = await search_image_saucenao(image_path)

    except Exception as e:
        if str(e) == "Лимит превышен":
            await loading_message.edit_text("⚠ Лимит SauceNAO исчерпан — попробуйте позже.", reply_markup=reply_markup)
        else:
            await loading_message.edit_text(f"Ошибка SauceNAO: {str(e)}", reply_markup=reply_markup)

        if os.path.exists(image_path):
            os.remove(image_path)
        return

    if os.path.exists(image_path):
        os.remove(image_path)

    # === Формируем текст как в версии start ===
    links_text = "\n".join(f"{i+1}. {l}" for i,l in enumerate(external_links)) if external_links else None
    reply_text = "🔎 Результаты SauceNAO:\n\n"

    if authors_text: reply_text += f"📌 Название: {authors_text}\n"
    if details_text: reply_text += f"📄 Детали: {details_text}\n\n"
    if jp_name: reply_text += f"🇯🇵 JP: {jp_name}\n"
    if ep_name: reply_text += f"{ep_name}\n"
    if dA_id: reply_text += f"DeviantArt: {dA_id}\n"
    if twitter_id: reply_text += f"Twitter: {twitter_id}\n"
    if pixiv_id: reply_text += f"Pixiv: {pixiv_id}\n"
    if full_author_text: reply_text += f"Автор: {full_author_text}\n"
    if ep_time: reply_text += f"{ep_time}\n\n"
    if links_text: reply_text += f"🔗 Ссылки:\n{links_text}"

    if not authors_text and not links_text:
        reply_text = "❔ Источник не найден.\nВозможно работа новая, редкая или сгенерирована ИИ."

    await loading_message.edit_text(reply_text.strip(), reply_markup=reply_markup)






# Глобальный словарь для отслеживания медиагрупп
media_groups_buffer = {}

async def fast_group_rec(update, context):
    message = update.message
    user_id = update.effective_user.id
    media_group_id = message.media_group_id

    # Создаем буфер для этой медиагруппы, если еще нет
    if media_group_id not in media_groups_buffer:
        media_groups_buffer[media_group_id] = {
            "images": [],
            "last_update": time.time(),
            "task": None,
            "notified_count": 0,
            "caption": None   # поле для подписи
        }

    buffer = media_groups_buffer[media_group_id]

    # Если это первое сообщение медиагруппы — фиксируем подпись
    if buffer["caption"] is None and message.caption:
        buffer["caption"] = message.caption

    # Сохраняем фото в память
    if message.photo:
        file = await message.photo[-1].get_file()
        bio = BytesIO()
        await file.download_to_memory(out=bio)
        bio.seek(0)
        buffer["images"].append(bio.getvalue())
        buffer["last_update"] = time.time()

        buffer["notified_count"] += 1
        await message.reply_text(f"📸 Фото {buffer['notified_count']} добавлено для анализа...")

    # Если это первый файл в группе, запускаем отслеживание завершения
    if buffer["task"] is None:
        buffer["task"] = asyncio.create_task(finish_group_after_delay(media_group_id, context, message))


async def finish_group_after_delay(media_group_id, context, message):
    await asyncio.sleep(2)  # минимальная задержка перед началом отслеживания

    while True:
        elapsed = time.time() - media_groups_buffer[media_group_id]["last_update"]
        if elapsed >= 2:
            break
        await asyncio.sleep(0.5)

    buffer = media_groups_buffer[media_group_id]

    # Сохраняем изображения и подпись в context
    context.user_data['group_images'] = buffer["images"]
    context.user_data['img_caption'] = buffer["caption"]

    # Удаляем из буфера
    del media_groups_buffer[media_group_id]

    # Клавиатура
    keyboard = [
        [InlineKeyboardButton("🍄‍🟫 Распознать гриб 🍄‍🟫", callback_data='mushrooms_gpt')],
        [InlineKeyboardButton("🛒 Сравнить продукты 🛒", callback_data='products_gpt')],        
        [InlineKeyboardButton("🥫 Сравнить составы 🥫", callback_data='compcomparison_gpt')],
        [InlineKeyboardButton("🍎 Подсчёт калорий 🍎", callback_data='calories_gpt')],
        [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    caption_text = f"\n\n📝 Текущая подпись: {context.user_data['img_caption']}" if context.user_data['img_caption'] else ""

    await message.reply_text(
        "✅ Все изображения получены.\n\n"
        "Если вы хотели сделать пост или предложку, а не распознать содержимое на изображении, то вернитесь в меню и действуйте в соответствии с инструкциями.\n\n"
        "В случае с распознаванием гриба, при загрузке фото вы можете указывать подпись к ним, например о запахе гриба или каких-то иных особенностях, это поможет нейросети.\n\n"
        "Для сравнения составов или подсчёта калорийности вы можете дать нейросети дополнительные указания в комментарии к фото."        
        f"{caption_text}",
        reply_markup=reply_markup
    )













import os
import re
import gallery_dl
from telegram import Update
from telegram.ext import CallbackContext

async def post_by_twitter_link(link: str, update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    logger.info(f"link: {link}")
    
    # Отправляем уведомление пользователю
    await update.message.reply_text("⏳ Пост создаётся, ожидайте...")
    
    author_name = None
    artist_link = None
    title = None
    
    # Проверяем, является ли ссылка Twitter, Lofter, Weibo или Tumblr
    twitter_match = re.search(r"https://x.com/([^/]+)/status/(\d+)", link)
    lofter_match = re.search(r"https://([^.]+).lofter.com/post/(\w+)", link)
    weibo_match = re.search(r"https://www.weibo.com/\d+/(\w+)", link)
    tumblr_match = re.search(r"https://([^.]+).tumblr.com", link)
    
    if twitter_match:
        author_name = twitter_match.group(1)
        artist_link = f"https://x.com/{author_name}"
        title = author_name  # Используем никнейм как заголовок
    elif lofter_match:
        author_name = lofter_match.group(1)
        artist_link = f"https://{author_name}.lofter.com"
        title = author_name
    elif weibo_match:
        author_name = "weibo"
        artist_link = link  # Оставляем исходную ссылку
        title = "Weibo"
    elif tumblr_match:
        author_name = tumblr_match.group(1)
        artist_link = f"https://{author_name}.tumblr.com"
        title = author_name
    else:
        await update.message.reply_text("❌ Ошибка: Некорректная ссылка на пост.")
        return
    
    # Директория для сохранения файлов в папке с ботом
    base_dir = os.path.join(os.getcwd(), "twitter_media")
    save_dir = os.path.join(base_dir, str(user_id))
    os.makedirs(save_dir, exist_ok=True)


    # Установка логина и пароля для Twitter
    # Настройка аутентификации через cookies (auth_token и ct0)
    cookies_file_path = "/etc/secrets/cookies.txt"  # путь к секретному файлу на Render
    gallery_dl.config.set(("extractor", "twitter"), "cookies-file", cookies_file_path)
    # Устанавливаем путь для сохранения файлов
    gallery_dl.config.set((), "base-directory", save_dir)
    gallery_dl.config.set((), "directory", "")  # Отключаем подкаталоги
    gallery_dl.config.set(("extractor", "twitter"), "videos", False)  # Отключаем загрузку видео
    gallery_dl.config.set(("extractor", "twitter"), "retweets", False)  # Отключаем ретвиты
    
    try:
        # Запускаем загрузку
        job = gallery_dl.job.DownloadJob(link)
        job.run()
        logger.info(f"job: {job}")        
        
        # Список загруженных файлов
        media_files = [os.path.join(save_dir, f) for f in os.listdir(save_dir) if f.endswith(('.jpg', '.png'))]
        logger.info(f"media_files: {media_files}")            
        if not media_files:
            await update.message.reply_text("❌ Ошибка: Не удалось скачать изображения.")
            return
        
        # Заполняем user_data
        user_data[user_id] = {
            'status': 'twitter_image',
            'artist_link': artist_link,
            'extra_links': [artist_link],
            'author_name': f'Автор: {author_name}',
            'title': title,
            'media': media_files,
            'image_counter': len(media_files),
        }
        logging.info(f"user_data: {user_data}")        
        # Передаём изображения в handle_image
        await handle_image(update, context)
        logging.info(f"user_data2: {user_data}")        
        return await publish(update, context)
    except Exception as e:
        logging.error(f"Ошибка в post_by_twitter_link: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")



# Обработчик для нового меню "Грибы и растения"
async def plants_and_mushrooms_menu(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    inat_url = "https://www.inaturalist.org/computer_vision_demo"
    # Формируем клавиатуру для меню "Грибы и растения"
    keyboard = [
        [InlineKeyboardButton("🪴 Добавить в мои растения 🪴", callback_data='plantsave_to_my_plants')], 
        [InlineKeyboardButton("📝Распознать текст📝", callback_data='text_rec_with_gpt')],           
        [InlineKeyboardButton("🍂 Что не так с растением? 🍂", callback_data='text_plant_help_with_gpt')],
        [InlineKeyboardButton("Распознать на iNaturalist", url=inat_url)],        
        [InlineKeyboardButton("⬅️ Назад", callback_data='plants_and_mushrooms_backmenu')]  # Кнопка "Назад"
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение с новой клавиатурой
    await query.edit_message_text(
        "Что именно вы желаете распознать? \n\nЧерез кнопку \"Добавить в мои растения\" вы можете сразу же автоматически добавить это растение в список своих растений и отслеживать его поливку и необходимые условия. \n\nРаспознавание текста поддерживает текст, написанный от руки, но читаемым почерком.\n\nЧерез кнопку \"Что не так с растением?\" вы можете прочитать предположительные проблемы этого растения, такие как болезни, вредители и прочее.",
        reply_markup=reply_markup
    )
    return ASKING_FOR_OCR

# Обработчик для кнопки "Назад"
async def plants_and_mushrooms_backmenu(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    # Формируем основную клавиатуру
    keyboard = [
        [InlineKeyboardButton("🗺Добавить это растение на карту 🗺", callback_data='plantmap_gpt')],  
        [InlineKeyboardButton("🌿 Распознать растение 🌿", callback_data='recognize_plant')],
        [InlineKeyboardButton("🍄‍🟫 Распознать гриб 🍄‍🟫", callback_data='mushrooms_gpt')],                                          
        [InlineKeyboardButton("💬Найти отзывы💬", callback_data='barcode_with_gpt')],
        [InlineKeyboardButton("📋Дополнительные возможности📋", callback_data='plants_and_mushrooms_menu')],                      # Новая кнопка            
        [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Возвращаемся к исходному меню
    await query.edit_message_text(
        "/ᐠ - ˕ -マ≼ Ⳋ Изображение успешно загружено!\n "
        "Что именно вы желаете сделать?"
        "Обычно обработка запроса на распознавание занимает до 10-15 секунд.\n\n"
        "Кнопка \"Распознать растение\" работает через специально обученную на растениях нейросеть и потому полученные с её помощью результаты в высокой степени достоверны. \n\n Кнопка \"Распознать гриб\" использует более общую нейросеть и может ошибаться, будьте осторожны\n\n"
        "Кнопка \"Найти отзывы\" автоматически находит в интернете и присылает выжимку отзывов на товар с фотографии.\n\n"
        "Через кнопку \"Дополнительные возможности\" вы можете распознать текст, определить проблемы с растением, добавить его в список своих\n",
        reply_markup=reply_markup
    )

    return ASKING_FOR_OCR

async def run_gpt(update: Update, context: CallbackContext) -> int:

    # Полное меню
    full_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏙 Посмотреть чужие генерации", callback_data="view_shared")],        
        [InlineKeyboardButton("🖼 Сменить модель", callback_data='choose_modele')],
        [InlineKeyboardButton("🎨 Выбрать стиль", callback_data='choose_preset')],  
        [InlineKeyboardButton("━━━━━━━━━━ ✦ ━━━━━━━━━━", callback_data='separator')],
        [InlineKeyboardButton("✂️ Сбросить диалог", callback_data='reset_dialog')],        
        [InlineKeyboardButton("✏️ Придумать новую роль", callback_data='set_role_button')],
        [InlineKeyboardButton("📜 Выбрать роль", callback_data='role_select')],
        [InlineKeyboardButton("━━━━━━━━━━ ✦ ━━━━━━━━━━", callback_data='separator')],        
        [InlineKeyboardButton("📗 Помощь", callback_data='short_help_gpt')],
        [InlineKeyboardButton("🌌 В главное меню 🌌", callback_data='restart')],
        [InlineKeyboardButton("🔽 Скрыть меню", callback_data='hidestartgpt_menu')]
    ])

    # Скрытое меню (только кнопка для показа)
    collapsed_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton("📒 Меню 📒", callback_data='showstartgpt_menu')]
    ])

    if update.message:
        user_id = update.message.from_user.id  # Когда вызвано командой /search
        message_to_reply = update.message
    elif update.callback_query:
        user_id = update.callback_query.from_user.id  # Когда нажата кнопка
        message_to_reply = update.callback_query.message
        
        # Убираем индикатор загрузки на кнопке
        await update.callback_query.answer()

        if update.callback_query.data == "showstartgpt_menu":
            await message_to_reply.edit_reply_markup(reply_markup=full_menu)
            await message_to_reply.edit_text(
                "Бот может искать и анализировать информацию в интеренете, анализировать содержимое ссылки веб-страницы, распознавать фото, видео, аудио и музыку и тд. \n\nА так же генерировать изображения через SD3 или Flux если начать сообщение со слова \"Нарисуй\". Для подробностей воспользуйтесь кнопкой \"помощь\"\n\n",
                reply_markup=full_menu,
                parse_mode="Markdown"
            )
            return RUNNING_GPT_MODE

        elif update.callback_query.data == "hidestartgpt_menu":
            await message_to_reply.edit_reply_markup(reply_markup=collapsed_menu)
            await message_to_reply.edit_text(
                "🦊 Режим общения с GPT активирован. Отправьте сообщение чтобы начать диалог. Либо воспользуйтесь кнопкой меню для дополнительных настроек",
                reply_markup=collapsed_menu,
                parse_mode="Markdown"
            )
            return RUNNING_GPT_MODE

    # Устанавливаем флаг режима GPT и сбрасываем другие режимы
    is_gpt_mode[user_id] = True
    is_search_mode[user_id] = False
    is_ocr_mode[user_id] = False



    # Отправляем сообщение с коллапсированным меню по умолчанию
    await message_to_reply.reply_text(
        "🦊 Режим общения с GPT активирован. Отправьте сообщение чтобы начать диалог. Либо воспользуйтесь кнопкой меню для дополнительных настроек",
        reply_markup=collapsed_menu,
        parse_mode="Markdown"
    )
    
    return RUNNING_GPT_MODE



async def run_gpt_menu(update: Update, context: CallbackContext) -> int:
    # Полное меню
    full_menu = InlineKeyboardMarkup([       
        [InlineKeyboardButton("🖼 Сменить модель", callback_data='choose_modele')],
        [InlineKeyboardButton("🎨 Выбрать стиль", callback_data='choose_preset')],  
        [InlineKeyboardButton("━━━━━━━━━━ ✦ ━━━━━━━━━━", callback_data='separator')],
        [InlineKeyboardButton("✂️ Сбросить диалог", callback_data='reset_dialog')],        
        [InlineKeyboardButton("✏️ Придумать новую роль", callback_data='set_role_button')],
        [InlineKeyboardButton("📜 Выбрать роль", callback_data='role_select')], 
        [InlineKeyboardButton("━━━━━━━━━━ ✦ ━━━━━━━━━━", callback_data='separator')],         
        [InlineKeyboardButton("📗 Помощь", callback_data='short_help_gpt')],
        [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')],
        [InlineKeyboardButton("🔽 Скрыть меню", callback_data='gptmenu_hide')]
    ])

    # Скрытое меню (только кнопка для показа)
    collapsed_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton("📒 Меню 📒", callback_data='gptmenu_show')]
    ])

    if update.message:
        user_id = update.message.from_user.id  # Когда вызвано командой /search
        message_to_reply = update.message
    elif update.callback_query:
        user_id = update.callback_query.from_user.id  # Когда нажата кнопка
        message_to_reply = update.callback_query.message
        
        # Убираем индикатор загрузки на кнопке
        await update.callback_query.answer()

        if update.callback_query.data == "gptmenu_show":
            await message_to_reply.edit_reply_markup(reply_markup=full_menu)  # Меняем только кнопки
            return RUNNING_GPT_MODE

        elif update.callback_query.data == "gptmenu_hide":
            await message_to_reply.edit_reply_markup(reply_markup=collapsed_menu)  # Меняем только кнопки
            return RUNNING_GPT_MODE

    return RUNNING_GPT_MODE



async def handle_short_gpt_help(update: Update, context: CallbackContext) -> None:
    """Обработчик для кнопки 'Помощь по GPT'."""
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие

    help_text_1 = """
Режим диалога с ботом поддерживает следующие функции:

---Ведения связного диалога с контекстом в несколько сотен сообщений

---Выбор, придумывание и хранение ролей для диалога

---Доступ в интернет. Бот имеет доступ в сеть в связи с чем вы можете попросить его найти там что-то и предоставить информацию в удобном для вас виде. Например узнать что идёт в кино, погоду, найти и упорядочить какую-то информацию и тд

---Анализ содержания веб страниц по ссылке на них. Вы можете отправить боту ссылку на любую веб страницу и попросить бота что-то сделать с ней. Например отправить боту ссылку на научную статью написанную на английском языке и попросить пересказать выводы этой статьи на русском. Можете так же придумать что угодно ещё. Сылка и запрос к ней должны быть в одном сообщении

---Безлимитный анализ изображений, вы можете попросить бота что-то распознать с изображения, объяснить, дать совет и что угодно ещё

---Анализ музыки в виде mp3 файлов и голосовых сообщений. Например вы можете спросить что за жанр у данной песни, попросить посоветовать что-то похожее, распознать текст песни или голососвго сообщения и тд. У данной функции есть лимит в 20мб на отправляемый файл

---Анализ коротких видео и гиф. Так же как и с музыкой, есть лимит 20мб на файл

---Анализ .txt и .pdf документов. Для того чтобы он сработал корректно отправьте боту пояснение того что вам нужно сделать с информацией в файле ДО или одновременно с отправкой файла, но не после

===============================================================================

Так же в боте доступна генерация изображений. Для этого в режиме диалога с ботом начните своё сообщение с слова "Нарисуй: ***" где вместо *** вбейте свой запрос на любом языке. Если после генерации вы видите надпись "Ошибка при обработке запроса." вместо вашего запроса, то это значит что сломалась нейросеть переводящая запросы на английский. В таком случае вам придётся указать запрос на английском самостоятельно

Примеры запросов:
<pre>Нарисуй: кот на подоконнике</pre>
Обычный запрос, все настройки выставлены по-умолчанию.

<pre>нарисуй:765576, ангел в заснеженном лесу (3), [3:2]</pre>
Запрос с настройками. В данном случае 765576 - это <b>seed</b>, 3  - <b>guidance_scale</b>, а 3:2 - соотношение сторон изображения. <b>Steps</b> в круглых скобках при этом не указан и выставлен по-умолчанию. Так же "нарисуй" написано с маленькой буквы, это тоже правильный вариант.

<pre>Нарисуй дом в корнях огромного дерева (4, 20) [3:5]</pre>
Тут указан <b>Steps</b> - 20. А так же <b>guidance_scale</b> - 4 и соотношение 3:5. "Нарисуй" написано без двоеточия - такой вариант тоже считывается

<code>seed</code> - это идентификатор каждого конкретного сгенерированного изображения. Если вам понравилась какая-то из генераций, но вы хотите посмотреть как бы она выглядела с другими настройками, то вы можете использовать её seed для того чтобы изменять конкретно данную генерацию лишь слегка корректирую запрос или прочие настройки.
<code>guidance_scale</code> - это приближение генерации к тексту вашего запроса. Чем число выше, тем сильнее нейросеть пытается воссоздать именно текстовый запрос, однако сама генерация от этого может получитсья хуже, более грубой и с большим числом артефактов. Обычно корректное значение между 2 и 6, но в целом диапазон от 1 до 20
<code>Steps</code> - это шаги повторных обработок изображения. Чем их больше тем больше на изображении деталей и тем лучше оно прорисовано. Однако слишком большое число существенно замедляет время генерации и даёт не особо красивые перегруженные деталями генерации. Адекватные значения 15-30.

Кроме того, в некоторых моделях, наприме SD turbo используются свои очень специфические параметры. В упомянутой turbo напрмиер guidance_scale равен 1 а steps около 4-6 и только в таких значениях данная модель выдаёт хорошие результаты. Так что если вы поменяли настройки в генерации какой-то модели и она "сломалась", то вероятно причина именно в этом.
    """
    keyboard = [
        [InlineKeyboardButton("✂️ Сбросить диалог", callback_data='reset_dialog')],
        [InlineKeyboardButton("✏️ Придумать новую роль", callback_data='set_role_button')],
        [InlineKeyboardButton("📜 Выбрать роль", callback_data='role_select')],  
        [InlineKeyboardButton("🖼 Сменить модель", callback_data='choose_modele')],
        [InlineKeyboardButton("🎨 Выбрать стиль", callback_data='choose_preset')], 
        [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Отправляем сообщение с кнопкой
    await query.edit_message_text(help_text_1, parse_mode="HTML", reply_markup=reply_markup)









async def stop_gpt(update: Update, context: CallbackContext) -> int:
    # Проверяем, был ли вызов через кнопку или команду
    if update.callback_query:
        query = update.callback_query
        user_id = query.from_user.id
        await query.answer()
        await query.message.reply_text(
            "Режим общения с GPT отключен. Вы вернулись к основному режиму.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎨 Найти источник или проверить на ИИ 🎨", callback_data='start_search')],
                [InlineKeyboardButton("🌱 Распознать (Растение или текст) 🌱", callback_data='start_ocr')], 
                [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]
            ])
        )
    else:
        # Если вызов произошел через команду
        user_id = update.message.from_user.id
        await update.message.reply_text(
            "Режим общения с GPT отключен. Вы вернулись к основному режиму.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎨 Найти источник или проверить на ИИ 🎨", callback_data='start_search')],
                [InlineKeyboardButton("🌱 Распознать (Растение или текст) 🌱", callback_data='start_ocr')], 
                [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]
            ])
        )

    is_ocr_mode[user_id] = False  # Выключаем режим поиска
    is_search_mode[user_id] = False
    is_gpt_mode[user_id] = False
    is_role_mode[user_id] = False
    is_asking_mode[user_id] = False  # Отключаем режим GPT для пользователя
    return ConversationHandler.END






def chunk_buttons(buttons, chunk_size):
    """Группирует кнопки по chunk_size в строке."""
    return [buttons[i:i + chunk_size] for i in range(0, len(buttons), chunk_size)]



async def handle_role_select(update: Update, context: CallbackContext):
    """Обработчик для выбора роли из списка."""
    user_id = (
        update.callback_query.from_user.id
        if update.callback_query
        else update.message.from_user.id
    )

    # Получаем роли пользователя, если есть
    roles = user_roles.get(user_id, {})
    logger.info(f"roles {roles}")    
    # Если ролей нет, отображаем только дефолтные роли
    if not roles:
        # Исключаем default_role из отображаемых ролей
        excluded_roles = {"default_role"}
        
        # Создаём кнопки для дефолтных ролей
        default_buttons = [
            InlineKeyboardButton(
                f"✅ {role_data['short_name']}" if role_id in {roles.get("selected_role"), roles.get("default_role"), roles.get("game_role")} else role_data["short_name"],
                callback_data=f"defaultrole_{role_id}"
            )
            for role_id, role_data in DEFAULT_ROLES.items()
            if role_id not in excluded_roles
        ]

        # Группируем кнопки
        grouped_default_buttons = chunk_buttons(default_buttons, 3)

        # Создаём кнопки для ролей из GAME_ROLES
        game_buttons = [
            InlineKeyboardButton(
                f"✅ {role_data['short_name']}" if role_id in {roles.get("selected_role"), roles.get("default_role"), roles.get("game_role")} else role_data["short_name"],
                callback_data=f"gamerole_{role_id}"
            )
            for role_id, role_data in GAME_ROLES.items()
        ]

        # Группируем кнопки
        grouped_game_buttons = chunk_buttons(game_buttons, 2)  # Можно изменить на 3, если нужно

        # Создаём разделители
        separator_game_button = [InlineKeyboardButton("━━━━━━━━━━ ✦ ━━━━━━━━━━", callback_data='separator')]
        separator_game_button_2 = [InlineKeyboardButton("━━━━━━━━━━ ✦ ━━━━━━━━━━", callback_data='separator')]




        new_role_button = [InlineKeyboardButton("✏️ Добавить новую роль", callback_data='set_role_button')]
        reset = [InlineKeyboardButton("✂️ Сбросить диалог", callback_data='reset_dialog')]        
        cancel_button = [InlineKeyboardButton("⬅️ Закрыть окно ⬅️", callback_data='cancel_role_selection')]  # Кнопка отмены        
        # Формируем клавиатуру и текст сообщения
        keyboard = InlineKeyboardMarkup(grouped_default_buttons + [separator_game_button] + grouped_game_buttons + [separator_game_button_2] +  [new_role_button] + [reset] + [cancel_button])
        message_text = "У вас пока нет своих ролей. Выберите одну из доступных ролей по умолчанию."

        # Отправляем сообщение
        if update.callback_query:
            await update.callback_query.answer()
            await update.effective_chat.send_message(message_text, reply_markup=keyboard, parse_mode='Markdown')
        else:
            await update.message.reply_text(message_text, reply_markup=keyboard, parse_mode='Markdown')
        context.user_data['role_message_id'] = msg.message_id
        return

    # Определяем исключаемые роли
    excluded_roles = {"default_role", "selected_role", "game_role"}

    # Определяем текущую выбранную роль
    current_role = None
    if "selected_role" in roles:
        current_role = f"Текущая роль: *{roles['selected_role']}*"
    if "game_role" in roles and roles["game_role"] in GAME_ROLES:
        current_role = f"Текущая роль: *{GAME_ROLES[roles['game_role']]['short_name']}*"       
    elif "default_role" in roles and roles["default_role"] in DEFAULT_ROLES:
        current_role = f"Текущая роль: *{DEFAULT_ROLES[roles['default_role']]['short_name']}*"

    # Создаём кнопки для ролей по умолчанию, исключая default_role
    default_buttons = [
        InlineKeyboardButton(
            f"✅ {role_data['short_name']}" if role_id in {roles.get("selected_role"), roles.get("default_role"), roles.get("game_role")} else role_data["short_name"],
            callback_data=f"defaultrole_{role_id}"
        )
        for role_id, role_data in DEFAULT_ROLES.items()
        if role_id not in excluded_roles
    ]

    # Создаём кнопки для пользовательских ролей, исключая selected_role
    custom_buttons = []
    if "short_names" in roles:
        custom_buttons = [
            InlineKeyboardButton(
                f"✅ {roles['short_names'].get(role_id, ' '.join(str(role_text).split()[:5]))}"
                if role_text == roles.get("selected_role") else roles["short_names"].get(role_id, ' '.join(str(role_text).split()[:5])),
                callback_data=f"newroleselect_{role_id}"
            )
            for role_id, role_text in roles.items()
            if role_id not in excluded_roles and role_id != "short_names"
        ]



    # Создаём кнопки для ролей из GAME_ROLES
    game_buttons = [
        InlineKeyboardButton(
            f"✅ {role_data['short_name']}" if role_id in {roles.get("selected_role"), roles.get("default_role"), roles.get("game_role")} else role_data["short_name"],
            callback_data=f"gamerole_{role_id}"
        )
        for role_id, role_data in GAME_ROLES.items()
        if role_id not in excluded_roles
    ]

    # Группируем кнопки
    grouped_game_buttons = chunk_buttons(game_buttons, 2)  # Можно изменить на 3, если нужно

    # Создаём разделители
    separator_game_button_3 = [InlineKeyboardButton("━━━━━━━━━━ ✦ ━━━━━━━━━━", callback_data='separator')]



    # Группируем кнопки
    grouped_default_buttons = chunk_buttons(default_buttons, 3)
    separator_button = [InlineKeyboardButton("━━━━━━━━━━ ✦ ━━━━━━━━━━", callback_data='separator')]
    grouped_custom_buttons = chunk_buttons(custom_buttons, 2)

    # Добавляем новую кнопку в конец
    new_role_button = [InlineKeyboardButton("✏️ Добавить новую роль", callback_data='set_role_button')]
    reset = [InlineKeyboardButton("✂️ Сбросить диалог", callback_data='reset_dialog')]    
    cancel_button = [InlineKeyboardButton("⬅️ Закрыть окно ⬅️", callback_data='cancel_role_selection')]  # Кнопка отмены    

    # Объединяем кнопки и формируем клавиатуру
    keyboard = InlineKeyboardMarkup(grouped_default_buttons + [separator_game_button_3] + grouped_game_buttons + [separator_button] +  grouped_custom_buttons + [new_role_button] + [reset] + [cancel_button])

    # Формируем сообщение с учётом текущей роли
    message_text = "Выберите роль из списка."
    if current_role:
        message_text += f"\n\n{current_role}"

    # Отправляем ответ в зависимости от типа update
    if update.callback_query:
        await update.callback_query.answer()
        msg = await update.effective_chat.send_message(message_text, reply_markup=keyboard, parse_mode='Markdown')
    else:
        msg = await update.message.reply_text(message_text, reply_markup=keyboard, parse_mode='Markdown')

    context.user_data['role_message_id'] = msg.message_id


# Обработчик выбора роли (включая роли по умолчанию)
async def handle_role_selected(update: Update, context: CallbackContext):
    """Обработчик выбора конкретной роли из кнопок."""
    user_id = update.callback_query.from_user.id
    query_data = update.callback_query.data

    # Обновляем роль пользователя
    if query_data.startswith("defaultrole_"):
        role_id = query_data.split("_")[1]
        selected_role_data = DEFAULT_ROLES.get(role_id)

        if selected_role_data:
            # Устанавливаем выбранную роль как default_role
            if user_id not in user_roles:
                user_roles[user_id] = {}

            user_roles[user_id]["default_role"] = role_id  # Сохраняем ID роли
            user_roles[user_id].pop("selected_role", None)  
            user_roles[user_id].pop("game_role", None)                       
            save_context_to_firebase(user_id)  # Сохраняем изменения в Firebase

            # Формируем обновленный текст сообщения
            message_text = f"Выберите роль из списка.\n\nТекущая роль: *{selected_role_data['short_name']}*"

            # Получаем обновленную клавиатуру
            keyboard = await create_updated_keyboard(user_id)

            # Обновляем сообщение целиком (текст + клавиатура)
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                text=message_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )

        else:
            await update.callback_query.answer("Ошибка выбора роли.")

    elif query_data.startswith("newroleselect_"):
        role_id = query_data.split("_")[1]  # Получаем ID роли

        if user_id in user_roles and role_id in user_roles[user_id]:
            selected_role = user_roles[user_id][role_id]

            # Устанавливаем выбранную роль как "selected_role" и сбрасываем default_role
            user_roles[user_id]["selected_role"] = selected_role
            user_roles[user_id].pop("default_role", None)  # Удаляем default_role, если он существует
            user_roles[user_id].pop("game_role", None)
            save_context_to_firebase(user_id)

            # Формируем обновленный текст сообщения
            message_text = f"Выберите роль из списка.\n\nТекущая роль: *{selected_role}*"
            message_text_2 = f"Вы выбрали роль: <pre>{selected_role}</pre>"
            # Получаем обновленную клавиатуру
            keyboard = await create_updated_keyboard(user_id)

            # Создаём инлайн-кнопку для удаления роли
            delete_button = InlineKeyboardButton(
                "Удалить эту роль",
                callback_data=f"clear_role_{role_id}"
            )
            new_keyboard = InlineKeyboardMarkup([[delete_button]])

            # Обновляем сообщение целиком (текст + клавиатура)
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                text=message_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            # Отправляем новое сообщение с кнопкой удаления
            await update.callback_query.message.reply_text(
                message_text_2,
                reply_markup=new_keyboard,
                parse_mode='HTML'
            )
        else:
            await update.callback_query.answer("Ошибка выбора роли.")
    elif query_data.startswith("gamerole_"):
        role_id = query_data.split("_")[1]
        selected_role_data = GAME_ROLES.get(role_id)

        if selected_role_data:
            if user_id not in user_roles:
                user_roles[user_id] = {}

            user_roles[user_id]["game_role"] = role_id  
            user_roles[user_id].pop("default_role", None) 
            user_roles[user_id].pop("selected_role", None)                        
            save_context_to_firebase(user_id)

            message_text = f"Вы выбрали игровую роль.\n\nТекущая игровая роль: *{selected_role_data['short_name']}*"
            keyboard = await create_updated_keyboard(user_id)

            # Отправка уведомления, если оно есть в словаре
            alert_text = selected_role_data.get("alert")
            if alert_text:
                await update.callback_query.answer(alert_text, show_alert=True)
            else:
                await update.callback_query.answer()

            await update.callback_query.edit_message_text(
                text=message_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            await update.callback_query.answer("Ошибка выбора игровой роли.")

async def create_updated_keyboard(user_id):
    """Создает обновленную клавиатуру с учетом текущего состояния ролей пользователя."""
    roles = user_roles.get(user_id, {})
    excluded_roles = {"default_role", "selected_role", "game_role"}

    # Создаём кнопки для ролей по умолчанию
    default_buttons = [
        InlineKeyboardButton(
            f"✅ {role_data['short_name']}" if role_id in {roles.get("selected_role"), roles.get("default_role"), roles.get("game_role")} else role_data["short_name"],
            callback_data=f"defaultrole_{role_id}"
        )
        for role_id, role_data in DEFAULT_ROLES.items()
        if role_id not in excluded_roles
    ]

    # Создаём кнопки для ролей из GAME_ROLES


    # Группируем кнопки
  # Можно изменить на 3, если нужно
    game_buttons = [
        InlineKeyboardButton(
            f"✅ {role_data['short_name']}" if role_id in {roles.get("selected_role"), roles.get("default_role"), roles.get("game_role")} else role_data["short_name"],
            callback_data=f"gamerole_{role_id}"
        )
        for role_id, role_data in GAME_ROLES.items()
        if role_id not in excluded_roles and role_id != "short_names"            
    ]    
    # Создаём разделители



    # Создаём кнопки для пользовательских ролей
    custom_buttons = []
    if "short_names" in roles:
        custom_buttons = [
            InlineKeyboardButton(
                f"✅ {roles['short_names'].get(role_id, ' '.join(str(role_text).split()[:5]))}"
                if role_text == roles.get("selected_role") else roles["short_names"].get(role_id, ' '.join(str(role_text).split()[:5])),
                callback_data=f"newroleselect_{role_id}"
            )
            for role_id, role_text in roles.items()
            if role_id not in excluded_roles and role_id != "short_names"
        ]
    
    separator_game_button_3 = [InlineKeyboardButton("━━━━━━━━━━ ✦ ━━━━━━━━━━", callback_data='separator')]
    # Группируем кнопки
    grouped_default_buttons = chunk_buttons(default_buttons, 3)
    grouped_game_buttons = chunk_buttons(game_buttons, 2)    
    grouped_custom_buttons = chunk_buttons(custom_buttons, 2)
    separator_button = [InlineKeyboardButton("━━━━━━━━━━ ✦ ━━━━━━━━━━", callback_data='separator')]
    # Добавляем кнопки "Добавить новую роль" и "Отмена"
    new_role_button = [InlineKeyboardButton("✏️ Добавить новую роль", callback_data='set_role_button')]
    reset = [InlineKeyboardButton("✂️ Сбросить диалог", callback_data='reset_dialog')]
    cancel_button = [InlineKeyboardButton("⬅️ Закрыть окно ⬅️", callback_data='cancel_role_selection')]

    # Формируем клавиатуру
    keyboard = InlineKeyboardMarkup(grouped_default_buttons + [separator_game_button_3] + grouped_game_buttons + [separator_button] +  grouped_custom_buttons + [new_role_button] + [reset] + [cancel_button])
    return keyboard         

from telegram.error import TelegramError  # Импортируем ошибку

async def handle_cancel_role(update: Update, context: CallbackContext):
    """Удаляет сообщение с выбором роли"""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    # Получаем ID сообщения с выбором роли
    role_message_id = context.user_data.get('role_message_id')

    if role_message_id:
        try:
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=role_message_id)
        except TelegramError:
            pass  # Игнорируем ошибку, если сообщение уже удалено

    # Можно отправить другое сообщение, если нужно
    await query.message.reply_text("Окно выбора закрыто.", reply_markup=None)

async def handle_delete_role(update: Update, context: CallbackContext):
    """Обработчик удаления выбранной роли."""
    user_id = update.callback_query.from_user.id
    query_data = update.callback_query.data
    role_id = query_data.split("_")[2]  # Получаем ID роли из callback_data

    if user_id in user_roles and role_id in user_roles[user_id]:
        # Удаляем роль
        deleted_role = user_roles[user_id].pop(role_id)
        save_context_to_firebase(user_id)

        await update.callback_query.answer("Роль удалена.")
        await update.callback_query.message.reply_text(
            f"Роль '{deleted_role}' была успешно удалена."
        )

        # Удаляем старое сообщение с клавиатурой, если оно существует
        if 'role_message_id' in context.user_data:
            try:
                await context.bot.delete_message(
                    chat_id=update.callback_query.message.chat_id,
                    message_id=context.user_data['role_message_id']
                )
            except Exception as e:
                print(f"Ошибка при удалении сообщения: {e}")

        # Обновляем клавиатуру
        await handle_role_select(update, context)
    else:
        await update.callback_query.answer("Ошибка удаления роли.")


async def set_role(update: Update, context: CallbackContext):
    """Команда для установки новой роли пользователем."""
    user_id = update.message.from_user.id
    role_text = update.message.text.replace("/set_role", "").strip()
    
    if role_text:
        set_user_role(user_id, role_text)
        await update.message.reply_text(f"Ваша роль успешно сохранена и применена: {role_text}")
    else:
        await update.message.reply_text("Пожалуйста, введите роль после команды /set_role.")

async def handle_set_role_button(update: Update, context: CallbackContext):
    """Обработчик для кнопки установки роли."""
    user_id = update.callback_query.from_user.id
    
    # Завершаем текущий разговор с GPT, если он активен
    if is_gpt_mode.get(user_id, False):
        is_gpt_mode[user_id] = False  # Выключаем режим GPT
    
    # Включаем режим ролей
    is_role_mode[user_id] = True
    await update.callback_query.answer()  # Отправить ответ на нажатие кнопки

    # Создаём разметку с кнопкой "Отмена"
    keyboard = [[InlineKeyboardButton("🌌Отмена🌌", callback_data='run_gpt')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение с HTML-разметкой
    await update.callback_query.message.reply_text(
        "Пожалуйста, введите описание новой роли. Это может быть очень короткое, либо наоборот длинное и подробное описание. "
        "В круглых скобках в начале вы можете указать слово или фразу, которая будет отображаться в кнопке. Пример: \n"
        "<pre>(Лиса) Ты мудрая старая лиса, живущая на окраине волшебного леса</pre>",
        parse_mode='HTML',
        reply_markup=reply_markup  # Добавляем клавиатуру с кнопкой
    )
    
    return ASKING_FOR_ROLE


async def receive_role_input(update: Update, context: CallbackContext):
    """Обработчик для ввода роли пользователем."""
    user_id = update.message.from_user.id
    role_text = update.message.text.strip()

    if role_text:
        set_user_role(user_id, role_text)  # Устанавливаем роль
        await update.message.reply_text(f"Ваша роль успешно изменена на: {role_text}")
    else:
        await update.message.reply_text("Пожалуйста, введите роль после команды /set_role.")
    
    # Отключаем режим ролей и возвращаемся в режим GPT
    is_role_mode[user_id] = False
    is_gpt_mode[user_id] = True  # Включаем режим GPT обратно
    await handle_role_select(update, context)    
    return ConversationHandler.END  # Завершаем разговор, можно продолжить с основного состояния  



async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    username = update.message.from_user.username or update.message.from_user.first_name
    user_id = update.message.from_user.id
    caption = update.message.caption or ""

    logger.info("Обработка аудио от пользователя")

    audio = update.message.audio or update.message.voice
    file = await context.bot.get_file(audio.file_id)

    file_extension = os.path.splitext(file.file_path)[1] or ".oga"
    fd, local_file_path = tempfile.mkstemp(suffix=file_extension)
    os.close(fd)

    await file.download_to_drive(local_file_path)

    audio_type = "[Голосовое сообщение]" if update.message.voice else "[Аудиофайл]"
    full_caption = f"{audio_type} {caption}".strip()

    # Сообщение "ожидания"
    waiting_message = await update.message.reply_text("🎧 Обрабатываю аудио...")

    async def process_audio():
        try:
            full_audio_response = await generate_audio_response(local_file_path, user_id, query=caption)
            logger.info("Ответ от Gemini: %s", full_audio_response)

            add_to_context(user_id, full_caption, message_type="user_send_audio")
            add_to_context(user_id, full_audio_response, message_type="bot_audio_response")
            save_context_to_firebase(user_id)

            # Разбивка текста на части по 4096 символов
            if len(full_audio_response) <= MAX_MESSAGE_LENGTH:
                await waiting_message.edit_text(full_audio_response)
            else:
                parts = [full_audio_response[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(full_audio_response), MAX_MESSAGE_LENGTH)]
                await waiting_message.edit_text(parts[0])
                for i, part in enumerate(parts[1:], start=1):
                    await update.message.reply_text(part)

        except Exception as e:
            logger.error("Ошибка при обработке аудио: %s", e)
            await waiting_message.edit_text("⚠️ Произошла ошибка при обработке аудио. Попробуйте снова.")

        finally:
            os.remove(local_file_path)

    asyncio.create_task(process_audio())


async def handle_gptgif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    username = update.message.from_user.username or update.message.from_user.first_name
    user_id = update.message.from_user.id
    caption = update.message.caption or ""

    logger.info("Обработка GIF от пользователя")

    # Сообщение пользователю, что идёт обработка
    waiting_message = await update.message.reply_text("Обрабатываю GIF...")

    async def process_gif():
        animation = update.message.animation
        file = await context.bot.get_file(animation.file_id)

        # Определение исходного расширения
        file_extension = os.path.splitext(file.file_path)[1] or ".mp4"

        # Создание временного файла
        fd, local_file_path = tempfile.mkstemp(suffix=file_extension)
        os.close(fd)

        try:
            # Загрузка GIF в файл
            await file.download_to_drive(local_file_path)

            # Генерация ответа
            full_animation_response = await generate_video_response(
                local_file_path,
                user_id,
                query=caption
            )

            add_to_context(user_id, caption, message_type="user_send_gif")
            add_to_context(user_id, full_animation_response, message_type="bot_gif_response")
            save_context_to_firebase(user_id)

            if full_animation_response:
                # Отправка ответа пользователю (с учётом длинных сообщений)
                text_parts = await send_reply_with_limit(full_animation_response)

                if len(text_parts) == 1:
                    await waiting_message.edit_text(
                        text_parts[0],
                        parse_mode='MarkdownV2',
                        reply_markup=collapsed_menu
                    )
                else:
                    await waiting_message.edit_text(text_parts[0], parse_mode='MarkdownV2')
                    for i, part in enumerate(text_parts[1:], start=1):
                        is_last = (i == len(text_parts) - 1)
                        await update.message.reply_text(
                            part,
                            parse_mode='MarkdownV2',
                            reply_markup=collapsed_menu if is_last else None
                        )
            else:
                await waiting_message.edit_text("Произошла ошибка при обработке GIF. Попробуйте снова. /restart")

        except Exception as e:
            await waiting_message.edit_text(f"Ошибка: {e}")

        finally:
            if os.path.exists(local_file_path):
                os.remove(local_file_path)

    # Запускаем обработку GIF в фоне
    asyncio.create_task(process_gif())


async def handle_gptvideo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    username = update.message.from_user.username or update.message.from_user.first_name
    user_id = update.message.from_user.id
    caption = update.message.caption or ""

    logger.info(f"Обработка видео от пользователя {username} ({user_id})")

    waiting_message = await update.message.reply_text("Обрабатываю видео...")

    async def process_video():
        video = update.message.video
        file = await context.bot.get_file(video.file_id)

        # Определение исходного расширения файла
        file_extension = os.path.splitext(file.file_path)[1] or ".mp4"

        # Создание временного файла с исходным расширением
        fd, local_file_path = tempfile.mkstemp(suffix=file_extension)
        os.close(fd)

        try:
            # Скачивание видео
            await file.download_to_drive(local_file_path)

            # Генерация ответа
            full_video_response = await generate_video_response(
                local_file_path,
                user_id,
                query=caption
            )

            # Добавление в контекст
            add_to_context(user_id, caption, message_type="user_send_video")
            add_to_context(user_id, full_video_response, message_type="bot_video_response")
            save_context_to_firebase(user_id)

            if full_video_response:
                await waiting_message.edit_text(full_video_response)
            else:
                await waiting_message.edit_text("Не удалось обработать видео. Попробуйте снова. /restart")

        except Exception as e:
            await waiting_message.edit_text(f"Ошибка при обработке видео: {e}")

        finally:
            if os.path.exists(local_file_path):
                os.remove(local_file_path)

    # Запускаем фоновую задачу
    asyncio.create_task(process_video())
        
import asyncio
import os
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def handle_documentgpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    username = update.message.from_user.username or update.message.from_user.first_name
    user_id = update.message.from_user.id
    caption = update.message.caption or ""

    reset_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("✂️Сбросить диалог✂️", callback_data='reset_dialog')],
        [InlineKeyboardButton("📜\nВыбрать роль", callback_data='role_select')], 
        [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')],
    ])

    logger.info("Обработка текстового документа от пользователя")

    # Сразу отправляем "заглушку", чтобы пользователь видел, что идёт работа
    waiting_message = await update.message.reply_text("Обрабатываю документ...")

    async def process_document():
        document = update.message.document
        file = await context.bot.get_file(document.file_id)

        file_extension = os.path.splitext(document.file_name)[1] or ".txt"

        fd, local_file_path = tempfile.mkstemp(suffix=file_extension)
        os.close(fd)

        try:
            await file.download_to_drive(local_file_path)

            full_text_response = await generate_document_response(local_file_path, user_id, caption)

            add_to_context(user_id, caption, message_type="user_send_document")         
            add_to_context(user_id, full_text_response, message_type="bot_document_response")
            save_context_to_firebase(user_id)        

            # Разбиваем текст на части
            text_parts = await send_reply_with_limit(full_text_response)
            logger.info(f"text_parts {text_parts}")

            # Первую часть заменяем в "ожидании"
            if text_parts:
                await waiting_message.edit_text(
                    text_parts[0],
                    parse_mode='MarkdownV2',
                    reply_markup=reset_button if len(text_parts) == 1 else None
                )

            # Остальные части отправляем отдельными сообщениями
            for i, part in enumerate(text_parts[1:], start=1):
                is_last_part = i == len(text_parts) - 1
                await update.message.reply_text(
                    part,
                    reply_markup=reset_button if is_last_part else None,
                    parse_mode='MarkdownV2'
                )

        except Exception as e:
            logger.error(f"Ошибка обработки документа: {e}")
            await waiting_message.edit_text(f"Ошибка при обработке документа: {e}")
        finally:
            os.remove(local_file_path)

    # Запускаем асинхронную задачу в фоне
    asyncio.create_task(process_document())



async def gpt_running(update: Update, context: CallbackContext) -> int:

    user_id = None
    user_message = None    
    user_image = None
    logger.info(f"user_message {user_message}")
    # Основная клавиатура с тремя кнопками
    full_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏙 Посмотреть чужие генерации", callback_data="view_shared")],        
        [InlineKeyboardButton("🖼 Сменить модель", callback_data='choose_modele')],
        [InlineKeyboardButton("🎨 Выбрать стиль", callback_data='choose_preset')],  
        [InlineKeyboardButton("━━━━━━━━━━ ✦ ━━━━━━━━━━", callback_data='separator')],
        [InlineKeyboardButton("✂️ Сбросить диалог", callback_data='reset_dialog')],        
        [InlineKeyboardButton("✏️ Придумать новую роль", callback_data='set_role_button')],
        [InlineKeyboardButton("📜 Выбрать роль", callback_data='role_select')],  
        [InlineKeyboardButton("━━━━━━━━━━ ✦ ━━━━━━━━━━", callback_data='separator')],        
        [InlineKeyboardButton("📗 Помощь", callback_data='short_help_gpt')],
        [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')],
        [InlineKeyboardButton("🔽 Скрыть меню", callback_data='gptmenu_hide')]
    ])

    # Клавиатура с одной кнопкой "Меню"
    collapsed_menu = InlineKeyboardMarkup([
        [InlineKeyboardButton("📒 Меню 📒", callback_data='gptmenu_show')]
    ])

    # Если обновление - это callback-запрос (нажатие кнопки)
    if update.callback_query:
        query = update.callback_query
        user_id = query.from_user.id
        await query.answer()

        if query.data == "gptmenu_show":
            await query.message.edit_reply_markup(reply_markup=full_menu)
            return RUNNING_GPT_MODE

        elif query.data == "gptmenu_hide":
            await query.message.edit_reply_markup(reply_markup=collapsed_menu)
            return RUNNING_GPT_MODE

        elif query.data == 'reset_dialog':
            user_roles[user_id] = "Ты играешь роль телеграм чат бота"
            save_context_to_firebase(user_id)
            await query.answer("Диалог и роль сброшены.")
            return ASKING_FOR_ROLE







    if update.message.reply_to_message and update.message.text:
        quoted_text = update.message.quote.text if update.message.quote else None
        bot_id = context.bot.id
        user_id = update.message.from_user.id
        original_message = update.message.reply_to_message  # Здесь добавляем переменную
        logger.info(f"quoted_text: {quoted_text}")  
        user_message = update.message.text
        draw_triggers = ["нарисуй", "нарисуй:", "Нарисуй", "Нарисуй:", "draw", "draw:", "Draw", "Draw:"]

        if any(user_message.startswith(trigger) for trigger in draw_triggers):
            extra_text = user_message.split(maxsplit=1)[1] if len(user_message.split()) > 1 else ""
            
            if quoted_text:
                prompt_text = quoted_text
            elif original_message:
                prompt_text = original_message
            else:
                prompt_text = ""

            if extra_text:
                prompt_text += " " + extra_text

            # Запускаем асинхронную генерацию без перевода
            return await limited_image_generation(update, context, user_id, prompt_text)

        if original_message.text:      

            if original_message.from_user.id == bot_id:
                prefix = "Пользователь процитировал одно из твоих прошлых сообщений, которое выглядит так"
            elif original_message.from_user.id == user_id:
                prefix = "Пользователь процитировал одно из своих прошлых сообщений, которое выглядит так"
            else:
                prefix = f"Пользователь процитировал сообщение от {original_message.from_user.full_name}, которое выглядит так"

            query = f"{prefix}: " \
                    f"\"{quoted_text if quoted_text else original_message.text}\" и написал: \"{user_message}\"."

            logger.info(f"query_text: {query}")  

            waiting_message = await update.message.reply_text("Думаю над ответом, пожалуйста, подождите...")

            async def process():
                try:
                    response_text = await generate_gemini_response(user_id, query=query)
                    add_to_context(
                        user_id,
                        f"{prefix}: \"{quoted_text if quoted_text else original_message.text}\" И написал: \"{user_message}\"",
                        message_type="user_reply_text"
                    )


                    if response_text:
                        text_parts = await send_reply_with_limit(response_text)

                        if len(text_parts) == 1:
                            # Один ответ — сразу редактируем сообщение и добавляем кнопки
                            await waiting_message.edit_text(
                                text_parts[0],
                                parse_mode='MarkdownV2',
                                reply_markup=collapsed_menu
                            )
                        else:
                            # Редактируем сообщение ожидания первой частью ответа
                            await waiting_message.edit_text(text_parts[0], parse_mode='MarkdownV2')

                            # Остальные части отправляем новыми сообщениями
                            for i, part in enumerate(text_parts[1:], start=1):
                                is_last = (i == len(text_parts) - 1)
                                await update.message.reply_text(
                                    part,
                                    parse_mode='MarkdownV2',
                                    reply_markup=collapsed_menu if is_last else None
                                )

                        add_to_context(user_id, response_text, message_type="bot_response")
                        save_context_to_firebase(user_id)
                    else:
                        await waiting_message.edit_text("Произошла ошибка при генерации ответа. Попробуйте снова. /restart")

                except Exception as e:
                    await waiting_message.edit_text(f"Ошибка: {e}")

            asyncio.create_task(process())
            return
        elif original_message.photo:
        
            waiting_message = await update.message.reply_text("Обрабатываю изображение...")
        
            async def process():
                try:
                    # Проверяем, начинается ли caption с ключевых слов (дорисуй, доделай и т.д.)
                    match = re.match(r"(?i)^(дорисуй|доделай|замени|добавь|отредактируй):?\s*(.+)", user_message)
                    if match:
                        inpaint_prompt = match.group(2).strip()
                        logging.info(f"inpaint_prompt: {inpaint_prompt}")
        
                        # Загружаем изображение
                        photo_file = await original_message.photo[-1].get_file()
                        img_data = io.BytesIO()
                        await photo_file.download_to_memory(out=img_data)
        
                        # Определяем путь к папке temp
                        base_dir = os.path.dirname(os.path.abspath(__file__))
                        temp_dir = os.path.join(base_dir, "temp")
                        os.makedirs(temp_dir, exist_ok=True)
        
                        # Сохраняем временное изображение
                        temp_image_path = os.path.join(temp_dir, f"inpaint_{user_id}.jpg")
                        with open(temp_image_path, "wb") as f:
                            f.write(img_data.getvalue())
        
                        # Передаём в функцию дорисовки
                        response_text = await inpaint_image(update, context, temp_image_path, inpaint_prompt)
        
                    else:
                        # Если не дорисовка — просто описание изображения
                        original_photo = update.message.reply_to_message.photo[-1]
                        file = await context.bot.get_file(original_photo.file_id)
        
                        os.makedirs("downloads", exist_ok=True)
                        image_path = f"downloads/image_{original_photo.file_id}.jpg"
                        await file.download_to_drive(image_path)
        
                        response_text = await generate_image_description(
                            user_id,
                            image_path=image_path,
                            query=user_message
                        )
        
                        add_to_context(user_id, f"{user_message}", message_type="user_reply_image")
        
                    # Отправка ответа пользователю
                    if response_text:
                        text_parts = await send_reply_with_limit(response_text)
        
                        if len(text_parts) == 1:
                            await waiting_message.edit_text(
                                text_parts[0],
                                parse_mode='MarkdownV2',
                                reply_markup=collapsed_menu
                            )
                        else:
                            await waiting_message.edit_text(text_parts[0], parse_mode='MarkdownV2')
        
                            for i, part in enumerate(text_parts[1:], start=1):
                                is_last = (i == len(text_parts) - 1)
                                await update.message.reply_text(
                                    part,
                                    parse_mode='MarkdownV2',
                                    reply_markup=collapsed_menu if is_last else None
                                )
        
                        add_to_context(user_id, response_text, message_type="bot_response")
                        save_context_to_firebase(user_id)
                    else:
                        await waiting_message.edit_text("Произошла ошибка при обработке изображения. Попробуйте снова. /restart")
        
                except Exception as e:
                    await waiting_message.edit_text(f"Ошибка: {e}")
        
            asyncio.create_task(process())
            return
        elif original_message.video:
            waiting_message = await update.message.reply_text("Обрабатываю видео...")

            async def process_video():
                try:
                    original_video = original_message.video
                    file = await context.bot.get_file(original_video.file_id)

                    os.makedirs("downloads", exist_ok=True)
                    video_file_path = f"downloads/video_{original_video.file_id}.mp4"
                    await file.download_to_drive(video_file_path)

                    response_text = await generate_video_response(
                        video_file_path=video_file_path,
                        user_id=user_id,
                        query=user_message
                    )
                    add_to_context(user_id, f"{user_message}", message_type="user_reply_video")

                    if response_text:
                        text_parts = await send_reply_with_limit(response_text)

                        if len(text_parts) == 1:
                            await waiting_message.edit_text(
                                text_parts[0],
                                parse_mode='MarkdownV2',
                                reply_markup=collapsed_menu
                            )
                        else:
                            await waiting_message.edit_text(text_parts[0], parse_mode='MarkdownV2')
                            for i, part in enumerate(text_parts[1:], start=1):
                                is_last = (i == len(text_parts) - 1)
                                await update.message.reply_text(
                                    part,
                                    parse_mode='MarkdownV2',
                                    reply_markup=collapsed_menu if is_last else None
                                )

                        add_to_context(user_id, response_text, message_type="bot_response")
                        save_context_to_firebase(user_id)
                    else:
                        await waiting_message.edit_text("Произошла ошибка при генерации ответа. Попробуйте снова. /restart")

                except Exception as e:
                    await waiting_message.edit_text(f"Ошибка: {e}")

            asyncio.create_task(process_video())
            return
        elif original_message.audio or original_message.voice:
            waiting_message = await update.message.reply_text("Обрабатываю аудио...")

            async def process_audio():
                try:
                    original_audio = original_message.audio or original_message.voice
                    file = await context.bot.get_file(original_audio.file_id)

                    os.makedirs("downloads", exist_ok=True)
                    audio_file_path = f"downloads/audio_{original_audio.file_id}.mp3"
                    await file.download_to_drive(audio_file_path)

                    response_text = await generate_audio_response(
                        audio_file_path=audio_file_path,
                        user_id=user_id,
                        query=user_message
                    )
                    add_to_context(user_id, f"{user_message}", message_type="user_reply_audio")

                    if response_text:
                        text_parts = await send_reply_with_limit(response_text)

                        if len(text_parts) == 1:
                            await waiting_message.edit_text(
                                text_parts[0],
                                parse_mode='MarkdownV2',
                                reply_markup=collapsed_menu
                            )
                        else:
                            await waiting_message.edit_text(text_parts[0], parse_mode='MarkdownV2')
                            for i, part in enumerate(text_parts[1:], start=1):
                                is_last = (i == len(text_parts) - 1)
                                await update.message.reply_text(
                                    part,
                                    parse_mode='MarkdownV2',
                                    reply_markup=collapsed_menu if is_last else None
                                )

                        add_to_context(user_id, response_text, message_type="bot_response")
                        save_context_to_firebase(user_id)
                    else:
                        await waiting_message.edit_text("Произошла ошибка при генерации ответа. Попробуйте снова. /restart")

                except Exception as e:
                    await waiting_message.edit_text(f"Ошибка: {e}")

            asyncio.create_task(process_audio())
            return
        elif original_message.animation:  # Гифки попадают в animation
            waiting_message = await update.message.reply_text("Обрабатываю анимацию...")

            async def process_animation():
                try:
                    original_animation = original_message.animation
                    file = await context.bot.get_file(original_animation.file_id)

                    os.makedirs("downloads", exist_ok=True)
                    animation_file_path = f"downloads/animation_{original_animation.file_id}.mp4"
                    await file.download_to_drive(animation_file_path)

                    prompt_animation = (
                        f"Пользователь процитировал анимацию и написал: \"{user_message}\". "
                        f"Ответь на сообщение или запрос пользователя."
                    )

                    response_text = await generate_video_response(
                        video_file_path=animation_file_path,
                        user_id=user_id,
                        query=prompt_animation,
                    )
                    add_to_context(user_id, f"{user_message}", message_type="user_reply_GIF")

                    if response_text:
                        text_parts = await send_reply_with_limit(response_text)

                        if len(text_parts) == 1:
                            await waiting_message.edit_text(
                                text_parts[0],
                                parse_mode='MarkdownV2',
                                reply_markup=collapsed_menu
                            )
                        else:
                            await waiting_message.edit_text(text_parts[0], parse_mode='MarkdownV2')
                            for i, part in enumerate(text_parts[1:], start=1):
                                is_last = (i == len(text_parts) - 1)
                                await update.message.reply_text(
                                    part,
                                    parse_mode='MarkdownV2',
                                    reply_markup=collapsed_menu if is_last else None
                                )

                        add_to_context(user_id, response_text, message_type="bot_response")
                        save_context_to_firebase(user_id)
                    else:
                        await waiting_message.edit_text("Произошла ошибка при генерации ответа. Попробуйте снова. /restart")

                except Exception as e:
                    await waiting_message.edit_text(f"Ошибка: {e}")

            asyncio.create_task(process_animation())
            return
        elif original_message.document:  # Проверяем, если сообщение содержит документ
            waiting_message = await update.message.reply_text("Обрабатываю документ...")

            async def process_document():
                try:
                    original_document = original_message.document
                    file = await context.bot.get_file(original_document.file_id)

                    os.makedirs("downloads", exist_ok=True)
                    document_extension = original_document.file_name.split(".")[-1].lower()
                    document_file_path = f"downloads/document_{original_document.file_id}.{document_extension}"
                    await file.download_to_drive(document_file_path)

                    if document_extension in ["txt", "pdf"]:
                        prompt_document = (
                            f"Пользователь обратился к документу и написал: \"{user_message}\". "
                            f"Ответь на сообщение или запрос пользователя."
                        )

                        response_text = await generate_document_response(
                            document_path=document_file_path,
                            user_id=user_id,
                            query=prompt_document
                        )
                        add_to_context(user_id, f"{user_message}", message_type="user_reply_document")

                        if response_text:
                            text_parts = await send_reply_with_limit(response_text)

                            if len(text_parts) == 1:
                                await waiting_message.edit_text(
                                    text_parts[0],
                                    parse_mode='MarkdownV2',
                                    reply_markup=collapsed_menu
                                )
                            else:
                                await waiting_message.edit_text(text_parts[0], parse_mode='MarkdownV2')
                                for i, part in enumerate(text_parts[1:], start=1):
                                    is_last = (i == len(text_parts) - 1)
                                    await update.message.reply_text(
                                        part,
                                        parse_mode='MarkdownV2',
                                        reply_markup=collapsed_menu if is_last else None
                                    )

                            add_to_context(user_id, response_text, message_type="bot_response")
                            save_context_to_firebase(user_id)
                        else:
                            await waiting_message.edit_text("Произошла ошибка при обработке документа. Попробуйте снова. /restart")
                    else:
                        await waiting_message.edit_text("Этот формат документа не поддерживается. Отправьте .txt или .pdf.")

                except Exception as e:
                    await waiting_message.edit_text(f"Ошибка: {e}")

            asyncio.create_task(process_document())
            return






    if update.message.document:
        mime_type = update.message.document.mime_type
        file_name = update.message.document.file_name.lower() if update.message.document.file_name else ""
        
        # Проверяем MIME-тип или расширение файла
        if mime_type in ("text/plain", "application/pdf") or file_name.endswith((".txt", ".pdf")):
            return await handle_documentgpt(update, context)      
    if update.message.audio or update.message.voice:
        return await handle_audio(update, context)
    if update.message.animation:  # Проверка на GIF
        return await handle_gptgif(update, context)
    if update.message.video or update.message.document and update.message.document.mime_type.startswith("video"):
        return await handle_gptvideo(update, context)
    # Проверка, отправил ли пользователь изображение
    if update.message.photo:
        user_id = update.message.from_user.id
        user_message = update.message.caption or "Распознай что на изображении"
    
        waiting_message = await update.message.reply_text("Распознаю изображение...")
    
        async def process_photo():
            try:
                # Сохраняем изображение локально
                original_photo = await update.message.photo[-1].get_file()
                file = await context.bot.get_file(original_photo.file_id)
                os.makedirs("downloads", exist_ok=True)
                image_path = f"downloads/image_{original_photo.file_id}.jpg"
                await file.download_to_drive(image_path)
    
                # Проверяем, начинается ли caption с "Дорисуй:" и т.п.
                match = re.match(r"(?i)^(дорисуй|доделай|замени|добавь|отредактируй):?\s*(.+)", user_message)
                if match:
                    inpaint_prompt = match.group(2).strip()
                    logging.info(f"inpaint_prompt: {inpaint_prompt}")
    
                    # Загружаем изображение в память
                    photo_file = await update.message.photo[-1].get_file()
                    img_data = io.BytesIO()
                    await photo_file.download_to_memory(out=img_data)
    
                    # Определяем путь к папке temp внутри директории бота
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    temp_dir = os.path.join(base_dir, "temp")
                    os.makedirs(temp_dir, exist_ok=True)
    
                    temp_image_path = os.path.join(temp_dir, f"inpaint_{user_id}.jpg")
                    with open(temp_image_path, "wb") as f:
                        f.write(img_data.getvalue())
    
                    # Передаём в обработку
                    return await inpaint_image(update, context, temp_image_path, inpaint_prompt)
    
                # --- Обычная генерация описания ---
                response_text = await generate_image_description(user_id, image_path=image_path, query=user_message)
                add_to_context(user_id, f"[Изображение], с подписью: {user_message}", message_type="user_send_image")
                logging.info(f"Ответ с изображением: {response_text}")
    
                if response_text:
                    text_parts = await send_reply_with_limit(response_text)
    
                    if len(text_parts) == 1:
                        await waiting_message.edit_text(
                            text_parts[0],
                            parse_mode='MarkdownV2',
                            reply_markup=collapsed_menu
                        )
                    else:
                        # первую часть заменяем "ожидание"
                        await waiting_message.edit_text(text_parts[0], parse_mode='MarkdownV2')
                        # остальные части — новыми сообщениями
                        for i, part in enumerate(text_parts[1:], start=1):
                            is_last = (i == len(text_parts) - 1)
                            await update.message.reply_text(
                                part,
                                parse_mode='MarkdownV2',
                                reply_markup=collapsed_menu if is_last else None
                            )
    
                    add_to_context(user_id, response_text, message_type="bot_image_response")
                    save_context_to_firebase(user_id)
                else:
                    await waiting_message.edit_text("Произошла ошибка при генерации ответа. Попробуйте снова. /restart")
    
            except Exception as e:
                logging.error(f"Ошибка при обработке изображения: {e}")
                await waiting_message.edit_text("Ошибка при обработке изображения. Попробуйте снова. /restart")
    
        asyncio.create_task(process_photo())
        return

    else:
        user_id = update.message.from_user.id
        user_message = update.message.text          
        # Обработка текстового запроса без изображения
        draw_triggers = ["нарисуй", "нарисуй:", "Нарисуй", "Нарисуй:", "draw", "draw:", "Draw", "Draw:"]

        if any(user_message.startswith(trigger) for trigger in draw_triggers):
            prompt_text = user_message.split(maxsplit=1)[1] if len(user_message.split()) > 1 else ""

            if not prompt_text:
                await update.message.reply_text("Пожалуйста, укажите описание для генерации изображения после слова 'нарисуй'.")
                return RUNNING_GPT_MODE

            # Запускаем асинхронную генерацию без перевода
            return await limited_image_generation(update, context, user_id, prompt_text)

        else:
            waiting_message = await update.message.reply_text("Думаю над ответом, пожалуйста, подождите...")

            async def process():
                try:
                    response_text = await generate_gemini_response(user_id, query=user_message)
                    add_to_context(user_id, user_message, message_type="user_send_text")

                    if response_text:
                        text_parts = await send_reply_with_limit(response_text)

                        if len(text_parts) == 1:
                            # Только одно сообщение — добавим кнопки сразу
                            await waiting_message.edit_text(
                                text_parts[0],
                                parse_mode='MarkdownV2',
                                reply_markup=collapsed_menu
                            )
                        else:
                            # Много частей — первая без кнопок
                            await waiting_message.edit_text(text_parts[0], parse_mode='MarkdownV2')

                            for i, part in enumerate(text_parts[1:], start=1):
                                is_last = (i == len(text_parts) - 1)
                                await update.message.reply_text(
                                    part,
                                    parse_mode='MarkdownV2',
                                    reply_markup=collapsed_menu if is_last else None
                                )
                        add_to_context(user_id, response_text, message_type="bot_text_response")
                        save_context_to_firebase(user_id)
                    else:
                        await waiting_message.edit_text("Произошла ошибка при генерации ответа. Попробуйте снова. /restart")

                except Exception as e:
                    await waiting_message.edit_text(f"Ошибка: {e}")

            asyncio.create_task(process())

        return RUNNING_GPT_MODE

async def inpaint_image(update: Update, context: CallbackContext, image_path: str, prompt: str):
    """Генерация измененного изображения через Google Imagen."""
    user_id = update.effective_user.id

    # Фоновая загрузка исходного изображения
    asyncio.create_task(download_and_upload_image(image_path))

    # Отправляем сообщение о начале обработки
    msg = await update.message.reply_text("⏳ Ожидайте, изображение принято...")

    # Переводим промпт
    translated_prompt = await translate_promt_with_gemini(user_id, query=prompt)

    # Обновляем сообщение с уточнением
    await msg.edit_text(
        f"⏳ Ожидайте, изображение изменяется по запросу: {translated_prompt}\n\n"
        "Если бот неправильно автоматически перевёл ваш запрос, то напишите его изначально на английском, "
        "в таком случае запрос просто перенесётся в конечный результат."
    )

    # Генерируем измененное изображение
    captions, image_urls = await generate_inpaint_gemini(image_path, translated_prompt)

    if not image_urls:
        await msg.edit_text(
            "⚠️ Не удалось изменить изображение. Попробуйте переформулировать запрос иначе.\n\n"
            "⚠️ Либо же запрос подвергся цензуре."
        )
        return

    # Фоновая загрузка изображений на Catbox
    for image_url in image_urls:
        asyncio.create_task(download_and_upload_image(image_url))

    # Формируем подпись
    caption_text = f"Модель: <b>Imagen3</b>\n\n"
    for i, caption in enumerate(captions):
        caption_text += f"<b>Изображение {i+1}:</b>\n<blockquote expandable>{caption}</blockquote>\n\n"

    caption_text += f"Ваш запрос:\n<code>{prompt}</code>\n\n"
    caption_text += f"Конечный запрос:\n<code>Дорисуй {translated_prompt}</code>"

    # Ограничение на подпись в Telegram (1024 символа)
    MAX_CAPTION_LENGTH = 1000
    MAX_MESSAGE_LENGTH = 4000

    # Разделяем текст на части, чтобы не превышать лимит
    caption_part, message_parts = split_html_text(caption_text, MAX_CAPTION_LENGTH, MAX_MESSAGE_LENGTH)

    # Проверяем количество изображений
    if len(image_urls) == 1:
        # Случай с одним изображением
        image_path = image_urls[0]
        with open(image_path, "rb") as img:
            if len(caption_text) <= MAX_CAPTION_LENGTH:
                # Если длина подписи не превышает лимит, отправляем фото с подписью и клавиатурой
                sent_message = await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=img,
                    caption=caption_part,
                    parse_mode="HTML"
                )
                # Создаём клавиатуру
                keyboard = [
                    [InlineKeyboardButton("📒 Сохранить чтобы не потерять", callback_data=f"save_{user_id}_{sent_message.message_id}")],
                    [InlineKeyboardButton("🗂 Мои сохранённые генерации", callback_data="scheduled_by_tag")],
                    [InlineKeyboardButton("🌃 Опубликовать в общую папку", callback_data=f"neuralpublic_{user_id}_{sent_message.message_id}")],
                    [InlineKeyboardButton("🏙 Посмотреть чужие публикации", callback_data="view_shared")],
                    [InlineKeyboardButton("🖼 Сменить модель", callback_data='choose_modele')],
                    [InlineKeyboardButton("🎨 Выбрать стиль", callback_data='choose_preset')],
                    [InlineKeyboardButton("🌌 В главное меню 🌌", callback_data='restart')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                # Прикрепляем клавиатуру к отправленному сообщению
                await context.bot.edit_message_reply_markup(
                    chat_id=update.effective_chat.id,
                    message_id=sent_message.message_id,
                    reply_markup=reply_markup
                )
            else:
                # Если длина подписи превышает лимит, отправляем фото с первой частью подписи без клавиатуры
                sent_message = await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=img,
                    caption=caption_part,
                    parse_mode="HTML"
                )
                # Отправляем оставшиеся части подписи
                last_caption_message_id = None
                for part in message_parts:
                    sent_message = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=part,
                        parse_mode="HTML"
                    )
                    last_caption_message_id = sent_message.message_id

                # Создаём клавиатуру
                keyboard = [
                    [InlineKeyboardButton("📒 Сохранить чтобы не потерять", callback_data=f"save_{user_id}_{sent_message.message_id}")],
                    [InlineKeyboardButton("🗂 Мои сохранённые генерации", callback_data="scheduled_by_tag")],
                    [InlineKeyboardButton("🌃 Опубликовать в общую папку", callback_data=f"neuralpublic_{user_id}_{sent_message.message_id}")],
                    [InlineKeyboardButton("🏙 Посмотреть чужие публикации", callback_data="view_shared")],
                    [InlineKeyboardButton("🖼 Сменить модель", callback_data='choose_modele')],
                    [InlineKeyboardButton("🎨 Выбрать стиль", callback_data='choose_preset')],
                    [InlineKeyboardButton("🌌 В главное меню 🌌", callback_data='restart')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                # Прикрепляем клавиатуру к последнему сообщению с текстом
                target_message_id = last_caption_message_id if last_caption_message_id else sent_message.message_id
                await context.bot.edit_message_reply_markup(
                    chat_id=update.effective_chat.id,
                    message_id=target_message_id,
                    reply_markup=reply_markup
                )
    else:
        # Случай с медиагруппой (несколько изображений)
        media_group = []
        for image_path in image_urls:
            with open(image_path, "rb") as img:
                # Добавляем изображения в медиагруппу без подписи
                media_group.append(InputMediaPhoto(img))

        # Отправляем медиагруппу без подписи
        sent_messages = await context.bot.send_media_group(
            chat_id=update.effective_chat.id,
            media=media_group
        )

        # Получаем ID первого сообщения медиагруппы
        first_media_message_id = sent_messages[0].message_id

        # Отправляем части подписи как отдельные сообщения
        last_caption_message_id = None
        for part in [caption_part] + message_parts:
            sent_message = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=part,
                parse_mode="HTML"
            )
            last_caption_message_id = sent_message.message_id

        # Создаём клавиатуру
        keyboard = [
            [InlineKeyboardButton("📒 Сохранить чтобы не потерять", callback_data=f"save_{user_id}_{sent_message.message_id}")],
            [InlineKeyboardButton("🗂 Мои сохранённые генерации", callback_data="scheduled_by_tag")],
            [InlineKeyboardButton("🌃 Опубликовать в общую папку", callback_data=f"neuralpublic_{user_id}_{sent_message.message_id}")],
            [InlineKeyboardButton("🏙 Посмотреть чужие публикации", callback_data="view_shared")],
            [InlineKeyboardButton("🖼 Сменить модель", callback_data='choose_modele')],
            [InlineKeyboardButton("🎨 Выбрать стиль", callback_data='choose_preset')],
            [InlineKeyboardButton("🌌 В главное меню 🌌", callback_data='restart')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Определяем, к какому сообщению прикрепить клавиатуру
        target_message_id = last_caption_message_id if last_caption_message_id else first_media_message_id

        # Прикрепляем клавиатуру к целевому сообщению
        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=target_message_id,
            reply_markup=reply_markup
        )










MODELS = {
    # FLUX Models (Negative prompt обычно не нужен)
    "black-forest-labs/FLUX.1-dev": {
        "add_prompt": "",
        "negative": False
    },
    "black-forest-labs/FLUX.1-schnell": {
        "add_prompt": "",
        "negative": False
    },
    # SD Models (Negative prompt нужен)
    "stabilityai/stable-diffusion-xl-base-1.0": {
        "add_prompt": "",
        "negative": True
    },
    "stabilityai/stable-diffusion-3-medium-diffusers": {
        "add_prompt": "",
        "negative": True
    },
    # Google (Твой Imagen 3)
    "imagen3": {
        "add_prompt": "Generate ",
        "negative": False
    }
}

MODEL_SHORTNAMES = {
    "black-forest-labs/FLUX.1-dev": "🌃 FLUX.1 Dev",
    "black-forest-labs/FLUX.1-schnell": "🚀 FLUX.1 Schnell",
    "stabilityai/stable-diffusion-xl-base-1.0": "💠 SDXL Base 1.0",
    "stabilityai/stable-diffusion-3-medium-diffusers": "🎨 SD3 Medium",
    "imagen3": "🧠 Google Imagen 3"
}

# --- ФУНКЦИИ ---

# 1. Единое меню выбора модели
async def choose_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Получаем текущую модель (функция get_user_model должна быть у тебя в коде базы данных)
    user_model = get_user_model(user_id) 
    
    # Если модель не найдена в списке (например, старая удаленная), ставим дефолтную
    if user_model not in MODELS:
        user_model = "black-forest-labs/FLUX.1-dev"

    keyboard = []
    row = []
    
    for model_key, params in MODELS.items():
        name = MODEL_SHORTNAMES.get(model_key, model_key)
        
        if model_key == user_model:
            name = f"{name} ✅"
    
        row.append(InlineKeyboardButton(name, callback_data=f"set_model|{model_key}"))
    
        # когда набралось 2 — кидаем строку в клавиатуру и очищаем
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    # если моделей нечётное количество — добавляем остаток
    if row:
        keyboard.append(row)

    # Добавляем служебные кнопки
    keyboard.append([InlineKeyboardButton("━━━━━━━━━━ ✦ ━━━━━━━━━━", callback_data="none")])
    keyboard.append([InlineKeyboardButton("🎨 Выбрать стиль (Preset)", callback_data='choose_preset')])
    keyboard.append([InlineKeyboardButton("📗 Помощь", callback_data='short_help_gpt')])    
    keyboard.append([InlineKeyboardButton("❌ Закрыть меню", callback_data="cancelmodel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "⚙️ <b>Настройки генерации</b>\n\n"
        "В связи с изменениями на HuggingFace, список бесплатных моделей обновлен.\n\n"
        "🌃 <b>FLUX</b> — Отличное качество, следует промпту. <i>(Dev — качественнее, Schnell — быстрее)</i>\n"
        "💠 <b>SDXL / SD3</b> — Классические модели Stable Diffusion.\n"
        "🧠 <b>Google Imagen</b> — Работает отдельно, понимает сложные запросы, умеет дорисовывать.\n\n"
        "Вы можете менять соотношение сторон генерации и немного настравиать её, в частности указывать seed чтобы зафиксировать одну генерацию и изменять её, подробнее читайте по кнопке помощь\n\n"        
        f"📌 Текущая модель: <b>{MODEL_SHORTNAMES.get(user_model, user_model)}</b>"
    )

    if update.callback_query:
        # Если это клик по кнопке — редактируем сообщение
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    else:
        # Если это новая команда — отправляем новое сообщение
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")


# 2. Обработчик нажатия на модель
async def model_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Парсим callback_data "set_model|model_name"
    _, selected_model = query.data.split('|', 1)
    user_id = query.from_user.id
    
    # Сохраняем в БД (твоя функция)
    set_user_model(user_id, selected_model)
    
    # Обновляем user_data для текущей сессии
    context.user_data['selected_model'] = {
        'name': selected_model,
        'params': MODELS[selected_model]
    }

    # Если выбрали Imagen, можно отправить доп. инструкцию (как у тебя было)
    if selected_model == "imagen3":
         await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="✅ Выбрана модель: <b>Google Imagen 3</b>\n\nИспользуйте <code>Нарисуй</code> для генерации или <code>Дорисуй</code> для редактирования фото.",
            parse_mode="HTML"
        )
    
    # Просто обновляем меню, чтобы переставить галочку
    await choose_style(update, context)


# 3. Поиск параметров (упрощенная версия)
def find_model_params(model_name: str) -> dict:
    """Ищет параметры модели в плоском словаре MODELS."""
    return MODELS.get(model_name, MODELS["black-forest-labs/FLUX.1-dev"])








# Обработчик выбора Imagen 3
async def select_imagen3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    # Устанавливаем модель Imagen 3
    set_user_model(user_id, "imagen3")

    # Обновляем интерфейс выбора модели
    await choose_style(update, context)
    context.user_data['selected_model'] = {
        'name': "imagen3",
        'params': "imagen3"
    }
    # Отправляем подтверждающее сообщение
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Выбрана модель: Google Imagen 3\n\nЭта модель умеет генерировать сопутствующий текст к изображениям, если дать ей такую задачу в запросе. А так же переделывать ваши изображения. Например пытаться дорисовать, раскрасить набросок, что-то добавить на фото, расширить фото в какую-то из сторон, изменить время суток на фото и что угодно ещё. \n\nДля того чтобы сгенерировать изображение начните сообщение со слово <code>Нарисуй</code> и затем ваш запрос. Чтобы переделать ваше изображение, отправьте его боту с подписью которая начинается с <code>Дорисуй</code> и затем напишите что именно вы хотите. \n\nТак же эта модельона умеет генерировать по несколько изображений за раз. Для этого явно укажите такое задание в запросе, например:\n<pre>Нарисуй покажи шаг за шагом в 4 изображения как нарисовать сову от наброска и до финальной иллюстрации</pre>\n Слова <code>Дорисуй</code> и <code>Нарисуй</code> это триггеры запускающие один из вариантов кода, поэтому они всегда должны быть в начале. Затем может следовать любой запрос.",
        parse_mode="HTML"
    )
    await query.answer()

# Обработчик кнопки "Выбрать стиль"
async def select_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await choose_style(update, context)



async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.delete()
    
    # Вызов run_gpt после удаления сообщения
    await run_gpt(update, context)





async def token_set(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите токены через запятую.")
        return

    new_tokens = {token.strip() for token in ' '.join(context.args).split(',')}
    
    try:
        ref_tokens = db.reference('Tokens/All_tokens')
        existing_tokens = ref_tokens.get() or []  # Загружаем текущие токены
        existing_tokens = set(existing_tokens)  # Преобразуем в множество для исключения дубликатов

        updated_tokens = existing_tokens | new_tokens  # Добавляем новые токены

        ref_tokens.set(list(updated_tokens))  # Сохраняем в Firebase
        logging.info("Обновлены API-ключи в Firebase")
        await update.message.reply_text("API-ключи успешно добавлены в Firebase.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении токенов в Firebase: {e}")
        await update.message.reply_text("Ошибка при сохранении токенов. Проверьте логи.")

image_queue = asyncio.Queue()
user_positions = {}
global_semaphore = asyncio.Semaphore(4)

async def limited_image_generation(update, context, user_id, prompt):
    """Добавляем задачи в очередь и корректно определяем позицию"""
    # Проверяем текущий размер очереди
    position = image_queue.qsize()

    if position > 0:  # Если в очереди уже есть задачи, выдаем позицию
        user_positions[user_id] = position + 1
        await update.message.reply_text(f"Очередь на генерацию: {position + 1}-й в списке. Ожидайте...")
    else:  # Если очередь пуста, пользователь будет первым, но не показываем лишний текст
        user_positions[user_id] = 1

    # Добавляем задачу в очередь
    await image_queue.put((update, context, user_id, prompt))

    # Запускаем обработку очереди, если не запущена
    asyncio.create_task(process_queue())
async def process_queue():
    """Фоновая задача для обработки очереди"""
    while True:
        async with global_semaphore:
            # Достаем задачу из очереди
            next_task = await image_queue.get()
            update, context, user_id, prompt = next_task
            
            try:
                await generate_image(update, context, user_id, prompt)
            except Exception as e:
                logger.error(f"Ошибка генерации: {e}")
                await update.message.reply_text("⚠️ Ошибка при обработке вашего запроса")
            
            # Обновляем позиции в очереди
            for uid in user_positions:
                if user_positions[uid] > user_positions.get(user_id, 0):
                    user_positions[uid] -= 1
            if user_id in user_positions:
                del user_positions[user_id]     


PRESET_PROMPTS = {
    "Нет": "",    

    "Аниме": "anime style, vibrant and dynamic, highly detailed, expressive characters, cinematic lighting, vivid color palette",

    "Ghibli": "Ghibli art style, realistic anime style, soft and painterly, warm and nostalgic atmosphere, 90s anime, magical realism, expressive characters, rich natural environments, detailed rich studio ghibli style backgrounds, studio ghibli style characters",

    "Манга": "manga style, black and white, detailed linework, expressive characters, dramatic panel composition",

    "Импрессионизм": "impressionism, loose brushstrokes, dreamlike quality, soft focus, atmospheric perspective, emotional composition",

    "Цифровой арт": "digital painting, ultra-detailed, smooth gradients, vibrant and expressive colors, professional concept art style",

    "Масляная живопись": "oil painting, rich texture, visible brush strokes, deep colors, classical artistic composition, museum-quality artwork",

    "Акварельный рисунок": "watercolor painting, soft and fluid brush strokes, delicate color blending, translucent layers, dreamy and atmospheric style",

    "Фэнтези": "fantasy art, epic composition, mystical atmosphere, intricate details, magical creatures, enchanted landscapes, cinematic lighting",

    "Тёмное фэнтези": "dark fantasy, gothic aesthetic, eerie atmosphere, dramatic lighting, ancient ruins, sinister creatures, detailed and moody color palette",

    "Минимализм": "minimalism, clean and simple, harmonious composition, delicate ink lines, limited color palette, serene and elegant aesthetic",

    "Набросок": "sketch drawing, raw and expressive, loose lines, monochrome or minimal color, detailed anatomy and structure, hand-drawn feel",

    "Пиксель-арт": "pixel art, retro 8-bit or 16-bit style, vibrant color palette, detailed shading, nostalgic video game aesthetic, crisp pixel details",

    "3D модель": "3D render, high-poly model, ultra-realistic textures, cinematic lighting, professional CG rendering, physically accurate materials",

    "Корейский стиль": "Korean contemporary painting, minimalisit clean colors, limited color palette, emotional depth, traditional meets modern aesthetics",

    "Киберпанк": "cyberpunk style, neon-drenched cityscapes, high-tech low-life, futuristic atmosphere, rain-soaked streets, glowing holograms, high contrast lighting",

    "Реализм": "realistic painting, ultra-detailed, masterful brushwork, natural lighting, expressive realism, high-resolution textures",

    "Генерация фотографии": "photo-realistic generation, ultra-high resolution, natural colors, perfect depth of field, cinematic lighting, hyper-detailed textures",

    "Художественное фото": "artistic photography, dramatic composition, rich color grading, play of light and shadow, cinematic feel, emotionally captivating",

    "Старинные фото": "vintage photography, sepia or black and white, grainy texture, historical aesthetic, aged film look, authentic old-time feel"
}



async def generate_image(update, context, user_id, prompt, query_message=None):
    """Генерация изображения с учетом выбранной модели"""
    # Получаем модель из контекста или Firebase
    selected_model = context.user_data.get('selected_model')
    logger.info(f"selected_model: {selected_model}")    
    global LAST_SUCCESSFUL_TOKEN
    if not selected_model:
        model_name = get_user_model(user_id)
        model_params = find_model_params(model_name)
        selected_model = {
            'name': model_name,
            'params': model_params
        }
        context.user_data['selected_model'] = selected_model

    model_name = selected_model['name']
    model_params = selected_model['params']
    if model_name == "glif-loradex-trainer/araminta":
        model_name = "glif-loradex-trainer/araminta_k_flux_dev_illustration_art"
    if model_name == "imagen3":
        return await google_imagen(update, context, prompt, user_id)
    # Загружаем токены из Firebase
    all_tokens = get_all_tokens()
    last_token = get_last_successful_token()

    if not all_tokens:
        logger.error("Нет доступных API-ключей для Hugging Face")
        await update.message.reply_text("Ошибка: нет доступных API-ключей. Попробуйте позже.")
        return None

    # Определяем порядок токенов: сначала последний успешный, затем остальные
    if last_token and last_token in all_tokens:
        token_order = [last_token] + [key for key in all_tokens if key != last_token]
    else:
        token_order = all_tokens


    # Определяем, куда отправить сообщение
    response_target = update.message if update.message else query_message

    if response_target:
        await response_target.reply_text(f"Ожидайте, генерирую изображение по запросу: '{prompt}'...")

    # Получаем add_prompt для выбранной модели
    original_prompt = prompt
    logger.info(f"original_prompt: {original_prompt}")
    add_prompt = selected_model['params']['add_prompt']

    retries = len(token_order)  # Количество попыток = количеству токенов
    retry_message = None  # Глобальная переменная для хранения сообщения

    for i, HF_API_KEY in enumerate(token_order):
        logger.info(f"Пробуем API-ключ {i+1}/{len(token_order)}: {HF_API_KEY}")
        client_image = AsyncInferenceClient(provider="auto", api_key=HF_API_KEY, timeout=300)

        try:
            start_time = time.time()  # Фиксируем начальное время
            prompt = original_prompt  
            # Инициализация параметров по умолчанию
            seed = random.randint(1, 2000000000)  # Генерация случайного seed
            guidance_scale = None
            num_inference_steps = None
            width, height = 1024, 1024  # Значения по умолчанию

            # Парсинг seed из начала текста
            seed_match = re.match(r"^(\d+),", prompt)
            if seed_match:
                seed = int(seed_match.group(1))
                prompt = re.sub(r"^\d+,", "", prompt).strip()

            # Парсинг соотношения сторон из квадратных скобок
            aspect_ratio_match = re.search(r"\[(\d+):(\d+)\]$", prompt)
            if aspect_ratio_match:
                aspect_width = int(aspect_ratio_match.group(1))
                aspect_height = int(aspect_ratio_match.group(2))
                prompt = re.sub(r"\[\d+:\d+\]$", "", prompt).strip()

                # Вычисление ширины и высоты, учитывая ограничения
                if aspect_width >= aspect_height:
                    width = min(1400, max(512, int(1400 * (aspect_width / aspect_height))))
                    height = min(1400, max(512, int(width * (aspect_height / aspect_width))))
                else:
                    height = min(1400, max(512, int(1400 * (aspect_height / aspect_width))))
                    width = min(1400, max(512, int(height * (aspect_width / aspect_height))))

            # Теперь парсим guidance_scale и num_inference_steps
            params_match = re.search(r"\((\d+(\.\d+)?)(?:,\s*(\d+))?\)", prompt)
            if params_match:
                guidance_scale = float(params_match.group(1))  # Всегда будет найдено
                num_inference_steps = int(params_match.group(3)) if params_match.group(3) else None  # Проверяем наличие второго числа
                prompt = re.sub(r"\([\d\.]+(?:,\s*\d+)?\)$", "", prompt).strip()

            # Очистка промта от всех парсинговых значений
            clean_prompt = prompt.strip()

            # Формирование full_prompt на основе очищенного промта и add_prompt
            # Получаем пресет из Firebase
            preset_name = get_user_preset(user_id)
            preset_prompt = PRESET_PROMPTS.get(preset_name, "")

            # Формируем mix_prompt с учетом пресета
            mix_prompt = f"{add_prompt} {clean_prompt} {preset_prompt}"

            full_prompt = await translate_promt_with_gemini(user_id, query=mix_prompt)
            logger.info(f"full_prompt: {full_prompt}")

            # Коррекция размеров кратно 64
            width = max(512, min(1408, width - (width % 64)))
            height = max(512, min(1408, height - (height % 64)))
            # **Заданный negative_prompt для большинства изображений**
            negative_prompt = (
                "blurry, distorted, deformed, bad anatomy, bad proportions, extra limbs, "
                "missing fingers, too many fingers, malformed hands, long neck, watermark, "
                "low quality, low resolution, grainy, unnatural lighting, bad perspective, "
                "mutated body, disproportional, extra heads, floating limbs, extra eyes, "
                "bad composition, broken symmetry, duplicate elements, jpeg artifacts"
                if selected_model['params']['negative']
                else None
            )

            logger.info(f"width: {width}")
            logger.info(f"height: {height}")
            # Параметры для генерации изображения
            params = {
                "height": height,
                "width": width,
                "seed": seed,
                #"max_sequence_length": 512,
            }
            if selected_model['params']['negative']:
                params["negative_prompt"] = negative_prompt
            # Добавляем guidance_scale, если он указан
            if "guidance_scale" in locals():
                params["guidance_scale"] = guidance_scale

            # Добавляем num_inference_steps, если он указан
            if "num_inference_steps" in locals():
                params["num_inference_steps"] = num_inference_steps

            # Генерация изображения
            image = await client_image.text_to_image(full_prompt, model=model_name, **params)
            logger.info(f"prompt на генерацию: {full_prompt}")
            elapsed_time = time.time() - start_time  # Вычисляем прошедшее время

            MAX_CAPTION_LENGTH = 1024  # Максимальная длина caption в Telegram

            caption = (
                f"`Нарисуй: {original_prompt}`\n\n"
                f"Seed: `{seed}, `\n"
                + (f"Guidance Scale: {guidance_scale}\n" if guidance_scale is not None else "")
                + (f"Steps: {num_inference_steps}\n" if num_inference_steps is not None else "")
                + f"Resolution: {width}x{height}\n"
                f"Время генерации: {elapsed_time:.2f} сек.\n\n"
                f"Модель: `{model_name}`\n"                
                f"Переведённый prompt: \n```\nНарисуй: {full_prompt}```\n"
            )

            with io.BytesIO() as output:
                image.save(output, format="PNG")
                output.seek(0)

                # Загружаем изображение на Catbox (если нужно)
                catbox_url = await upload_image_to_catbox_in_background(output.getvalue())

                # Определяем источник запроса
                message = update.message if update.message else update.callback_query.message
                user_id = update.effective_user.id  # Получаем user_id

                # Создаем клавиатуру с кнопками
                keyboard = [
                    [InlineKeyboardButton("📒 Сохранить чтобы не потерять", callback_data=f"save_{user_id}_{message.message_id}")],                                    
                    [InlineKeyboardButton("🗂 Мои сохранённые генерации", callback_data="scheduled_by_tag")],
                    [InlineKeyboardButton("🌃 Опубликовать в общую папку", callback_data=f"neuralpublic_{user_id}_{message.message_id}")],    
                    [InlineKeyboardButton("🏙 Посмотреть чужие публикации", callback_data="view_shared")],                                        
                    [InlineKeyboardButton("🖼 Сменить модель", callback_data='choose_modele')],
                    [InlineKeyboardButton("🎨 Выбрать стиль", callback_data='choose_preset')], 
                    [InlineKeyboardButton("🔄 Повторить генерацию", callback_data=f"regenerate_{user_id}_{message.message_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                # Проверяем длину caption
                if len(caption) > MAX_CAPTION_LENGTH:
                    sent_message = await message.reply_photo(photo=output)

                    # Сохраняем информацию о первом сообщении (с фото)
                    context.user_data[f"split_message_{user_id}_{sent_message.message_id}"] = {
                        "full_caption": caption,
                        "file_id": sent_message.photo[-1].file_id,
                    }
                    keyboard[0][0] = InlineKeyboardButton(
                        "📒 Сохранить чтобы не потерять",
                        callback_data=f"save_{user_id}_{sent_message.message_id}"
                    )
                    # Обновляем callback_data для кнопки публикации
                    keyboard[2][0] = InlineKeyboardButton(
                        "🌃 Опубликовать в общую папку",
                        callback_data=f"neuralpublic_{user_id}_{sent_message.message_id}"
                    )

                    # Отправляем caption отдельно, но уже в формате HTML
                    await message.reply_text(
                        text=escape_gpt_markdown_v2(caption),
                        parse_mode="MarkdownV2",  # Меняем MarkdownV2 → HTML
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    # Если caption влезает, отправляем обычным способом
                    sent_message = await message.reply_photo(
                        photo=output,
                        caption=escape_gpt_markdown_v2(caption),
                        parse_mode="MarkdownV2",
                        reply_markup=reply_markup
                    )      
                    logger.info(f"caption1 {caption} ")                             
            # Запоминаем успешный токен
            set_last_successful_token(HF_API_KEY)
            logger.info(f"Успешный токен: {HF_API_KEY}")
            
            # Тут настройки полученного сообщения
            return image  # Возвращаем изображение, если успешно


        except Exception as e:
            logger.error(f"Ошибка с токеном {HF_API_KEY}: {e}")
            retries -= 1

            if retries > 0:
                try:
                    if retry_message is None:  # Создаём сообщение только один раз
                        retry_message = await response_target.reply_text(
                            f"⏳ Возникла ошибка. Пробуем другой токен ({i+2}/{len(token_order)}), подождите..."
                        )
                    else:  # Редактируем предыдущее сообщение
                        await retry_message.edit_text(
                            f"⏳ Возникла ошибка. Пробуем другой токен ({i+2}/{len(token_order)}), немного терпения..."
                        )

                except Exception as edit_error:
                    logger.warning(f"Не удалось обновить сообщение: {edit_error}")
                await asyncio.sleep(2)

            else:
                try:
                    await retry_message.reply_text(
                        "Произошла ошибка при генерации изображения. Попробуйте:\n\n"
                        "1) Сменить модель (стиль), возможно, проблема в ней.\n"
                        "2) Подождать несколько часов — может быть, проблемы с серверами.\n"
                        "3) Если ничего не помогло, сообщите о проблеме через /send, скорее всего исчерпан лимит всех токенов.\n\n"
                        "При желании вы можете получить свои токены и добавить их в бот. \n"
                        'Для прочтения инструкции о том как это сделать, <a href="https://telegra.ph/Dobavlenie-tokena-generacii-03-21">перейдите по ссылке</a>.\n '
                        "Один токен получается примерно за 2 минуты и добавляет 20 генераций в месяц в бот.\n\n"
                        "Так же вы можете выбрать модель Imagen 3, она скорее всего работает.",
                        parse_mode="HTML",
                        disable_web_page_preview=True
                    )
                except Exception as edit_error:
                    logger.warning(f"Не удалось обновить сообщение с ошибкой: {edit_error}")
                return None


async def google_imagen(update, context, prompt, user_id):
    """Генерация изображения через Google Imagen."""
    msg = await update.message.reply_text("⏳ Ожидайте, изображение генерируется...")

    # Переводим промт
    full_prompt = await translate_promt_with_gemini(update.effective_user.id, query=prompt)

    # Обновляем сообщение с уточнением
    await msg.edit_text(f"⏳ Ожидайте, изображение генерируется по запросу: {full_prompt}\n\n Если бот неправильно автоматически перевёл ваш запрос, то напишите его изначально на английском, в таком случае запрос просто перенесётся в конечный результат")

    # Добавляем "Generate " в начало промта
    full_prompt = "Generate image of " + full_prompt
    # Получаем пресет из Firebase
    preset_name = get_user_preset(user_id)
    preset_prompt = PRESET_PROMPTS.get(preset_name, "")

    # Формируем mix_prompt с учетом пресета
    mix_prompt = f"{full_prompt} {preset_prompt}"
    # Генерируем изображение
    captions, image_urls = await Generate_gemini_image(mix_prompt)
    if not image_urls:
        keyboard = [
            [InlineKeyboardButton("🖼 Сменить модель", callback_data='choose_modele')],
            [InlineKeyboardButton("🎨 Выбрать стиль", callback_data='choose_preset')],
            [InlineKeyboardButton("🌌 В главное меню 🌌", callback_data='restart')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await msg.edit_text(
            f"⚠️ Не удалось сгенерировать изображение по запросу {full_prompt}\n\n"
            "⚠️ Попробуйте сформулировать запрос иначе. Гугл часто блокирует запросы всего, что может быть потенциально спорным. "
            "Попробуйте разные варианты или проверьте работоспособность модели через максимально нейтральный запрос, например:\n<pre>Нарисуй Draw cat on apple tree</pre>\n. Если бот неправильно автоматически перевёл ваш запрос, "
            "то напишите его изначально на английском, в таком случае запрос просто перенесётся в конечный результат.",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        return

    # Фоновая загрузка изображений на Catbox
    for image_url in image_urls:
        asyncio.create_task(download_and_upload_image(image_url))
    logger.info(f"image_urls: {image_urls}") 

    caption_text = f"Модель: <b>Imagen3</b>\nПресет: {preset_name}\n\n"
    for i, caption in enumerate(captions):
        caption_text += f"<b>Изображение {i+1}:</b>\n<blockquote expandable>{caption}</blockquote>\n\n"


    caption_text += f"Ваш запрос:\n<code>Нарисуй {prompt}</code>\n\n"
    caption_text += f"Конечный запрос:\n<code>{mix_prompt}</code>"

    # Ограничение на подпись в Telegram (1024 символа)
    MAX_CAPTION_LENGTH = 1000 
    MAX_MESSAGE_LENGTH = 4000 

    # Разделяем текст на части, чтобы не превышать лимит
    caption_part, message_parts = split_html_text(caption_text, MAX_CAPTION_LENGTH, MAX_MESSAGE_LENGTH)
    logger.info(f"caption_part {caption_part}")    
    for idx, part in enumerate(message_parts):
        logger.info(f"message_parts {idx}: {part}")




    # Проверяем количество изображений
    if len(image_urls) == 1:
        # Случай с одним изображением
        image_path = image_urls[0]
        with open(image_path, "rb") as img:
            if len(caption_text) <= MAX_CAPTION_LENGTH:
                # Если длина подписи не превышает лимит, отправляем фото с подписью и клавиатурой
                sent_message = await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=img,
                    caption=caption_part,
                    parse_mode="HTML"
                )
                # Создаём клавиатуру
                keyboard = [
                    [InlineKeyboardButton("📒 Сохранить чтобы не потерять", callback_data=f"save_{user_id}_{sent_message.message_id}")],
                    [InlineKeyboardButton("🗂 Мои сохранённые генерации", callback_data="scheduled_by_tag")],
                    [InlineKeyboardButton("🌃 Опубликовать в общую папку", callback_data=f"neuralpublic_{user_id}_{sent_message.message_id}")],
                    [InlineKeyboardButton("🏙 Посмотреть чужие публикации", callback_data="view_shared")],
                    [InlineKeyboardButton("🖼 Сменить модель", callback_data='choose_modele')],
                    [InlineKeyboardButton("🎨 Выбрать стиль", callback_data='choose_preset')],
                    [InlineKeyboardButton("🌌 В главное меню 🌌", callback_data='restart')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                # Прикрепляем клавиатуру к отправленному сообщению
                await context.bot.edit_message_reply_markup(
                    chat_id=update.effective_chat.id,
                    message_id=sent_message.message_id,
                    reply_markup=reply_markup
                )
            else:
                # Если длина подписи превышает лимит, отправляем фото с первой частью подписи без клавиатуры
                sent_message = await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=img,
                    caption=caption_part,
                    parse_mode="HTML"
                )
                logger.info(f"message_parts2 {message_parts}")
                # Отправляем оставшиеся части подписи
                last_caption_message_id = None
                for part in message_parts:
                    sent_message = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=part,  # Отправляем именно элемент списка, а не весь список
                        parse_mode="HTML"
                    )
                    last_caption_message_id = sent_message.message_id

                # Создаём клавиатуру
                keyboard = [
                    [InlineKeyboardButton("📒 Сохранить чтобы не потерять", callback_data=f"save_{user_id}_{sent_message.message_id}")],
                    [InlineKeyboardButton("🗂 Мои сохранённые генерации", callback_data="scheduled_by_tag")],
                    [InlineKeyboardButton("🌃 Опубликовать в общую папку", callback_data=f"neuralpublic_{user_id}_{sent_message.message_id}")],
                    [InlineKeyboardButton("🏙 Посмотреть чужие публикации", callback_data="view_shared")],
                    [InlineKeyboardButton("🖼 Сменить модель", callback_data='choose_modele')],
                    [InlineKeyboardButton("🎨 Выбрать стиль", callback_data='choose_preset')],
                    [InlineKeyboardButton("🌌 В главное меню 🌌", callback_data='restart')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                # Прикрепляем клавиатуру к последнему сообщению с текстом
                target_message_id = last_caption_message_id if last_caption_message_id else sent_message.message_id
                await context.bot.edit_message_reply_markup(
                    chat_id=update.effective_chat.id,
                    message_id=target_message_id,
                    reply_markup=reply_markup
                )
    else:
        # Случай с медиагруппой (несколько изображений)
        media_group = []
        for image_path in image_urls:
            with open(image_path, "rb") as img:
                # Добавляем изображения в медиагруппу без подписи
                media_group.append(InputMediaPhoto(img))

        # Отправляем медиагруппу без подписи
        sent_messages = await context.bot.send_media_group(
            chat_id=update.effective_chat.id,
            media=media_group
        )

        # Получаем ID первого сообщения медиагруппы
        first_media_message_id = sent_messages[0].message_id

        # Отправляем части подписи как отдельные сообщения
        last_caption_message_id = None

        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=caption_text,
            parse_mode="HTML"
        )
        last_caption_message_id = sent_message.message_id  # Обновляем ID последнего сообщения с текстом

        # Создаём клавиатуру
        keyboard = [
            [InlineKeyboardButton("📒 Сохранить чтобы не потерять", callback_data=f"save_{user_id}_{first_media_message_id}")],
            [InlineKeyboardButton("🗂 Мои сохранённые генерации", callback_data="scheduled_by_tag")],
            [InlineKeyboardButton("🌃 Опубликовать в общую папку", callback_data=f"neuralpublic_{user_id}_{first_media_message_id}")],
            [InlineKeyboardButton("🏙 Посмотреть чужие публикации", callback_data="view_shared")],
            [InlineKeyboardButton("🖼 Сменить модель", callback_data='choose_modele')],
            [InlineKeyboardButton("🎨 Выбрать стиль", callback_data='choose_preset')],
            [InlineKeyboardButton("🌌 В главное меню 🌌", callback_data='restart')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Определяем, к какому сообщению прикрепить клавиатуру
        if last_caption_message_id:
            # Если есть части подписи, прикрепляем клавиатуру к последнему сообщению с текстом
            target_message_id = last_caption_message_id
        else:
            # Если подписи нет, прикрепляем клавиатуру к первому сообщению медиагруппы
            target_message_id = first_media_message_id

        # Прикрепляем клавиатуру к целевому сообщению
        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=target_message_id,
            reply_markup=reply_markup
        )

async def download_and_upload_image(image_path):
    """Загрузка изображения из локального файла и отправка его на Catbox."""
    logging.info(f"image_path {image_path}.")
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        image = Image.open(io.BytesIO(image_bytes))

        with io.BytesIO() as output:
            image.save(output, format="PNG")
            output.seek(0)
            await upload_image_to_catbox_in_background(output.getvalue())

    except Exception as e:
        logging.info(f"Ошибка загрузки и отправки изображения: {e}")




from bs4 import BeautifulSoup






# Определение специальных символов Markdown V2, которые нужно экранировать
# Источник: https://core.telegram.org/bots/api#markdownv2-style
MARKDOWN_V2_CHARS_TO_ESCAPE = r'_*[]()~`>#+-=|{}.!'
# Регулярное выражение для поиска неэкранированных спецсимволов
# Используем negative lookbehind (?<!) чтобы не затронуть уже экранированные символы (\)
MD_ESCAPE_REGEX = re.compile(r'(?<!\\)([' + re.escape(MARKDOWN_V2_CHARS_TO_ESCAPE) + r'])')

# Вспомогательная функция для экранирования текста для HTML внутри <pre> или <code>
def escape_html_tags(text):
    return html.escape(text, quote=False) # quote=False чтобы не трогать кавычки

def markdown_v2_to_html(text: str) -> str:
    """
    Конвертирует текст с разметкой Markdown V2 в HTML, поддерживаемый Telegram.

    Args:
        text: Исходный текст с Markdown V2.

    Returns:
        Текст с HTML-тегами.
    """
    if not text:
        return ""

    # 0. Обработка экранированных символов Markdown
    # Заменим \*, \_, \~ и т.д. на временные плейсхолдеры, чтобы они не мешали
    # основным регуляркам, а затем вернем их как обычные символы.
    escaped_placeholders = {}
    placeholder_idx = 0
    def escape_md_char(match):
        nonlocal placeholder_idx
        char = match.group(1)
        placeholder = f"__MD_ESCAPED_{placeholder_idx}__"
        escaped_placeholders[placeholder] = char
        placeholder_idx += 1
        return placeholder

    text = re.sub(r'\\([' + re.escape(MARKDOWN_V2_CHARS_TO_ESCAPE) + r'])', escape_md_char, text)

    # 1. Блоки кода (```language\n code ```) -> <pre><code class="language-...">code</code></pre>
    # Или (```\n code ```) -> <pre>code</pre>
    def replace_pre(match):
        lang = match.group(1)
        code = match.group(2)
        escaped_code = escape_html_tags(code) # Экранируем HTML внутри кода
        if lang:
            lang = lang.strip()
            # Telegram ожидает class="language-...", если язык указан
            return f'<pre><code class="language-{html.escape(lang)}">{escaped_code}</code></pre>'
        else:
            return f'<pre>{escaped_code}</pre>'
    # Ищем ``` возможно с языком, затем \n, затем сам код (.*?), затем \n```
    text = re.sub(r'```(\w*)\n(.*?)(\n)?```', replace_pre, text, flags=re.DOTALL | re.MULTILINE)

    # 2. Встроенный код (`code`) -> <code>code</code>
    def replace_inline_code(match):
        code = match.group(1)
        escaped_code = escape_html_tags(code) # Экранируем HTML внутри кода
        return f'<code>{escaped_code}</code>'
    text = re.sub(r'`(.*?)`', replace_inline_code, text)

    # 3. Ссылки ([text](url)) -> <a href="url">text</a>
    def replace_link(match):
        link_text = match.group(1)
        url = match.group(2)
        # Экранируем URL, особенно если там есть кавычки или другие символы
        escaped_url = html.escape(url, quote=True)
        # Текст ссылки НЕ экранируем здесь, т.к. он может содержать другую разметку
        return f'<a href="{escaped_url}">{link_text}</a>'
    # Ищем [текст_не_]](url_без_))
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, text)

    # 4. Жирный (*text*) -> <b>text</b>
    # Используем нежадный поиск .*? и проверяем, чтобы перед/после не было \
    # Заменяем только если символ * не является частью плейсхолдера
    text = re.sub(r'(?<!\\)\*(?!\s)(.*?)(?<!\s)\*(?!\\)', r'<b>\1</b>', text)

    # 5. Курсив (_text_) -> <i>text</i> (в Markdown V2 _это курсив_, __это подчеркивание__)
    # Используем нежадный поиск .*?, проверяем пробелы и экранирование
    text = re.sub(r'(?<!\\)_(?!\s)(.*?)(?<!\s)_(?!\\)', r'<i>\1</i>', text)

    # 6. Подчеркнутый (__text__) -> <u>text</u>
    text = re.sub(r'(?<!\\)__(?!\s)(.*?)(?<!\s)__(?!\\)', r'<u>\1</u>', text)

    # 7. Зачеркнутый (~text~) -> <s>text</s>
    text = re.sub(r'(?<!\\)~(?!\s)(.*?)(?<!\s)~(?!\\)', r'<s>\1</s>', text)

    # 8. Спойлер (||text||) -> <tg-spoiler>text</tg-spoiler>
    text = re.sub(r'(?<!\\)\|\|(?!\s)(.*?)(?<!\s)\|\|(?!\\)', r'<tg-spoiler>\1</tg-spoiler>', text)

    # 9. Блок цитирования (> text или >> text)
    # Это сложнее, так как цитаты могут быть многострочными и вложенными.
    # Простой подход: заменить строки, начинающиеся с >, на <blockquote>.
    # Более сложный: сгруппировать последовательные строки цитат.
    # Используем простой подход для начала, заменяя каждую строку.
    # Замечание: Это не будет поддерживать вложенность через >>
    # Важно: Делаем это построчно ПОСЛЕ других замен.
    lines = text.split('\n')
    in_blockquote = False
    result_lines = []
    for line in lines:
        if line.startswith('>'):
            quote_content = line[1:].strip()
            if not in_blockquote:
                result_lines.append('<blockquote>') # Используем стандартный тег здесь
                in_blockquote = True
            # НЕ экранируем HTML здесь, т.к. внутри цитаты может быть другая разметка
            result_lines.append(quote_content)
        else:
            if in_blockquote:
                result_lines.append('</blockquote>')
                in_blockquote = False
            result_lines.append(line)
    # Закрыть blockquote, если он был последним
    if in_blockquote:
        result_lines.append('</blockquote>')

    text = '\n'.join(result_lines)

    # 10. Восстановление экранированных символов
    for placeholder, char in escaped_placeholders.items():
        text = text.replace(placeholder, char)

    return text


def split_html_text(text: str, max_caption_length: int, max_message_length: int):
    """
    Разделяет текст (сначала конвертируя Markdown V2 в HTML) на части для Telegram.
    Старается сохранить HTML-теги. Заменяет <blockquote> на <blockquote expandable>.
    Первая часть (caption) может иметь длину до max_caption_length (если > 0).
    Остальные части имеют длину до max_message_length.

    Args:
        text: Исходный текст (может содержать Markdown V2).
        max_caption_length: Максимальная длина первой части (0, если caption не нужен).
        max_message_length: Максимальная длина последующих частей.

    Returns:
        Кортеж: (caption_part: str | None, message_parts: list[str])
                 Возвращает (None, [исходный_html]) если длина текста меньше лимитов.
    """

    # ---- Шаг 1: Конвертация Markdown V2 в HTML ----
    html_text = markdown_v2_to_html(text)

    # Базовые проверки
    if max_message_length <= 0:
        raise ValueError("max_message_length должен быть положительным числом.")
    if max_caption_length < 0:
        raise ValueError("max_caption_length не может быть отрицательным.")

    # Список поддерживаемых тегов Telegram (основные)
    # <a href="...">, <b>, <i>, <u>, <s>, <tg-spoiler>, <code>, <pre>, <blockquote>
    # Замечание: Telegram обрабатывает атрибут class в <pre><code class="...">
    SUPPORTED_TAGS = {"a", "b", "i", "u", "s", "tg-spoiler", "code", "pre", "blockquote"}

    parts = []
    open_tags = [] # Стек открытых тегов на момент разреза
    current_pos = 0
    text_len = len(html_text)

    # Определяем длину первого блока
    first_max_len = max_caption_length if max_caption_length > 0 else max_message_length

    # Если текст короткий и не требует разделения
    is_caption_needed = max_caption_length > 0
    initial_max_len = first_max_len if is_caption_needed else max_message_length

    if text_len <= initial_max_len:
         # Применяем модификацию blockquote к единственной части
        final_text = html_text.replace('<blockquote>', '<blockquote expandable>')
        if is_caption_needed:
            return final_text, []
        else:
             # Если caption не нужен, но текст умещается в max_message_length
            if text_len <= max_message_length:
                 return None, [final_text]
            # Если caption не нужен, но текст длиннее max_message_length (но <= first_max_len, что невозможно тут)
            # Эта ветка по идее не должна сработать при text_len <= initial_max_len
            # Но на всякий случай - продолжаем разделение

    # --- Основной цикл разделения ---
    while current_pos < text_len:
        max_len = first_max_len if not parts else max_message_length
        # Предварительная позиция конца среза
        end_pos = min(current_pos + max_len, text_len)
        cut_pos = end_pos # Позиция фактического разреза

        # Если мы не в конце текста, ищем безопасное место для разреза
        if end_pos < text_len:
            # Ищем ближайший пробел, \n, или конец тега (>) с конца к началу
            safe_cut_found = False
            # Идем назад от предполагаемого конца среза
            for i in range(end_pos - 1, current_pos - 1, -1):
                char = html_text[i]
                # Безопасные точки для разреза: пробельные символы или конец тега
                if char in (' ', '\n', '\t', '>'):
                    # Дополнительная проверка: не находимся ли мы внутри тега <...> ?
                    # Ищем последний '<' перед позицией i+1
                    last_open_bracket = html_text.rfind('<', current_pos, i + 1)
                    # Ищем последний '>' перед позицией i+1
                    last_close_bracket = html_text.rfind('>', current_pos, i + 1)

                    # Если '<' найден и он после последнего '>', значит мы внутри тега <...текст_разреза
                    if last_open_bracket != -1 and last_open_bracket > last_close_bracket:
                        continue # Небезопасно, ищем дальше

                    cut_pos = i + 1 # Режем *после* безопасного символа
                    safe_cut_found = True
                    break
                # Если встретили '<' до безопасного символа, значит мы внутри тега <tag...разрез...
                # Это тоже небезопасно, но проверка выше должна это покрыть.
                # Добавим явную проверку на всякий случай
                if char == '<':
                     # Ищем '>' после этого '<' в пределах предполагаемого среза
                     matching_close = html_text.find('>', i, end_pos)
                     if matching_close == -1 or matching_close > end_pos -1:
                          # Тег не закрывается в пределах среза, резать здесь нельзя
                          continue

            # Если безопасного места не нашли (очень длинное слово/тег без пробелов),
            # вынужденно режем по max_len.
            if not safe_cut_found:
                cut_pos = end_pos
                # Можно добавить предупреждение для отладки
                # print(f"Warning: Forced cut required near position {cut_pos}")

        # --- Извлечение и обработка части ---
        # 1. Получаем сырой фрагмент текста
        raw_part = html_text[current_pos:cut_pos]

        # 2. Формируем префикс из открытых тегов с предыдущего шага
        prefix = "".join([f"<{tag_info['name']}{tag_info['attrs']}>" for tag_info in open_tags])

        # 3. Формируем суффикс из закрывающих тегов для *этой* части
        # Анализируем теги *внутри* raw_part, учитывая начальный стек open_tags
        # чтобы понять, какие теги останутся открытыми в конце ЭТОГО фрагмента
        current_part_open_tags = list(open_tags) # Копия стека на начало этого фрагмента
        temp_open_tags_next = list(open_tags) # Стек, который перейдет на СЛЕДУЮЩИЙ шаг

        # Используем простой парсер стека тегов для определения состояния *в конце* raw_part
        i = 0
        while i < len(raw_part):
            if raw_part[i] == '<':
                end_tag_char_index = raw_part.find('>', i)
                if end_tag_char_index != -1:
                    tag_content = raw_part[i+1:end_tag_char_index]
                    tag_parts = tag_content.split(maxsplit=1)
                    tag_name = tag_parts[0].lower()

                    is_closing_tag = tag_name.startswith('/')
                    actual_tag_name = tag_name[1:] if is_closing_tag else tag_name
                    attributes = ""
                    if not is_closing_tag and len(tag_parts) > 1:
                         attributes = " " + tag_parts[1]

                    # Проверяем, поддерживается ли тег
                    if actual_tag_name in SUPPORTED_TAGS:
                        if is_closing_tag:
                            # Закрывающий тег: пытаемся снять со стека
                            if temp_open_tags_next and temp_open_tags_next[-1]['name'] == actual_tag_name:
                                temp_open_tags_next.pop()
                        # Проверяем самозакрывающиеся (хотя для HTML5 это редкость, кроме <br>, <hr> и т.д., которых нет в SUPPORTED_TAGS)
                        # и пропускаем их добавление в стек
                        elif not tag_content.endswith('/'):
                             # Открывающий тег: добавляем в стек
                             temp_open_tags_next.append({'name': actual_tag_name, 'attrs': attributes})

                    i = end_tag_char_index # Переходим за '>'
                else:
                    # Незакрытый '<' в конце фрагмента? Игнорируем или обрабатываем как текст.
                    # Безопаснее остановиться здесь.
                    break
            i += 1

        # 4. Собираем финальную часть с префиксом и автозакрытием от BeautifulSoup
        # Используем BeautifulSoup для надежного закрытия тегов *внутри* текущего фрагмента
        # Префикс + сам фрагмент + закрывающие теги для того, что было открыто *в этом фрагменте*
        # но не закрыто до cut_pos.
        part_with_prefix = prefix + raw_part
        soup = BeautifulSoup(part_with_prefix, 'html.parser')

        # Получаем "исправленный" HTML фрагмент от BeautifulSoup
        # BS автоматически закроет теги, которые были открыты в part_with_prefix
        processed_part = "".join(str(content) for content in soup.body.contents) if soup.body else str(soup)

        # Удаляем пустые строки в начале/конце, если они не <pre>
        # processed_part = processed_part.strip() # Может быть слишком агрессивно для <pre>

        # 5. Добавляем обработанную часть в результат, если она не пустая
        if processed_part and not processed_part.isspace():
             # --- Модификация blockquote для этой части ---
             final_part = processed_part.replace('<blockquote>', '<blockquote expandable>')
             parts.append(final_part)

        # 6. Обновляем стек открытых тегов для следующей итерации
        open_tags = temp_open_tags_next

        # 7. Переходим к следующей части
        current_pos = cut_pos

    # Разделяем на caption и messages
    caption_part = None
    message_parts = []

    if max_caption_length > 0 and parts:
        caption_part = parts[0]
        message_parts = parts[1:]
    else:
        message_parts = parts

    # На случай если последний фрагмент оставил теги открытыми (хотя BS должен был закрыть)
    # Можно добавить закрывающие теги к последнему элементу message_parts, но обычно не требуется

    return caption_part, message_parts








async def choose_preset(update, context):
    """Отправляет кнопки с пресетами пользователю."""
    user_id = update.effective_user.id
    preset_name = get_user_preset(user_id)  # Получаем текущий пресет пользователя

    # Создаем список кнопок пресетов, добавляя галочку к активному пресету
    buttons = [
        InlineKeyboardButton(
            f"✅ {preset}" if preset == preset_name else preset, 
            callback_data=f"preset_{preset}"
        )
        for preset in PRESET_PROMPTS.keys()
    ]

    # Создаем кнопку закрыть
    close_button = [InlineKeyboardButton("❌ Закрыть это меню ❌", callback_data="presetclose")]

    # Группируем кнопки пресетов по две в ряд и добавляем кнопку закрыть внизу
    keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    keyboard.append([InlineKeyboardButton("🖼 Сменить модель", callback_data='choose_modele')])    
    keyboard.append(close_button)  # Добавляем кнопку закрыть последней строкой

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Формируем сообщение с текущим стилем
    current_preset_text = f"Текущий стиль: *{preset_name}*" if preset_name else "Стиль не выбран."
    message_text = (
        f"{current_preset_text}\n\n"
        "Выберите стиль. Стиль представляет из себя заранее заготовленный промпт, "
        "который автоматически будет добавляться к вашим запросам:"
    )

    if update.message:  # Вызов через команду
        await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode="Markdown")

    elif update.callback_query:  # Вызов через кнопку
        message = update.callback_query.message
        if message and message.text:  # Проверяем, есть ли текст
            await message.edit_text(message_text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await message.reply_text(message_text, reply_markup=reply_markup, parse_mode="Markdown")
        await update.callback_query.answer()  # Закрываем запрос



# Обработчик для кнопки закрыть
async def handle_presetclose_button(update, context):
    query = update.callback_query
    await query.message.delete()  # Удаляем сообщение
    await query.answer()  # Подтверждаем обработку callback
    await run_gpt(update, context)

async def preset_callback(update, context):
    """Обрабатывает выбор пресета."""
    query = update.callback_query
    user_id = query.from_user.id
    preset_name = query.data.replace("preset_", "")

    if preset_name in PRESET_PROMPTS:
        set_user_preset(user_id, preset_name)
        await query.answer(f"Выбран пресет: {preset_name}")
        await choose_preset(update, context)
    else:
        await query.answer("Ошибка: выбранный пресет не найден.")  



async def handle_neuralpublic_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    # Извлекаем user_id и message_id из callback_data
    parts = query.data.split('_')
    user_id = int(parts[1])
    message_id = int(parts[2])

    # Проверяем, не был ли caption разбит на части
    saved_data = context.user_data.get(f"split_message_{user_id}_{message_id}")
    if saved_data:
        caption = query.message.text_html
        file_id = saved_data["file_id"]
    else:
        caption = query.message.caption_html
        logger.info(f"caption2 {caption} ")         
        file_id = query.message.photo[-1].file_id

    # Сохраняем данные о генерации в контексте
    context.user_data["shared_generation_data"] = {
        "user_id": user_id,
        "message_id": message_id,
        "caption": caption,
        "file_id": file_id,
    }

    # Отображаем клавиатуру с эмодзи
    emojis = [
        "👀", "🤷‍♂️", "🧶", "🦊", "🦄", "🦆", "🐳", "🌿", "🌸", "🍓",
        "🍑", "🍆", "🌈", "🌧", "☀️", "⭐️", "🫖", "🌙", "🌠", "❄️",
        "🗑", "📎", "✏️", "🎨", "😈", "📷", "📚", "⏳", "✅", "❇️",
        "❌", "🔄", "🩷", "💛", "💚", "💙", "❤️", "💜", "🖤", "🤍",
    ]
    reply_markup = createneural_emoji_keyboard(emojis, user_id, message_id)
    await query.message.reply_text("Выберите метку для публикации в общую папку:", reply_markup=reply_markup)

def createneural_emoji_keyboard(emojis, user_id, message_id):
    keyboard = []
    row = []
    for emoji in emojis:
        row.append(InlineKeyboardButton(emoji, callback_data=f"sharedtag_{emoji}_{user_id}_{message_id}"))
        if len(row) == 4:  # Если в строке 4 кнопки, добавляем её в клавиатуру
            keyboard.append(row)
            row = []  # Начинаем новую строку
    if row:  # Добавляем оставшиеся кнопки, если они есть
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

async def handle_shared_tag_selection(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    await query.message.delete()

    # Извлекаем данные из callback_data
    _, tag, user_id_str, message_id_str = query.data.split('_')
    user_id = int(user_id_str)
    message_id = int(message_id_str)

    # Получаем данные из контекста
    generation_data = context.user_data.get("shared_generation_data")
    if not generation_data:
        await query.message.reply_text("🚫 Ошибка: данные генерации не найдены")
        return

    # Формируем данные для сохранения
    media_group_data = {
        "media": [{
            "caption": generation_data["caption"],
            "file_id": generation_data["file_id"],
            "parse_mode": "HTML"
        }],
        "scheduled": tag
    }

    # Сохраняем в отдельную ветку shared_publications
    save_to_shared_publications(user_id, f"{user_id}_{message_id}", media_group_data)

    # Очищаем контекст
    context.user_data.pop("shared_generation_data", None)

    # Отправляем подтверждение
    await query.message.reply_text(
        "✅ Публикация успешно добавлена в общий доступ!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏙 Посмотреть общие публикации", callback_data="view_shared")]
        ])
    )
async def handle_sharefromuser_publication(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    # Проверяем корректность данных
    if "_" in query.data:
        _, key = query.data.split("_", 1)
    else:
        await query.message.reply_text("🚫 Ошибка: Некорректный формат данных.")
        return

    user_id = str(update.effective_user.id)
    logger.info(f"key {key} ")
    # Копируем публикацию в shared_publications
    success = copy_to_shared_publications(user_id, key)

    if success:
        # Отправляем подтверждение
        await query.message.reply_text(
            "✅ Публикация успешно добавлена в общий доступ!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏙 Посмотреть общие публикации", callback_data="view_shared")]
            ])
        )
    else:
        await query.message.reply_text("🚫 Ошибка: Не удалось найти публикацию.")



# Формирование клавиатуры с метками публикаций
def generate_shared_keyboard(publications, user_id):
    scheduled_counts = {}

    # Подсчёт количества публикаций для каждой метки
    for owner_id, user_data in publications.items():
        for post_id, post_data in user_data.items():
            label = post_data.get("scheduled", "🧶")
            scheduled_counts[label] = scheduled_counts.get(label, 0) + 1
    
    keyboard = [[InlineKeyboardButton("📜 Все записи", callback_data="view_shared_all")]]
    
    # Добавляем кнопку "⭐ Избранные", если у пользователя есть избранные записи
    favorite_count = sum(
        1 for owner_id, user_data in publications.items()
        for post_id, post_data in user_data.items()
        if user_id in post_data.get("favorites", [])
    )
    if favorite_count > 0:
        keyboard.append([InlineKeyboardButton(f"⭐ Избранные ({favorite_count})", callback_data="view_shared_favorites")])

    row = []
    for label, count in scheduled_counts.items():
        row.append(InlineKeyboardButton(f"{label} ({count})", callback_data=f"view_shared_{label}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

# Обработчик кнопки "🌍 Общие публикации"
async def handle_view_shared(update: Update, context: CallbackContext):
    await update.callback_query.answer()  # Гасим нажатие кнопки

    user_id = update.callback_query.from_user.id
    publications = load_shared_publications()
    keyboard = generate_shared_keyboard(publications, user_id)
    
    await update.callback_query.message.reply_text(
        "Выберите метку для просмотра публикаций:", 
        reply_markup=keyboard
    )


# Обработчик выбора метки публикации
from html import unescape
async def handle_select_scheduled(update: Update, context: CallbackContext):
    query = update.callback_query
    selected_label = query.data.replace("view_shared_", "")
    user_id = query.from_user.id
    publications = load_shared_publications()

    post_buttons = []
    
    for owner_id, user_data in publications.items():
        for post_id, post_data in user_data.items():
            label = post_data.get("scheduled", "🧶")
            favorites = post_data.get("favorites", [])
            fav_count = len(favorites)  # Количество добавлений в избранное

            # Фильтруем публикации: если выбраны "⭐ Избранные", показываем только те, где user_id в favorites
            if selected_label == "favorites":
                if user_id not in favorites:
                    continue  
            elif selected_label != "all" and label != selected_label:
                continue  

            # Обрезка caption
            caption = post_data["media"][0]["caption"]
            caption = re.sub(r"<.*?>", "", caption)  # Убираем HTML-теги
            caption = unescape(caption)  # Декодируем HTML-сущности
            caption = re.split(r"\bseed\b", caption, flags=re.IGNORECASE)[0]  # Обрезаем по "seed"
            caption = re.sub(r"^(?:нарисуй|draw)[:,]?\s*\d*,?\s*", "", caption, flags=re.IGNORECASE)
            caption = re.sub(r"^\d+,\s*", "", caption)  # Убираем числа в начале строки
            
            # Обрезаем caption до ближайшего пробела перед 23 символами
            if len(caption) > 31:
                cutoff = caption[:31].rfind(" ")
                caption = caption[:cutoff] if cutoff != -1 else caption[:31]

            # Добавляем количество добавлений в избранное
            text_preview = f"{caption.strip()} ({fav_count})" if fav_count > 0 else caption

            post_buttons.append((
                fav_count,  # Для сортировки
                InlineKeyboardButton(
                    f"{label} {text_preview}",
                    callback_data=f"viewneuralpost_{owner_id}_{post_id}"
                )
            ))

    # Сортируем кнопки по количеству добавлений в избранное (по убыванию)
    post_buttons.sort(reverse=True, key=lambda x: x[0])

    if not post_buttons:
        await query.answer("Нет публикаций с данной меткой.", show_alert=True)
        return

    keyboard = [[button[1]] for button in post_buttons]
    keyboard.append([InlineKeyboardButton("⬅ Назад", callback_data="view_shared")])
    
    await query.message.edit_text("Выберите публикацию из списка представленного ниже:", reply_markup=InlineKeyboardMarkup(keyboard))



# Обработчик показа конкретной публикации
# Обработчик показа конкретной публикации
async def handle_view_post(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    try:
        query = update.callback_query
        logger.info(f"query {query}") 
        _, user_id, post_id = query.data.split("_", 2)
        publications = load_shared_publications()
        
        post_data = publications.get(user_id, {}).get(post_id)
        
        if not post_data:
            await query.answer("Публикация не найдена.", show_alert=True)
            return
        
        media = post_data["media"][0]
        caption = media["caption"]
        original_caption = caption
        logger.info(f"caption {caption}")
        # Проверяем длину caption
        if len(caption) > 1024:
            # Если caption слишком длинный, отправляем фото без подписи
            await context.bot.send_photo(
                chat_id=query.message.chat.id,
                photo=media["file_id"]
            )
            send_caption_separately = True
            logger.info(f"send_caption_separately {send_caption_separately}")                
        else:
            # Если caption в пределах лимита, отправляем его вместе с фото
            await context.bot.send_photo(
                chat_id=query.message.chat.id,
                photo=media["file_id"],
                caption=caption,
                parse_mode="HTML"
            )
            send_caption_separately = False
            logger.info(f"send_caption_separately {send_caption_separately}")          
        logger.info(f"send_caption_separately {send_caption_separately}")                
        # Получаем количество добавлений в избранное
        favorites = post_data.get("favorites", [])
        fav_count = len(favorites)

        # Формируем текст второго сообщения
       
        # Генерация клавиатуры с оставшимися постами
        selected_label = post_data.get("scheduled", "🧶")
        post_buttons = []
        fav_text = f"Этот пост добавлен в избранное {fav_count} раз(а)\n" if fav_count > 0 else ""
        remaining_posts_text = f"Ниже можно посмотреть список других постов с меткой {selected_label}:" 
        # Добавляем дополнительные кнопки перед списком записей
        if int(query.from_user.id) in favorites:
            fav_button = InlineKeyboardButton("❌ Удалить из избранного", callback_data=f"favorite_{user_id}_{post_id}")
        else:
            fav_button = InlineKeyboardButton("⭐ Сохранить в избранное", callback_data=f"favorite_{user_id}_{post_id}")


        extra_buttons = [
            [
                InlineKeyboardButton("Пост ТГ", callback_data=f"publish_{post_id}"),
                InlineKeyboardButton("Пост ВК", callback_data=f"vkpub_{post_id}")
            ],
            [fav_button],  # Используем динамически выбранную кнопку
            [InlineKeyboardButton("========......========", callback_data="no_action")]
        ]

        for u_id, user_data in publications.items():
            for p_id, p_data in user_data.items():
                if u_id == user_id and p_id != post_id:  # Исключаем уже показанный пост
                    label = p_data.get("scheduled", "🧶")
                    # Фильтрация записей по выбранной метке
                    if selected_label != "all" and label != selected_label:
                        continue  
                    # 🎯 Обрабатываем caption так же, как в handle_select_scheduled
                    caption = p_data["media"][0]["caption"]
                    caption = re.sub(r"<.*?>", "", caption)  # Убираем HTML-теги
                    caption = unescape(caption)  # Декодируем HTML-сущности
                    caption = re.split(r"\bseed\b", caption, flags=re.IGNORECASE)[0]  # Обрезаем по "seed"
                    caption = re.sub(r"^(?:нарисуй|draw)[:,]?\s*\d*,?\s*", "", caption, flags=re.IGNORECASE)              
                    caption = re.sub(r"^\d+,\s*", "", caption)  # Убираем числа в начале строки

                    # Обрезаем caption до ближайшего пробела перед 23 символами
                    if len(caption) > 31:
                        cutoff = caption[:31].rfind(" ")
                        caption = caption[:cutoff] if cutoff != -1 else caption[:31]

                    text_preview = f"{caption.strip()} ({fav_count})" if fav_count > 0 else caption

                    post_buttons.append(
                        InlineKeyboardButton(f"{label} {text_preview}", callback_data=f"viewneuralpost_{u_id}_{p_id}")
                    )

        keyboard = extra_buttons if all(isinstance(i, list) for i in extra_buttons) else [[button] for button in extra_buttons]

        if post_buttons:
            keyboard.extend([[button] for button in post_buttons])
        else:
            keyboard.append([InlineKeyboardButton("Других постов с этой меткой пока нет", callback_data="no_posts_available")])

        keyboard.append([InlineKeyboardButton("⬅ Другие посты", callback_data="view_shared")])

        # Если caption был слишком длинным, отправляем его отдельным сообщением
        if send_caption_separately:
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=f"{original_caption}\n\n{fav_text}{remaining_posts_text}",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=f"{fav_text}{remaining_posts_text}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await query.answer("Произошла ошибка.")



async def handle_add_favorite(update: Update, context: CallbackContext):
    await update.callback_query.answer()    
    query = update.callback_query
    _, owner_id, post_id = query.data.split("_", 2)
    user_id = query.from_user.id

    added = add_to_favorites(user_id, owner_id, post_id, context)

    # Отправляем сообщение в зависимости от результата
    text = "✅ Пост добавлен в избранное." if added else "❌ Пост удалён из избранного."
    await query.message.reply_text(text)


async def regenerate_image(update, context):
    """Обработчик для повторной генерации с новым seed"""
    query = update.callback_query
    await query.answer()

    # Получаем user_id и message_id из callback_data
    data_parts = query.data.split("_")
    if len(data_parts) < 3:
        return  # Неправильный формат callback_data

    user_id = int(data_parts[1])
    message_id = int(data_parts[2])

    # Отправляем пользователю сообщение о начале повторной генерации
    await context.bot.send_message(chat_id=user_id, text="Ожидайте, повторная генерация запущена")

    # Извлекаем текст из оригинального сообщения с кнопкой
    if not query.message:
        return  # Сообщение не найдено

    full_text = query.message.text if query.message.text else query.message.caption
    if not full_text:
        return  # Нет текста для обработки

    # Парсим промпт из текста сообщения
    prompt_match = re.search(r"^(.+?)\n\nSeed:", full_text, re.DOTALL)
    if prompt_match:
        prompt = prompt_match.group(1).strip()
    else:
        prompt = full_text  # Если шаблон не найден, используем весь текст

    # Убираем ключевые слова в начале строки и возможное число с запятой
    prompt = re.sub(r"^(?:Нарисуй[:,]?|draw[:,]?)\s*\d*,?\s*", "", prompt, flags=re.IGNORECASE).strip()

    logger.info(f"Повторная генерация с prompt: {prompt}")

    # Запускаем генерацию с новым seed
    await generate_image(update, context, user_id, prompt, query_message=query.message)

from huggingface_hub import InferenceClient

async def handle_save_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    # Извлекаем user_id и message_id из callback_data
    parts = query.data.split('_')
    user_id = int(parts[1])
    message_id = int(parts[2])

    # Проверяем, не был ли caption разбит на части
    saved_data = context.user_data.get(f"split_message_{user_id}_{message_id}")
    if saved_data:
        caption = query.message.text_html
        file_id = saved_data["file_id"]
    else:
        caption = query.message.caption_html
        logger.info(f"caption2 {caption} ")         
        file_id = query.message.photo[-1].file_id

    # Сохраняем данные о генерации в контексте
    context.user_data["generation_data"] = {
        "user_id": user_id,
        "message_id": message_id,
        "caption": caption,
        "file_id": file_id,
    }

    # Отображаем клавиатуру с эмодзи
    emojis = [
        "👀", "🤷‍♂️", "🧶", "🦊", "🦄", "🦆", "🐳", "🌿", "🌸", "🍓",
        "🍑", "🍆", "🌈", "🌧", "☀️", "⭐️", "🫖", "🌙", "🌠", "❄️",
        "🗑", "📎", "✏️", "🎨", "😈", "📷", "📚", "⏳", "✅", "❇️",
        "❌", "🔄", "🩷", "💛", "💚", "💙", "❤️", "💜", "🖤", "🤍",
    ]
    reply_markup = create_emoji_keyboard(emojis, user_id, message_id)
    await query.message.reply_text("Выберите метку для записи:", reply_markup=reply_markup)




async def upload_image_to_catbox_in_background(image_bytes: bytes):
    """Фоновая задача для загрузки изображения на Catbox."""
    file_path = "temp_image.png"  # Локальный путь для временного хранения изображения
    try:
        # Сохраняем изображение во временный файл
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        # Загружаем изображение на Catbox
        catbox_url = await second_upload_image(file_path)
        logging.info(f"Изображение успешно загружено на Catbox: {catbox_url}")
    except Exception as e:
        logging.error(f"Не удалось загрузить изображение на Catbox: {e}")
    finally:
        # Гарантированно удаляем временный файл с повторными попытками
        if os.path.exists(file_path):
            for _ in range(7):  # Пытаемся 5 раз
                try:
                    os.remove(file_path)
                    logging.info(f"Временный файл {file_path} удалён.")
                    break  # Успешно удалили, выходим из цикла
                except Exception as e:
                    logging.warning(f"Ошибка удаления {file_path}, повторная попытка через 1 секунду...: {e}")
                    time.sleep(2)  # Ждём 1 секунду перед повторной попыткой
            else:
                logging.error(f"Не удалось удалить временный файл {file_path} после 5 попыток.")

async def examples_table_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Отправляем промежуточное сообщение
    loading_message = await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="⏳ Таблица загружается, подождите немного..."
    )

    # Список URL-ов для изображений с обоих хостингов
    image_urls = [
        ("https://files.catbox.moe/5ux771.jpg", "https://i.ibb.co/3mJjVcy5/2.jpg"),
        ("https://files.catbox.moe/0pqvrr.jpg", "https://i.ibb.co/LhJ7sjj6/3.jpg"),
        ("https://files.catbox.moe/tqqvrn.jpg", "https://i.ibb.co/dwRCWM14/4.jpg"),
        ("https://files.catbox.moe/sy67tu.jpg", "https://i.ibb.co/jkhfq6Bm/5.jpg")
    ]

    async def is_image_available(url):
        """Проверяет доступность изображения по URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url) as response:
                    return response.status == 200
        except Exception:
            return False

    # Формируем медиа группу
    media_group = []
    for idx, (catbox_url, ibb_url) in enumerate(image_urls):
        # Проверяем доступность изображения на catbox
        if not await is_image_available(catbox_url):
            image_url = ibb_url  # Если catbox недоступен, используем ibb
        else:
            image_url = catbox_url

        # Добавляем описание только к первому изображению
        caption = (
            '<b>Пример:</b>\n'
            '<code>Нарисуй: 322434, цифровой арт с совой сидящей на ветке на фоне луны (3, 15) [3:2]</code>\n\n'
            'В данном случае 322434 - это seed, 3 - guidance_scale, '
            '15 - num_inference_steps, 3:2 - соотношение сторон. '
            'Подробнее смотрите по кнопке помощи.'
        ) if idx == 0 else None

        media_group.append(
            InputMediaPhoto(
                media=image_url,
                caption=caption,
                parse_mode='HTML'
            )
        )

    # Отправляем медиа группу
    sent_messages = await context.bot.send_media_group(
        chat_id=query.message.chat_id,
        media=media_group
    )

    # Удаляем промежуточное сообщение
    await context.bot.delete_message(
        chat_id=query.message.chat_id,
        message_id=loading_message.message_id
    )

    # Добавляем кнопку "Помощь" под последним сообщением медиагруппы
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📗 Помощь", callback_data='short_help_gpt')],
        [InlineKeyboardButton("🖼 Сменить модель", callback_data='choose_modele')],
        [InlineKeyboardButton("🎨 Выбрать стиль", callback_data='choose_preset')], 
        [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')] 
    ])
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Нажмите кнопку ниже для получения дополнительной информации:",
        reply_markup=keyboard
    )






# Функция для обработки нажатия кнопки "Сбросить диалог"
async def reset_dialog(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    
    # Сброс контекста в Firebase
    reset_firebase_dialog(user_id)
    

    await query.answer("Диалог сброшен. Вы можете начать новый разговор.", show_alert=True)






async def start_search(update: Update, context: CallbackContext) -> int:
    if update.message:
        user_id = update.message.from_user.id  # Когда вызвано командой /search
        message_to_reply = update.message
    elif update.callback_query:
        user_id = update.callback_query.from_user.id  # Когда нажата кнопка "Начать поиск"
        message_to_reply = update.callback_query.message
        await update.callback_query.answer()

    # Устанавливаем флаг для режима поиска и сбрасываем другие флаги
    is_search_mode[user_id] = True
    is_gpt_mode[user_id] = False
    is_ocr_mode[user_id] = False

    # Создаем кнопку "Отменить поиск"
    keyboard = [
        [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение с кнопкой
    await message_to_reply.reply_text(
        "Пожалуйста, отправьте изображение для поиска источника или для проверки, сгенерировано ли оно нейросетью.",
        reply_markup=reply_markup
    )
    
    return ASKING_FOR_FILE

async def search_image_saucenao(image_path: str):
    url = 'https://saucenao.com/search.php'
    params = {
        'api_key': 'd3d3b527510c50ca559d38901614b0da7c86db75',
        'output_type': 0,
        'numres': 10,
        'db': 999,
    }

    async with aiohttp.ClientSession() as session:
        with open(image_path, 'rb') as image_file:
            files = {'file': image_file}

            async with session.post(url, params=params, data=files) as response:
                # Проверка на превышение лимита
                if response.status == 429:
                    html_content = await response.text()
                    if "Daily Search Limit Exceeded" in html_content:
                        raise Exception("Лимит превышен")  # Бросаем исключение, если превышен лимит
                    else:
                        logging.error("Ошибка 429: неизвестная причина")
                        return None, [], None, None, None, None, None, None, None
                
                # Проверка успешного ответа
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')

                    # Находим все блоки результатов
                    result_blocks = soup.find_all('td', class_='resulttablecontent')
                    results = []

                    # Проверяем, до какого места мы можем обрабатывать результаты
                    for block in result_blocks:
                        if block.find_parent(class_='result', id='result-hidden-notification'):
                            break

                        similarity_info = block.find('div', class_='resultsimilarityinfo')
                        if similarity_info:
                            similarity_percentage = float(similarity_info.text.replace('%', '').strip())
                            
                            if similarity_percentage >= 60:
                                results.append((similarity_percentage, block))

                    # Инициализируем переменные
                    authors_text = None
                    links = []
                    jp_name = None
                    details_text = None
                    ep_name = None
                    ep_time = None
                    dA_id = None
                    full_author_text = None
                    pixiv_id = None
                    twitter_id = None

                    if results:
                        results.sort(key=lambda x: x[0], reverse=True)
                        best_match = results[0][1]

                        result_title_div = best_match.find('div', class_='resulttitle')
                        authors_parts = []
                        details_parts = []

                        if result_title_div:
                            for elem in result_title_div.children:
                                if elem.name == "strong" and 'subtext' not in elem.get("class", []):
                                    authors_text = elem.text.strip()
                                    break
                                elif elem.name == "small":
                                    details_parts.append(elem.text.strip())
                            
                            if not authors_text:
                                authors_text = " ".join(authors_parts).replace("  ", " ").strip()
                            details_text = result_title_div.get_text(separator="\n", strip=True)
                            details_text = "\n".join(details_text.splitlines()[1:]).strip()

                        result_content_div = best_match.find('div', class_='resultcontentcolumn')

                        if result_content_div:
                            ep_name = ""
                            ep_time = None

                            ep_span = result_content_div.find('span', class_='subtext', string="EP")
                            if ep_span:
                                ep_name = ep_span.find_next('strong').next_sibling.strip()
                                ep_name = f"Название эпизода: {ep_name}"

                            subtext_spans = result_content_div.find_all('span', class_='subtext')
                            for span in subtext_spans:
                                if "Est Time:" in span.get_text():
                                    ep_time = span.get_text().replace("Est Time:", "").strip()
                                    ep_time = f"Таймметка скриншота в эпизоде: {ep_time}"
                                    break

                            dA_id_link = result_content_div.find('a', href=True)
                            if dA_id_link and "deviantart" in dA_id_link['href']:
                                dA_id = dA_id_link['href']
                            pixiv_id_link = result_content_div.find('a', href=True)
                            if pixiv_id_link and "pixiv" in pixiv_id_link['href']:
                                pixiv_id = pixiv_id_link['href']   
                            twitter_id_link = result_content_div.find('a', href=True)
                            if twitter_id_link and "twitter.com" in twitter_id_link['href']: 
                                twitter_id = twitter_id_link['href']  # Формируем строку в нужном формате
                            else:
                                twitter_id = None                                              

                            full_author_text = ""
                            author_tag = result_content_div.find('strong', string=lambda text: text.strip() == "Author:")
                            if author_tag:
                                author_link_tag = author_tag.find_next('a', class_='linkify')
                                if author_link_tag:
                                    author_name = author_link_tag.text.strip()
                                    author_url = author_link_tag['href']
                                    full_author_text = f"{author_name} - {author_url}"

                            result_miscinfo_div = best_match.find('div', class_='resultmiscinfo')
                            external_links = [a['href'] for a in result_miscinfo_div.find_all('a', href=True)] if result_miscinfo_div else []

                            jp_name_div = result_content_div.find('span', class_='subtext', string="JP")
                            jp_name = jp_name_div.find_next_sibling(text=True).strip() if jp_name_div else None

                        return authors_text, external_links, jp_name, details_text, ep_name, ep_time, dA_id, full_author_text, pixiv_id, twitter_id
                    else:
                        return None, [], None, None, None, None, None, None, None, None
                else:
                    logging.error(f"Ошибка {response.status}: {await response.text()}")
                    return None, [], None, None, None, None, None, None, None

async def plants_upload_image(file_path: str) -> str:
    try:
        # Сначала Uploadcare (таймаут 8 сек)
        return await asyncio.wait_for(upload_uploadcare(file_path), timeout=8)
    except Exception as e:
        print(f"Ошибка при загрузке на Uploadcare: {e}. Переход к ImgBB.")
        try:
            return await asyncio.wait_for(upload_image_to_imgbb(file_path), timeout=5)
        except asyncio.TimeoutError:
            print("Таймаут при загрузке на ImgBB. Переход к Catbox.")
            try:
                return await upload_catbox(file_path)
            except Exception as e:
                print(f"Ошибка при загрузке на Catbox: {e}. Переход к FreeImage.")
                return await upload_free_image(file_path)
        except Exception as e:
            print(f"Ошибка при загрузке на ImgBB: {e}. Переход к Catbox.")
            try:
                return await upload_catbox(file_path)
            except Exception as catbox_error:
                print(f"Ошибка при загрузке на Catbox: {catbox_error}. Переход к FreeImage.")
                return await upload_free_image(file_path)

UPLOADCARE_PUBLIC_KEY = "dfb67a63bf689bd1e116"  # ⚠️ сюда вставь свой ключ

async def upload_uploadcare(file_path: str) -> str:
    """
    Загрузка изображения на Uploadcare.
    Возвращает прямую ссылку на файл.
    """
    url = "https://upload.uploadcare.com/base/"
    try:
        async with aiohttp.ClientSession() as session:
            with open(file_path, "rb") as f:
                data = aiohttp.FormData()
                data.add_field("UPLOADCARE_PUB_KEY", UPLOADCARE_PUBLIC_KEY)
                data.add_field("UPLOADCARE_STORE", "1")  # сохранять в хранилище
                data.add_field("file", f, filename=os.path.basename(file_path))

                async with session.post(url, data=data, timeout=10) as resp:
                    if resp.status != 200:
                        raise Exception(f"Uploadcare вернул {resp.status}")
                    result = await resp.json()
                    file_id = result.get("file")
                    if not file_id:
                        raise Exception(f"Uploadcare не вернул file_id: {result}")
                    return f"https://ucarecdn.com/{file_id}/"
    except Exception as e:
        raise Exception(f"Ошибка Uploadcare: {e}")



async def second_upload_image(file_path: str) -> str:
    try:
        # Попытка загрузки на Catbox с таймаутом 5 секунд
        return await asyncio.wait_for(upload_catbox(file_path), timeout=5)
    except asyncio.TimeoutError:
        print("Таймаут при загрузке на Catbox. Переход к ImgBB.")
        try:
            return await upload_image_to_imgbb(file_path)
        except Exception as e:
            print(f"Ошибка при загрузке на ImgBB: {e}. Переход к FreeImage.")
            return await upload_free_image(file_path)
    except Exception as e:
        print(f"Ошибка при загрузке на Catbox: {e}. Переход к ImgBB.")
        try:
            return await upload_image_to_imgbb(file_path)
        except Exception as imgbb_error:
            print(f"Ошибка при загрузке на ImgBB: {imgbb_error}. Переход к FreeImage.")
            return await upload_free_image(file_path)

# Функция для загрузки на Catbox
async def upload_catbox(file_path: str) -> str:
    async with aiohttp.ClientSession() as session:
        with open(file_path, 'rb') as f:
            form = aiohttp.FormData()
            form.add_field('reqtype', 'fileupload')
            form.add_field('fileToUpload', f)
            form.add_field('userhash', '1f68d2a125c66f6ab79a4f89c')  # Замените на ваш реальный userhash
            async with session.post('https://catbox.moe/user/api.php', data=form) as response:
                if response.status == 200:
                    return await response.text()  # возвращает URL загруженного файла
                else:
                    logging.info(f"Ошибка загрузки на Catbox: {response.status}")                    
                    raise Exception(f"Ошибка загрузки на Catbox: {response.status}")


# Функция для загрузки на FreeImage
async def upload_free_image(file_path: str) -> str:
    async with aiohttp.ClientSession() as session:
        with open(file_path, 'rb') as f:  # Открываем файл заново
            form = aiohttp.FormData()
            form.add_field('key', '6d207e02198a847aa98d0a2a901485a5')  # Ваш API ключ для freeimage.host
            form.add_field('action', 'upload')
            form.add_field('source', f)  # Используем файл для загрузки
            async with session.post('https://freeimage.host/api/1/upload', data=form) as free_image_response:
                if free_image_response.status == 200:
                    response_json = await free_image_response.json()
                    return response_json['image']['url']  # Проверьте правильность пути к URL в ответе
                else:
                    raise Exception(f"Ошибка загрузки на Free Image Hosting: {free_image_response.status}")




async def parse_yandex_results(img_url):
    search_url = f"https://yandex.ru/images/search?source=collections&rpt=imageview&url={img_url}"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'lxml')
    
    similar_images = soup.find_all('li', class_='cbir-similar__thumb')
    result_links = []
    for i in similar_images:
        result_links.append(f"https://yandex.ru{i.find('a').get('href')}")
    
    return result_links


async def ai_or_not(update: Update, context: CallbackContext):
    """Проверяет, сгенерировано ли изображение ИИ, используя сохранённые байты"""
    image_bytes = context.user_data.get("image_bytes")

    if image_bytes is None:
        await update.callback_query.answer("Изображение не найдено.")
        return

    api_user = '1334786424'
    api_secret = 'HaC88eFy4NLhyo86Md9aTKkkKaQyZeEU'

    keyboard = [
        [InlineKeyboardButton("Sightengine", url="https://sightengine.com/detect-ai-generated-images")],
        [InlineKeyboardButton("Illuminarty AI", url="https://app.illuminarty.ai/#/")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    temp_file = None
    try:
        # ✅ Сохраняем image_bytes во временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            temp_file = tmp.name
            tmp.write(image_bytes)

        # ✅ Отправляем изображение на анализ в Sightengine
        data = {
            'models': 'genai',
            'api_user': api_user,
            'api_secret': api_secret
        }

        async with aiohttp.ClientSession() as session:
            for attempt in range(5):
                with open(temp_file, 'rb') as f:
                    form = aiohttp.FormData()
                    for k, v in data.items():
                        form.add_field(k, v)
                    form.add_field('media', f, filename=os.path.basename(temp_file))

                    async with session.post('https://api.sightengine.com/1.0/check.json', data=form) as response:
                        if response.status == 200:
                            output = await response.json()
                            ai_generated_score = output.get('type', {}).get('ai_generated', 0)

                            await update.callback_query.answer()
                            await update.callback_query.message.reply_text(
                                f"Изображение сгенерировано АИ с вероятностью: {ai_generated_score * 100:.2f}%\n\n"
                                "Вы можете прислать другое изображение для проверки, либо проверить самостоятельно:",
                                reply_markup=reply_markup
                            )
                            return

                        elif response.status == 429:
                            logger.warning("Лимит запросов к API Sightengine. Повтор через 5 секунд.")
                            await asyncio.sleep(5)
                        else:
                            err_text = await response.text()
                            logger.info(f"Ошибка API Sightengine: {response.status} - {err_text}")
                            await update.callback_query.message.reply_text(
                                "Не удалось определить вероятность. Попробуйте позже или вручную:",
                                reply_markup=reply_markup
                            )
                            return

        await update.callback_query.answer("Не удалось обработать изображение после нескольких попыток.")

    except Exception as e:
        logger.exception(f"Ошибка при анализе изображения: {e}")
        await update.callback_query.message.reply_text(
            "Произошла ошибка при анализе изображения. Попробуйте позже.",
            reply_markup=reply_markup
        )

    finally:
        # ✅ Удаляем временный файл
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception as e:
                logger.warning(f"Не удалось удалить временный файл {temp_file}: {e}")


async def handle_file(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id

    # Проверка, если пользователь находится в режиме поиска
    if user_id in is_search_mode and is_search_mode[user_id]:
        if update.message.photo:
            file = await update.message.photo[-1].get_file()
            image_path = 'temp_image.jpg'
            await file.download_to_drive(image_path)
            # Здесь логика для поиска по изображению
            return ASKING_FOR_FILE
        elif update.message.document:
            if update.message.document.mime_type.startswith('image/'):
                file = await update.message.document.get_file()
                image_path = 'temp_image.jpg'
                await file.download_to_drive(image_path)
                # Логика для обработки документов
                return ASKING_FOR_FILE
            else:
                await update.message.reply_text("Пожалуйста, отправьте изображение для поиска источников.")
                return ASKING_FOR_FILE
        else:
            await update.message.reply_text("Пожалуйста, отправьте изображение для поиска источников.")
            return ASKING_FOR_FILE
    
    # Проверка, если пользователь находится в режиме OCR
    if user_id in is_ocr_mode and is_ocr_mode[user_id]:
        if update.message.photo:
            file = await update.message.photo[-1].get_file()
            image_path = 'temp_image.jpg'
            await file.download_to_drive(image_path)
            # Логика для OCR-обработки
            return ASKING_FOR_OCR
        elif update.message.document:
            if update.message.document.mime_type.startswith('image/'):
                file = await update.message.document.get_file()
                image_path = 'temp_image.jpg'
                await file.download_to_drive(image_path)
                return ASKING_FOR_OCR
            else:
                await update.message.reply_text("Пожалуйста, отправьте изображение для OCR.")
                return ASKING_FOR_OCR
        else:
            await update.message.reply_text("Пожалуйста, отправьте изображение для OCR.")
            return ASKING_FOR_OCR


    if user_id in is_gpt_mode and is_gpt_mode[user_id]:
        if update.message.text:
            # Обрабатываем текст сообщения через GPT
            user_message = update.message.text
            response = generate_gemini_response(user_id, query=user_message)
            await update.message.reply_text(response)
            return RUNNING_GPT_MODE
        elif update.message.photo or update.message.document:
            await update.message.reply_text("В режиме GPT поддерживается только текстовый ввод.")
            return RUNNING_GPT_MODE            

    if user_id in is_role_mode and is_role_mode[user_id]:
        if update.message.text:
            # Обрабатываем текст сообщения через GPT
            user_message = update.message.text
            response = generate_gemini_response(user_id, query=user_message)
            await update.message.reply_text(response)
            return RUNNING_GPT_MODE
        elif update.message.photo or update.message.document:
            await update.message.reply_text("В режиме GPT поддерживается только текстовый ввод.")
            return RUNNING_GPT_MODE 

    if user_id in is_asking_mode and is_asking_mode[user_id]:
        if update.message.text:
            # Обрабатываем текст сообщения через GPT
            user_message = update.message.text
            response = generate_gemini_response(user_id, query=user_message)
            await update.message.reply_text(response)
            return ASKING_FOR_FOLLOWUP
        elif update.message.photo or update.message.document:
            await update.message.reply_text("В режиме GPT поддерживается только текстовый ввод.")
            return ASKING_FOR_FOLLOWUP

    # Если пользователь отправил команду /restart, сбрасываем состояние
    if update.message.text == "/restart":
        return await restart(update, context)

    await update.message.reply_text("Пожалуйста, отправьте файл документом или изображение.")
    return ASKING_FOR_FILE

async def finish_search(update: Update, context: CallbackContext) -> int:
    # Проверяем, вызвана ли функция через кнопку или командой
    if update.callback_query:
        query = update.callback_query
        user_id = query.from_user.id
        await query.answer()  # Отвечаем на запрос, чтобы убрать индикатор загрузки на кнопке
        await query.edit_message_text(
            "Вы вышли из режима поиска и вернулись к основным функциям бота",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎨 Найти источник или проверить на ИИ 🎨", callback_data='start_search')],
                [InlineKeyboardButton("🌱 Распознать(растение, грибы, текст) 🌱", callback_data='start_ocr')],
                [InlineKeyboardButton("🦊 Поговорить с ботом 🦊", callback_data='run_gpt')],
                [InlineKeyboardButton("‼️ Полный сброс процесса ‼️", callback_data='restart')]
            ])
        )
    else:
        # Если вызов произошел через команду
        user_id = update.message.from_user.id
        await update.message.reply_text(
            "Вы вышли из режима поиска и вернулись к основным функциям бота",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎨 Найти источник или проверить на ИИ 🎨", callback_data='start_search')],
                [InlineKeyboardButton("🌱 Распознать(растение, грибы, текст) 🌱", callback_data='start_ocr')],
                [InlineKeyboardButton("🦊 Поговорить с ботом 🦊", callback_data='run_gpt')],
                [InlineKeyboardButton("‼️ Полный сброс процесса ‼️", callback_data='restart')]
            ])
        )

    is_search_mode[user_id] = False  # Выключаем режим поиска
    return ConversationHandler.END

# Основная логика обработчика сообщений
async def main_logic(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id

    # Если пользователь находится в режиме поиска, игнорируем основную логику
    if is_search_mode.get(user_id, False):
        return

    # Если пользователь находится в режиме OCR, игнорируем основную логику
    if is_ocr_mode.get(user_id, False):
        return ASKING_FOR_OCR

    if is_gpt_mode.get(user_id, False):
        return RUNNING_GPT_MODE        

    if is_role_mode.get(user_id, False):
        return ASKING_FOR_ROLE 

    if is_asking_mode.get(user_id, False):
        return ASKING_FOR_FOLLOWUP


    # Основная логика обработки сообщений
    await update.message.reply_text("Обрабатываем сообщение в основной логике.")
    return ConversationHandler.END

# Добавим функцию для обработки неизвестных сообщений в режиме поиска
async def unknown_search_message(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Пожалуйста, отправьте фото или документ.")
    return ASKING_FOR_FILE

async def restart(update: Update, context: CallbackContext) -> int:
    # === Определяем пользователя и сообщение для ответа ===
    user = update.effective_user
    if not user:
        return ConversationHandler.END

    user_id = user.id

    if update.message:
        message_to_reply = update.message
    elif update.callback_query:
        await update.callback_query.answer()
        message_to_reply = update.callback_query.message
    else:
        return ConversationHandler.END

    # === 1. Очищаем PTB user_data (ПЕРСОНАЛЬНО) ===
    context.user_data.clear()

    # === 2. Очищаем все кастомные хранилища по user_id ===
    storages = (
        user_data,
        is_search_mode,
        is_ocr_mode,
        is_gpt_mode,
        is_asking_mode,
        is_role_mode,
        waiting_for_forward,
        waiting_for_caption,
        waiting_for_vk,
        waiting_for_twitter,
        waiting_for_coordinates,
    )

    for storage in storages:
        storage.pop(user_id, None)

    logger.info(f"User {user_id} restarted the process.")

    # === 3. Очищаем папку twitter_media ===
    twitter_media_path = os.path.join(os.getcwd(), "twitter_media")
    if os.path.exists(twitter_media_path):
        try:
            shutil.rmtree(twitter_media_path)
            logger.info("Директория twitter_media успешно очищена.")
        except Exception as e:
            logger.error(f"Ошибка при удалении twitter_media: {e}")

    # === 4. Кнопки стартового меню ===
    keyboard = [
        [InlineKeyboardButton("🗂 Папки с сохранёнными постами 🗂", callback_data="scheduled_by_tag")],
        [InlineKeyboardButton("🎨 Найти источник или проверить на ИИ 🎨", callback_data='start_search')],
        [InlineKeyboardButton("🌱 Растения, грибы, текст, поиск 🌱", callback_data='start_ocr')],
        [InlineKeyboardButton("🦊 Поговорить с ботом 🦊", callback_data='run_gpt')],
        [InlineKeyboardButton("📖 Посмотреть помощь", callback_data="osnhelp")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    random_kaomoji = random.choice(KAOMOJI_LIST)

    await message_to_reply.reply_text(
        f'🌠Привет <code>{random_kaomoji}</code>\n\n'
        f'<b>Если вам нужно что-то распознать или найти отзывы по фото — просто пришлите его.</b>\n\n'
        'Если вы хотите прислать предложку или сделать пост для соцсети, '
        'сначала отправьте текст подписи. Если текста нет — напишите "нет".\n\n'
        'Либо выберите режим работы ниже:\n\n',
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    # === 5. Начальное состояние после рестарта ===
    user_data[user_id] = {'status': 'awaiting_artist_link'}

    return ASKING_FOR_ARTIST_LINK



async def rerestart(update: Update, context: CallbackContext) -> int:
    # Проверка типа события
    if update.message:
        user_id = update.message.from_user.id
        message_to_reply = update.message
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
        message_to_reply = update.callback_query.message
    else:
        return ConversationHandler.END

    # Удаляем все данные пользователя
    if user_id in user_data:
        del user_data[user_id]  # Удаляем старые данные пользователя  

    if user_id in is_search_mode:
        del is_search_mode[user_id]  # Выключаем режим поиска, если он включен

    if user_id in is_ocr_mode:
        del is_ocr_mode[user_id]

    if user_id in is_gpt_mode:
        del is_gpt_mode[user_id]

    if user_id in is_asking_mode:
        del is_asking_mode[user_id]

    if user_id in is_role_mode:
        del is_role_mode[user_id] 

    if user_id in waiting_for_forward:
        del waiting_for_forward[user_id] 

    if user_id in waiting_for_vk:
        del waiting_for_vk[user_id] 
    if user_id in waiting_for_twitter:
        del waiting_for_twitter[user_id]  
    if user_id in waiting_for_coordinates:
        del waiting_for_coordinates[user_id]                
    logger.info(f"User {user_id} restarted the process.") 
    # Очищаем папку twitter_media
    twitter_media_path = os.path.join(os.getcwd(), "twitter_media")
    if os.path.exists(twitter_media_path):
        try:
            shutil.rmtree(twitter_media_path)
            logger.info("Директория twitter_media успешно очищена.")
        except Exception as e:
            logger.error(f"Ошибка при удалении twitter_media: {e}")
    # Отправляем сообщение с кнопками
    keyboard = [
        [InlineKeyboardButton("🗂 Папки с сохранёнными постами 🗂", callback_data="scheduled_by_tag")],
        [InlineKeyboardButton("🎨 Найти источник или проверить на ИИ 🎨", callback_data='start_search')],
        [InlineKeyboardButton("🌱 Растения, грибы, текст, поиск 🌱", callback_data='start_ocr')],            
        [InlineKeyboardButton("🦊 Поговорить с ботом 🦊", callback_data='run_gpt')],
        [InlineKeyboardButton("📖 Посмотреть помощь", callback_data="osnhelp")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message_to_reply.reply_text(
        '✅Ваш пост успешно создан и бот перезапущен, теперь ждёт ваших навых постов! \n(=^・ェ・^=)\n\n'
        'Либо же вы можете отредактировать, сохранить в папку или опубликовать в соцсети созданный только что или один из созданных ранее постов. \n\nДля начала создания нового поста пришлите текст который будет служить подписью. Если подпись не нужна то пришлите "нет"\n\n',
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    # Устанавливаем новое состояние после перезапуска
    user_data[user_id] = {'status': 'awaiting_artist_link'}
    
    return ASKING_FOR_ARTIST_LINK


async def start_ocr(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    if query:
        await query.answer()  # Гасим нажатие кнопки

    is_ocr_mode[query.from_user.id] = True    
    is_search_mode[query.from_user.id] = False
    is_gpt_mode[query.from_user.id] = False

    # Создаем кнопку "Отменить поиск"
    keyboard = [
        [InlineKeyboardButton("🪴 Мои растения 🪴", callback_data='myplants')],
        [InlineKeyboardButton("🗺 Карта растений 🗺", callback_data='show_map')],
        [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Если это вызвано через callback_query (нажатие кнопки), то редактируем сообщение
    if query:
        await query.edit_message_text(
            text="Пожалуйста, отправьте изображение для поиска отзывов, распознавания, размещения на карту или занесения в список ваших растений. Лучше отправлять сжатые изображения, тогда бот работает быстрее. Оригиналы в виде файлов отправляйте только по необходимости (мелкий текст, мелкие растения и тд)\n\n Так же вы можете посмотреть ранее добавленные растения по кнопкам ниже",
            reply_markup=reply_markup
        )
    else:
        # Если вызвано напрямую (не через кнопку), отправляем новое сообщение
        await update.message.reply_text(
            text="Пожалуйста, отправьте изображение для поиска отзывов, распознавания, размещения на карту или занесения в список ваших растений. Лучше отправлять сжатые изображения, тогда бот работает быстрее. Оригиналы в виде файлов отправляйте только по необходимости (мелкий текст, мелкие растения и тд)\n\n Так же вы можете посмотреть ранее добавленные растения по кнопкам ниже",            reply_markup=reply_markup
        )

    return ASKING_FOR_OCR

async def finish_ocr(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("🎨 Найти источник или проверить на ИИ 🎨", callback_data='start_search')],
        [InlineKeyboardButton("🌱 Растения, грибы, текст 🌱", callback_data='start_ocr')],
        [InlineKeyboardButton("🦊 Поговорить с ботом 🦊", callback_data='run_gpt')],
        [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]

    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:  # Если функция вызвана через нажатие кнопки
        query = update.callback_query
        user_id = query.from_user.id
        is_ocr_mode[user_id] = False  # Выключаем режим поиска
        is_search_mode[user_id] = False
        is_gpt_mode[user_id] = False
        is_role_mode[user_id] = False
        is_asking_mode[user_id] = False  # Выключаем режим поиска
        
        await query.answer()  # Отвечаем на запрос, чтобы убрать индикатор загрузки на кнопке
        await query.edit_message_text(
            "Вы вышли из режима распознавания и вернулись к основным функциям бота. Вы можете продолжить заполнять статью на том моменте на котором остановились, либо воспользоваться одной из кнопок:", 
            reply_markup=reply_markup  # Добавляем кнопки
        )
    
    elif update.message:  # Если функция вызвана через команду /fin_ocr
        user_id = update.message.from_user.id
        is_ocr_mode[user_id] = False  # Выключаем режим поиска
        is_search_mode[user_id] = False
        is_gpt_mode[user_id] = False
        is_role_mode[user_id] = False
        is_asking_mode[user_id] = False  # Выключаем режим поиска
        
        await update.message.reply_text(
            "Вы вышли из режима распознавания и вернулись к основным функциям бота. Вы можете продолжить заполнять статью на том моменте на котором остановились, либо воспользоваться одной из кнопок:", 
            reply_markup=reply_markup  # Добавляем кнопки
        )

    return ConversationHandler.END
    
# Добавим функцию для обработки неизвестных сообщений в режиме поиска
async def unknown_ocr_message(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Пожалуйста, отправьте фото или документ.")
    return ASKING_FOR_OCR

# Обработчик нажатия на кнопку "Распознать текст"
async def ocr_space_with_url(img_url, api_key):
    ocr_url = "https://api.ocr.space/parse/imageurl"

    async with aiohttp.ClientSession() as session:
        params = {
            'apikey': api_key,
            'url': img_url,
            'language': 'rus',  # Указываем язык
            'isOverlayRequired': 'False',  # Нужно ли накладывать текст на изображение
            'detectOrientation': 'True',  # Определять ориентацию текста
            'scale': 'True'  # Масштабировать изображение
        }

        async with session.get(ocr_url, params=params) as response:
            if response.status == 200:
                result = await response.json()
                try:
                    return result["ParsedResults"][0]["ParsedText"]
                except (KeyError, IndexError):
                    return "Текст не был распознан."
            else:
                return f"Ошибка API OCR.space: {response.status}"


# Измененный обработчик кнопки для OCR
async def button_ocr(update, context):
    query = update.callback_query
    await query.answer()

    # Получаем URL изображения с Catbox
    img_url = context.user_data.get('img_url')

    if query.data == 'recognize_text':
        if img_url:
            # Вызов функции для распознавания текста через Google Cloud Vision API с использованием URL
            api_key = 'K86410931988957'  # Ваш ключ API
            recognized_text = await ocr_space_with_url(img_url, api_key)
            keyboard = [
                [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # Отправляем распознанный текст пользователю
            await query.message.reply_text(
                f"Распознанный текст:\n{recognized_text}\n\nОтправьте следующее изображение для распознавания либо нажмите кнопку ниже",
                reply_markup=reply_markup  # Добавляем кнопку к последнему сообщению
            )
        else:
            # Отправляем сообщение об ошибке с кнопкой
            await query.message.reply_text(
                "URL изображения не найден. Попробуйте ещё раз.",
                reply_markup=reply_markup  # Добавляем кнопку к этому сообщению
            )

    elif query.data == 'recognize_plant':
        await recognize_plant(update, context)  # Вызов функции для распознавания растения
    else:
        await query.message.reply_text("Неизвестная команда.")





from pathlib import Path

def sync_download_image(url, file_path):
    response = requests.get(url)
    response.raise_for_status()
    with open(file_path, 'wb') as f:
        f.write(response.content)

def sync_post_image(api_url, image_bytes: BytesIO):
    files = {
        'images': ('image.jpg', image_bytes, 'image/jpeg')
    }
    data = {
        'organs': 'auto'
    }
    response = requests.post(api_url, files=files, data=data)
    return response

async def recognize_plant(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.callback_query.from_user.id
    image_bytes = context.user_data.get('image_bytes')
    buffer = BytesIO(image_bytes)
    buffer.seek(0)
    encoded_image = base64.b64encode(buffer.read()).decode('utf-8')
    if not image_bytes:
        await update.callback_query.answer("Сначала загрузите изображение.")
        return

    await update.callback_query.message.reply_text("Распознаю растение...")

    api_key = "2b10C744schFhHigMMjMsDmV"
    project = "all"
    lang = "ru"
    include_related_images = "true"
    no_reject = "false"
    nb_results = 3
    type_param = "kt"

    api_url = (
        f"https://my-api.plantnet.org/v2/identify/{project}"
        f"?include-related-images={include_related_images}"
        f"&no-reject={no_reject}"
        f"&nb-results={nb_results}"
        f"&lang={lang}"
        f"&type={type_param}"
        f"&api-key={api_key}"
    )

    try:
        # Отправка изображения
        payload = {'image': encoded_image}

        # Отправка JSON-объекта на ваш Google Apps Script
        response = requests.post(
            'https://script.google.com/macros/s/AKfycbxsLoPIT3xgg2NrR6q212abtI32pstNrG0v9-OPv7IsdT0Ky-MJqAULed1xM6A2uYwhfw/exec',
            json=payload
        )

        if response.status_code == 200:
            prediction = response.json()

            if prediction.get('results'):
                keyboard = []
                for idx, plant in enumerate(prediction['results'][:3]):
                    species = plant.get('species', {})
                    scientific_name = species.get('scientificNameWithoutAuthor', 'Неизвестное растение')
                    common_names = species.get('commonNames', [])
                    common_name_str = ', '.join(common_names) if common_names else 'Название отсутствует'
                    similarity_score = plant.get('score', 0) * 100
                    similarity_text = f"{similarity_score:.2f}%"

                    images = plant.get('images', [])
                    context.user_data[f"plant_{idx}"] = {
                        "scientific_name": scientific_name,
                        "common_names": common_name_str,
                        "images": images
                    }

                    keyboard.append([InlineKeyboardButton(
                        text=f"{similarity_text} - {scientific_name} ({common_name_str})",
                        callback_data=f"plant_{idx}"
                    )])

                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.callback_query.message.reply_text(
                    "Выберите одно из предложенных растений:",
                    reply_markup=reply_markup
                )
            else:
                await update.callback_query.message.reply_text("Растение не найдено.")
        else:
            await update.callback_query.message.reply_text(
                "Ошибка при распознавании растения. Возможно, это не растение, или попробуйте другое фото."
            )

    except requests.RequestException:
        await update.callback_query.message.reply_text("Не удалось отправить изображение или ошибка API.")
    except Exception as e:
        await update.callback_query.message.reply_text(f"Произошла ошибка: {str(e)}")
    finally:
        # Очистка изображения из user_data
        context.user_data.pop('image_bytes', None)

API_Pl_KEY = "2b10C744schFhHigMMjMsDmV"
PROJECT = "all"
API_ENDPOINT = f"https://my-api.plantnet.org/v2/identify/{PROJECT}?api-key={API_Pl_KEY}"

async def recognize_test_plant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверка, что команда пришла в ответ на сообщение
    if not update.message.reply_to_message:
        await update.message.reply_text("Пожалуйста, используйте команду в ответ на сообщение с изображением.")
        return

    # Получение файла из сообщения
    photo = update.message.reply_to_message.photo
    doc = update.message.reply_to_message.document

    if photo:
        # Берем наибольшее изображение
        file = await photo[-1].get_file()
    elif doc and doc.mime_type and doc.mime_type.startswith("image/"):
        file = await doc.get_file()
    else:
        await update.message.reply_text("Ответьте на изображение (фото или документ) для распознавания.")
        return

    logger.info("Загружаю изображение...")
    image_bytes = BytesIO()
    await file.download_to_memory(out=image_bytes)
    image_bytes.seek(0)

    # Подготовка запроса к PlantNet
    files = [
        ('images', ('image.jpg', image_bytes, 'image/jpeg')),
    ]
    data = {
        'organs': ['leaf']  # Можно изменить на flower, fruit и т.п.
    }

    try:
        logger.info("Отправка изображения в PlantNet...")
        response = requests.post(API_ENDPOINT, files=files, data=data)
        response.raise_for_status()
        json_result = response.json()

        logger.info("Ответ получен. Отправка пользователю...")
        await update.message.reply_text(json.dumps(json_result, indent=2)[:4000])
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе: {e}")
        await update.message.reply_text("Ошибка при отправке запроса к PlantNet.")




# Инициализация Wikipedia API с User-Agent
user_agent = "MyPlantBot/1.0 sylar1907942@gmail.com)"
wiki_wiki = wikipediaapi.Wikipedia(language='ru', user_agent=user_agent)  


wikipedia.set_lang('ru')  # Установите язык на русский

wikipedia.set_lang('ru')  # Установите язык на русский
async def get_wikipedia_link(scientific_name: str, common_names: list) -> tuple:
    return await asyncio.to_thread(_sync_get_wikipedia_link, scientific_name, common_names)

def _sync_get_wikipedia_link(scientific_name: str, common_names: list) -> tuple:
    try:
        # Выполняем поиск по научному названию
        search_results = wikipedia.search(scientific_name)

        if search_results:
            for article_title in search_results:
                page = wiki_wiki.page(article_title)
                if page.exists():
                    categories = page.categories
                    if any('растения' in cat.lower() for cat in categories):
                        return (f"https://ru.wikipedia.org/wiki/{article_title.replace(' ', '_')}", article_title)

        # Ищем по общим названиям
        for name in common_names:
            search_results = wikipedia.search(name)
            if search_results:
                for article_title in search_results:
                    page = wiki_wiki.page(article_title)
                    if page.exists():
                        categories = page.categories
                        if any('растения' in cat.lower() for cat in categories):
                            return (f"https://ru.wikipedia.org/wiki/{article_title.replace(' ', '_')}", article_title)

    except Exception as e:
        logger.error(f"Error fetching Wikipedia link: {e}")

    return (None, None)

import functools

async def get_wikipedia_summary(article_title: str) -> str:
    try:
        summary = await asyncio.to_thread(functools.partial(wikipedia.summary, article_title, sentences=12))
        return summary
    except Exception as e:
        logger.error(f"Error fetching summary for {article_title}: {e}")
        return "Краткое описание недоступно\n\n"    






def escape_markdown_v2(text: str) -> str:
    # Проверка на наличие экранирования и удаление, если оно присутствует
    if re.search(r'\\[\\\*\[\]\(\)\{\}\.\!\?\-\#\@\&\$\%\^\&\+\=\~]', text):
        # Убираем экранирование у всех специальных символов Markdown
        text = re.sub(r'\\([\\\*\[\]\(\)\{\}\.\!\?\-\#\@\&\$\%\^\&\+\=\~])', r'\1', text)

    # Временная замена ** на |TEMP| без экранирования
    text = re.sub(r'\*\*(.*?)\*\*', r'|TEMP|\1|TEMP|', text)

    # Временная замена ``` на |CODE_BLOCK| для исключения из экранирования
    text = text.replace('```', '|CODE_BLOCK|')

    # Временная замена ` на |INLINE_CODE| для исключения из экранирования
    text = text.replace('`', '|INLINE_CODE|')

    # Экранируем все специальные символы
    text = re.sub(r'(?<!\\)([\\\*\[\]\(\)\{\}\.\!\?\-\#\@\&\$\%\^\&\+\=\~])', r'\\\1', text)

    # Восстанавливаем |TEMP| обратно на *
    text = text.replace('|TEMP|', '*')

    # Восстанавливаем |CODE_BLOCK| обратно на ```
    text = text.replace('|CODE_BLOCK|', '```')

    # Восстанавливаем |INLINE_CODE| обратно на `
    text = text.replace('|INLINE_CODE|', '`')

    # Экранируем символ |
    text = re.sub(r'(?<!\\)\|', r'\\|', text)

    # Экранируем символ _ везде, кроме конца строки
    text = re.sub(r'(?<!\\)_(?!$)', r'\\_', text)

    return text











async def analyze_ingredients(update, context):
    """
    Обрабатывает запрос на анализ состава по уже скачанному изображению.
    """
    user_id = update.effective_user.id
    image_bytes = context.user_data.get('image_bytes')

    # Проверяем наличие изображения
    if not image_bytes:
        await update.callback_query.answer("Изображение не найдено.")
        return

    # Отправляем предварительное сообщение
    processing_message = await update.callback_query.message.reply_text("Анализирую состав, ожидайте...")
    query = update.callback_query
    if query:
        await query.answer()  # Гасим нажатие кнопки

    async def process():
        try:
            # Открываем картинку напрямую из памяти (уже скачанный файл)
            image = Image.open(BytesIO(image_bytes))
            image.load()

            # Генерация ответа через Gemini для анализа состава
            response_text = await response_ingredients(
                user_id,
                image=image
            )
            
            # Разбиваем текст с учетом HTML-тегов.
            # Так как caption не используется, первый аргумент-смещение равен 0.
            _, message_parts = split_html_text(response_text, 0, 4096)
            text_parts = message_parts

            # Клавиатура для возврата в главное меню
            keyboard = [
                [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Отправляем все части ответа
            for i, part in enumerate(text_parts):
                safe_part = sanitize_html(part)  # Фильтрация HTML

                if i == 0:  # Первая часть ответа заменяет сообщение "Анализирую состав..."
                    if len(text_parts) == 1:
                        # Если ответ состоит из одной части, сразу добавляем клавиатуру
                        await processing_message.edit_text(
                            safe_part,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                        return  # Завершаем, так как все отправлено
                    else:
                        await processing_message.edit_text(safe_part, parse_mode='HTML')
                
                elif i == len(text_parts) - 1: # Последняя часть получает клавиатуру
                    await update.callback_query.message.reply_text(
                        safe_part,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                else: # Промежуточные части отправляются без клавиатуры
                    await update.callback_query.message.reply_text(safe_part, parse_mode='HTML')

        except Exception as e:
            logging.error(f"Ошибка при анализе состава: {e}")
            try:
                await processing_message.edit_text("Произошла ошибка при обработке вашего запроса.")
            except Exception as edit_error:
                logging.error(f"Не удалось изменить сообщение об ошибке: {edit_error}")

    # Запускаем обработку в фоновой задаче, чтобы не блокировать основной поток
    asyncio.create_task(process())



async def recognize_animal_insect(update, context):
    user_id = update.effective_user.id
    caption = context.user_data.get('img_caption')  # <-- подпись, если есть
    image_bytes = context.user_data.get('image_bytes')  # <-- байты из fast_rec
    img_url = context.user_data.get('img_url')  # fallback

    # Проверяем наличие изображения
    if not image_bytes and not img_url:
        await update.callback_query.answer("Изображение не найдено.")
        return

    processing_message = await update.callback_query.message.reply_text("Распознаю животное/насекомое, ожидайте...")
    query = update.callback_query
    if query:
        await query.answer()  # Гасим нажатие кнопки

    async def process():
        try:
            # Используем уже скачанный файл из памяти
            if image_bytes:
                img_bytes = image_bytes
            else:
                # fallback: скачать по ссылке
                async with aiohttp.ClientSession() as session:
                    async with session.get(img_url) as resp:
                        if resp.status != 200:
                            raise Exception("Не удалось скачать изображение")
                        img_bytes = await resp.read()

            # Открываем картинку из памяти
            image = Image.open(BytesIO(img_bytes))
            image.load()

            # Вызов генерации ответа через нейросеть
            response_text = await response_animal(
                user_id,
                image=image,
                caption=caption if caption else None
            )

            # Разбиваем текст по кускам
            caption_part, message_parts = split_html_text(response_text, 0, 4096)
            text_parts = [caption_part] + message_parts if caption_part else message_parts

            # Клавиатура
            keyboard = [
                [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Отправляем все части
            for i, part in enumerate(text_parts):
                safe_part = sanitize_html(part)

                if i == 0:  # первая часть заменяет "Распознаю..."
                    if len(text_parts) == 1:
                        await processing_message.edit_text(
                            safe_part,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                        return
                    else:
                        await processing_message.edit_text(safe_part, parse_mode='HTML')
                elif i == len(text_parts) - 1:
                    await update.callback_query.message.reply_text(
                        safe_part,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                else:
                    await update.callback_query.message.reply_text(safe_part, parse_mode='HTML')

            await update.callback_query.answer()

        except Exception as e:
            logging.error(f"Ошибка при распознавании животного/насекомого: {e}")
            try:
                await processing_message.edit_text("Произошла ошибка при обработке изображения.")
            except:
                pass

    # Запускаем как фоновую задачу
    asyncio.create_task(process())


async def text_plant_help_with_gpt(update, context):
    user_id = update.effective_user.id
    caption = context.user_data.get('img_caption')  # <-- достаём подпись

    # Проверяем наличие файла
    image_path = 'temp_image.jpg'
    if not os.path.exists(image_path):
        await update.callback_query.answer("Файл изображения не найден. Отправьте фото снова.")
        return

    processing_message = await update.callback_query.message.reply_text("Запрос принят, ожидайте...")
    query = update.callback_query
    if query:
        await query.answer()  # Гасим нажатие кнопки

    async def process():
        try:
            # Загружаем уже сохранённое изображение
            image = Image.open(image_path)
            image.load()

            # Генерация ответа через Gemini
            response_text = await generate_plant_issue_response(
                user_id, 
                image=image, 
                caption=caption if caption else None
            )
            # Разбиваем текст с учетом HTML-тегов, игнорируя caption
            caption_part, message_parts = split_html_text(response_text, 0, 4096)
            text_parts = [caption_part] + message_parts if caption_part else message_parts

            # Клавиатура
            keyboard = [
                [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)


            # Отправляем все части ответа
            for i, part in enumerate(text_parts):
                safe_part = sanitize_html(part)  # <-- фильтрация
                
                if i == 0:  # Первая часть заменяет "Запрос принят..."
                    if len(text_parts) == 1:
                        await processing_message.edit_text(
                            safe_part,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                        return
                    else:
                        await processing_message.edit_text(safe_part, parse_mode='HTML')
                elif i == len(text_parts) - 1:
                    await update.callback_query.message.reply_text(
                        safe_part,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                else:
                    await update.callback_query.message.reply_text(safe_part, parse_mode='HTML')
            await update.callback_query.answer()

        except Exception as e:
            logging.error(f"Ошибка при генерации описания проблемы растения: {e}")
            try:
                await processing_message.edit_text("Произошла ошибка при обработке изображения.")
            except:
                pass



    # Запускаем фоновую задачу
    asyncio.create_task(process())

ALLOWED_TAGS = {
    "b", "strong", "i", "em", "u", "ins", "s", "strike", "del",
    "tg-spoiler", "code", "pre", "a", "blockquote"
}

def sanitize_html(text: str) -> str:
    # Заменяем <br> на перенос строки
    text = text.replace("<br>", "\n")

    # Фильтруем теги
    def repl_tag(match):
        tag = match.group(1).lower()
        if tag.startswith("/"):
            tag = tag[1:]
        if tag in ALLOWED_TAGS:
            return match.group(0)  # оставляем как есть
        return html.escape(match.group(0))  # экранируем, чтобы не ломало парсинг
    
    return re.sub(r"</?([a-zA-Z0-9\-]+)(\s+[^>]*)?>", repl_tag, text)


from tempfile import NamedTemporaryFile
async def mushrooms_gpt(update, context):
    user_id = update.effective_user.id
    img_url = context.user_data.get('img_url')              # для одного фото
    group_images = context.user_data.get('group_images')    # для нескольких фото (список bytes)
    caption = context.user_data.get('img_caption')

    # Если нет ни одного изображения
    if not img_url and not group_images:
        await update.callback_query.answer("Изображение не найдено.")
        return

    processing_message = await update.callback_query.message.reply_text("Запрос принят, ожидайте...")
    query = update.callback_query
    if query:
        await query.answer()  # Гасим нажатие кнопки
    async def process():
        temp_files = []
        try:
            images = []

            # Если у нас группа изображений
            if group_images:
                for idx, img_bytes in enumerate(group_images):
                    with NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                        temp_file.write(img_bytes)
                        temp_file.flush()
                        temp_files.append(temp_file.name)
                        images.append(Image.open(temp_file.name))
            else:
                # Одинарное изображение
                with open("temp_image.jpg", "rb") as f:
                    image = Image.open(f)
                    image.load()
                    images.append(image)
                    temp_files.append("temp_image.jpg")

            # Генерация ответа через Gemini
            response_text = await generate_mushrooms_multi_response(
                user_id=user_id,
                images=images,
                query=caption
            )

            # Разбиваем текст на части
            caption_part, message_parts = split_html_text(response_text, 0, 4096)
            text_parts = [caption_part] + message_parts if caption_part else message_parts

            # Клавиатура
            keyboard = [[InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Отправляем все части ответа
            for i, part in enumerate(text_parts):
                part = sanitize_html(part)  # очистка текста перед отправкой
                if i == 0:
                    if len(text_parts) == 1:
                        await processing_message.edit_text(
                            part,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                        return
                    else:
                        await processing_message.edit_text(part, parse_mode='HTML')
                elif i == len(text_parts) - 1:
                    await update.callback_query.message.reply_text(
                        part, reply_markup=reply_markup, parse_mode='HTML'
                    )
                else:
                    await update.callback_query.message.reply_text(part, parse_mode='HTML')

            await update.callback_query.answer()

        except Exception as e:
            logging.error(f"Ошибка при генерации описания гриба: {e}")
            try:
                await processing_message.edit_text("Произошла ошибка при обработке изображения.")
            except:
                pass
        finally:
            # Удаляем временные файлы
            for path in temp_files:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                        logging.info(f"Удалён временный файл {path}")
                    except Exception as del_e:
                        logging.warning(f"Не удалось удалить {path}: {del_e}")

    asyncio.create_task(process())



async def products_gpt(update, context):
    user_id = update.effective_user.id
    img_url = context.user_data.get('img_url')
    group_images = context.user_data.get('group_images')
    caption = context.user_data.get('img_caption')
    image_path = context.user_data.get('img_path')
    if not img_url and not group_images and not image_path:
        await update.callback_query.answer("Изображение не найдено.")
        return

    processing_message = await update.callback_query.message.reply_text("Запрос принят, ожидайте...")
    query = update.callback_query
    if query:
        await query.answer()

    async def process():
        temp_files = []
        try:
            images = []

            if group_images:
                # Несколько фото
                for idx, img_bytes in enumerate(group_images):
                    with NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                        temp_file.write(img_bytes)
                        temp_file.flush()
                        temp_files.append(temp_file.name)
                        images.append(Image.open(temp_file.name))
            elif image_path:
                # Уже скачанный файл
                image = Image.open(image_path)
                image.load()
                images.append(image)
                temp_files.append(image_path)  # учтем в очистке, если надо
            else:
                # fallback (если всё же нет local_image_path, но есть img_url)
                with open("temp_image.jpg", "rb") as f:
                    image = Image.open(f)
                    image.load()
                    images.append(image)
                    temp_files.append("temp_image.jpg")

            # Генерация ответа через Gemini
            response_text = await generate_products_response(
                user_id=user_id,
                images=images,
                query=caption
            )


            # Разбиваем текст на части
            caption_part, message_parts = split_html_text(response_text, 0, 4096)
            text_parts = [caption_part] + message_parts if caption_part else message_parts

            # Клавиатура
            keyboard = [[InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Отправляем все части ответа
            for i, part in enumerate(text_parts):
                part = sanitize_html(part)  # очистка текста перед отправкой
                if i == 0:
                    if len(text_parts) == 1:
                        await processing_message.edit_text(
                            part,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                        return
                    else:
                        await processing_message.edit_text(part, parse_mode='HTML')
                elif i == len(text_parts) - 1:
                    await update.callback_query.message.reply_text(
                        part, reply_markup=reply_markup, parse_mode='HTML'
                    )
                else:
                    await update.callback_query.message.reply_text(part, parse_mode='HTML')

            await update.callback_query.answer()

        except Exception as e:
            logging.error(f"Ошибка при сравнении продуктов: {e}")
            try:
                await processing_message.edit_text("Произошла ошибка при обработке изображения.")
            except:
                pass
        finally:
            # Удаляем временные файлы
            for path in temp_files:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                        logging.info(f"Удалён временный файл {path}")
                    except Exception as del_e:
                        logging.warning(f"Не удалось удалить {path}: {del_e}")

    asyncio.create_task(process())


async def calories_gpt(update, context):
    user_id = update.effective_user.id
    img_url = context.user_data.get('img_url')              # для одного фото
    group_images = context.user_data.get('group_images')    # для нескольких фото (список bytes)
    caption = context.user_data.get('img_caption')

    # Если нет ни одного изображения
    if not img_url and not group_images:
        await update.callback_query.answer("Изображение не найдено.")
        return

    processing_message = await update.callback_query.message.reply_text("Запрос принят, ожидайте...")
    query = update.callback_query
    if query:
        await query.answer()  # Гасим нажатие кнопки

    async def process():
        temp_files = []
        try:
            images = []

            # Если у нас группа изображений
            if group_images:
                for idx, img_bytes in enumerate(group_images):
                    with NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                        temp_file.write(img_bytes)
                        temp_file.flush()
                        temp_files.append(temp_file.name)
                        images.append(Image.open(temp_file.name))
            else:
                # Используем уже скачанный temp_image.jpg
                image_path = "temp_image.jpg"
                if os.path.exists(image_path):
                    image = Image.open(image_path)
                    image.load()
                    images.append(image)
                    temp_files.append(image_path)
                else:
                    raise FileNotFoundError("Файл temp_image.jpg не найден. Сначала отправьте фото.")

            # Генерация ответа через Gemini
            response_text = await generate_calories_response(
                user_id=user_id,
                images=images,
                query=caption
            )

            # Разбиваем текст на части
            caption_part, message_parts = split_html_text(response_text, 0, 4096)
            text_parts = [caption_part] + message_parts if caption_part else message_parts

            # Клавиатура
            keyboard = [[InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Отправляем все части ответа
            for i, part in enumerate(text_parts):
                part = sanitize_html(part)  # очистка текста перед отправкой
                if i == 0:
                    if len(text_parts) == 1:
                        await processing_message.edit_text(
                            part,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                        return
                    else:
                        await processing_message.edit_text(part, parse_mode='HTML')
                elif i == len(text_parts) - 1:
                    await update.callback_query.message.reply_text(
                        part, reply_markup=reply_markup, parse_mode='HTML'
                    )
                else:
                    await update.callback_query.message.reply_text(part, parse_mode='HTML')

            await update.callback_query.answer()

        except Exception as e:
            logging.error(f"Ошибка при генерации описания гриба: {e}")
            try:
                await processing_message.edit_text("Произошла ошибка при обработке изображения.")
            except:
                pass
        finally:
            # Удаляем временные файлы
            for path in temp_files:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                        logging.info(f"Удалён временный файл {path}")
                    except Exception as del_e:
                        logging.warning(f"Не удалось удалить {path}: {del_e}")

    asyncio.create_task(process())





async def composition_comparison_gpt(update, context):
    user_id = update.effective_user.id
    group_images = context.user_data.get('group_images')    # список байтов изображений
    caption = context.user_data.get('img_caption')

    # Если нет изображений
    if not group_images:
        await update.callback_query.answer("Изображения не найдены.")
        return

    processing_message = await update.callback_query.message.reply_text("Запрос принят, ожидайте...")
    query = update.callback_query
    if query:
        await query.answer()  # Гасим нажатие кнопки

    async def process():
        temp_files = []
        try:
            images = []

            # Обработка группы изображений
            for idx, img_bytes in enumerate(group_images):
                with NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                    temp_file.write(img_bytes)
                    temp_file.flush()
                    temp_files.append(temp_file.name)
                    images.append(Image.open(temp_file.name))

            # Генерация ответа через Gemini (функцию сделай аналогично generate_mushrooms_multi_response)
            response_text = await generate_composition_comparison_response(
                user_id=user_id,
                images=images,
                query=caption
            )

            # Разбиваем текст на части
            caption_part, message_parts = split_html_text(response_text, 0, 4096)
            text_parts = [caption_part] + message_parts if caption_part else message_parts

            # Клавиатура
            keyboard = [[InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Отправляем все части ответа
            for i, part in enumerate(text_parts):
                part = sanitize_html(part)  # очистка текста перед отправкой
                if i == 0:
                    if len(text_parts) == 1:
                        await processing_message.edit_text(
                            part,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                        return
                    else:
                        await processing_message.edit_text(part, parse_mode='HTML')
                elif i == len(text_parts) - 1:
                    await update.callback_query.message.reply_text(
                        part, reply_markup=reply_markup, parse_mode='HTML'
                    )
                else:
                    await update.callback_query.message.reply_text(part, parse_mode='HTML')

            await update.callback_query.answer()

        except Exception as e:
            logging.error(f"Ошибка при сравнении составов: {e}")
            try:
                await processing_message.edit_text("Произошла ошибка при обработке изображений.")
            except:
                pass
        finally:
            # Удаляем временные файлы
            for path in temp_files:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                        logging.info(f"Удалён временный файл {path}")
                    except Exception as del_e:
                        logging.warning(f"Не удалось удалить {path}: {del_e}")

    asyncio.create_task(process())





async def text_rec_with_gpt(update, context):
    user_id = update.effective_user.id
    image_path = context.user_data.get('img_path')  # <-- используем локальный путь

    if not image_path:
        await update.callback_query.answer("Изображение не найдено.")
        return

    waiting_message = await update.callback_query.message.reply_text("Распознаю текст на изображении, подождите...")
    query = update.callback_query
    if query:
        await query.answer()  # Гасим нажатие кнопки

    async def process():
        try:
            # Загружаем уже скачанный файл
            image = Image.open(image_path)
            image.load()
    
            response = await generate_text_rec_response(user_id, image=image, query=None)
    
            if not response:
                response = "Ошибка при распознавании текста."

            context.user_data['recognized_text'] = response

            text_parts = await send_reply_with_limit(response)

            followup_button = InlineKeyboardMarkup([
                [InlineKeyboardButton("Задать уточняющий вопрос", callback_data='ask_followup')],
                [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]
            ])

            # Если всего одна часть — редактируем сообщение ожидания
            if len(text_parts) == 1:
                await waiting_message.edit_text(
                    text_parts[0],
                    reply_markup=followup_button,
                    parse_mode='MarkdownV2'
                )
            else:
                # Первую часть вставляем в waiting_message
                await waiting_message.edit_text(text_parts[0], parse_mode='MarkdownV2')

                # Остальные части отправляем отдельными сообщениями
                for i, part in enumerate(text_parts[1:], start=1):
                    is_last = (i == len(text_parts) - 1)
                    await update.callback_query.message.reply_text(
                        part,
                        parse_mode='MarkdownV2',
                        reply_markup=followup_button if is_last else None
                    )

                # Дополнительное сообщение-приглашение
                await update.callback_query.message.reply_text(
                    "Хотите задать уточняющий вопрос или прислать другое изображение?",
                    reply_markup=followup_button
                )

        except Exception as e:
            await waiting_message.edit_text(f"Ошибка при обработке изображения: {e}")

    asyncio.create_task(process())

async def handle_followup_question(update, context):
    """Функция, обрабатывающая нажатие кнопки для уточняющего вопроса."""
    user_id = update.callback_query.from_user.id
    # Завершаем текущий разговор с GPT, если он активен
    if is_ocr_mode.get(user_id, False):
        is_ocr_mode[user_id] = False  # Выключаем режим GPT
    
    # Включаем режим ролей
    is_asking_mode[user_id] = True    
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Пожалуйста, введите ваш уточняющий вопрос.")
    return ASKING_FOR_FOLLOWUP



def split_text_into_chunks(text, max_length=MAX_MESSAGE_LENGTH):
    """Разделяет текст на части, каждая из которых не превышает max_length."""
    chunks = []
    while len(text) > max_length:
        split_index = text.rfind("\n", 0, max_length)
        if split_index == -1:  # Если нет переносов строки, делим по max_length
            split_index = max_length
        chunks.append(text[:split_index].strip())
        text = text[split_index:].strip()
    chunks.append(text)
    return chunks

async def receive_followup_question(update, context):
    """Обработка уточняющего вопроса после распознавания текста."""
    user_id = update.message.from_user.id
    followup_question = update.message.text

    recognized_text = context.user_data.get('recognized_text', '')

    # Собираем полный запрос
    full_query = f"{recognized_text}\n\n{followup_question}"

    # Сообщение ожидания
    waiting_message = await update.message.reply_text("Обрабатываю уточняющий вопрос, подождите...")

    async def process():
        try:
            # Запрашиваем у Gemini
            response = await generate_text_rec_response(user_id, query=full_query)

            if response:
                response_chunks = split_text_into_chunks(response)

                # Если ответ помещается в одно сообщение — редактируем ожидание
                if len(response_chunks) == 1:
                    await waiting_message.edit_text(response_chunks[0])
                else:
                    # Первую часть заменяем в waiting_message
                    await waiting_message.edit_text(response_chunks[0])

                    # Остальное — отдельными сообщениями
                    for chunk in response_chunks[1:]:
                        await update.message.reply_text(chunk)

                # Клавиатура
                keyboard = [[InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    "Режим распознавания активен. Вы можете продолжить присылать изображения",
                    reply_markup=reply_markup
                )
            else:
                await waiting_message.edit_text("Ошибка при обработке уточняющего вопроса.")

        except Exception as e:
            await waiting_message.edit_text(f"Ошибка: {e}")

        finally:
            # Включаем режимы обратно
            is_role_mode[user_id] = False
            is_ocr_mode[user_id] = True

    asyncio.create_task(process())
    return ConversationHandler.END







import re

from urllib.parse import quote  # Импортируем функцию quote

async def barcode_with_gpt(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    img_path = context.user_data.get('img_path')

    if not img_path:
        await query.answer("Файл изображения не найден.", show_alert=True)
        return

    # Отправляем сообщение о начале обработки
    processing_message = await query.message.reply_text("Запрос принят, ожидайте...")
    if query:
        await query.answer()  # Гасим нажатие кнопки

    async def process():
        try:
            # Загружаем картинку из временного файла
            image = Image.open(img_path)
            image.load()

            # Запрос к модели
            response = await generate_barcode_response(user_id, image=image, query=None)
            logging.info(f"response: {response}")

            # Поиск названия товара
            product_name_match = re.search(
                r'Название товара.*?[:：]\s*(.*?)\s*\n\s*1\)', 
                response, 
                re.IGNORECASE
            )
            product_name = product_name_match.group(1).strip() if product_name_match else "Не найдено"
            logging.info(f"product_name: {product_name}")

            encoded_product_name = quote(product_name)

            # Очистка текста от заголовка
            match = re.search(r'товара:\s*', response, re.IGNORECASE)
            if match:
                response = response[match.end():]

            # Разделяем текст на части по 4096 символов
            caption_part, message_parts = split_html_text(response, 0, 4096)
            text_parts = [caption_part] + message_parts if caption_part else message_parts

            # Клавиатура с отзывами
            keyboard = [
                [InlineKeyboardButton("🔍 Поиск отзывов в Google", web_app=WebAppInfo(url=f"https://www.google.com/search?q={encoded_product_name}+отзывы"))],
                [InlineKeyboardButton("🔍 Поиск отзывов в Яндекс", web_app=WebAppInfo(url=f"https://yandex.ru/search/?text={encoded_product_name}+отзывы"))],
                [InlineKeyboardButton("🌌 В главное меню 🌌", callback_data='restart')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Отправляем ответ по частям
            for i, part in enumerate(text_parts):
                if i == 0:
                    if len(text_parts) == 1:
                        await processing_message.edit_text(
                            part,
                            reply_markup=reply_markup,
                            parse_mode="HTML"
                        )
                        return
                    else:
                        await processing_message.edit_text(part, parse_mode="HTML")
                elif i == len(text_parts) - 1:
                    await query.message.reply_text(part, reply_markup=reply_markup, parse_mode="HTML")
                else:
                    await query.message.reply_text(part, parse_mode="HTML")

        except Exception as e:
            logging.error(f"Ошибка при обработке изображения: {e}")
            await processing_message.edit_text("Произошла ошибка при обработке изображения.")



    # Запускаем фоновую задачу
    asyncio.create_task(process())


async def barcode_with_gpt_maybe(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    img_url = context.user_data.get('img_url')

    if not img_url:
        await query.answer("Изображение не найдено.", show_alert=True)
        return

    try:
        with open('temp_image.jpg', 'rb') as file:
            image = Image.open(file)
            image.load()
            
            # Запрос к Gemini
            response = await generate_barcode_response(user_id, image=image, query=None)
            barcode = extract_barcode(response)

            if barcode:
                context.user_data['barcode_text'] = barcode  # Сохраняем штрихкод
                await query.answer(f"Штрихкод найден: {barcode}", show_alert=True)

                # Запускаем поиск отзывов
                await process_barcode_search(update, context)
            else:
                await query.answer("Штрихкод не найден.", show_alert=True)
                
    except Exception as e:
        logging.error(f"Ошибка при обработке изображения: {e}")
        await query.answer("Ошибка при обработке изображения.", show_alert=True)




def extract_barcode(text: str) -> str | None:
    """
    Извлекает из текста штрихкод (последовательность цифр 8-14 знаков).
    Если штрихкод не найден, возвращает None.
    """
    matches = re.findall(r'\b\d{8,14}\b', text)
    return matches[0] if matches else None

GOOGLE_CSE_ID = "b232a6db8dceb4ac8"  # ID вашей поисковой системы Google Custom Search
GOOGLE_API_KEY = "AIzaSyCLq5s14u58HVmA5vQ3tBLTAVn3ljeoo2I"  # Ваш API-ключ Google
async def search_barcode_reviews(barcode, user_id):  # Добавляем user_id в аргументы
    query = f"{barcode} отзывы"
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&cx={GOOGLE_CSE_ID}&key={GOOGLE_API_KEY}"
    
    logging.info(f"Google Search Query: {query}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                
                search_results = [
                    {
                        "title": item.get("title", "No Title"),
                        "link": item.get("link", "No Link"),
                        "snippet": item.get("snippet", "No Snippet")
                    }
                    for item in data.get("items", [])
                ]

                logging.info(f"search_results: {search_results}")

                generate_results = search_results[:4]
                analysis_text = await generate_barcode_analysis(user_id, generate_results)  # Возвращает текст
                otzyvy = await generate_barcode_otzyvy(user_id, analysis_text)

                return otzyvy  # Просто возвращаем текст

    except Exception as e:
        logging.info(f"Ошибка при поиске: {e}")
        return "Ошибка при получении отзывов."

# Вызов функции для поиска отзывов по штрихкоду
async def process_barcode_search(update, context):
    query = update.callback_query
    barcode = context.user_data.get('barcode_text')
    user_id = update.effective_user.id

    logging.info(f"barcode: {barcode}, user_id: {user_id}")

    if not barcode:
        await query.message.reply_text("Штрихкод не найден.")
        return

    await query.message.reply_text(f"Ищу отзывы по штрихкоду {barcode}...")
    otzyvy = await search_barcode_reviews(barcode, user_id)  # Получаем готовый текст

    await query.message.reply_text(otzyvy)  # Просто отправляем текст






async def plantmap_gpt(update, context):
    user_id = update.effective_user.id
    img_url = context.user_data.get('img_url')
    await update.callback_query.answer()
    if not img_url:
        await update.callback_query.answer("Изображение не найдено.")
        return

    waiting_message = await update.callback_query.message.reply_text("Растение обрабатывается, ожидайте...")

    try:

        with open('temp_image.jpg', 'rb') as file:
            image = Image.open(file)
            image.load()
            
            # Генерация ответа через Gemini
            response = await generate_mapplants_response(user_id, image=image)
            
            # Парсим ответ
            name_match = re.search(r"1\)Русские названия:?\s*([^,\n2]+)", response)
            type_match = re.search(r"0\)Это:\s*(\S+)", response)

            if not name_match or not type_match:
                await update.callback_query.message.reply_text("Ошибка: не удалось извлечь данные из ответа.")
                return

            name = name_match.group(1).strip().capitalize()
            plant_type = type_match.group(1)

            # Удаляем "0)Это: " из полного текста
            full_text = re.sub(r"0\)Это:.*?\n", "", response, count=1, flags=re.DOTALL).strip()

            # Сохранение в Firebase
            data = {
                "Full_text": full_text,
                "Type": plant_type,
                "img_url": img_url
            }
            record_key = save_to_user_mapplants(user_id, name, data)
            logging.info(f"record_key: {record_key}")  
            if user_id in is_ocr_mode:
                is_ocr_mode[user_id] = False
            if user_id not in waiting_for_coordinates:
                waiting_for_coordinates[user_id] = True
                waiting_for_coordinates[user_id] = {"name": name, "record_key": record_key}
                  # Сохраняем название растения
            # Создаем кнопку с WebApp
            webapp_url2 = "https://epsg.io/map#srs=4326&x=38.371124&y=56.035226&z=9&layer=streets"            
            keyboard = [
                [InlineKeyboardButton("Получить координаты", web_app=WebAppInfo(url=webapp_url2))],
                [InlineKeyboardButton("Получить координаты в браузере", url=webapp_url2)],                
                [InlineKeyboardButton("🌌В главное меню(отмена)🌌", callback_data='restart')]
            ]

            # Создаем клавиатуру
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Формируем сообщение об успешном добавлении
            success_message = (
                f"Растение '<b>{name}</b>' распознано успешно!Теперь вы можете добавить его на общую карту.\n"
                "Если автоматически распозналось неверное название, то пожалуйста пришлите верное название.\n\n"
                "Если же название распознано верно, то пришлите координаты. Это можно сделать через карту встроенную в телеграм:\n"
                "1) Нажмите кнопку 'прикрепить'(скрепка),\n"
                "2) Выберите раздел 'геопозиция',\n"
                "3) Выберите на карте нужное место,\n"
                "4) Нажмите 'Отправить выбранную геопозицию'.\n\n"            
                "Либо вы можете прислать координаты вручную, в формате 'долгота, широта', либо 'долгота широта', например:\n"
                "<pre>37.153434 55.963768</pre>\n\n"
                "Так же вы можете воспользоваться кнопкой ниже, она откроет карту на которой вы сможете найти нужное место и скопировать координаты"
                )
            
            # Заменяем сообщение "ожидайте..." на сообщение об успехе
            await context.bot.edit_message_text(
                chat_id=update.callback_query.message.chat_id,
                message_id=waiting_message.message_id,
                text=success_message,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
    except Exception as e:
        logging.error(f"Ошибка в plantmap_gpt: {e}")
        await update.callback_query.message.reply_text(f"Ошибка при обработке: {e}")


async def scientific_gpt(update, context):
    user_id = update.effective_user.id
    query = update.callback_query
    if query:
        await query.answer()  # Гасим нажатие кнопки
    
    # Получаем scientific_name из контекста
    scientific_name = context.user_data.get('scientific_name')
    if not scientific_name:
        await query.message.reply_text("Научное название растения не найдено.")
        return
    
    # Отправляем сообщение ожидания
    waiting_message = await query.message.reply_text("Информация о растении добавляется, ожидайте...")
    
    try:
        # Формируем запрос для получения информации о растении
        query_text = (
            f"Дай информацию по растению с названием {scientific_name} в пределах 150 слов, по следующим пунктам:\n"
            "0) Что это. Гриб, растение, дерево, ягода. Этот пункт начни с фразы \"0)Это: \" В ответе напиши только одно слово из перечисленных, если ничего не подходит то напиши \"распознать не вышло\"\n"
            "1) Русскоязычные названия, от самого популярного до самых редких, если есть. Этот пункт начни с фразы \"1)Русские названия: \" В ответе перечисли только название или названия без лишних пояснений. Если русского названия нет то напиши исходное название игнорируя то что оно не является русским\n"
            "2) Общая краткая информация и описание, как выглядит, не длиннее 30 слов. Этот пункт начни с фразы \"2)Общая информация: \"\n"
            "3) Где обычно растёт, на какой территории и в какой местности, не длиннее 15 слов. Этот пункт начни с фразы \"3)Произрастает: \"\n"
            "4) Где и как применяется, ядовит или нет, не длиннее 20 слов. Этот пункт начни с фразы \"4)Применение: \"\n"
            "5) Дополнительная важная или интересная информация по этому растению, если есть. Этот пункт начни с фразы \"5)Дополнительно: \"\n\n"
            "Строго придерживайся заданного формата ответа, это нужно для того, чтобы корректно работал код программы.\n"
            "Никакого лишнего текста кроме заданных пунктов не пиши.\n"
        )
        
        # Генерация ответа через модель
        response = await generate_plant_help_response(user_id, query=query_text)
        
        # Парсим ответ
        name_match = re.search(r"1\)Русские названия:?\s*([^,\n2]+)", response)
        type_match = re.search(r"0\)Это:\s*(\S+)", response)
        if not name_match or not type_match:
            await query.message.reply_text("Ошибка: не удалось извлечь данные из ответа.")
            return
        
        name = name_match.group(1).strip().capitalize()
        plant_type = type_match.group(1)
        
        # Удаляем "0)Это: " из полного текста
        full_text = re.sub(r"0\)Это:.*?\n", "", response, count=1, flags=re.DOTALL).strip()
        
        # Сохранение в Firebase
        data = {
            "Full_text": full_text,
            "Type": plant_type,
            "scientific_name": scientific_name
        }
        record_key = save_to_user_mapplants(user_id, name, data)
        logging.info(f"record_key: {record_key}")
        
        if user_id in is_ocr_mode:
            is_ocr_mode[user_id] = False
        if user_id not in waiting_for_coordinates:
            waiting_for_coordinates[user_id] = True
            waiting_for_coordinates[user_id] = {"name": name, "record_key": record_key}
        # Создаем кнопку с WebApp
        # Создаем кнопку с WebApp
        webapp_url2 = "https://epsg.io/map#srs=4326&x=38.371124&y=56.035226&z=9&layer=streets"       
        # Создаем кнопку "В главное меню"
        keyboard = [
            [InlineKeyboardButton("Получить координаты", web_app=WebAppInfo(url=webapp_url2))],
            [InlineKeyboardButton("🌌Отмена🌌", callback_data='restart')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)    
        # Формируем сообщение об успешном добавлении
        success_message = (
            f"Растение '<b>{name}</b>' добавлено успешно!\n"
            "Теперь пришлите координаты. Это можно сделать через карту встроенную в телеграм:\n"
            "1) Нажмите кнопку 'прикрепить'(скрепка),\n"
            "2) Выберите раздел 'геопозиция',\n"
            "3) Выберите на карте нужное место,\n"
            "4) Нажмите 'Отправить выбранную геопозицию'.\n\n"            
            "Либо вы можете прислать координаты вручную, в формате 'долгота, широта', либо 'долгота широта', например:\n"
            "<pre>37.153434 55.963768</pre>\n\n"
            "Так же вы можете воспользоваться кнопкой ниже, она откроет карту на которой вы сможете найти нужное место и скопировать координаты"            
        )
        
        # Заменяем сообщение "ожидайте..." на сообщение об успехе
        await context.bot.edit_message_text(
            chat_id=update.callback_query.message.chat_id,
            message_id=waiting_message.message_id,
            text=success_message,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"Ошибка в scientific_gpt: {e}")
        await query.message.reply_text(f"Ошибка при обработке: {e}")



async def add_new_plant(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    await update.callback_query.answer()
    if user_id in is_ocr_mode:
        is_ocr_mode[user_id] = False    
    # Переключаем пользователя в режим ожидания координат
    waiting_for_coordinates[user_id] = True
    waiting_for_coordinates[user_id] = {"name": "", "record_key": ""}    
    await update.callback_query.message.reply_text(
        "Вы вошли в режим добавления растения. Пожалуйста, пришлите название растения, которое вы хотите добавить на карту. \n\n"
        "Так же вы можете в квадратных скобках указать текст, который будет отображаться при нажатии на метку вместо стандартного текста. \n"
        "Например:\n"
        "<pre>Опята [тут много опят]</pre>",
        parse_mode="HTML"  # Указываем парсмод HTML
    )


import re
import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

async def handle_coordinates(update, context):
    user_id = update.effective_user.id
    img_url = context.user_data.get('img_url')

    # Проверяем, что пользователь находится в состоянии ожидания координат
    if user_id not in waiting_for_coordinates:
        await update.message.reply_text("Я не жду от вас координат. Сначала добавьте растение.")
        return

    data = waiting_for_coordinates[user_id]
    logging.info(f"data: {data}")

    # Проверяем, есть ли уже name и record_key в данных
    name = data.get("name")
    record_key = data.get("record_key")

    # Проверяем, что именно прислал пользователь
    if update.message.location:
        lat = update.message.location.latitude
        lon = update.message.location.longitude
    elif update.message.text:
        user_input = update.message.text.strip()
        # Регулярное выражение для поиска текста в квадратных скобках
        brackets_pattern = r"\[([^\]]+)\]"
        brackets_match = re.search(brackets_pattern, user_input)
        
        # Если найдены квадратные скобки, извлекаем текст из них
        if brackets_match:
            user_full_text = brackets_match.group(1).strip()  # Текст внутри скобок
            user_input = re.sub(brackets_pattern, "", user_input).strip()  # Удаляем скобки и их содержимое из user_input
        else:
            user_full_text = None  # Если скобок нет, переменная остаётся пустой
        # Обновлённое регулярное выражение для поддержки запятой или пробела как разделителя
        coord_pattern = r"^\s*(-?\d+\.?\d*)\s*[, ]\s*(-?\d+\.?\d*)\s*$"
        match = re.match(coord_pattern, user_input)

        if match:
            lon, lat = map(float, match.groups())
            # Теперь lon и lat содержат долготу и широту
        else:
            # Пользователь ввёл не координаты, а, возможно, название растения
            waiting_message = await update.message.reply_text(f"Вы указали '{user_input}'. Ищу информацию об этом растении...")
            try:
                query = (
                    f"Дай информацию по растению с названием {user_input} в пределах 150 слов, по следующим пунктам:\n"
                    "0) Что это. Гриб, растение, дерево, ягода. Этот пункт начни с фразы \"0)Это: \" В ответе напиши только одно слово из перечисленных, если ничего не подходит то напиши \"распознать не вышло\"\n"
                    "1) Русскоязычные названия, от самого популярного до самых редких, если есть. Этот пункт начни с фразы \"1)Русские названия: \" В ответе перечисли только название или названия без лишних пояснений\n"
                    "2) Общая краткая информация и описание, как выглядит, не длиннее 30 слов. Этот пункт начни с фразы \"2)Общая информация: \"\n"
                    "3) Где обычно растёт, на какой территории и в какой местности, не длиннее 15 слов. Этот пункт начни с фразы \"3)Произрастает: \"\n"
                    "4) Где и как применяется, ядовит или нет, не длиннее 20 слов. Этот пункт начни с фразы \"4)Применение: \"\n"
                    "5) Дополнительная важная или интересная информация по этому растению, если есть. Этот пункт начни с фразы \"5)Дополнительно: \"\n\n"
                    "Строго придерживайся заданного формата ответа, это нужно для того, чтобы корректно работал код программы.\n"
                    "Никакого лишнего текста кроме заданных пунктов не пиши.\n"
                )
                response = await generate_plant_help_response(user_id, query)
                
                name_match = re.search(r"1\)Русские названия: ?([^,\n2]+)", response)
                type_match = re.search(r"0\)Это:\s*(\S+)", response)
                
                if not name_match or not type_match:
                    await update.message.reply_text("Ошибка: не удалось извлечь данные о растении.")
                    return
                
                new_name = name_match.group(1).strip().capitalize()
                plant_type = type_match.group(1)
                full_text = re.sub(r"0\)Это:.*?\n", "", response, count=1, flags=re.DOTALL).strip()
                
                data = {
                    "Full_text": full_text,
                    "Type": plant_type,
                    "img_url": img_url if img_url is not None else "изображение отсутствует",
                    "user_full_text": user_full_text
                }

                # Если name и record_key отсутствуют, вызываем save_to_user_mapplants
                if not name or not record_key:
                    record_key = save_to_user_mapplants(user_id, new_name, data)
                    waiting_for_coordinates[user_id] = {
                        "name": new_name,
                        "record_key": record_key  # Храним новое название растения
                    }
                else:
                    # Если name и record_key есть, вызываем update_to_user_mapplants
                    update_to_user_mapplants(user_id, name, new_name, data)
                    waiting_for_coordinates[user_id] = {
                        "name": new_name,  # Храним новое название растения
                        "record_key": record_key  # Сохраняем record_key, чтобы потом записать координаты
                    }

                # Создаем кнопку с WebApp
                webapp_url2 = "https://epsg.io/map#srs=4326&x=38.371124&y=56.035226&z=9&layer=streets"       
                # Создаем кнопку "В главное меню"
                keyboard = [
                    [InlineKeyboardButton("Получить координаты", web_app=WebAppInfo(url=webapp_url2))],
                    [InlineKeyboardButton("🌌Отмена🌌", callback_data='restart')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                # Формируем текст сообщения
                success_message = (
                    f"Растение '<b>{new_name}</b>' добавлено успешно! Если вы указали не то название то можете прислать верное\n"
                    "Теперь пришлите координаты. Это можно сделать через карту встроенную в телеграм:\n"
                    "1) Нажмите кнопку 'прикрепить'(скрепка),\n"
                    "2) Выберите раздел 'геопозиция',\n"
                    "3) Выберите на карте нужное место,\n"
                    "4) Нажмите 'Отправить выбранную геопозицию'.\n\n"            
                    "Либо вы можете прислать координаты вручную, в формате 'долгота, широта', либо 'долгота широта', например:\n"
                    "<pre>37.153434 55.963768</pre>\n\n"
                    "Так же вы можете воспользоваться кнопкой ниже, она откроет карту на которой вы сможете найти нужное место и скопировать координаты"
                )

                # Редактируем сообщение, добавляя кнопку
                # Универсальное получение chat_id
                if update.message:
                    chat_id = update.message.chat_id
                elif update.callback_query and update.callback_query.message:
                    chat_id = update.callback_query.message.chat_id
                else:
                    logger.error("Не удалось определить chat_id")
                    return

                # Отправка или редактирование сообщения
                try:
                    if update.callback_query and update.callback_query.message:
                        # Если это callback-запрос, редактируем существующее сообщение
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=waiting_message.message_id,
                            text=success_message,
                            parse_mode='HTML',
                            reply_markup=reply_markup
                        )
                    elif update.message:
                        # Если это текстовое сообщение, отправляем новое сообщение
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=success_message,
                            parse_mode='HTML',
                            reply_markup=reply_markup
                        )               
                except Exception as e:
                    logger.error(f"Ошибка при отправке/редактировании сообщения: {e}")                        
                return
            except Exception as e:
                logging.error(f"Ошибка при получении информации о растении: {e}")
                await update.message.reply_text("Ошибка при обработке запроса о растении.")
                return
    else:
        await update.message.reply_text("Ошибка: не удалось определить координаты.")
        return

    # Сохранение координат
    try:
        ref = db.reference(f"map_plants/{user_id}/{name}/{record_key}")
        current_data = ref.get() or {}
        current_data["coordinates"] = f"{lat}, {lon}"
        if img_url and "img_url" not in current_data:
            current_data["img_url"] = img_url
        ref.set(current_data)

        del waiting_for_coordinates[user_id]
        is_ocr_mode[user_id] = True

        umap_url = await view_map()
        webapp_url = "https://umap.openstreetmap.fr/ru/map/anemone_1177482?scaleControl=true&miniMap=false&scrollWheelZoom=true&zoomControl=true&editMode=disabled&moreControl=true&searchControl=null&tilelayersControl=null&embedControl=false&datalayersControl=true&onLoadPanel=none&captionBar=false&captionMenus=true&measureControl=true&datalayers=ad0d1cbb-4dd3-4476-8111-c8a40f97126b%2Ca5a444be-fdb5-44aa-81a7-2a0c4b889705&locateControl=true&starControl=false#9/55.6147/37.3123"  # URL твоей карты
        # Создание клавиатуры
        keyboard = [
            [InlineKeyboardButton("💠Запустить карту в телеграм💠", web_app=WebAppInfo(url=webapp_url))],    
            [InlineKeyboardButton("🌐Посмотреть в браузере🌐", url=webapp_url)],
            [InlineKeyboardButton("✏️ Добавить ещё по названию ✏️", callback_data='addnewplant')],        
            [InlineKeyboardButton("📷 Добавить ещё по фото 📷", callback_data='start_ocr')],
            [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]
        ]

        # Оборачиваем клавиатуру в InlineKeyboardMarkup
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправляем сообщение с клавиатурой
        await update.message.reply_text(
            f"Координаты {lon}, {lat} для '{name}' успешно сохранены! И растение теперь отображается на карте. Вы можете продолжить присылать растения",
            reply_markup=reply_markup  # Передаем reply_markup вместо keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при сохранении координат: {e}")
        await update.message.reply_text("Произошла ошибка при сохранении координат.")




async def convert_to_geojson(data: dict) -> dict:
    """
    Преобразует данные о растениях в формат GeoJSON с учетом типа растения. 
    :param data: Словарь с данными о растениях (результат load_all_plants_data).
    :return: GeoJSON объект.
    """
    type_mappings = {
        "Дерево": {"iconUrl": "https://i.ibb.co/qY5T5XDC/ututdd.png", "color": "DarkSlateGray", "iconClass": "Default"},
        "Ягода": {"iconUrl": "https://i.ibb.co/7xvZZfj0/71su67.png", "color": "#a4a8fa", "iconClass": "Default"},
        "Гриб": {"iconUrl": "https://i.ibb.co/9XrNZ7Z/qvxtuy.png", "color": "#6f6350", "iconClass": "Drop"},
        "Растение": {"iconUrl": "https://i.ibb.co/WpvMDw8v/faakdn.png", "color": "LightGoldenRodYellow", "iconClass": "Drop"},
    }

    features = []
    logging.info(f"data: {data}")
    for user_id, plants in data.items():
        for plant_name, records in plants.items():
            # Достаем общие данные о растении
            common_data = records.pop("common_data", {})

            for record_key, record_data in records.items():
                coordinates = record_data.get("coordinates", "").split(",")
                if len(coordinates) == 2:
                    try:
                        longitude = float(coordinates[0].strip())
                        latitude = float(coordinates[1].strip())

                        # Подставляем общие данные
                        full_text = record_data.get("Full_text", "")
                        user_full_text = record_data.get("user_full_text", "")                        
                        plant_type = record_data.get("Type", "Растение").strip().lower()
                        mapping = type_mappings.get(plant_type.capitalize(), type_mappings["Растение"])

                        img_url = record_data.get("img_url", "")
                        logging.info(f"img_url: {img_url}")                        
                        if user_full_text and user_full_text.strip():
                            text_to_use = user_full_text
                        else:
                            text_to_use = full_text

                        # Проверяем, есть ли img_url, и формируем description соответственно
                        if img_url and img_url.strip() and img_url != "изображение отсутствует":
                            description = f"{{{{{img_url}|300}}}}\n{text_to_use}"
                        else:
                            description = text_to_use

                        feature = {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [latitude, longitude],
                            },
                            "properties": {
                                "name": plant_name,
                                "description": description,
                                "_umap_options": {
                                    "color": mapping["color"],
                                    "iconUrl": mapping["iconUrl"],
                                    "iconClass": mapping["iconClass"],
                                    "showLabel": True,
                                    "labelInteractive": True,
                                    "labelDirection": "right",
                                },
                            },
                        }
                        logging.info(f"feature: {feature}")                       
                        features.append(feature)
                    except ValueError:
                        logging.warning(f"Неверный формат координат для растения {plant_name} у пользователя {user_id}")

    return {
        "type": "FeatureCollection",
        "features": features,
    }


async def generate_umap_url(geojson_url: str) -> str:
    """
    Генерирует URL для просмотра карты на UMap.
    
    :param geojson_url: URL GeoJSON файла.
    :return: URL карты UMap.
    """
    base_url = "https://umap.openstreetmap.fr/ru/map/"
    params = {
        "dataUrl": geojson_url,
        "zoom": 5,
        "lat": 56.0,
        "lon": 37.0,
    }
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{base_url}?{query_string}"

async def view_map():
    # Загрузка данных
    all_plants_data = load_all_plants_data()
  
    geojson_data = await convert_to_geojson(all_plants_data)
    # Загружаем GeoJSON на GitHub
    geojson_url = await upload_geojson_to_github(geojson_data)
    if not geojson_url:
        return None

    # Генерация URL карты
    return await generate_umap_url(geojson_url)


async def show_map(update: Update, context: CallbackContext):
    query = update.callback_query
    if query:
        await query.answer()  # Гасим нажатие кнопки
    await view_map()

    webapp_url = "https://umap.openstreetmap.fr/ru/map/anemone_1177482?scaleControl=true&miniMap=false&scrollWheelZoom=true&zoomControl=true&editMode=disabled&moreControl=true&searchControl=null&tilelayersControl=null&embedControl=false&datalayersControl=true&onLoadPanel=none&captionBar=false&captionMenus=true&measureControl=true&datalayers=ad0d1cbb-4dd3-4476-8111-c8a40f97126b%2Ca5a444be-fdb5-44aa-81a7-2a0c4b889705&locateControl=true&starControl=false#9/55.6147/37.3123"  # URL твоей карты
    keyboard = [
        [InlineKeyboardButton("💠Запустить карту в телеграм💠", web_app=WebAppInfo(url=webapp_url))],    
        [InlineKeyboardButton("🌐Посмотреть в браузере🌐", url=webapp_url)],
        [InlineKeyboardButton("✏️ Добавить растение по названию ✏️", callback_data='addnewplant')],        
        [InlineKeyboardButton("📷 Добавить растение по фото 📷", callback_data='start_ocr')],
        [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Если это вызвано через callback_query (нажатие кнопки), то редактируем сообщение
    if query:
        await query.edit_message_text(
            text="Тут вы можете посмотреть карту с растениями и грибами которые добавили на неё пользователи:",
            reply_markup=reply_markup
        )
    else:
        # Если вызвано напрямую (не через кнопку), отправляем новое сообщение
        await update.effective_chat.send_message(
            text="Тут вы можете посмотреть карту с растениями и грибами которые добавили на неё пользователи:",
            reply_markup=reply_markup
        )



GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "sylar112/geojson"  # Твой репозиторий
FILE_PATH = "plants.geojson"  # Имя файла
BRANCH = "main"  # Ветка, куда загружать

# 🔹 Функция загрузки GeoJSON на GitHub
async def upload_geojson_to_github(geojson_data: dict) -> str:
    try:
        url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

        # Получаем SHA текущего файла (нужно для обновления)
        resp = requests.get(url, headers=headers)
        sha = resp.json().get("sha", None)

        data = {
            "message": "Обновление GeoJSON",
            "content": base64.b64encode(json.dumps(geojson_data, ensure_ascii=False, indent=4).encode()).decode(),
            "branch": BRANCH,
        }
        if sha:
            data["sha"] = sha  # Добавляем SHA для обновления

        resp = requests.put(url, headers=headers, json=data)
        if resp.status_code == 201 or resp.status_code == 200:
            return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{FILE_PATH}"  # Прямая ссылка на файл
        else:
            logging.info(f"Ошибка GitHub API: {resp.json()}")
            return ""
    except Exception as e:
        logging.info(f"Ошибка при загрузке GeoJSON: {e}")
        return ""







async def save_to_my_plants(update: Update, context: CallbackContext) -> None:
    user_id = update.callback_query.from_user.id
    img_url = context.user_data.get('img_url')

    if not img_url:
        await update.callback_query.answer("Сначала загрузите изображение.")
        return
    await update.callback_query.answer()

    # Отправляем сообщение о начале процесса
    waiting_message = await update.callback_query.message.reply_text("Растение добавляется, ожидайте...")
    # Шаг 1: Распознавание растения через PlantNet API
    recognized_plants = await recognize_plant_automatically(update, context)
    if not recognized_plants:
        await update.callback_query.message.reply_text(
            "Не удалось распознать растение. Попробуйте снова."
        )
        return

    # Шаг 2: Выбор наиболее вероятного растения
    best_match = max(recognized_plants, key=lambda plant: plant['score'])
    scientific_name = best_match.get('species', {}).get('scientificNameWithoutAuthor', 'Неизвестное растение')
    query = (
        f"Дай информацию по растению с названием {scientific_name}, твой ответ должен быть не длиннее 150 слов, по следующим пунктам:\n"
        "0) Русскоязычные названия, от самого популярного до самых редких, если есть. Этот пункт начни с фразы \"0)Русские названия:\" В ответе перечисли только название или названия без лишних пояснений\n"
        "1) Общая краткая информация и описание, как выглядит, не длиннее 30 слов. Этот пункт начни с фразы \"1)Общая информация\"\n"
        "2) Где обычно растёт, на какой территории и в какой местности, не длиннее 15 слов. Этот пункт начни с фразы \"2)Произрастает:\"\n"
        "3) Где и как применяется, ядовит или нет, не длиннее 20 слов. Этот пункт начни с фразы \"3)Применение:\"\n"
        "4) Частота полива зимой: 1 раз в ... дней. Этот пункт начни с фразы \"4)Полив зимой: раз в ... дней\"\n. Вместо троточия просто напиши число\n"
        "5) Частота полива летом: 1 раз в ... дней. Этот пункт начни с фразы \"5)Полив летом: раз в ... дней\"\n. Вместо троточия просто напиши число\n"
        "6) Светолюбивость: (число от 0 до 10, где 0 — самые теневыносливые растения, а 10 — самые светолюбивые). Этот пункт начни с фразы \"6)Светолюбивость:\" и напиши только число\n"
        "7) Средняя температура для комфортного роста: градусов по Цельсию. Этот пункт начни с фразы \"7)Температура:\" и только число в градусах по цельсию\n"
        "8) Минимальная температура, которую данное растение может выдержать без урона здоровью. Этот пункт начни с фразы \"8)Минимальная кратковременная температура:\" и только число\n"
        "9) Дополнительная важная или интересная информация по этому растению, если есть. Этот пункт начни с фразы \"9)Дополнительно:\", не больше 40 слов \n\n"
        "Строго придерживайся заданного формата ответа, это нужно для того, чтобы корректно работал код программы.\n"
        "Никакого лишнего текста кроме заданных пунктов не пиши.\n"        
    )
    # Шаг 3: Сохранение растения в Firebase
    response_text = await generate_plant_help_response(user_id, query=query)


    plant_data = {
        "Full_text": response_text,
        "img_url": img_url,
        "rus_name": extract_rus_name(response_text),
        "winter": extract_watering(response_text, "Полив зимой"),
        "summer": extract_watering(response_text, "Полив летом"),
        "sunlight": extract_number(response_text, "Светолюбивость"),
        "temperature": extract_avg_number(response_text, "Температура"),
        "min_temp": extract_avg_number(response_text, "Минимальная кратковременная температура"),
    }
    save_to_user_plants(user_id, scientific_name, plant_data)
    rus_name = extract_rus_name(response_text)        
    # Создаем кнопку "Отменить поиск"
    keyboard = [
        [InlineKeyboardButton("🪴 Мои растения 🪴", callback_data='myplants')],
        [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]

    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Отправка подтверждения пользователю
    await waiting_message.edit_text(f"✅ Растение '{rus_name}' успешно добавлено в ваши растения! Вы можете продолжить присылать фото растений, или посмотреть список",
        reply_markup=reply_markup
    )


async def recognize_plant_automatically(update: Update, context: CallbackContext):
    """
    Распознает растение, отправляя изображение через прокси Google Apps Script.
    """
    image_bytes_io = context.user_data.get('image_bytes')
    if not image_bytes_io:
        return []

    # Кодируем изображение в base64
    image_bytes_io.seek(0) # Возвращаем курсор в начало файла
    encoded_image = base64.b64encode(image_bytes_io.read()).decode('utf-8')
    
    payload = {'image': encoded_image}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(GAS_URL, json=payload) as response:
                if response.status == 200:
                    prediction = await response.json()
                    # Проверяем, не вернул ли GAS ошибку
                    if 'error' in prediction:
                         logger.error(f"Ошибка от GAS при распознавании: {prediction['error']}")
                         return []
                    return prediction.get('results', [])
                else:
                    logger.error(f"Ошибка HTTP {response.status} при распознавании через прокси.")
                    return []
    except Exception as e:
        logger.error(f"Исключение при распознавании через прокси: {e}")
        return []
    finally:
        # Очищаем изображение после использования
        context.user_data.pop('image_bytes', None)

        
async def send_buttons_after_media(query):
    keyboard = [
        [InlineKeyboardButton("🗺Добавить это растение на карту 🗺", callback_data='scientific_gpt')],
        [InlineKeyboardButton("🪴Добавить в мои растения🪴", callback_data='gptplant_response')],         
        [InlineKeyboardButton("Подробнее об этом растении", callback_data='gpt_plants_more')],         
        [InlineKeyboardButton("Помощь по уходу за этим растением", callback_data='gpt_plants_help')],        
        [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        "Для занесения этого растения в список ваших растений, добавления на карту, либо для получения более подробной информации об этом растении и уходе за ним, воспользуйтесь кнопками ниже. Либо отправьте следующее изображение",
        reply_markup=reply_markup
    )
from urllib.parse import urlencode
# URL вашего Google Apps Script
GAS_URL = 'https://script.google.com/macros/s/AKfycbxsLoPIT3xgg2NrR6q212abtI32pstNrG0v9-OPv7IsdT0Ky-MJqAULed1xM6A2uYwhfw/exec'

async def get_image_file(url: str, session: aiohttp.ClientSession) -> BytesIO | None:
    if not url:
        return None

    proxy_url = f"{GAS_URL}?{urlencode({'url': url})}"

    try:
        async with session.get(proxy_url) as response:
            if response.status != 200:
                return None

            data = await response.json()
            if 'image_b64' not in data:
                return None

            return BytesIO(base64.b64decode(data['image_b64']))

    except Exception as e:
        logger.error(f"Ошибка загрузки {url}: {e}")
        return None

async def button_more_plants_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    plant_key = query.data
    await query.message.reply_text("Запрос принят, собираю информацию об этом растении, подождите немного.")
    plant_data = context.user_data.get(plant_key)
    if plant_data:
        scientific_name = plant_data['scientific_name']
        common_names = plant_data['common_names']
        context.user_data['scientific_name'] = scientific_name

        if isinstance(common_names, str):
            common_names = [common_names]

        wikipedia_link, article_title = await get_wikipedia_link(scientific_name, common_names)

        description = ""
        if wikipedia_link:
            try:
                summary = await get_wikipedia_summary(article_title)
                description += f"{summary}\n\n"
            except Exception as e:
                logger.error(f"Error fetching summary for {article_title}: {e}")
                description += "Краткое описание недоступно\n\n"
        else:
            description = "\n\nИнформация по данному растению не найдена\n\n"

        images = plant_data.get('images', [])
        media = []

        if images:
            async with aiohttp.ClientSession() as session:
                tasks = [
                    get_image_file(img["url"]["o"], session)
                    for img in images if "url" in img
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                media = []
                for idx, image_file in enumerate(results):
                    if isinstance(image_file, Exception) or image_file is None:
                        continue

                    caption = None
                    if idx == 0:
                        caption = (
                            f"Растение: {escape_markdown_v2(scientific_name)}\n"
                            f"Общие названия: {escape_markdown_v2(', '.join(common_names))}\n"
                            f"{truncate_text_with_link(description, 300, wikipedia_link, scientific_name)}"
                        )

                    media.append(InputMediaPhoto(media=image_file, caption=caption))

                if media:
                    try:
                        await query.message.reply_media_group(media)
                    except Exception as e:
                        logger.error(f"Ошибка отправки медиагруппы: {e}")
                        await query.message.reply_text("Ошибка при отправке изображений.")
                else:
                    await query.message.reply_text("Изображения не загрузились")

                # В любом случае — ждём, disable_web_page_preview=False
                await asyncio.sleep(2)
        else: # Этот else относится к if images:
            await query.message.reply_text("Изображения не найдены")

        # Только после медиа — отправляем кнопки
        await send_buttons_after_media(query)
    else:
        await query.message.reply_text("Данные о растении не найдены")

    await query.answer()

async def gpt_plants_more_handler(update, context):
    """Асинхронный обработчик для запроса ухода за растением по научному названию."""
    user_id = update.callback_query.from_user.id
    scientific_name = context.user_data.get("scientific_name")

    if not scientific_name:
        await update.callback_query.answer("Научное название не указано. Попробуйте снова.")
        return

    query_alert = update.callback_query
    await query_alert.answer("Ищу информацию, подождите около 10-15 секунд.", show_alert=True)

    query = (
        f"Расскажи больше про {scientific_name}, например, интересные факты, "
        "способы применения, укажи если ядовито, какие-то особенности и прочее. "
        "При этом будь лаконичной, ответ должен быть не длинее 300 слов."
    )

    message = update.callback_query.message

    # Сообщение-заглушка
    waiting_message = await message.edit_text("🔎 Собираю информацию, пожалуйста, подождите...")

    async def process():
        try:
            # Генерация ответа без контекста
            response_text = await generate_plant_help_response(user_id, query=query)

            # Разбиваем текст на части
            caption_part, message_parts = split_html_text(response_text, 0, 4096)
            text_parts = [caption_part] + message_parts if caption_part else message_parts

            logger.info(f"text_parts {text_parts}")

            keyboard = [
                [InlineKeyboardButton("🪴Добавить в мои растения🪴", callback_data='gptplant_response')],
                [InlineKeyboardButton("Помощь по уходу за этим растением", callback_data='gpt_plants_help')],
                [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if not text_parts:
                await waiting_message.edit_text("К сожалению, не удалось получить информацию. Попробуйте снова позже.")
                return

            if len(text_parts) == 1:
                # Если единственная часть — сразу редактируем заглушку и добавляем кнопки
                await waiting_message.edit_text(
                    text_parts[0],
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                # Первая часть заменяет "ожидание"
                await waiting_message.edit_text(text_parts[0], parse_mode='HTML')

                # Остальные отправляем новыми сообщениями
                for i, part in enumerate(text_parts[1:], start=1):
                    is_last = (i == len(text_parts) - 1)
                    await update.callback_query.message.reply_text(
                        part,
                        parse_mode='HTML',
                        reply_markup=reply_markup if is_last else None
                    )

        except Exception as e:
            await waiting_message.edit_text(f"Ошибка при получении информации: {e}")

    # Запуск в фоне
    asyncio.create_task(process())


async def gpt_plants_help_handler(update, context):
    """Асинхронный обработчик для запроса ухода за растением по научному названию."""
    user_id = update.callback_query.from_user.id
    scientific_name = context.user_data.get("scientific_name")

    if not scientific_name:
        await update.callback_query.answer("Научное название не указано. Попробуйте снова.")
        return

    query = update.callback_query        
    await query.answer("Ищу информацию, подождите около 10-15 секунд.", show_alert=True)

    # Первое сообщение "ожидания"
    waiting_message = await update.callback_query.message.edit_text(
        "Думаю над ответом, пожалуйста, подождите..."
    )

    async def process():
        try:
            # Формируем запрос
            query_text = f"Как ухаживать за {scientific_name}? Ответ не длиннее 200 слов"

            # Генерация ответа без контекста
            response_text = await generate_plant_help_response(user_id, query=query_text)
            logger.info(f"response_text {response_text}")

            caption_part, message_parts = split_html_text(response_text, 0, 4096)
            text_parts = [caption_part] + message_parts if caption_part else message_parts

            keyboard = [
                [InlineKeyboardButton("🪴Добавить в мои растения🪴", callback_data='gptplant_response')],
                [InlineKeyboardButton("Подробнее об этом растении", callback_data='gpt_plants_more')],
                [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if not text_parts:
                await waiting_message.edit_text("К сожалению, не удалось получить информацию. Попробуйте снова.")
                return

            if len(text_parts) == 1:
                # Один ответ — сразу редактируем сообщение ожидания и добавляем кнопки
                await waiting_message.edit_text(
                    text_parts[0],
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            else:
                # Первая часть заменяет "ожидание"
                await waiting_message.edit_text(text_parts[0], parse_mode='HTML')

                # Остальные части отправляем отдельными сообщениями
                for i, part in enumerate(text_parts[1:], start=1):
                    is_last = (i == len(text_parts) - 1)
                    await update.callback_query.message.reply_text(
                        part,
                        parse_mode='HTML',
                        reply_markup=reply_markup if is_last else None
                    )

        except Exception as e:
            await waiting_message.edit_text(f"Ошибка: {e}")

    # Запуск фоновой задачи
    asyncio.create_task(process())

def extract_rus_name(response_text):
    match = re.search(r"0\)Русские названия:(.*?)1\)Общая информация", response_text, re.DOTALL)
    return match.group(1).strip() if match else "Не найдено"

async def gptplant_response(update, context):
    """Асинхронный обработчик для запроса ухода за растением по научному названию."""
    user_id = update.callback_query.from_user.id
    scientific_name = context.user_data.get("scientific_name")
    img_url = context.user_data.get('img_url')    
    await update.callback_query.answer()

    if not scientific_name:
        await update.callback_query.answer("Научное название не указано. Попробуйте снова.")
        return

    # Формируем запрос с научным названием
    query = (
        f"Дай информацию по растению с названием {scientific_name}, твой ответ должен быть не длиннее 150 слов, по следующим пунктам:\n"
        "0) Русскоязычные названия, от самого популярного до самых редких, если есть. Этот пункт начни с фразы \"0)Русские названия:\" В ответе перечисли только название или названия без лишних пояснений\n"
        "1) Общая краткая информация и описание, как выглядит, не длиннее 30 слов. Этот пункт начни с фразы \"1)Общая информация\"\n"
        "2) Где обычно растёт, на какой территории и в какой местности, не длиннее 15 слов. Этот пункт начни с фразы \"2)Произрастает:\"\n"
        "3) Где и как применяется, ядовит или нет, не длиннее 20 слов. Этот пункт начни с фразы \"3)Применение:\"\n"
        "4) Частота полива зимой: 1 раз в ... дней. Этот пункт начни с фразы \"4)Полив зимой: раз в ... дней\"\n. Вместо троточия просто напиши число\n"
        "5) Частота полива летом: 1 раз в ... дней. Этот пункт начни с фразы \"5)Полив летом: раз в ... дней\"\n. Вместо троточия просто напиши число\n"
        "6) Светолюбивость: (число от 0 до 10, где 0 — самые теневыносливые растения, а 10 — самые светолюбивые). Этот пункт начни с фразы \"6)Светолюбивость:\" и напиши только число\n"
        "7) Средняя температура для комфортного роста: градусов по Цельсию. Этот пункт начни с фразы \"7)Температура:\" и только число в градусах по цельсию\n"
        "8) Минимальная температура, которую данное растение может выдержать без урона здоровью. Этот пункт начни с фразы \"8)Минимальная кратковременная температура:\" и только число\n"
        "9) Дополнительная важная или интересная информация по этому растению, если есть. Этот пункт начни с фразы \"9)Дополнительно:\", не больше 40 слов \n\n"
        "Строго придерживайся заданного формата ответа, это нужно для того, чтобы корректно работал код программы.\n"
        "Никакого лишнего текста кроме заданных пунктов не пиши.\n"         
    )
    # Генерация ответа без контекста
    response_text = await generate_plant_help_response(user_id, query=query)
    logger.info(f"response_text {response_text}")
    
    plant_data = {
        "Full_text": response_text,
        "img_url": img_url,
        "rus_name": extract_rus_name(response_text),  # Добавляем русские названия
        "winter": extract_watering(response_text, "Полив зимой"),
        "summer": extract_watering(response_text, "Полив летом"),
        "sunlight": extract_number(response_text, "Светолюбивость"),
        "temperature": extract_avg_number(response_text, "Температура"),
        "min_temp": extract_avg_number(response_text, "Минимальная кратковременная температура"),
    }
    
    save_to_user_plants(user_id, scientific_name, plant_data)
    rus_name = extract_rus_name(response_text)    
    keyboard = [
        [InlineKeyboardButton("🪴 Мои растения 🪴", callback_data='myplants')],
        [InlineKeyboardButton("Помощь по уходу за этим растением", callback_data='gpt_plants_help')],   
        [InlineKeyboardButton("Подробнее об этом растении", callback_data='gpt_plants_more')],         
        [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]

    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Отправка подтверждения пользователю
    await update.callback_query.message.edit_text(f"✅ Растение '{rus_name}' успешно добавлено в ваши растения! Вы можете продолжить присылать фото растений, или посмотреть список",
        reply_markup=reply_markup
    )

def get_season() -> str:
    """Определяет текущий сезон (зима или лето)."""
    month = datetime.now().month
    return "winter" if month in {10, 11, 12, 1, 2, 3} else "summer"


user_plants_list_messages = {}

async def handle_myplants_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатие кнопки 'Мои растения'."""
    query = update.callback_query
    user_id = query.from_user.id
    query = update.callback_query
    await query.answer()    
    message_text, keyboard = await generate_plants_buttons(user_id)
    
    if keyboard:
        if user_id in user_plants_list_messages:
            # Если у нас есть ID предыдущего сообщения, пробуем его отредактировать
            try:
                await context.bot.edit_message_text(
                    text=message_text,
                    chat_id=query.message.chat_id,
                    message_id=user_plants_list_messages[user_id],
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            except Exception:
                # Если сообщение не найдено (например, было удалено), отправляем новое
                new_message = await query.message.reply_text(message_text, reply_markup=keyboard, parse_mode="HTML")
                user_plants_list_messages[user_id] = new_message.message_id
        else:
            # Если ещё нет сохранённого ID, отправляем новое сообщение
            new_message = await query.message.reply_text(message_text, reply_markup=keyboard, parse_mode="HTML")
            user_plants_list_messages[user_id] = new_message.message_id
    else:
        await query.answer(message_text, show_alert=True)  # Показываем алерт, если список пуст

# Обработчик для кнопок пагинации
async def handle_pagination(update, context):
    query = update.callback_query
    await query.answer()  # Подтверждаем получение запроса
    
    # Проверяем, что callback_data начинается с "plantpage_"
    if query.data.startswith("plantpage_"):
        # Извлекаем номер страницы, поле сортировки и направление сортировки из callback_data
        _, page, sort_field, reverse_sort = query.data.split("_")
        page = int(page)
        reverse_sort = reverse_sort == "True"  # Преобразуем строку в булево значение
        logging.info(f"sort_field: {sort_field}")        
        logging.info(f"reverse_sort: {reverse_sort}")        
        # Получаем user_id из контекста или из update
        user_id = query.from_user.id
        
        # Если пользователь уже имеет состояние сортировки, используем его
        if user_id in SORT_STATES:
            sort_field = SORT_STATES[user_id]["field"]
            reverse_sort = SORT_STATES[user_id]["reverse"]
        logging.info(f"sort_field2: {sort_field}")        
        logging.info(f"reverse_sort2: {reverse_sort}")        
        # Генерируем новые кнопки для указанной страницы с учетом сортировки
        reverse_sort_for_generation = not reverse_sort
        if user_id in SORT_STATES:
            SORT_STATES[user_id] = {"field": "name", "reverse": reverse_sort_for_generation}
        logging.info(f"SORT_STATES0: {SORT_STATES}")                 
        # Генерируем новые кнопки для указанной страницы с учетом сортировки
        message_text, keyboard = await generate_plants_buttons(
            user_id=user_id,
            sort_by=sort_field,
            reverse=reverse_sort,  # Используем инвертированное значение
            page=page
        )
        
        # Обновляем сообщение с новыми кнопками
        await query.edit_message_text(
            text=message_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )



# Храним состояние сортировки для пользователей
SORT_STATES = {}

from math import ceil

async def generate_plants_buttons(user_id: int, sort_by: str = None, reverse: bool = False, page: int = 0):
    """Генерирует кнопки с информацией о растениях пользователя с возможностью сортировки и пагинации."""

    plants = load_user_plants(user_id)
    if not plants:
        return "У вас нет сохранённых растений.", None
    season = get_season()
  
    header = f"{'Название':<14} |{'Вода'} |{'t°С':^4} |{'t°Min'}|{'Свет'}"
    rows = []
    buttons = []
    logging.info(f"sort_field3: {sort_by}")        
    logging.info(f"reverse_sort3: {reverse}")      
    # Обрабатываем состояние сортировки
    if user_id not in SORT_STATES:
        SORT_STATES[user_id] = {"field": "name", "reverse": reverse}
    logging.info(f"SORT_STATES: {SORT_STATES}")     
    # Обновляем состояние, если нажата кнопка сортировки
    if sort_by:
        if SORT_STATES[user_id]["field"] == sort_by:
            SORT_STATES[user_id]["reverse"] = not SORT_STATES[user_id]["reverse"]
        else:
            SORT_STATES[user_id] = {"field": sort_by, "reverse": False}
    
    # Используем текущее состояние сортировки
    sort_field = SORT_STATES[user_id]["field"]
    reverse_sort = SORT_STATES[user_id]["reverse"]
    logging.info(f"sort_field4: {sort_field}")        
    logging.info(f"reverse_sort4: {reverse_sort}")      
    # Преобразуем данные в список для сортировки
    plant_list = []
    for name, data in plants.items():
        short_name = data.get("rus_name", name).split(",")[0][:16].ljust(18, '\u2009')
        filler = '\u2009' if len(short_name) % 2 == 0 else '\u200B'
        short_name = short_name.ljust(14, filler)
        season_value = str(data.get(season, "?")).rjust(1)
        temperature = str(data.get("temperature", "?")).rjust(1)
        min_temp = str(data.get("min_temp", "?")).rjust(1)
        sunlight = str(data.get("sunlight", "?")).rjust(1)
        plant_list.append((name, short_name, season_value, temperature, min_temp, sunlight))
    
    # Выбираем ключ для сортировки
    sort_keys = {
        "name": lambda x: x[1],         # По имени (short_name)
        "water": lambda x: int(x[2]) if x[2].isdigit() else -1,   # По количеству воды
        "mintemp": lambda x: int(x[4]) if x[4].isdigit() else -100,  # По min_temp
        "sunlight": lambda x: int(x[5]) if x[5].isdigit() else -1,  # По свету
    }
    logging.info(f"sort_field5: {sort_field}")        
    logging.info(f"reverse_sort5: {reverse_sort}")       
    # Сортируем
    plant_list.sort(key=sort_keys[sort_field], reverse=reverse_sort)
    
    # Формируем строки для сообщения и кнопки
    for name, short_name, season_value, temperature, min_temp, sunlight in plant_list:
        row_text = f"{short_name[:14]} |{season_value:^4} |{temperature:^4} |{min_temp:^4} |{sunlight:^4}"
        rows.append(row_text)
    
    # Разбиваем кнопки на страницы по 9 элементов
    total_pages = ceil(len(plant_list) / 9)
    start_index = page * 9
    end_index = start_index + 9
    current_page_plants = plant_list[start_index:end_index]
    
    for name, short_name, season_value, temperature, min_temp, sunlight in current_page_plants:
        button_text1 = f"{short_name[:16]}"
        button_text1 = button_text1[:64]  # Эта строка лишняя, 16 символов и так в пределах 64
        button_text2 = f" {season_value} | {temperature} | {min_temp} | {sunlight}"        
        buttons.append([
            InlineKeyboardButton(button_text1, callback_data=f"myplant_{name}"),
            InlineKeyboardButton(button_text2, callback_data=f"myplant_{name}")
        ])
    waterkeyboard = [InlineKeyboardButton("🌧Отметить поливку✅", callback_data="water_plant")] 
    pre_buttons = [
        InlineKeyboardButton(f"Сортировать по:", callback_data="separator")
    ]
    
    # Создаем кнопки сортировки
    sort_buttons = [
        InlineKeyboardButton(f"Имя {'🔽' if sort_field == 'name' and not reverse_sort else '🔼'}", callback_data="plantsort_name"),
        InlineKeyboardButton(f"Полив {'🔽' if sort_field == 'water' and not reverse_sort else '🔼'}", callback_data="plantsort_water"),
        InlineKeyboardButton(f"Min t°С {'🔽' if sort_field == 'min_temp' and not reverse_sort else '🔼'}", callback_data="plantsort_mintemp"),
        InlineKeyboardButton(f"Свет {'🔽' if sort_field == 'sunlight' and not reverse_sort else '🔼'}", callback_data="plantsort_sunlight"),
    ]
    
    # Добавляем кнопки переключения страниц
    navigation_buttons = []
    if total_pages > 1:
        prev_page = page - 1 if page > 0 else total_pages - 1
        next_page = page + 1 if page < total_pages - 1 else 0
        navigation_buttons = [
            InlineKeyboardButton("⬅️ Назад", callback_data=f"plantpage_{prev_page}_{sort_field}_{SORT_STATES[user_id]['reverse']}"),
            InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="page_info"),
            InlineKeyboardButton("➡️ Вперед", callback_data=f"plantpage_{next_page}_{sort_field}_{SORT_STATES[user_id]['reverse']}")
        ]
    # Добавляем информацию о поливках
    watering_info = format_watering_info(user_id)   
    # Формируем текст сообщения
    newplant = [InlineKeyboardButton("🌱 Добавить новое растение 🌱", callback_data='start_ocr')] 
    backtomenu = [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]
    message_text = f"<pre>Вода - поливать раз в Х дней\nt°С - Средняя комфортная температура\nt°Min - минимальная температура\nСвет - теневыносливость, где 10 это самые светолюбивые растения 1 это самые теневыносливые\n\nВаши текущие растения:\n{header}\n" + "\n".join(rows) + f"</pre>\n\n{watering_info}"
    keyboard = InlineKeyboardMarkup([waterkeyboard] + [pre_buttons] + [sort_buttons] + buttons + [navigation_buttons] + [newplant] + [backtomenu])
    
    return message_text, keyboard

MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
}

def format_watering_info(user_id: int) -> str:
    """Форматирует информацию о последних поливках."""
    water_plants = load_water_plants(user_id)
    if not water_plants:
        return "Данные о поливке отсутствуют."
    
    water_dates = [datetime.strptime(date, "%d.%m.%y %H:%M") for date in water_plants]
    water_dates.sort(reverse=True)

    last_watering = water_dates[0]
    days_ago = (datetime.now() - last_watering).days

    # Формируем список последних поливок с русскими названиями месяцев
    watering_list = "\n".join([
        f"{i+1}) {dt.day} {MONTHS_RU[dt.month]} в {dt.strftime('%H:%M')}"
        for i, dt in enumerate(water_dates)
    ])
    
    return f"🌧Последняя поливка была {days_ago} дней назад.\n\nСписок последних поливок:\n{watering_list}"


async def watering_button_handler(update: Update, context: CallbackContext) -> None:
    """Обрабатывает нажатие на кнопку 'Полито'."""
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    message_id = query.message.message_id

    mark_watering(user_id)  # Добавляем запись о поливе

    # Генерируем новое сообщение и кнопки
    message_text, keyboard = await generate_plants_buttons(user_id)

    if keyboard:
        await query.message.edit_text(
            text=message_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )

    await query.answer("Записано! ✅", show_alert=True)

# Словарь для хранения ID сообщений с изображениями растений
user_plant_messages = {}

async def plant_callback(update: Update, context: CallbackContext):
    """Обработчик нажатий на кнопки растений с обрезкой подписи."""
    query = update.callback_query
    # Отвечаем на запрос сразу, чтобы убрать состояние загрузки у кнопки
    await query.answer()

    logging.info(f"Получен callback-запрос: {query.data}")
    user_id = query.from_user.id

    try:
        # Убедимся, что формат callback_data соответствует ожидаемому ('plant_ИмяРастения')
        # plant_name останется на английском, если ключи в load_user_plants английские
        plant_name = query.data.split("_", 1)[1]
    except IndexError:
        logging.error(f"Неверный формат callback_data для пользователя {user_id}: {query.data}")
        # Можно отправить сообщение пользователю или просто записать в лог
        # await context.bot.send_message(chat_id=user_id, text="Произошла внутренняя ошибка.")
        return # Прекращаем обработку, если данные некорректны

    logging.info(f"Запрошено растение: {plant_name} для пользователя: {user_id}")
    # Загружаем данные о растениях пользователя
    plants = load_user_plants(user_id) # Предполагается, что эта функция определена где-то еще
    plant_data = plants.get(plant_name)

    if not plant_data:
        logging.warning(f"Данные для растения '{plant_name}' не найдены для пользователя {user_id}")
        # Сообщаем пользователю (можно отправить новое сообщение или отредактировать старое, если есть)
        await context.bot.send_message(chat_id=user_id, text=f"Информация о растении '{plant_name}' не найдена.")
        return

    img_url = plant_data.get("img_url")
    full_text = plant_data.get("Full_text", "") # Получаем текст, по умолчанию пустая строка

    if not img_url:
        logging.error(f"Отсутствует URL изображения для растения '{plant_name}' у пользователя {user_id}")
        # Обрабатываем отсутствующий URL, можно отправить только текст или сообщение об ошибке
        await context.bot.send_message(chat_id=user_id, text=f"Ошибка: Не удалось найти изображение для '{plant_name}'.")
        return

    # --- Подготовка и обрезка подписи ---
    # Удаляем префикс "0)Русские названия: " из начала текста
    caption = re.sub(r"^0\)Русские названия:\s*", "", full_text, 1)

    MAX_CAPTION_LENGTH = 1024 # Лимит Telegram для подписей к фото

    if len(caption) > MAX_CAPTION_LENGTH:
        logging.info(f"Подпись для '{plant_name}' слишком длинная ({len(caption)} симв.), обрезается.")
        # Обрезаем и добавляем многоточие, оставляя место для "..." (3 символа)
        caption = caption[:MAX_CAPTION_LENGTH - 3] + "..."
    # --- Конец логики обработки подписи ---

    # Создаём кнопки "Удалить" и "Закрыть"
    keyboard = [
        [InlineKeyboardButton("❌ Удалить", callback_data=f"plantdelete_{plant_name}")],
        [InlineKeyboardButton("🚫 Закрыть", callback_data="plantclose")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Удаляем предыдущее сообщение с растением, если оно было сохранено
    # Это по-прежнему зависит от доступности user_plant_messages в этой области видимости
    if user_id in user_plant_messages:
        previous_message_id = user_plant_messages.pop(user_id) # Удаляем ID из словаря перед попыткой удаления
        try:
            logging.info(f"Попытка удалить предыдущее сообщение {previous_message_id} для пользователя {user_id}")
            await context.bot.delete_message(chat_id=user_id, message_id=previous_message_id)
        except Exception as e:
            # Логируем ошибку, если удаление не удалось (сообщение уже удалено, бот удален из чата и т.д.)
            # Продолжаем выполнение, т.к. главная цель - отправить новое сообщение.
            logging.warning(f"Не удалось удалить предыдущее сообщение {previous_message_id} для пользователя {user_id}: {e}")

    # Отправляем новое сообщение с фото, подписью (возможно обрезанной) и кнопками
    try:
        sent_message = await context.bot.send_photo(
            chat_id=user_id,
            photo=img_url,
            caption=caption, # Используем возможно обрезанную подпись
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN # Убедитесь, что ваш текст размечен под Markdown, или используйте ParseMode.HTML / None
        )
        # Запоминаем ID нового сообщения, чтобы его можно было удалить позже
        user_plant_messages[user_id] = sent_message.message_id
        logging.info(f"Отправлено фото растения '{plant_name}' (сообщение {sent_message.message_id}) пользователю {user_id}")

    except Exception as e:
        logging.error(f"Не удалось отправить фото для растения '{plant_name}' пользователю {user_id}: {e}")
        # Информируем пользователя о сбое, если возможно
        try:
            await context.bot.send_message(chat_id=user_id, text=f"Не удалось отобразить информацию для '{plant_name}'. Попробуйте еще раз.")
        except Exception as inner_e:
             logging.error(f"Не удалось отправить сообщение об ошибке пользователю {user_id}: {inner_e}")

async def plant_close_callback(update: Update, context: CallbackContext):
    """Обработчик кнопки 'Закрыть' — просто удаляет сообщение."""
    query = update.callback_query
    try:
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
    await query.answer()

async def delete_plant_callback(update: Update, context: CallbackContext):
    """Обработчик кнопки удаления растения."""
    query = update.callback_query
    user_id = query.from_user.id
    plant_name = query.data.split("_", 2)[1]

    delete_user_plant(user_id, plant_name)

    await query.answer(f"✅ Растение '{plant_name}' удалено.", show_alert=True)

    # Удаляем сообщение с деталями растения
    if user_id in user_plant_messages:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=user_plant_messages[user_id])
            del user_plant_messages[user_id]
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")

    # Обновляем сообщение со списком растений
    message_text, keyboard = await generate_plants_buttons(user_id)

    if keyboard and user_id in user_plants_list_messages:
        try:
            await context.bot.edit_message_text(
                chat_id=user_id,
                message_id=user_plants_list_messages[user_id],
                text=message_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Ошибка при обновлении списка растений: {e}")



async def handle_sorting(update: Update, context: CallbackContext):
    """Обрабатывает сортировку списка растений."""
    query = update.callback_query
    user_id = query.from_user.id

    # Определяем, по какому полю сортировать
    sort_by = query.data.split("_")[1]  # 'sort_name' -> 'name'

    # Получаем обновленный список растений с учетом сортировки
    message_text, keyboard = await generate_plants_buttons(user_id, sort_by)

    # Обновляем сообщение, к которому прикреплены кнопки
    await query.message.edit_text(text=message_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    # Подтверждаем обработку нажатия кнопки
    await query.answer()

def extract_watering(text: str, label: str) -> int | None:
    """
    Извлекает среднее количество дней между поливами из текста между двумя метками.
    `label` может быть 'Полив зимой' или 'Полив летом'.
    """
    # Определяем границы фрагмента
    if label == "Полив зимой":
        pattern_start = r"4\)\s*Полив зимой.*?"
        pattern_end = r"5\)"
    elif label == "Полив летом":
        pattern_start = r"5\)\s*Полив летом.*?"
        pattern_end = r"6\)"
    else:
        return None

    # Извлекаем нужный фрагмент текста
    match = re.search(f"({pattern_start})(.*?)(?={pattern_end})", text, re.DOTALL)
    if not match:
        return None

    fragment = match.group(2)  # Только содержательная часть между метками

    # Ищем все числа в диапазоне
    numbers = list(map(int, re.findall(r"\d+", fragment)))
    if not numbers:
        return None
    elif len(numbers) >= 2:
        avg = sum(numbers[:2]) // 2
    else:
        avg = numbers[0]

    return avg

def extract_number(text, label):
    """Извлекает одно число из текста."""
    match = re.search(fr"{label}[:\s]+(\d+)", text)
    return int(match.group(1)) if match else None

def extract_avg_number(text, label):
    """Извлекает среднее число из диапазона либо одно число, включая отрицательные значения."""
    match = re.search(fr"{label}[:\s]+(-?\d+)[\-/–]?(-?\d+)?", text)
    if match:
        numbers = [int(n) for n in match.groups() if n]
        return sum(numbers) // len(numbers) if numbers else None
    return None


def truncate_text_with_link(text: str, max_length: int, link: str | None, scientific_name_raw: str) -> str:
    """
    Обрезает УЖЕ ЭКРАНИРОВАННЫЙ текст до max_length символов (учитывая длину ссылки),
    добавляет ссылку на статью или Google-поиск, с корректным MarkdownV2.
    Предполагается, что входной 'text' уже прошел через escape_markdown_v2.
    """
    # Экранируем троеточие
    ellipsis = r'' # Используем r'' для ясности или просто '\.\.\.'

    # Экранируем имя для использования в тексте ссылки
    escaped_scientific_name_for_link_text = escape_markdown_v2(scientific_name_raw)

    # Формируем Markdown ссылки (URL НЕ экранируем, текст ссылки - экранируем)
    if link:
        # Используем экранированное имя в тексте ссылки
        link_text_part = f"Узнать больше о {escaped_scientific_name_for_link_text} на Википедии"
        # Не нужно дополнительно экранировать link_text_part, т.к. имя уже экранировано
        link_markdown = f"\n[{link_text_part}]({link})" # URL link не экранируется
    else:
        # URL для Google должен быть URL-кодирован, но не Markdown-экранирован
        # Используем необработанное имя для запроса в Google
        Google_Search_query = scientific_name_raw.replace(' ', '+') # Простое кодирование для URL
        Google_Search_link = f"https://www.google.com/search?q={Google_Search_query}"
        link_text_part = f"Найти {escaped_scientific_name_for_link_text} в Google"
        # Не нужно дополнительно экранировать link_text_part
        link_markdown = f"\n[{link_text_part}]({Google_Search_link})" # URL не экранируется

    # Вычисляем допустимую длину для ОСНОВНОГО ТЕКСТА (уже экранированного)
    # Считаем, что max_length - это ОБЩАЯ желаемая длина для текста + троеточия + ссылки
    available_length = max_length - len(link_markdown) - len(ellipsis)

    # Убедимся, что доступная длина не отрицательная
    if available_length < 0:
        available_length = 0 # Не можем отобразить текст, только ссылку

    # Обрезаем УЖЕ ЭКРАНИРОВАННЫЙ текст, если нужно
    if len(text) > available_length:
        # Обрезаем экранированный текст и добавляем экранированное троеточие
        truncated_text = text[:available_length].rstrip() + ellipsis # rstrip() убирает пробелы перед ...
    else:
        truncated_text = text

    # Возвращаем финальный текст (уже экранированный) + корректно сформированную Markdown-ссылку
    return truncated_text + link_markdown










async def help_command(update: Update, context: CallbackContext) -> None:
    """Обработчик для кнопки 'Помощь по GPT'."""
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие

    HELP_TEXT = """▶️Пост в Анемоне формируется из двух частей - непосредственно сам пост, видимый в телеграме, плюс статья Telagraph, доступная по ссылке (для примера посмотрите любой из последних постов в группе). Бот позволяет сделать обе части.  

    ▶️Статья в Telegraph формируется в порядке отправки вами изображений и текста боту.  
    Во время создания статьи, с помощью соответствующих кнопок вы можете:  
    - открыть предпросмотр телеграф статьи;  
    - удалить последний добавленный элемент (работает неограниченное количество раз, пока статья не станет пустой);  
    - редактировать всё содержимое вашей статьи через список добавленных изображений и текста. С любым фрагментом можно делать что угодно: менять текст на изображение и наоборот, удалять, исправлять. Однако это возможно только до тех пор, пока вы не используете кнопку "К Завершению Публикации". После её нажатия редактировать статью уже будет нельзя, только наполнить новую.  

    ▶️Поддерживаемые тэги разметки статьи:  
    - <code>***</code> — горизонтальная линия-разделитель (отправьте три звёздочки отдельным сообщением, в этом месте в статье Telegraph появится разделитель);  
    - <code>_текст_</code> — курсив;  
    - <code>*текст*</code> — жирный текст;  
    - <code>[текст ссылки](ссылка)</code> — гиперссылка;  
    - <code>видео:</code> — вставка видео с Vimeo или YouTube;  
    - <code>цитата:</code> — цитата;  
    - <code>цитата по центру:</code> — центрированная цитата;  
    - <code>заголовок:</code> — заголовок;  
    - <code>подзаголовок:</code> — подзаголовок.  

    Последние 5 тэгов пишутся в начале сообщения и применяются ко всему сообщению целиком. Каждое новое сообщение — это новый абзац. Сообщения без тэгов — обычный текст.  

    Пример:  
    - <pre>цитата: *Волк* никогда не будет жить в загоне, но загоны всегда будут жить в *волке*</pre> — в статье Telegraph примет вид цитаты, в которой слово "волк" выделено жирным;  
    - <pre>видео: ссылка_на_видео</pre> — вставка интерактивного видео YouTube или Vimeo.  



    """

    keyboard = [
        [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')],
        [InlineKeyboardButton("Удалить последний элемент", callback_data='delete_last')],
        [InlineKeyboardButton("Ссылка на статью", callback_data='preview_article')],
        [InlineKeyboardButton("Редактировать", callback_data='edit_article')],
        [InlineKeyboardButton("🌠 К Завершению Публикации 🌠", callback_data='create_article')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Отправляем сообщение с кнопкой
    await query.edit_message_text(HELP_TEXT, parse_mode="HTML", reply_markup=reply_markup)




async def handle_artist_link(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    if user_id in user_data and user_data[user_id]['status'] == 'awaiting_artist_link':
        user_data[user_id]['artist_link'] = update.message.text
        logger.info(f"User {user_id} provided author link:")


        await update.message.reply_text(
            '🌟Хорошо. Теперь отправьте имя автора. \n\n <i>Чтобы скрыть слово "Автор:", используйте символ "^" в начале и конце сообщения. Например: ^Имя^</i>',
            parse_mode='HTML' # Добавляем клавиатуру
        )
        user_data[user_id]['status'] = 'awaiting_author_name'
        return ASKING_FOR_AUTHOR_NAME
    else:
        await update.message.reply_text('🚫Ошибка: данные не найдены.')
        return ConversationHandler.END

# Ввод имени художника
async def handle_author_name(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id

    # Проверка, что пользователь находится в нужном состоянии
    if user_id in user_data and user_data[user_id].get('status') == 'awaiting_author_name':

        # Если авторское имя ещё не сохранено
        if 'author_name' not in user_data[user_id]:
            author_input = update.message.text.strip()

            # Проверяем, если авторское имя обернуто в "^...^"
            match_full = re.match(r'^\^(.*)\^$', author_input, re.S)
            if match_full:
                # Если весь текст внутри "^...^", используем его как заголовок и убираем авторское имя
                title = match_full.group(1).strip()
                user_data[user_id]['title'] = title
                user_data[user_id]['author_name'] = ""  # Очищаем author_name
                user_data[user_id]['extra_phrase'] = ""  # Нет доп. фразы
            else:
                # Проверка на наличие фразы в начале текста "^...^"
                match_partial = re.match(r'^\^(.*?)\^\s*(.*)', author_input, re.S)
                if match_partial:
                    # Извлекаем фразу и имя автора
                    phrase = match_partial.group(1).strip()  # Фраза из "^...^"
                    author_name = match_partial.group(2).strip()  # Остаток текста как автор
                    user_data[user_id]['extra_phrase'] = phrase  # Сохраняем фразу
                    user_data[user_id]['author_name'] = author_name  # Имя автора
                    user_data[user_id]['title'] = author_name  # Используем как заголовок
                else:
                    # Если нет фразы в "^...^", сохраняем всё как имя автора
                    author_name = author_input
                    user_data[user_id]['author_name'] = author_name
                    user_data[user_id]['title'] = author_name  # Заголовок статьи

        else:
            # Если author_name уже есть, просто используем его для заголовка
            author_name = user_data[user_id]['author_name']
            user_data[user_id]['title'] = author_name  # Обновляем заголовок

        # Переход к следующему этапу
        keyboard = [
            [InlineKeyboardButton("Помощь и разметка", callback_data='help_command')],
            [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            'Отлично \n🌌Теперь приступим к наполнению публикации контентом. Отправьте изображения файлом (без сжатия) или текст. Если вы отправите изображение с подписью, то в статье телеграф текст будет так же отображаться как подпись под изображением.\n\n'
            'Текст поддерживает различное форматирование. Для получения списка тэгов нажмите на кнопку помощи.\n\n'
            '<i>Так же вы можете переслать в бот сообщения с текстом и/или изображениями, и бот тут же автоматически перенесет всё это в статью в той же очерёдности</i>',
            parse_mode='HTML',
            reply_markup=reply_markup  # Добавляем клавиатуру
        )
        user_data[user_id]['status'] = 'awaiting_image'
        return ASKING_FOR_IMAGE

    else:
        await update.message.reply_text('🚫Ошибка: данные не найдены. Попробуйте снова или нажмите /restart.')
        return ConversationHandler.END



def compress_image(file_path: str, output_path: str) -> None:
    # Определяем максимальный размер файла в байтах (5 МБ)
    max_size = 5 * 1024 * 1024

    # Проверяем, является ли файл GIF или .rar
    if file_path.endswith('.gif') or file_path.endswith('.rar'):
        return

    # Открываем изображение
    with Image.open(file_path) as img:
        # Проверяем формат и размер изображения
        if img.format == 'PNG' and os.path.getsize(file_path) > max_size:
            # Если PNG и размер больше 5 МБ, конвертируем в JPG
            img = img.convert('RGB')
            temp_path = file_path.rsplit('.', 1)[0] + '.jpg'
            img.save(temp_path, format='JPEG', quality=90)
            file_path = temp_path
            img = Image.open(file_path)
        
        # Если изображение имеет альфа-канал, преобразуем его в RGB
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            img = img.convert('RGB')

        # Сохраняем изображение в формате JPG с начальным качеством
        quality = 90
        img.save(output_path, format='JPEG', quality=quality)

        # Проверяем размер файла и сжимаем при необходимости
        while os.path.getsize(output_path) > max_size:
            quality -= 10
            if quality < 10:
                break
            img.save(output_path, format='JPEG', quality=quality)

        # Если изображение всё ещё больше 5 МБ, уменьшаем разрешение
        while os.path.getsize(output_path) > max_size:
            width, height = img.size
            img = img.resize((width // 2, height // 2), Image.Resampling.LANCZOS)  # Заменён ANTIALIAS
            img.save(output_path, format='JPEG', quality=quality)

        # Удаляем временный JPG файл, если он был создан
        if file_path.endswith('.jpg'):
            os.remove(file_path)

# Функция для загрузки изображения на сloudinary
async def upload_image_to_cloudinary(file_path: str) -> str:
    CLOUDINARY_URL = 'https://api.cloudinary.com/v1_1/dmacjjaho/image/upload'
    UPLOAD_PRESET = 'ml_default'
    timeout = ClientTimeout(total=10)  # Таймаут в 10 секунд    
    
    async with aiohttp.ClientSession() as session:
        with open(file_path, 'rb') as f:
            form = aiohttp.FormData()
            form.add_field('file', f)
            form.add_field('upload_preset', UPLOAD_PRESET)

            async with session.post(CLOUDINARY_URL, data=form) as response:
                if response.status == 200:
                    response_json = await response.json()
                    return response_json['secure_url']
                else:
                    response_text = await response.text()  # Логируем текст ошибки
                    raise Exception(f"Ошибка загрузки на Cloudinary: {response.status}, ответ: {response_text}")


# Функция для загрузки изображения на imgbb
async def upload_image_to_imgbb(file_path: str) -> str:
    timeout = aiohttp.ClientTimeout(total=4)  # Таймаут в 4 секунды
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            with open(file_path, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field('key', IMGBB_API_KEY)
                form.add_field('image', f)

                async with session.post('https://api.imgbb.com/1/upload', data=form) as response:
                    response_text = await response.text()  # Читаем полный ответ от сервера
                    
                    if response.status == 200:
                        response_json = await response.json()
                        return response_json['data']['url']
                    else:
                        logging.error(f"Ошибка загрузки на imgbb: {response.status}, ответ: {response_text}")
                        raise Exception(f"Ошибка загрузки на imgbb: {response.status}, ответ: {response_text}")
        except Exception as e:
            logging.exception(f"Ошибка при загрузке изображения: {e}")
            raise

# Функция для загрузки изображения на Imgur
async def upload_image_to_imgur(file_path: str) -> str:
    IMGUR_CLIENT_ID = '5932e0bc7fdb523'  # Укажите свой ID клиента Imgur
    headers = {'Authorization': f'Client-ID {IMGUR_CLIENT_ID}'}
    async with aiohttp.ClientSession() as session:
        with open(file_path, 'rb') as f:
            form = aiohttp.FormData()
            form.add_field('image', f)

            async with session.post('https://api.imgur.com/3/image', headers=headers, data=form) as response:
                if response.status == 200:
                    response_json = await response.json()
                    return response_json['data']['link']
                else:
                    raise Exception(f"Ошибка загрузки на Imgur: {response.status}")

# Функция для загрузки изображения на Catbox
async def upload_image_to_catbox(file_path: str) -> str:
    async with aiohttp.ClientSession() as session:
        with open(file_path, 'rb') as f:
            form = aiohttp.FormData()
            form.add_field('reqtype', 'fileupload')
            form.add_field('fileToUpload', f)
            
            # Добавляем ваш userhash
            form.add_field('userhash', '1f68d2a125c66f6ab79a4f89c')

            async with session.post('https://catbox.moe/user/api.php', data=form) as response:
                if response.status == 200:
                    return await response.text()  # возвращает URL загруженного файла
                else:
                    raise Exception(f"Ошибка загрузки на Catbox: {response.status}")

async def upload_image_to_freeimage(file_path: str) -> str:
    async with aiohttp.ClientSession() as session:
        with open(file_path, 'rb') as f:
            form = aiohttp.FormData()
            form.add_field('key', '6d207e02198a847aa98d0a2a901485a5')  # Ваш API ключ для freeimage.host
            form.add_field('action', 'upload')
            form.add_field('source', f)  # Используем файл для загрузки

            async with session.post('https://freeimage.host/api/1/upload', data=form) as response:
                if response.status == 200:
                    response_json = await response.json()
                    return response_json['image']['url']  # Проверьте правильность пути к URL в ответе
                elif response.status == 400:
                    response_text = await response.text()
                    raise Exception(f"Ошибка загрузки на Free Image Hosting: {response_text}")
                else:
                    raise Exception(f"Ошибка загрузки на Free Image Hosting: {response.status}")

from imagekitio import ImageKit

imagekit = ImageKit(
    public_key='public_yUK3D2wI8elYAhJMfsRIlS2tDR0=',
    private_key='private_R4rPdLI6gLW/y1KyjSn/5+QrvVo=',
    url_endpoint='https://ik.imagekit.io/hijnwtjlc'
)

async def upload_image_to_imagekit(file_path: str) -> str:
    try:
        upload = imagekit.upload(
            file=open(file_path, "rb"),
            file_name=os.path.basename(file_path),
        )
        return upload.url
    except Exception as e:
        logging.error(f"Ошибка загрузки на ImageKit: {e}")
        raise


# Основная функция загрузки изображения с проверкой доступности сервисов
async def upload_image(file_path: str) -> str:
    try:
        # Попытка загрузки на ImageKit
        return await upload_image_to_imagekit(file_path)
    except Exception as e:
        logging.error(f"Ошибка загрузки на ImageKit: {e}")
        
        try:
            # Попытка загрузки на imgbb
            return await upload_image_to_imgbb(file_path)
        except Exception as e:
            logging.error(f"Ошибка загрузки на imgbb: {e}")

            try:
                # Попытка загрузки на Free Image Hosting
                return await upload_image_to_freeimage(file_path)
            except Exception as e:
                logging.error(f"Ошибка загрузки на Free Image Hosting: {e}")
                
                try:
                    # Попытка загрузки на Imgur
                    return await upload_image_to_imgur(file_path)
                except Exception as e:
                    logging.error(f"Ошибка загрузки на Imgur: {e}")
                    
                    try:
                        # Попытка загрузки на Cloudinary
                        return await upload_image_to_cloudinary(file_path)
                    except Exception as e:
                        logging.error(f"Ошибка загрузки на Cloudinary: {e}")
                        raise Exception("Не удалось загрузить изображение на все сервисы.")



# Определяем разметку тегов
markup_tags = {
    '*': 'strong',  # Жирный текст
    '_': 'em',      # Курсив
}


def apply_markup(text: str) -> dict:
    """Применяет разметку к тексту на основе команд и возвращает узел контента в формате Telegra.ph."""
    
    text = text.strip()  # Убираем пробелы в начале и в конце текста
    text_lower = text.lower()

    # Обработка команд
    if text_lower.startswith("подзаголовок: "):
        content = text[len("Подзаголовок: "):].strip()
        content = apply_markup_to_content(content)
        return {"tag": "h4", "children": content}
    elif text_lower.startswith("цитата:"):
        content = text[len("Цитата:"):].strip()
        content = apply_markup_to_content(content)
        return {"tag": "blockquote", "children": content}
    elif text_lower.startswith("заголовок: "):
        content = text[len("Заголовок: "):].strip()
        content = apply_markup_to_content(content)
        return {"tag": "h3", "children": content}
    elif text_lower.startswith("цитата по центру:"):
        content = text[len("Цитата по центру:"):].strip()
        content = apply_markup_to_content(content)
        return {"tag": "aside", "children": content}
    elif text_lower.startswith("***"):
        return {"tag": "hr"}
    elif text_lower.startswith("видео: "):
        video_url = text[len("Видео: "):].strip()
        # Кодируем URL, чтобы он подходил для использования в src
        encoded_url = re.sub(r'https://', 'https%3A%2F%2F', video_url)
        
        # Проверяем, это YouTube или Vimeo
        if "youtube.com" in video_url or "youtu.be" in video_url:
            return {
                "tag": "figure",
                "children": [
                    {
                        "tag": "iframe",
                        "attrs": {
                            "src": f"/embed/youtube?url={encoded_url}",
                            "width": 640,
                            "height": 360,
                            "frameborder": 0,
                            "allowtransparency": "true",
                            "allowfullscreen": "true",
                            "scrolling": "no"
                        }
                    }
                ]
            }
        elif "vimeo.com" in video_url:
            return {
                "tag": "figure",
                "children": [
                    {
                        "tag": "iframe",
                        "attrs": {
                            "src": f"/embed/vimeo?url={encoded_url}",
                            "width": 640,
                            "height": 360,
                            "frameborder": 0,
                            "allowtransparency": "true",
                            "allowfullscreen": "true",
                            "scrolling": "no"
                        }
                    }
                ]
            }

    # Если команда не распознана, обрабатываем текст с разметкой
    content = apply_markup_to_content(text)
    return {"tag": "div", "children": content}

def apply_markup_to_content(content: str) -> list:
    """Обрабатывает разметку в тексте и возвращает список узлов для Telegra.ph."""
    nodes = []

    # Регулярные выражения для разметки
    regex_markup = re.compile(r'(\*|_)(.*?)\1', re.DOTALL)
    link_regex = re.compile(r'\[(.*?)\]\((.*?)\)', re.DOTALL)

    # Сначала обрабатываем гиперссылки
    pos = 0
    temp_nodes = []
    for match in link_regex.finditer(content):
        # Добавляем текст до текущего совпадения
        if pos < match.start():
            temp_nodes.append(content[pos:match.start()])

        # Добавляем узел ссылки
        link_text, url = match.groups()
        temp_nodes.append({"tag": "a", "attrs": {"href": url}, "children": [{"tag": "text", "children": [link_text]}]})

        # Обновляем позицию
        pos = match.end()

    # Добавляем оставшийся текст после обработки гиперссылок
    if pos < len(content):
        temp_nodes.append(content[pos:])

    # Теперь обрабатываем остальную разметку
    for node in temp_nodes:
        if isinstance(node, str):
            # Обрабатываем текст с разметкой
            while True:
                match = regex_markup.search(node)
                if not match:
                    # Если больше нет совпадений, добавляем оставшийся текст
                    nodes.append({"tag": "text", "children": [node]})
                    break
                # Добавляем текст до текущего совпадения
                if match.start() > 0:
                    nodes.append({"tag": "text", "children": [node[:match.start()]]})

                # Определяем тег и добавляем узел
                tag = markup_tags.get(match.group(1))
                if tag:
                    nodes.append({"tag": tag, "children": [match.group(2)]})

                # Обновляем строку: обрезаем её до конца текущего совпадения
                node = node[match.end():]
        else:
            nodes.append(node)

    return nodes

async def edit_article(update: Update, context: CallbackContext) -> None:
    # Проверяем, является ли обновление запросом обратного вызова (нажатие кнопки)
    if update.callback_query:
        query = update.callback_query
        user_id = query.from_user.id
    else:
        user_id = update.message.from_user.id  # Если это сообщение, получаем ID пользователя

    media = user_data[user_id].get('media', [])
    
    if not media:
        await update.message.reply_text("🚫 Ошибка: нет фрагментов для редактирования.")
        return

    # Удаляем предыдущее сообщение с кнопками содержания статьи
    if 'last_content_message_id' in user_data[user_id]:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,  # Используем effective_chat
                message_id=user_data[user_id]['last_content_message_id']
            )
        except Exception as e:
            print(f"Ошибка при удалении сообщения с содержанием: {e}")

    # Настройки пагинации
    items_per_page = 30  # Количество кнопок на странице
    total_pages = (len(media) + items_per_page - 1) // items_per_page  # Общее количество страниц
    current_page = user_data[user_id].get('current_page', 0)  # Текущая страница

    # Ограничиваем текущую страницу
    current_page = max(0, min(current_page, total_pages - 1))
    
    # Создаем новый список кнопок для текущей страницы
    keyboard = []
    image_counter = 1  # Счётчик для изображений
    start_idx = current_page * items_per_page
    end_idx = min(start_idx + items_per_page, len(media))

    for idx in range(start_idx, end_idx):
        item = media[idx]
        if item['type'] == 'text':
            text = item['content']
            if isinstance(text, dict) and 'children' in text:
                try:
                    text = ''.join(
                        str(child['children'][0]) if isinstance(child['children'][0], str) else ''
                        for child in text['children']
                        if isinstance(child, dict) and 'children' in child
                    )
                except Exception as e:
                    print(f"Ошибка при обработке текста: {e}")
                    print(f"Текстовые данные: {text}")
                    text = "Ошибка обработки текста"
            preview_text = (text[:12] + '...') if len(text) > 12 else text
        else:
            preview_text = f"{image_counter} изображение"
            image_counter += 1
        
        keyboard.append([
            InlineKeyboardButton(text=str(preview_text), callback_data=f"preview_{idx}"),
            InlineKeyboardButton(text="Редактировать", callback_data=f"edit_{idx}"),
            InlineKeyboardButton(text="Удалить", callback_data=f"delete_{idx}"),
        ])

    # Добавляем кнопки навигации, если это не первая страница
    if current_page > 0:
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='page_down')])
    
    # Добавляем кнопки навигации, если это не последняя страница
    if current_page < total_pages - 1:
        keyboard.append([InlineKeyboardButton("Вперёд ➡️", callback_data='page_up')])
    
    keyboard.append([InlineKeyboardButton("🌌 Предпросмотр ссылки 🌌", callback_data='preview_article')])
    keyboard.append([InlineKeyboardButton("Помощь и разметка", callback_data='help_command')])
    keyboard.append([InlineKeyboardButton("🌠 К Завершению Публикации 🌠", callback_data='create_article')])
    # Отправляем новое сообщение и сохраняем его ID
    sent_message = await (query.message if update.callback_query else update.message).reply_text(
        "Выберите фрагмент для редактирования или удаления:", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    # Сохраняем ID нового сообщения с кнопками
    user_data[user_id]['last_content_message_id'] = sent_message.message_id
    user_data[user_id]['current_page'] = current_page  # Сохраняем текущую страницу



async def handle_edit_delete(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    action, index = query.data.split('_')
    index = int(index)

    media = user_data[user_id].get('media', [])

    # Проверяем, существует ли фрагмент с таким индексом
    if index >= len(media):
        await query.message.reply_text("🚫 Ошибка: указанный индекс недействителен.")
        return

    if action == 'edit':
        # Если тип контента — изображение, предлагаем отправить новое изображение
        if media[index]['type'] == 'image':
            context.user_data['editing_index'] = index
            await query.message.reply_text("Пожалуйста, отправьте новое изображение или текст:")
            return ASKING_FOR_IMAGE  # Переход к ожиданию нового изображения
        # Если тип контента — текст, предлагаем ввести новый текст
        elif media[index]['type'] == 'text':
            context.user_data['editing_index'] = index
            await query.message.reply_text("Пожалуйста, отправьте новое изображение или текст:")
            return EDITING_FRAGMENT  # Переходим в состояние редактирования текста

    elif action == 'delete':
        if index < len(media):
            media.pop(index)
            user_data[user_id]['media'] = media  # Сохраняем изменения

            # Обновляем кнопки
# Количество кнопок на одной странице
            PAGE_SIZE = 30

            # Получаем текущую страницу из user_data (по умолчанию 1)
            if 'page' not in user_data[user_id]:
                user_data[user_id]['page'] = 1
            current_page = user_data[user_id]['page']

            # Обновляем кнопки
            keyboard = []
            image_counter = 1  # Счётчик для изображений

            # Подсчёт общего количества элементов
            total_items = len(media)
            total_pages = (total_items + PAGE_SIZE - 1) // PAGE_SIZE  # Рассчитываем количество страниц

            # Показ элементов только для текущей страницы
            start_idx = (current_page - 1) * PAGE_SIZE
            end_idx = start_idx + PAGE_SIZE

            for idx, item in enumerate(media[start_idx:end_idx], start=start_idx):
                if item['type'] == 'text':
                    text = item['content']
                    
                    # Извлечение текста, если нужно
                    if isinstance(text, dict) and 'children' in text:
                        text = ''.join(child['children'][0] for child in text['children'] if isinstance(child, dict) and 'children' in child)
                    
                    preview_text = (text[:12] + '...') if len(text) > 12 else text
                else:  # Если элемент — это изображение
                    preview_text = f"{image_counter} изображение"  # Нумерация только для изображений
                    image_counter += 1  # Увеличиваем счётчик только для изображений
                
                # Добавляем кнопки для текущей страницы
                keyboard.append([
                    InlineKeyboardButton(text=str(preview_text), callback_data=f"preview_{idx}"),
                    InlineKeyboardButton(text="Редактировать", callback_data=f"edit_{idx}"),
                    InlineKeyboardButton(text="Удалить", callback_data=f"delete_{idx}"),
                ])

            # Добавляем кнопки для переключения страниц
            navigation_buttons = []
            if current_page > 1:
                navigation_buttons.append(InlineKeyboardButton("⬆️ Предыдущая страница", callback_data=f"prev_page_{current_page - 1}"))
            if current_page < total_pages:
                navigation_buttons.append(InlineKeyboardButton("⬇️ Следующая страница", callback_data=f"next_page_{current_page + 1}"))

            if navigation_buttons:
                keyboard.append(navigation_buttons)

            # Добавляем кнопку предпросмотра
            keyboard.append([InlineKeyboardButton("🌌 Предпросмотр ссылки 🌌", callback_data='preview_article')])
            keyboard.append([InlineKeyboardButton("Помощь и разметка", callback_data='help_command')])
            keyboard.append([InlineKeyboardButton("🌠 К Завершению Публикации 🌠", callback_data='create_article')])

            # Отправляем новое сообщение с обновлённым списком кнопок
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_reply_markup(reply_markup=reply_markup)  # Обновляем клавиатуру

            await query.message.reply_text("✅ Фрагмент удалён.")
        return





async def handle_new_text(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    index = context.user_data['editing_index']
    media = user_data[user_id].get('media', [])

    # Убедимся, что индекс действителен
    if index >= 0 and index < len(media):
        # Если редактируемый элемент — это текст
        if media[index]['type'] == 'text':
            # Обновляем текст
            formatted_text = apply_markup(update.message.text)
            media[index] = {  # Обновляем существующий текст
                'type': 'text',
                'content': formatted_text
            }
            user_data[user_id]['media'] = media  # Сохраняем изменения

            # Удаляем предыдущее сообщение с кнопками содержания статьи
            if 'last_content_message_id' in user_data[user_id]:
                try:
                    await context.bot.delete_message(
                        chat_id=update.message.chat_id, 
                        message_id=user_data[user_id]['last_content_message_id']
                    )
                except Exception as e:
                    print(f"Ошибка при удалении сообщения с содержанием: {e}")

            # Настройки пагинации
            items_per_page = 30  # Количество кнопок на странице
            total_pages = (len(media) + items_per_page - 1) // items_per_page  # Общее количество страниц
            current_page = user_data[user_id].get('current_page', 0)  # Текущая страница

            # Ограничиваем текущую страницу
            current_page = max(0, min(current_page, total_pages - 1))


            # Создаём новый список кнопок для содержания статьи
    # Создаем новый список кнопок для текущей страницы
            keyboard = []
            image_counter = 1  # Счётчик для изображений
            start_idx = current_page * items_per_page
            end_idx = min(start_idx + items_per_page, len(media))

            for idx, item in enumerate(media):
                item = media[idx]
                if item['type'] == 'text':
                    text = item['content']
                    
                    # Извлечение текста, если нужно
                    if isinstance(text, dict) and 'children' in text:
                        text = ''.join(child['children'][0] for child in text['children'] if isinstance(child, dict) and 'children' in child)
                    
                    preview_text = (text[:12] + '...') if len(text) > 12 else text
                else:  # Если элемент — это изображение
                    preview_text = f"{image_counter} изображение"  # Нумерация только для изображений
                    image_counter += 1  # Увеличиваем счётчик только для изображений
                
                # Добавляем кнопки для предпросмотра, редактирования и удаления
                keyboard.append([
                    InlineKeyboardButton(text=str(preview_text), callback_data=f"preview_{idx}"),
                    InlineKeyboardButton(text="Редактировать", callback_data=f"edit_{idx}"),
                    InlineKeyboardButton(text="Удалить", callback_data=f"delete_{idx}"),
                ])

            if current_page > 0:
                keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='page_down')])
            
            # Добавляем кнопки навигации, если это не последняя страница
            if current_page < total_pages - 1:
                keyboard.append([InlineKeyboardButton("Вперёд ➡️", callback_data='page_up')])
            

            keyboard.append([
                InlineKeyboardButton("🌌 Предпросмотр статьи🌌 ", callback_data='preview_article')
            ])    

            # Отправляем новое сообщение с обновлённым списком кнопок
            reply_markup = InlineKeyboardMarkup(keyboard)
            sent_message = await context.bot.send_message(
                chat_id=update.message.chat_id,
                text='📝 Текущее содержание статьи2:',
                reply_markup=reply_markup
            )

            # Сохраняем ID нового сообщения с кнопками
            user_data[user_id]['last_content_message_id'] = sent_message.message_id
            user_data[user_id]['current_page'] = current_page  
            # Сообщаем пользователю об успешном обновлении текста
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text='✅ Текст обновлён.',
                reply_to_message_id=update.message.message_id
            )

            # Удаляем индекс редактирования после завершения
            del context.user_data['editing_index']

            return ASKING_FOR_IMAGE
        else:
            # Ошибка, если тип редактируемого элемента не текст
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text='🚫 Ошибка: указанный элемент не является текстом.',
                reply_to_message_id=update.message.message_id
            )
            del context.user_data['editing_index']  # Удаляем индекс, если он недействителен
            return ConversationHandler.END
    else:
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text='🚫 Ошибка: указанный индекс недействителен.',
            reply_to_message_id=update.message.message_id
        )
        del context.user_data['editing_index']  # Удаляем индекс, если он недействителен
        return ConversationHandler.END


async def handle_new_image(update: Update, context: CallbackContext, index: int, media: list) -> int:
    user_id = update.message.from_user.id
    message_id = update.message.message_id

    if update.message.photo or update.message.document:
        if update.message.photo:
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text='🚫 Ошибка: пожалуйста, отправьте изображение как файл (формат JPG, PNG или .RAR для .GIF), без сжатия. Для подробностей введите /help',
                reply_to_message_id=message_id
            )
            return ASKING_FOR_IMAGE 

        elif update.message.document:
            file_name = update.message.document.file_name
            file_ext = file_name.lower().split('.')[-1]
            file = await context.bot.get_file(update.message.document.file_id)

        # Создаем временный файл для сохранения изображения
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as tmp_file:
            file_path = tmp_file.name
            await file.download_to_drive(file_path)

        if file_ext == 'rar':
            new_file_path = f'{os.path.splitext(file_path)[0]}.gif'
            shutil.move(file_path, new_file_path)
            file_path = new_file_path
            file_name = os.path.basename(file_path)
            file_ext = 'gif'

        if file_ext in ('jpg', 'jpeg', 'png', 'gif'):
            if file_ext == 'gif':
                try:
                    image_url = await upload_image(file_path)
                    media[index] = {  # Обновляем существующее изображение
                        'type': 'image',
                        'url': image_url,
                        'caption': update.message.caption if update.message.caption else ""
                    }
                    user_data[user_id]['media'] = media  # Сохраняем изменения

                    # Удаляем предыдущее сообщение, если оно есть
                    if 'last_image_message_id' in user_data[user_id]:
                        try:
                            await context.bot.delete_message(chat_id=update.message.chat_id, message_id=user_data[user_id]['last_image_message_id'])
                        except Exception as e:
                            print(f"Ошибка при удалении сообщения: {e}")

                    # Отправляем новое сообщение
                    sent_message = await context.bot.send_message(
                        chat_id=update.message.chat_id,
                        text='✅ Изображение очень обновлено.',
                        reply_to_message_id=message_id
                    )

                    # Сохраняем ID нового сообщения
                    user_data[user_id]['last_image_message_id'] = sent_message.message_id

                    # Удаляем индекс редактирования после завершения
                    del context.user_data['editing_index']

                    return ASKING_FOR_IMAGE
                except Exception as e:
                    await context.bot.send_message(
                        chat_id=update.message.chat_id,
                        text=f'🚫 Ошибка при загрузке изображения: {str(e)}. Попробуйте снова.',
                        reply_to_message_id=message_id
                    )
                    return ConversationHandler.END

            else:
                if os.path.getsize(file_path) > 5 * 1024 * 1024:
                    compressed_path = f'{os.path.splitext(file_path)[0]}_compressed.jpg'
                    compress_image(file_path, compressed_path)
                    file_path = compressed_path

                try:
                    image_url = await upload_image(file_path)
                    media[index] = {  # Обновляем существующее изображение
                        'type': 'image',
                        'url': image_url,
                        'caption': update.message.caption if update.message.caption else ""
                    }
                    user_data[user_id]['media'] = media  # Сохраняем изменения
                    os.remove(file_path)

                    # Удаляем предыдущее сообщение, если оно есть
                    if 'last_image_message_id' in user_data[user_id]:
                        try:
                            await context.bot.delete_message(chat_id=update.message.chat_id, message_id=user_data[user_id]['last_image_message_id'])
                        except Exception as e:
                            print(f"Ошибка при удалении сообщения: {e}")

                    # Отправляем новое сообщение
                    sent_message = await context.bot.send_message(
                        chat_id=update.message.chat_id,
                        text='✅ Изображение добавлено.',
                        reply_to_message_id=message_id
                    )

                    # Удаляем предыдущее сообщение с кнопками содержания статьи, если оно существует
                    if 'last_content_message_id' in user_data[user_id]:
                        try:
                            await context.bot.delete_message(
                                chat_id=update.message.chat_id, 
                                message_id=user_data[user_id]['last_content_message_id']
                            )
                        except Exception as e:
                            print(f"Ошибка при удалении сообщения с содержанием: {e}")


                    # Настройки пагинации
                    items_per_page = 30  # Количество кнопок на странице
                    total_pages = (len(media) + items_per_page - 1) // items_per_page  # Общее количество страниц
                    current_page = user_data[user_id].get('current_page', 0)  # Текущая страница

                    # Ограничиваем текущую страницу
                    current_page = max(0, min(current_page, total_pages - 1))

                    # Создаём новый список кнопок для содержания статьи
                    keyboard = []
                    image_counter = 1  # Счётчик для изображений
                    start_idx = current_page * items_per_page
                    end_idx = min(start_idx + items_per_page, len(media))
                    for idx in range(start_idx, end_idx):
                        item = media[idx]
                        if item['type'] == 'text':
                            text = item['content']
                            
                            # Извлечение текста, если нужно
                            if isinstance(text, dict) and 'children' in text:
                                text = ''.join(child['children'][0] for child in text['children'] if isinstance(child, dict) and 'children' in child)
                            
                            preview_text = (text[:12] + '...') if len(text) > 12 else text
                        else:  # Если элемент — это изображение
                            preview_text = f"Обн изобр-ие"  # Нумерация только для изображений
                            image_counter += 1  # Увеличиваем счётчик только для изображений
                        
                        # Добавляем кнопки для предпросмотра, редактирования и удаления
                        keyboard.append([
                            InlineKeyboardButton(text=str(preview_text), callback_data=f"preview_{idx}"),
                            InlineKeyboardButton(text="Редактировать", callback_data=f"edit_{idx}"),
                            InlineKeyboardButton(text="Удалить", callback_data=f"delete_{idx}"),
                        ])

                    if current_page > 0:
                        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='page_down')])
                    
                    # Добавляем кнопки навигации, если это не последняя страница
                    if current_page < total_pages - 1:
                        keyboard.append([InlineKeyboardButton("Вперёд ➡️", callback_data='page_up')])
                    
                    keyboard.append([
                        InlineKeyboardButton("🌌 Предпросмотр статьи🌌 ", callback_data='preview_article')
                    ])    

                    # Отправляем новое сообщение с обновлённым списком кнопок
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    sent_message = await context.bot.send_message(
                        chat_id=update.message.chat_id,
                        text='📝 Текущее содержание статьи1:',
                        reply_markup=reply_markup
                    )

                    # Сохраняем ID нового сообщения с кнопками
                    user_data[user_id]['last_content_message_id'] = sent_message.message_id
                    user_data[user_id]['current_page'] = current_page  

                    # Удаляем индекс редактирования после завершения
                    del context.user_data['editing_index']

                    return ASKING_FOR_IMAGE
                except Exception as e:
                    await context.bot.send_message(
                        chat_id=update.message.chat_id,
                        text=f'🚫 Ошибка при загрузке изображения: {str(e)}. Попробуйте снова.',
                        reply_to_message_id=message_id
                    )
                    return ConversationHandler.END

        else:
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text='Пожалуйста, отправьте изображение в формате JPG, PNG или .RAR для .GIF.',
                reply_to_message_id=message_id
            )
            return ASKING_FOR_IMAGE
    else:
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text='🚫 Ошибка: ожидается изображение или файл.',
            reply_to_message_id=message_id
        )
        return ConversationHandler.END




async def handle_image(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    caption = update.message.caption
    message_id = update.message.message_id
    if user_id in user_data and user_data[user_id]['status'] == 'twitter_image':
        logging.info(f"Автоматически загружаем изображения из twitter_data для {user_id}")

        media_files = user_data[user_id].get('media', [])
        uploaded_media = []

        for file_path in media_files:
            if not file_path or not isinstance(file_path, str):
                logging.warning(f"Некорректный путь к файлу: {file_path}")
                continue

            if not os.path.exists(file_path):
                logging.warning(f"Файл {file_path} не найден!")
                continue

            try:
                image_url = await upload_image(file_path)
                uploaded_media.append({'type': 'image', 'url': image_url, 'caption': caption or ""})
                os.remove(file_path)  # Удаляем локальный файл после загрузки
            except Exception as e:
                logging.error(f"Ошибка загрузки {file_path}: {str(e)}")

        # Очищаем директорию после загрузки
        if media_files:
            media_folder = os.path.dirname(media_files[0])
            shutil.rmtree(media_folder, ignore_errors=True)

        # Обновляем user_data: только media и image_counter, остальное сохраняем
        user_data[user_id]['media'] = uploaded_media
        user_data[user_id]['image_counter'] = len(uploaded_media)
        user_data[user_id]['status'] = 'awaiting_image'

        logging.info(f"Обновленный user_data: {user_data}")

        return ASKING_FOR_IMAGE
    # Проверяем, редактирует ли пользователь что-либо
    if 'editing_index' in context.user_data:
        index = context.user_data['editing_index']
        media = user_data[user_id].get('media', [])

        # Проверяем, если индекс действителен
        if 0 <= index < len(media):
            # Проверяем, если редактируем текст, и если получен текст
            if media[index]['type'] == 'text':
                # Если пользователь прислал текст, обрабатываем его как текст
                if update.message.text:
                    return await handle_new_text_from_image(update, context, index, media)

                # Если вместо текста пришло изображение
                if update.message.photo or update.message.document:
                    return await handle_new_image(update, context, index, media)

            # Проверяем, если редактируем изображение
            if media[index]['type'] == 'image':
                # Проверяем, если пользователь отправил текст вместо изображения
                if update.message.text:
                    return await handle_new_text_from_image(update, context, index, media)

                # Проверка фото
                if update.message.photo:
                    await context.bot.send_message(
                        chat_id=update.message.chat_id,
                        text='Пожалуйста, отправьте изображение как файл (формат JPG, PNG или .RAR для .GIF), без сжатия. Для подробностей введите /help',
                        reply_to_message_id=message_id
                    )
                    return ASKING_FOR_IMAGE

                elif update.message.document:
                    file_name = update.message.document.file_name
                    if file_name:  # Проверка, что файл имеет имя
                        file_ext = file_name.lower().split('.')[-1]

                        # Если не удается определить расширение, выходим
                        if not file_ext:
                            await context.bot.send_message(
                                chat_id=update.message.chat_id,
                                text='🚫 Ошибка: не удалось определить расширение файла. Пожалуйста, отправьте файл с правильным расширением.',
                                reply_to_message_id=message_id
                            )
                            return ConversationHandler.END

                        file = await context.bot.get_file(update.message.document.file_id)
                        # Скачивание и создание временного файла
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as tmp_file:
                            file_path = tmp_file.name
                            await file.download_to_drive(file_path)                    

                # Обработка документа

                        if file_ext == 'rar':
                            new_file_path = f'{os.path.splitext(file_path)[0]}.gif'
                            shutil.move(file_path, new_file_path)
                            file_path = new_file_path
                            file_name = os.path.basename(file_path)
                            file_ext = 'gif'

                        if file_ext in ('jpg', 'jpeg', 'png', 'gif'):
                            if file_ext == 'gif':
                                try:
                                    image_url = await upload_image(file_path)
                                    media[index] = {  # Обновляем существующее изображение
                                        'type': 'image',
                                        'url': image_url,
                                        'caption': caption if caption else ""
                                    }
                                    user_data[user_id]['media'] = media  # Сохраняем изменения

                                    # Удаляем предыдущее сообщение, если оно есть
                                    if 'last_image_message_id' in user_data[user_id]:
                                        try:
                                            await context.bot.delete_message(chat_id=update.message.chat_id, message_id=user_data[user_id]['last_image_message_id'])
                                        except Exception as e:
                                            print(f"Ошибка при удалении сообщения: {e}")

                                    # Отправляем новое сообщение
                                    sent_message = await context.bot.send_message(
                                        chat_id=update.message.chat_id,
                                        text='✅ Изображение замечательно обновлено.',
                                        reply_to_message_id=message_id
                                    )

                                    # Сохраняем ID нового сообщения
                                    user_data[user_id]['last_image_message_id'] = sent_message.message_id

                                    # Удаляем индекс редактирования после завершения
                                    del context.user_data['editing_index']

                                    return ASKING_FOR_IMAGE
                                except Exception as e:
                                    await context.bot.send_message(
                                        chat_id=update.message.chat_id,
                                        text=f'🚫 Ошибка при загрузке изображения: {str(e)}. Попробуйте снова.',
                                        reply_to_message_id=message_id
                                    )
                                    return ConversationHandler.END
                            else:
                                if os.path.getsize(file_path) > 5 * 1024 * 1024:
                                    compressed_path = f'{os.path.splitext(file_path)[0]}_compressed.jpg'
                                    compress_image(file_path, compressed_path)
                                    file_path = compressed_path

                                try:




                                    image_url = await upload_image(file_path)
                                    media[index] = {  # Обновляем существующее изображение
                                        'type': 'image',
                                        'url': image_url,
                                        'caption': caption if caption else ""
                                    }
                                    user_data[user_id]['media'] = media # Сохраняем изменения
                                    os.remove(file_path)

                                    # Удаляем предыдущее сообщение, если оно есть
                                    if 'last_image_message_id' in user_data[user_id]:
                                        try:
                                            await context.bot.delete_message(chat_id=update.message.chat_id, message_id=user_data[user_id]['last_image_message_id'])
                                        except Exception as e:
                                            print(f"Ошибка при удалении сообщения: {e}")

                                    # Отправляем новое сообщение
                                    keyboard = []
                                    image_counter = 1  # Счётчик для изображений

                                    # Настройки пагинации
                                    items_per_page = 30  # Количество кнопок на странице
                                    total_pages = (len(media) + items_per_page - 1) // items_per_page  # Общее количество страниц
                                    current_page = user_data[user_id].get('current_page', 0)  # Текущая страница

                                    # Ограничиваем текущую страницу
                                    current_page = max(0, min(current_page, total_pages - 1))

                                    # Создаём новый список кнопок для содержания статьи
                                    start_idx = current_page * items_per_page
                                    end_idx = min(start_idx + items_per_page, len(media))
                                    for idx in range(start_idx, end_idx):
                                        item = media[idx]
                                        if item['type'] == 'text':
                                            text = item['content']
                                            
                                            # Извлечение текста, если нужно
                                            if isinstance(text, dict) and 'children' in text:
                                                text = ''.join(child['children'][0] for child in text['children'] if isinstance(child, dict) and 'children' in child)
                                            
                                            preview_text = (text[:12] + '...') if len(text) > 12 else text
                                        else:  # Если элемент — это изображение
                                            preview_text = f"{image_counter} изображение"  # Нумерация только для изображений
                                            image_counter += 1  # Увеличиваем счётчик только для изображений
                                        
                                        # Добавляем кнопки для предпросмотра, редактирования и удаления
                                        keyboard.append([
                                            InlineKeyboardButton(text=str(preview_text), callback_data=f"preview_{idx}"),
                                            InlineKeyboardButton(text="Редактировать", callback_data=f"edit_{idx}"),
                                            InlineKeyboardButton(text="Удалить", callback_data=f"delete_{idx}"),
                                        ])

                                    # Добавляем кнопки навигации, если это не первая страница
                                    if current_page > 0:
                                        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='page_down')])

                                    # Добавляем кнопки навигации, если это не последняя страница
                                    if current_page < total_pages - 1:
                                        keyboard.append([InlineKeyboardButton("Вперёд ➡️", callback_data='page_up')])

                                    keyboard.append([InlineKeyboardButton("🌌 Предпросмотр статьи🌌", callback_data='preview_article')])
                                    keyboard.append([InlineKeyboardButton("Помощь и разметка", callback_data='help_command')])
                                    keyboard.append([InlineKeyboardButton("🌠 К Завершению Публикации 🌠", callback_data='create_article')])


                                    # Отправляем новое сообщение с обновлённым списком кнопок
                                    reply_markup = InlineKeyboardMarkup(keyboard)
                                    sent_message_with_buttons = await context.bot.send_message(
                                        chat_id=update.message.chat_id,
                                        text='✅ Изображение Заменено. \n📝 Текущее содержание статьи:',
                                        reply_markup=reply_markup
                                    )

                                    # Сохраняем ID нового сообщения с кнопками
                                    user_data[user_id]['last_image_message_id'] = sent_message_with_buttons.message_id
                                    user_data[user_id]['current_page'] = current_page

                                    # Удаляем индекс редактирования после завершения
                                    del context.user_data['editing_index']

                                    return ASKING_FOR_IMAGE
                                except Exception as e:
                                    await context.bot.send_message(
                                        chat_id=update.message.chat_id,
                                        text=f'🚫 Ошибка при загрузке изображения: {str(e)}. Попробуйте снова.',
                                        reply_to_message_id=message_id
                                    )
                                    return ConversationHandler.END

                        else:
                            await context.bot.send_message(
                                chat_id=update.message.chat_id,
                                text='Пожалуйста, отправьте изображение в формате JPG, PNG или .RAR для .GIF.',
                                reply_to_message_id=message_id
                            )
                            return ASKING_FOR_IMAGE

                    elif media[index]['type'] == 'text':
                        # Если редактируем текст, вызываем обработчик текста
                        return await handle_new_text(update, context)
                    else:
                        await context.bot.send_message(
                            chat_id=update.message.chat_id,
                            text='🚫 Ошибка: указанный элемент имеет недопустимый тип.',
                            reply_to_message_id=message_id
                        )
                        del context.user_data['editing_index']
                        return ConversationHandler.END
                else:
                    await context.bot.send_message(
                        chat_id=update.message.chat_id,
                        text='🚫 Ошибка: указанный индекс изображения недействителен.',
                        reply_to_message_id=message_id
                    )
                    del context.user_data['editing_index']  # Удаляем индекс, если он недействителен
                    return ConversationHandler.END

    # Если не в состоянии редактирования, продолжаем обычную обработку изображений
    if user_id in user_data and user_data[user_id]['status'] == 'awaiting_image':

        # === НОВЫЙ БЛОК ДЛЯ АУДИО ===
        if update.message.audio:
            audio = update.message.audio
            audio_file_id = audio.file_id
            
            # Инициализируем список музыки, если его нет
            if 'music' not in user_data[user_id]:
                user_data[user_id]['music'] = []
            
            # --- ЛОГИКА ОПРЕДЕЛЕНИЯ ИМЕНИ (music_name) ---
            # 1. Приоритет: Подпись к файлу (caption)
            if update.message.caption:
                music_name = update.message.caption
            # 2. Приоритет: Имя файла (file_name)
            elif audio.file_name:
                music_name = audio.file_name
            # 3. Приоритет: music1, music2... (если нет ни подписи, ни имени файла)
            else:
                # Считаем текущее количество + 1 для номера
                next_index = len(user_data[user_id]['music']) + 1
                music_name = f"music{next_index}"
            
            # Сохраняем в структуру не просто ID, а словарь с ID и именем
            music_data = {
                'file_id': audio_file_id,
                'music_name': music_name
            }
            
            user_data[user_id]['music'].append(music_data)
            # ---------------------------------------------
            
            music_count = len(user_data[user_id]['music'])
            
            # Формируем клавиатуру (такую же, как при отправке фото)
            keyboard = [
                [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')],
                [InlineKeyboardButton("Ссылка на статью", callback_data='preview_article')],
                [InlineKeyboardButton("Редактировать", callback_data='edit_article')],
                [InlineKeyboardButton("📗 Помощь и разметка Telegraph📗", callback_data='help_command')],
                [InlineKeyboardButton("🌠 К Завершению Публикации 🌠", callback_data='create_article')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text=f'🎵 Аудиозапись "{music_name}" добавлена (всего: {music_count} шт.).\nВы можете прислать еще аудио, изображения или завершить создание поста.',
                reply_to_message_id=message_id,
                reply_markup=reply_markup
            )
            return ASKING_FOR_IMAGE
        # ============================

        
        if update.message.photo:
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text='Пожалуйста, отправьте изображение как файл (формат JPG, PNG или .RAR для .GIF), без сжатия. Для подробностей введите /help',
                reply_to_message_id=message_id
            )
            return ASKING_FOR_IMAGE

        elif update.message.document:
            file_name = update.message.document.file_name
            file_ext = file_name.lower().split('.')[-1]
            file = await context.bot.get_file(update.message.document.file_id)

            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as tmp_file:
                file_path = tmp_file.name
                await file.download_to_drive(file_path)

            if file_ext == 'rar':
                new_file_path = f'{os.path.splitext(file_path)[0]}.gif'
                shutil.move(file_path, new_file_path)
                file_path = new_file_path
                file_name = os.path.basename(file_path)
                file_ext = 'gif'

            if file_ext in ('jpg', 'jpeg', 'png', 'gif'):
                if file_ext == 'gif':
                    try:
                        image_url = await upload_image(file_path)
                        if 'media' not in user_data[user_id]:
                            user_data[user_id]['media'] = []
                        user_data[user_id]['media'].append({
                            'type': 'image',
                            'url': image_url,
                            'caption': caption if caption else ""
                        })

                        # Удаляем предыдущее сообщение, если оно есть
                        if 'last_image_message_id' in user_data[user_id]:
                            try:
                                await context.bot.delete_message(chat_id=update.message.chat_id, message_id=user_data[user_id]['last_image_message_id'])
                            except Exception as e:
                                print(f"Ошибка при удалении сообщения: {e}")

                        keyboard = [
                            [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')],
                            [InlineKeyboardButton("Удалить последний элемент", callback_data='delete_last')],
                            [InlineKeyboardButton("Ссылка на статью", callback_data='preview_article')],
                            [InlineKeyboardButton("Редактировать", callback_data='edit_article')],
                            [InlineKeyboardButton("📗 Помощь и разметка Telegraph📗", callback_data='help_command')],
                            [InlineKeyboardButton("🌠 К Завершению Публикации 🌠", callback_data='create_article')]
                        ]

                        reply_markup = InlineKeyboardMarkup(keyboard)                                

                        if 'image_counter' not in user_data[user_id]:
                            user_data[user_id]['image_counter'] = 0

                        # Когда бот получает изображение, увеличиваем счётчик
                        user_data[user_id]['image_counter'] += 1
                        image_counter = user_data[user_id]['image_counter']

                        # Используем счётчик в сообщении
                        image_text = "изображение" if image_counter == 1 else "изображения"
                        sent_message = await context.bot.send_message(
                            chat_id=update.message.chat_id,
                            text=f'✅ {image_counter} {image_text} добавлено. ヽ(o＾▽＾o)ノ\n\n Дождитесь загрузки остальных изображений, если их больше чем одно. Затем вы можете продолжить присылать изображения или перейти к завершению.\n\n Так же на этом этапе можно заполнить текстом и изображениями создающуюся параллельно статью telegraph, если она вам нужна, для этого используются кнопки ниже.\n\n Если статья telegraph вам не нужна то просто проигнорируйте все кнопки ниже и сразу жмите \n" К Завершению публикации " ',
                            reply_to_message_id=message_id,
                            reply_markup=reply_markup
                        )

                        # Сохраняем ID нового сообщения
                        user_data[user_id]['last_image_message_id'] = sent_message.message_id

                        return ASKING_FOR_IMAGE
                    except Exception as e:
                        await context.bot.send_message(
                            chat_id=update.message.chat_id,
                            text=f'🚫Ошибка при загрузке изображения: {str(e)}. Можете попробовать прислать файл ещё раз через некоторое время или нажать /restart',
                            reply_to_message_id=message_id
                        )
                        return ConversationHandler.END
                else:
                    if os.path.getsize(file_path) > 5 * 1024 * 1024:
                        compressed_path = f'{os.path.splitext(file_path)[0]}_compressed.jpg'
                        compress_image(file_path, compressed_path)
                        file_path = compressed_path

                    try:
                        image_url = await upload_image(file_path)
                        if 'media' not in user_data[user_id]:
                            user_data[user_id]['media'] = []
                        user_data[user_id]['media'].append({
                            'type': 'image',
                            'url': image_url,
                            'caption': caption if caption else ""
                        })
                        os.remove(file_path)

                        # Удаляем предыдущее сообщение, если оно есть
                        if 'last_image_message_id' in user_data[user_id]:
                            try:
                                await context.bot.delete_message(chat_id=update.message.chat_id, message_id=user_data[user_id]['last_image_message_id'])
                            except Exception as e:
                                print(f"Ошибка при удалении сообщения: {e}")

                        keyboard = [
                            [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')],
                            [InlineKeyboardButton("Удалить последний элемент", callback_data='delete_last')],
                            [InlineKeyboardButton("Ссылка на статью", callback_data='preview_article')],
                            [InlineKeyboardButton("Редактировать", callback_data='edit_article')],
                            [InlineKeyboardButton("📗 Помощь и разметка Telegraph📗", callback_data='help_command')],
                            [InlineKeyboardButton("🌠 К Завершению Публикации 🌠", callback_data='create_article')]
                        ]

                        reply_markup = InlineKeyboardMarkup(keyboard) 


                        if 'image_counter' not in user_data[user_id]:
                            user_data[user_id]['image_counter'] = 0

                        # Когда бот получает изображение, увеличиваем счётчик
                        user_data[user_id]['image_counter'] += 1
                        image_counter = user_data[user_id]['image_counter']

                        # Используем счётчик в сообщении
                        image_text = "изображение" if image_counter == 1 else "изображения"
                        sent_message = await context.bot.send_message(
                            chat_id=update.message.chat_id,
                            text=f'✅ {image_counter} {image_text} добавлено.\n\n ヽ(o＾▽＾o)ノ Дождитесь загрузки остальных изображений, если их больше чем одно. Затем вы можете продолжить присылать изображения или перейти к завершению.\n\n Так же на этом этапе можно заполнить текстом и изображениями создающуюся параллеольно статью telegraph, если она вам нужна, для этого используются кнопки ниже.\n\n Если статья telegraph вам не нужна то просто проигнорируйте все кнопки ниже и сразу жмите \n" К Завершению публикации " ',
                            reply_to_message_id=message_id,
                            reply_markup=reply_markup
                        )

                        # Сохраняем ID нового сообщения
                        user_data[user_id]['last_image_message_id'] = sent_message.message_id

                        return ASKING_FOR_IMAGE
                    except Exception as e:
                        await context.bot.send_message(
                            chat_id=update.message.chat_id,
                            text=f'🚫Ошибка при загрузке изображения: {str(e)}. Можете попробовать прислать файл ещё раз через некоторое время или нажать /restart',
                            reply_to_message_id=message_id
                        )
                        return ConversationHandler.END

            else:
                await context.bot.send_message(
                    chat_id=update.message.chat_id,
                    text='Пожалуйста, отправьте изображение в формате JPG, PNG или .RAR для .GIF.',
                    reply_to_message_id=message_id
                )
                return ASKING_FOR_IMAGE

        elif update.message.text:
            return await handle_text(update, context)

        else:
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text='Пожалуйста, отправьте изображение как файл (формат JPG, PNG или .RAR для .GIF), без сжатия, или текст.',
                reply_to_message_id=message_id
            )
            return ASKING_FOR_IMAGE

    else:
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text='🚫Ошибка: данные не найдены. Попробуйте отправить снова. Или нажмите /restart',
            reply_to_message_id=message_id
        )
        return ConversationHandler.END


        
# Функция для обработки текстовых сообщений
async def handle_text(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    message_text = update.message.text
    # Если пользователь отвечает "нет" в любом регистре и с точкой или без
    if message_text.lower() in ["нет", "нет."]:
        # Отправляем сообщение с кнопкой завершения публикации
        keyboard = [
            [InlineKeyboardButton("🌠 К Завершению Публикации 🌠", callback_data='create_article')],
            [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Отлично! В таком случае нажмите кнопку ниже:",
            reply_markup=reply_markup
        )
        return ASKING_FOR_IMAGE  # Указываем нужный этап разговора (если требуется)
    # Если не в режиме редактирования, продолжаем обычную обработку текстовых сообщений
    user_data_entry = user_data.get(user_id, {})

    # Проверяем статус пользователя
    if user_data_entry.get('status') == 'awaiting_image':
        # Обработка текстовых сообщений с разметкой
        formatted_text = apply_markup(message_text)

        # Проверка наличия раздела 'media' и добавление текста
        if 'media' not in user_data_entry:
            user_data_entry['media'] = []

        user_data_entry['media'].append({'type': 'text', 'content': formatted_text})

        # Сохраняем обновлённые данные
        user_data[user_id] = user_data_entry

        # Удаление предыдущего сообщения, если оно существует
        if 'last_message_id' in user_data_entry:
            try:
                await context.bot.delete_message(
                    chat_id=update.message.chat_id, 
                    message_id=user_data_entry['last_message_id']
                )
            except Exception as e:
                print(f"Ошибка при удалении сообщения: {e}")

        # Отправляем новое сообщение


        keyboard = [
            [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')],
            [InlineKeyboardButton("Удалить последний элемент", callback_data='delete_last')],
            [InlineKeyboardButton("Ссылка на статью", callback_data='preview_article')],
            [InlineKeyboardButton("Редактировать", callback_data='edit_article')],
            [InlineKeyboardButton("📗 Помощь и разметка Telegraph 📗", callback_data='help_command')],
            [InlineKeyboardButton("🌠 К Завершению Публикации 🌠", callback_data='create_article')],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard) 

        if 'text_counter' not in user_data[user_id]:
            user_data[user_id]['text_counter'] = 0

        # Когда бот получает текст, увеличиваем счётчик
        user_data[user_id]['text_counter'] += 1
        text_counter = user_data[user_id]['text_counter']

        # Используем счётчик текста в сообщении
        text_message = "текст" if text_counter == 1 else "текст"
        sent_message = await update.message.reply_text(
            f'✅ {text_message} успешно добавлен.\nヽ(o＾▽＾o)ノ\n\n Вы можете продолжить присылать контент или нажать " К Завершению Публикации " для перехода к завершающему этапу.\n\n',
            reply_to_message_id=update.message.message_id,
            reply_markup=reply_markup  # Добавляем клавиатуру с кнопкой
        )
        # Сохраняем ID нового сообщения
        user_data_entry['last_message_id'] = sent_message.message_id
        user_data[user_id] = user_data_entry

        return ASKING_FOR_IMAGE
    else:
        await update.message.reply_text('🚫 Ошибка: данные не найдены. Попробуйте отправить снова. Или нажмите /restart')
        return ConversationHandler.END

def extract_text_from_json(data):
    if isinstance(data, dict):
        # Если текущий элемент - это словарь, рекурсивно обрабатываем его ключ 'children'
        return ''.join(extract_text_from_json(child) for child in data.get('children', []))
    elif isinstance(data, list):
        # Если текущий элемент - это список, обрабатываем каждый элемент списка
        return ''.join(extract_text_from_json(item) for item in data)
    elif isinstance(data, str):
        # Если текущий элемент - это строка, возвращаем её
        return data
    return ''



async def handle_new_text_from_image(update: Update, context: CallbackContext, index, media) -> int:
    user_id = update.message.from_user.id
    message_text = update.message.text

    # Проверка наличия данных пользователя и медиа
    if user_id not in user_data or 'media' not in user_data[user_id]:
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text='🚫 Ошибка: данные пользователя не найдены. Попробуйте снова.',
            reply_to_message_id=update.message.message_id
        )
        return ConversationHandler.END

    # Проверка корректности индекса
    if not (0 <= index < len(media)):
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text='🚫 Ошибка: недопустимый индекс редактируемого элемента.',
            reply_to_message_id=update.message.message_id
        )
        return ConversationHandler.END

    # Применение разметки к тексту
    formatted_text = apply_markup(message_text)

    # Замена изображения на текст в media
    media[index] = {
        'type': 'text',
        'content': formatted_text
    }
    user_data[user_id]['media'] = media  # Обновляем данные пользователя

    # Уведомление пользователя
    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text='✅ Содержание изменено.',
        reply_to_message_id=update.message.message_id
    )

    # Удаляем индекс редактирования только после успешной замены
    del context.user_data['editing_index']

    # Удаляем предыдущее сообщение с кнопками содержания статьи, если оно существует
    if 'last_content_message_id' in user_data[user_id]:
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id, 
                message_id=user_data[user_id]['last_content_message_id']
            )
        except Exception as e:
            print(f"Ошибка при удалении сообщения с содержанием: {e}")

        # Настройки пагинации
    items_per_page = 30  # Количество кнопок на странице
    total_pages = (len(media) + items_per_page - 1) // items_per_page  # Общее количество страниц
    current_page = user_data[user_id].get('current_page', 0)  # Текущая страница

    # Ограничиваем текущую страницу
    current_page = max(0, min(current_page, total_pages - 1))        

    # Создаём новый список кнопок для содержания статьи
    keyboard = []
    image_counter = 1  # Счётчик для изображений
    start_idx = current_page * items_per_page
    end_idx = min(start_idx + items_per_page, len(media))
    for idx in range(start_idx, end_idx):
        item = media[idx]
        if item['type'] == 'text':
            text = item['content']
            
            # Извлечение текста, если нужно
            if isinstance(text, dict) and 'children' in text:
                text = ''.join(child['children'][0] for child in text['children'] if isinstance(child, dict) and 'children' in child)
            
            preview_text = (text[:12] + '...') if len(text) > 12 else text
        else:  # Если элемент — это изображение
            preview_text = f"{image_counter} изображение"  # Нумерация только для изображений
            image_counter += 1  # Увеличиваем счётчик только для изображений
        
        # Добавляем кнопки для предпросмотра, редактирования и удаления
        keyboard.append([
            InlineKeyboardButton(text=str(preview_text), callback_data=f"preview_{idx}"),
            InlineKeyboardButton(text="Редактировать", callback_data=f"edit_{idx}"),
            InlineKeyboardButton(text="Удалить", callback_data=f"delete_{idx}"),
        ])
    # Добавляем кнопки навигации, если это не первая страница
    if current_page > 0:
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='page_down')])
    
    # Добавляем кнопки навигации, если это не последняя страница
    if current_page < total_pages - 1:
        keyboard.append([InlineKeyboardButton("Вперёд ➡️", callback_data='page_up')])
    
    keyboard.append([InlineKeyboardButton("Предпросмотр статьи", callback_data='preview_article')])
    keyboard.append([InlineKeyboardButton("Помощь и разметка", callback_data='help_command')])
    keyboard.append([InlineKeyboardButton("🌠 К Завершению Публикации 🌠", callback_data='create_article')])
    # Отправляем новое сообщение с обновлённым списком кнопок
    reply_markup = InlineKeyboardMarkup(keyboard)
    sent_message = await context.bot.send_message(
        chat_id=update.message.chat_id,
        text='📝 Текущее содержание статьи3:',
        reply_markup=reply_markup
    )

    # Сохраняем ID нового сообщения с кнопками
    user_data[user_id]['last_content_message_id'] = sent_message.message_id
    user_data[user_id]['current_page'] = current_page 

    del context.user_data['editing_index']

    return ASKING_FOR_IMAGE
        

async def send_media_group(update, media_group, caption):
    if not media_group:
        return
    try:
        await update.message.reply_text(caption, parse_mode='HTML')
        await update.message.reply_media_group(media=media_group)
    except Exception as e:
        raise

async def send_media_group_with_retries(update, media_group, max_retries=3, delay=2):
    retries = 0

    # Определяем, является ли событие сообщением или callback-запросом
    if update.message:
        message_to_reply = update.message
    elif update.callback_query:
        message_to_reply = update.callback_query.message
    else:
        return None  # Не удалось определить источник, возвращаем None

    message_id = None  # ID первого сообщения в группе

    while retries < max_retries:
        try:
            # Обрабатываем изображения в медиагруппе
            processed_media_group = []
            for media in media_group:
                if media.type == "photo":
                    processed_image, _ = await process_image(media.media)  # Игнорируем второй элемент (is_gif)
                    if not processed_image:
                        raise Exception("Failed to process image for media group")
                    
                    # Добавляем обработанное изображение в новый объект InputMedia
                    processed_media_group.append(
                        InputMediaPhoto(
                            media=processed_image,
                            caption=media.caption if hasattr(media, "caption") else None,
                            parse_mode=media.parse_mode if hasattr(media, "parse_mode") else None
                        )
                    )
                elif media.type == "animation":
                    processed_image, _ = await process_image(media.media)  # Игнорируем второй элемент (is_gif)
                    if not processed_image:
                        raise Exception("Failed to process animation for media group")
                    
                    # Добавляем обработанную анимацию в новый объект InputMedia
                    processed_media_group.append(
                        InputMediaAnimation(
                            media=processed_image,
                            caption=media.caption if hasattr(media, "caption") else None,
                            parse_mode=media.parse_mode if hasattr(media, "parse_mode") else None
                        )
                    )
                else:
                    # Оставляем остальные типы медиа без изменений
                    processed_media_group.append(media)

            # Отправляем медиагруппу и сохраняем результат
            sent_messages = await message_to_reply.reply_media_group(processed_media_group)

            # Сохраняем message_id первого изображения
            if sent_messages:
                message_id = sent_messages[0].message_id  # ID первого отправленного сообщения

            return message_id  # Успешная отправка, возвращаем ID первого сообщения
        except Exception as e:
            retries += 1
            if retries < max_retries:
                await asyncio.sleep(delay)

    return None  # Если все попытки не удались, возвращаем None




async def convert_image_repost(photo_url: str):
    """
    Загружает изображение по URL, конвертирует в формат JPG,
    уменьшает разрешение, если необходимо, и сжимает для публикации.
    Если файл - это GIF, возвращает его без изменений.
    """
    try:
        # Загрузка файла по URL
        async with aiohttp.ClientSession() as session:
            async with session.get(photo_url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch file from URL: {photo_url}")
                
                # Определяем MIME-тип файла из заголовков ответа
                content_type = response.headers.get('Content-Type', '')
                logging.info(f"content_type: {content_type}")                
                # Если файл - GIF, возвращаем его без изменений
                if content_type == 'image/gif':
                    gif_data = await response.read()
                    return io.BytesIO(gif_data)  # Возвращаем как файл в памяти

                if content_type.startswith("video/"):
                    gif_data = await response.read()
                    return io.BytesIO(gif_data)  # Возвращаем как файл в памяти


                # Если это не GIF, продолжаем обработку
                img_data = await response.read()

        # Открытие изображения
        img = Image.open(io.BytesIO(img_data))

        # Конвертация изображения в формат JPEG (если не JPEG)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Уменьшаем разрешение, если максимальная сторона > 2450px
        max_dimension = 2500
        if max(img.width, img.height) > max_dimension:
            scale = max_dimension / max(img.width, img.height)
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Сохраняем изображение в буфер
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=100)
        output.seek(0)

        # Проверяем размер файла (если > 2MB, сжимаем)
        max_file_size = 2 * 1024 * 1024  # 2MB
        if len(output.getvalue()) > max_file_size:
            # Понижаем качество изображения
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=85)
            output.seek(0)

            # Если размер все еще больше 2MB, уменьшаем разрешение
            if len(output.getvalue()) > max_file_size:
                scale = (max_file_size / len(output.getvalue())) ** 0.5
                new_size = (int(img.width * scale), int(img.height * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                output = io.BytesIO()
                img.save(output, format="JPEG", quality=85)
                output.seek(0)

        return output  # Возвращаем обработанный файл в памяти
    except Exception as e:
        return None


# --- Настройка логирования (замените на ваш реальный логгер) ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
# --- ---

async def process_image(photo_url):
    """
    Асинхронно загружает и обрабатывает изображение с URL.

    - Проверяет, является ли изображение GIF (по Content-Type или формату).
      Если да, возвращает исходные данные GIF.
    - Если не GIF:
        - Конвертирует в RGB (если необходимо).
        - Уменьшает размер, если одна из сторон больше max_dimension.
        - Сохраняет как JPEG.
        - Если размер JPEG превышает max_file_size, снижает качество.
        - Если размер все еще превышает лимит, дополнительно уменьшает
          изображение и сохраняет с пониженным качеством.
    - Возвращает BytesIO с данными изображения и флаг is_gif (True/False).
    - В случае ошибки возвращает (None, False).
    """
    logger.info(f"Processing photo_url: {photo_url}")
    img_data = None # Инициализируем на случай ошибки до чтения данных

    try:
        # 1. Загрузка изображения
        async with aiohttp.ClientSession() as session:
            async with session.get(photo_url) as response:
                logger.info(f"HTTP status code for {photo_url}: {response.status}")
                if response.status != 200:
                    # Используем f-string для более информативного сообщения
                    raise Exception(f"Failed to fetch image from URL {photo_url}. Status: {response.status}")
                content_type = response.headers.get("Content-Type", "").lower()
                img_data = await response.read()
                logger.info(f"Downloaded {len(img_data)} bytes. Content-Type: {content_type}")
        if content_type.startswith("video/"):
            logger.info("Content-Type is video/* — treating as animated GIF / video")
            output = io.BytesIO(img_data)
            return output, True
        # 2. Проверка на GIF по Content-Type (первый и самый быстрый способ)
        if "gif" in content_type:
            logger.info("Image is a GIF (based on Content-Type), returning original data")
            output = io.BytesIO(img_data)
            # output.seek(0) # seek(0) не обязателен для нового BytesIO
            return output, True  # Важно: Возвращаемся СРАЗУ ЖЕ

        # 3. Попытка открыть изображение с помощью Pillow
        # Это нужно, если Content-Type неверный или отсутствует,
        # а также для получения формата и свойств изображения.
        try:
            # Используем контекстный менеджер для BytesIO
            with io.BytesIO(img_data) as img_stream:
                 img = Image.open(img_stream)
                 # Обязательно загружаем данные, чтобы BytesIO не закрылся раньше времени
                 img.load()
        except Exception as open_exc:
            # Если Pillow не может открыть файл, значит формат не поддерживается или файл поврежден
            # Логируем ОРИГИНАЛЬНУЮ ошибку Pillow для диагностики
            logger.error(f"Pillow failed to open image data from {photo_url}: {open_exc}")
            # Создаем новое, более понятное исключение, но сохраняем исходное
            raise Exception(f"Pillow cannot identify image file from {photo_url}") from open_exc

        # 4. Проверка на GIF по формату, определенному Pillow
        # (на случай, если Content-Type был неверным)
        if img.format == "GIF":
            logger.info("Image is a GIF (based on Pillow format detection), returning original data")
            output = io.BytesIO(img_data)
            # output.seek(0) # Не обязательно
            return output, True # Важно: Возвращаемся СРАЗУ ЖЕ

        # --- Если код дошел сюда, изображение ТОЧНО не GIF ---

        # 5. Обработка не-GIF изображений
        logger.info(f"Processing non-GIF image (Format: {img.format}, Mode: {img.mode}). Original size: {img.width}x{img.height}")

        # Конвертация в RGB (для совместимости с JPEG)
        if img.mode in ("RGBA", "P"): # 'P' - палитра (часто в PNG, GIF)
            logger.info(f"Converting image mode from {img.mode} to RGB")
            img = img.convert("RGB")

        # Изменение размера, если изображение слишком большое
        max_dimension = 2500
        if max(img.width, img.height) > max_dimension:
            scale = max_dimension / max(img.width, img.height)
            new_size = (int(img.width * scale), int(img.height * scale))
            logger.info(f"Resizing image from {img.size} to {new_size}")
            # Используем LANCZOS (или ANTIALIAS в старых версиях Pillow) для лучшего качества
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # 6. Сохранение в JPEG с контролем размера файла
        output = io.BytesIO()
        jpeg_quality = 100 # Начинаем с максимального качества
        img.save(output, format="JPEG", quality=jpeg_quality)
        logger.info(f"Saved as JPEG (Q={jpeg_quality}). Size: {len(output.getvalue()) / 1024:.2f} KB")

        max_file_size = 2 * 1024 * 1024 # 2 MB

        # Попытка №2: Снижение качества, если размер превышен
        if output.tell() > max_file_size: # Используем output.tell() т.к. seek(0) не делали
            jpeg_quality = 85
            logger.info(f"JPEG size exceeds limit ({max_file_size / 1024 / 1024 :.1f} MB). Trying lower quality (Q={jpeg_quality}).")
            output = io.BytesIO() # Создаем новый объект BytesIO
            img.save(output, format="JPEG", quality=jpeg_quality)
            logger.info(f"Saved as JPEG (Q={jpeg_quality}). Size: {len(output.getvalue()) / 1024:.2f} KB")

            # Попытка №3: Дополнительное уменьшение размера, если все еще слишком большой
            if output.tell() > max_file_size:
                logger.info(f"JPEG size still exceeds limit. Resizing further.")
                # Рассчитываем масштаб на основе текущего размера файла (с Q=85)
                # Это приблизительный расчет, так как сжатие JPEG нелинейно
                current_size_bytes = output.tell()
                scale = (max_file_size / current_size_bytes) ** 0.5 # Корень для 2D масштабирования

                # Уменьшаем текущие размеры изображения (которые могли быть уже уменьшены ранее)
                new_width = max(1, int(img.width * scale)) # Не допускаем нулевого размера
                new_height = max(1, int(img.height * scale))
                new_size = (new_width, new_height)

                logger.info(f"Further resizing image from {img.size} to {new_size}")
                img_resized_further = img.resize(new_size, Image.Resampling.LANCZOS)

                output = io.BytesIO() # Снова новый объект
                img_resized_further.save(output, format="JPEG", quality=jpeg_quality) # Используем то же качество 85
                logger.info(f"Resized and saved as JPEG (Q={jpeg_quality}). Final size: {len(output.getvalue()) / 1024:.2f} KB")

                # Финальная проверка (опционально: можно выдать ошибку, если все равно не влезло)
                if output.tell() > max_file_size:
                     logger.error(f"Image size STILL exceeds limit ({output.tell()} bytes) after resizing and quality reduction. URL: {photo_url}")
                     # Можно либо вернуть этот файл (как сейчас), либо вернуть None/вызвать Exception
                     # raise Exception("Failed to reduce image size below the limit after all attempts.")

        # Устанавливаем позицию в начало перед возвратом
        output.seek(0)
        return output, False # Возвращаем обработанный JPEG

    # Блок except должен быть снаружи основного блока try/except для загрузки,
    # чтобы ловить и ошибки загрузки, и ошибки обработки Pillow.
    except aiohttp.ClientError as e:
         # Ошибка сети или HTTP
         logger.error(f"Network or HTTP error fetching image {photo_url}: {e}")
         return None, False
    except Exception as e:
        # Ловим все остальные ошибки (включая ошибки Pillow, ошибки конвертации и т.д.)
        # Используем exc_info=True для полного трейсбека в логах
        logger.error(f"Error processing image {photo_url}: {e}", exc_info=True)
        return None, False # Сигнализируем об ошибке




async def send_photo_with_retries(update, photo_url, caption, parse_mode, reply_markup=None, max_retries=3, delay=2):
    retries = 0
    if update.message:
        message_to_reply = update.message
    elif update.callback_query:
        message_to_reply = update.callback_query.message
    else:
        return None

    while retries < max_retries:
        try:
            # Обработка изображения
            processed_image, is_gif = await process_image(photo_url)
            if not processed_image:
                raise Exception("Failed to process media")
            
            # Если это GIF, сообщаем пользователю о процессе обработки
            if is_gif:
                await message_to_reply.reply_text("Gif обрабатывается, ожидайте...\n\nВ боте GIF будет отображаться в сжатом виде. Не переживайте, так и должно быть для ускорения работы бота. Однако если вы воспользуетесь кнопкой публикации то на ваш канал отправится именно полный вариант")

            # Выбор метода отправки
            if is_gif:
                message = await message_to_reply.reply_animation(
                    animation=processed_image,
                    filename="animation.gif",
                    caption=caption,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup
                )
            else:
                message = await message_to_reply.reply_photo(
                    photo=processed_image,
                    caption=caption,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup
                )
            return message
        except Exception as e:
            logger.error(f"Failed to send media: {e}")
            retries += 1
            if retries < max_retries:
                logger.info(f"Retrying in {delay} seconds... (Attempt {retries}/{max_retries})")
                await asyncio.sleep(delay)
    return None



async def delete_last(update: Update, context: CallbackContext) -> None:
    # Определяем, откуда пришёл запрос - через команду или через кнопку
    if update.message:  # Если это сообщение
        user_id = update.message.from_user.id
        chat_id = update.message.chat_id
        message_id = update.message.message_id
    elif update.callback_query:  # Если это callback через кнопку
        user_id = update.callback_query.from_user.id
        chat_id = update.callback_query.message.chat_id
        message_id = update.callback_query.message.message_id
    else:
        return  # Если это что-то другое, то ничего не делаем

    if user_id in user_data and 'media' in user_data[user_id]:
        if user_data[user_id]['media']:
            last_item = user_data[user_id]['media'].pop()  # Удаляем последний элемент
            item_type = last_item['type']
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Удалён последний элемент типа: {item_type}\n\nДля предпросмотра введите команду /preview",
                reply_to_message_id=message_id
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text="Ваша статья пуста. Нет элементов для удаления.",
                reply_to_message_id=message_id
            )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="У вас нет активной статьи для редактирования. Используйте /start для начала.",
            reply_to_message_id=message_id
        )





async def preview_article(update: Update, context: CallbackContext) -> None:
    # Проверяем, вызвано ли через сообщение или инлайн-кнопку
    if update.message:
        user_id = update.message.from_user.id
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
    else:
        return

    if user_id in user_data:
        try:
            author_name = "by AnemoneBot"
            author_link = "https://t.me/anemone2_bot"
            artist_link = user_data[user_id].get('artist_link', '')
            media = user_data[user_id].get('media', [])
            title = user_data[user_id].get('title', 'Предпросмотр статьи')
            if not title:
                title = author_name
            if title.lower() in ["нет", "нет."]:
                title = "*"  # Заменяем на "*"  
            # Создаём контент для страницы
            content = [{'tag': 'p', 'children': [{'tag': 'a', 'attrs': {'href': artist_link}, 'children': [artist_link]}]}]

            # Добавление изображений с разделителями
            for index, item in enumerate(media):
                if item['type'] == 'text':
                    content.append({'tag': 'p', 'children': [item['content']]})
                elif item['type'] == 'image':
                    # Создаем фигуру с изображением и подписью
                    figure_content = [{'tag': 'img', 'attrs': {'src': item['url']}}]
                    if item.get('caption'):
                        figure_content.append({'tag': 'figcaption', 'children': [item['caption']]})

                    content.append({'tag': 'figure', 'children': figure_content})

                    # Добавление разделителя после изображения, если это не последнее изображение
                    if index < len(media) - 1:
                        content.append({'tag': 'hr'})

            # Создание статьи в Telegra.ph
            response = requests.post('https://api.telegra.ph/createPage', json={
                'access_token': TELEGRAPH_TOKEN,
                'title': title,
                'author_name': author_name,
                'author_url': author_link,
                'content': content
            })
            response.raise_for_status()
            response_json = response.json()

            if response_json.get('ok'):
                preview_url = f"https://telegra.ph/{response_json['result']['path']}"

                # Создание кнопки
                keyboard = [[InlineKeyboardButton("🌠 К Завершению Публикации 🌠", callback_data='create_article')]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                # Отправляем предпросмотр пользователю
                if update.message:
                    await update.message.reply_text(f'Предпросмотр статьи: {preview_url}', reply_markup=reply_markup)
                elif update.callback_query:
                    await update.callback_query.message.reply_text(f'Предпросмотр статьи: {preview_url}', reply_markup=reply_markup)
            else:
                if update.message:
                    await update.message.reply_text('Ошибка при создании предпросмотра статьи.')
                elif update.callback_query:
                    await update.callback_query.message.reply_text('Ошибка при создании предпросмотра статьи.')

        except requests.RequestException as e:
            if update.message:
                await update.message.reply_text(f'Ошибка при создании предпросмотра: {e}')
            elif update.callback_query:
                await update.callback_query.message.reply_text(f'Ошибка при создании предпросмотра: {e}')
    else:
        if update.message:
            await update.message.reply_text('Нет данных для предпросмотра. Начните с отправки текста или изображений.')
        elif update.callback_query:
            await update.callback_query.message.reply_text('Нет данных для предпросмотра. Начните с отправки текста или изображений.')





async def handle_preview_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие

    if query.data == 'preview_article':
        await preview_article(update, context)

async def handle_delete_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие

    if query.data == 'delete_last':
        await delete_last(update, context)


async def handle_help_text_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие

    if query.data == 'help_command':
        await help_command(update, context)


async def handle_create_article_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()  # Ответ на нажатие

    # Вызываем функцию publish, которая создаёт статью
    await publish(update, context)


async def handle_restart_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие

    if query.data == 'restart':
        await restart(update, context)

async def handle_edit_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие

    if query.data == 'edit_article':
        await edit_article(update, context)   

# Добавьте обработчик для переключения страниц
async def handle_page_change(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    
    if query.data == 'page_down':
        user_data[user_id]['current_page'] -= 1
    elif query.data == 'page_up':
        user_data[user_id]['current_page'] += 1

    await edit_article(update, context)  # Повторно вызываем функцию редактирования


# Функция для рекурсивного поиска изображений
def count_images_in_content(content):
    image_count = 0
    for item in content:
        if isinstance(item, dict):
            if item.get('tag') == 'img':
                image_count += 1
            elif item.get('tag') == 'figure' and 'children' in item:
                # Если есть тег figure, проверяем его содержимое
                image_count += count_images_in_content(item['children'])
    return image_count


from urllib.parse import urlparse


def format_link(link: str) -> str:
    # Парсим URL
    parsed_url = urlparse(link)
    domain = parsed_url.netloc  # Получаем домен, например, ema3art.tumblr.com
    # Убираем "www." если оно есть
    domain = domain.replace('www.', '')

    # Словарь для специальных названий
    custom_names = {
        'x.com': 'x.com',
        'pixiv.net': 'pixiv',
        'weibo.com': 'weibo',
        'artstation.com': 'artstation',
        'zcool.com.cn': 'zcool',
        't.me': 't.me',  # Добавлено для Telegram
    }

    # Проверяем, является ли это Tumblr-ссылкой
    if 'tumblr.com' in domain:
        link_name = 'tumblr'
    elif 'lofter.com' in domain:
        # Для lofter используем фиксированное имя
        link_name = 'lofter'
    elif domain in custom_names:
        # Используем специальное название, если оно задано
        link_name = custom_names[domain]
    else:
        # Убираем домен верхнего уровня (.com, .net, и т.д.)
        link_name = domain.split('.')[0]

    # Формируем гиперссылку
    return f"<a href=\"{link}\">{link_name}</a>"





# Основная функция публикации
async def publish(update: Update, context: CallbackContext) -> None:
    # Проверяем, пришло ли событие от сообщения или от callback_query
    if update.message:
        user_id = update.message.from_user.id
        message_to_reply = update.message
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
        message_to_reply = update.callback_query.message
    else:
        return  # Если ни того, ни другого нет, просто выйдем

    if user_id in user_data:
        try:
            author_name = "by AnemoneBot"
            author_link = "https://t.me/anemone2_bot"
            artist_link = user_data[user_id]['artist_link']
            media = user_data[user_id].get('media', [])
            title = user_data[user_id].get('title', 'test')
            # Проверяем значение title
            logger.info(f"title: {title}")    
            logger.info(f"media: {media}")             
            if not title:
                title = author_name
            if title.lower() in ["нет", "нет."]:
                title = "*"  # Заменяем на "*"                              

            extra_links = user_data[user_id].get('extra_links', [])
            if extra_links:
                links_string = " • " + " • ".join(format_link(link) for link in extra_links)
            else:
                links_string = "" 
            # Извлекаем фразу перед "Автор", если она есть
            extra_phrase = user_data[user_id].get('extra_phrase', "")
            author_name_final = user_data[user_id].get('author_name', '')           
            # Проверяем значение author_name_final в зависимости от user_id
            logger.info(f"author_name_final: {author_name_final}") 
            # Формируем строку с фразой перед "Автор", если она есть
            if extra_phrase:
                author_line = f"{extra_phrase}\n\n{author_name_final}"
            else:
                author_line = f"{author_name_final}"
            # Проверяем, есть ли авторское имя
            if not author_name_final:
                author_line = title  # Если это заголовок из "^...^", то используем только заголовок
            else:
                # Формируем строку с фразой перед "Автор", если она есть
                if extra_phrase:
                    author_line = f"{extra_phrase}\n\n{author_name_final}"
                else:
                    author_line = f"{author_name_final}"
            logger.info(f"author_line: {author_line}")
            # === ПОДГОТОВКА ДАННЫХ О МУЗЫКЕ ===
            music_list = user_data[user_id].get('music', [])
            music_post_flag = True if music_list else False
            music_media_data = music_list if music_list else None
            
            moscow_tz = pytz.timezone('Europe/Moscow')
            now = datetime.now(moscow_tz)
            
            # Проверяем наличие даты и времени в ((дата, время))
            # Проверяем наличие даты и времени в формате ((дд.мм, чч:мм))
            time_pattern = r"\(\((\d{1,2}(?:\.\d{1,2})?),\s*(\d{1,2}:\d{2})\)\)"
            time_match = re.search(time_pattern, author_line)
            logger.info(f"time_match: {time_match}")       
            if time_match:
                date_part = time_match.group(1)   # "30.06" или "18"
                time_part = time_match.group(2)   # "0:35"
            
                hour, minute = map(int, time_part.split(":"))
            
                if "." in date_part:
                    day_str, month_str = date_part.split(".")
                    day = int(day_str)
                    month = int(month_str)
                    year = now.year
            
                    try:
                        naive_pub_dt = datetime(year, month, day, hour, minute)
                        pub_dt = moscow_tz.localize(naive_pub_dt)
            
                        if pub_dt < now:
                            pub_dt = moscow_tz.localize(datetime(year + 1, month, day, hour, minute))
                    except Exception as e:
                        logger.error(f"Ошибка в дате: {e}")
                        pub_dt = None
                else:
                    # только день указан
                    day = int(date_part)
                    month = now.month
                    year = now.year
            
                    try:
                        naive_pub_dt = datetime(year, month, day, hour, minute)
                        pub_dt = moscow_tz.localize(naive_pub_dt)
            
                        if pub_dt < now:
                            # пробуем следующий месяц
                            if month == 12:
                                year += 1
                                month = 1
                            else:
                                month += 1
                            pub_dt = moscow_tz.localize(datetime(year, month, day, hour, minute))
                    except Exception as e:
                        logger.error(f"Ошибка в дате (без месяца): {e}")
                        pub_dt = None
            
                if pub_dt:
                    time = pub_dt.strftime("%d.%m, %H:%M")
                    author_line = re.sub(time_pattern, "", author_line).strip()
                    logger.info(f"Найдена отложенная дата публикации: {time}")
                else:
                    time = None
                    logger.warning("Не удалось сформировать дату публикации")
            else:
                time = None
            # Создание статьи в Telegra.ph
            content = [
                {
                    'tag': 'p',
                    'children': [
                        {
                            'tag': 'a',
                            'attrs': {'href': artist_link},
                            'children': [artist_link]
                        }
                    ]
                }
            ]

            # Добавление изображений с разделителями
            for index, item in enumerate(media):
                if item['type'] == 'text':
                    content.append({'tag': 'p', 'children': [item['content']]})
                elif item['type'] == 'image':
                    # Создаем фигуру с изображением и подписью
                    figure_content = [
                        {'tag': 'img', 'attrs': {'src': item['url']}},
                    ]
                    if item.get('caption'):
                        figure_content.append({'tag': 'figcaption', 'children': [item['caption']]})

                    content.append({'tag': 'figure', 'children': figure_content})

                    if index < len(media) - 1:
                        content.append({'tag': 'hr'})

            content.append({'tag': 'hr'})
            content.append({
                'tag': 'i',
                'children': [f'Оригиналы доступны в браузере через меню (⋮)']
            })
            if len(title) > 15:
                title = title[:12] + '...'
            else:
                title = title
            response = requests.post('https://api.telegra.ph/createPage', json={
                'access_token': TELEGRAPH_TOKEN,
                'title': title,
                'author_name': author_name,
                'author_url': author_link,
                'content': content
            })

            response.raise_for_status()
            response_json = response.json()

            if response_json.get('ok'):
                article_url = f"https://telegra.ph/{response_json['result']['path']}"
                webappurl = f"https://anemonne.onrender.com/anemonearts?channel_id=@anemonn&gallery=true&proxy=true"

                
                article_response = requests.get(f'https://api.telegra.ph/getPage?access_token={TELEGRAPH_TOKEN}&path={response_json["result"]["path"]}&return_content=true')
                article_response.raise_for_status()
                article_data = article_response.json()

                image_count = count_images_in_content(content)

                if author_line.lower().strip() in ["*", "нет", "нет."]:
                    author_line = ""
                if image_count > 1:
                    # Фильтруем только изображения, чтобы избежать смешивания с текстом
                    image_media = [item for item in media if item['type'] == 'image']
                    
                    # Разделение только изображений на группы по 10
                    media_groups = [image_media[i:i + 10] for i in range(0, len(image_media), 10)]
                    media_group_data = []
                    
                    # Для хранения информации о том, был ли добавлен текст
                    text_added = False
                    first_message_id = None
                    for group in media_groups:
                        media_group = []

                        for idx, item in enumerate(group):
                            caption = None
                            
                            # Если текст ещё не добавлен, добавляем подпись к первому изображению
                            if not text_added:
                                caption = f'{author_line}\n<a href="{article_url}">Оригинал</a> • <a href="{webappurl}">Галерея</a>{links_string}'
                                text_added = True

                            # Добавляем только изображения в медиа-группу
                            media_group.append(InputMediaPhoto(media=item['url'], caption=caption, parse_mode='HTML' if caption else None))
                            
                            # Запоминаем данные для последующего использования
                            media_group_data.append({
                                "file_id": item['url'],
                                "caption": caption,
                                "parse_mode": 'HTML' if caption else None
                            })

                        # Используем функцию для повторных попыток отправки медиа-группы
                        message_id = await send_media_group_with_retries(update, media_group)
                        if message_id is None:
                            await message_to_reply.reply_text(f'🚫Ошибка при отправке медиа-группы.')
                            return
                        await update.effective_chat.pin_message(message_id)
                        if caption:
                            await message_to_reply.reply_text(
                                f"✅ Медиагруппа отправлена с подписью.",
                                reply_markup=create_publish_button(user_id),  # Кнопка публикации
                                disable_web_page_preview=True
                            )

                        # Сохраняем message_id в хранилище
                        key = f"{user_id}_{message_id}"  # Создаем ключ как строку
                        if user_id not in media_group_storage:
                            media_group_storage[user_id] = {}

                        media_group_storage[user_id][key] = {
                            "media": media_group_data,
                            "scheduled": 'Отсутствует',
                            "time": time,
                            "original_link": article_url,  # <--- ДОБАВИТЬ ЭТУ СТРОКУ
                            # === ДОБАВЛЯЕМ МУЗЫКУ В БАЗУ ===
                            "music_post": music_post_flag,
                            "musicmedia": music_media_data
                            # ===============================
                        }
                        await update.effective_chat.pin_message(message_id)                        
                        save_media_group_data(media_group_storage, user_id)  # Сохраняем в файл


                if image_count == 1:
                    single_image = next((item for item in media if item['type'] == 'image'), None)
                    if single_image:
                        caption = f'{author_line}\n<a href="{article_url}">Оригинал</a> • <a href="{webappurl}">Галерея</a>{links_string}'
                        
                        # Формируем временный ключ
                        temp_key = f"{user_id}_0"  # Используем временный ключ до получения message_id
                        
                        # Формируем временную запись
                        media_group_storage.setdefault(user_id, {})  # Убедитесь, что для user_id есть пространство
                        media_group_storage[user_id][temp_key] = {
                            "media": [
                                {
                                    "file_id": single_image['url'],
                                    "caption": caption,
                                    "parse_mode": 'HTML'
                                }
                            ],
                            "scheduled": 'Отсутствует',
                            "time": time,
                            "original_link": article_url,  # <--- ДОБАВИТЬ ЭТУ СТРОКУ
                            # === ДОБАВЛЯЕМ МУЗЫКУ В БАЗУ ===
                            "music_post": music_post_flag,
                            "musicmedia": music_media_data
                            # ===============================
                        }
                        
                        # Отправляем изображение
                        message = await send_photo_with_retries(
                            update=update,
                            photo_url=single_image['url'],
                            caption=caption,
                            parse_mode='HTML'
                        )
                        if not message:
                            await message_to_reply.reply_text('🚫Ошибка при отправке изображения. /restart')
                            return
                        
                        # Обновляем ключ с использованием message_id
                        message_id = message.message_id
                        updated_key = f"{user_id}_{message_id}"
                        media_group_storage[user_id][updated_key] = media_group_storage[user_id].pop(temp_key)
                        
                        # Закрепляем сообщение
                        await update.effective_chat.pin_message(message_id)
                        
                        # Сохраняем данные в Firebase
                        save_media_group_data(media_group_storage, user_id)

                elif image_count == 0:
                    message_with_link = f'{author_line}\n<a href="{article_url}">Оригинал</a>'
                    
                    # Формируем временный ключ
                    temp_key = f"{user_id}_0"  # Используем временный ключ до получения message_id
                    
                    # Формируем временную запись
                    media_group_storage.setdefault(user_id, {})  # Убедитесь, что для user_id есть пространство
                    media_group_storage[user_id][temp_key] = {
                        "media": [
                            {
                                "file_id": None,
                                "caption": message_with_link,
                                "parse_mode": 'HTML'
                            }
                        ],
                        "scheduled": 'Отсутствует',
                        "time": time,
                        "original_link": article_url,  # <--- ДОБАВИТЬ ЭТУ СТРОКУ
                        # === ДОБАВЛЯЕМ МУЗЫКУ В БАЗУ ===
                        "music_post": music_post_flag,
                        "musicmedia": music_media_data
                        # ===============================
                    }
                    
                    # Отправляем сообщение
                    message = await message_to_reply.reply_text(message_with_link, parse_mode='HTML')
                    if not message:
                        await message_to_reply.reply_text('🚫Ошибка при отправке сообщения. /restart')
                        return
                    
                    # Обновляем ключ с использованием message_id
                    message_id = message.message_id
                    updated_key = f"{user_id}_{message_id}"
                    media_group_storage[user_id][updated_key] = media_group_storage[user_id].pop(temp_key)
                    
                    # Сохраняем данные в Firebase
                    save_media_group_data(media_group_storage, user_id)

                    # Отправляем уведомление пользователю
                    await message_to_reply.reply_text(
                        "✅ Сообщение без изображений успешно отправлено.",
                        disable_web_page_preview=True
                    )

                # --- РЕКОМЕНДУЕМЫЙ ВАРИАНТ ---
                # ЭТОТ КОД нужно поместить в самый конец блока if response_json.get('ok'):, 
                # ПОСЛЕ всех обработок image_count и ПОЛУЧЕНИЯ message_id.
                
                # Немедленное планирование задачи, если было указано время
                if time and message_id:
                    key_for_job = f"{user_id}_{message_id}"
                    # 'pub_dt' - это объект datetime, который был вычислен в начале функции
                    schedule_publication_job(
                        job_queue=context.job_queue,
                        user_id=user_id,
                        message_id=message_id,
                        key=key_for_job,
                        pub_dt_aware=pub_dt
                    )
                    # Опционально: уведомить пользователя о точном времени
                    await message_to_reply.reply_text(f"✅ Публикация запланирована на {time}.")

                image_text = (
                    "изображение" if image_count % 10 == 1 and image_count % 100 != 11
                    else "изображения" if 2 <= image_count % 10 <= 4 and (image_count % 100 < 10 or image_count % 100 >= 20)
                    else "изображений"
                )

                post_text = (
                    f'Готово✅\n'
                    f'====--- В посте {image_count} {image_text}. ---====\n'
                )
                
                if time:
                    post_text += f'\n⏳Запись отложена на {time}⏳'
                
                post_text += (
                    '\n\nНажмите одну из кнопок ниже, чтобы опубликовать его в вашу группу или канал, '
                    'отредактировать или предложить в Анемон'
                )
                
                await message_to_reply.reply_text(
                    post_text,
                    reply_markup=create_publish_button(user_id, message_id)
                )

                # Отправляем сообщение с кнопкой для публикации в ВК

                del user_data[user_id]


                # Вызов команды restart
                await rerestart(update, context)

                return ConversationHandler.END
            else:
                await message_to_reply.reply_text('🚫Ошибка при создании статьи. /restart')
        except requests.RequestException as e:
            logger.info(f"Request error: {e}")
            await message_to_reply.reply_text('🚫Ошибка при создании статьи. /restart')
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            await message_to_reply.reply_text('🚫Произошла неожиданная ошибка. /restart')






async def schedule_post_handler(update: Update, context: CallbackContext) -> None:
    """
    Показывает начальную клавиатуру для планирования.
    Загружает существующие значения из Firebase, если они есть.
    """
    query = update.callback_query
    await query.answer()
    
    _, user_id_str, message_id_str = query.data.split('_')
    user_id = int(user_id_str)
    message_id = int(message_id_str)
    
    # Ключ для хранения выбора в user_data, уникальный для каждого поста
    selection_key = f'schedule_{user_id}_{message_id}'
    
    # Загружаем данные из Firebase
    key = f"{user_id}_{message_id}"
    try:
        ref = db.reference(f'users_publications/{user_id}/{key}')
        post_data = ref.get() or {}
    except Exception as e:
        logging.error(f"Ошибка при загрузке поста из Firebase: {e}")
        post_data = {}
        
    selections = {}
    now = datetime.now()

    # Если есть ключ 'time', парсим его
    if 'time' in post_data and post_data['time']:
        try:
            # Формат "день.месяц, час:минута"
            time_str = post_data['time']
            day_month, hour_minute = time_str.split(',')
            day = int(day_month.split('.')[0])
            month = int(day_month.split('.')[1])
            hour = int(hour_minute.split(':')[0].strip())
            minute = int(hour_minute.split(':')[1])
            
            selections['day'] = day
            selections['hour'] = hour
            selections['minute'] = minute
            
            if month == now.month:
                selections['month'] = 'current'
            # Проверяем, является ли месяц следующим (учитывая переход через год)
            elif month == (now.month % 12) + 1:
                selections['month'] = 'next'
                
        except (ValueError, IndexError) as e:
            logging.warning(f"Не удалось распарсить 'time': {post_data.get('time')}. Ошибка: {e}")

    # 👇 ВСТАВЬ ЭТО СЮДА:
    if 'month' not in selections:
        selections['month'] = 'current'
    
    # Проверяем ключи onlyvk/onlytg
    if post_data.get('onlytg'):
        selections['platform'] = 'tg'
    elif post_data.get('onlyvk'):
        selections['platform'] = 'vk'
    else:
        # Если ни один ключ не установлен, считаем что это "в оба"
        selections['platform'] = 'both'
        
    # Сохраняем начальные/загруженные выборы в user_data
    context.user_data[selection_key] = selections
    
    keyboard = create_schedule_keyboard(user_id, message_id, selections)
    chat_id = query.message.chat_id  # ID чата, откуда пришёл callback
    await context.bot.send_message(
        chat_id=chat_id,
        text="Выберите дату, время и место для отложенной публикации:",
        reply_markup=keyboard
    )


async def schedule_update_handler(update: Update, context: CallbackContext) -> None:
    """
    Обновляет клавиатуру при выборе опции.
    """
    query = update.callback_query
    
    parts = query.data.split('_')
    # schedule_update_user_id_message_id_type_value
    user_id = int(parts[2])
    message_id = int(parts[3])
    selection_type = parts[4]
    selection_value = parts[5]

    # Преобразуем числовые значения
    if selection_value.isdigit():
        selection_value = int(selection_value)

    selection_key = f'schedule_{user_id}_{message_id}'
    
    # Получаем или создаем словарь выборов
    selections = context.user_data.get(selection_key, {})
    
    # Обновляем выбор
    selections[selection_type] = selection_value
    context.user_data[selection_key] = selections
    
    # Перерисовываем клавиатуру
    keyboard = create_schedule_keyboard(user_id, message_id, selections)
    await query.edit_message_reply_markup(reply_markup=keyboard)
    await query.answer() # Ответ без текста, просто чтобы убрать "часики"

async def schedule_confirm_handler(update: Update, context: CallbackContext) -> None:
    """
    Подтверждает выбор, валидирует дату и сохраняет в Firebase.
    """
    query = update.callback_query
    
    _, _, user_id_str, message_id_str = query.data.split('_')
    user_id = int(user_id_str)
    message_id = int(message_id_str)
    
    selection_key = f'schedule_{user_id}_{message_id}'
    selections = context.user_data.get(selection_key, {})

    # ### ИЗМЕНЕНО: Начало блока ###
    # Устанавливаем значения по умолчанию (завтрашний день), если они не были выбраны пользователем.
    # Это гарантирует, что даже если пользователь ничего не нажал, у нас будет корректная дата.
    if 'day' not in selections or 'month' not in selections:
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        
        if 'day' not in selections:
            selections['day'] = tomorrow.day
        
        if 'month' not in selections:
            # Если завтрашний день в другом месяце, выбираем "Следующий" месяц
            if now.month != tomorrow.month:
                selections['month'] = 'next'
            else:
                selections['month'] = 'current'
    # ### ИЗМЕНЕНО: Конец блока ###
    
    # --- Валидация ---
    required_keys = ['month', 'day', 'hour', 'minute', 'platform']
    if not all(key in selections for key in required_keys):
        await query.answer("Пожалуйста, выберите все параметры: месяц, день, час, минуту и куда публиковать.", show_alert=True)
        return

    now = datetime.now()
    year = now.year
    
    if selections['month'] == 'current':
        month = now.month
    else: # 'next'
        month = now.month + 1
        if month > 12:
            month = 1
            year += 1
            
    day = selections['day']
    
    # Проверка на корректность даты (например, 31 февраля)
    try:
        # calendar.monthrange(year, month) возвращает (день недели первого дня, кол-во дней в месяце)
        num_days_in_month = calendar.monthrange(year, month)[1]
        if day > num_days_in_month:
            await query.answer(f"Выбрана неверная дата: в {calendar.month_name[month].lower()} {year} года всего {num_days_in_month} дней.", show_alert=True)
            return
        
        # Полная проверка, что выбранное время не в прошлом
        scheduled_dt = datetime(year, month, day, selections['hour'], selections['minute'])
        if scheduled_dt < now:
            await query.answer("Выбранное время уже прошло. Пожалуйста, выберите будущее время.", show_alert=True)
            return

    except ValueError: # На случай, если month некорректен (хотя наша логика это исключает)
        await query.answer("Произошла ошибка с выбором месяца. Попробуйте еще раз.", show_alert=True)
        return
        
    # --- Сохранение в Firebase ---
    time_string = f"{selections['day']:02d}.{month:02d}, {selections['hour']:02d}:{selections['minute']:02d}"
    
    updates = {
        'time': time_string,
        'onlyvk': None, # Сначала сбрасываем оба ключа
        'onlytg': None
    }
    
    if selections['platform'] == 'tg':
        updates['onlytg'] = True
    elif selections['platform'] == 'vk':
        updates['onlyvk'] = True
    # Если 'both', то оба ключа остаются None (т.е. будут удалены из Firebase)

    try:
        key = f"{user_id}_{message_id}"
        ref = db.reference(f'users_publications/{user_id}/{key}')
        ref.update(updates)

        moscow_tz = pytz.timezone('Europe/Moscow')
        now = datetime.now(moscow_tz)  # aware datetime           
        # Парсим без года, добавим его позже
        pub_dt_naive = datetime.strptime(time_string, "%d.%m, %H:%M")

        # Добавляем текущий год
        pub_dt_with_year = pub_dt_naive.replace(year=now.year)

        # Делаем aware из naive, указываем зону
        pub_dt_aware = moscow_tz.localize(pub_dt_with_year)

        # Если время уже прошло — переносим на следующий год
        if pub_dt_aware < now:
            pub_dt_with_year = pub_dt_with_year.replace(year=now.year + 1)
            pub_dt_aware = moscow_tz.localize(pub_dt_with_year)



        schedule_publication_job(
            job_queue=context.job_queue,
            user_id=user_id,
            message_id=message_id,
            key=key,
            pub_dt_aware=pub_dt_aware,
            only_tg=selections['platform'] == 'tg',
            only_vk=selections['platform'] == 'vk'
        )

        # Очистка временных данных
        if selection_key in context.user_data:
            del context.user_data[selection_key]
            
        await query.answer("✅ Настройки сохранены!", show_alert=False)
        await query.message.edit_text(
            f"✅ Публикация запланирована на: *{time_string}*",
            parse_mode='Markdown'
        )

        # --- 🔔 УВЕДОМЛЕНИЕ ДЛЯ ВТОРОГО ПОЛЬЗОВАТЕЛЯ ---
        try:
            # Получаем краткий текст поста
            post_key = f"{user_id}_{message_id}"
            post_caption = await get_post_caption(post_key)

            # Определяем получателя уведомления
            if user_id == 6217936347:
                target_user_id = 419817885
                sender_name = "Артём"
            elif user_id == 419817885:
                target_user_id = 6217936347
                sender_name = "Нова"
            else:
                target_user_id = None

            # Если это один из них — отправляем уведомление
            if target_user_id:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=(
                        f"{sender_name} добавил отложенный пост на {time_string}, "
                        f"с содержимым: {post_caption}\n\n"
                        f"Для просмотра отложенных постов введите /otl"
                    )
                )
        except Exception as e:
            logging.info(f"Ошибка при отправке уведомления другому пользователю: {e}")

    except Exception as e:
        logging.error(f"Ошибка при обновлении Firebase: {e}")
        await query.answer(f"🚫 Ошибка при сохранении: {e}", show_alert=True)


def create_schedule_keyboard(user_id: int, message_id: int, selections: dict) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора даты и времени публикации.
    
    :param user_id: ID пользователя
    :param message_id: ID сообщения с постом
    :param selections: Словарь с текущими выборами пользователя (например, {'month': 'current', 'day': 15})
    :return: Объект InlineKeyboardMarkup
    """
    keyboard = []
    
    # --- Секция выбора месяца ---
    keyboard.append([InlineKeyboardButton("Выберите месяц:", callback_data='noop')])
    now = datetime.now()
    # ### ИЗМЕНЕНО: Начало блока ###
    # Вычисляем завтрашний день и месяц по умолчанию
    tomorrow = now + timedelta(days=1)
    default_day = tomorrow.day
    # Определяем, находится ли завтрашний день в следующем месяце
    default_month_key = 'next' if now.month != tomorrow.month else 'current'
    # ### ИЗМЕНЕНО: Конец блока ###

    # Получаем текущий, следующий и через один месяц
    month_options = {
        'current': now.month,
        'next': (now.month % 12) + 1,
        'plus2': ((now.month + 1) % 12) + 1,
    }

    # Если месяц ещё не выбран — по умолчанию выбирается текущий
    selected_month_key = selections.get('month', 'current')

    month_texts = {
        'current': "Текущий",
        'next': "Следующий",
        'plus2': "Через один",
    }

    month_buttons = []
    for key, name in month_texts.items():
        text = f"✅ {name}" if selected_month_key == key else name
        month_buttons.append(
            InlineKeyboardButton(
                text,
                callback_data=f"schedule_update_{user_id}_{message_id}_month_{key}"
            )
        )
    keyboard.append(month_buttons)

    # --- Секция выбора дня ---
    keyboard.append([InlineKeyboardButton("Выберите день:", callback_data='noop')])
    selected_day = selections.get('day', default_day)
    
    day_buttons = []
    for day in range(1, 32):
        day_text = str(day)
        # Сравниваем с `selected_day`, который теперь содержит либо выбор пользователя, либо значение по умолчанию
        if selected_day == day:
            day_text = f"✅ {day}"
            
        day_buttons.append(InlineKeyboardButton(day_text, callback_data=f"schedule_update_{user_id}_{message_id}_day_{day}"))
        if len(day_buttons) == 6:
            keyboard.append(day_buttons)
            day_buttons = []
    if day_buttons:
        keyboard.append(day_buttons)

    # --- Секция выбора часа ---
    keyboard.append([InlineKeyboardButton("Выберите час:", callback_data='noop')])
    hour_buttons = []
    for hour in range(24):
        hour_text = f"{hour:02d}"
        if selections.get('hour') == hour:
            hour_text = f"✅ {hour:02d}"
        hour_buttons.append(InlineKeyboardButton(hour_text, callback_data=f"schedule_update_{user_id}_{message_id}_hour_{hour}"))
        if len(hour_buttons) == 6:
            keyboard.append(hour_buttons)
            hour_buttons = []
    if hour_buttons:
        keyboard.append(hour_buttons)
        
    # --- Секция выбора минуты ---
    keyboard.append([InlineKeyboardButton("Выберите минуту:", callback_data='noop')])
    minute_buttons = []
    for minute in range(0, 60, 5):
        minute_text = f"{minute:02d}"
        if selections.get('minute') == minute:
            minute_text = f"✅ {minute:02d}"
        minute_buttons.append(InlineKeyboardButton(minute_text, callback_data=f"schedule_update_{user_id}_{message_id}_minute_{minute}"))
        if len(minute_buttons) == 6:
            keyboard.append(minute_buttons)
            minute_buttons = []
    if minute_buttons:
        keyboard.append(minute_buttons)

    # --- Секция выбора платформы ---
    keyboard.append([InlineKeyboardButton("Выберите куда опубликовать:", callback_data='noop')])
    tg_text, vk_text, both_text = "Телеграм", "ВК", "В оба"
    if selections.get('platform') == 'tg':
        tg_text = "✅ Телеграм"
    elif selections.get('platform') == 'vk':
        vk_text = "✅ ВК"
    elif selections.get('platform') == 'both':
        both_text = "✅ В оба"
    keyboard.append([
        InlineKeyboardButton(tg_text, callback_data=f"schedule_update_{user_id}_{message_id}_platform_tg"),
        InlineKeyboardButton(vk_text, callback_data=f"schedule_update_{user_id}_{message_id}_platform_vk"),
        InlineKeyboardButton(both_text, callback_data=f"schedule_update_{user_id}_{message_id}_platform_both"),
    ])

    # --- Кнопки управления ---
    keyboard.append([InlineKeyboardButton("✅ Подтвердить выбор", callback_data=f"schedule_confirm_{user_id}_{message_id}")])
    keyboard.append([
        InlineKeyboardButton("🗑 Удалить из отложенных", callback_data=f"otloj_delete_{user_id}_{message_id}")
    ])      
    keyboard.append([InlineKeyboardButton("❌ Закрыть окно", callback_data="ozondelete_msg")])
    
    return InlineKeyboardMarkup(keyboard)

async def delete_scheduled_time_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    try:
        _, _, user_id_str, message_id_str = query.data.split('_')
        user_id = int(user_id_str)
        message_id = int(message_id_str)
        key = f"{user_id}_{message_id}"

        # Удаляем ключ 'time' из Firebase
        ref = db.reference(f'users_publications/{user_id}/{key}')
        ref.child('time').delete()

        # Удаляем связанные задачи из JobQueue
        tg_job_name = f"tg_pub_{key}"
        vk_job_name = f"vk_pub_{key}"

        tg_jobs = context.job_queue.get_jobs_by_name(tg_job_name)
        vk_jobs = context.job_queue.get_jobs_by_name(vk_job_name)

        for job in tg_jobs + vk_jobs:
            job.schedule_removal()
            logging.info(f"Удалена задача: {job.name}")

        # Удаляем сообщение с клавиатурой
        await query.message.delete()

        # Подтверждение пользователю
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="✅ Публикация удалена из отложенных и задача отменена."
        )

    except Exception as e:
        logging.error(f"Ошибка при удалении из отложенных: {e}")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="❌ Не удалось удалить из отложенных. Попробуйте позже."
        )


def create_publish_button(user_id, message_id):
    keyboard = [
        [
            InlineKeyboardButton("🗂 Сохранить пост себе в папку 🗂", callback_data=f"snooze_with_tag_{user_id}_{message_id}")
        ],   
        [
            InlineKeyboardButton("Пост в Telegram", callback_data=f"publish_{user_id}_{message_id}"),
            InlineKeyboardButton("Пост в ВК", callback_data=f"vkpub_{user_id}_{message_id}")
        ],
        [
            InlineKeyboardButton("Пост в X.com", callback_data=f"twitterpub_{user_id}_{message_id}")
        ],   
        [
            InlineKeyboardButton("🗓️ Отложить 🗓️", callback_data=f"schedulepost_{user_id}_{message_id}")
        ],
        [
            InlineKeyboardButton("🌠 Предложить этот пост в Анемон 🌠", callback_data=f"share_{user_id}_{message_id}")
        ],
        [   
            InlineKeyboardButton("━━━━━━━━━━ ✦ ━━━━━━━━━━", callback_data='separator')
        ],         
        [
            InlineKeyboardButton("✏️ Заменить подпись ✏️", callback_data=f"caption_{user_id}_{message_id}")
        ],      
        [
            InlineKeyboardButton("🎨 Сортировать по палитре 🎨", callback_data=f"palettesort_{user_id}_{message_id}")
        ],          
        [
            InlineKeyboardButton("🔄 Случайно перемешать изображения 🔄", callback_data=f"shuffle_{user_id}_{message_id}")
        ],
        [
            InlineKeyboardButton("🔀 Поменять 2 изображения местами 🔀", callback_data=f"swapimages_{user_id}_{message_id}")
        ],
        [
            InlineKeyboardButton("❌ Удалить 1 изображение ❌", callback_data=f"filedelete_{user_id}_{message_id}")
        ]                     
    ]        
    return InlineKeyboardMarkup(keyboard) 

def create_publish_and_snooze_buttons(user_id, message_id):
    """Создает клавиатуру с кнопками для публикации и отложенной отправки."""
    keyboard = [
        [
            InlineKeyboardButton("🗂 Сохранить пост себе в папку 🗂", callback_data=f"snooze_with_tag_{user_id}_{message_id}")
        ],
        [
            InlineKeyboardButton("🔄 Случайно перемешать изображения 🔄", callback_data=f"shuffle_{user_id}_{message_id}")
        ],
        [
            InlineKeyboardButton("🎨 Сортировать по палитре 🎨", callback_data=f"palettesort_{user_id}_{message_id}")
        ],
        [
        InlineKeyboardButton("Поменять 2 изображения местами", callback_data=f"swapimages_{user_id}_{message_id}")
        ],
        [
        InlineKeyboardButton("❌ Удалить 1 изображение ❌", callback_data=f"filedelete_{user_id}_{message_id}")
        ]                

    ]
    return InlineKeyboardMarkup(keyboard)




def create_shuffle_buttons(user_id, message_id):

    keyboard = [
        [
            InlineKeyboardButton("Опубликовать в Telegram", callback_data=f"publish_{user_id}_{message_id}")
        ],
        [
            InlineKeyboardButton("Опубликовать в ВК", callback_data=f"vkpub_{user_id}_{message_id}")
        ],
        [
            InlineKeyboardButton("🗂 Сохранить пост себе в папку 🗂", callback_data=f"snooze_with_tag_{user_id}_{message_id}")
        ],
        [
            InlineKeyboardButton("🔄 Случайно перемешать ещё раз 🔄", callback_data=f"shuffle_{user_id}_{message_id}")
        ],
        [
            InlineKeyboardButton("🎨 Сортировать по палитре 🎨", callback_data=f"palettesort_{user_id}_{message_id}")
        ],
        [
        InlineKeyboardButton("Поменять 2 изображения местами", callback_data=f"swapimages_{user_id}_{message_id}")
        ],
        [
        InlineKeyboardButton("❌ Удалить 1 изображение ❌", callback_data=f"filedelete_{user_id}_{message_id}")
        ]    
    ]
    return InlineKeyboardMarkup(keyboard)     


async def handle_tag_selection(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    await query.message.delete()

    # Извлекаем выбранный смайлик и данные
    _, tag, user_id_str, message_id_str = query.data.split('_')
    user_id = int(user_id_str)
    message_id = int(message_id_str)
    # Проверяем, есть ли данные о генерации в контексте
    global media_group_storage
    # Загружаем данные

    generation_data = context.user_data.get("generation_data")

    if generation_data:
        # Если данные о генерации есть, используем их
        media_group_storage = load_publications_from_firebase()
        user_data = media_group_storage.get(str(user_id), {})

        # Формируем данные для сохранения
        media_group_data = {
            "media": [
                {
                    "caption": generation_data["caption"],  # HTML-капшн
                    "file_id": generation_data["file_id"],  # URL изображения
                    "parse_mode": "HTML"
                }
            ],
            "scheduled": tag  # Метка (эмодзи)
        }

        # Сохраняем данные в Firebase
        user_data[f"{user_id}_{message_id}"] = media_group_data
        media_group_storage[str(user_id)] = user_data
        save_publications_to_firebase(user_id, f"{user_id}_{message_id}", media_group_data)

        # Очищаем данные о генерации из контекста
        context.user_data.pop("generation_data", None)

        # Уведомление пользователя
        await query.message.reply_text(
            f"✅ Запись успешно добавлена в папку {tag}.\n Теперь вы можете найти её там и продолжить редактирование, либо опубликовать",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🗂 Посмотреть мои папки 🗂", callback_data="scheduled_by_tag")],
                [InlineKeyboardButton("‼️ Перезапуск бота ‼️", callback_data='restart')]
            ])
        )
        return
    media_group_storage = load_publications_from_firebase()   

    # Доступ к данным по user_id
    user_data = media_group_storage.get(str(user_id))
  
    if not user_data:
        await query.message.reply_text("🚫 Ошибка: Данные пользователя не найдены.")
        return

    # Доступ к данным по message_id
    message_key = f"{user_id}_{message_id}"
    media_group_data = user_data.get(message_key)
    if not media_group_data:
        await query.message.reply_text("🚫 Ошибка: Данные о медиагруппе не найдены.")
        return

    # Обновляем значение ключа 'scheduled'
    media_group_data["scheduled"] = tag

    # Сохраняем обновлённые данные обратно
    user_data[message_key] = media_group_data
    media_group_storage[str(user_id)] = user_data

    # Сохраняем обновлённый словарь в Firebase
    save_media_group_data(media_group_storage, user_id)

    # Уведомление пользователя
    await query.message.reply_text(
        f"✅ Запись успешно добавлена в папку {tag}.\n Теперь вы можете найти её там и продолжить редактирование, либо опубликовать",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🗂 Посмотреть мои папки 🗂", callback_data="scheduled_by_tag")],
            [InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')]
        ])
    )






def create_emoji_keyboard(emojis, user_id, message_id):
    keyboard = []
    row = []
    for emoji in emojis:
        row.append(InlineKeyboardButton(emoji, callback_data=f"tag_{emoji}_{user_id}_{message_id}"))
        if len(row) == 4:  # Если в строке 4 кнопки, добавляем её в клавиатуру
            keyboard.append(row)
            row = []  # Начинаем новую строку
    if row:  # Добавляем оставшиеся кнопки, если они есть
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

# Асинхронная функция обработки
async def handle_snooze_with_tag_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    await query.message.delete()
    # Извлекаем данные из callback_data
    print(f"Received callback data: {query.data}")  # Диагностика
    parts = query.data.split('_')
    user_id_str = parts[-2]  # Предпоследний элемент — user_id
    message_id_str = parts[-1]  # Последний элемент — message_id

    user_id = int(user_id_str)
    message_id = int(message_id_str)

    emojis = [
        "👀", "🤷‍♂️", "🧶", "🦊", "🦄", "🦆", "🐳", "🌿", "🌸", "🍓",
        "🍑", "🍆", "🌈", "🌧", "☀️", "⭐️", "🫖", "🌙", "🌠", "❄️",
        "🗑", "📎", "✏️", "🎨", "😈", "📷", "📚", "⏳", "✅", "❇️",
        "❌", "🔄", "🩷", "💛", "💚", "💙", "❤️", "💜", "🖤", "🤍",
    ]

    # Создаём клавиатуру с эмодзи
    reply_markup = create_emoji_keyboard(emojis, user_id, message_id)

    # Отправляем сообщение с клавиатурой
    await query.message.reply_text("Выберите метку для записи:", reply_markup=reply_markup)



# Функция для отображения отложенных записей с определённой меткой
async def show_scheduled_by_tag(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    # Логируем конкретно query.data для удобства отладки
    logger.info(f"Callback data: {query.data}")
    # Получаем выбранную метку из callback_data
    _, _, tag = query.data.split('_')

    # Если пришёл ключ "nofolder", заменяем его на "Отсутствует"
    if tag == "nofolder":
        tag = "Отсутствует"

    global media_group_storage
    # Загружаем данные из файла
    media_group_storage = load_publications_from_firebase()

    # ID текущего пользователя
    current_user_id = str(update.effective_user.id)

    scheduled = []
    # Проверяем данные только для текущего пользователя
    if current_user_id in media_group_storage:
        user_publications = media_group_storage[current_user_id]
        for message_id, data in user_publications.items():
            if isinstance(data, dict):
                
                # --- НАЧАЛО ИЗМЕНЕНИЙ ---
                
                # Флаг, который определяет, нужно ли добавлять запись в список
                record_matches = False

                # 1. Особая логика, если запрошен тег 'time'
                if tag == 'time':
                    # Ищем все записи, у которых просто есть ключ 'time'
                    if 'time' in data and data.get('time') is not None:
                        record_matches = True
                
                # 2. Стандартная логика для всех остальных тегов
                else:
                    record_tag = data.get('scheduled')
                    if record_tag == tag:
                        record_matches = True

                # Если запись подошла по одному из условий выше, обрабатываем её
                if record_matches:
                    
                # --- КОНЕЦ ИЗМЕНЕНИЙ ---

                    # Проверяем, что 'media' — это список
                    if 'media' in data and isinstance(data['media'], list):
                        media_list = data['media']
                        if media_list:
                            raw_caption = media_list[0].get('caption', '')

                            # Используем BeautifulSoup для очистки от HTML-разметки
                            soup = BeautifulSoup(raw_caption, 'html.parser')

                            # Оставляем только текст из гиперссылок
                            for a in soup.find_all('a'):
                                a.replace_with(a.get_text())

                            # Получаем очищенный текст
                            cleaned_caption = soup.get_text()

                            # Логика определения финального текста (ваша логика остается без изменений)
                            if "автор: " in cleaned_caption.lower():
                                match = re.search(r'автор:\s*([^•<\n]+)', cleaned_caption, re.IGNORECASE)
                                caption = match.group(1).strip() if match else ''
                            else:
                                caption = ' '.join(cleaned_caption.split()[:3])
                            logging.info(f"cleaned_caption {cleaned_caption}")                                
                            if cleaned_caption.startswith("Модель: Imagen3"):
                                match = re.search(r"Ваш запрос:\s*(.+)", cleaned_caption, re.DOTALL)
                                if match:
                                    caption = match.group(1).strip()
                            logging.info(f"cleaned_caption2 {cleaned_caption}")

                            # Добавляем в список с подписью
                            time_str = ''
                            # Теперь время будет добавляться к подписи для любой записи, где оно есть
                            time_value = data.get('time')
                            if time_value:
                                time_str = f"({time_value}) "
                            
                            # При добавлении в итоговый список мы используем исходный 'tag',
                            # чтобы кнопка и заголовок отображались корректно (например, "Записи из папки time")
                            scheduled.append((message_id, f"{time_str}{caption}", tag))



    if scheduled:
        page = int(context.user_data.get('folderpage', 0))
        items_per_page = 8
        total_pages = (len(scheduled) + items_per_page - 1) // items_per_page
        
        # Ограничиваем показ только нужными записями
        start = page * items_per_page
        end = start + items_per_page
        scheduled_page = scheduled[start:end]
        
        keyboard = [
            [InlineKeyboardButton("🗂 Другие папки 🗂", callback_data="scheduled_by_tag")],
            [InlineKeyboardButton("━━━━━━━━━━ ✦ ━━━━━━━━━━", callback_data="separator")]
        ]
        
        # Добавляем только записи текущей страницы
        for index, (key, caption, tag) in enumerate(scheduled_page):
            keyboard.append([InlineKeyboardButton(f"📗 {caption} ({tag})", callback_data=f"view_{key}")])
            keyboard.append([
                InlineKeyboardButton("В ТГ", callback_data=f"publish_{key}"),
                InlineKeyboardButton("В ВК", callback_data=f"vkpub_{key}"),
                InlineKeyboardButton("В X.com", callback_data=f"twitterpub_{key}"),
                InlineKeyboardButton("Удалить", callback_data=f"yrrasetag_{key}"),
            ])
        
        # Кнопки навигации (отображаются только если страниц больше 1)
        if total_pages > 1:
            prev_button = InlineKeyboardButton("◀ Назад", callback_data=f"folderpage_{page - 1}_{tag}") if page > 0 else InlineKeyboardButton("◀", callback_data="noop")
            next_button = InlineKeyboardButton("▶ Вперёд", callback_data=f"folderpage_{page + 1}_{tag}") if page < total_pages - 1 else InlineKeyboardButton("▶", callback_data="noop")

            keyboard.append([
                prev_button,
                InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="separator"),
                next_button
            ])
        
        # Дополнительные кнопки
        keyboard.append([
            InlineKeyboardButton("━━━━━━━━━━ ✦ ━━━━━━━━━━", callback_data="separator")
        ])
        keyboard.append([
            InlineKeyboardButton("🗑 Удалить все из этой папки 🗑", callback_data=f"tagdelete_{tag}")
        ])
        keyboard.append([
            InlineKeyboardButton("🌌В главное меню 🌌", callback_data='restart')
        ])        
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📋 Записи из папки {tag}:",
            reply_markup=reply_markup
        )
    else:
        await query.message.reply_text(f"🛑 Нет записей с меткой {tag}.")


async def generate_scheduled_keyboard(update: Update, context: CallbackContext, tag: str, page: int = 0) -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для показа запланированных записей по тегу."""
    global media_group_storage
    media_group_storage = load_publications_from_firebase()
    current_user_id = str(update.effective_user.id)
    scheduled = []

    if current_user_id in media_group_storage:
        user_publications = media_group_storage[current_user_id]
        for message_id, data in user_publications.items():
            if isinstance(data, dict):
                record_tag = data.get('scheduled', '')
                if record_tag == tag:
                    if 'media' in data and isinstance(data['media'], list):
                        media_list = data['media']
                        if media_list:
                            raw_caption = media_list[0].get('caption', '')
                            soup = BeautifulSoup(raw_caption, 'html.parser')
                            for a in soup.find_all('a'):
                                a.replace_with(a.get_text())
                            cleaned_caption = soup.get_text()
                            caption = (
                                re.search(r'автор:\s*([^•<\n]+)', cleaned_caption, re.IGNORECASE).group(1).strip()
                                if "автор: " in cleaned_caption.lower()
                                else ' '.join(cleaned_caption.split()[:3])
                            )
                            scheduled.append((message_id, caption, tag))

    items_per_page = 8
    total_pages = (len(scheduled) + items_per_page - 1) // items_per_page

    start = page * items_per_page
    end = start + items_per_page
    scheduled_page = scheduled[start:end]

    keyboard = [
        [InlineKeyboardButton("🗂 Другие папки 🗂", callback_data="scheduled_by_tag")],
        [InlineKeyboardButton("━━━━━━━━━━ ✦ ━━━━━━━━━━", callback_data="separator")]
    ]

    for index, (key, caption, tag) in enumerate(scheduled_page):
        keyboard.append([InlineKeyboardButton(f"📗 {caption} ({tag})", callback_data=f"view_{key}")])
        keyboard.append([
            InlineKeyboardButton("В ТГ", callback_data=f"publish_{key}"),
            InlineKeyboardButton("В ВК", callback_data=f"vkpub_{key}"),
            InlineKeyboardButton("В X.com", callback_data=f"twitterpub_{key}"),
            InlineKeyboardButton("Удалить", callback_data=f"yrrasetag_{key}"),
        ])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀ Назад", callback_data=f"folderpage_{page - 1}_{tag}"))
    nav_buttons.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="separator"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("▶ Вперёд", callback_data=f"folderpage_{page + 1}_{tag}"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton("━━━━━━━━━━ ✦ ━━━━━━━━━━", callback_data="separator")])
    keyboard.append([InlineKeyboardButton("🗑 Удалить все из этой папки 🗑", callback_data=f"tagdelete_{tag}")])
    keyboard.append([InlineKeyboardButton("🌌В главное меню 🌌", callback_data='restart')])

    return InlineKeyboardMarkup(keyboard)


async def change_page(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    action, page, tag = query.data.split('_')
    context.user_data['folderpage'] = int(page)
    
    # Передаем тег обратно в функцию отображения
    await show_scheduled_by_tag(update, context)



async def delete_all_by_tag(update: Update, context: CallbackContext) -> None:
    query = update.callback_query

    # Получаем выбранную метку из callback_data
    _, tag = query.data.split('_')
    global media_group_storage
    # Загружаем данные из файла
    media_group_storage = load_publications_from_firebase()

    # ID текущего пользователя
    current_user_id = str(update.effective_user.id)

    # Проверяем, что данные есть для текущего пользователя
    if current_user_id in media_group_storage:
        user_publications = media_group_storage[current_user_id]

        # Собираем ключи для удаления
        keys_to_delete = [
            key for key, data in user_publications.items()
            if isinstance(data, dict) and data.get('scheduled') == tag
        ]

        print(f"Tag from callback_data: '{tag}'")
        print(f"Keys to delete: {keys_to_delete}")

        # Удаляем записи из базы и локального хранилища
        delete_from_firebase(keys_to_delete, current_user_id)
        for key in keys_to_delete:
            user_publications.pop(key, None)

        # Если у пользователя больше нет записей, удаляем его из общего хранилища
        if not user_publications:
            media_group_storage.pop(current_user_id, None)

        print(f"Media group storage after deletion: {media_group_storage}")

        # Сохраняем обновлённые данные обратно в файл
        save_media_group_data(media_group_storage, current_user_id)

        await query.answer(f"✅ Все записи из папки '{tag}' удалены.", show_alert=True)
        await handle_scheduled_tags(update, context)

    else:
        await query.message.reply_text("🚫 У вас нет записей с такой меткой.")


async def yrrase_scheduled(update: Update, context: CallbackContext) -> None:
    query = update.callback_query

    # Извлекаем ключ и метку из callback_data
    _, key = query.data.split('yrrasetag_', maxsplit=1)
    tag = context.user_data.get('current_tag', 'Отсутствует')

    global media_group_storage
    media_group_storage = load_publications_from_firebase()
    current_user_id = str(update.effective_user.id)

    if current_user_id in media_group_storage:
        user_publications = media_group_storage[current_user_id]
        if key in user_publications:
            scheduled_tag = user_publications[key].get('scheduled', "Отсутствует")
            delete_from_firebase([key], current_user_id)
            user_publications.pop(key, None)
            if not user_publications:
                media_group_storage.pop(current_user_id, None)
            save_media_group_data(media_group_storage, current_user_id)

            # ❗️Дополнительно: Удаление задач из JobQueue
            try:
                tg_job_name = f"tg_pub_{key}"
                vk_job_name = f"vk_pub_{key}"

                tg_jobs = context.job_queue.get_jobs_by_name(tg_job_name)
                vk_jobs = context.job_queue.get_jobs_by_name(vk_job_name)

                for job in tg_jobs + vk_jobs:
                    job.schedule_removal()
                    logging.info(f"Удалена задача из JobQueue: {job.name}")

            except Exception as e:
                logging.warning(f"Не удалось удалить задачу из JobQueue: {e}")

            # Обновляем клавиатуру
            page = context.user_data.get('folderpage', 0)
            reply_markup = await generate_scheduled_keyboard(update, context, scheduled_tag, page)

            await query.edit_message_text(
                f"📋 Записи из папки {scheduled_tag}:",
                reply_markup=reply_markup
            )
            return

    await query.message.reply_text("🚫 Указанная запись не найдена.")



# Функция для обработки команды /scheduledmark
async def handle_scheduled_tags(update: Update, context: CallbackContext) -> None:
    # Определяем, вызвана ли функция командой или нажатием кнопки
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        send_method = query.message.reply_text
        user_id = str(query.from_user.id)
    else:
        send_method = update.message.reply_text
        user_id = str(update.message.from_user.id)
    global media_group_storage
    # Загружаем данные
    media_group_storage = load_publications_from_firebase()
    tag_counts = {}  # Словарь для подсчёта количества постов на метку
    other_count = 0  # Счётчик для временных меток
    no_folder_count = 0  # Счётчик для записей без метки ("Отсутствует")

    # Проверяем, есть ли записи для данного user_id
    if user_id not in media_group_storage:
        await send_method("🛑 У вас нет записей.")
        return

    # Фильтруем записи только для данного пользователя
    user_publications = media_group_storage[user_id]

    # Подсчёт количества записей для каждой метки
    scheduled_time_count = 0  # Счётчик записей с ключом 'time'

    # Подсчёт количества записей для каждой метки
    for message_id, data in user_publications.items():
        if isinstance(data, dict):
            tag = data.get('scheduled')

            # Считаем отложенные публикации
            if 'time' in data:
                scheduled_time_count += 1

            # Пропускаем записи с scheduled == None
            if tag is None:
                continue

            if tag == "Отсутствует":
                no_folder_count += 1
                continue

            # Проверяем, является ли метка временем
            try:
                datetime.strptime(tag, "%Y-%m-%d %H:%M")
                other_count += 1
            except ValueError:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Создаём клавиатуру с метками
    keyboard = []
    row = []
    for tag, count in sorted(tag_counts.items()):
        row.append(InlineKeyboardButton(f"{tag} ({count})", callback_data=f"filter_tag_{tag}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    # Добавляем кнопку "Отложенные публикации"
    if scheduled_time_count > 0:
        keyboard.append([InlineKeyboardButton(f"Отложенные публикации ({scheduled_time_count})", callback_data='filter_tag_time')])

    # Добавляем кнопку "Нет метки", если есть временные метки
    if other_count > 0:
        keyboard.append([InlineKeyboardButton(f"Нет метки ({other_count})", callback_data="filter_tag_other")])

    # Добавляем кнопку "Записи без папки", если есть такие
    if no_folder_count > 0:
        keyboard.append([InlineKeyboardButton(f"Записи без папки ({no_folder_count})", callback_data="filter_tag_nofolder")])

    # Кнопка возврата в главное меню
    keyboard.append([InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')])

    total_count = sum(tag_counts.values()) + other_count + no_folder_count
    # Отправляем сообщение с клавиатурой
    if keyboard:
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = await send_method("Выберите папку для отображения записей:", reply_markup=reply_markup)
        context.user_data['last_message_id'] = message.message_id        
    else:
        await send_method("🛑 Нет доступных меток.")





from telegram import Update, MessageOriginChannel  # Добавлен импорт MessageOriginChannel
from telegram.ext import CallbackContext
import logging




async def handle_forwarded_message(update: Update, context: CallbackContext):
    message = update.message
    user_id = message.from_user.id


    # Проверяем, является ли сообщение пересланным из канала
    if message.forward_origin and isinstance(message.forward_origin, MessageOriginChannel):
        channel_data = message.forward_origin.chat

        # Получаем ID канала
        chat_id = channel_data.id

        try:
            # Проверяем права администратора
            is_admin = await check_admin_rights(context, chat_id, user_id)
            if not is_admin:
                await message.reply_text("🚫 У вас или у бота нет прав администратора в этом канале.")
                return

            # Сохраняем ID канала
            save_channel_to_firebase(chat_id, user_id)
            await message.reply_text(f"Канал успешно привязан! ID канала: {chat_id}")

            # Сбрасываем состояние ожидания
            del waiting_for_forward[user_id]
        except Exception as e:

            
            # Создаем разметку с кнопкой
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("‼️ Перезапуск бота ‼️", callback_data='restart')]
            ])
            
            # Отправляем сообщение с кнопкой
            await message.reply_text(
                "Произошла ошибка при привязке канала.", 
                reply_markup=keyboard
            )
    else:
        # Создаем разметку с кнопкой для другого сообщения
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("‼️ Перезапуск бота ‼️", callback_data='restart')]
        ])
        
        # Отправляем сообщение с кнопкой
        await message.reply_text(
            "Пожалуйста, пересылайте только сообщения из каналов. \n\nЕсли вы передумали, то перезапустите бота:",
            reply_markup=keyboard
        )


async def check_admin_rights(context: CallbackContext, chat_id: int, user_id: int) -> bool:
    """
    Проверяет, является ли пользователь администратором в указанном канале.
    """
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        return any(admin.user.id == user_id for admin in admins)
    except Exception as e:
        logging.error(f"Ошибка при проверке прав администратора: {e}")
        return False

import mimetypes









from html import escape

async def handle_replace_caption(update: Update, context: CallbackContext) -> int:
    """Обрабатывает нажатие на кнопку 'заменить текст'."""
    query = update.callback_query
    await query.answer()

    # Извлекаем user_id и message_id из callback_data
    _, user_id_str, message_id_str = query.data.split('_', maxsplit=2)
    user_id = int(user_id_str)
    message_id = int(message_id_str)
    key = f"{user_id}_{message_id}"
    global media_group_storage
    # Загружаем данные из Firebase
    media_group_storage = load_publications_from_firebase()

    # Проверяем, есть ли записи для указанного user_id
    user_publications = media_group_storage.get(str(user_id))
    if not user_publications:
        await query.message.reply_text("🚫 Ошибка: Пользовательские данные не найдены.")
        return ConversationHandler.END

    # Проверяем, что запись существует
    publication = user_publications.get(key)
    if not publication:
        await query.message.reply_text("🚫 Запись не найдена.")
        return ConversationHandler.END

    # Проверяем, что в публикации есть медиа
    media = publication.get('media')
    if not media or not isinstance(media, list):
        await query.message.reply_text("🚫 Ошибка: В записи отсутствуют медиафайлы.")
        return ConversationHandler.END

    # Извлекаем подпись первого изображения
    first_caption = media[0].get('caption', '🚫 Подпись отсутствует.')
    formatted_caption = escape(first_caption)  # Экранируем HTML
    # Сохраняем информацию о текущей публикации для этого пользователя
    waiting_for_caption[user_id] = key
    if user_id not in waiting_for_caption:
        waiting_for_caption[user_id] = True  # Помещаем пользователя в состояние ожидания

    # Создаём разметку для кнопки "Отмена"
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Отмена", callback_data='restart')]]
    )
    logger.info(f"Полученный user_id: {first_caption}") 
    # Отправляем текущую подпись и входим в режим ожидания новой
    await query.message.reply_text(
        text=f"Текущая подпись:\n\n{first_caption}\n\nВ формате HTML: <pre>{formatted_caption}</pre>\n\nВведите новую подпись. Вы можете использовать как форматирование встроенное в телеграм так и HTML Разметку. Всё форматирование, например жирный текст, спойлеры, гиперссылки будет сохранено.",
        parse_mode='HTML',
        disable_web_page_preview=True,
        reply_markup=keyboard  # Добавляем кнопки
    )

    return





async def handle_new_caption(update: Update, context: CallbackContext, key) -> int:
    """Обрабатывает ввод новой подписи."""
    user_id = str(update.effective_user.id)
    logger.info(f"Полученный Context: {context.__dict__}")
    logger.info(f"Полученный user_id: {user_id}")     
    handle_caption = key  
    # Логирование полного объекта Update
    logger.info(f"Полученный Update: {update.to_dict()}")
    
    if user_id not in user_data:
        user_data[user_id] = {}  # Инициализация пустого словаря для пользователя
    
    # Получаем новую подпись
    new_caption = update.message.text.strip()  # Убираем лишние пробелы

    if not new_caption:
        await update.message.reply_text("🚫 Ошибка: Подпись не может быть пустой.")
        return WAITING_FOR_NEW_CAPTION

    global media_group_storage
    media_group_storage = load_publications_from_firebase()

    # Проверяем, существует ли запись
    user_publications = media_group_storage.get(user_id)
    if not user_publications or key not in user_publications:
        await update.message.reply_text("🚫 Запись не найдена.")
        del waiting_for_caption[user_id]
        return ConversationHandler.END

    publication = user_publications[key]

    # Проверяем, что запись содержит медиафайлы
    media = publication.get('media')
    if not media or not isinstance(media, list):
        await update.message.reply_text("🚫 Ошибка: В записи отсутствуют медиафайлы.")
        del waiting_for_caption[user_id]
        return ConversationHandler.END

    # Форматируем подпись с учётом Telegram-разметки
    formatted_caption = format_text_to_html(update.message)
    formatted_caption = html.unescape(format_text_to_html(update.message))
    media[0]['caption'] = formatted_caption

    # Сохраняем обновленные данные в Firebase
    save_publications_to_firebase(user_id, key, publication)
    
    try:
        user_id = update.effective_user.id        
        # Создание клавиатуры с кнопками
        keyboard = [
            [InlineKeyboardButton("📄 Посмотреть обновлённую запись 📄", callback_data=f"view_{key}")],
            [
                InlineKeyboardButton("Пост ТГ", callback_data=f"publish_{key}"),
                InlineKeyboardButton("Пост ВК", callback_data=f"vkpub_{key}"),                
                InlineKeyboardButton("Удалить", callback_data=f"erase_{key}")
            ],
            [InlineKeyboardButton("🗂 Мои папки 🗂", callback_data="scheduled_by_tag")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправляем сообщение с кнопками
        await update.message.reply_text(f"✅ Подпись успешно обновлена на:\n{formatted_caption}", reply_markup=reply_markup, parse_mode='HTML', disable_web_page_preview=True,)
    except Exception as e:
        await update.message.reply_text(f"🚫 Ошибка сохранения данных: {e}")
    finally:
        del waiting_for_caption[user_id]
        
    # Завершаем обработку
    return ASKING_FOR_ARTIST_LINK




async def publish_to_telegram_scheduled(context: CallbackContext):
    """Публикует пост в Telegram по расписанию с поддержкой медиагрупп."""
    job_data = context.job.data
    user_id = job_data['user_id']
    message_id = job_data['message_id']

    bot = context.bot
    logging.info(f"Начало публикации в Telegram для user_id: {user_id}, message_id: {message_id}")

    # Загружаем данные из Firebase
    media_group_storage = load_publications_from_firebase()
    user_data = media_group_storage.get(str(user_id))
    if not user_data:
        logging.error(f"Данные пользователя {user_id} не найдены.")
        return

    key = f"{user_id}_{message_id}"
    media_group_data = user_data.get(key)
    logging.info(f"--- Анализ сообщения ID: {msg.message_id} ---")
    
    if not media_group_data:
        logging.error(f"Данные для публикации {key} не найдены.")
        return

    # --- ЛОГИКА МУЗЫКАЛЬНОЙ КНОПКИ ---
    is_music_post = media_group_data.get('music_post', False)
    music_reply_markup = None
    
    if is_music_post:
        web_app_url = f"https://anemonne.onrender.com/musicplayer/{user_id}/{key}"
        music_name = "Музыка"
        musicmedia = media_group_data.get('musicmedia', [])

        if musicmedia and isinstance(musicmedia, list):
            raw_name = musicmedia[0].get('music_name')
            if raw_name:
                music_name = raw_name.rsplit('.', 1)[0]
                if len(music_name) > 19:
                    cut = music_name[:19].rsplit(' ', 1)[0]
                    music_name = cut + "..."

        button_text = f"◄⠀▐▐ ⠀►  |  {music_name}"
        music_reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(text=button_text, url=web_app_url)]
        ])
    # ---------------------------------

    try:
        # Логика извлечения медиа и каналов
        media_items = media_group_data.get('media')
        channel_ref = db.reference('users_publications/channels')
        channels_data = channel_ref.get() or {}
        user_channels = [
            chat_id for chat_id, info in channels_data.items()
            if user_id in info.get('user_ids', [])
        ]

        if not user_channels:
            logging.warning(f"У пользователя {user_id} нет привязанных каналов.")
            return

        chat_id = user_channels[0]
        media_group = []
        for item in media_items:
            file_url = item['file_id']
            mime_type, _ = mimetypes.guess_type(file_url)
            processed_image = await convert_image_repost(file_url)
            if processed_image:
                caption = item.get('caption')
                parse_mode = item.get('parse_mode')
                if mime_type == "image/gif":
                    media_group.append(InputMediaDocument(media=processed_image, caption=caption, filename="animation.gif", parse_mode=parse_mode))
                else:
                    media_group.append(InputMediaPhoto(media=processed_image, caption=caption, parse_mode=parse_mode))

        # --- ОТПРАВКА И СОХРАНЕНИЕ ---
        sent_messages = [] # Список для всех отправленных сообщений

        # Сценарий 1: Музыка + 1 файл (отправляем отдельно чтобы прицепить кнопку)
        if is_music_post and len(media_group) == 1:
            item = media_group[0]
            msg = None
            if isinstance(item, InputMediaPhoto):
                msg = await bot.send_photo(
                    chat_id=chat_id,
                    photo=item.media,
                    caption=item.caption,
                    parse_mode=item.parse_mode,
                    reply_markup=music_reply_markup
                )
            else:
                 msg = await bot.send_animation(
                    chat_id=chat_id,
                    animation=item.media,
                    caption=item.caption,
                    parse_mode=item.parse_mode,
                    reply_markup=music_reply_markup
                )
            if msg:
                sent_messages.append(msg)

        # Сценарий 2: Группа файлов
        else:
            msgs_list = await bot.send_media_group(chat_id=chat_id, media=media_group)
            if msgs_list:
                sent_messages.extend(msgs_list)

            if is_music_post:
                await bot.send_message(
                    chat_id=chat_id,
                    text="🎧 Нажмите кнопку ниже, чтобы слушать музыку:",
                    reply_markup=music_reply_markup
                )

        # === ЦИКЛ СОХРАНЕНИЯ В ФОНЕ ===
        # 1. Определяем общие данные из первого сообщения (если они есть)
        main_caption = ""
        main_original_link = media_group_data.get('original_link')

        if sent_messages:
            if sent_messages[0].caption:
                main_caption = sent_messages[0].caption
            
            if not main_original_link and sent_messages[0].caption_entities:
                for entity in sent_messages[0].caption_entities:
                    if entity.type == 'text_link' and entity.url and 'telegra.ph' in entity.url:
                        main_original_link = entity.url
                        break

        # Формируем список задач
        queue_data = []
        for msg in sent_messages:
            if not msg.photo:
                continue

            new_post_id = msg.message_id
            best_photo = msg.photo[-1]
            new_file_id = best_photo.file_id
            
            post_caption = msg.caption if msg.caption else main_caption
            post_date = int(msg.date.timestamp())

            queue_data.append({
                'channel_id': str(chat_id),
                'message_id': new_post_id,
                'file_id': new_file_id,
                'caption': post_caption,
                'date_timestamp': post_date,
                'original_link': main_original_link
            })

        # Запускаем последовательную обработку
        if queue_data:
            asyncio.create_task(gpt_helper.process_background_queue(bot, queue_data))
        # ==============================


        logging.info(f"Пост {key} успешно опубликован в Telegram канал {chat_id}.")
        
        # Удаляем ключ time только после успешной публикации
        db.reference(f'users_publications/{user_id}/{key}/time').delete()
        logging.info(f"Ключ time для {key} удален.")

        # Уведомляем пользователя об успешной публикации
        await bot.send_message(
            chat_id=user_id,
            text="✅ Ваша отложенная публикация была успешно размещена в канале."
        )
    
    except Exception as e:
        logging.error(f"Ошибка при публикации поста {key} в Telegram: {e}")


async def handle_testid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text  # <-- это строка
    response_text = handle_testid_command_logic(message_text)  # переименовали, чтобы не пересекалось
    await update.message.reply_text(response_text)
def handle_testid_command_logic(message_text: str, user_id_to_manage: int = 6217936347) -> str:
    """
    Обрабатывает команду /testid для управления тестовыми конфигурациями в Firebase.

    Args:
        message_text (str): Полный текст сообщения от пользователя.
        user_id_to_manage (int): ID пользователя, который будет перемещаться между каналами Telegram.

    Returns:
        str: Текстовый ответ для отправки пользователю.
    """
    # Нормализация команды для удобства обработки
    command_parts = message_text.lower().strip().split()
    command = command_parts[1] if len(command_parts) > 1 else ""
    command = command.replace('_', '').replace('-', '')

    # --- КОНСТАНТЫ для удобства управления ---
    VK_OWNER_ID_PATH = f'users_publications/vk_keys/{user_id_to_manage}/owner_id'
    VK_TEST_ID = "198197516"
    VK_PROD_ID = "35194055"

    TG_PROD_CHANNEL = "-1001479526905"
    TG_TEST_CHANNEL = "-1002371033409"
    
    TG_PROD_USERS_PATH = f'users_publications/channels/{TG_PROD_CHANNEL}/user_ids'
    TG_TEST_USERS_PATH = f'users_publications/channels/{TG_TEST_CHANNEL}/user_ids'

    # --- ЛОГИКА КОМАНД ---

    def set_vk_test() -> str:
        """Переключает VK на тестовый ID."""
        try:
            ref = db.reference(VK_OWNER_ID_PATH)
            ref.set(VK_TEST_ID)
            return f"✅ VK ID успешно переключен на тестовый: {VK_TEST_ID}"
        except Exception as e:
            logging.error(f"Ошибка при смене VK ID на тестовый: {e}")
            return "❌ Не удалось изменить VK ID."

    def set_vk_return() -> str:
        """Возвращает VK на рабочий ID."""
        try:
            ref = db.reference(VK_OWNER_ID_PATH)
            ref.set(VK_PROD_ID)
            return f"✅ VK ID успешно возвращен на рабочий: {VK_PROD_ID}"
        except Exception as e:
            logging.error(f"Ошибка при возврате VK ID на рабочий: {e}")
            return "❌ Не удалось вернуть VK ID."

    def set_tg_test() -> str:
        """Перемещает пользователя в тестовый Telegram канал."""
        try:
            # Удаление из рабочего канала
            prod_ref = db.reference(TG_PROD_USERS_PATH)
            prod_users = prod_ref.get() or []
            if user_id_to_manage in prod_users:
                prod_users.remove(user_id_to_manage)
                prod_ref.set(prod_users)

            # Добавление в тестовый канал
            test_ref = db.reference(TG_TEST_USERS_PATH)
            test_users = test_ref.get() or []
            if user_id_to_manage not in test_users:
                test_users.append(user_id_to_manage)
                test_ref.set(test_users)
            
            return f"✅ Пользователь {user_id_to_manage} перенесен в тестовый TG канал."
        except Exception as e:
            logging.error(f"Ошибка при переносе в тестовый TG канал: {e}")
            return "❌ Не удалось перенести пользователя в тестовый TG канал."

    def set_tg_return() -> str:
        """Возвращает пользователя в рабочий Telegram канал."""
        try:
            # Удаление из тестового канала
            test_ref = db.reference(TG_TEST_USERS_PATH)
            test_users = test_ref.get() or []
            if user_id_to_manage in test_users:
                test_users.remove(user_id_to_manage)
                test_ref.set(test_users)

            # Добавление в рабочий канал
            prod_ref = db.reference(TG_PROD_USERS_PATH)
            prod_users = prod_ref.get() or []
            if user_id_to_manage not in prod_users:
                prod_users.append(user_id_to_manage)
                prod_ref.set(prod_users)
                
            return f"✅ Пользователь {user_id_to_manage} возвращен в рабочий TG канал."
        except Exception as e:
            logging.error(f"Ошибка при возврате в рабочий TG канал: {e}")
            return "❌ Не удалось вернуть пользователя в рабочий TG канал."

    # --- ОСНОВНОЙ ОБРАБОТЧИК ---
    
    # VK команды
    if command in ("вктест", "vktest"):
        return set_vk_test()
    
    if command in ("вквернуть", "vkvernut"):
        return set_vk_return()

    # TG команды
    if command in ("тгтест", "tgtest"):
        return set_tg_test()
        
    if command in ("тгвернуть", "tgvernut"):
        return set_tg_return()

    # Комбинированные команды
    if command in ("тест", "test"):
        vk_msg = set_vk_test()
        tg_msg = set_tg_test()
        return f"--- Общий тестовый режим ---\n{vk_msg}\n{tg_msg}"

    if command in ("сброс", "reset"):
        vk_msg = set_vk_return()
        tg_msg = set_tg_return()
        return f"--- Сброс к рабочим настройкам ---\n{vk_msg}\n{tg_msg}"

    # Инструкция
    if command == "":
        return (
            "⚙️ Инструкция по команде /testid:\n\n"
            "▶️ `/testid вктест` - переключить VK на тестовый ID.\n"
            "◀️ `/testid вквернуть` - вернуть VK на рабочий ID.\n\n"
            "▶️ `/testid тгтест` - перенести пользователя в тестовый TG канал.\n"
            "◀️ `/testid тгвернуть` - вернуть пользователя в рабочий TG канал.\n\n"
            "🚀 `/testid тест` - активировать тестовый режим для VK и TG.\n"
            "🔄 `/testid сброс` - вернуть все настройки к рабочим."
        )

    return "🤔 Неизвестная команда. Используйте `/testid` для получения инструкции."



async def publish_to_vk_scheduled(context: CallbackContext):
    """Публикует пост в ВКонтакте по расписанию (с логикой, аналогичной handle_vkpub_button)."""
    job_data = context.job.data
    user_id = job_data["user_id"]
    message_id = job_data["message_id"]
    key = f"{user_id}_{message_id}"

    logging.info(f"[VK SCHEDULE] Начало публикации для user_id={user_id}, message_id={message_id}")

    # --- Загружаем данные из Firebase ---
    media_group_storage = load_publications_from_firebase()
    user_publications = media_group_storage.get(str(user_id), {})
    media_group_data = user_publications.get(key)

    if not media_group_data:
        logging.error(f"[VK SCHEDULE] ❌ Данные для публикации {key} не найдены.")
        return

    media_items = media_group_data.get("media", [])
    if not media_items or not isinstance(media_items, list):
        logging.error(f"[VK SCHEDULE] ❌ Медиагруппа пуста или некорректна для {key}.")
        return

    image_urls = [item.get("file_id") for item in media_items if "file_id" in item]
    if not image_urls:
        logging.error(f"[VK SCHEDULE] ❌ Отсутствуют ссылки на изображения для {key}.")
        return

    # --- Получаем VK-ключи ---
    vk_keys_ref = db.reference(f"users_publications/vk_keys/{user_id}")
    vk_keys = vk_keys_ref.get()
    if not vk_keys:
        logging.warning(f"[VK SCHEDULE] ⚠️ Не найдены VK-ключи для пользователя {user_id}.")
        return

    token = vk_keys.get("token")
    owner_id = vk_keys.get("owner_id")
    if not token or not owner_id:
        logging.error(f"[VK SCHEDULE] ❌ Некорректные данные VK для {user_id}.")
        return

    # --- Авторизация VK ---
    vk_session = VkApi(token=token)
    vk = vk_session.get_api()

    # --- Подготовка подписи ---
    first_caption = media_items[0].get("caption", "")
    cleaned_caption = extract_text_before_first_link(first_caption)
    formatted_caption = format_caption_for_vk(first_caption)

    # --- Загрузка изображений ---
    uploaded_photos = []
    try:
        upload_url = vk.photos.getWallUploadServer(group_id=owner_id)["upload_url"]
        async with aiohttp.ClientSession() as session:
            for url in image_urls:
                photo = await upload_photo_to_vk(
                    vk, url, owner_id, formatted_caption, session, upload_url
                )
                uploaded_photos.append(f"photo{photo['owner_id']}_{photo['id']}")
                await asyncio.sleep(random.uniform(0.8, 1.9))  # пауза для стабильности
    except Exception as e:
        logging.error(f"[VK SCHEDULE] 🚫 Ошибка загрузки изображений для {key}: {e}")
        return

    # --- Публикация поста ---
    try:
        if int(owner_id) > 0:
            owner_id = -int(owner_id)

        vk.wall.post(
            owner_id=int(owner_id),
            from_group=1,
            message=html.unescape(cleaned_caption),
            attachments=",".join(uploaded_photos),
            random_id=get_random_id(),
            primary_attachments_mode="grid"
        )

        logging.info(f"[VK SCHEDULE] ✅ Пост {key} успешно опубликован в ВК.")

        # --- Удаляем ключ time после успешной публикации ---
        db.reference(f"users_publications/{user_id}/{key}/time").delete()
        logging.info(f"[VK SCHEDULE] ⏰ Ключ 'time' удалён для {key}.")

        # --- Отправляем уведомление пользователю ---
        bot = context.bot
        await bot.send_message(
            chat_id=user_id,
            text="✅ Ваша отложенная публикация была успешно размещена в ВКонтакте."
        )

    except Exception as e:
        logging.error(f"[VK SCHEDULE] 🚫 Ошибка публикации поста {key} в ВК: {e}")




# Новая асинхронная функция для получения краткого содержания поста
async def get_post_caption(post_key: str) -> str:
    """
    Асинхронно получает и обрабатывает заголовок поста по его ключу.
    Ключ имеет формат 'user_id_message_id'.
    """
    try:
        user_id, full_key = post_key.split('_')[0], post_key  # Используем весь post_key как вложенный ключ
    except ValueError:
        return "Неверный ключ"

    logging.info(f"user_id: {user_id}, full_key: {full_key}")
    
    # Загружаем все публикации
    media_group_storage = load_publications_from_firebase()

    
    # Ищем нужную публикацию
    post_data = media_group_storage.get(user_id, {}).get(full_key)

    
    if not post_data or 'media' not in post_data or not post_data['media']:
        return "Пост не найден"

    raw_caption = post_data['media'][0].get('caption', '')
    if not raw_caption:
        return "Без текста"

    # Используем BeautifulSoup для очистки от HTML
    soup = BeautifulSoup(raw_caption, 'html.parser')
    for a in soup.find_all('a'):
        a.replace_with(a.get_text())
    cleaned_caption = soup.get_text()

    # Логика определения финального текста
    caption = ""
    if "Модель: Imagen3" in cleaned_caption:
        match = re.search(r"Ваш запрос:\s*(.+)", cleaned_caption, re.DOTALL)
        if match:
            caption = match.group(1).strip().replace('\n', ' ')
    elif "автор: " in cleaned_caption.lower():
        match = re.search(r'автор:\s*([^•<\n]+)', cleaned_caption, re.IGNORECASE)
        if match:
            caption = match.group(1).strip()
    
    if not caption:
        caption = ' '.join(cleaned_caption.split()[:5])  # Берем первые 5 слов, если ничего не подошло

    # Обрезаем для краткости
    return (caption[:30] + '…') if len(caption) > 30 else caption

# --- Основная, обновленная функция ---


async def list_scheduled_jobs(update: Update, context: CallbackContext):
    """
    Показывает все активные задачи публикаций в виде клавиатуры.
    Отображает имя автора с платформой в скобках и сортирует по ближайшей дате.
    """
    jobs = context.job_queue.jobs()
    logging.info(f"jobs: {jobs}")    

    scheduled_posts = {}

    for job in jobs:
        if not job.name or not job.name.startswith(('tg_pub_', 'vk_pub_')):
            continue

        try:
            parts = job.name.split('_')
            platform = parts[0]
            author_id = parts[2]
            message_id = parts[3]
            post_key = f"{author_id}_{message_id}"
        except IndexError:
            logging.warning(f"Не удалось распарсить имя задачи: {job.name}")
            continue

        scheduled_time = job.next_t
        if not scheduled_time:
            continue

        if post_key not in scheduled_posts:
            scheduled_posts[post_key] = {
                'author_id': author_id,
                'platforms': set(),
                'scheduled_time': scheduled_time
            }
        else:
            scheduled_posts[post_key]['scheduled_time'] = min(
                scheduled_posts[post_key]['scheduled_time'], scheduled_time
            )

        scheduled_posts[post_key]['platforms'].add(platform)

    if not scheduled_posts:
        await update.message.reply_text("Сейчас нет запланированных публикаций.")
        return

    # Сортируем по дате
    sorted_posts = sorted(scheduled_posts.items(), key=lambda x: x[1]['scheduled_time'])

    keyboard = [
        [
            InlineKeyboardButton("👤 Автор (платформа)", callback_data="noop_header"),
            InlineKeyboardButton("📝 Пост", callback_data="noop_header"),
            InlineKeyboardButton("🕓 Время", callback_data="noop_header")
        ]
    ]

    for post_key, data in sorted_posts:
        author_id = data['author_id']
        scheduled_time = data['scheduled_time'].astimezone(pytz.timezone("Europe/Moscow"))  # или нужный вам часовой пояс

        time_str = scheduled_time.strftime('%d.%m, %H:%M')

        if author_id == '6217936347':
            author_name = "Артем"
        elif author_id == '419817885':
            author_name = "Нова"
        else:
            author_name = "Другой"

        platforms = sorted(data['platforms'])
        platform_str = ", ".join(platforms)

        # имя + платформа
        full_author = f"{author_name} ({platform_str})"

        post_caption = await get_post_caption(post_key)

        row = [
            InlineKeyboardButton(full_author, callback_data=f"otlview_{post_key}"),
            InlineKeyboardButton(post_caption, callback_data=f"otlview_{post_key}"),
            InlineKeyboardButton(time_str, callback_data=f"schedulepost_{post_key}")
        ]
        keyboard.append(row)
    # --- НОВОЕ: Добавляем кнопку для календаря ---
    keyboard.append([
        InlineKeyboardButton("📊 Посмотреть на шкале", callback_data="view_timeline")
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔧 Активные публикации:", reply_markup=reply_markup)


import logging
import json
import pytz
import io
import requests
from datetime import datetime, timedelta

# Matplotlib для генерации изображения
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
from textwrap import wrap
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
## ------------------- НОВЫЙ КОД ------------------- ##

async def _get_post_details(post_key: str, context: CallbackContext) -> dict:
    """
    Вспомогательная функция для получения деталей поста: подписи и первого изображения.
    """
    media_group_storage = load_publications_from_firebase()
    author_id, _ = post_key.split('_', 1)

    user_publications = media_group_storage.get(author_id, {})
    data = user_publications.get(post_key)

    if not data:
        return {'caption': 'Не найдено', 'image_data': None, 'author': 'Неизвестен'}

    if isinstance(data, str):
        data = json.loads(data)

    media = data.get('media', {})

    # если media — словарь, получаем значения
    if isinstance(media, dict):
        media_items = list(media.values())
    # если media — список, используем напрямую
    elif isinstance(media, list):
        media_items = media
    else:
        media_items = []

    if not media_items:
        return {'caption': 'Нет медиа', 'image_data': None, 'author': 'Неизвестен'}


    first_media = media_items[0]
    caption = first_media.get('caption', 'Без подписи')
    file_id = first_media.get('file_id')

    # Определяем имя автора
    if author_id == '6217936347':
        author_name = "Артем"
    elif author_id == '419817885':
        author_name = "Нова"
    else:
        author_name = "Другой"

    image_data = None
    if file_id:
        try:
            if file_id.startswith('http'):
                response = requests.get(file_id, stream=True)
                response.raise_for_status()
                image_data = response.raw
            else:
                # Скачиваем файл из Telegram
                tg_file = await context.bot.get_file(file_id)
                file_bytes = await tg_file.download_as_bytearray()
                image_data = io.BytesIO(file_bytes)
        except Exception as e:
            logging.error(f"Ошибка загрузки изображения для timeline {file_id}: {e}")
            # Можно подставить картинку-заглушку
            image_data = None

    return {'caption': caption, 'image_data': image_data, 'author': author_name}


def preprocess_caption(text: str) -> str:
    """
    Заменяет /n на символ новой строки и удаляет HTML-теги.
    """
    # Заменяем /n на \n
    processed_text = text.replace('/n', '\n')
    # Удаляем все HTML-теги
    clean_text = re.sub(r'<[^>]+>', '', processed_text)
    return clean_text

import io
import gc
import pytz
import logging
import asyncio
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from textwrap import wrap
from PIL import Image

async def generate_timeline_image(context, posts_data: list) -> io.BytesIO:
    """
    Генерирует изображение временной шкалы постов с помощью Matplotlib.
    Оптимизировано для снижения использования оперативной памяти.
    """
    num_posts = len(posts_data)
    fig_height = max(6, 4 * num_posts)

    # Создание холста
    fig, ax = plt.subplots(figsize=(12, fig_height), constrained_layout=False)
    fig.patch.set_facecolor('#f0f0f0')
    ax.set_facecolor('#ffffff')

    # Скрываем оси и рамки
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.get_xaxis().set_ticks([])
    ax.get_yaxis().set_ticks([])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, num_posts * 10 + 3)

    # Заголовок
    ax.text(5, num_posts * 10 + 2, 'План публикаций на 30 дней',
            ha='center', va='center', fontsize=24, fontweight='bold', color='#333333')

    # Основной цикл
    for i, (post_key, data) in enumerate(posts_data):
        details = await _get_post_details(post_key, context)
        scheduled_time = data['scheduled_time'].astimezone(pytz.timezone("Europe/Moscow"))
        y_base = (num_posts - i - 1) * 10

        # Тень и фон блока
        shadow = patches.Rectangle((0.55, y_base + 0.45), 9, 9,
                                   linewidth=0, facecolor='#cccccc', zorder=0)
        rect = patches.Rectangle((0.5, y_base + 0.5), 9, 9,
                                 linewidth=1, edgecolor='none', facecolor='#ffffff', zorder=1)
        ax.add_patch(shadow)
        ax.add_patch(rect)

        # Отображение изображения поста
        if details.get('image_data'):
            try:
                img = Image.open(details['image_data'])
                img.thumbnail((400, 400))  # уменьшаем в 4–10 раз без потери качества
                img_array = np.asarray(img)
                img.close()
                del img

                # Вычисляем параметры расположения
                box_x, box_y = 1, y_base + 1
                box_w, box_h = 3.5, 7.5
                box_aspect = box_w / box_h
                img_h, img_w = img_array.shape[:2]
                img_aspect = img_w / img_h

                if img_aspect > box_aspect:
                    new_w, new_h = box_w, box_w / img_aspect
                    new_x, new_y = box_x, box_y + (box_h - new_h) / 2
                else:
                    new_h, new_w = box_h, box_h * img_aspect
                    new_y, new_x = box_y, box_x + (box_w - new_w) / 2

                zoom_factor = box_h / img_h * 2000 / fig.dpi
                imagebox = OffsetImage(img_array, zoom=zoom_factor)
                ab = AnnotationBbox(imagebox, (box_x + box_w/2, box_y + box_h/2),
                                    frameon=False, zorder=2)
                ax.add_artist(ab)
                del img_array

            except Exception as e:
                logging.error(f"Не удалось отрисовать изображение: {e}")
                ax.text(2.75, y_base + 4.75, "Ошибка\nзагрузки\nизображения",
                        ha='center', va='center', fontsize=12, color='red', zorder=2)

        # Текстовые элементы
        text_x_pos = 5.0
        date_str = scheduled_time.strftime('%d %B, %Y')
        time_str = scheduled_time.strftime('%H:%M')

        ax.text(text_x_pos, y_base + 8.5, f"☆ {date_str}  -  ☆ {time_str}",
                ha='left', va='center', fontsize=16, fontweight='bold', color='#005a9c', zorder=3)
        ax.text(text_x_pos, y_base + 7.8, f"☆ Автор: {details.get('author', '—')}",
                ha='left', va='center', fontsize=14, color='#555555', zorder=3)

        caption_text = details.get('caption', '')
        clean_caption = preprocess_caption(caption_text)
        wrapped_text = '\n'.join(wrap(clean_caption, width=45, replace_whitespace=False, break_long_words=False))

        ax.text(text_x_pos, y_base + 6.5, wrapped_text,
                ha='left', va='top', fontsize=12, color='#333333', zorder=3, wrap=True)

        # микропаузa для избежания пиков памяти
        await asyncio.sleep(0)

    # Сохранение в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=72)
    buf.seek(0)

    # Очистка памяти
    ax.clear()
    plt.close(fig)
    gc.collect()

    return buf


async def show_timeline(update: Update, context: CallbackContext) -> None:
    """
    Обработчик нажатия на кнопку "Посмотреть на шкале".
    """
    query = update.callback_query
    await query.answer()

    # Отправляем временное сообщение и сохраняем его
    loading_msg = await query.message.reply_text("⏳ Генерирую шкалу, это может занять несколько секунд...")

    jobs = context.job_queue.jobs()
    moscow_tz = pytz.timezone("Europe/Moscow")
    now = datetime.now(moscow_tz)
    limit_date = now + timedelta(days=30)

    scheduled_posts = {}
    for job in jobs:
        if not job.name or not job.name.startswith(('tg_pub_', 'vk_pub_')):
            continue
        if not job.next_t or job.next_t.astimezone(moscow_tz) > limit_date:
            continue
        try:
            parts = job.name.split('_')
            platform = parts[0]
            author_id = parts[2]
            message_id = parts[3]
            post_key = f"{author_id}_{message_id}"
            if post_key not in scheduled_posts:
                scheduled_posts[post_key] = {'platforms': set(), 'scheduled_time': job.next_t}
            scheduled_posts[post_key]['platforms'].add(platform)
        except IndexError:
            continue

    if not scheduled_posts:
        await loading_msg.edit_text("Нет запланированных публикаций на ближайшие 30 дней.")
        return

    # Сортировка по времени
    sorted_posts = sorted(scheduled_posts.items(), key=lambda x: x[1]['scheduled_time'])

    # Разбиваем на чанки по 6 постов
    chunk_size = 6
    post_chunks = [sorted_posts[i:i + chunk_size] for i in range(0, len(sorted_posts), chunk_size)]

    try:
        # Генерируем и отправляем изображения по мере готовности
        for idx, chunk in enumerate(post_chunks):
            image_buffer = await generate_timeline_image(context, chunk)

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Закрыть окно", callback_data="ozondelete_msg")]
            ])

            caption = f"Вот ваш план публикаций (часть {idx + 1}/{len(post_chunks)})."

            if idx == 0:
                # Первое изображение заменяет сообщение "Генерирую…"
                await context.bot.edit_message_media(
                    media=InputMediaPhoto(media=image_buffer, caption=caption),
                    chat_id=loading_msg.chat_id,
                    message_id=loading_msg.message_id,
                    reply_markup=keyboard
                )
            else:
                # Остальные отправляются новыми сообщениями
                await context.bot.send_photo(
                    chat_id=loading_msg.chat_id,
                    photo=image_buffer,
                    caption=caption,
                    reply_markup=keyboard
                )

    except Exception as e:
        logging.error(f"Ошибка при генерации шкалы: {e}", exc_info=True)
        await loading_msg.edit_text(f"❌ Произошла ошибка при создании шкалы: {e}")



async def send_otl_post_buttons(query, key, data):
    """Отправляет сообщение с кнопками управления публикацией."""
    await query.message.reply_text(
        text=f"Папка: {data.get('scheduled', 'Не указана')}\n\nКоличество медиа в посте: {len(data.get('media', []))}\n\nПри нажатии кнопки \"Редактировать пост\" вы можете отсортировать или удалить изображения, а так же поменять подпись. ",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🗓️ Изменить время 🗓️", callback_data=f"schedulepost_{key}")
            ],             
            [
                InlineKeyboardButton("📝 Редактировать пост 📝", callback_data=f"editpost_{key}")
            ],                
            [
                InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')
            ],  
            [
                InlineKeyboardButton("❌ Удалить пост❌", callback_data=f"yrrasetag_{key}")  
            ],                      
        ])
    )




async def handle_otloj_scheduled(update: Update, context: CallbackContext) -> None:
    """
    Обрабатывает просмотр запланированной публикации.
    Извлекает ID пользователя из ключа callback'а для получения нужных данных.
    """
    query = update.callback_query
    await query.answer()
    
    MAX_CAPTION_LENGTH = 1024

    # 1. Разделяем callback_data, чтобы получить ключ (key)
    if '_' in query.data:
        _, key = query.data.split('_', 1)
    else:
        await query.message.reply_text("🚫 Ошибка: Некорректный формат данных.")
        return

    # 2. ИЗМЕНЕНИЕ: Извлекаем ID пользователя из самого ключа
    # Ключ имеет формат "user_id_post_id", например "419817885_26678"
    try:
        current_user_id = key.split('_')[0]
    except IndexError:
        await query.message.reply_text("🚫 Ошибка: Некорректный формат ключа.")
        return

    global media_group_storage
    # Загружаем данные из хранилища (например, Firebase)
    media_group_storage = load_publications_from_firebase()

    # 3. Проверяем, что публикации для этого пользователя существуют
    if current_user_id in media_group_storage:
        user_publications = media_group_storage[current_user_id]
        
        # 4. Используем ПОЛНЫЙ ключ для получения конкретной публикации
        data = user_publications.get(key)
        
        if data:
            try:
                # Если данные - это строка JSON, преобразуем в словарь
                if isinstance(data, str):
                    data = json.loads(data)

                if isinstance(data, dict) and 'media' in data:
                    media = data['media']
                    media_group = []
                    captions_only = []

                    # Определяем, является ли media списком или словарем
                    media_items = media if isinstance(media, list) else media.values()

                    for media_data in media_items:
                        if 'file_id' not in media_data:
                            continue

                        file_id = media_data['file_id']
                        caption = media_data.get('caption', '')
                        parse_mode = media_data.get('parse_mode', None)

                        # Если подпись слишком длинная, она будет отправлена отдельно
                        caption_to_send = caption if len(caption) <= MAX_CAPTION_LENGTH else ''

                        file_id_lower = file_id.lower()
                        
                        # Обработка GIF/MP4
                        if file_id_lower.endswith(('.gif', '.mp4')):
                            try:
                                await query.message.reply_text("Видео/GIF обрабатывается, ожидайте...")
                                processed_media, _ = await process_image(file_id)
                                if not processed_media:
                                    raise Exception("Не удалось обработать медиафайл.")
                                
                                await query.message.reply_animation(
                                    animation=processed_media,
                                    caption=caption,
                                    parse_mode=parse_mode
                                )
                            except Exception as e:
                                # logger.error(f"Ошибка при отправке gif/mp4: {e}")
                                await query.message.reply_text(f"🚫 Ошибка при отправке анимации: {e}")

                        # Обработка изображений
                        elif file_id_lower.endswith(('.jpg', '.jpeg', '.png')) or not file_id.startswith("http"):
                            media_group.append(
                                InputMediaPhoto(
                                    media=file_id,
                                    caption=caption_to_send,
                                    parse_mode=parse_mode
                                )
                            )
                        # Обработка остальных типов как документов
                        else:
                            media_group.append(
                                InputMediaDocument(
                                    media=file_id,
                                    caption=caption_to_send,
                                    parse_mode=parse_mode
                                )
                            )
                        
                        # Отправка длинных подписей отдельным сообщением
                        if len(caption) > MAX_CAPTION_LENGTH:
                            await query.message.reply_text(
                                text=caption,
                                parse_mode=parse_mode
                            )

                    # Отправка медиа-группы, если она была сформирована
                    if media_group:
                        await context.bot.send_media_group(
                            chat_id=query.message.chat_id,
                            media=media_group
                        )

                    # Отправка информации о записи с кнопками управления
                    await send_otl_post_buttons(query, key, data)

                else:
                    await query.message.reply_text("🚫 Ошибка: Некорректный формат данных в записи.")
            except json.JSONDecodeError as e:
                await query.message.reply_text(f"🚫 Ошибка чтения данных: {e}")
        else:
            await query.message.reply_text("🚫 Запись не найдена.")
    else:
        await query.message.reply_text("🚫 Публикации для данного пользователя не найдены.")





async def reschedule_publications_on_startup(context: CallbackContext):
    """
    Сканирует все публикации при запуске бота и восстанавливает
    запланированные задачи. Если время прошло менее недели назад —
    переносятся на сегодня/завтра в то же время. Иначе — на следующий год.
    """
    logging.info("Запуск восстановления отложенных публикаций при старте...")
    moscow_tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(moscow_tz)

    publications = load_publications_from_firebase()

    for user_id, user_pubs in publications.items():
        if user_id in ['channels', 'vk_keys']:
            continue

        for message_id_key, pub_data in user_pubs.items():
            if isinstance(pub_data, dict) and 'time' in pub_data and pub_data['time']:
                time_str = pub_data['time']
                try:
                    pub_dt_naive = datetime.strptime(time_str, "%d.%m, %H:%M")
                    pub_dt_with_year = pub_dt_naive.replace(year=now.year)
                    pub_dt_aware = moscow_tz.localize(pub_dt_with_year)
                    time_diff = now - pub_dt_aware

                    if pub_dt_aware < now:
                        if time_diff <= timedelta(weeks=1):
                            today_pub_dt = now.replace(hour=pub_dt_aware.hour,
                                                       minute=pub_dt_aware.minute,
                                                       second=0, microsecond=0)
                            if today_pub_dt > now:
                                pub_dt_aware = today_pub_dt
                            else:
                                pub_dt_aware = today_pub_dt + timedelta(days=1)

                            try:
                                user_id_int = int(user_id)
                                await context.bot.send_message(
                                    chat_id=user_id_int,
                                    text=(
                                        f"Публикация '{message_id_key}' была просрочена из-за ошибки бота или сервера, "
                                        f"поэтому она будет выполнена {pub_dt_aware.strftime('%d.%m в %H:%M')}."
                                    )
                                )
                            except Exception as notify_err:
                                logging.warning(f"Не удалось уведомить пользователя {user_id}: {notify_err}")
                        else:
                            pub_dt_with_year = pub_dt_with_year.replace(year=now.year + 1)
                            pub_dt_aware = moscow_tz.localize(pub_dt_with_year)

                    user_id_int = int(user_id)
                    message_id_int = int(message_id_key.split('_')[-1])

                    # Получаем платформы
                    only_tg = pub_data.get('onlytg') is True
                    only_vk = pub_data.get('onlyvk') is True

                    # Планируем публикацию
                    schedule_publication_job(
                        job_queue=context.job_queue,
                        user_id=user_id_int,
                        message_id=message_id_int,
                        key=message_id_key,
                        pub_dt_aware=pub_dt_aware,
                        only_tg=only_tg,
                        only_vk=only_vk
                    )

                except Exception as e:
                    logging.error(
                        f"Ошибка при обработке времени '{time_str}' для {message_id_key}: {e}"
                    )

    logging.info("Восстановление отложенных публикаций завершено.")

def schedule_publication_job(
    job_queue: JobQueue,
    user_id: int,
    message_id: int,
    key: str,
    pub_dt_aware: datetime,
    only_tg: bool = False,
    only_vk: bool = False
):
    """
    Планирует задачи публикации в TG и VK.
    Если задача с таким именем уже есть — удаляет её и создаёт заново.
    Если передан only_tg или only_vk, противоположная задача также удаляется.
    """
    job_data = {'user_id': user_id, 'message_id': message_id, 'key': key}
    logging.info(f"only_tg {only_tg}")
    logging.info(f"only_vk {only_vk}")

    tg_job_name = f"tg_pub_{key}"
    vk_job_name = f"vk_pub_{key}"

    # === Удаление TG задачи, если only_vk ===
    if only_vk:
        existing_tg_jobs = job_queue.get_jobs_by_name(tg_job_name)
        for job in existing_tg_jobs:
            job.schedule_removal()
            logging.info(f"Удалена TG задача {tg_job_name}, так как only_vk=True")

    # === Удаление VK задачи, если only_tg ===
    if only_tg:
        existing_vk_jobs = job_queue.get_jobs_by_name(vk_job_name)
        for job in existing_vk_jobs:
            job.schedule_removal()
            logging.info(f"Удалена VK задача {vk_job_name}, так как only_tg=True")

    # === Создание TG задачи ===
    if not only_vk:
        existing_tg_jobs = job_queue.get_jobs_by_name(tg_job_name)
        for job in existing_tg_jobs:
            job.schedule_removal()
            logging.info(f"Старая TG задача {tg_job_name} удалена.")
        job_queue.run_once(publish_to_telegram_scheduled, when=pub_dt_aware, data=job_data, name=tg_job_name)
        logging.info(f"Запланирована TG публикация {tg_job_name} на {pub_dt_aware}")

    # === Создание VK задачи ===
    if not only_tg:
        existing_vk_jobs = job_queue.get_jobs_by_name(vk_job_name)
        for job in existing_vk_jobs:
            job.schedule_removal()
            logging.info(f"Старая VK задача {vk_job_name} удалена.")
        job_queue.run_once(publish_to_vk_scheduled, when=pub_dt_aware, data=job_data, name=vk_job_name)
        logging.info(f"Запланирована VK публикация {vk_job_name} на {pub_dt_aware}")



async def handle_publish_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    temp_message = await query.message.reply_text("📤 Пост переносится, ожидайте...")
    
    _, user_id_str, message_id_str = query.data.split('_')
    user_id = int(user_id_str)
    message_id = int(message_id_str)
    
    global media_group_storage
    media_group_storage = load_publications_from_firebase()

    user_data = media_group_storage.get(str(user_id))
    if not user_data:
        await temp_message.edit_text("🚫 Ошибка: Пользовательские данные не найдены.")
        return

    key = f"{user_id}_{message_id}"
    media_group_data = user_data.get(key)

    if media_group_data:
        try:
            if isinstance(media_group_data, str):
                media_group_data = json.loads(media_group_data)

            media_items = media_group_data.get('media')
            if not media_items or not isinstance(media_items, list):
                await temp_message.edit_text("🚫 Ошибка: Некорректный формат данных.")
                return
            
            # --- НОВАЯ ЛОГИКА: Проверка на музыкальный пост ---
            is_music_post = media_group_data.get('music_post', False)
            music_reply_markup = None
            
            if is_music_post:
                web_app_url = f"https://anemonne.onrender.com/musicplayer/{user_id}/{key}"

                music_name = "Музыка"
                musicmedia = media_group_data.get('musicmedia', [])

                if musicmedia and isinstance(musicmedia, list):
                    raw_name = musicmedia[0].get('music_name')
                    if raw_name:
                        # убираем расширение файла
                        music_name = raw_name.rsplit('.', 1)[0]
                        # обрезаем до 20 символов
                        if len(music_name) > 19:
                            cut = music_name[:19].rsplit(' ', 1)[0]
                            music_name = cut + "..."

                button_text = f"◄⠀▐▐ ⠀►  |  {music_name}"

                music_reply_markup = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            text=button_text,
                            url=web_app_url
                        )
                    ]
                ])
            # --------------------------------------------------

        except json.JSONDecodeError as e:
            await temp_message.edit_text(f"🚫 Ошибка преобразования данных: {e}")
            return

        channel_ref = db.reference('users_publications/channels')
        channels_data = channel_ref.get() or {}

        user_channels = [
            chat_id for chat_id, info in channels_data.items()
            if user_id in info.get('user_ids', [])
        ]

        if not user_channels:
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("‼️Перезапуск бота‼️", callback_data='restart')]]
            )
            await temp_message.edit_text(
                "Сейчас у вас нет привязанных каналов...", 
                reply_markup=keyboard
            )
            if user_id not in waiting_for_forward:
                waiting_for_forward[user_id] = True
            return

        chat_id = user_channels[0]
        media_group = []
        
        # Сбор медиа
        for item in media_items:
            file_url = item['file_id']
            mime_type, _ = mimetypes.guess_type(file_url)
            processed_image = await convert_image_repost(file_url)

            if processed_image is not None:
                caption = item.get('caption')
                parse_mode = item.get('parse_mode')

                if mime_type == "image/gif":
                    media_group.append(
                        InputMediaDocument(
                            media=processed_image,
                            caption=caption,
                            filename="animation.gif",
                            parse_mode=parse_mode
                        )
                    )
                else:
                    media_group.append(
                        InputMediaPhoto(
                            media=processed_image,
                            caption=caption,
                            parse_mode=parse_mode
                        )
                    )
            else:
                await temp_message.edit_text(f"🚫 Ошибка при обработке файла: {file_url}")
                return

        # --- ОБНОВЛЕННАЯ ЛОГИКА ПУБЛИКАЦИИ И СОХРАНЕНИЯ ---
        try:
            sent_messages = [] # Список для сбора всех отправленных сообщений

            # Сценарий 1: Музыкальный пост и ВСЕГО ОДИН файл.
            # Отправляем через send_photo/send_animation, чтобы прикрепить кнопку к посту.
            if is_music_post and len(media_group) == 1:
                item = media_group[0]
                msg = None
                if isinstance(item, InputMediaPhoto):
                    msg = await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=item.media,
                        caption=item.caption,
                        parse_mode=item.parse_mode,
                        reply_markup=music_reply_markup
                    )
                else:
                    msg = await context.bot.send_animation(
                        chat_id=chat_id,
                        animation=item.media,
                        caption=item.caption,
                        parse_mode=item.parse_mode,
                        reply_markup=music_reply_markup
                    )
                if msg:
                    sent_messages.append(msg)

            # Сценарий 2: Обычный пост или Музыкальный пост с НЕСКОЛЬКИМИ файлами
            else:
                # send_media_group возвращает список сообщений
                msgs_list = await context.bot.send_media_group(
                    chat_id=chat_id,
                    media=media_group
                )
                if msgs_list:
                    sent_messages.extend(msgs_list) # Добавляем все сообщения альбома
                    
                if is_music_post:
                     await context.bot.send_message(
                        chat_id=chat_id,
                        text="🎧 Нажмите кнопку ниже, чтобы слушать музыку:",
                        reply_markup=music_reply_markup
                    )

            # === ИНТЕГРАЦИЯ С БАЗОЙ ДАННЫХ (ЦИКЛ ПО ВСЕМ ФОТО) ===
            # 1. Определяем общие данные (Подпись и Ссылку)
            # В handle_publish_button у нас может не быть media_group_data['original_link'] явно,
            # поэтому надежнее парсить первое отправленное сообщение.
            
            main_caption = ""
            main_original_link = None
            if isinstance(media_group_data, dict):
                 main_original_link = media_group_data.get('original_link')

            if sent_messages:
                if sent_messages[0].caption:
                    main_caption = sent_messages[0].caption
                
                if not main_original_link and sent_messages[0].caption_entities:
                    for entity in sent_messages[0].caption_entities:
                        if entity.type == 'text_link' and entity.url and 'telegra.ph' in entity.url:
                            main_original_link = entity.url
                            break
            
            # 2. Формируем очередь задач
            queue_data = []
            for msg in sent_messages:
                if msg.photo:
                    new_post_id = msg.message_id
                    best_photo = msg.photo[-1]
                    new_file_id = best_photo.file_id
                    
                    post_caption = msg.caption if msg.caption else main_caption
                    post_date = int(msg.date.timestamp())

                    # Собираем данные в словарь, но НЕ запускаем задачу
                    queue_data.append({
                        'channel_id': str(chat_id),
                        'message_id': new_post_id,
                        'file_id': new_file_id,
                        'caption': post_caption,
                        'date_timestamp': post_date,
                        'original_link': main_original_link
                    })
            
            # 3. Запускаем ОДНУ фоновую задачу для всей очереди
            if queue_data:
                asyncio.create_task(gpt_helper.process_background_queue(context.bot, queue_data))
            # ==================================================



            await temp_message.edit_text(f"✅ Пост успешно опубликован в канале {chat_id}!")
            
        except Forbidden as e:
            if "bot is not a member of the channel chat" in str(e):
                await temp_message.edit_text(
                    "🚫 Для возможности публиковать посты добавьте бота в канал."
                )
            else:
                await temp_message.edit_text(f"🚫 Ошибка доступа: {e}")
        except Exception as e:
            await temp_message.edit_text(f"🚫 Ошибка при публикации поста: {e}")
    else:
        await temp_message.edit_text("🚫 Ошибка: Данные о медиагруппе не найдены.")


async def handle_share_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()  # Ответ пользователю, что нажатие обработано

    # Извлекаем user_id и message_id из callback_data
    _, user_id_str, message_id_str = query.data.split('_')
    user_id = int(user_id_str)
    message_id = int(message_id_str)
    global media_group_storage
    # Загружаем данные из Firebase
    media_group_storage = load_publications_from_firebase()

    # Проверяем, есть ли записи для указанного user_id
    user_data = media_group_storage.get(str(user_id))
    if not user_data:
        await query.message.reply_text("🚫 Ошибка: Пользовательские данные не найдены.")
        return

    # Проверяем наличие конкретной записи
    key = f"{user_id}_{message_id}"
    media_group_data = user_data.get(key)

    if media_group_data:
        try:
            # Если данные - это строка, преобразуем в словарь
            if isinstance(media_group_data, str):
                media_group_data = json.loads(media_group_data)

            # Извлекаем список медиа
            media_items = media_group_data.get('media')
            if not media_items or not isinstance(media_items, list):
                await query.message.reply_text("🚫 Ошибка: Некорректный формат данных.")
                return
        except json.JSONDecodeError as e:
            await query.message.reply_text(f"🚫 Ошибка преобразования данных: {e}")
            return

        # Создаём медиагруппу для отправки в группу
        media_group = []
        for item in media_items:
            file_url = item['file_id']

            # Определяем MIME-тип файла по URL
            mime_type, _ = mimetypes.guess_type(file_url)

            # Обрабатываем файл через convert_image_repost
            processed_image = await convert_image_repost(file_url)

            if processed_image is not None:
                caption = item.get('caption')  # None, если 'caption' отсутствует
                parse_mode = item.get('parse_mode')  # None, если 'parse_mode' отсутствует

                if mime_type == "image/gif":  # Если это GIF
                    media_group.append(
                        InputMediaDocument(
                            media=processed_image,  # Используем обработанный GIF
                            caption=caption,
                            filename="animation.gif",
                            parse_mode=parse_mode
                        )
                    )
                else:  # Любое другое изображение
                    media_group.append(
                        InputMediaPhoto(
                            media=processed_image,  # Используем обработанное изображение
                            caption=caption,
                            parse_mode=parse_mode
                        )
                    )
            else:
                await query.message.reply_text(f"🚫 Ошибка при обработке файла: {file_url}")
                return

        # Отправляем сообщение, кто предложил пост
        user_name = query.from_user.username or "Неизвестный пользователь"
        first_name = query.from_user.first_name or "Без имени"
        proposed_message = f"Пост предложен пользователем {first_name} (@{user_name})"

        try:
            # Отправляем информацию о пользователе в канал
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=proposed_message
            )

            # Публикуем медиагруппу в заранее заданной группе
            await context.bot.send_media_group(
                chat_id=GROUP_CHAT_ID,  # Заранее заданная группа
                media=media_group
            )
            await query.message.reply_text("✅ Пост успешно предложен в Анемон!")
        except Exception as e:
            await query.message.reply_text(f"🚫 Ошибка при публикации поста: {e}")
    else:
        await query.message.reply_text("🚫 Ошибка: Данные о медиагруппе не найдены.")


from datetime import datetime













async def swap_images(update: Update, context: CallbackContext) -> None:
    """Начинаем процесс замены изображений."""
    query = update.callback_query
    await query.answer()

    if query and '_' in query.data:
        _, key = query.data.split('_', maxsplit=1)
    else:
        await query.message.reply_text("🛑 Неверный формат данных.")
        return

    global media_group_storage
    # Загружаем данные из файла
    media_group_storage = load_publications_from_firebase()


    # Разбиваем ключ на user_id и user_message
    user_id, user_message = key.split('_', maxsplit=1)

    # Проверяем наличие user_id
    if user_id in media_group_storage:
        user_publications = media_group_storage[user_id]
        # Проверяем наличие записи под user_message
        if key in user_publications:
            media_group = user_publications[key]

            # Проверяем, является ли media_group словарём с ключом 'media'
            if isinstance(media_group, dict) and 'media' in media_group:
                media = media_group['media']
            else:
                await query.message.reply_text("🛑 Некорректный формат данных.")
                return

            if len(media) < 2:
                await query.message.reply_text("🛑 Недостаточно изображений для замены.")
                return

            # Создаём кнопки для выбора первого изображения
            keyboard = [
                [InlineKeyboardButton(f"Изображение {i+1}", callback_data=f"swap_first_{key}_{i}")]
                for i in range(len(media))
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text("Выберите первое изображение для замены:", reply_markup=reply_markup)
        else:
            await query.message.reply_text("🛑 Запись не найдена.")
    else:
        await query.message.reply_text("🛑 Пользователь не найден.")


async def select_first_image(update: Update, context: CallbackContext) -> None:
    """Обрабатываем выбор первого изображения."""
    query = update.callback_query
    await query.answer()

    if query and query.data.startswith("swap_first_"):
        data_parts = query.data.split('_')
        # Собираем ключ пользователя и сообщение
        user_id = data_parts[2]
        user_message = "_".join(data_parts[3:-1])
        first_index = int(data_parts[-1])
        context.user_data['swap_key'] = f"{user_id}_{user_message}"
        context.user_data['first_index'] = first_index
    else:
        await query.message.reply_text("🛑 Неверный формат данных.")
        return

    key = context.user_data['swap_key']

    global media_group_storage
    # Загружаем данные из Firebase
    media_group_storage = load_publications_from_firebase()

    # Проверяем наличие user_id в media_group_storage
    if user_id in media_group_storage:
        user_publications = media_group_storage[user_id]
        # Проверяем наличие записи по ключу
        if key in user_publications:
            media_group = user_publications[key]
            # Проверяем, является ли media_group словарём с ключом 'media'
            media = media_group.get("media") if isinstance(media_group, dict) else None
        else:
            await query.message.reply_text("🛑 Запись не найдена.")
            return
    else:
        await query.message.reply_text("🛑 Пользователь не найден.")
        return

    if not media or len(media) < 2:
        await query.message.reply_text("🛑 Недостаточно изображений для замены.")
        return

    # Создаём кнопки для выбора второго изображения (исключая уже выбранное)
    keyboard = [
        [InlineKeyboardButton(f"Изображение {i+1}", callback_data=f"swap_second_{key}_{i}")]
        for i in range(len(media))
        if i != context.user_data['first_index']
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Обновляем сообщение вместо отправки нового
    await query.edit_message_text("Выберите второе изображение для замены:", reply_markup=reply_markup)





async def select_second_image(update: Update, context: CallbackContext) -> None:
    """Обрабатываем выбор второго изображения и выполняем замену."""
    query = update.callback_query
    await query.answer()

    if query and query.data.startswith("swap_second_"):
        # Разделяем данные
        data_parts = query.data.split('_')
        user_id = data_parts[2]
        user_message = "_".join(data_parts[3:-1])
        second_index = int(data_parts[-1])
        first_index = context.user_data.get('first_index')

        if first_index is None:
            await query.message.reply_text("🛑 Сначала выберите первое изображение.")
            return

        # Формируем ключ
        key = f"{user_id}_{user_message}"
    else:
        await query.message.reply_text("🛑 Неверный формат данных.")
        return

    # Логируем ключ и индексы

    global media_group_storage
    # Загружаем данные из Firebase
    media_group_storage = load_publications_from_firebase()

    # Проверяем наличие user_id в media_group_storage
    if user_id in media_group_storage:
        user_publications = media_group_storage[user_id]
        # Проверяем наличие записи по ключу
        if key in user_publications:
            media_group = user_publications[key]
            # Проверяем, является ли media_group словарём с ключом 'media'
            media = media_group.get("media") if isinstance(media_group, dict) else None
        else:
            await query.message.reply_text("🛑 Запись не найдена.")
            return
    else:
        await query.message.reply_text("🛑 Пользователь не найден в хранилище.")
        return

    # Проверка структуры данных
    if not media or not isinstance(media, list) or len(media) < 2:
        await query.message.reply_text("🛑 Недостаточно изображений для замены.")
        return

    # Проверяем индексы
    if first_index >= len(media) or second_index >= len(media):
        await query.message.reply_text("🛑 Ошибка индексов.")
        return


    # Сохраняем начальные значения caption и parse_mode первого изображения
    first_caption = media[0].get('caption')
    first_parse_mode = media[0].get('parse_mode')

    # Меняем изображения местами
    media[first_index], media[second_index] = media[second_index], media[first_index]

    # Восстанавливаем caption и parse_mode для первого изображения
    media[0]['caption'] = first_caption
    media[0]['parse_mode'] = first_parse_mode

    # Убираем caption и parse_mode у остальных изображений
    for item in media[1:]:
        item['caption'] = None
        item['parse_mode'] = None

    # Сохраняем изменения обратно в хранилище
    user_publications[key]['media'] = media
    save_media_group_data(media_group_storage, user_id)

    # Формируем медиагруппу для отображения
    media_group_preview = []
    for media_data in media:
        if 'file_id' in media_data:
            media_group_preview.append(
                InputMediaPhoto(
                    media=media_data['file_id'],
                    caption=media_data.get('caption', ''),
                    parse_mode=media_data.get('parse_mode', None)
                )
            )
    await query.message.delete()
    # Отправляем медиагруппу
    if media_group_preview:
        await context.bot.send_media_group(
            chat_id=query.message.chat_id,
            media=media_group_preview
        )

    # Отправляем информацию о записи с кнопками
    await query.message.reply_text(
        text="✅ Изображения успешно заменены и пост обновлен.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("В ТГ", callback_data=f"publish_{key}"),
                InlineKeyboardButton("В ВК", callback_data=f"vkpub_{key}"),
                InlineKeyboardButton("В X.com", callback_data=f"twitterpub_{key}"),
                InlineKeyboardButton("Удалить", callback_data=f"yrrasetag_{key}"),  
            ],
            [
                InlineKeyboardButton("🌠 Предложить этот пост в Анемон 🌠", callback_data=f"share_{key}")
            ],            
            [
                InlineKeyboardButton("🔄 Случайно перемешать 🔄", callback_data=f"shuffle_{key}")
            ],
            [
                InlineKeyboardButton("🎨 Сортировать по палитре 🎨", callback_data=f"palettesort_{key}")
            ],
            [
                InlineKeyboardButton("📔 Сохранить в папку 📔", callback_data=f"snooze_with_tag_{key}")
            ],                                    
            [
                InlineKeyboardButton("Поменять 2 изображения местами", callback_data=f"swapimages_{key}")
            ],
            [
                InlineKeyboardButton("❌ Удалить 1 изображение ❌", callback_data=f"filedelete_{key}")
            ],
            [
                InlineKeyboardButton("🗂 Посмотреть папки 🗂", callback_data="scheduled_by_tag")
            ],
            [
                InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')
            ],            
        ])
    )









async def filedelete_image(update: Update, context: CallbackContext) -> None:
    """Начинаем процесс удаления изображения."""
    query = update.callback_query
    await query.answer()


    # Проверяем формат callback_data
    if query and query.data.startswith("filedelete_"):
        data_parts = query.data.split('_')
        user_id = data_parts[1]
        user_message = "_".join(data_parts[2:])
        key = f"{user_id}_{user_message}"
    else:
        await query.message.reply_text("🛑 Неверный формат данных.")
        return
    global media_group_storage
    # Загружаем данные из Firebase
    media_group_storage = load_publications_from_firebase()

    # Проверяем наличие user_id в media_group_storage
    if user_id in media_group_storage:
        user_publications = media_group_storage[user_id]

        # Проверяем наличие ключа
        if key in user_publications:
            media_group = user_publications[key]

            # Проверяем структуру media_group
            if isinstance(media_group, dict) and 'media' in media_group:
                media = media_group['media']  # Извлекаем список media
            else:
                await query.message.reply_text("🛑 Некорректный формат данных.")
                return

            if len(media) < 1:
                await query.message.reply_text("🛑 Нет изображений для удаления.")
                return

            # Создаём кнопки для выбора изображения для удаления
            keyboard = [
                [InlineKeyboardButton(f"Изображение {i+1}", callback_data=f"fileselect_{user_id}_{user_message}_{i}")]
                for i in range(len(media))
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text("Выберите изображение для удаления:", reply_markup=reply_markup)
        else:
            await query.message.reply_text("🛑 Запись не найдена.")
    else:
        await query.message.reply_text("🛑 Пользователь не найден.")


async def fileselect_image_to_delete(update: Update, context: CallbackContext) -> None:
    """Обрабатываем выбор изображения для удаления и выполняем удаление."""
    query = update.callback_query
    await query.answer()

    # Проверяем формат callback_data
    if query and query.data.startswith("fileselect_"):
        data_parts = query.data.split('_')
        user_id = data_parts[1]
        user_message = "_".join(data_parts[2:-1])
        index = int(data_parts[-1])  # Последняя часть — индекс изображения
        key = f"{user_id}_{user_message}"
    else:
        await query.message.reply_text("🛑 Неверный формат данных.")
        return

    global media_group_storage
    # Загружаем данные из Firebase
    media_group_storage = load_publications_from_firebase()
    media_group = media_group_storage.get(user_id, {}).get(key)

    # Проверяем наличие данных
    if not media_group:
        await query.message.reply_text("🛑 Данные не найдены.")
        return

    # Проверяем структуру данных
    if isinstance(media_group, dict) and 'media' in media_group:
        media = media_group['media']
    elif isinstance(media_group, list):
        media = media_group
    else:
        await query.message.reply_text("🛑 Некорректный формат данных.")
        return

    # Проверяем индекс
    if not (0 <= index < len(media)):
        await query.message.reply_text("🛑 Ошибка индекса.")
        return

    # Удаляем изображение
    removed_image = media.pop(index)

    # Переносим caption и parse_mode к первому изображению, если удаляется первое
    if index == 0 and media:
        media[0]['caption'] = removed_image.get('caption', '')
        media[0]['parse_mode'] = removed_image.get('parse_mode', None)

    # Сохраняем обновления в Firebase
    if isinstance(media_group_storage[user_id][key], dict):
        media_group_storage[user_id][key]['media'] = media
    else:
        media_group_storage[user_id][key] = media
    save_media_group_data(media_group_storage, user_id)

    # Формируем превью медиагруппы
    media_group_preview = [
        InputMediaPhoto(
            media=item['file_id'],
            caption=item.get('caption', ''),
            parse_mode=item.get('parse_mode', None)
        ) for item in media
    ]

    # Отправляем медиагруппу
    if media_group_preview:
        await context.bot.send_media_group(
            chat_id=query.message.chat_id,
            media=media_group_preview
        )
    else:
        await query.message.reply_text("Медиагруппа пуста. Все изображения удалены.")

    # Формируем ответ с информацией об удалённом изображении
    json_removed_image = json.dumps(removed_image, ensure_ascii=False, indent=4)
    await query.message.reply_text(
        text=f"✅ Изображение успешно удалено и пост обновлен.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("В ТГ", callback_data=f"publish_{key}"),
                InlineKeyboardButton("В ВК", callback_data=f"vkpub_{key}"),
                InlineKeyboardButton("В X.com", callback_data=f"twitterpub_{key}"),
                InlineKeyboardButton("Удалить", callback_data=f"yrrasetag_{key}"),  
            ],
            [
                InlineKeyboardButton("🌠 Предложить этот пост в Анемон 🌠", callback_data=f"share_{key}")
            ],            
            [
                InlineKeyboardButton("🔄 Случайно перемешать 🔄", callback_data=f"shuffle_{key}")
            ],
            [
                InlineKeyboardButton("🎨 Сортировать по палитре 🎨", callback_data=f"palettesort_{key}")
            ],
            [
                InlineKeyboardButton("📔 Сохранить в папку 📔", callback_data=f"snooze_with_tag_{key}")
            ],
            [
                InlineKeyboardButton("Поменять 2 изображения местами", callback_data=f"swapimages_{key}")
            ],
            [
                InlineKeyboardButton("❌ Удалить 1 изображение ❌", callback_data=f"filedelete_{key}")
            ],
            [
                InlineKeyboardButton("🗂 Посмотреть папки 🗂", callback_data="scheduled_by_tag")
            ],
            [
                InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')
            ],            
        ]),
        parse_mode='HTML'
    )









async def handle_view_scheduled(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    MAX_CAPTION_LENGTH = 1024
    # Разделяем callback_data
    if '_' in query.data:
        _, key = query.data.split('_', 1)
    else:
        await query.message.reply_text("🚫 Ошибка: Некорректный формат данных.")
        return
    
    global media_group_storage
    # Загружаем данные из файла
    media_group_storage = load_publications_from_firebase()
    
    # ID текущего пользователя
    current_user_id = str(update.effective_user.id)
    
    # Проверяем, что данные есть для текущего пользователя
    if current_user_id in media_group_storage:
        user_publications = media_group_storage[current_user_id]
        data = user_publications.get(key)
        if data:
            try:
                # Если данные - это строка, преобразуем в словарь
                if isinstance(data, str):
                    data = json.loads(data)
                
                if isinstance(data, dict) and 'media' in data:
                    media = data['media']
                    media_group = []
                    captions_only = []
                    
                    if isinstance(media, list):
                        for media_data in media:
                            if 'file_id' in media_data:
                                file_id = media_data['file_id']
                                # Проверяем, является ли это URL или file_id
                                if file_id.startswith("http"):
                                    media_type = "url"
                                else:
                                    media_type = "file_id"
                                
                                caption = media_data.get('caption', '')
                                parse_mode = media_data.get('parse_mode', None)
                                
                                # Проверяем длину caption
                                if len(caption) > MAX_CAPTION_LENGTH:
                                    # Если caption слишком длинный, отправляем его отдельно
                                    caption_to_send = ''
                                else:
                                    caption_to_send = caption
                                
                                file_id_lower = file_id.lower()
                                if file_id_lower.endswith('.gif') or file_id_lower.endswith('.mp4'):
                                    # Обработка gif/mp4 через process_image и отправка как animation
                                    try:
                                        processed_image, is_gif = await process_image(file_id)
                                        if not processed_image:
                                            raise Exception("Failed to process gif/mp4")

                                        if is_gif:
                                            await query.message.reply_text("Gif обрабатывается, ожидайте...\n\nВ боте GIF будет отображаться в сжатом виде...")

                                        message = await query.message.reply_animation(
                                            animation=processed_image,
                                            filename="animation.gif",
                                            caption=caption,
                                            parse_mode=parse_mode
                                        )
                                    except Exception as e:
                                        logger.error(f"Ошибка при отправке gif/mp4: {e}")
                                elif file_id_lower.endswith('.jpg') or file_id_lower.endswith('.jpeg') or file_id_lower.endswith('.png') or media_type == 'file_id':
                                    media_group.append(
                                        InputMediaPhoto(
                                            media=file_id,
                                            caption=caption_to_send,
                                            parse_mode=parse_mode
                                        )
                                    )
                                else:
                                    # fallback — если ничего не подошло, можно попробовать отправить как документ
                                    media_group.append(
                                        InputMediaDocument(
                                            media=file_id,
                                            caption=caption_to_send,
                                            parse_mode=parse_mode
                                        )
                                    )

                    elif isinstance(media, dict):
                        for _, media_data in media.items():
                            if 'file_id' in media_data:
                                file_id = media_data['file_id']
                                if file_id.startswith("http"):
                                    media_type = "url"
                                else:
                                    media_type = "file_id"
                                
                                caption = media_data.get('caption', '')
                                parse_mode = media_data.get('parse_mode', None)
                                
                                # Проверяем длину caption
                                if len(caption) > MAX_CAPTION_LENGTH:
                                    # Если caption слишком длинный, отправляем его отдельно
                                    caption_to_send = ''
                                else:
                                    caption_to_send = caption
                                
                                file_id_lower = file_id.lower()
                                if file_id_lower.endswith('.gif') or file_id_lower.endswith('.mp4'):
                                    # Обработка gif/mp4 через process_image и отправка как animation
                                    try:
                                        processed_image, is_gif = await process_image(file_id)
                                        if not processed_image:
                                            raise Exception("Failed to process gif/mp4")

                                        if is_gif:
                                            await query.message.reply_text("Gif обрабатывается, ожидайте...\n\nВ боте GIF будет отображаться в сжатом виде...")

                                        message = await query.message.reply_animation(
                                            animation=processed_image,
                                            filename="animation.gif",
                                            caption=caption,
                                            parse_mode=parse_mode
                                        )
                                    except Exception as e:
                                        logger.error(f"Ошибка при отправке gif/mp4: {e}")
                                elif file_id_lower.endswith('.jpg') or file_id_lower.endswith('.jpeg') or file_id_lower.endswith('.png') or media_type == 'file_id':
                                    media_group.append(
                                        InputMediaPhoto(
                                            media=file_id,
                                            caption=caption_to_send,
                                            parse_mode=parse_mode
                                        )
                                    )
                                else:
                                    # fallback — если ничего не подошло, можно попробовать отправить как документ
                                    media_group.append(
                                        InputMediaDocument(
                                            media=file_id,
                                            caption=caption_to_send,
                                            parse_mode=parse_mode
                                        )
                                    )
                    
                    # Отправка медиа-группы
                    if media_group:
                        await context.bot.send_media_group(
                            chat_id=query.message.chat_id,
                            media=media_group
                        )
                    
                    # Отправка подписей без изображений
                    for caption in captions_only:
                        await query.message.reply_text(
                            text=caption,
                            parse_mode='HTML'
                        )
                    
                    # Отправка caption, если он был слишком длинным
                    for media_data in media:
                        caption = media_data.get('caption', '')
                        if len(caption) > MAX_CAPTION_LENGTH:
                            await query.message.reply_text(
                                text=caption,
                                parse_mode=media_data.get('parse_mode', None)
                            )
                    
                    # Отправляем информацию о записи с кнопками
                    await send_scheduled_post_buttons(query, key, data)
                else:
                    await query.message.reply_text("🚫 Ошибка: Некорректный формат данных.")
            except json.JSONDecodeError as e:
                await query.message.reply_text(f"🚫 Ошибка преобразования данных: {e}")
        else:
            await query.message.reply_text("🚫 Запись не найдена.")




async def send_scheduled_post_buttons(query, key, data):
    """Отправляет сообщение с кнопками управления публикацией."""
    await query.message.reply_text(
        text=f"Папка: {data.get('scheduled', 'Не указана')}\n\nКоличество медиа в посте: {len(data.get('media', []))}\n\nПри нажатии кнопки \"Редактировать пост\" вы можете отсортировать или удалить изображения, а так же поменять подпись. ",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("В ТГ", callback_data=f"publish_{key}"),
                InlineKeyboardButton("В ВК", callback_data=f"vkpub_{key}"),
                InlineKeyboardButton("В X.com", callback_data=f"twitterpub_{key}"),
                InlineKeyboardButton("Удалить", callback_data=f"yrrasetag_{key}"),  
            ],
            [
                InlineKeyboardButton("🗓️ Отложить 🗓️", callback_data=f"schedulepost_{key}")
            ],             
            [
                InlineKeyboardButton("🌠 Предложить этот пост в Анемон 🌠", callback_data=f"share_{key}")
            ],
            [
                InlineKeyboardButton("📝 Редактировать пост 📝", callback_data=f"editpost_{key}")
            ],                
            [
                InlineKeyboardButton("📔 Сменить папку 📔", callback_data=f"snooze_with_tag_{key}")
            ],
            [
                InlineKeyboardButton("🗂 Посмотреть мои папки 🗂", callback_data="scheduled_by_tag")
            ],
            [
                InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')
            ],            
        ])
    )

async def handle_edit_post(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if '_' in query.data:
        _, key = query.data.split('_', 1)
    else:
        await query.message.reply_text("🚫 Ошибка: Некорректный формат данных.")
        return

    await query.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Случайно перемешать 🔄", callback_data=f"shuffle_{key}")
            ],
            [
                InlineKeyboardButton("🎨 Сортировать по палитре 🎨", callback_data=f"palettesort_{key}")
            ],
            [
                InlineKeyboardButton("Поменять 2 изображения местами", callback_data=f"swapimages_{key}")
            ],
            [
                InlineKeyboardButton("❌ Удалить 1 изображение ❌", callback_data=f"filedelete_{key}")
            ],
            [
                InlineKeyboardButton("✏️ Заменить подпись ✏️", callback_data=f"caption_{key}")
            ],
            [
                InlineKeyboardButton("⬅️ Назад", callback_data=f"backtomain_{key}")
            ]
        ])
    )

async def handle_back_to_main(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    if '_' in query.data:
        _, key = query.data.split('_', 1)
    else:
        await query.message.reply_text("🚫 Ошибка: Некорректный формат данных.")
        return

    # Загружаем актуальные данные
    media_group_storage = load_publications_from_firebase()
    current_user_id = str(update.effective_user.id)
    if current_user_id in media_group_storage:
        user_publications = media_group_storage[current_user_id]
        data = user_publications.get(key)
        if data:
            # Используем edit_message_text для замены сообщения
            await query.message.edit_text(
                text=f"Папка: {data.get('scheduled', 'Не указана')}\n\nКоличество медиа в посте: {len(data.get('media', []))}",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("В ТГ", callback_data=f"publish_{key}"),
                        InlineKeyboardButton("В ВК", callback_data=f"vkpub_{key}"),
                        InlineKeyboardButton("В X.com", callback_data=f"twitterpub_{key}"),
                        InlineKeyboardButton("Удалить", callback_data=f"yrrasetag_{key}"),  
                    ],
                    [
                        InlineKeyboardButton("🌠 Предложить этот пост в Анемон 🌠", callback_data=f"share_{key}")
                    ],
                    [
                        InlineKeyboardButton("📝 Редактировать пост 📝", callback_data=f"editpost_{key}")
                    ],                   
                    [
                        InlineKeyboardButton("📔 Сменить папку 📔", callback_data=f"snooze_with_tag_{key}")
                    ],
                    [
                        InlineKeyboardButton("🗂 Посмотреть мои папки 🗂", callback_data="scheduled_by_tag")
                    ],
                    [
                        InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')
                    ], 
                ])
            )
        else:
            await query.message.reply_text("🚫 Запись не найдена.")
    else:
        await query.message.reply_text("🚫 Пользователь не найден в базе данных.")




import random

async def handle_shuffle_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()  # Ответ пользователю, что нажатие обработано

    # Проверяем формат callback_data
    if query and query.data.startswith("shuffle_"):
        data_parts = query.data.split('_', 1)
        key = data_parts[1] if len(data_parts) > 1 else None
    else:
        await query.message.reply_text("\u274c Ошибка: Некорректный формат данных.")
        return

    global media_group_storage
    # Загружаем данные из Firebase
    media_group_storage = load_publications_from_firebase()

    # Проверяем наличие ключа в хранилище
    user_id, user_message = key.split('_', 1) if '_' in key else (None, None)
    if user_id in media_group_storage:
        user_publications = media_group_storage[user_id]

        if key in user_publications:
            media_group = user_publications[key]

            # Проверяем структуру media_group
            if isinstance(media_group, dict) and 'media' in media_group:
                media = media_group['media']
            else:
                await query.message.reply_text("\u274c Некорректный формат данных.")
                return

            if not isinstance(media, list) or len(media) < 1:
                await query.message.reply_text("\u274c Нет изображений для перемешивания.")
                return

            # Сохраняем caption и parse_mode первого элемента
            first_caption = media[0].get('caption')
            first_parse_mode = media[0].get('parse_mode')

            # Перемешиваем media
            random.shuffle(media)

            # Устанавливаем сохранённые caption и parse_mode для первого элемента
            media[0]['caption'] = first_caption
            media[0]['parse_mode'] = first_parse_mode

            # Сбрасываем caption и parse_mode у остальных
            for item in media[1:]:
                item['caption'] = None
                item['parse_mode'] = None

            # Создаём медиагруппу для отправки
            media_group = [
                InputMediaPhoto(
                    media=item['file_id'],
                    caption=item.get('caption', ''),
                    parse_mode=item.get('parse_mode')
                ) for item in media if 'file_id' in item
            ]

            # Отправляем медиагруппу пользователю
            if media_group:
                await context.bot.send_media_group(
                    chat_id=query.message.chat_id,
                    media=media_group
                )

            # Обновляем данные в хранилище
            media_group_storage[user_id][key]['media'] = media
            save_media_group_data(media_group_storage, user_id)

            # Отправляем сообщение с кнопками
            await query.message.reply_text(
                text=f"🔄 Изображения перемешаны:\n\nКоличество медиа: {len(media)}",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("В ТГ", callback_data=f"publish_{key}"),
                        InlineKeyboardButton("В ВК", callback_data=f"vkpub_{key}"),
                        InlineKeyboardButton("В X.com", callback_data=f"twitterpub_{key}"),
                        InlineKeyboardButton("Удалить", callback_data=f"yrrasetag_{key}"),  
                    ],
                    [
                        InlineKeyboardButton("🌠 Предложить этот пост в Анемон 🌠", callback_data=f"share_{key}")
                    ],                    
                    [
                        InlineKeyboardButton("🔄 Случайно перемешать ещё раз 🔄", callback_data=f"shuffle_{key}")
                    ],
                    [
                        InlineKeyboardButton("🎨 Сортировать по палитре 🎨", callback_data=f"palettesort_{key}")
                    ],
                    [
                        InlineKeyboardButton("📔 Сохранить в папку 📔", callback_data=f"snooze_with_tag_{key}")
                    ],                                                    
                    [
                        InlineKeyboardButton("Поменять 2 изображения местами", callback_data=f"swapimages_{key}")
                    ],
                    [
                        InlineKeyboardButton("❌ Удалить 1 изображение ❌", callback_data=f"filedelete_{key}")
                    ],
                    [
                        InlineKeyboardButton("🗂 Посмотреть папки 🗂", callback_data="scheduled_by_tag")
                    ],
                    [
                        InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')
                    ],                    
                ])
            )
        else:
            await query.message.reply_text("🚫 Ошибка: 'media' не найдено или некорректного формата.")

    else:
        await query.message.reply_text("🚫 Запись не найдена.")

import requests
from PIL import Image
from io import BytesIO
import numpy as np
from colorsys import rgb_to_hsv





async def download_image(session, url):
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.read()
            return Image.open(BytesIO(data))
        else:
            raise Exception(f"Failed to download image: {url}")

async def download_images(image_urls):
    async with aiohttp.ClientSession() as session:
        tasks = [download_image(session, url) for url in image_urls]
        return await asyncio.gather(*tasks)
    






SORT_OPTIONS = [
    ("`🖤-Тёмный       `", "dark"),
    ("`🤍-Светлый      `", "light"),
    ("`🌈-Насыщенные    `", "saturated"),
    ("`🩶-Серые         `", "desaturated"),
    ("`❤️-Красный       `", "red"),
    ("`🧡-Оранжевый     `", "orange"),
    ("`💛-Жёлтый        `", "yellow"),
    ("`💚-Зелёный       `", "green"),
    ("`🩵-Голубой       `", "cyan"),
    ("`💙-Синий         `", "blue"),
    ("`💜-Фиолетовый    `", "purple"),
    ("`От тёплых к холодным`", "warm")
]



def analyze_image_colors(image, criterion):
    """
    Анализирует изображение и возвращает распределения.
    """
    img = image.convert('RGB').resize((150, 150), Image.Resampling.LANCZOS)
    arr = np.array(img).reshape(-1, 3)
    hsv_pixels = [rgb_to_hsv(r / 255, g / 255, b / 255) for r, g, b in arr]
    total_pixels = len(hsv_pixels)

    # --- ТОЧНЫЙ ПОПИКСЕЛЬНЫЙ АНАЛИЗ АХРОМАТИКИ ---
    # Белый: строго ВЫСОКАЯ яркость (>= 0.75) И НИЗКАЯ насыщенность (< 0.3)
    exact_white_pixels = sum(1 for _, s, v in hsv_pixels if v >= 0.75 and s < 0.3)
    # Черный: строго НИЗКАЯ яркость (< 0.33)
    exact_black_pixels = sum(1 for _, _, v in hsv_pixels if v < 0.33)
    # Серый: средняя яркость и низкая насыщенность
    exact_gray_pixels = sum(1 for _, s, v in hsv_pixels if 0.33 <= v < 0.75 and s < 0.3)


    dark_high_sat_pixels = sum(1 for _, s, v in hsv_pixels if v < 0.33 and s >= 0.3)
    bright_high_sat_pixels = sum(1 for _, s, v in hsv_pixels if v >= 0.75 and s >= 0.3)

    dark_low_sat_pixels = sum(1 for _, s, v in hsv_pixels if v < 0.33 and s < 0.3)
    bright_low_sat_pixels = sum(1 for _, s, v in hsv_pixels if v >= 0.75 and s < 0.3)


    # Глобальный анализ яркости
    brightness = [v for _, _, v in hsv_pixels]
    dark_pixels = sum(1 for v in brightness if v < 0.33)
    medium_pixels = sum(1 for v in brightness if 0.33 <= v < 0.75)
    bright_pixels = sum(1 for v in brightness if v >= 0.75)
    total_brightness = sum(brightness) / len(brightness)
    total_bright = 1 - total_brightness

    brightness_distribution = {
        "dark": dark_pixels / total_pixels,
        "medium": medium_pixels / total_pixels,
        "bright": bright_pixels / total_pixels,
        "total_bright": total_bright,
        # Прокидываем точные попиксельные пересечения наружу
        "exact_white": exact_white_pixels / total_pixels,
        "exact_black": exact_black_pixels / total_pixels,
        "exact_gray": exact_gray_pixels / total_pixels,
        "dark_high_sat": dark_high_sat_pixels / total_pixels,
        "bright_high_sat": bright_high_sat_pixels / total_pixels,
        "dark_low_sat": dark_low_sat_pixels / total_pixels,
        "bright_low_sat": bright_low_sat_pixels / total_pixels,
    }

    # Анализ насыщенности
    saturation = [s for _, s, _ in hsv_pixels]
    gray_pixels = sum(1 for s in saturation if s < 0.3)
    medium_saturation_pixels = sum(1 for s in saturation if 0.3 <= s < 0.75)
    high_saturation_pixels = sum(1 for s in saturation if s >= 0.75)

    saturation_distribution = {
        "gray": gray_pixels / total_pixels,
        "medium": medium_saturation_pixels / total_pixels,
        "high": high_saturation_pixels / total_pixels,
    }

    # Анализ оттенков
    hue_distribution = {
        "red": [0, 0, 0, 0, 0, 0],  # [hv, mv, lv, hs, ms, ls]
        "orange": [0, 0, 0, 0, 0, 0],
        "yellow": [0, 0, 0, 0, 0, 0],
        "green": [0, 0, 0, 0, 0, 0],
        "cyan": [0, 0, 0, 0, 0, 0],
        "blue": [0, 0, 0, 0, 0, 0],
        "purple": [0, 0, 0, 0, 0, 0],
    }
    color_boundaries = {
        "red": (340 / 360, 5 / 360),
        "orange": (5/ 360, 45 / 360),
        "yellow": (45 / 360, 75 / 360),  
        "green": (75 / 360, 170 / 360),  
        "cyan": (170 / 360, 200 / 360),
        "blue": (200 / 360, 250 / 360),
        "purple": (250 / 360, 340 / 360),
    }





    overlap_margin = 10 / 360  # Граница перекрытия в градусах (5°)

    for h, s, v in hsv_pixels:
        for color, (lower, upper) in color_boundaries.items():
            is_in_range = lower <= h < upper or (lower > upper and (h >= lower or h < upper))
            is_in_overlap = (lower - overlap_margin <= h < lower) or (upper <= h < upper + overlap_margin)

            if is_in_range or is_in_overlap:
                index = 0 if v >= 0.66 else 1 if v >= 0.33 else 2
                hue_distribution[color][index] += 1

                sat_index = 3 if s >= 0.5 else 4 if s >= 0.2 else 5
                hue_distribution[color][sat_index] += 1

    hue_distribution = {
        color: {
            "hv": round(100 * hv / total_pixels, 2),
            "mv": round(100 * mv / total_pixels, 2),
            "lv": round(100 * lv / total_pixels, 2),
            "hs": round(100 * hs / total_pixels, 2),
            "ms": round(100 * ms / total_pixels, 2),
            "ls": round(100 * ls / total_pixels, 2),
        }
        for color, (hv, mv, lv, hs, ms, ls) in hue_distribution.items()
    }

    # Расчёт веса
    for color, data in hue_distribution.items():
        brightness_weight = (
            -3.0 * brightness_distribution["dark"] +
            2.0 * brightness_distribution["medium"] +
            0.5 * brightness_distribution["bright"]
        )
        saturation_weight = (
            -3.0 * saturation_distribution["gray"] +
            1.0 * saturation_distribution["medium"] +
            3.0 * saturation_distribution["high"]
        )
        
        if brightness_distribution["bright"] > 0.8:
            saturation_weight += 1.5 * saturation_distribution["gray"]
            data["ls"], data["ms"] = -0.2 * data["ls"], 3.0 * data["ms"]
            
        if saturation_distribution["gray"] > 0.85:
            if brightness_distribution["dark"] > 0.3 and brightness_distribution["bright"] < 0.7:
                data["hs"], data["ms"], data["ls"] = (
                    16.0 * data["hs"],
                    15.0 * data["ms"],
                    0.5 * data["ls"]
                )
                
        color_mass = data["hs"] + data["ms"] + data["ls"]
        
        # ИСПРАВЛЕНИЕ 1: Снижаем порог отсечения мелких деталей до 0.2%
        if color_mass < 0.2:
            data["tw"] = 0
            continue

        global_bonus = (brightness_weight + saturation_weight)
        
        # ИСПРАВЛЕНИЕ 2: Защищаем цвет от влияния серого фона.
        # Если фон депрессивный (global_bonus < 0), мы не штрафуем цвет, 
        # а наоборот, даем небольшой бонус за его собственную насыщенность (hs, ms)
        if global_bonus < 0:
            color_bonus = (data["hs"] * 1.5 + data["ms"] * 0.5) 
        else:
            color_bonus = global_bonus * (color_mass / 100.0)

        # ИСПРАВЛЕНИЕ 3: Смягчаем штрафы за "тёмность" цвета (-2 * lv заменено на -0.5 * lv)
        # Шарф в тенях все еще должен оставаться красным.
        data["tw"] = round(max(0, (
            5.0 * data["hs"] + 3.0 * data["ms"] + 0.5 * data["ls"] + 
            2.0 * data["mv"] - 0.5 * data["lv"] + 
            10.0 * color_bonus
        )), 2)

    # Проверка, если все значения tw равны 0
    # Проверка, если все значения tw равны 0
    if all(data["tw"] == 0 for data in hue_distribution.values()):
        for color, data in hue_distribution.items():
            # Собираем значения hs, ms, ls
            values = [data["hs"], data["ms"], data["ls"]]
            
            # Проверяем наличие положительных значений
            positive_values = [v for v in values if v > 0]
            
            if positive_values:
                # Если есть положительные значения, берём максимальное из них
                data["tw"] = max(positive_values)
            else:
                # Если все значения отрицательные, берём наименьшее по модулю (наибольшее отрицательное) и делаем его положительным
                data["tw"] = abs(min(values))

    return brightness_distribution, saturation_distribution, hue_distribution

def hue_finele(hue_distribution, criterion):
    """
    Вычисляет итоговый оттенок (hue) изображения на основе данных распределения оттенков.

    :param hue_distribution: Словарь с данными о распределении оттенков.
    :param criterion: Критерий, к которому будет ближе финальный оттенок.
    :return: Финальное значение оттенка (hue) изображения.
    """
    # Отбираем топ-3 цвета по значению tw
    top_colors = sorted(
        ((color, data["tw"]) for color, data in hue_distribution.items() if data["tw"] > 0),
        key=lambda x: x[1],
        reverse=True
    )[:3]


    if len(top_colors) < 1:
        return None  # Если нет данных о цветах, возвращаем None

    # Определение hue для каждого цвета
    hue_positions = {
        "red": 0,
        "orange": 30,
        "yellow": 60,
        "green": 130,
        "cyan": 180,
        "blue": 230,
        "purple": 280
    }

    # Проверка и обработка criterion
    if criterion in ["dark", "light"]:

        hue_criterion = None  # Устанавливаем в None, чтобы избежать ошибок
    elif criterion in ["saturated", "desaturated", "warm"]:

        hue_criterion = hue_positions["red"]
    else:
        if criterion not in hue_positions:
            raise ValueError(f"🚫 Неверный критерий сортировки: {criterion}")
        hue_criterion = hue_positions[criterion]


    # Проверяем разницу между первыми двумя цветами
    if hue_criterion is not None and len(top_colors) > 1 and (
        abs(top_colors[0][1] - top_colors[1][1]) <= 20 or top_colors[1][1] > 150
    ):
        # Определяем ближайший к hue_criterion
        color1, value1 = top_colors[0]
        color2, value2 = top_colors[1]
        hue1 = hue_positions[color1]
        hue2 = hue_positions[color2]

        # Вычисляем расстояния до hue_criterion
        dist1 = abs((hue1 - hue_criterion) % 360)
        dist2 = abs((hue2 - hue_criterion) % 360)
        if dist1 > 180:
            dist1 = 360 - dist1
        if dist2 > 180:
            dist2 = 360 - dist2

        # Определяем базовый цвет по близости к hue_criterion
        if dist1 <= dist2:
            base_color, base_value = color1, value1
            secondary_color = (color2, value2)
        else:
            base_color, base_value = color2, value2
            secondary_color = (color1, value1)

        # Перемещаем второй цвет в логику обработки дополнительных цветов
        additional_colors = [secondary_color] + top_colors[2:]
    else:
        base_color, base_value = top_colors[0]
        additional_colors = top_colors[1:]

    base_hue = hue_positions[base_color]

    # Учитываем вес базового цвета на основе значения tw
    base_weight = base_value / 1000  # Нормализуем вес в диапазоне [0, 1]


    # Обработка дополнительных цветов
    adjustments = []
    for color, value in additional_colors:
        if color in hue_positions:
            delta_hue = (hue_positions[color] - base_hue) % 360
            if delta_hue > 180:
                delta_hue -= 360  # Приведение к диапазону [-180, 180]

            # Определяем делитель для расчёта shift_degree
            divisor = 100 if value > base_value + 100 else 10

            # Рассчитываем градус смещения с учетом tw
            shift_degree = (value / divisor) * (1 - base_weight * 0.35)  # Вес базового цвета уменьшает влияние других цветов
            adjustments.append((delta_hue, shift_degree))

    # Если оба смещения направлены в одну сторону, учитываем только первое
    if len(adjustments) > 1:
        if all(adj[0] > 0 for adj in adjustments) or all(adj[0] < 0 for adj in adjustments):
            adjustments = [max(adjustments, key=lambda x: abs(x[1]))]

    # Применяем корректировку
    final_hue_adjustment = sum(delta * (weight / abs(delta)) for delta, weight in adjustments)
    final_hue = (base_hue + final_hue_adjustment) % 360
    return round(final_hue, 2)






import math

def calculate_normalized_brightness(brightness_distribution, saturation_distribution):
    # Веса для распределений яркости
    brightness_weights = {
        "dark": 0.3,       # Уменьшаем итоговое значение
        "medium": 0.2,      # Нейтральное влияние
        "bright": -0.1      # Увеличиваем итоговое значение
    }
    # Веса для распределений насыщенности
    saturation_weights = {
        "gray": -0.1,        # Увеличиваем итоговое значение (считаем серость ярче)
        "medium": 0.2,      # Нейтральное влияние
        "high": 0.3        # Уменьшаем итоговое значение (высокая насыщенность воспринимается темнее)
    }

    # Рассчитываем взвешенную сумму яркости
    weighted_brightness = sum(
        brightness_distribution[key] * weight
        for key, weight in brightness_weights.items()
    )
    # Рассчитываем взвешенную сумму насыщенности
    weighted_saturation = sum(
        saturation_distribution[key] * weight
        for key, weight in saturation_weights.items()
    )

    # Сумма всех весов
    total_weights_sum = sum(brightness_weights.values()) + sum(saturation_weights.values())

    # Итоговая нормализованная яркость
    raw_brightness = (brightness_distribution["total_bright"] + weighted_brightness + weighted_saturation) * total_weights_sum

    # Применяем логистическую функцию для экспоненциальной нормализации
    def logistic_function(x):
        return 1 / (1 + math.exp(-x))

    # Ограничиваем значение в пределах от 0 до 1
    normalized_brightness = logistic_function(raw_brightness)
    normalized_brightness = max(0, min(1, normalized_brightness))

    return normalized_brightness


# Сортирует изображения по яркости
async def sort_images_by_priority(media, criterion):
    """
    Сортирует изображения по яркости: от светлого к тёмному (light) или наоборот (dark).
    """
    # Подготовка списка URL
    image_urls = [item['file_id'] for item in media if 'file_id' in item]

    # Скачивание изображений асинхронно
    try:
        downloaded_images = await download_images(image_urls)  # Используем await здесь
    except Exception as e:
        raise RuntimeError(f"Error downloading images: {e}")

    # Анализируем изображения и определяем hue для каждого
    analyzed_images = []

    for item, image in zip(media, downloaded_images):
        if image is not None:
            brightness_distribution, saturation_distribution, hue_distribution = analyze_image_colors(image, criterion)


            top_colors = sorted(
                ((color, data["tw"]) for color, data in hue_distribution.items() if data["tw"] > 0),
                key=lambda x: x[1],
                reverse=True
            )[:3]


            color_weights = {
                'yellow': -0.02,
                'blue': 0.01,
                'green': -0.003,
                'cyan': -0.005,
                'red': 0.002,
                'purple': 0.005,
                'orange': -0.007
            }


            brightness_distribution, saturation_distribution, _ = analyze_image_colors(image, criterion)
            normalized_brightness = calculate_normalized_brightness(
                brightness_distribution, saturation_distribution
            )
          
            # Корректировка по цветам
            color_adjustment = 0
            total_weight = sum(weight for _, weight in top_colors)
            for color, weight in top_colors:
                if color in color_weights:
                    influence = color_weights[color] * (weight / total_weight)
                    color_adjustment += influence

            # Ограничение влияния цветов на диапазон [-0.2, +0.2]
            color_adjustment = max(min(color_adjustment, 0.2), -0.2)

            # Влияние серых пикселей
            gray_ratio = saturation_distribution['gray']
            middle_ratio = saturation_distribution['medium']
            if (gray_ratio > 0.85 or middle_ratio > 0.8) and brightness_distribution['bright'] > 0.85:
                # Если много серых пикселей или средняя насыщенность при высокой яркости, усиливаем яркость
                color_adjustment *= (1 - gray_ratio)  # Уменьшаем влияние цветовой корректировки
                normalized_brightness += 0.2 * gray_ratio  # Усиливаем базовую яркость

            # Итоговая яркость
            finale_brightness = max(min(normalized_brightness + color_adjustment, 1), 0)

            if criterion == 'light':
                # Обратная сортировка для 'dark'
                finale_brightness = 1 - finale_brightness


            # Добавляем данные изображения и его итоговую яркость
            analyzed_images.append((item, finale_brightness))

    # Сортировка по убыванию итоговой яркости
    sorted_images = sorted(analyzed_images, key=lambda x: x[1], reverse=True)

    return [item[0] for item in sorted_images]






# сортировка по цветам
async def sort_images_by_hue(media, criterion):
    """
    Сортирует изображения по оттенкам (hue), используя критерий для начального порядка.
    
    :param media: Список словарей с медиа-данными, включая URL изображений.
    :param criterion: Критерий цвета для первого изображения (например, 'red', 'blue', и т.д.).
    :return: Список отсортированных идентификаторов файлов.
    """
    # Подготовка списка URL
    image_urls = [item['file_id'] for item in media if 'file_id' in item]

    # Скачивание изображений асинхронно
    try:
        downloaded_images = await download_images(image_urls)  # Используем await здесь
    except Exception as e:
        raise RuntimeError(f"Error downloading images: {e}")
    
    # Анализируем изображения и определяем hue для каждого
    analyzed_images = []
    for item, image in zip(media, downloaded_images):
        if image is not None:
            hue_distribution = analyze_image_colors(image, criterion)[2]  # Передаем Image напрямую
            final_hue = hue_finele(hue_distribution, criterion)
            if final_hue is not None:
                analyzed_images.append((item, final_hue))


    # Проверка результатов анализа
    if not analyzed_images:
        raise ValueError("🚫 Hue-анализ изображений не дал результатов.")

    # Определяем начальный hue для сортировки на основе критерия
    hue_positions = {
        "red": 0,
        "orange": 30,
        "yellow": 60,
        "green": 130,
        "cyan": 180,
        "blue": 230,
        "purple": 280
    }
    if criterion not in hue_positions:
        raise ValueError(f"🚫 Неверный критерий сортировки: {criterion}")
    
    base_hue = hue_positions[criterion]

    # Функция сортировки по разнице углов
    # Функция для расчёта абсолютной разницы углов
    def hue_distance(hue1, hue2):
        return min(abs(hue1 - hue2), 360 - abs(hue1 - hue2))

    # Находим ближайшее изображение к base_hue
    closest_image = min(analyzed_images, key=lambda img: hue_distance(img[1], base_hue))
    sorted_images = [closest_image]  # Начинаем с ближайшего изображения

    # Удаляем ближайшее изображение из списка
    remaining_images = [img for img in analyzed_images if img != closest_image]

    # Будем добавлять следующее изображение, которое будет ближе всего к последнему selected final_hue
    last_hue = closest_image[1]

    while remaining_images:
        # Выбираем следующее изображение, которое наиболее близко к последнему выбранному final_hue
        next_image = min(remaining_images, key=lambda img: hue_distance(img[1], last_hue))
        sorted_images.append(next_image)
        
        # Обновляем последний выбранный hue
        last_hue = next_image[1]
        
        # Убираем это изображение из оставшихся
        remaining_images = [img for img in remaining_images if img != next_image]

    # Возвращаем отсортированные идентификаторы файлов
    return [item[0] for item in sorted_images]


import math
def gaussian_weight(hue, target, sigma):
    return math.exp(-((hue - target) ** 2) / (2 * sigma ** 2))
# сортировка по насыщенности
async def sort_images_by_color_priority(media, criterion):
    """
    Сортирует изображения по насыщенности: от насыщенного и светлого к тёмному (light) или наоборот (dark).
    """
    # Подготовка списка URL
    image_urls = [item['file_id'] for item in media if 'file_id' in item]

    # Скачивание изображений асинхронно
    try:
        downloaded_images = await download_images(image_urls)  # Используем await здесь
    except Exception as e:
        raise RuntimeError(f"Error downloading images: {e}")

    # Анализируем изображения и определяем насыщенность для каждого
    analyzed_images = []

    for item, image in zip(media, downloaded_images):
        if image is not None:
            # Анализ изображения
            brightness_distribution, saturation_distribution, hue_distribution = analyze_image_colors(image, criterion)
            final_hue = hue_finele(hue_distribution, criterion)



            # Вычисляем averaged_saturation
            gray_weight = -0.8  # Серым придаём больший вес
            medium_weight = 4.4  # Средние пиксели имеют меньший вес
            high_weight = 10.7  # Насыщенные пиксели имеют больший вес

            brightness_boost_factor = brightness_distribution['bright']  # Используем яркость напрямую
            if brightness_boost_factor > 0:
                medium_weight *= 1.5 + brightness_boost_factor 
                high_weight *= 2 + brightness_boost_factor 
            else:
                # Для низкой яркости можно оставить исходные значения или уменьшить веса
                medium_weight *= 0.9
                high_weight *= 0.9
                       
            averaged_saturation = (
                saturation_distribution['gray'] * gray_weight +
                saturation_distribution['medium'] * medium_weight +
                saturation_distribution['high'] * high_weight
            ) / (gray_weight + medium_weight + high_weight)

            # Корректируем averaged_saturation в зависимости от яркости
            bright_boost = 1.2  # Усиление при ярких пикселях
            middle_boost = 1.1  # Усиление при средних пикселях            
            dark_damp = 0.1  # Ослабление при тёмных пикселях

            # Дополнительный коэффициент нелинейного ослабления для "dark"
            dark_penalty_scale = 2.0  # Множитель для усиления влияния высокой "dark"
            dark_adjustment = brightness_distribution['dark'] ** dark_penalty_scale

            brightness_factor = ((
                brightness_distribution['bright'] * bright_boost +
                brightness_distribution['medium'] * middle_boost +
                brightness_distribution['dark'] * (1 - dark_damp) -
                dark_adjustment  # Учитываем нелинейное влияние "dark"
            ) / (bright_boost + middle_boost + dark_damp)) - (
                ((brightness_distribution['bright'] * 2) + brightness_distribution['medium'] + brightness_distribution['dark']) / 6.5
            )


            # Суммируем значения для учета их в одной переменной
            combined_value = (saturation_distribution['gray']) + (brightness_distribution['dark']) - (saturation_distribution['medium'] / 2) - (saturation_distribution['high'] / 2) 

            # Используем сдвиг для того, чтобы снижение начиналось при значении примерно 1
            shift_start = 1  # Начало сильного сдвига
            shift_factor = 4  # Сила сдвига, можно настроить            
            final_brightness_factor = brightness_factor / (1 + math.exp((combined_value - shift_start) * shift_factor))
            # Ограничиваем итоговую насыщенность в пределах [0, 1]
         
            averaged_saturation = max(0, min(1, averaged_saturation + final_brightness_factor))


            # Усиление для теплых и холодных оттенков
            warm_hue_boost = 0.04
            cold_hue_damp = 0.04
            max_adjustment = 0.1

            # Стандартное отклонение для гауссовой функции (ширина изменения)
            sigma = 30  # Чем меньше значение, тем резче спад влияния

            # Рассчитываем вес в зависимости от final_hue
            if (0 <= final_hue <= 140) or (330 <= final_hue <= 360):  # Тёплые оттенки
                weight_90 = gaussian_weight(final_hue, 90, sigma) if final_hue <= 140 else 0
                weight_350 = gaussian_weight(final_hue, 350, sigma) if final_hue >= 330 else 0
                weight = max(weight_90, weight_350)  # Выбираем наибольшее влияние
                adjustment = warm_hue_boost * weight
                finale_Saturation = averaged_saturation + min(max_adjustment, adjustment)

            elif 140 < final_hue < 330:  # Холодные оттенки
                weight = gaussian_weight(final_hue, 240, sigma)
                adjustment = cold_hue_damp * weight
                finale_Saturation = averaged_saturation - min(max_adjustment, adjustment)

            else:  # Предохранитель для значений вне диапазона
                finale_Saturation = averaged_saturation

            # Ограничиваем значение finale_Saturation в пределах допустимого диапазона
            finale_Saturation = max(0, min(1, finale_Saturation))

            # Ограничиваем результат в пределах [0, 1]
            finale_Saturation = max(0, min(1, finale_Saturation))  

            if criterion == 'desaturated':
                # Обратная сортировка для 'dark'
                finale_Saturation = 1 - finale_Saturation
            # Добавляем данные изображения и его итоговую насыщенность
            analyzed_images.append((item, finale_Saturation))

    # Сортировка по убыванию итоговой насыщенности
    sorted_images = sorted(analyzed_images, key=lambda x: x[1], reverse=True)

    return [item[0] for item in sorted_images]





# сортировка по теплоте
async def sort_images_by_warm(media, criterion):
    image_urls = [item['file_id'] for item in media if 'file_id' in item]

    try:
        downloaded_images = await download_images(image_urls)
    except Exception as e:
        raise RuntimeError(f"Error downloading images: {e}")

    analyzed_images = []

    for item, image in zip(media, downloaded_images):
        if image is not None:
            # Анализ изображения
            brightness_distribution, saturation_distribution, hue_distribution = analyze_image_colors(image, criterion)

            # Нормализация
            normalized_brightness = (
                0.2 * brightness_distribution['dark'] +
                0.5 * brightness_distribution['medium'] +
                0.8 * brightness_distribution['bright']
            )

            normalized_saturation = (
                0.1 * saturation_distribution['gray'] +
                0.6 * saturation_distribution['medium'] +
                0.9 * saturation_distribution['high']
            )

            warm_colors = ['red', 'orange', 'yellow']
            cold_colors = ['green', 'cyan', 'blue', 'purple']

            warm_tw = sum(hue_distribution[color]['tw'] for color in warm_colors)
            cold_tw = sum(hue_distribution[color]['tw'] for color in cold_colors)
            total_tw = sum(hue_distribution[color]['tw'] for color in hue_distribution)

            final_warm = (warm_tw - cold_tw) / total_tw if total_tw > 0 else 0

            # Итоговая метрика
            score = (
                0.6 * final_warm +  # Влияние цветов
                0.3 * normalized_brightness +  # Влияние яркости
                0.1 * (1 - normalized_saturation)  # Влияние насыщенности
            )

            analyzed_images.append((item, score))

    # Сортировка по убыванию итогового score
    sorted_images = sorted(analyzed_images, key=lambda x: x[1], reverse=True)

    return [item[0] for item in sorted_images]







async def handle_palettesort(update, context):
    query = update.callback_query
    await query.answer()

    # Проверяем формат callback_data
    if query.data and '_' in query.data:
        _, user_id, user_message = query.data.split('_', 2)
        key = f"{user_id}_{user_message}"
    else:
        await query.message.reply_text("🚫 Ошибка: Некорректный формат данных.")
        return


    global media_group_storage
    # Загружаем данные из Firebase
    media_group_storage = load_publications_from_firebase()

    if user_id in media_group_storage and key in media_group_storage[user_id]:
        data = media_group_storage[user_id][key]

        # Предлагаем выбор начального критерия сортировки
        buttons = [[InlineKeyboardButton(label, callback_data=f"sort_{user_id}_{user_message}_{option}")]
                   for label, option in SORT_OPTIONS]
        await query.message.reply_text(
            "Выберите желаемый цвет первого изображения для сортировки:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await query.message.reply_text("🚫 Запись не найдена.")


async def handle_palettesort(update, context):
    query = update.callback_query
    await query.answer()

    # Проверяем формат callback_data
    if query.data and '_' in query.data:
        _, user_id, user_message = query.data.split('_', 2)
        key = f"{user_id}_{user_message}"
    else:
        await query.message.reply_text("🚫 Ошибка: Некорректный формат данных.")
        return



    # Загружаем данные из Firebase
    global media_group_storage
    media_group_storage = load_publications_from_firebase()

    if user_id in media_group_storage and key in media_group_storage[user_id]:
        data = media_group_storage[user_id][key]

        # Предлагаем выбор начального критерия сортировки
        buttons = [[InlineKeyboardButton(label, callback_data=f"sort_{user_id}_{user_message}_{option}")]
                   for label, option in SORT_OPTIONS]
        await query.message.reply_text(
            "Выберите желаемый цвет первого изображения для сортировки:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await query.message.reply_text("🚫 Запись не найдена.")


async def sort_by_criteria(update, context):
    query = update.callback_query
    await query.answer()

    # Проверяем формат callback_data
    if query.data and '_' in query.data:
        parts = query.data.split('_')
        if len(parts) >= 4:
            _, user_id, user_message, criterion = parts[0], parts[1], '_'.join(parts[2:-1]), parts[-1]
            key = f"{user_id}_{user_message}"
        else:
            await query.message.reply_text("🚫 Ошибка: Некорректный формат данных.")
            return
    else:
        await query.message.reply_text("🚫 Ошибка: Некорректный формат данных.")
        return



    global media_group_storage
    media_group_storage = load_publications_from_firebase()

    if user_id in media_group_storage and key in media_group_storage[user_id]:
        data = media_group_storage[user_id][key]

        try:
            if isinstance(data, str):
                data = json.loads(data)

            media = None
            if isinstance(data, list):
                media = data
            elif isinstance(data, dict) and 'media' in data:
                media = data['media']

            if media and isinstance(media, list):
                # Отправка сообщения о начале сортировки
                progress_message = await query.message.reply_text(
                    text=f"Сортировка начата. Выбранный критерий: {criterion.capitalize()}\n\n"
                )

                # Сортировка всего списка media
                if criterion in {"dark", "light"}:
                    sorted_media = await sort_images_by_priority(media, criterion)
                elif criterion in {"saturated", "desaturated"}:
                    sorted_media = await sort_images_by_color_priority(media, criterion)
                elif criterion == "warm":
                    sorted_media = await sort_images_by_warm(media, criterion)
                else:
                    sorted_media = await sort_images_by_hue(media, criterion)

                # Завершение обновления прогресса

                # Остальная логика остаётся прежней
                first_caption = media[0].get('caption')
                first_parse_mode = media[0].get('parse_mode')

                sorted_media[0]['caption'] = first_caption
                sorted_media[0]['parse_mode'] = first_parse_mode

                for item in sorted_media[1:]:
                    item['caption'] = None
                    item['parse_mode'] = None

                media_group = [
                    InputMediaPhoto(
                        media=item['file_id'],
                        caption=item.get('caption', ''),
                        parse_mode=item.get('parse_mode', None)
                    ) for item in sorted_media if 'file_id' in item
                ]

                if media_group:
                    await context.bot.send_media_group(
                        chat_id=query.message.chat_id,
                        media=media_group
                    )

                # Сохраняем данные с учетом их типа
                if isinstance(data, list):
                    media_group_storage[user_id][key] = {"media": sorted_media}
                else:
                    data['media'] = sorted_media
                    media_group_storage[user_id][key] = data  # Сохраняем остальные поля

                save_media_group_data(media_group_storage, user_id)

                await query.message.reply_text(
                    text=f"✅ Изображения отсортированы:\n\nКритерий: {criterion}, Количество медиа: {len(sorted_media)}",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("В ТГ", callback_data=f"publish_{key}"),
                            InlineKeyboardButton("В ВК", callback_data=f"vkpub_{key}"),
                            InlineKeyboardButton("В X.com", callback_data=f"twitterpub_{key}"),
                            InlineKeyboardButton("Удалить", callback_data=f"yrrasetag_{key}"),  
                        ],
                        [
                            InlineKeyboardButton("🌠 Предложить этот пост в Анемон 🌠", callback_data=f"share_{key}")
                        ],                        
                        [
                            InlineKeyboardButton("🔄 Случайно перемешать 🔄", callback_data=f"shuffle_{key}")
                        ],
                        [
                            InlineKeyboardButton("🎨 Сортировать по палитре 🎨", callback_data=f"palettesort_{key}")
                        ],
                        [
                            InlineKeyboardButton("📔 Сохранить в папку 📔", callback_data=f"snooze_with_tag_{key}")
                        ],                                                          
                        [
                            InlineKeyboardButton("Поменять 2 изображения местами", callback_data=f"swapimages_{key}")
                        ],
                        [
                            InlineKeyboardButton("❌ Удалить 1 изображение ❌", callback_data=f"filedelete_{key}")
                        ],
                        [
                            InlineKeyboardButton("🗂 Посмотреть папки 🗂", callback_data="scheduled_by_tag")
                        ],
                        [
                            InlineKeyboardButton("🌌В главное меню🌌", callback_data='restart')
                        ],                        
                    ])
                )
            else:
                await query.message.reply_text("🚫 Ошибка: 'media' не найдено или некорректного формата.")
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            await query.message.reply_text(f"🚫 Ошибка обработки данных: {e}")
    else:
        await query.message.reply_text("🚫 Запись не найдена.")



import requests
from vk_api import VkApi
from vk_api.utils import get_random_id






def extract_text_before_first_link(caption: str) -> str:
    """
    Извлекает текст из подписи до первой гиперссылки и удаляет указанные HTML-теги,
    оставляя их содержимое.
    """
    # Удаляем указанные HTML-теги, оставляя их содержимое
    tags_to_remove = [
        r"</?b>",                       # <b> и </b>
        r"</?i>",                       # <i> и </i>
        r"</?u>",                       # <u> и </u>
        r"</?s>",                       # <s> и </s>
        r"</?span\s+class=\"tg-spoiler\">",  # <span class="tg-spoiler"> и </span>
        r"</?code>",                    # <code> и </code>
    ]
    
    # Объединяем паттерны в одно регулярное выражение
    combined_pattern = "|".join(tags_to_remove)
    
    # Удаляем указанные теги, оставляя их содержимое
    cleaned_caption = re.sub(combined_pattern, "", caption, flags=re.DOTALL)
    
    # Извлекаем текст до первой гиперссылки
    match = re.split(r'<a\s+href="[^"]+">', cleaned_caption, maxsplit=1)
    
    if match:
        return match[0].strip()  # Возвращаем текст до первого <a>, удаляя лишние пробелы
    return caption  # Если ссылки нет, возвращаем оригинальную подпись
def format_caption_for_vk(caption: str) -> str:
    """
    Форматирует caption для публикации в VK.
    1. Удаляет ссылки на Telegraph.
    2. Упорядочивает ссылки в формате:
       Ссылки:
       • название - ссылка
    3. Если ссылки отсутствуют или остался только текст, возвращает его без изменений.
    """

    # Удаляем ссылки на Telegraph
    caption = re.sub(r'<a\s+href="https://telegra.ph/[^"]+">[^<]+</a>', '', caption)

    # Извлекаем все ссылки
    links = re.findall(r'<a\s+href="([^"]+)">([^<]+)</a>', caption)
    
    # Формируем текст для ссылок, исключая пустые или некорректные ссылки
    links_text = ""
    if links:
        valid_links = [f"• {text.strip()} - {url.strip()}" for url, text in links if text.strip() and url.strip()]
        if valid_links:
            links_text = "Ссылки:\n" + "\n".join(valid_links)

    # Убираем ссылки из текста
    caption_without_links = re.sub(r'<a\s+href="[^"]+">[^<]+</a>', '', caption).strip()

    # Удаляем лишние символы "•", оставшиеся без текста
    caption_without_links = re.sub(r'\s*•\s*', ' ', caption_without_links).strip()

    # Если нет ссылок и остался только текст, вернуть его
    if not links_text:
        return caption_without_links.strip()

    # Формируем итоговый caption
    formatted_caption = caption_without_links.strip()
    if formatted_caption:
        formatted_caption += "\n\n"  # Добавляем отступ перед "Ссылки:"
    formatted_caption += links_text

    # Убираем лишние пустые строки
    formatted_caption = re.sub(r'\n\s*\n', '\n', formatted_caption).strip()

    return formatted_caption
    


async def handle_vk_keys_input(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    message_text = update.message.text

    try:
        # Ожидается формат: <owner_id> <token>
        owner_id, token = map(str.strip, message_text.split(maxsplit=1))
        save_vk_keys_to_firebase(user_id, owner_id, token)
        del waiting_for_vk[user_id]  # Убираем из состояния ожидания
        await update.message.reply_text("✅ Данные для публикации в ВК успешно сохранены.")
    except ValueError:
        await update.message.reply_text("🚫 Ошибка: Укажите ID группы и токен через пробел.")
    except Exception as e:
        await update.message.reply_text(f"🚫 Ошибка сохранения данных: {e}")






async def handle_vkpub_button(update, context):
    """Обработка кнопки публикации поста в ВКонтакте."""
    query = update.callback_query
    await query.answer()

    loading_message = await query.message.reply_text("📤 Пост переносится в ВК, ожидайте...")

    if not query.data.startswith("vkpub_"):
        await loading_message.edit_text("🚫 Неверный формат callback данных.")
        return

    # --- Извлечение данных из callback ---
    _, user_id_str, message_id_str = query.data.split('_', maxsplit=2)
    user_id = int(user_id_str)
    message_id = int(message_id_str)
    key = f"{user_id}_{message_id}"

    # --- Получаем медиагруппу из Firebase ---
    media_group_storage = load_publications_from_firebase()
    user_publications = media_group_storage.get(str(user_id), {})
    media_group_data = user_publications.get(key)

    if not media_group_data:
        await loading_message.edit_text("🚫 Ошибка: Данные о медиагруппе не найдены.")
        return

    media_items = media_group_data.get("media", [])
    if not media_items or not isinstance(media_items, list):
        await loading_message.edit_text("🚫 Ошибка: Медиагруппа пуста или имеет некорректный формат.")
        return

    image_urls = [item.get("file_id") for item in media_items if "file_id" in item]
    if not image_urls:
        await loading_message.edit_text("🚫 Ошибка: Ссылки на изображения отсутствуют.")
        return

    # --- Проверка VK-ключей ---
    vk_keys_ref = db.reference(f'users_publications/vk_keys/{user_id}')
    vk_keys = vk_keys_ref.get()
    if not vk_keys:
        await loading_message.edit_text(
            "В данный момент у вас не настроена публикация в вашу ВК группу. "
            "Для этого вам нужно получить два значения - ID вашей вк группы и токен.\n\n "
            'Токен вы можете получить тут: vkhost.github.io\n'
            'Для этого перейдите по указанной ссылке и следуйте инструкциям указанным там, в качестве приложения выберите VKадмин\n\n'
            'ID группы можно узнать из адресной строки, из настроек группы. либо тут regvk.com/id/\n\n'
            'Когда у вас будут и ID и токен, отправьте их сюда разделив пробелом или новой строкой.\nТак:\n'
            '<pre>IDгруппы токен</pre>\n'
            'Или так:\n'
            '<pre>IDгруппы\n'
            'токен</pre>'                                    
            ,
            parse_mode="HTML"
        )
        if user_id not in waiting_for_vk:
            waiting_for_vk[user_id] = True         
        return

    token = vk_keys.get("token")
    owner_id = vk_keys.get("owner_id")
    if not token or not owner_id:
        await loading_message.edit_text("🚫 Ошибка: Некорректные данные для ВК. Проверьте настройки.")
        return

    # --- Авторизация ---
    vk_session = VkApi(token=token)
    vk = vk_session.get_api()

    # --- Подготовка подписи ---
    first_caption = media_items[0].get("caption", "")
    cleaned_caption = extract_text_before_first_link(first_caption)
    formatted_caption = format_caption_for_vk(first_caption)

    # --- Загрузка изображений ---
    try:
        # Получаем один upload_url для всех изображений
        upload_url = vk.photos.getWallUploadServer(group_id=owner_id)['upload_url']
        uploaded_photos = []

        async with aiohttp.ClientSession() as session:
            for url in image_urls:
                photo = await upload_photo_to_vk(vk, url, owner_id, formatted_caption, session, upload_url)
                uploaded_photos.append(f"photo{photo['owner_id']}_{photo['id']}")
                await asyncio.sleep(random.uniform(0.8, 1.9))  # дополнительная пауза для стабильности

    except Exception as e:
        await loading_message.edit_text(f"🚫 Ошибка загрузки изображений в ВК: {e}")
        return

    # --- Публикация поста ---
    try:
        if int(owner_id) > 0:
            owner_id = -int(owner_id)

        vk.wall.post(
            owner_id=int(owner_id),
            from_group=1,
            message=html.unescape(cleaned_caption),
            attachments=",".join(uploaded_photos),
            random_id=get_random_id(),
            primary_attachments_mode="grid"
        )

        await loading_message.edit_text("✅ Пост успешно опубликован в ВКонтакте")

    except Exception as e:
        await loading_message.edit_text(f"🚫 Ошибка публикации поста в ВК: {e}")


# Настройка логирования
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%H:%M:%S')

async def upload_photo_to_vk(vk, image_url, group_id, caption, session, upload_url, max_retries=5, delay=2):
    """
    Асинхронно загружает фото в группу ВКонтакте с повторными попытками при ошибках.
    В случае ошибки upload_url обновляется.
    """
    for attempt in range(1, max_retries + 1):
        start_time = time.strftime("%H:%M:%S")
        try:
            logging.info(f"🔄 Попытка {attempt}/{max_retries} загрузить {image_url}")

            # 1️⃣ Скачиваем изображение
            async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status != 200:
                    raise ValueError(f"Ошибка загрузки: HTTP {resp.status}")
                image_data = await resp.read()

            # 2️⃣ Формируем форму для VK
            form = aiohttp.FormData()
            form.add_field('photo', image_data, filename='image.jpg', content_type='image/jpeg')

            # 3️⃣ Отправляем изображение на VK
            async with session.post(upload_url, data=form, timeout=aiohttp.ClientTimeout(total=30)) as upload_resp:
                text = await upload_resp.text()

                # VK иногда отдаёт HTML при перегрузке
                if "<html" in text.lower():
                    raise ValueError("VK вернул HTML (таймаут/ошибка сервера)")

                try:
                    upload_json = await upload_resp.json(content_type=None)
                except Exception:
                    raise ValueError(f"Ошибка декодирования JSON. Ответ: {text[:200]}")

            if not upload_json.get('photo') or not upload_json.get('server') or not upload_json.get('hash'):
                raise ValueError(f"Некорректный ответ VK: {upload_json}")

            # 4️⃣ Сохраняем фото на стене
            await asyncio.sleep(random.uniform(0.4, 0.9))
            saved_photo = vk.photos.saveWallPhoto(
                group_id=group_id,
                photo=upload_json['photo'],
                server=upload_json['server'],
                hash=upload_json['hash'],
                caption=caption
            )[0]

            logging.info(f"✅ Фото успешно загружено: {image_url}")
            return saved_photo

        except Exception as e:
            logging.info(f"⚠️ Ошибка на попытке {attempt}: {e}")

            # Если ошибка на загрузке или VK ответил HTML — пробуем новый upload_url
            if attempt < max_retries:
                try:
                    upload_url = vk.photos.getWallUploadServer(group_id=group_id)['upload_url']
                    logging.info("🔁 Обновлён upload_url перед новой попыткой.")
                except Exception as url_err:
                    logging.info(f"⚠️ Ошибка при обновлении upload_url: {url_err}")

                await asyncio.sleep(delay + random.uniform(0.5, 1.5))
                delay *= 1.6  # увеличиваем задержку экспоненциально
            else:
                raise ValueError(f"❌ Ошибка загрузки {image_url} после {max_retries} попыток: {e}")

import tweepy

# Обработчик кнопки публикации в Twitter
async def handle_twitterpub_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    loading_message = await query.message.reply_text("📤 Пост переносится в Twitter, ожидайте...")
    
    if not query.data.startswith("twitterpub_"):
        await loading_message.edit_text("🚫 Неверный формат callback данных.")
        return

    _, user_id_str, message_id_str = query.data.split('_', maxsplit=2)
    user_id = int(user_id_str)
    message_id = int(message_id_str)
    key = f"{user_id}_{message_id}"

    # Загрузка данных из Firebase
    global media_group_storage
    media_group_storage = load_publications_from_firebase()
    user_publications = media_group_storage.get(str(user_id), {})
    media_group_data = user_publications.get(key)

    if not media_group_data:
        await loading_message.edit_text("🚫 Ошибка: Данные о медиагруппе не найдены.")
        return

    media_items = media_group_data.get("media", [])
    if not media_items or not isinstance(media_items, list):
        await loading_message.edit_text("🚫 Ошибка: Медиагруппа пуста или имеет некорректный формат.")
        return

    # Извлекаем ссылки на изображения и caption
    image_urls = [item.get("file_id") for item in media_items if "file_id" in item]
    first_caption = media_items[0].get("caption", "")
    cleaned_caption = extract_text_before_first_link(first_caption)

    # Проверяем наличие API ключей Twitter
    twitter_keys_ref = db.reference(f'users_publications/twitter_keys/{user_id}')
    twitter_keys = twitter_keys_ref.get()

    if not twitter_keys:
        await loading_message.edit_text(
            "У вас не настроена публикация в Twitter.\n"
            "Отправьте API ключи с разрешениями на запись в формате:\n"
            "<pre>api_key api_secret access_token access_token_secret</pre>"
            "Получить их можно на сайте developer.x.com, подробнее можете спросить у любой нейросети или у разработчика бота через команду /send (мне лень писать инструкцию, всё равно пользоваться этой кнопкой никто кроме меня не будет.). Для перезапуска введите /resstart",
            parse_mode="HTML"
        )
        if user_id not in waiting_for_twitter:
            waiting_for_twitter[user_id] = True
        return

    api_key = twitter_keys["api_key"]
    api_secret = twitter_keys["api_secret"]
    access_token = twitter_keys["access_token"]
    access_token_secret = twitter_keys["access_token_secret"]
    bearer_token = twitter_keys.get("bearer_token")  # Необходим для API v2 (если есть)

    try:
        # Аутентификация в Twitter API v2
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )

        # Аутентификация в API v1.1 (нужна для загрузки медиа)
        auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
        api = tweepy.API(auth, wait_on_rate_limit=True)
    except Exception as e:
        await loading_message.edit_text(f"🚫 Ошибка авторизации в Twitter: {e}")
        return

    # Если есть изображения, загружаем их и отправляем твит с медиа
    uploaded_media_ids = []
    if image_urls:
        try:
            for url in image_urls:
                media_id = await upload_photo_to_twitter(api, url)
                if media_id:
                    uploaded_media_ids.append(media_id)
        except Exception as e:
            await loading_message.edit_text(f"🚫 Ошибка загрузки изображений в Twitter: {e}")
            return

    try:
        if uploaded_media_ids:
            client.create_tweet(text=cleaned_caption, media_ids=uploaded_media_ids)
        else:
            client.create_tweet(text=cleaned_caption)

        await loading_message.edit_text("✅ Пост успешно опубликован в Twitter")
    except Exception as e:
        await loading_message.edit_text(f"🚫 Ошибка публикации в Twitter: {e}")

async def upload_photo_to_twitter(api, image_url):
    """Загружает изображение в Twitter и возвращает media_id."""
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            if response.status != 200:
                raise Exception(f"Ошибка загрузки изображения: HTTP {response.status}")
            image_data = await response.read()

    # Загрузка изображения в Twitter (API v1.1, так как API v2 не поддерживает)
    media = api.media_upload(filename="image.jpg", file=BytesIO(image_data))
    return media.media_id











async def unknown_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id not in user_data:
        await update.message.reply_text('🚫Неизвестное сообщение. Пожалуйста, отправьте ссылку на автора, имя автора или изображение. В случае если это сообщение повторяется нажмите /restart')
    else:
        # Обработка сообщений в процессе
        if user_data[user_id]['status'] == 'awaiting_artist_link':
            await handle_artist_link(update, context)
        elif user_data[user_id]['status'] == 'awaiting_author_name':
            await handle_author_name(update, context)
        elif user_data[user_id]['status'] == 'awaiting_image':
            await handle_image(update, context)
            
# Функция для разбиения списка изображений на группы по 10
def chunk_images(images, chunk_size=10):
    for i in range(0, len(images), chunk_size):
        yield images[i:i + chunk_size]

TELEGRAM_API_TIMEOUT = 20  # Увеличьте время ожидания        



async def send_mode(update: Update, context: CallbackContext) -> None:
    """Включение режима дублирования сообщений."""
    user_id = update.message.from_user.id
    if user_id not in users_in_send_mode:
        users_in_send_mode[user_id] = True    
    await update.message.reply_text('🔄 Режим прямой связи включен. Все последующие сообщения будут дублироваться администрации. Для завершения режима введите /fin')
    
async def fin_mode(update: Update, context: CallbackContext) -> None:
    """Выключение режима дублирования сообщений и возврат к изначальной логике."""

    try:     
        user_id = update.effective_user.id

        await update.message.reply_text('✅ Режим пересылки сообщений администрации отключен. Бот вернулся к своему основному режиму работы.')

    except Exception as e:
        await update.message.reply_text(f"🚫 Ошибка сохранения данных: {e}")
    finally:
        del users_in_send_mode[user_id]
from telegram import InputMediaPhoto, InputMediaVideo, InputMediaDocument

async def duplicate_message(update: Update, context: CallbackContext) -> None:
    """Дублирование сообщений пользователя в группу, включая медиа-группы, одиночные сообщения и документы."""
    user = update.message.from_user
    user_name = user.username if user.username else user.full_name
    user_id = user.id  # Получаем user_id
    message_prefix = f"{user_name} (ID: {user_id}) отправил сообщение:"

    if user.id in users_in_send_mode:
        # Если сообщение является частью медиа-группы
        if update.message.media_group_id:
            media_group = []
            messages = await context.bot.get_updates(offset=update.update_id - 10)  # Получаем несколько предыдущих сообщений для сборки медиа-группы

            # Фильтрация сообщений с тем же media_group_id
            for message in messages:
                if message.message.media_group_id == update.message.media_group_id:
                    if message.message.photo:
                        media_group.append(InputMediaPhoto(message.message.photo[-1].file_id, caption=message.message.caption if message.message.caption else ""))
                    elif message.message.video:
                        media_group.append(InputMediaVideo(message.message.video.file_id, caption=message.message.caption if message.message.caption else ""))
                    elif message.message.document:
                        media_group.append(InputMediaDocument(message.message.document.file_id, caption=message.message.caption if message.message.caption else ""))

            # Отправляем медиа-группу, если она есть
            if media_group:
                await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=message_prefix)
                await context.bot.send_media_group(chat_id=GROUP_CHAT_ID, media=media_group)
                await update.message.reply_text("Сообщение успешно отправлено администрации. Для завершения режима дублирования введите /fin")

        # Обработка одиночных текстовых сообщений
        elif update.message.text:
            await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=f"{message_prefix}\n{update.message.text}")
            await update.message.reply_text("Сообщение успешно отправлено администрации. Для завершения режима дублирования введите /fin")

        # Обработка одиночных фото
        elif update.message.photo:
            photo = update.message.photo[-1].file_id  # Получаем последнюю фотографию с наибольшим разрешением
            await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=message_prefix)
            await context.bot.send_photo(chat_id=GROUP_CHAT_ID, photo=photo, caption=update.message.caption)
            await update.message.reply_text("Сообщение успешно отправлено администрации. Для завершения режима дублирования введите /fin")

        # Обработка одиночных документов (включая изображения, отправленные как файл)
        elif update.message.document:
            doc = update.message.document.file_id
            await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=message_prefix)
            await context.bot.send_document(chat_id=GROUP_CHAT_ID, document=doc, caption=update.message.caption)
            await update.message.reply_text("Сообщение успешно отправлено администрации. Для завершения режима дублирования введите /fin")

        # Обработка одиночных видео
        elif update.message.video:
            video = update.message.video.file_id
            await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=message_prefix)
            await context.bot.send_video(chat_id=GROUP_CHAT_ID, video=video, caption=update.message.caption)
            await update.message.reply_text("Сообщение успешно отправлено администрации. Для завершения режима дублирования введите /fin")

        # Обработка стикеров
        elif update.message.sticker:
            await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=message_prefix)
            await context.bot.send_sticker(chat_id=GROUP_CHAT_ID, sticker=update.message.sticker.file_id)
            await update.message.reply_text("Сообщение успешно отправлено администрации. Для завершения режима дублирования введите /fin")

        # Обработка аудио
        elif update.message.audio:
            await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=message_prefix)
            await context.bot.send_audio(chat_id=GROUP_CHAT_ID, audio=update.message.audio.file_id, caption=update.message.caption)
            await update.message.reply_text("Сообщение успешно отправлено администрации. Для завершения режима дублирования введите /fin")

        # Добавьте обработку других типов сообщений по мере необходимости
    else:
        # Если пользователь не в режиме дублирования, продолжаем с основной логикой
        await start(update, context)








def load_cookies_from_file(path: str) -> dict:
    cookies = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) < 7:
                continue
            name = parts[5]
            value = parts[6]
            cookies[name] = value
    return cookies

async def handle_ozon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        keyboard = [
            [
                InlineKeyboardButton("Мои товары", callback_data="myozon_items")
            ]
        ]        
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "📊Если вы хотите добавить новый товар то укажите на него ссылку после команды <code>/ozon</code>\n"
            "Формата:\n"
            "<pre>/ozon Ваша_Ссылка</pre>\n"
            "Пример:\n"
            "<pre>/ozon https://www.ozon.ru/product/filtr-dlya-ochistki-vody-pod-moyku-barer-master-osmo-50-bez-krana-pyatistupenchatyy-c-tehnologiey-1388575614/</pre>\n\n"
            "Либо вы можете посмотреть уже добавленные вами товары и графики по ним по кнопке ниже:",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        logger.info("Пользователь не указал ссылку после команды /ozon")
        return

    user_url = context.args[0]
    logger.info(f"Получена ссылка от пользователя: {user_url}")

    if "ozon.ru" not in user_url:
        await update.message.reply_text("Пожалуйста, укажите корректную ссылку на ozon.")
        logger.info(f"Получена некорректная ссылка: {user_url}")
        return

    # Генерируем уникальный ключ для этого взаимодействия с продуктом для хранения в контексте
    # Использование самого URL может быть слишком длинным или проблематичным для callback_data позже
    # Более простой способ - использовать user_url как ключ в user_data напрямую, если это работает для вашего контекста.
    # Для callback_data мы передадим короткий, уникальный ID.
    product_interaction_id = str(uuid.uuid4()).split('-')[0] # Короткий уникальный ID

    api_url = f"https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2?url={user_url}"
    logger.info(f"Сформирован API-запрос: {api_url}")
    #cookie_path = os.path.join("config", "ozon.txt") # Убедитесь, что этот путь корректен
    cookie_path = "/etc/secrets/ozon.txt"
    logger.info(f"cookie_path: {cookie_path}")
    cookies = load_cookies_from_file(cookie_path)
    logger.info(f"cookies: {cookies if cookies else 'Куки не загружены'}")

    try:
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(api_url) as response:
                logger.info(f"Ответ от API Ozon: статус {response.status}")
                if response.status != 200:
                    # Попытка получить больше информации об ошибке
                    error_text = await response.text()
                    logger.error(f"Ошибка API Ozon {response.status}: {error_text[:500]}")
                    await update.message.reply_text(f"Ошибка при получении данных с Ozon: {response.status}. Попробуйте обновить cookies.")
                    return
                data = await response.json()

        widget_states_raw = data.get("widgetStates", {})
        logger.info(f"Извлечён widgetStates: {list(widget_states_raw.keys())[:5]}...")

        price_data = None
        for key, value in widget_states_raw.items():
            if key.startswith("webPrice") and isinstance(value, str):
                try:
                    price_data = json.loads(value)
                    logger.info(f"Найден webPrice по ключу: {key}")
                    break
                except json.JSONDecodeError:
                    logger.info(f"Ошибка декодирования JSON по ключу: {key}")
                    continue

        if not price_data:
            await update.message.reply_text("Не удалось найти информацию о цене. Структура ответа Ozon могла измениться.")
            logger.warning(f"Не найден webPrice для {user_url}. Ключи Data: {data.keys()}. Ключи WidgetStates: {list(widget_states_raw.keys())}")
            return
        
        # Очистка цен от символов валюты и неразрывных пробелов
        card_price_raw = price_data.get("cardPrice", "—").replace('₽', '').replace('\u2009', '').replace('&nbsp;', '').strip()
        price_raw = price_data.get("price", "—").replace('₽', '').replace('\u2009', '').replace('&nbsp;', '').strip()
        original_price_raw = price_data.get("originalPrice", "—").replace('₽', '').replace('\u2009', '').replace('&nbsp;', '').strip()

        # Сохраняем None если цена "—", иначе строку с ценой
        card_price = card_price_raw if card_price_raw != "—" else None
        price = price_raw if price_raw != "—" else None
        original_price = original_price_raw # Старая цена может быть "—"

        title_candidates = [
            data.get("seo", {}).get("title", ""),
            data.get("seo", {}).get("metaTitle", ""),
            data.get("seo", {}).get("ogTitle", "")
        ]
        title = next((t for t in title_candidates if t), "Название товара не найдено")
        title = title.split(" купить")[0] # Очищаем заголовок

        # Сохраняем данные для потенциального отслеживания
        if 'ozon_tracking_temp' not in context.user_data:
            context.user_data['ozon_tracking_temp'] = {}
        context.user_data['ozon_tracking_temp'][product_interaction_id] = {
            "url": user_url,
            "title": title,
            "card_price": card_price, # Храним как строку или None
            "price": price,           # Храним как строку или None
        }

        response_text = (
            f"📦 <b>{title}</b>\n\n"
            f"💳 Цена с Ozon Картой: <b>{card_price_raw}</b>\n" # Отображаем исходные строки
            f"💰 Цена без карты: <b>{price_raw}</b>\n"
            f"📉 Старая цена: <s>{original_price}</s>"
        )

        keyboard = [
            [
                InlineKeyboardButton("Сохранить для отслеживания 🎯", callback_data=f"ozon_track_start_{product_interaction_id}")
            ],
            [
                InlineKeyboardButton("Мои Отслеживания 📒", callback_data="myozon_items")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_html(response_text, reply_markup=reply_markup)

    except aiohttp.ClientError as e:
        logger.error(f"Aiohttp ClientError при запросе к Ozon: {e}")
        await update.message.reply_text(f"Сетевая ошибка при доступе к Ozon: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError при обработке ответа Ozon: {e}")
        await update.message.reply_text("Ошибка при обработке данных от Ozon. Формат ответа мог измениться.")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка в handle_ozon: {e}", exc_info=True)
        await update.message.reply_text(f"Произошла ошибка: {str(e)}")



async def ozon_delete_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    product_id = query.data.split("_")[-1]

    success = delete_ozon_product_firebase(user_id, product_id)

    if not success:
        await query.answer("Ошибка при удалении товара.", show_alert=True)
        return

    # Получаем обновлённый список товаров
    user_ref = db.reference(f"ozon_prices/{user_id}/tracked_items/")
    tracked_items = user_ref.get() or []

    # Отрисовываем новую клавиатуру (по умолчанию страница 0)
    keyboard = build_keyboard(tracked_items, page=0)

    await query.edit_message_reply_markup(reply_markup=keyboard)


MAX_ITEMS_PER_PAGE = 5

def format_price_table(tracked_items, page):
    start = page * MAX_ITEMS_PER_PAGE
    end = start + MAX_ITEMS_PER_PAGE
    subset = tracked_items[start:end]

    lines = ["Название  | нач.₽  | тек.₽  | мин.₽"]

    for item in subset:
        try:
            if not isinstance(item, dict):
                continue  # пропустить, если item не словарь

            title = str(item.get('title', '—'))[:10].ljust(10)

            try:
                base = int(float(item.get('base_price_when_set', 0)))
            except (ValueError, TypeError):
                base = 0

            price_entries = item.get('price_history') or []
            valid_prices = []

            latest_card_price = base  # по умолчанию
            for entry in reversed(price_entries):
                if isinstance(entry, dict):
                    try:
                        raw_price = str(entry.get('card_price', base)).replace(' ', '').replace(',', '.')
                        try:
                            price = int(float(raw_price))
                        except ValueError:
                            continue
                        latest_card_price = price
                        break  # нашли последний валидный — выходим
                    except (ValueError, TypeError):
                        continue

            # найти минимальную цену
            for entry in price_entries:
                if isinstance(entry, dict):
                    try:
                        raw_price = str(entry.get('card_price', base)).replace(' ', '').replace(',', '.')
                        try:
                            price = int(float(raw_price))
                        except ValueError:
                            continue
                        valid_prices.append(price)
                    except (ValueError, TypeError):
                        continue

            min_card_price = min(valid_prices) if valid_prices else base

            line = f"{title}|{base:^8}|{latest_card_price:^8}|{min_card_price:^8}"
            lines.append(line)

        except Exception as e:
            print("Ошибка на товаре:", item.get("title") if isinstance(item, dict) else str(item))
            continue  # не прерывать выполнение из-за одного товара

    return '<pre>' + '\n'.join(lines) + '</pre>'



def build_keyboard(tracked_items, page):
    MAX_ITEMS_PER_PAGE = 5
    start = page * MAX_ITEMS_PER_PAGE
    end = start + MAX_ITEMS_PER_PAGE
    subset = tracked_items[start:end]

    buttons = []
    for item in subset:
        title = item.get('title', '')[:20]
        product_id = item.get('item_id', '')
        is_active = item.get('is_active_tracking', False)
        threshold = item.get('notification_threshold_rub')

        # Галочка для активных
        if is_active:
            title = f"✅ {title}"

        # ⬅️ Изменение: проверяем рубли, иначе проценты
        if isinstance(threshold, (int, float)) and threshold > 0:
            threshold_text = f"⏰: {threshold}"
        else:
            percent = item.get('notification_threshold_percent')  # ⬅️
            if isinstance(percent, (int, float)) and percent > 0:  # ⬅️
                threshold_text = f"⏰: {percent}%"  # ⬅️
            else:
                threshold_text = "⏰: нет"

        buttons.append([
            InlineKeyboardButton(title, callback_data=f"ozon_view_stat_{product_id}"),
            InlineKeyboardButton(threshold_text, callback_data=f"changenotif_{product_id}"),
            InlineKeyboardButton("Удалить", callback_data=f"ozon_delete_{product_id}"),
        ])

    # Навигация по страницам
    nav_buttons = []
    total_pages = (len(tracked_items) - 1) // MAX_ITEMS_PER_PAGE + 1
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"ozon_page_{page - 1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"ozon_page_{page + 1}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    return InlineKeyboardMarkup(buttons)



async def ozon_message_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.delete()



import io
import matplotlib.pyplot as plt
from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

async def ozon_view_stat(update, context):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if not data.startswith("ozon_view_stat_"):
        return

    product_id = data.replace("ozon_view_stat_", "")
    logger.info(f"product_id: {product_id}")

    # Шаг 1: отправка временного сообщения
    waiting_message = await query.message.reply_text("⏳ Подождите, строю график...")

    try:
        product_data = load_ozon_product_firebase(user_id, product_id)
        if not product_data:
            await waiting_message.edit_text(
                "❌ Не удалось загрузить данные о товаре.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Закрыть окно", callback_data="ozondelete_msg")]
                ])
            )
            return

        title = product_data.get("title", "Без названия")
        url = product_data.get("url", "")
        initial_price = float(product_data.get("initial_card_price_at_tracking", 0))

        price_history = product_data.get("price_history", [])
        if not price_history:
            await waiting_message.edit_text(
                "❌ Нет истории цен для этого товара.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Закрыть окно", callback_data="ozondelete_msg")]
                ])
            )
            return

        # Фильтрация некорректных записей
        price_history_filtered = [
            p for p in price_history
            if p and "timestamp_utc" in p and "card_price" in p and p["card_price"]
        ]

        valid_price_data = []
        for p in price_history_filtered:
            try:
                date = datetime.fromisoformat(p["timestamp_utc"])
                price = float(str(p["card_price"]).replace(' ', '').replace(',', '.'))
                valid_price_data.append((date, price))
            except (ValueError, TypeError):
                continue  # Пропускаем некорректные записи

        if not valid_price_data:
            await waiting_message.edit_text(
                "❌ Нет корректной истории цен для этого товара.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Закрыть окно", callback_data="ozondelete_msg")]
                ])
            )
            return

        # Сортировка по дате
        valid_price_data.sort(key=lambda x: x[0])
        dates, prices = zip(*valid_price_data)

        current_price = prices[-1]
        min_price = min(prices)
        price_diff = initial_price - current_price

        # Построение графика
        fig, ax = plt.subplots()
        ax.plot(dates, prices, marker='o', linestyle='-', color='blue')
        ax.set_title("Динамика цены")
        ax.set_xlabel("Дата")
        ax.set_ylabel("Цена, ₽")
        ax.grid(True)
        fig.autofmt_xdate()

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close(fig)

        stat_text = (
            f"📦 <b>{title}</b>\n\n"
            f"🔹 <b>Изначальная цена:</b> {initial_price} ₽\n"
            f"🔸 <b>Текущая цена:</b> {current_price} ₽\n"
            f"📉 <b>Минимальная цена:</b> {min_price} ₽\n"
            f"↘️ <b>Разница:</b> {price_diff:.2f} ₽\n"
            f"🔗 <a href='{url}'>Ссылка на товар</a>"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Закрыть окно", callback_data="ozondelete_msg")]
        ])

        await waiting_message.delete()

        await query.message.reply_photo(
            photo=buf,
            caption=stat_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    except Exception as e:
        logger.exception("Ошибка при построении графика:")
        await waiting_message.edit_text(
            "❌ Произошла ошибка при построении графика.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Закрыть окно", callback_data="ozondelete_msg")]
            ])
        )



async def show_tracked_items(update: Update, context: ContextTypes.DEFAULT_TYPE, page=0):
    user = update.effective_user
    if not user:
        if update.callback_query:
            user = update.callback_query.from_user
        else:
            return  # или выбросить исключение

    user_id = str(user.id)
    user_data = context.application.bot_data.get(user_id, {})
    tracked_items = load_ozon_tracking_from_firebase(user_id)
    logger.info(f"tracked_items: {tracked_items}")
    if not tracked_items:
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text("У вас пока нет отслеживаемых товаров.")
        elif update.message:
            await update.message.reply_text("У вас пока нет отслеживаемых товаров.")
        return

    text = format_price_table(tracked_items, page)
    keyboard = build_keyboard(tracked_items, page)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")
    elif update.message:
        await update.message.reply_html(text, reply_markup=keyboard)




async def ozon_change_threshold_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        _, product_id = query.data.split("_", 1)
    except ValueError:
        await query.edit_message_text("Ошибка: неверный формат команды изменения порога.")
        return

    user_id = str(query.from_user.id)
    tracked_items = load_ozon_tracking_from_firebase(user_id)

    # Ищем нужный товар
    item = next((x for x in tracked_items if x["item_id"] == product_id), None)
    if not item:
        await query.edit_message_text("Товар не найден в отслеживаемых.")
        return

    # Сохраняем во временное хранилище
    temp_data_store = context.user_data.setdefault("ozon_change_temp", {})
    temp_data_store[product_id] = item

    # Показываем клавиатуру с выбором порога
    threshold_options = [50, 100, 200, 300, 500, 1000, 2500, 5000, 10000, "5-10%", "10-20%", "20-30%", "30-40%", "40-50%"]
    keyboard = []
    row = []
    for th in threshold_options:
        row.append(InlineKeyboardButton(str(th), callback_data=f"ozon_update_thresh_{th}_{product_id}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("Уведомления не нужны 🚫", callback_data=f"ozon_update_thresh_0_{product_id}")
    ])

    await query.edit_message_text(
        text="Выберите новый порог уведомлений о снижении цены:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def ozon_update_threshold_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        # callback_data=f"ozon_update_thresh_{th}_{product_id}"
        # parts[0]=ozon, parts[1]=update, parts[2]=thresh, parts[3]=th, parts[4]=product_id
        parts = query.data.split("_", 4)
        threshold_str = parts[3]
        product_id = parts[4]
        # logger.info(f"ozon_update_threshold_callback: data='{query.data}', threshold_str='{threshold_str}', product_id='{product_id}'")
    except IndexError: # Если split вернул меньше 5 частей
        logger.error(f"ozon_update_threshold_callback: Неверный формат callback_data: {query.data}")
        await query.edit_message_text("Ошибка: не удалось прочитать данные для обновления порога.")
        return
    # Убрали int(threshold_str) отсюда, будем парсить ниже

    user_id = str(query.from_user.id)
    temp_data_store = context.user_data.get("ozon_change_temp", {})
    item = temp_data_store.get(product_id)

    if not item:
        logger.warning(f"ozon_update_threshold_callback: Временные данные для {product_id} не найдены (user {user_id}).")
        await query.edit_message_text("Временные данные не найдены. Попробуйте начать изменение порога заново.")
        return

    # Логика определения типа порога (аналогично ozon_set_threshold_callback)
    new_threshold_rub = 0
    new_threshold_percent = 0
    new_is_percent_threshold = False
    new_is_active_tracking = True # По умолчанию отслеживание активно

    if threshold_str == "0": # Уведомления не нужны
        new_is_active_tracking = False
    elif "%" in threshold_str:
        new_is_percent_threshold = True
        try:
            new_threshold_percent = int(threshold_str.split('-')[0].replace('%', ''))
            if new_threshold_percent <= 0:
                 await query.edit_message_text("Ошибка: процентное значение должно быть положительным.")
                 # Очищаем временные данные в случае ошибки, чтобы не застрять
                 temp_data_store.pop(product_id, None)
                 if not temp_data_store:
                     context.user_data.pop("ozon_change_temp", None)
                 return
        except ValueError:
            logger.error(f"Неверный формат процентного порога при обновлении: {threshold_str}")
            await query.edit_message_text("Ошибка: неверный формат процентного порога.")
            temp_data_store.pop(product_id, None)
            if not temp_data_store:
                context.user_data.pop("ozon_change_temp", None)
            return
    else: # Это абсолютное значение в рублях
        try:
            new_threshold_rub = int(threshold_str)
            if new_threshold_rub <= 0: # Должно быть >0, т.к. "0" обработан отдельно
                await query.edit_message_text("Ошибка: пороговое значение должно быть положительным.")
                temp_data_store.pop(product_id, None)
                if not temp_data_store:
                    context.user_data.pop("ozon_change_temp", None)
                return
        except ValueError:
            logger.error(f"Неверный формат абсолютного порога при обновлении: {threshold_str}")
            await query.edit_message_text("Ошибка: неверный формат числового порога.")
            temp_data_store.pop(product_id, None)
            if not temp_data_store:
                context.user_data.pop("ozon_change_temp", None)
            return

    # Обновляем поля в объекте item
    item["notification_threshold_rub"] = new_threshold_rub
    item["notification_threshold_percent"] = new_threshold_percent
    item["is_percent_threshold"] = new_is_percent_threshold
    item["is_active_tracking"] = new_is_active_tracking
    item["last_changed_utc"] = datetime.now(timezone.utc).isoformat()
    # Важно: base_price_when_set НЕ меняется при простом изменении порога.
    # Оно меняется только если пользователь выбирает "отслеживать от новой цены"
    # после срабатывания уведомления.

    # Сохраняем обратно в Firebase
    # Убедитесь, что update_ozon_tracking_item определена и работает
    update_success = update_ozon_tracking_item(user_id, product_id, item) 

    msg = ""
    if update_success:
        item_title_short = item.get('title', 'Товар')[:50]
        if not new_is_active_tracking:
            msg = f"Уведомления для товара «{item_title_short}...» отключены."
        elif new_is_percent_threshold:
            base_price_display = item.get('base_price_when_set', 'начальной')
            msg = (f"Порог для «{item_title_short}...» изменен: {new_threshold_percent}% "
                   f"(от базовой цены {base_price_display} ₽).")
        else: # Рублевый порог
            msg = f"Порог для «{item_title_short}...» изменен: {new_threshold_rub} руб."
    else:
        msg = "Ошибка при сохранении изменений. Попробуйте позже."

    # Удаляем временные данные
    temp_data_store.pop(product_id, None)
    if not temp_data_store: # если словарь стал пустым
        context.user_data.pop("ozon_change_temp", None)


    # Обновляем сообщение со списком отслеживаемых товаров
    # Убедитесь, что эти функции определены и работают
    tracked_items_after_update = load_ozon_tracking_from_firebase(user_id) 
    # Предполагается, что у вас есть система пагинации, page=0 может быть не всегда корректным
    # Возможно, потребуется передавать/сохранять текущую страницу пользователя
    current_page = context.user_data.get(f"ozon_list_page_{user_id}", 0) # Пример получения текущей страницы
    
    keyboard = build_keyboard(tracked_items_after_update, page=current_page)
    text_content = format_price_table(tracked_items_after_update, page=current_page)
    
    # Добавляем сообщение об успехе/ошибке ПЕРЕД таблицей.
    final_text = msg + "\n\n" + text_content

    await query.edit_message_text(text=final_text, reply_markup=keyboard, parse_mode="HTML")



# Обработчик команды "мои товары"
async def handle_my_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # update может быть как командой, так и callback_query
    # Нужно правильно получить update для передачи в show_tracked_items

    # Если это callback_query — у него другой объект update
    if update.callback_query:
        await update.callback_query.answer()  # закрыть "часики" на кнопке
        # Подменяем update, чтобы show_tracked_items работал как обычно
        await show_tracked_items(update, context, page=0)
    else:
        await show_tracked_items(update, context, page=0)

# Обработчик callback_data для смены страницы
async def handle_ozonpage_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    page = int(query.data.split('_')[-1])
    await show_tracked_items(update, context, page=page)



async def ozon_track_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Подтверждаем callback-запрос

    try:
        # callback_data=f"ozon_track_start_{product_interaction_id}"
        _, _, _, product_interaction_id = query.data.split("_", 3)
    except ValueError:
        logger.error(f"Неверный callback_data для ozon_track_start: {query.data}")
        await query.edit_message_text("Ошибка: неверные данные для отслеживания.")
        return

    temp_data_store = context.user_data.get('ozon_tracking_temp', {})
    logger.info(f"temp_data_store: {temp_data_store}")    
    product_details = temp_data_store.get(product_interaction_id)

    if not product_details:
        logger.warning(f"Временные данные не найдены для product_interaction_id: {product_interaction_id}")
        await query.edit_message_text("Не удалось найти данные о товаре для отслеживания. Попробуйте снова.")
        return

    threshold_options = [50, 100, 200, 300, 500, 1000, 2500, 5000, 10000, "5-10%", "10-20%", "20-35%", "30-40%", "40-50%"]
    keyboard = []
    row = []
    for th in threshold_options:
        # callback_data=f"ozon_set_thresh_{th}_{product_interaction_id}"
        row.append(InlineKeyboardButton(str(th), callback_data=f"ozon_set_thresh_{th}_{product_interaction_id}"))
        if len(row) == 3: # 3 кнопки в ряду
            keyboard.append(row)
            row = []
    if row: # Добавляем оставшиеся кнопки
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("Уведомления не нужны 🚫", callback_data=f"ozon_set_thresh_0_{product_interaction_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Хотите включить уведомления о понижении цены? Если да, то на сколько (в рублях от текущей цены с картой Ozon)?",
        reply_markup=reply_markup
    )




async def ozon_set_threshold_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        logging.info(f"Получен callback_data: {query.data}")
        parts = query.data.split("_", 4) # ozon_set_thresh_{th}_{product_interaction_id}
        logging.info(f"Разбито на части: {parts}")
        _, _, _, threshold_str, product_interaction_id = parts
        # threshold = int(threshold_str) # <-- Убираем эту строку, обработаем ниже
        logging.info(f"Строка порога: {threshold_str}, ID взаимодействия: {product_interaction_id}")
    except ValueError:
        logger.error(f"Неверный callback_data для ozon_set_threshold: {query.data}")
        await query.edit_message_text("Ошибка: неверные данные порога.")
        return

    user_id = query.from_user.id
    temp_data_store = context.user_data.get('ozon_tracking_temp', {})
    product_details = temp_data_store.get(product_interaction_id)

    if not product_details:
        logger.warning(f"Временные данные не найдены для product_interaction_id: {product_interaction_id} при установке порога.")
        await query.edit_message_text("Не удалось найти данные о товаре. Попробуйте снова.")
        return

    try:
        base_price_to_track = None
        card_price_val_str = product_details.get("card_price")
        price_val_str = product_details.get("price")
        if card_price_val_str:
            base_price_to_track = float(str(card_price_val_str).replace(' ', '').replace(',', '.'))
        elif price_val_str:
            base_price_to_track = float(str(price_val_str).replace(' ', '').replace(',', '.'))
        
        if base_price_to_track is None:
            await query.edit_message_text("Не удалось определить текущую цену для отслеживания.")
            logger.error(f"Не удалось определить базовую цену для отслеживания: {product_details}")
            return
    except ValueError as e:
        await query.edit_message_text("Ошибка в формате цены товара.")
        logger.error(f"ValueError при конвертации цены для отслеживания: {e}, детали: {product_details}")
        return

    current_time_iso = datetime.now(timezone.utc).isoformat()

    threshold_rub = 0
    threshold_percent = 0
    is_percent_threshold = False
    is_active_tracking = True # По умолчанию отслеживание активно, если выбран порог

    if threshold_str == "0": # Уведомления не нужны
        is_active_tracking = False
    elif "%" in threshold_str:
        is_percent_threshold = True
        try:
            # Берем первое число из диапазона, например "5" из "5-10%"
            threshold_percent = int(threshold_str.split('-')[0].replace('%', ''))
            if threshold_percent <= 0: # Процент должен быть положительным
                 await query.edit_message_text("Ошибка: процентное значение должно быть положительным.")
                 return
        except ValueError:
            logger.error(f"Неверный формат процентного порога: {threshold_str}")
            await query.edit_message_text("Ошибка: неверный формат процентного порога.")
            return
    else: # Это абсолютное значение в рублях
        try:
            threshold_rub = int(threshold_str)
            if threshold_rub <= 0: # Абсолютный порог тоже должен быть положительным, если это не "0"
                await query.edit_message_text("Ошибка: пороговое значение должно быть положительным.")
                return
        except ValueError:
            logger.error(f"Неверный формат абсолютного порога: {threshold_str}")
            await query.edit_message_text("Ошибка: неверный формат числового порога.")
            return

    item_to_save = {
        "item_id": str(uuid.uuid4()),
        "url": product_details["url"],
        "title": product_details["title"],
        "initial_card_price_at_tracking": product_details["card_price"],
        "initial_price_at_tracking": product_details["price"],
        "base_price_when_set": base_price_to_track,
        "notification_threshold_rub": threshold_rub, # Будет 0, если выбран процент
        "notification_threshold_percent": threshold_percent, # Будет 0, если выбраны рубли
        "is_percent_threshold": is_percent_threshold,
        "added_timestamp_utc": current_time_iso,
        "last_checked_timestamp_utc": current_time_iso,
        "is_active_tracking": is_active_tracking,
        "price_history": [{
            "timestamp_utc": current_time_iso,
            "card_price": product_details["card_price"],
            "price": product_details["price"]
        }]
    }

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Мои Отслеживания 📒", callback_data="myozon_items")]
    ])

    if save_ozon_tracking_to_firebase(user_id, item_to_save): # Убедитесь, что эта функция у вас определена
        if not is_active_tracking:
            message_text = f"Товар '{product_details['title'][:50]}...' сохранен. Уведомления о снижении цены отключены."
        elif is_percent_threshold:
            message_text = (
                f"Товар '{product_details['title'][:50]}...' сохранен! "
                f"Вы получите уведомление, если цена упадет на {threshold_percent}% или более "
                f"от текущей цены {base_price_to_track} ₽."
            )
        else: # Рублевый порог
            message_text = (
                f"Товар '{product_details['title'][:50]}...' сохранен! "
                f"Вы получите уведомление, если цена упадет на {threshold_rub} руб. или более."
            )
        await query.edit_message_text(message_text, reply_markup=keyboard)
    else:
        await query.edit_message_text(
            "Не удалось сохранить товар для отслеживания. Пожалуйста, попробуйте позже.",
            reply_markup=keyboard
        )

    if product_interaction_id in temp_data_store:
        del temp_data_store[product_interaction_id]
        if not temp_data_store:
             del context.user_data['ozon_tracking_temp']







async def fetch_ozon_product_data_for_check(url: str, cookies: dict):
    """Вспомогательная функция для получения текущих данных для данного URL Ozon."""
    api_url = f"https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2?url={url}"
    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.get(api_url) as response:
            if response.status == 200:
                data = await response.json()
                widget_states_raw = data.get("widgetStates", {})
                price_data_json = None
                for key, value in widget_states_raw.items():
                    if key.startswith("webPrice") and isinstance(value, str):
                        try:
                            price_data_json = json.loads(value)
                            break
                        except json.JSONDecodeError:
                            continue # Пропускаем, если JSON невалидный
                
                if price_data_json:
                    card_price_raw = price_data_json.get("cardPrice", "—").replace('₽', '').replace('\u2009', '').replace('&nbsp;', '').strip()
                    price_raw = price_data_json.get("price", "—").replace('₽', '').replace('\u2009', '').replace('&nbsp;', '').strip()
                    
                    current_card_price_float = None
                    current_price_float = None

                    try:
                        if card_price_raw != "—":
                            current_card_price_float = float(card_price_raw.replace(',', '.'))
                    except ValueError: 
                        logger.warning(f"Не удалось распознать цену по карте '{card_price_raw}' для {url}")
                    
                    try:
                        if price_raw != "—":
                            current_price_float = float(price_raw.replace(',', '.'))
                    except ValueError:
                        logger.warning(f"Не удалось распознать обычную цену '{price_raw}' для {url}")

                    return {
                        "card_price_str": card_price_raw if card_price_raw != "—" else None,
                        "price_str": price_raw if price_raw != "—" else None,
                        "current_card_price_float": current_card_price_float,
                        "current_price_float": current_price_float,
                    }
            else:
                error_text_short = await response.text()
                logger.error(f"Ошибка API Ozon при проверке {response.status} для {url}: {error_text_short[:200]}")
    return None


async def daily_ozon_price_check_job(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Запуск ежедневной проверки цен Ozon...")
    all_tracking_data_ref = db.reference("ozon_prices") # Убедитесь, что db определена
    all_users_tracking = all_tracking_data_ref.get()

    if not all_users_tracking:
        logger.info("Нет товаров для отслеживания.")
        return

    #cookie_path = os.path.join("config", "ozon.txt")
    cookie_path = "/etc/secrets/ozon.txt"
    cookies = load_cookies_from_file(cookie_path) # Убедитесь, что эта функция определена
    if not cookies:
        logger.error("Не удалось загрузить cookies для проверки цен Ozon. Проверка отменена.")
        return

    current_time_iso = datetime.now(timezone.utc).isoformat()

    for user_id_str, user_data in all_users_tracking.items():
        user_id = int(user_id_str)
        tracked_items = user_data.get("tracked_items", [])
        updated_items_for_user = []
        needs_db_update_for_user = False

        for item_index, item_copy in enumerate(tracked_items):
            item = dict(item_copy)
            if not item.get("is_active_tracking", False):
                updated_items_for_user.append(item)
                continue
            
            url = item.get("url")
            if not url:
                updated_items_for_user.append(item)
                continue
            
            logger.info(f"Проверка товара: {url} для пользователя {user_id}")
            current_price_info = await fetch_ozon_product_data_for_check(url, cookies) # Убедитесь, что эта функция определена
            
            item["last_checked_timestamp_utc"] = current_time_iso
            needs_db_update_for_user = True

            if current_price_info:
                if "price_history" not in item or not isinstance(item["price_history"], list):
                    item["price_history"] = []
                
                item["price_history"].append({
                    "timestamp_utc": current_time_iso,
                    "card_price": current_price_info["card_price_str"],
                    "price": current_price_info["price_str"]
                })

                price_to_compare = None
                if current_price_info["current_card_price_float"] is not None:
                    price_to_compare = current_price_info["current_card_price_float"]
                elif current_price_info["current_price_float"] is not None:
                    price_to_compare = current_price_info["current_price_float"]
                
                if price_to_compare is not None:
                    base_price_when_set_str = item.get("base_price_when_set")
                    # Получаем значения порогов. По умолчанию 0, если не найдены.
                    threshold_rub_val = item.get("notification_threshold_rub", 0) 
                    threshold_percent_val = item.get("notification_threshold_percent", 0)
                    is_percent = item.get("is_percent_threshold", False)

                    if base_price_when_set_str is not None and (threshold_rub_val > 0 or threshold_percent_val > 0) :
                        try:
                            base_price_when_set = float(base_price_when_set_str)
                            target_price = None
                            threshold_description = ""

                            if is_percent and threshold_percent_val > 0:
                                # Рассчитываем целевую цену для процентного порога
                                price_drop_for_percent = base_price_when_set * (threshold_percent_val / 100.0)
                                target_price = base_price_when_set - price_drop_for_percent
                                threshold_description = f"{threshold_percent_val}% (было {base_price_when_set} ₽, снижение на ~{price_drop_for_percent:.2f} ₽)"
                            elif not is_percent and threshold_rub_val > 0:
                                # Рассчитываем целевую цену для рублевого порога
                                target_price = base_price_when_set - float(threshold_rub_val)
                                threshold_description = f"{threshold_rub_val} ₽"
                            
                            if target_price is not None and price_to_compare <= target_price:
                                message = (
                                    f"🔔 Цена на товар снизилась!\n"
                                    f"📦 <a href='{url}'>{item.get('title', 'Товар')}</a>\n"
                                    f"📉 Было (при установке отслеживания): {base_price_when_set} ₽\n"
                                    f"✨ Стало: {price_to_compare} ₽ (Карта: {current_price_info['card_price_str'] or '—'} ₽, Без карты: {current_price_info['price_str'] or '—'} ₽)\n"
                                    f"🎯 Установленный порог: {threshold_description}"
                                )
                                try:
                                    # Кнопки для продолжения/остановки отслеживания (ваш существующий код)
                                    # Обратите внимание, что callback_data для кнопок продолжения может потребовать
                                    # item["item_id"] вместо item_index, если item_index может меняться.
                                    # Пока оставим item_index, как у вас было.
                                    item_id = item.get("item_id")
                                    keyboard = InlineKeyboardMarkup([
                                        [
                                            InlineKeyboardButton("✅ Да, от новой цены", callback_data=f"ozon_continue_new|{item_id}"),
                                            InlineKeyboardButton("📉 Да, от старой", callback_data=f"ozon_continue_old|{item_id}"),
                                            InlineKeyboardButton("❌ Нет, остановить", callback_data=f"ozon_stop|{item_id}")
                                        ]
                                    ])
                                    await context.bot.send_message(
                                        chat_id=user_id,
                                        text=message + "\n\nХотите продолжить отслеживание?",
                                        parse_mode='HTML',
                                        reply_markup=keyboard,
                                        disable_web_page_preview=False
                                    )
                                    logger.info(f"Отправлено уведомление о снижении цены пользователю {user_id} для товара {url}")
                                    item["is_active_tracking"] = False # Деактивируем после уведомления
                                except Exception as e:
                                    logger.error(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
                        except ValueError:
                             logger.error(f"Ошибка конвертации base_price_when_set или порогов в float для {url} пользователя {user_id}")
            else:
                 logger.warning(f"Не удалось получить текущую цену для {url} пользователя {user_id}")
            
            updated_items_for_user.append(item)
            delay = random.uniform(5, 15) 
            logger.info(f"Пауза на {delay:.2f} секунд перед следующим товаром.")
            await asyncio.sleep(delay)    
        
        if needs_db_update_for_user:
            db.reference(f"ozon_prices/{user_id}/tracked_items").set(updated_items_for_user)
            logger.info(f"Обновлены данные отслеживания в Firebase для пользователя {user_id}")






async def ozon_tracking_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id) # Используем str для совместимости с вашей функцией update
    chat_id = query.message.chat_id
    action_data = query.data
    action, item_id = action_data.split("|")

    user_ref = db.reference(f"ozon_prices/{user_id}/tracked_items")
    tracked_items = user_ref.get()

    if not tracked_items:
        await context.bot.send_message(chat_id=chat_id, text="Ошибка: список отслеживаемых товаров пуст.")
        return

    # Ищем товар
    item = next((x for x in tracked_items if x.get("item_id") == item_id), None)

    if item is None:
        await context.bot.send_message(chat_id=chat_id, text="Ошибка: товар не найден.")
        return

    current_time_iso = datetime.now(timezone.utc).isoformat()
    updated_fields = {}

    if action == "ozon_continue_new":
        # Берем последнюю известную цену из истории
        last_entry = item.get("price_history", [])[-1]
        card_price_str = last_entry.get("card_price")
        price_str = last_entry.get("price")
        
        new_base = None
        # Пробуем взять цену по карте, если её нет - обычную
        raw_price = card_price_str if card_price_str and card_price_str != "—" else price_str
        
        if raw_price and raw_price != "—":
            try:
                # Обязательно убираем ВСЕ пробелы перед конвертацией
                clean_price = str(raw_price).replace(' ', '').replace('\u2009', '').replace('&nbsp;', '').replace(',', '.')
                new_base = float(clean_price)
            except ValueError:
                pass

        if new_base is not None:
            updated_fields["base_price_when_set"] = new_base
            updated_fields["is_active_tracking"] = True
            updated_fields["added_timestamp_utc"] = current_time_iso
            msg = f"✅ Отслеживание продолжено. Новая базовая цена: <b>{new_base} ₽</b>."
        else:
            msg = "❌ Ошибка: не удалось определить новую цену. Отслеживание не возобновлено."

    elif action == "ozon_continue_old":
        updated_fields["is_active_tracking"] = True
        msg = "📉 Отслеживание продолжено от старой базовой цены."

    elif action == "ozon_stop":
        updated_fields["is_active_tracking"] = False
        msg = "❌ Отслеживание остановлено."
    else:
        await context.bot.send_message(chat_id=chat_id, text="Неизвестный выбор.")
        return

    # Сохраняем изменения точечно (это безопаснее, чем перезаписывать весь массив)
    if updated_fields:
        success = update_ozon_tracking_item(user_id, item_id, updated_fields)
        if success:
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")
        else:
            await context.bot.send_message(chat_id=chat_id, text="❌ Ошибка при сохранении в базу данных.")

import pytz










async def fullhelp_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Отправляет список команд бота в HTML-формате.
    Каждая команда заключена в тег <code> для удобного копирования.
    """
    # Текст помощи — HTML
    help_text = (
        "<b>✨ Команды бота — список</b>\n\n"
        "<code>/vpn</code>     - бесплатные ключи и подписки на впн серверы, в том числе для обхода белых списков.\n"
        "<code>/timer</code>   - интерактивное веб-приложение для пометок с привязкой ко времени таймера (удобно при просмотре фильмов и сериалов если нужно быстро пометить для себя какой-то фрагмент чтобы не забыть где он был).\n"
        "<code>/cat</code>     - случайный факт о котах.\n"
        "<code>/map</code>     - интерактивная карта растений и грибов.\n"
        "<code>/ozon</code>    - отслеживание динамики цен на товар с Ozon с графиком динамики по дням.\n"
        "<code>/search</code>  - режим поиска источника изображения.\n"
        "<code>/ocr</code>     - режим распознавания (растения, текст, грибы, состав продуктов и тд).\n"
        "<code>/gpt</code>     - режим диалога с нейросетью.\n"
        "<code>/scheduledmark</code> - папки с вашими сохранёнными постами.\n"
        "<code>/restart</code> - перезапустить бота (вернуться в основное меню).\n"
        "<code>/send</code>    - отправить сообщение администрации Анемона.\n"
        "<code>/fin</code>     - завершить режим отправки сообщений.\n"
    )

    # Опциональная inline-кнопка (возврат в главное меню)
    keyboard = [
        [InlineKeyboardButton("🌌 В главное меню 🌌", callback_data='restart')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение (HTML)
    # Используем update.effective_message, чтобы работать и с callback_query (если потребуется)
    await update.effective_message.reply_text(
        help_text,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )



async def rand(update, context):
    number = random.randint(0, 5674)  # генерируем число
    url = f"https://t.me/anemonn/{number}"
    await update.message.reply_text(url)


async def ignore_pinned_message(update: Update, context: CallbackContext):
    # Ничего не делаем, просто игнорируем событие закрепления
    pass

def get_smart_colors(b_dist, s_dist, h_dist, norm_brightness):
    # ==========================================
    # НАСТРОЙКИ DOM (ДОМИНАНТНОГО ЦВЕТА) И БАЗОВЫХ ВЕСОВ
    # ==========================================
    cfg_dom = {
        # Базовый множитель для серого. 
        # Увеличить: серый цвет будет чаще становиться доминантным. Уменьшить: реже.
        "base_gray_mult": 520.0,
        
        # Сила "штрафа" (уменьшения веса) черного цвета на светлых фотографиях.
        # Увеличить: черный цвет будет быстрее исчезать из кандидатов на светлых фото.
        "bright_black_penalty": 10.0,
        
        # Бонус к весу белого цвета, если на фото много серого (>15%).
        # Увеличить: белый чаще будет побеждать серый при обилии нейтральных тонов.
        "white_gray_boost": 10.0,
        
        # Штраф цвета за "темноту". Какая доля веса цвета сгорает из-за его темных пикселей.
        # Увеличить: темные/грязные цвета реже будут становиться DOM. Уменьшить: будут чаще.
        "color_dark_penalty": 0.7,
        
        # Штраф цвета за "светлоту". Какая доля веса сгорает из-за засвеченных пикселей.
        # Увеличить: пастельные/светлые оттенки реже становятся DOM.
        "color_bright_penalty": 0.1,
        
        # Какая доля от "отрезанного" веса темных цветных пикселей передается в Черный цвет.
        # Увеличить: Черный быстрее набирает вес от темных синих/зеленых и т.д.
        "color_to_black_transfer": 0.5,
        
        # Какая доля от "отрезанного" веса светлых цветных пикселей передается в Белый цвет.
        # Увеличить: Белый быстрее набирает вес от светлых пастельных оттенков.
        "color_to_white_transfer": 0.5,

        # --- НОВЫЙ ПАРАМЕТР ---
        # Бонус за насыщенность (чистоту) цвета.
        # Увеличить: сочные/насыщенные цвета будут агрессивно обгонять тусклые и грязные оттенки.
        # Например, при 0.8: цвет, состоящий на 100% из насыщенных пикселей, получит +80% к весу.        
        "color_sat_boost": 1.8, 
        # --- НОВОЕ: Множители чувствительности к насыщенности ---
        # Значения > 1.0 позволяют цвету получать высокий бонус даже при средней насыщенности.
        "hue_sat_multipliers": {
            "purple": 3,
            "pink": 2.3,
            "blue": 1.7
        },


        # Минимальный порог веса для того, чтобы цвет вообще рассматривался как кандидат в DOM.
        # Увеличить: мелкие детали никогда не станут DOM. Уменьшить: больше мусорных кандидатов.
        "min_dom_weight": 0.9
    }

    # ==========================================
    # НАСТРОЙКИ SEC (ВТОРИЧНОГО/VISUAL ЦВЕТА)
    # ==========================================
    cfg_sec = {
        # Минимальный сырой вес для участия в расчете SEC.
        "min_sec_weight": 0.5,
        # --- НОВЫЙ ПАРАМЕТР ---
        # Бонус за индивидуальную насыщенность (чистоту) SEC цвета.
        # Увеличить: сочные/насыщенные оттенки будут получать множитель к итоговому 
        # visual_score и легко обгонять тусклые/грязные цвета-кандидаты.
        "color_sat_boost": 20, 
        # --- Ч/Б на фоне Ч/Б ---
        # Порог веса, после которого применяется штрафной множитель (чтобы ч/б было сложнее стать SEC).
        "achro_weight_threshold": 15.0,
        # Множитель веса (если вес больше порога выше). 
        # Увеличить (>0.5): серому/черному будет проще стать SEC на фоне белого/черного.
        "achro_on_achro_mult": 0.7,

        # --- ЦВЕТ на фоне Ч/Б ---
        # Множитель для цвета, если фото в основном серое (>55%).
        # Увеличить: любые цвета на серых фото будут иметь огромный шанс стать SEC.
        "color_on_achro_mult_mono": 2.0,
        # Множитель для цвета на фоне ч/б в обычных условиях.
        # Увеличить: цветные элементы будут еще сильнее доминировать над ч/б фоном.
        "color_on_achro_mult_norm": 5.0,
        
        # Порог веса для определения "маленькой детали" (например, красной кнопки на сером фоне).
        "small_color_threshold": 15.0,
        # Доп. буст для маленьких деталей. Увеличить: мелкие яркие детали агрессивнее становятся SEC.
        "small_color_boost": 1.5,
        
        # Порог кол-ва насыщенных пикселей на фото, чтобы применить глобальный буст цвета.
        "high_sat_threshold": 0.05,
        # Множитель для высоконасыщенных фото. Увеличить: насыщенные цвета легче перебивают тусклые.
        "high_sat_boost": 1.2,

        # --- Ч/Б на фоне ЦВЕТА ---
        # Виртуальный базовый вес черного (умножается на долю темных неярких пикселей).
        # Увеличить: Черный чаще будет SEC на цветных фотографиях с тенями.
        "black_on_color_base": 200.0,
        # Итоговый множитель черного на цветном фоне. Увеличить: черному проще пробиться в SEC.
        "black_on_color_mult": 0.8,
        
        # Виртуальный базовый вес белого (умножается на долю ярких неярких пикселей).
        # Увеличить: Белый чаще будет SEC на фото с пересветами.
        "white_on_color_base": 1800.0,
        # Итоговый множитель белого на цветном фоне.
        "white_on_color_mult": 1.2,
        
        # Множитель серого на фоне цвета. 
        # Увеличить: серый перестанет игнорироваться и начнет вытеснять цвета из SEC (не рекомендуется).
        "gray_on_color_mult": 0.3,
        # --- НОВОЕ: Множители чувствительности для SEC ---
        # Работает аналогично DOM, помогая фиолетовому спектру пробиваться в SEC.
        "hue_sat_multipliers": {
            "purple": 3,
            "pink": 2.3,
            "blue": 1.7
        },
        # --- ЦВЕТ на фоне ЦВЕТА (дистанции на цветовом круге 0-360) ---
        # Дистанция 1 (очень близкие цвета). Увеличить: больше похожих оттенков будут игнорироваться.
        "dist_close": 20,
        "mult_close": 0.1,   # 0.0 значит, что близкие оттенки полностью сбрасываются.
        
        # Дистанция 2 (соседние цвета).
        "dist_medium": 45,
        "mult_medium": 0.7,  # Увеличить: соседним оттенкам (например, синему на фоне голубого) легче стать SEC.
        
        # Дистанция 3 (средне-далекие цвета).
        "dist_far": 65,
        "mult_far": 0.1,    # Штрафная зона, чтобы "грязные" переходы не становились SEC.
        
        # Множитель для контрастных цветов (дальше dist_far) на "сером" фото.
        "color_on_color_mult_mono": 1.0,
        # Множитель для контрастных цветов на обычных ярких фото.
        # Увеличить: противоположные цвета (красный-зеленый) будут всегда перебивать остальные.
        "color_on_color_mult_norm": 2.0,
    }

    dark_ratio = b_dist.get('dark', 0)
    bright_ratio = b_dist.get('bright', 0)
    gray_ratio = s_dist.get('gray', 0)
    high_sat_ratio = s_dist.get('high', 0)

    # --- БАЗОВЫЕ ВЕСА АХРОМАТИКИ ---
    base_black_weight = dark_ratio * 1.0
    base_white_weight = bright_ratio * 1.0
    exact_gray = b_dist.get('exact_gray', gray_ratio)
    
    # Корректировки яркости
    black_weight = base_black_weight
    if norm_brightness >= 0.65:
        darkness_factor = (0.65 - norm_brightness) / 0.65
        black_weight += darkness_factor * cfg_dom["bright_black_penalty"]

    white_weight = base_white_weight
    if exact_gray > 0.15:
        white_weight += cfg_dom["white_gray_boost"]

    gray_weight = exact_gray * cfg_dom["base_gray_mult"]

    # ==========================================
    # ЭТАП 1: ПОДГОТОВКА ВЕСОВ ДЛЯ DOM
    # ==========================================
    dom_weights = {
        "black": black_weight,
        "white": white_weight,
        "gray": gray_weight
    }
    
    for hue in h_dist.keys():
        dom_weights[hue] = 0.0

    for hue, data in h_dist.items():
        original_weight = data.get('tw', 0)
        total_hue_pixels = data.get('hv', 0) + data.get('mv', 0) + data.get('lv', 0)
        
        if total_hue_pixels > 0 and original_weight > 0:
            dark_ratio_in_color = data.get('lv', 0) / total_hue_pixels
            bright_ratio_in_color = data.get('hv', 0) / total_hue_pixels
            sat_ratio_in_color = data.get('hs', data.get('mv', 0)) / total_hue_pixels
            
            sat_mult = cfg_dom["hue_sat_multipliers"].get(hue, 1.0)
            effective_sat_ratio = min(1.0, sat_ratio_in_color * sat_mult)

            pure_color_weight = original_weight * (
                1.0 
                - cfg_dom["color_dark_penalty"] * dark_ratio_in_color 
                - cfg_dom["color_bright_penalty"] * bright_ratio_in_color
            )
            
            pure_color_weight *= (1.0 + (cfg_dom["color_sat_boost"] * effective_sat_ratio))
            
            dom_weights[hue] = pure_color_weight
            dom_weights["black"] += original_weight * cfg_dom["color_to_black_transfer"] * dark_ratio_in_color
            dom_weights["white"] += original_weight * cfg_dom["color_to_white_transfer"] * bright_ratio_in_color
        else:
            dom_weights[hue] = original_weight

    sorted_dom = sorted(dom_weights.items(), key=lambda x: x[1], reverse=True)
    valid_dom_candidates = [c for c in sorted_dom if c[1] >= cfg_dom["min_dom_weight"]]
    
    if not valid_dom_candidates:
        dom_color = sorted_dom[0][0] if sorted_dom else "black"
    else:
        dom_color = valid_dom_candidates[0][0]

    # ==========================================
    # ЭТАП 2: ПОДГОТОВКА СПИСКА ДЛЯ SEC (VISUAL)
    # ==========================================
    raw_combined_colors = []
    raw_combined_colors.append({"name": "black", "weight": black_weight})
    raw_combined_colors.append({"name": "white", "weight": white_weight})
    raw_combined_colors.append({"name": "gray",  "weight": gray_weight})

    for hue, data in h_dist.items():
        raw_combined_colors.append({"name": hue, "weight": data.get('tw', 0)})

    valid_colors = [c for c in raw_combined_colors if c['weight'] >= cfg_sec["min_sec_weight"]]
    if not valid_colors:
        # Теперь возвращаем 5 параметров
        return dom_color, None, None, [], dom_weights 
        
    valid_colors.sort(key=lambda x: x['weight'], reverse=True)

    # ==========================================
    # ЭТАП 3: РАСЧЕТ SEC (VISUAL SCORE)
    # ==========================================
    achromatic_set = {"black", "white", "gray"}
    hue_positions = {
        "red": 0, "orange": 40, "yellow": 85, "green": 130, 
        "cyan": 180, "blue": 240, "purple": 280, "pink": 320
    }

    is_mostly_monochrome = gray_ratio > 0.55
    high_sat_ratio = s_dist.get('high', 0.0) 

    best_sec_color = None
    best_sec_score = -1.0
    
    dark_low_sat = b_dist.get("dark_low_sat", 0)
    bright_low_sat = b_dist.get("bright_low_sat", 0)

    for i in range(len(valid_colors)):
        cand_color = valid_colors[i]['name']
        
        if cand_color == dom_color:
            valid_colors[i]["visual_score"] = 0.0
            continue

        cand_weight = valid_colors[i]['weight']
        multiplier = 0.0

        if dom_color in achromatic_set:
            if cand_color in achromatic_set:
                if (dom_color == "black" and cand_color == "white") or \
                   (dom_color == "white" and cand_color == "black"):
                    multiplier = 1.0
                elif cand_weight > cfg_sec["achro_weight_threshold"]:
                    multiplier = cfg_sec["achro_on_achro_mult"]
            else:
                multiplier = cfg_sec["color_on_achro_mult_mono"] if is_mostly_monochrome else cfg_sec["color_on_achro_mult_norm"]
                if cand_weight < cfg_sec["small_color_threshold"]:
                    multiplier *= cfg_sec["small_color_boost"]
                if high_sat_ratio > cfg_sec["high_sat_threshold"]:
                    multiplier *= cfg_sec["high_sat_boost"]

        else:
            if cand_color in achromatic_set:
                if cand_color == "black":
                    visual_black_weight = dark_low_sat * cfg_sec["black_on_color_base"]
                    cand_weight = visual_black_weight
                    multiplier = cfg_sec["black_on_color_mult"]
                elif cand_color == "white":
                    visual_white_weight = bright_low_sat * cfg_sec["white_on_color_base"]
                    cand_weight = visual_white_weight
                    multiplier = cfg_sec["white_on_color_mult"]
                else: 
                    multiplier = cfg_sec["gray_on_color_mult"]
            else:
                h1 = hue_positions.get(dom_color, 0)
                h2 = hue_positions.get(cand_color, 0)
                dist = abs((h1 - h2) % 360)
                if dist > 180: dist = 360 - dist
                
                if dist <= cfg_sec["dist_close"]:
                    multiplier = cfg_sec["mult_close"] 
                elif dist <= cfg_sec["dist_medium"]:
                    multiplier = cfg_sec["mult_medium"]
                elif dist <= cfg_sec["dist_far"]:
                    multiplier = cfg_sec["mult_far"]
                else:
                    multiplier = cfg_sec["color_on_color_mult_mono"] if is_mostly_monochrome else cfg_sec["color_on_color_mult_norm"]

        if multiplier <= 0.0:
            valid_colors[i]["visual_score"] = 0.0
            continue

        if cand_color not in achromatic_set:
            color_data = h_dist.get(cand_color, {})
            total_hue_pixels = color_data.get('hv', 0) + color_data.get('mv', 0) + color_data.get('lv', 0)
            if total_hue_pixels > 0:
                sat_ratio_in_cand = color_data.get('hs', color_data.get('mv', 0)) / total_hue_pixels
                
                sat_mult = cfg_sec["hue_sat_multipliers"].get(cand_color, 1.0)
                effective_sat_ratio = min(1.0, sat_ratio_in_cand * sat_mult)
                
                multiplier *= (1.0 + (cfg_sec["color_sat_boost"] * effective_sat_ratio))

        visual_score = cand_weight * multiplier
        valid_colors[i]["visual_score"] = round(visual_score, 2)

        if visual_score > best_sec_score:
            best_sec_score = visual_score
            best_sec_color = cand_color

    # ==========================================
    # НОВОЕ: ЭТАП 4: РАСЧЕТ TER (ТРЕТЬЕГО ЦВЕТА)
    # ==========================================
    best_ter_color = None
    best_ter_score = -1.0
    
    dom_sec_set = {dom_color, best_sec_color}

    for color_data in valid_colors:
        cand_color = color_data['name']
        cand_visual_score = color_data.get('visual_score', 0.0)

        # 1. Третий цвет не может быть dom, sec или ахроматическим (чёрный, белый, серый)
        if cand_color in dom_sec_set or cand_color in achromatic_set:
            continue
            
        # 2. Отсекаем все цвета со значением visual меньше 10
        if cand_visual_score < 20.0:
            continue
            
        # 3. Конфликты Blue / Cyan
        if cand_color == "cyan" and "blue" in dom_sec_set:
            continue
        if cand_color == "blue" and "cyan" in dom_sec_set:
            continue
            
        # 4. Выбираем с наибольшим visual_score
        if cand_visual_score > best_ter_score:
            best_ter_score = cand_visual_score
            best_ter_color = cand_color

    # Теперь возвращаем 5 параметров!
    return dom_color, best_sec_color, best_ter_color, valid_colors, dom_weights


def main() -> None:
    load_context_from_firebase()  # Загружаем историю чатов в user_contexts
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    ozon_choice_handler = CallbackQueryHandler(ozon_tracking_choice_handler, pattern=r"^ozon_(continue_new|continue_old|stop)\|[0-9a-fA-F\-]{36}$")
    # Настройка ConversationHandler для основной логики
    conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('edit', edit_article),            
            MessageHandler(filters.TEXT & ~filters.COMMAND, main_logic)  # Основная логика
        ],
        states={
            ASKING_FOR_ARTIST_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_artist_link)],
            ASKING_FOR_AUTHOR_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_author_name)],
            EDITING_FRAGMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_text)],
            ASKING_FOR_IMAGE: [
                MessageHandler(filters.PHOTO | filters.Document.ALL, handle_new_image),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
            ],
        },
        fallbacks=[
            ozon_choice_handler, # <--- ДОБАВИТЬ СЮДА
            MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message)
        ],
        per_user=True
    )

    search_handler = ConversationHandler(
        entry_points=[CommandHandler('search', start_search)],
        states={
            ASKING_FOR_FILE: [
                MessageHandler(filters.PHOTO | filters.Document.ALL, handle_file),
                MessageHandler(filters.ALL & ~filters.COMMAND, unknown_search_message),
            ],
        },
        fallbacks=[
            ozon_choice_handler, # <--- ДОБАВИТЬ СЮДА
            CommandHandler('fin_search', finish_search),
            CommandHandler('restart', restart),
        ],
        per_user=True,
        allow_reentry=True
    )

    ocr_handler = ConversationHandler(
        entry_points=[CommandHandler('ocr', start_ocr), CallbackQueryHandler(text_rec_with_gpt, pattern='^text_rec$')],
        states={
            ASKING_FOR_FILE: [
                MessageHandler(filters.PHOTO | filters.Document.ALL, handle_file),
                MessageHandler(filters.ALL & ~filters.COMMAND, unknown_ocr_message),
            ],
            ASKING_FOR_FOLLOWUP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_followup_question),            ],        
        },
        fallbacks=[
            ozon_choice_handler, # <--- ДОБАВИТЬ СЮДА
            CommandHandler('fin_ocr', finish_ocr),
            CommandHandler('restart', restart),
        ],
        per_user=True,
        allow_reentry=True
    )

    gpt_handler = ConversationHandler(
        entry_points=[CommandHandler('gpt', run_gpt), CommandHandler('set_role', handle_set_role_button), CommandHandler('short_help_gpt', handle_short_gpt_help)],
        states={
            ASKING_FOR_ROLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_role_input),
            ],
            ASKING_FOR_FILE: [
                MessageHandler(filters.PHOTO | filters.Document.ALL, handle_file),
                MessageHandler(filters.ALL & ~filters.COMMAND, unknown_ocr_message),
            ],
        },
        fallbacks=[
            ozon_choice_handler, # <--- ДОБАВИТЬ СЮДА
            CommandHandler('fin_gpt', stop_gpt),
            CommandHandler('restart', restart),
        ],
        per_user=True,
        allow_reentry=True
    )

    application.add_handler(MessageHandler(filters.StatusUpdate.PINNED_MESSAGE, ignore_pinned_message))
    # Добавляем обработчики команд
    application.add_handler(InlineQueryHandler(inline_query_handler))    
    application.add_handler(CallbackQueryHandler(handle_edit_button, pattern='edit_article'))
    application.add_handler(CallbackQueryHandler(handle_delete_button, pattern='delete_last'))
    application.add_handler(CallbackQueryHandler(handle_edit_delete, pattern='^edit_|^delete_'))
    application.add_handler(CallbackQueryHandler(handle_preview_button, pattern='preview_article'))
    application.add_handler(CallbackQueryHandler(handle_create_article_button, pattern='create_article'))
    application.add_handler(CallbackQueryHandler(handle_help_text_button, pattern='help_command'))
    application.add_handler(CallbackQueryHandler(handle_restart_button, pattern='restart'))
    application.add_handler(CallbackQueryHandler(handle_page_change, pattern='^page_')) 
    application.add_handler(CallbackQueryHandler(handle_publish_button, pattern='^publish_'))
    application.add_handler(CallbackQueryHandler(ai_or_not, pattern='ai_or_not'))
    application.add_handler(CallbackQueryHandler(finish_search, pattern='finish_search')) 
    application.add_handler(CallbackQueryHandler(finish_ocr, pattern='finish_ocr'))
    application.add_handler(CallbackQueryHandler(stop_gpt, pattern='stop_gpt'))      
    application.add_handler(CallbackQueryHandler(start_search, pattern='start_search'))
    application.add_handler(CallbackQueryHandler(start_ocr, pattern='start_ocr'))
    application.add_handler(CallbackQueryHandler(button_ocr, pattern='recognize_text'))
    application.add_handler(CallbackQueryHandler(button_ocr, pattern='recognize_plant'))
    application.add_handler(CallbackQueryHandler(button_more_plants_handler, pattern='plant_\\d+'))
    application.add_handler(CallbackQueryHandler(gpt_plants_help_handler, pattern='^gpt_plants_help$'))
    application.add_handler(CallbackQueryHandler(gpt_plants_more_handler, pattern='^gpt_plants_more$'))

    application.add_handler(CallbackQueryHandler(select_imagen3, pattern="^select_imagen3$"))

    
    application.add_handler(CallbackQueryHandler(text_rec_with_gpt, pattern='text_rec_with_gpt$'))
    application.add_handler(CallbackQueryHandler(text_plant_help_with_gpt, pattern='text_plant_help_with_gpt$'))    
    application.add_handler(CallbackQueryHandler(analyze_ingredients, pattern='analyze_ingredients$'))   
    application.add_handler(CallbackQueryHandler(recognize_animal_insect, pattern='recognize_animal_insect$'))      
    application.add_handler(CallbackQueryHandler(mushrooms_gpt, pattern='mushrooms_gpt$'))  
    application.add_handler(CallbackQueryHandler(products_gpt, pattern='products_gpt$'))     
    application.add_handler(CallbackQueryHandler(calories_gpt, pattern='calories_gpt$'))      
    
    application.add_handler(CallbackQueryHandler(composition_comparison_gpt, pattern='compcomparison_gpt$'))      
    application.add_handler(CallbackQueryHandler(regenerate_image, pattern=r"^regenerate_"))
    application.add_handler(CallbackQueryHandler(examples_table_handler, pattern='^examples_table$'))
    application.add_handler(CallbackQueryHandler(handle_view_shared, pattern="^view_shared$"))
    application.add_handler(CallbackQueryHandler(handle_select_scheduled, pattern=r"^view_shared_"))
    application.add_handler(CallbackQueryHandler(handle_view_post, pattern=r"^viewneuralpost_\d+_.+$"))
    application.add_handler(CallbackQueryHandler(handle_neuralpublic_button, pattern="^neuralpublic_"))
    application.add_handler(CallbackQueryHandler(handle_shared_tag_selection, pattern="^sharedtag_"))
    application.add_handler(CallbackQueryHandler(handle_sharefromuser_publication, pattern=r"^sharefromuserpublic_\d+_\d+$"))
    application.add_handler(CallbackQueryHandler(handle_edit_post, pattern=r"^editpost_\d+_\d+$"))
    application.add_handler(CallbackQueryHandler(handle_back_to_main, pattern=r"^backtomain_\d+_\d+$"))
    application.add_handler(CallbackQueryHandler(handle_add_favorite, pattern=r"^favorite_\d+_\d+_\d+$"))

    
    
    application.add_handler(CallbackQueryHandler(run_gpt, pattern='run_gpt')) 
    application.add_handler(CallbackQueryHandler(reset_dialog, pattern='^reset_dialog$')) 
    application.add_handler(CallbackQueryHandler(handle_set_role_button, pattern='^set_role_button$'))  
    application.add_handler(CallbackQueryHandler(handle_followup_question, pattern='^ask_followup'))    
    application.add_handler(CallbackQueryHandler(handle_short_gpt_help, pattern='^short_help_gpt$'))                 
    application.add_handler(CallbackQueryHandler(handle_vkpub_button, pattern=r'^vkpub_'))
    application.add_handler(CallbackQueryHandler(handle_twitterpub_button, pattern=r'^twitterpub_'))    
    application.add_handler(CallbackQueryHandler(filedelete_image, pattern=r'^filedelete_'))
    application.add_handler(CallbackQueryHandler(fileselect_image_to_delete, pattern=r'^fileselect_'))
    application.add_handler(CallbackQueryHandler(handle_role_select, pattern='^role_select$'))
    application.add_handler(CallbackQueryHandler(handle_role_selected, pattern='^(newroleselect_|defaultrole_|gamerole_)'))
    application.add_handler(CallbackQueryHandler(handle_delete_role, pattern=r"^clear_role_"))  
    application.add_handler(CallbackQueryHandler(mainhelp_callback, pattern="osnhelp"))
    application.add_handler(CallbackQueryHandler(handle_share_button, pattern='^share_'))   


    application.add_handler(CallbackQueryHandler(handle_cancel_role, pattern='^cancel_role_selection$'))    
    application.add_handler(CallbackQueryHandler(yrrase_scheduled, pattern="yrrasetag_"))
      
    application.add_handler(CallbackQueryHandler(plantmap_gpt, pattern='^plantmap_gpt$'))
    application.add_handler(CallbackQueryHandler(scientific_gpt, pattern='^scientific_gpt$'))    
    application.add_handler(CallbackQueryHandler(show_map, pattern="^show_map$"))
    application.add_handler(CallbackQueryHandler(gpt_running, pattern="^(showgpt_menu|hidegpt_menu)$"))
    application.add_handler(CallbackQueryHandler(run_gpt, pattern="^(showstartgpt_menu|hidestartgpt_menu)$"))  
    application.add_handler(CallbackQueryHandler(run_gpt_menu, pattern="^(gptmenu_show|gptmenu_hide)$"))     
    application.add_handler(CallbackQueryHandler(barcode_with_gpt, pattern='barcode_with_gpt$'))
    application.add_handler(CallbackQueryHandler(plants_and_mushrooms_menu, pattern='plants_and_mushrooms_menu$'))
    application.add_handler(CallbackQueryHandler(plants_and_mushrooms_backmenu, pattern='plants_and_mushrooms_backmenu$'))
    application.add_handler(CallbackQueryHandler(add_new_plant, pattern='addnewplant$'))
    application.add_handler(CommandHandler("map", show_map))
    application.add_handler(CommandHandler("rand", rand))

    application.add_handler(CallbackQueryHandler(more_keys, pattern=r"^more_keys_\d+$"))  
    application.add_handler(CallbackQueryHandler(download_file, pattern="^download_file$"))
    application.add_handler(CallbackQueryHandler(send_instruction, pattern="^vpninstruction_show$"))

    
      
    # Начало процесса замены
    application.add_handler(CallbackQueryHandler(swap_images, pattern=r'^swapimages_'))
    application.add_handler(CallbackQueryHandler(delete_all_by_tag, pattern=r"^tagdelete_"))
    # Выбор первого изображения
    application.add_handler(CallbackQueryHandler(select_first_image, pattern=r'^swap_first_'))

    # Выбор второго изображения
    application.add_handler(CallbackQueryHandler(select_second_image, pattern=r'^swap_second_'))
    # Обработчик для кнопки "Отложить"
    application.add_handler(CallbackQueryHandler(change_page, pattern=r"^folderpage_\d+_.*$"))
    application.add_handler(CommandHandler("choose_preset", choose_preset))
    application.add_handler(CallbackQueryHandler(preset_callback, pattern=r"^preset_"))
    application.add_handler(CallbackQueryHandler(handle_presetclose_button, pattern='^presetclose$'))    

    application.add_handler(CallbackQueryHandler(gptplant_response, pattern='^gptplant_response$'))      
    application.add_handler(CallbackQueryHandler(handle_myplants_callback, pattern='^myplants'))
    application.add_handler(CallbackQueryHandler(handle_pagination, pattern="^plantpage_"))
    application.add_handler(CallbackQueryHandler(save_to_my_plants, pattern='^plantsave_to_my_plants$'))
    application.add_handler(CallbackQueryHandler(handle_sorting, pattern='^plantsort_'))    
    application.add_handler(CallbackQueryHandler(watering_button_handler, pattern="^water_plant$"))
    application.add_handler(CallbackQueryHandler(plant_callback, pattern=r"^myplant_"))
    application.add_handler(CallbackQueryHandler(delete_plant_callback, pattern=r"^plantdelete_"))    
    application.add_handler(CallbackQueryHandler(plant_close_callback, pattern="^plantclose$"))

    # --- ДОБАВЬТЕ ЭТУ СТРОКУ ---
    application.add_handler(CallbackQueryHandler(show_timeline, pattern='^view_timeline$'))
    # --- КОНЕЦ ---
    
    
    application.add_handler(CallbackQueryHandler(handle_snooze_with_tag_button, pattern=r"^snooze_with_tag_\d+_\d+$"))  
    application.add_handler(CallbackQueryHandler(handle_tag_selection, pattern=r"^tag_"))
    application.add_handler(CallbackQueryHandler(handle_save_button, pattern=r"^save_\d+_\d+$"))
    application.add_handler(CallbackQueryHandler(handle_replace_caption, pattern=r"caption_"))

    application.add_handler(CallbackQueryHandler(select_style, pattern="choose_modele"))
    application.add_handler(CallbackQueryHandler(choose_preset, pattern="choose_preset"))    
    application.add_handler(CallbackQueryHandler(model_selection_handler, pattern="^set_model\|")) 
    application.add_handler(CallbackQueryHandler(cancel_handler, pattern="^cancelmodel"))

    
    application.add_handler(CommandHandler("scheduledmark", handle_scheduled_tags))
    application.add_handler(CallbackQueryHandler(handle_scheduled_tags, pattern="^scheduled_by_tag$"))
    application.add_handler(CallbackQueryHandler(show_scheduled_by_tag, pattern="^filter_tag_"))
    # Обработчик для команды /scheduled (показать список отложенных записей)

    application.add_handler(CallbackQueryHandler(handle_shuffle_button, pattern=r"^shuffle_\d+_\d+$"))
    application.add_handler(CallbackQueryHandler(handle_palettesort, pattern=r"^palettesort_\d+_\d+$"))
    application.add_handler(CallbackQueryHandler(sort_by_criteria, pattern=r"^sort_\w+_\w+$"))

    #OZON
    application.add_handler(CommandHandler("ozon", handle_ozon))
    application.add_handler(CallbackQueryHandler(ozon_track_start_callback, pattern="^ozon_track_start_"))
    application.add_handler(CallbackQueryHandler(ozon_set_threshold_callback, pattern="^ozon_set_thresh_"))
    application.add_handler(ozon_choice_handler)
    application.add_handler(CallbackQueryHandler(handle_ozonpage_change, pattern=r"^ozon_page_\d+$"))
    application.add_handler(CallbackQueryHandler(handle_my_items, pattern=r"^myozon_items$"))
    application.add_handler(CallbackQueryHandler(ozon_view_stat, pattern=r"^ozon_view_stat_"))
    application.add_handler(CallbackQueryHandler(ozon_delete_handler, pattern=r"^ozon_delete_"))
    application.add_handler(CallbackQueryHandler(ozon_message_delete, pattern="^ozondelete_msg$"))
    application.add_handler(CallbackQueryHandler(ozon_change_threshold_callback, pattern=r"^changenotif_"))
    application.add_handler(CallbackQueryHandler(ozon_update_threshold_callback, pattern=r"^ozon_update_thresh_"))    
    application.add_handler(CallbackQueryHandler(find_image_source, pattern='^find_image_source$'))
    # Обработчик для кнопки "Отложить 🗓️"
    application.add_handler(CallbackQueryHandler(schedule_post_handler, pattern=r'^schedulepost_'))
    
    # Обработчик для обновления выбора на клавиатуре
    application.add_handler(CallbackQueryHandler(schedule_update_handler, pattern=r'^schedule_update_'))

    # Обработчик для кнопки "Подтвердить выбор"
    application.add_handler(CallbackQueryHandler(schedule_confirm_handler, pattern=r'^schedule_confirm_'))

    # Добавляем обработчик для кнопок-заглушек, чтобы они ничего не делали, но убирали "часики"
    application.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer(), pattern=r'^noop$'))
    
    # Обработчик для просмотра конкретной отложенной записи
    application.add_handler(CallbackQueryHandler(handle_view_scheduled, pattern=r'^view_[\w_]+$')) 
    application.add_handler(CallbackQueryHandler(handle_otloj_scheduled, pattern=r'^otlview_[\w_]+$')) 
    application.add_handler(CallbackQueryHandler(delete_scheduled_time_handler, pattern=r"^otloj_delete_\d+_\d+$")) 

    vpn_keys_regex = "|".join(VPN_BUTTONS.keys())
    application.add_handler(CallbackQueryHandler(vpn_show_config, pattern=rf"^vpn_({vpn_keys_regex})$"))
    application.add_handler(CallbackQueryHandler(vpn_old, pattern="^vpn_old$"))
    application.add_handler(CallbackQueryHandler(vpn_instruction, pattern="^vpn_instruction$"))
    application.add_handler(CallbackQueryHandler(close_handler, pattern="^close$"))
    application.add_handler(CallbackQueryHandler(send_subscription, pattern="vpn_generate_sub"))
    application.add_handler(CommandHandler("oldvpn", vpn))
    application.add_handler(CommandHandler("vpn", vpn_menu))
    application.add_handler(CommandHandler("vpnconfig", send_subscription))

    application.add_handler(CommandHandler("proxy", send_proxies))
    application.add_handler(CallbackQueryHandler(send_proxies, pattern="refresh_proxies"))


    
    application.add_handler(CommandHandler("userid", userid_command))
    application.add_handler(CommandHandler("rec", recognize_test_plant))
    application.add_handler(CommandHandler("testid", handle_testid_command))  
    application.add_handler(CommandHandler("token", token_set))       
    application.add_handler(CommandHandler('webapp', webapp_command))    
    application.add_handler(CommandHandler("sendall", sendall))    
    application.add_handler(CommandHandler("data", data_command))      
    application.add_handler(CommandHandler("style", choose_style))   
    application.add_handler(CommandHandler('set_role', set_role ))          
    application.add_handler(CommandHandler('send', send_mode))
    application.add_handler(CommandHandler('fin', fin_mode))
    application.add_handler(CommandHandler('restart', restart))
    application.add_handler(CommandHandler('rerestart', rerestart))    
    application.add_handler(CommandHandler('help', fullhelp_command))
    application.add_handler(CommandHandler('publish', publish))
    application.add_handler(CommandHandler('preview', preview_article))  # Добавляем обработчик для /preview
    application.add_handler(CommandHandler('delete', delete_last))
    application.add_handler(CommandHandler('timer', send_timer_app_button))
    application.add_handler(CommandHandler("cat", cat_command))

    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, duplicate_message))  # Обработчик дублирования сообщений
    application.add_handler(CommandHandler("fileid", fileid_command))

    # Добавляем обработчики для команд /search и /fin_search
    application.add_handler(search_handler)
    application.add_handler(CommandHandler('fin_search', finish_search))  # Обработчик команды /fin_search

    # Добавляем обработчики для команд /ocr и /fin_ocr
    application.add_handler(ocr_handler)
    application.add_handler(CommandHandler('fin_ocr', finish_ocr)) 

    # Добавляем обработчики для команд /gpt и /fin_gpt
    application.add_handler(gpt_handler)
    application.add_handler(CommandHandler('fin_gpt', stop_gpt))     
    application.add_handler(CommandHandler("otl", list_scheduled_jobs))
    # Добавляем основной conversation_handler
    application.add_handler(conversation_handler)

    logger.info("Bot started and polling...")  
    keep_alive()#запускаем flask-сервер в отдельном потоке. Подробнее ниже...
    # Планируем ежедневную задачу
    # Запускать раз в день, например, в 09:00 UTC. Настройте время по необходимости.
    # import pytz # для таймзон
    # time = datetime.time(hour=9, minute=0, tzinfo=pytz.timezone('UTC'))
    # Для простоты, запускаем каждые 24 часа с первого запуска: interval=24 * 60 * 60, first=10
    moscow_tz = pytz.timezone('Europe/Moscow')
    time_to_run = dt_time(hour=8, minute=48, tzinfo=moscow_tz) 
    
    job_queue = application.job_queue

    # ⏳ Запуск обновления через 30 секунд после старта
    job_queue.run_once(lambda ctx: run_vpn_update(), when=30)
    # ⏱ Ежедневное автообновление в 04:00
    job_queue.run_daily(lambda ctx: run_vpn_update(), time=dt_time(hour=4, minute=0, tzinfo=moscow_tz))

    job_queue.run_daily(daily_ozon_price_check_job, time=time_to_run)
    
    logging.info(f"Задача daily_ozon_price_check_job зарегистрирована на ежедневный запуск в {time_to_run.strftime('%H:%M')} по Москве.")

    # Новая задача для сканирования публикаций
    # Запускаем каждый час, первая проверка сразу после запуска бота
    job_queue.run_once(reschedule_publications_on_startup, when=timedelta(seconds=10))
    logging.info("Задача reschedule_publications_on_startup зарегистрирована для однократного запуска при старте.")


    
    application.run_polling() 
if __name__ == '__main__':
    # Настройка логирования
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__) # Определяем logger здесь, если он не определен глобально ранее

    # Инициализация Firebase (замените вашей фактической инициализацией)
    try:
        import firebase_admin
        from firebase_admin import credentials, db # db используется глобально в функциях выше
        
        # Проверяем, не был ли Firebase уже инициализирован, чтобы избежать ошибок при горячей перезагрузке
        if not firebase_admin._apps:
            cred_path = os.path.join("config", "firebase_service_key.json") # Храните ваш JSON ключ сервиса здесь
            if not os.path.exists(cred_path):
                 logger.critical(f"Файл ключа сервиса Firebase не найден по пути {cred_path}. Выход.")
                 exit()
            cred = credentials.Certificate(cred_path)
            # Замените 'YOUR_FIREBASE_DATABASE_URL' на URL вашей БД
            firebase_admin.initialize_app(cred, {'databaseURL': 'YOUR_FIREBASE_DATABASE_URL'}) 
            logger.info("Firebase Admin SDK инициализирован.")
        else:
            logger.info("Firebase Admin SDK уже был инициализирован.")
    except Exception as e:
        logger.critical(f"Не удалось инициализировать Firebase Admin SDK: {e}")
        exit() # Критическая ошибка, бот не может функционировать без БД

    main()
