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

# --- API ENDPOINTS (Точки для работы с данными) ---

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

# --- ЗАМЕНИТЬ ФУНКЦИЮ get_image_from_telegram ---
def get_image_from_telegram(post_id, custom_channel_id=None):
    post_id = str(post_id)
    target_channel = custom_channel_id if custom_channel_id else DEFAULT_CHANNEL_ID
    
    cache_key = f"{target_channel}_{post_id}"
    current_time = time.time()

    # 1. ПРОВЕРКА КЭША С УЧЕТОМ ВРЕМЕНИ ЖИЗНИ (ССЫЛКИ ЖИВУТ 1 ЧАС)
    if cache_key in IMAGE_CACHE:
        cached_item = IMAGE_CACHE[cache_key]
        # Если записано None (предыдущая ошибка) — удаляем и пробуем снова
        if cached_item is None:
            del IMAGE_CACHE[cache_key]
        # Если ссылка старше 55 минут (3300 сек) — удаляем и обновляем, иначе она вернет 404
        elif (current_time - cached_item.get("cached_at", 0)) > 3300:
            logger.info(f" [TG CACHE] Expired for {cache_key}, refreshing...")
            del IMAGE_CACHE[cache_key]
        else:
            # logger.info(f" [TG CACHE] Hit for {cache_key}") # Можно раскомментировать для дебага
            return cached_item

    forward_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/forwardMessage"
    params = {
        "chat_id": DUMP_CHAT_ID,
        "from_chat_id": target_channel, 
        "message_id": post_id,
        "disable_notification": True
    }
    
    # 2. ЦИКЛ ПОВТОРНЫХ ПОПЫТОК (RETRY LOOP)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Используем session для скорости
            r = requests_session.post(forward_url, json=params, timeout=10)
            data = r.json()
            
            # ОБРАБОТКА ОГРАНИЧЕНИЙ TELEGRAM (429 Too Many Requests)
            if not data.get("ok"):
                error_code = data.get("error_code")
                desc = data.get("description", "")

                if error_code == 429:
                    # Telegram часто пишет "Retry in X seconds"
                    retry_after = data.get("parameters", {}).get("retry_after", 1)
                    # Если sleep слишком долгий, лучше прервать, чтобы не висел поток
                    if retry_after > 5: 
                        logger.warning(f" [TG RATE LIMIT] Too long wait ({retry_after}s) for {post_id}")
                        break 
                    
                    time.sleep(retry_after + 0.5) # Ждем и пробуем снова
                    continue
                
                # Если ошибки доступа - возвращаем сразу
                if "chat not found" in desc.lower() or "kicked" in desc.lower():
                    return {"error": "access_denied"}
                
                logger.error(f" [TG ERROR] {desc} (Post: {post_id})")
                return None
                
            result = data["result"]
            
            # --- СБОР ДАННЫХ (Ваш код логики даты/ссылок) ---
            origin_date = result.get("forward_date") or result.get("date")
            date_str = datetime.fromtimestamp(origin_date).strftime('%d.%m.%Y %H:%M') if origin_date else ""

            post_link = ""
            if "forward_from_chat" in result and "username" in result["forward_from_chat"]:
                orig_username = result["forward_from_chat"]["username"]
                orig_id = result.get("forward_from_message_id", post_id)
                post_link = f"https://t.me/{orig_username}/{orig_id}"
            elif target_channel.startswith("@"):
                clean_username = target_channel.replace("@", "")
                post_link = f"https://t.me/{clean_username}/{post_id}"

            # Поиск фото или документа
            file_id = None
            width = 1
            height = 1
            caption = result.get("caption", "") or result.get("text", "")

            if "photo" in result:
                photo = sorted(result["photo"], key=lambda x: x["width"])[-1] # Берем самое большое
                if photo["width"] > 100: # Отсекаем миниатюры если есть выбор
                    file_id = photo["file_id"]
                    width = photo["width"]
                    height = photo["height"]
            elif "document" in result and result["document"]["mime_type"].startswith("image"):
                 file_id = result["document"]["file_id"]
                 if "thumb" in result["document"]:
                     width = result["document"]["thumb"]["width"]
                     height = result["document"]["thumb"]["height"]

            if not file_id:
                # Сообщение есть, но картинки нет - кэшируем пустоту, чтобы не долбить API
                # IMAGE_CACHE[cache_key] = None # Лучше не кэшировать None, пусть пробует потом
                return None

            # 3. ПОЛУЧЕНИЕ ПУТИ ФАЙЛА (GetFile)
            path_r = requests_session.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}", timeout=10)
            path_data = path_r.json()
            
            if path_data.get("ok"):
                file_path = path_data["result"]["file_path"]
                full_tg_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"

                # Оборачиваем через публичный прокси
                # n=-1 отключает оптимизацию (чтобы не портить качество), но можно убрать
                final_url = f"https://wsrv.nl/?url={full_tg_url}&n=-1"
                res_obj = {
                    "url": final_url,
                    "width": width,
                    "height": height,
                    "caption": caption[:100],
                    "date": date_str,
                    "post_link": post_link,
                    "cached_at": time.time() # <--- ВАЖНО: Запоминаем время создания ссылки
                }
                IMAGE_CACHE[cache_key] = res_obj
                return res_obj
            else:
                 # Если getFile упал (редко), тоже можно retry, но пока просто break
                 break
                 
        except Exception as e:
            logger.error(f"Telegram Fetch Error ({post_id}): {e}")
            time.sleep(1) # Короткая пауза перед повтором при сетевой ошибке

    return None

@app.route('/api/anemone/resolve_image')
def api_resolve_image():
    post_id = request.args.get('post_id')
    channel_id = request.args.get('channel_id')
    
    img_data = get_image_from_telegram(post_id, custom_channel_id=channel_id)
    
    if img_data and "error" in img_data and img_data["error"] == "access_denied":
        return jsonify({"found": False, "error": "access_denied"})

    if img_data:
        from urllib.parse import quote
        encoded = quote(img_data['url'])
        
        return jsonify({
            "found": True,
            "url": f"/api/proxy_image?url={encoded}",
            "width": img_data['width'],
            "height": img_data['height'],
            "caption": img_data.get('caption', ''),
            "date": img_data.get('date', ''),
            "post_link": img_data.get('post_link', '') # Передаем ссылку
        })
    
    return jsonify({"found": False})

@app.route('/api/proxy_image')
def proxy_image():
    """
    Прокси-сервер. Скачивает картинку у Telegram и отдает браузеру 
    с разрешением CORS.
    """
    url = request.args.get('url')
    if not url: return "No URL", 400
    
    try:
        # Используем глобальную сессию и таймаут
        req = requests_session.get(url, stream=True, timeout=15)
        
        # Если ссылка протухла (Telegram вернул 404), прокси упадет,
        # и фронтенд увидит ошибку. (В идеале нужно чистить кэш тут, но это сложнее)
        if req.status_code != 200:
             return f"Telegram Error {req.status_code}", req.status_code

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in req.raw.headers.items()
                   if name.lower() not in excluded_headers]
        
        headers.append(('Access-Control-Allow-Origin', '*'))
        # Кэшируем в браузере на 55 минут (чуть меньше жизни ссылки TG)
        headers.append(('Cache-Control', 'public, max-age=3300')) 

        return Response(stream_with_context(req.iter_content(chunk_size=65536)),
                        status=req.status_code,
                        headers=headers,
                        content_type=req.headers.get('content-type'))
    except Exception as e:
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
        
        # Читаем max_id из запроса или берем дефолтный
        # Frontend должен передавать этот параметр
        req_max_id = request.args.get('max_id')
        if req_max_id and req_max_id.isdigit():
            max_limit = int(req_max_id)
        else:
            max_limit = DEFAULT_MAX_POST_ID
            
    except ValueError:
        return jsonify([])

    seed_str = f"{cx},{cy},{cz}"
    seed_int = int(hashlib.sha256(seed_str.encode('utf-8')).hexdigest(), 16) % 10**8
    random.seed(seed_int)

    items_count = random.randint(2, 4)
    chunk_size = 1500 # У вас в JS 1500, тут было 1000, лучше синхронизировать
    
    planes = []
    
    for i in range(items_count):
        px = random.uniform(-chunk_size/2, chunk_size/2)
        py = random.uniform(-chunk_size/2, chunk_size/2)
        pz = random.uniform(-chunk_size/2, chunk_size/2)
        scale = random.uniform(100, 300)

        # Генерируем ID на основе переданного лимита
        # max_limit берется из URL
        random_msg_id = random.randint(1, max_limit) 

        planes.append({
            "id": f"{cx}_{cy}_{cz}_{i}",
            "pos": [px, py, pz],
            "scale": [scale, scale * 1.5],
            "post_id": random_msg_id,
            "rotation": [random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), 0]
        })

    return jsonify({
        "cx": cx, "cy": cy, "cz": cz,
        "items": planes
    })











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
