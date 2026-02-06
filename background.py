from flask import Flask, request, jsonify, send_from_directory, make_response
from threading import Thread
import os
import logging
from flask import render_template_string
app = Flask(__name__, static_folder='static')  # Указываем папку для статики
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN не задан в переменных окружения")


# --- API ENDPOINTS (Точки для работы с данными) ---

import random
import requests
from flask import Response, stream_with_context
import random
import hashlib

DUMP_CHAT_ID = "5129048838"  
CHANNEL_ID = "-1001479526905" 

MAX_POST_ID = 8504

# Простой кэш в оперативной памяти: {post_id: "url_картинки"}
# Сбрасывается при перезагрузке сервера, но это не страшно
IMAGE_CACHE = {} 

def get_image_from_telegram(post_id):
    """
    1. Проверяет кэш.
    2. Если нет в кэше, пересылает пост в Dump Chat.
    3. Извлекает file_id и получает ссылку.
    """
    post_id = str(post_id)
    
    # 1. Проверка кэша (чтобы не спамить API)
    if post_id in IMAGE_CACHE:
        return IMAGE_CACHE[post_id]

    # 2. Формируем запрос на Forward
    forward_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/forwardMessage"
    params = {
        "chat_id": DUMP_CHAT_ID,      # Куда пересылаем (скрытый чат)
        "from_chat_id": CHANNEL_ID,   # Откуда (основной канал)
        "message_id": post_id,
        "disable_notification": True  # Без звука
    }
    
    try:
        r = requests.post(forward_url, json=params)
        data = r.json()
        
        if not data.get("ok"):
            # Пост удален или не существует
            IMAGE_CACHE[post_id] = None # Запоминаем, что поста нет
            return None
            
        result = data["result"]
        file_id = None
        
        # 3. Ищем картинку в сообщении
        if "photo" in result:
            # Берем последнее фото (самое высокое качество)
            file_id = result["photo"][-1]["file_id"]
        elif "document" in result and result["document"]["mime_type"].startswith("image"):
            # Если отправлено как файл (без сжатия)
            file_id = result["document"]["file_id"]
        elif "video" in result:
             # Можно брать превью видео
             file_id = result["video"]["thumb"]["file_id"]

        if not file_id:
            IMAGE_CACHE[post_id] = None # Это текст, картинки нет
            return None

        # 4. Получаем путь к файлу (getFile)
        path_r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}")
        path_data = path_r.json()
        
        if path_data.get("ok"):
            file_path = path_data["result"]["file_path"]
            # Ссылка на скачивание (живет 1 час)
            full_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
            
            # Сохраняем в кэш
            IMAGE_CACHE[post_id] = full_url
            return full_url
            
    except Exception as e:
        logging.error(f"Telegram Forward Error: {e}")
        
    return None


@app.route('/api/anemone/resolve_image')
def api_resolve_image():
    """
    Эндпоинт, который вызывает JS для каждого квадрата.
    """
    post_id = request.args.get('post_id')
    
    # Пытаемся получить реальную ссылку
    tg_url = get_image_from_telegram(post_id)
    
    if tg_url:
        # ВАЖНО: Мы отдаем ссылку на НАШ ПРОКСИ, а не на Telegram.
        # Потому что Telegram не дает заголовки CORS, и WebGL (Three.js) выдаст ошибку.
        from urllib.parse import quote
        encoded = quote(tg_url)
        return jsonify({"url": f"/api/proxy_image?url={encoded}"})
    
    # Если поста нет или в нем нет картинки -> возвращаем случайную заглушку
    # (чтобы в 3D мире не было дырок)
    return jsonify({"url": f"https://picsum.photos/seed/{post_id}/400/600"})


@app.route('/api/proxy_image')
def proxy_image():
    """
    Прокси-сервер. Скачивает картинку у Telegram и отдает браузеру 
    с разрешением CORS (Access-Control-Allow-Origin).
    """
    url = request.args.get('url')
    if not url: return "No URL", 400
    
    try:
        # Скачиваем потоком (stream=True), чтобы не грузить оперативку сервера
        req = requests.get(url, stream=True, timeout=10)
        
        # Фильтруем заголовки (hop-by-hop headers нельзя передавать)
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in req.raw.headers.items()
                   if name.lower() not in excluded_headers]
        
        # Разрешаем доступ отовсюду
        headers.append(('Access-Control-Allow-Origin', '*'))
        headers.append(('Cache-Control', 'public, max-age=3600')) # Кэш браузера на час

        return Response(stream_with_context(req.iter_content(chunk_size=1024)),
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
    except ValueError:
        return jsonify([])

    # Детерминированная случайность на основе координат
    seed_str = f"{cx},{cy},{cz}"
    seed_int = int(hashlib.sha256(seed_str.encode('utf-8')).hexdigest(), 16) % 10**8
    random.seed(seed_int)

    items_count = random.randint(2, 4) # Чуть меньше, чтобы не спамить API
    chunk_size = 1000
    
    planes = []
    
    for i in range(items_count):
        px = random.uniform(-chunk_size/2, chunk_size/2)
        py = random.uniform(-chunk_size/2, chunk_size/2)
        pz = random.uniform(-chunk_size/2, chunk_size/2)
        scale = random.uniform(100, 300)

        # Генерируем ID поста. Убедитесь, что MAX_POST_ID актуален.
        # Лучше брать диапазон ближе к концу, там больше живых картинок.
        random_msg_id = random.randint(100, MAX_POST_ID) 

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

def run():
    app.run(host='0.0.0.0', port=80)

def keep_alive():
    t = Thread(target=run)
    t.start()
