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
IMAGE_CACHE = {} 
from datetime import datetime

# --- ЗАМЕНА ФУНКЦИИ get_image_from_telegram ---
def get_image_from_telegram(post_id, custom_channel_id=None, req_id="Unknown"):
    t_start = time.time()
    post_id = str(post_id)
    target_channel = custom_channel_id if custom_channel_id else DEFAULT_CHANNEL_ID
    
    cache_key = f"{target_channel}_{post_id}"
    
    # 1. ЛОГИРОВАНИЕ КЭША
    if cache_key in IMAGE_CACHE:
        cached_item = IMAGE_CACHE[cache_key]
        if cached_item is None:
            logger.warning(f"[{req_id}] Cache HIT (None value) for {post_id}. Removing invalid cache.")
            del IMAGE_CACHE[cache_key]
        elif (time.time() - cached_item.get("cached_at", 0)) > 3300:
            logger.info(f"[{req_id}] Cache EXPIRED for {post_id} (Age: {int(time.time() - cached_item.get('cached_at', 0))}s). Refreshing...")
            del IMAGE_CACHE[cache_key]
        else:
            logger.info(f"[{req_id}] Cache HIT for {post_id}. Took {time.time() - t_start:.4f}s")
            return cached_item

    # Подготовка запроса
    forward_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/forwardMessage"
    params = {
        "chat_id": DUMP_CHAT_ID,
        "from_chat_id": target_channel, 
        "message_id": post_id,
        "disable_notification": True
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"[{req_id}] Attempt {attempt+1}/{max_retries}: Forwarding msg {post_id}...")
            
            t_req = time.time()
            # 2. ЗАМЕР ЗАПРОСА forwardMessage
            r = requests_session.post(forward_url, json=params, timeout=10)
            dur = time.time() - t_req
            
            logger.info(f"[{req_id}] Forward API took {dur:.3f}s. Status: {r.status_code}")

            data = r.json()
            
            if not data.get("ok"):
                error_code = data.get("error_code")
                desc = data.get("description", "")

                if error_code == 429:
                    retry_after = data.get("parameters", {}).get("retry_after", 1)
                    logger.warning(f"[{req_id}] RATE LIMIT (429). TG asks to wait {retry_after}s.")
                    
                    if retry_after > 5: 
                        logger.error(f"[{req_id}] Aborting: Wait time too long ({retry_after}s).")
                        break 
                    
                    time.sleep(retry_after + 0.5)
                    continue 
                
                if "chat not found" in desc.lower() or "kicked" in desc.lower():
                    logger.error(f"[{req_id}] Access Denied: {desc}")
                    return {"error": "access_denied"}
                
                logger.error(f"[{req_id}] TG API Error: {desc}")
                return None
                
            result = data["result"]
            
            # Логика поиска file_id (сокращена для ясности, оставьте вашу логику парсинга)
            # ... (ВАШ КОД ПАРСИНГА ОСТАЕТСЯ ТЕМ ЖЕ) ...
            # Но добавьте логирование, если файл не найден:
            
            # --- Вставьте сюда ваш блок поиска file_id, width, height ---
            # Для примера:
            file_id = None
            width = 1
            height = 1
            caption = result.get("caption", "") or result.get("text", "")
            
            # (Скопируйте вашу логику поиска photo/document сюда)
            if "photo" in result:
                photo = sorted(result["photo"], key=lambda x: x["width"])[-1]
                file_id = photo["file_id"]
                width = photo["width"]
                height = photo["height"]
            elif "document" in result and result["document"]["mime_type"].startswith("image"):
                 file_id = result["document"]["file_id"]
                 if "thumb" in result["document"]:
                     width = result["document"]["thumb"]["width"]
                     height = result["document"]["thumb"]["height"]
            # -----------------------------------------------------------

            if not file_id:
                logger.warning(f"[{req_id}] No image found in message {post_id}.")
                return None

            # 3. ЗАМЕР ЗАПРОСА getFile
            logger.info(f"[{req_id}] Getting File Path for {file_id[:10]}...")
            t_path = time.time()
            path_r = requests_session.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}", timeout=10)
            logger.info(f"[{req_id}] getFile API took {time.time() - t_path:.3f}s")
            
            path_data = path_r.json()
            
            if path_data.get("ok"):
                file_path = path_data["result"]["file_path"]
                full_tg_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"

                # Оборачиваем через публичный прокси
                # n=-1 отключает оптимизацию (чтобы не портить качество), но можно убрать
                final_url = f"https://wsrv.nl/?url={full_tg_url}&n=-1"
                
                # ... формирование даты и ссылок (ваш код) ...
                origin_date = result.get("forward_date") or result.get("date")
                date_str = datetime.fromtimestamp(origin_date).strftime('%d.%m.%Y %H:%M') if origin_date else ""
                
                res_obj = {
                    "url": final_url,
                    "width": width,
                    "height": height,
                    "caption": caption[:100],
                    "date": date_str,
                    "post_link": f"https://t.me/{target_channel.replace('@', '')}/{post_id}",
                    "cached_at": time.time()
                }
                IMAGE_CACHE[cache_key] = res_obj
                
                total_time = time.time() - t_start
                logger.info(f"[{req_id}] SUCCESS. Total resolve time: {total_time:.3f}s")
                return res_obj
            else:
                 logger.error(f"[{req_id}] getFile Failed: {path_data}")
                 break
                 
        except Exception as e:
            logger.error(f"[{req_id}] EXCEPTION in attempt {attempt}: {e}")
            time.sleep(1)

    logger.error(f"[{req_id}] FAILED after retries. Time: {time.time() - t_start:.3f}s")
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
