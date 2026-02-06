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

# --- ДОБАВЬТЕ ЭТИ ФУНКЦИИ В НАЧАЛО ФАЙЛА ИЛИ В HELPER ---

def get_real_image_url_from_channel(channel_id, message_id):
    """
    Пытается получить URL картинки из сообщения в канале.
    Т.к. getMessage нет, мы используем трюк: 
    Мы (бот) пытаемся переслать сообщение в чат к самому себе (или просто получить его, если библиотека позволяет).
    Но самый надежный способ через HTTP API без базы - это forwardMessage.
    """
    # 1. Пытаемся скопировать/переслать сообщение, чтобы получить его содержимое
    # Мы пересылаем сообщение в "никуда" (в чат с самим ботом нельзя, нужен chat_id).
    # Лучше всего использовать ID админа или лог-канала.
    # Если бот админ канала, он может видеть сообщения, но API не дает метода getMessage.
    # ЕДИНСТВЕННЫЙ способ получить file_id старого поста без БД - переслать его.
    
    # ВАЖНО: Замените YOUR_LOG_CHAT_ID на ваш ID (личка с ботом) или ID технического канала.
    # Бот должен быть там админом или участником.
    LOG_CHAT_ID = os.environ.get("LOG_CHAT_ID") # Или жестко пропишите ID цифрами
    
    if not LOG_CHAT_ID:
        # Если нет лог-чата, возвращаем заглушку, чтобы не крашилось
        return None 

    forward_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/forwardMessage"
    params = {
        "chat_id": LOG_CHAT_ID,
        "from_chat_id": channel_id,
        "message_id": message_id,
        "disable_notification": True
    }
    
    try:
        r = requests.post(forward_url, json=params)
        data = r.json()
        
        if not data.get("ok"):
            # Сообщение удалено или это не сообщение
            return None
            
        result = data["result"]
        
        # Проверяем, есть ли фото
        file_id = None
        if "photo" in result:
            file_id = result["photo"][-1]["file_id"] # Берем самое большое качество
        elif "document" in result and result["document"]["mime_type"].startswith("image"):
            file_id = result["document"]["file_id"]
            
        if file_id:
            # Получаем file_path
            path_r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}")
            path_data = path_r.json()
            if path_data.get("ok"):
                file_path = path_data["result"]["file_path"]
                return f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
                
    except Exception as e:
        logging.error(f"Error resolving image: {e}")
        
    return None

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

@app.route('/api/anemone/resolve_image')
def api_resolve_image():
    post_id = request.args.get('post_id')
    if not post_id:
        return jsonify({"url": "https://via.placeholder.com/300"})

    # 1. Пытаемся достать реальную ссылку через Telegram
    # ВНИМАНИЕ: Это медленная операция (2 запроса к API). 
    # В реальном проекте тут нужен кэш (Redis или словарь в памяти).
    
    img_url = get_real_image_url_from_channel(CHANNEL_ID, post_id)
    
    if img_url:
        # ВАЖНО: Мы не отдаем прямую ссылку Telegram, потому что Three.js заблокирует её (CORS).
        # Мы отдаем ссылку на НАШ прокси.
        # Кодируем URL, чтобы передать параметром
        from urllib.parse import quote
        encoded_url = quote(img_url)
        # Возвращаем ссылку на наш собственный прокси
        return jsonify({"url": f"/api/proxy_image?url={encoded_url}"})
    
    # Если картинки нет в посте или ошибка - отдаем красивую заглушку
    # Используем picsum, так как он поддерживает CORS
    return jsonify({"url": f"https://picsum.photos/seed/{post_id}/400/600"})

# --- ПРОКСИ ДЛЯ КАРТИНОК (РЕШЕНИЕ ПРОБЛЕМЫ CORS) ---
@app.route('/api/proxy_image')
def proxy_image():
    url = request.args.get('url')
    if not url:
        return "No URL", 400
        
    try:
        # Скачиваем картинку с Telegram/Интернета сервером
        req = requests.get(url, stream=True)
        
        # Отдаем её клиенту с правильными заголовками
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in req.raw.headers.items()
                   if name.lower() not in excluded_headers]
        
        # Разрешаем CORS
        headers.append(('Access-Control-Allow-Origin', '*'))

        return Response(stream_with_context(req.iter_content(chunk_size=1024)),
                        status=req.status_code,
                        headers=headers,
                        content_type=req.headers.get('content-type'))
    except Exception as e:
        return str(e), 500

# Константа канала (из твоего запроса)
CHANNEL_ID = "-1001479526905" 
MAX_POST_ID = 8504
TELEGRAM_BOT_TOKEN = "6026973561:AAEH542TDSuKUfVbIvo3LbmdeI3-Z_hMTvc"

@app.route('/anemonearts')
def anemone_arts_view():
    """Отдает HTML страницу бесконечного холста"""
    return send_from_directory(app.static_folder, 'anemone.html')

@app.route('/api/anemone/get_chunk', methods=['GET'])
def api_get_anemone_chunk():
    """
    Генерирует контент для одного куска пространства (chunk).
    Принимает координаты чанка x, y, z.
    Возвращает список URL картинок и их координаты внутри чанка.
    """
    from gpt_helper import get_telegram_file_url # Функция должна быть реализована (см. ниже)
    
    try:
        cx = int(request.args.get('x', 0))
        cy = int(request.args.get('y', 0))
        cz = int(request.args.get('z', 0))
    except ValueError:
        return jsonify([])

    # 1. Детерминированная случайность (Seed)
    # Это важно! Если мы вернемся в точку X=5, Y=5, там должны быть ТЕ ЖЕ картинки.
    # Используем координаты чанка как seed.
    seed_str = f"{cx},{cy},{cz}"
    # Превращаем строку в число для seed
    seed_int = int(hashlib.sha256(seed_str.encode('utf-8')).hexdigest(), 16) % 10**8
    random.seed(seed_int)

    # 2. Генерируем объекты в этом чанке
    # Допустим, 3-5 картин в каждом кубе пространства
    items_count = random.randint(3, 5)
    chunk_size = 1000 # Размер куба в условных единицах three.js
    
    planes = []
    
    for i in range(items_count):
        # Выбираем случайный пост. 
        # ВНИМАНИЕ: Стандартный Bot API не может проверить, есть ли в посте картинка,
        # без предварительного сохранения file_id. 
        # Здесь мы эмулируем процесс. В идеале у тебя должна быть БД с file_id.
        # Если нет - мы просто генерируем рандомный ID, но картинка может не загрузиться, 
        # если пост текстовый.
        
        # Для примера я буду использовать заглушки или реальный запрос, если есть file_id.
        # Чтобы это работало "из коробки" без БД, нужен метод get_post_image_url
        
        # Позиция внутри чанка (локальная)
        px = random.uniform(-chunk_size/2, chunk_size/2)
        py = random.uniform(-chunk_size/2, chunk_size/2)
        pz = random.uniform(-chunk_size/2, chunk_size/2)
        
        scale = random.uniform(100, 300) # Размер картины
        
        # Пытаемся получить рандомный ID поста
        random_msg_id = random.randint(1, MAX_POST_ID)
        
        # ВАЖНО: Тут должен быть вызов Telegram API.
        # Так как мы не можем делать 10 запросов к Telegram на каждый скролл (будет бан),
        # мы возвращаем структуру, а фронтенд будет грузить картинку лениво.
        
        # Для демонстрации я верну структуру. 
        # Реальный URL мы получим, только если у нас есть file_id.
        # Т.к. у нас нет базы всех file_id, мы будем использовать "заглушку" или
        # если ты реализуешь helper, то реальный URL.
        
        # Вариант "без костылей" требует базы данных file_id.
        # Вариант "с костылем": фронтенд получает ID поста, а картинку
        # мы проксируем через отдельный медленный запрос.
        
        planes.append({
            "id": f"{cx}_{cy}_{cz}_{i}",
            "pos": [px, py, pz], # Относительно центра чанка
            "scale": [scale, scale * 1.5], # Пропорции (пока просто прямоугольник)
            "post_id": random_msg_id,
            "rotation": [random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), 0]
        })

    return jsonify({
        "cx": cx, "cy": cy, "cz": cz,
        "items": planes
    })

@app.route('/api/anemone/resolve_image')
def api_resolve_image():
    """
    Получает URL картинки для конкретного post_id.
    Это позволяет не нагружать чанк-генератор.
    """
    post_id = request.args.get('post_id')
    
    # ТУТ САМАЯ СЛОЖНАЯ ЧАСТЬ:
    # Telegram Bot API НЕ дает получить фото по ID сообщения (post_id) в канале
    # методом getMessage (такого метода нет).
    #
    # РЕШЕНИЕ:
    # 1. Либо использовать MTProto (Telethon) - это сложно внедрить в текущий Flask.
    # 2. Либо использовать базу данных, которую ты наполнишь заранее.
    # 3. Либо (костыль) возвращать случайную картинку из тех, что мы знаем (file_id).
    
    # Чтобы код работал ПРЯМО СЕЙЧАС, я сделаю заглушку с реальными картинками,
    # но тебе нужно будет заменить это на поиск в твоей БД.
    
    # Пока вернем плейсхолдер или одну из известных картинок, если post_id не найден.
    # Реализуй в gpt_helper логику "найти file_id по post_id" если она есть.
    
    # Пример возврата прямой ссылки Telegram (она живет 1 час):
    # return jsonify({"url": "https://api.telegram.org/file/bot<TOKEN>/photos/file_0.jpg"})
    
    return jsonify({"url": f"https://picsum.photos/seed/{post_id}/400/600"})



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
