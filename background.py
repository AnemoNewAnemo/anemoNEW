from flask import Flask, request, jsonify, send_from_directory, make_response
from threading import Thread
import os
import logging
from flask import render_template_string
app = Flask(__name__, static_folder='static')  # Указываем папку для статики
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
from PIL import Image  # Библиотека для обработки изображений
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN не задан в переменных окружения")
from waitress import serve
import math
# --- API ENDPOINTS (Точки для работы с данными) ---
import uuid
import random
import requests
from flask import Response, stream_with_context
import random
import hashlib

import time  # <--- ДОБАВЛЕНО


import logging
import sys

# Настраиваем логирование в консоль (stdout)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
# Создаем сессию для ускорения запросов (keep-alive)
requests_session = requests.Session()
requests_session.headers.update({
    "User-Agent": "AnemoneBot/1.0"
})

DUMP_CHAT_ID = "-5129048838"  
DEFAULT_CHANNEL_ID = "-1001479526905" 

DEFAULT_MAX_POST_ID = 8504

# Простой кэш в оперативной памяти: {post_id: "url_картинки"}
# Сбрасывается при перезагрузке сервера, но это не страшно

import threading
from datetime import datetime
import sqlite3
# Простой кэш в оперативной памяти: {post_id: "url_картинки"}
# Сбрасывается при перезагрузке сервера, но это не страшно
# Глобальная блокировка для БД
DB_LOCK = threading.Lock()
# Семафор, чтобы не делать больше 1 запроса к API Телеграма одновременно
TG_API_LIMITER = threading.BoundedSemaphore(value=1)

def init_db():
    with DB_LOCK:
        conn = sqlite3.connect('anemone.db', check_same_thread=False)
        c = conn.cursor()
        # Создаем таблицу. Ключ: channel_id + post_id
        c.execute('''CREATE TABLE IF NOT EXISTS posts
                     (id TEXT PRIMARY KEY, 
                      url TEXT, 
                      width INTEGER, 
                      height INTEGER, 
                      caption TEXT, 
                      date TEXT, 
                      post_link TEXT,
                      timestamp REAL)''')
        conn.commit()
        conn.close()

init_db()

# Хелперы для БД
def get_cached_post(channel_id, post_id):
    key = f"{channel_id}_{post_id}"
    with DB_LOCK:
        conn = sqlite3.connect('anemone.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT * FROM posts WHERE id=?", (key,))
        row = c.fetchone()
        conn.close()
        if row:
            return {
                "url": row[1], "width": row[2], "height": row[3],
                "caption": row[4], "date": row[5], "post_link": row[6]
            }
    return None

def save_cached_post(channel_id, post_id, data):
    key = f"{channel_id}_{post_id}"
    with DB_LOCK:
        conn = sqlite3.connect('anemone.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO posts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (key, data['url'], data['width'], data['height'], 
                   data['caption'], data['date'], data['post_link'], time.time()))
        conn.commit()
        conn.close()


def get_image_from_telegram(post_id, custom_channel_id=None, req_id="Unknown"):
    t_start = time.time()
    post_id = str(post_id)
    target_channel = custom_channel_id if custom_channel_id else DEFAULT_CHANNEL_ID
    
    # --- 1. ПРОВЕРКА КЭША (Самый важный шаг) ---
    cached = get_cached_post(target_channel, post_id)
    if cached:
        logger.info(f"[{req_id}] DB HIT: {post_id}. Date: {cached['date']}")
        return cached

    # --- 2. СЕТЕВОЙ ЗАПРОС С ОГРАНИЧЕНИЕМ ---
    # Блокируем поток, если другой поток сейчас общается с Телеграмом.
    # Это предотвращает "взрыв" запросов.
    with TG_API_LIMITER:
        # Искусственная задержка (Jitter), чтобы не выглядеть как робот
        time.sleep(random.uniform(0.3, 0.7))
        
        forward_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/forwardMessage"
        params = {
            "chat_id": DUMP_CHAT_ID,
            "from_chat_id": target_channel, 
            "message_id": post_id,
            "disable_notification": True
        }
        
        forwarded_msg_id = None # ID сообщения в дамп-чате, чтобы потом удалить

        try:
            logger.info(f"[{req_id}] API Request: Forwarding {post_id}...")
            r = requests_session.post(forward_url, json=params, timeout=10)
            data = r.json()

            # Обработка 429 (Too Many Requests)
            if not data.get("ok"):
                if data.get("error_code") == 429:
                    retry = data.get("parameters", {}).get("retry_after", 5)
                    logger.warning(f"[{req_id}] RATELIMIT! TG said wait {retry}s")
                    # Если просят ждать — лучше просто вернуть ошибку сейчас, чем вешать сервер
                    return None
                
                logger.error(f"[{req_id}] TG Error: {data.get('description')}")
                # Если сообщение удалено или не найдено - запомним это как ошибку, чтобы не долбить снова
                # (Можно добавить запись в БД с пометкой 'deleted', но пока просто return)
                return None

            result = data["result"]
            forwarded_msg_id = result["message_id"] # Запоминаем ID копии

            # --- 3. ИЗВЛЕЧЕНИЕ ДАННЫХ ---
            
            # А) ДАТА (То, ради чего всё затевалось)
            # forward_date — дата оригинала. date — дата пересылки.
            origin_ts = result.get("forward_date") or result.get("date")
            date_str = datetime.fromtimestamp(origin_ts).strftime('%d.%m.%Y %H:%M') if origin_ts else ""

            # Б) ФОТО
            if "photo" not in result:
                logger.info(f"[{req_id}] No photo in message.")
                return None

            # Берем лучшее качество
            best_photo = sorted(result["photo"], key=lambda x: x["width"])[-1]
            file_id = best_photo["file_id"]
            
            # В) ОПИСАНИЕ
            caption = result.get("caption") or result.get("text") or ""
            
            # --- 4. ПОЛУЧЕНИЕ ССЫЛКИ (getFile) ---
            # getFile лимитируется отдельно и мягче, можно без жестких пауз
            file_r = requests_session.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}", timeout=10)
            file_data = file_r.json()
            
            if file_data.get("ok"):
                file_path = file_data["result"]["file_path"]
                # Формируем ссылку через прокси
                full_tg_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
                final_url = f"https://wsrv.nl/?url={full_tg_url}&n=-1"

                res_obj = {
                    "url": final_url,
                    "width": best_photo["width"],
                    "height": best_photo["height"],
                    "caption": caption[:200], # Обрезаем слишком длинные
                    "date": date_str,
                    "post_link": f"https://t.me/{target_channel.replace('@', '')}/{post_id}"
                }

                # --- 5. СОХРАНЕНИЕ В ВЕЧНЫЙ КЭШ ---
                save_cached_post(target_channel, post_id, res_obj)
                
                # --- 6. ЧИСТКА (Удаляем пересланное сообщение из дампа) ---
                # Это хорошая практика, чтобы не засорять чат и не привлекать внимание алгоритмов
                try:
                    del_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage"
                    requests_session.post(del_url, json={"chat_id": DUMP_CHAT_ID, "message_id": forwarded_msg_id})
                except:
                    pass # Не критично, если не удалилось

                return res_obj

        except Exception as e:
            logger.error(f"[{req_id}] Error: {e}")
            return None
            
    return None




@app.route('/api/anemone/resolve_image')
def api_resolve_image():
    # Генерируем короткий ID запроса (например, a1b2) для удобства чтения логов
    req_id = str(uuid.uuid4())[:8]
    
    post_id = request.args.get('post_id')
    channel_id = request.args.get('channel_id')
    
    logger.info(f"[{req_id}] START Resolve: Post {post_id} (Chan: {channel_id})")
    
    img_data = get_image_from_telegram(post_id, custom_channel_id=channel_id, req_id=req_id)
    
    if img_data and "error" in img_data and img_data["error"] == "access_denied":
        logger.info(f"[{req_id}] Access Denied response sent.")
        return jsonify({"found": False, "error": "access_denied"})

    if img_data:
        from urllib.parse import quote
        encoded = quote(img_data['url'])
        # Мы добавляем req_id в ссылку прокси, чтобы отследить и второй этап загрузки!
        return jsonify({
            "found": True,
            "url": img_data['url'],
            "width": img_data['width'],
            "height": img_data['height'],
            "caption": img_data.get('caption', ''),
            "date": img_data.get('date', ''),
            "post_link": img_data.get('post_link', '')
        })
    
    logger.warning(f"[{req_id}] Not found response sent.")
    return jsonify({"found": False})

@app.route('/api/proxy_image')
def proxy_image():
    url = request.args.get('url')
    # Получаем ID из параметра, если он есть, для связности логов
    req_id = request.args.get('req_id', 'proxy_unknown')
    
    if not url: return "No URL", 400
    
    # Логируем начало скачивания самой картинки
    logger.info(f"[{req_id}] PROXY START downloading image content...")
    t_start = time.time()
    
    try:
        # stream=True ОЧЕНЬ ВАЖЕН для больших картинок
        req = requests_session.get(url, stream=True, timeout=15)
        
        if req.status_code != 200:
             logger.error(f"[{req_id}] PROXY ERROR. TG status: {req.status_code}")
             return f"Telegram Error {req.status_code}", req.status_code

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in req.raw.headers.items()
                   if name.lower() not in excluded_headers]
        
        headers.append(('Access-Control-Allow-Origin', '*'))
        headers.append(('Cache-Control', 'public, max-age=3300')) 

        def generate():
            bytes_transferred = 0
            try:
                for chunk in req.iter_content(chunk_size=65536):
                    if chunk:
                        bytes_transferred += len(chunk)
                        yield chunk
                # Логируем успех ТОЛЬКО когда все байты отданы
                total_time = time.time() - t_start
                logger.info(f"[{req_id}] PROXY DONE. Transferred {bytes_transferred/1024:.1f} KB in {total_time:.2f}s")
            except Exception as e:
                logger.error(f"[{req_id}] PROXY STREAM ERROR: {e}")
                
        return Response(stream_with_context(generate()),
                        status=req.status_code,
                        headers=headers,
                        content_type=req.headers.get('content-type'))
                        
    except Exception as e:
        logger.error(f"[{req_id}] PROXY CONNECTION ERROR: {e}")
        return str(e), 500


import random
import requests
from flask import Response, stream_with_context

# --- ДОБАВЬТЕ ЭТИ ФУНКЦИИ В НАЧАЛО ФАЙЛА ИЛИ В HELPER ---

# --- ИСПРАВЛЕННЫЕ ЭНДПОИНТЫ ---

@app.route('/api/anemone/get_chunk', methods=['GET'])
def api_get_anemone_chunk():
    try:
        cx = int(request.args.get('x', 0))
        cy = int(request.args.get('y', 0))
        cz = int(request.args.get('z', 0))
        
        channel_id = request.args.get('channel_id', 'default_world')

        req_max_id = request.args.get('max_id')
        if req_max_id and req_max_id.isdigit():
            max_limit = int(req_max_id)
        else:
            max_limit = DEFAULT_MAX_POST_ID
            
    except ValueError:
        return jsonify([])

    # 1. Формируем уникальную строку сида
    seed_str = f"{channel_id}_{cx}_{cy}_{cz}"
    
    # 2. Генератор
    rng = random.Random(seed_str)

    # 3. ЛОГИКА СФЕРИЧЕСКОГО РАСПРЕДЕЛЕНИЯ
    # Считаем расстояние от центра (0,0,0) в "чанках"
    dist = math.sqrt(cx**2 + cy**2 + cz**2)
    
    # Коэффициент плотности. 
    # 0.8 - посты стоят плотнее, 1.5 - посты разлетаются шире.
    # Можно подстроить под себя.
    density_factor = 0.9 
    
    # Вычисляем, какие ID должны быть в этом радиусе "по идее".
    # Используем кубическую зависимость (dist^3), чтобы заполнять объем сферы равномерно.
    # +1 гарантирует, что в центре (dist=0) ID начнутся с 1.
    min_theoretical_id = int((dist * density_factor) ** 3) + 1
    max_theoretical_id = int(((dist + 1.2) * density_factor) ** 3) + 5
    
    # Определяем режим для этого чанка:
    # ЯДРО (Core) или ХАОС (Chaos)
    is_core = min_theoretical_id <= max_limit
    
    # Генерируем объекты
    items_count = rng.randint(2, 4)
    chunk_size = 1500 
    
    planes = []
    
    for i in range(items_count):
        px = rng.uniform(-chunk_size/2, chunk_size/2)
        py = rng.uniform(-chunk_size/2, chunk_size/2)
        pz = rng.uniform(-chunk_size/2, chunk_size/2)
        scale = rng.uniform(100, 300)

        # === ГЛАВНОЕ ИЗМЕНЕНИЕ ЗДЕСЬ ===
        if is_core:
            # Мы внутри "изученной вселенной". 
            # Выдаем ID, который строго привязан к этому расстоянию.
            # Ограничиваем верхнюю планку max_limit, чтобы не выйти за пределы.
            eff_max = min(max_theoretical_id, max_limit)
            
            # Защита: если min > eff_max (крайний случай на границе), берем eff_max
            eff_min = min(min_theoretical_id, eff_max)
            
            random_msg_id = rng.randint(eff_min, eff_max)
        else:
            # Мы в "дальнем космосе" (за пределами max_limit).
            # Генерируем случайные дубликаты из всего доступного пула.
            random_msg_id = rng.randint(1, max_limit)
        # ===============================

        planes.append({
            "id": f"{cx}_{cy}_{cz}_{i}", 
            "pos": [px, py, pz],
            "scale": [scale, scale * 1.5],
            "post_id": random_msg_id,
            "rotation": [rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), 0]
        })

    return jsonify({
        "cx": cx, "cy": cy, "cz": cz,
        "items": planes
    })

@app.route('/api/anemone/add_comment', methods=['POST'])
def api_add_comment():
    from gpt_helper import add_anemone_comment
    data = request.json
    
    # channel_id передается с фронта (из URL)
    res = add_anemone_comment(
        data.get('channel_id'),
        data.get('text'),
        data.get('x'),
        data.get('y'),
        data.get('z')
    )
    
    if res:
        return jsonify({"status": "success", "data": res})
    return jsonify({"status": "error"}), 500

@app.route('/api/anemone/get_comments', methods=['GET'])
def api_get_comments():
    from gpt_helper import get_anemone_comments
    channel_id = request.args.get('channel_id')
    comments = get_anemone_comments(channel_id)
    return jsonify(comments)










@app.route('/anemonearts')
def anemone_arts_view():
    """Отдает HTML страницу бесконечного холста"""
    return send_from_directory(app.static_folder, 'anemone.html')



@app.route('/api/timer/get_one', methods=['GET'])
def api_get_one_timer():
    from gpt_helper import get_single_media
    
    user_id = request.args.get('user_id')
    media_id = request.args.get('media_id')
    
    if not user_id or not media_id:
        return jsonify({"error": "Missing params"}), 400
        
    data = get_single_media(user_id, media_id)
    if data:
        # Возвращаем данные, добавляя ID внутрь объекта для удобства фронта
        data['id'] = media_id 
        return jsonify(data)
    else:
        return jsonify({"error": "Not found"}), 404



@app.route('/api/timer/get_all', methods=['GET'])
def api_get_timers():
    from gpt_helper import get_user_timers  # импорт внутри функции
    
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "No user_id provided"}), 400
    
    data = get_user_timers(user_id)
    return jsonify(data)


@app.route('/api/timer/create_media', methods=['POST'])
def api_create_media():
    from gpt_helper import add_new_media  # импорт внутри функции

    data = request.json
    user_id = data.get('user_id')
    title = data.get('title')
    m_type = data.get('type', 'movie')
    
    if not user_id or not title:
        return jsonify({"error": "Missing data"}), 400
        
    media_id = add_new_media(user_id, title, m_type)
    if media_id:
        return jsonify({"status": "success", "media_id": media_id})
    else:
        return jsonify({"status": "error"}), 500



@app.route('/api/timer/update_media_title', methods=['POST'])
def api_update_media_title():
    from gpt_helper import update_media_title
    
    data = request.json
    user_id = data.get('user_id')
    media_id = data.get('media_id')
    title = data.get('title')

    if not user_id or not media_id or not title:
        return jsonify({"error": "missing params"}), 400

    ok = update_media_title(user_id, media_id, title)
    return jsonify({"status": "success" if ok else "error"})


@app.route('/api/timer/add_entry', methods=['POST'])
def api_add_entry():
    from gpt_helper import add_timer_entry 

    data = request.json
    
    # ИЗМЕНЕНИЕ: Получаем список file_ids
    # Если фронтенд прислал старый file_id, превращаем его в список
    f_ids = data.get('file_ids', [])
    if not f_ids and data.get('file_id'):
        f_ids = [data.get('file_id')]

    res = add_timer_entry(
        user_id=data.get('user_id'),
        media_id=data.get('media_id'),
        note_text=data.get('text'),
        timestamp=data.get('timestamp'),
        episode=data.get('episode'),
        file_ids=f_ids  # Передаем список
    )
    return jsonify({"status": "success" if res else "error", "key": res})

@app.route('/api/timer/delete', methods=['DELETE'])
def api_delete_media():
    from gpt_helper import delete_media  # импорт внутри функции

    user_id = request.args.get('user_id')
    media_id = request.args.get('media_id')
    
    if delete_media(user_id, media_id):
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 500


# --- WEBAPP ROUTING (Маршруты для веб-приложений) ---

from flask import send_file
from io import BytesIO

# --- НОВЫЕ API ENDPOINTS ---

@app.route('/api/media/upload_image', methods=['POST'])
def api_upload_image():
    from gpt_helper import upload_file_to_telegram
    
    if 'image' not in request.files:
        return jsonify({"error": "No image"}), 400
        
    file = request.files['image']
    user_id = request.form.get('user_id') 
    
    if not user_id:
        return jsonify({"error": "No user_id"}), 400

    # Отправляем фото пользователю в чат
    file_id = upload_file_to_telegram(file, user_id)
    
    if file_id:
        return jsonify({"status": "success", "file_id": file_id})
    return jsonify({"status": "error", "message": "Telegram upload failed"}), 500


@app.route('/api/media/get_image_url', methods=['GET'])
def api_get_image_url():
    # Фронтенд просит ссылку на картинку по file_id
    from gpt_helper import get_telegram_file_link
    file_id = request.args.get('file_id')
    if not file_id:
        return jsonify({"error": "No id"}), 400
        
    link = get_telegram_file_link(file_id) # Функция выше
    if link:
        return jsonify({"url": link})
    return jsonify({"error": "Not found"}), 404



@app.route('/')
def home():
    return "Bot Server is Running. <br> Available apps: /timer-app"


@app.route('/timer-app/', defaults={'path': ''})
@app.route('/timer-app/<path:path>')
def serve_timer_app(path):
    full_path = os.path.join(app.static_folder, path)
    if path != "" and os.path.exists(full_path):
        return send_from_directory(app.static_folder, path)

    return send_from_directory(app.static_folder, 'timer_index.html')

@app.route('/api/timer/update_entry', methods=['POST'])
def api_update_entry():
    from gpt_helper import update_timer_entry
    data = request.json
    
    # ИЗМЕНЕНИЕ: Обработка списка
    f_ids = data.get('file_ids') # Может быть None, если не меняли картинки

    success = update_timer_entry(
        user_id=data.get('user_id'),
        media_id=data.get('media_id'),
        entry_id=data.get('entry_id'),
        text=data.get('text'),
        timestamp=data.get('timestamp'),
        file_ids=f_ids # Передаем в helper
    )
    return jsonify({"status": "success" if success else "error"})


@app.route('/api/timer/delete_entry', methods=['DELETE'])
def api_delete_entry():
    from gpt_helper import delete_timer_entry
    
    user_id = request.args.get('user_id')
    media_id = request.args.get('media_id')
    entry_id = request.args.get('entry_id')
    
    if delete_timer_entry(user_id, media_id, entry_id):
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 500

@app.route('/musicplayer/<user_id>/<message_id>')
def serve_music_player(user_id, message_id):
    """
    Отдает HTML страницу плеера.
    """
    # Проверка: если message_id заканчивается на .js или .css, значит 
    # браузер ошибся путем и просит статику. Игнорируем или отдаем 404, 
    # но лучше просто отдать HTML, а пути в HTML мы исправим ниже.
    return send_from_directory(app.static_folder, 'music_player.html')


@app.route('/api/music/get_playlist', methods=['GET'])
def api_get_playlist():
    from gpt_helper import get_specific_music_post, get_telegram_file_url
    
    user_id = request.args.get('user_id')
    message_id = request.args.get('message_id')
    
    if not user_id or not message_id:
        return jsonify({"error": "Missing params"}), 400

    post = get_specific_music_post(user_id, message_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    # 1. Формируем список треков
    tracks = []
    music_media = post.get('musicmedia', [])
    
    for item in music_media:
        f_id = item.get('file_id')
        name = item.get('music_name', 'Unknown Track')
        
        if f_id:
            url = get_telegram_file_url(f_id)
            if url:
                tracks.append({
                    "title": name,
                    "url": url
                })
    
    # 2. Формируем список обложек (ВСЕ картинки)
    covers = []
    if 'media' in post:
        for m in post['media']:
            media_file_id = m.get('file_id')
            if not media_file_id:
                continue
            
            # Если это уже ссылка
            if media_file_id.startswith('http'):
                covers.append(media_file_id)
            else:
                # Резолвим file_id
                img_url = get_telegram_file_url(media_file_id)
                if img_url:
                    covers.append(img_url)

    # Если картинок нет, добавляем заглушку, чтобы слайдер не был пустым (опционально)
    if not covers:
        covers.append("https://via.placeholder.com/400x400/1c1c1e/333?text=Music")

    return jsonify({
        "status": "success",
        "tracks": tracks,
        "covers": covers  # Возвращаем массив
    })


@app.route('/musicplayer/')
def music_player_root():
    """
    Если открыли просто /musicplayer/ без ID — покажем ошибку, 
    чтобы не было пустой 404 страницы.
    """
    return "Ошибка: Не указан ID пользователя и сообщения. Ссылка должна быть вида /musicplayer/user_id/message_id"

@app.route('/other-app/', defaults={'path': ''})
@app.route('/other-app/<path:path>')
def serve_other_app(path):
    return "This is a future app placeholder"


# --- SERVER STARTUP ---

# --- SERVER STARTUP ---
def run():
    # Вместо app.run(...) используем serve(...)
    # threads=6 означает, что сервер сможет обрабатывать 6 запросов одновременно
    logger.info("Starting Waitress server with 6 threads...")
    serve(app, host="0.0.0.0", port=80, threads=6)

def keep_alive():
    t = Thread(target=run)
    t.start()
