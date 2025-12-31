<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Music Player</title>
    <!-- Подключаем Telegram WebApp -->
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <!-- Подключаем SortableJS для перетаскивания -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Sortable/1.15.0/Sortable.min.js"></script>
    <style>
        :root {
            --primary-color: #fff;
            --accent-color: #3b82f6;
            --bg-color: #0f0f0f;
            --card-bg: #1c1c1e;
            --text-secondary: #8e8e93;
            --slider-bg: #3a3a3c;
        }

        body {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            background-color: var(--bg-color);
            color: var(--primary-color);
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            overflow: hidden;
            -webkit-font-smoothing: antialiased;
            /* Предотвращаем обновление страницы свайпом вниз на мобилках */
            overscroll-behavior-y: none;
        }

        .player-container {
            width: 100%;
            max-width: 380px;
            padding: 25px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
        }

        /* ОБЛОЖКА */
        .cover-wrapper {
            width: 100%;
            display: flex;
            justify-content: center;
            margin-bottom: 25px;
        }
        
        .cover-art {
            width: 100%;
            height: auto;
            max-height: 40vh; 
            background-color: transparent;
            border-radius: 12px;
            object-fit: contain; 
            box-shadow: 0 8px 24px rgba(0,0,0,0.4);
            transition: transform 0.3s ease;
        }

        /* ИНФО О ТРЕКЕ */
        .track-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            width: 100%;
        }
        
        .track-text-group {
            overflow: hidden;
            text-align: left;
            flex: 1;
            padding-right: 15px;
        }

        .track-title {
            font-size: 1.3em;
            font-weight: 700;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin: 0;
        }

        .btn-download {
            background: none;
            border: none;
            color: var(--primary-color);
            cursor: pointer;
            padding: 8px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0.7;
            transition: opacity 0.2s;
        }
        .btn-download:active { opacity: 1; background: rgba(255,255,255,0.1); }
        .btn-download svg { width: 20px; height: 20px; fill: currentColor; }

        /* ПРОГРЕСС БАР */
        .progress-container {
            width: 100%;
            height: 20px;
            cursor: pointer;
            position: relative;
            display: flex;
            align-items: center;
            margin-bottom: 5px;
            touch-action: none;
        }
        .progress-bar-bg {
            width: 100%;
            height: 4px;
            background: var(--slider-bg);
            border-radius: 2px;
            position: relative;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: var(--primary-color);
            border-radius: 2px;
            width: 0%;
            pointer-events: none;
        }
        .progress-knob {
            width: 12px;
            height: 12px;
            background: var(--primary-color);
            border-radius: 50%;
            position: absolute;
            top: 50%;
            left: 0%;
            transform: translate(-50%, -50%) scale(0);
            box-shadow: 0 2px 6px rgba(0,0,0,0.5);
            z-index: 2;
            cursor: grab;
            transition: transform 0.1s;
        }
        .progress-container:hover .progress-knob,
        .progress-container:active .progress-knob, 
        .progress-knob.dragging {
            transform: translate(-50%, -50%) scale(1);
        }

        .time-labels {
            display: flex; 
            justify-content: space-between; 
            font-size: 11px; 
            color: var(--text-secondary); 
            font-weight: 500;
            margin-bottom: 25px;
        }

        /* УПРАВЛЕНИЕ */
        .controls {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 30px;
            margin-bottom: 30px;
        }
        .btn-control {
            background: none;
            border: none;
            color: var(--primary-color);
            cursor: pointer;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.1s, opacity 0.2s;
        }
        .btn-control:active { transform: scale(0.9); opacity: 0.8; }
        .btn-skip svg { width: 32px; height: 32px; fill: currentColor; }
        .btn-play svg { width: 64px; height: 64px; fill: currentColor; }

        /* ГРОМКОСТЬ */
        .volume-container {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            margin-bottom: 25px;
            width: 100%;
        }
        .volume-icon svg { width: 16px; height: 16px; fill: var(--text-secondary); }
        .volume-slider {
            -webkit-appearance: none;
            width: 100%;
            height: 4px;
            background: var(--slider-bg);
            border-radius: 2px;
            outline: none;
            position: relative;
            cursor: pointer;
            background-image: linear-gradient(var(--primary-color), var(--primary-color));
            background-size: 100% 100%;
            background-repeat: no-repeat;
        }
        .volume-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            height: 16px;
            width: 16px;
            border-radius: 50%;
            background: #fff;
            cursor: pointer;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
            transform: scale(0);
            transition: transform 0.1s;
        }
        .volume-container:hover .volume-slider::-webkit-slider-thumb,
        .volume-slider:active::-webkit-slider-thumb { transform: scale(1); }
        .volume-slider::-moz-range-thumb {
            height: 16px;
            width: 16px;
            border: none;
            border-radius: 50%;
            background: #fff;
            transform: scale(0);
            transition: transform 0.1s;
        }
        .volume-container:hover .volume-slider::-moz-range-thumb,
        .volume-slider:active::-moz-range-thumb { transform: scale(1); }

        /* --- НОВЫЙ ПЛЕЙЛИСТ --- */
        .playlist {
            text-align: left;
            margin-top: 0;
            max-height: 180px; /* Чуть увеличил для удобства */
            overflow-y: auto;
            border-top: 1px solid rgba(255,255,255,0.1);
            padding-top: 10px;
            width: 100%;
        }
        .playlist::-webkit-scrollbar { width: 4px; }
        .playlist::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }

        /* Обновленный стиль элемента плейлиста */
        .playlist-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 5px; /* Уменьшил паддинги, т.к. элементы теперь крупные */
            margin-bottom: 2px;
            border-radius: 8px;
            transition: background 0.2s;
            user-select: none;
            background: transparent;
        }
        
        .playlist-item:hover {
            background: rgba(255,255,255,0.05);
        }
        
        .playlist-item.active {
            background: rgba(255,255,255,0.1);
        }
        .playlist-item.active .track-name {
            color: var(--primary-color);
            font-weight: 600;
        }

        /* Зона перетаскивания (Левая часть) */
        .drag-handle {
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: grab;
            color: var(--text-secondary);
            touch-action: none; /* Важно для мобилок */
        }
        .drag-handle:active { cursor: grabbing; color: var(--primary-color); }
        .drag-handle svg { width: 18px; height: 18px; fill: currentColor; }

        /* Название трека (Центр) */
        .track-name {
            flex: 1;
            margin: 0 10px;
            font-size: 14px;
            color: var(--text-secondary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            cursor: pointer;
            padding: 8px 0;
        }

        /* Кнопка копирования (Правая часть) */
        .copy-btn {
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: var(--text-secondary);
            border: none;
            background: none;
            opacity: 0.6;
            transition: opacity 0.2s;
        }
        .copy-btn:hover { opacity: 1; color: var(--primary-color); }
        .copy-btn svg { width: 16px; height: 16px; fill: currentColor; }

        /* Стиль "призрака" при перетаскивании (SortableJS) */
        .sortable-ghost {
            opacity: 0.4;
            background: rgba(59, 130, 246, 0.2);
        }
        .sortable-drag {
            cursor: grabbing;
        }

        .loading { color: var(--text-secondary); margin-top: 20%; }
        .error { color: #ff453a; margin-top: 20%; }

        /* Уведомление о копировании */
        .toast {
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(255,255,255,0.9);
            color: #000;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s;
            z-index: 100;
        }
        .toast.show { opacity: 1; }
    </style>
</head>
<body>

<div class="player-container" id="player-ui" style="display:none;">
    
    <!-- Обложка -->
    <div class="cover-wrapper">
        <img id="cover-img" class="cover-art" src="" alt="Cover">
    </div>
    
    <!-- Инфо и кнопка скачивания -->
    <div class="track-info">
        <div class="track-text-group">
            <div class="track-title" id="track-title">Loading...</div>
        </div>
        <a id="download-btn" class="btn-download" href="#" target="_blank" download>
            <svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
        </a>
    </div>

    <!-- Прогресс бар -->
    <div class="progress-container" id="progress-container">
        <div class="progress-bar-bg">
            <div class="progress-fill" id="progress-fill"></div>
        </div>
        <div class="progress-knob" id="progress-knob"></div>
    </div>
    
    <div class="time-labels">
        <span id="curr-time">0:00</span>
        <span id="dur-time">0:00</span>
    </div>

    <!-- Управление -->
    <div class="controls">
        <button class="btn-control btn-skip" onclick="musicApp.prevTrack()">
            <svg viewBox="0 0 24 24"><polygon points="19 20 9 12 19 4 19 20"></polygon><line x1="5" y1="19" x2="5" y2="5"></line></svg>
        </button>
        
        <button class="btn-control btn-play" onclick="musicApp.togglePlay()" id="play-btn">
            <svg viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
        </button>
        
        <button class="btn-control btn-skip" onclick="musicApp.nextTrack()">
            <svg viewBox="0 0 24 24"><polygon points="5 4 15 12 5 20 5 4"></polygon><line x1="19" y1="5" x2="19" y2="19"></line></svg>
        </button>
    </div>

    <!-- Громкость -->
    <div class="volume-container">
        <div class="volume-icon">
            <svg viewBox="0 0 24 24"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon></svg>
        </div>
        <input type="range" min="0" max="1" step="0.01" value="1" class="volume-slider" id="volume-slider">
        <div class="volume-icon">
            <svg viewBox="0 0 24 24"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
        </div>
    </div>

    <!-- Плейлист -->
    <div class="playlist" id="playlist-container">
        <!-- Список треков генерируется JS -->
    </div>
</div>

<!-- Всплывающее сообщение -->
<div id="toast" class="toast">Название скопировано</div>

<div id="loading-msg" class="loading">Загрузка музыки...</div>
<div id="error-msg" class="error" style="display:none;"></div>

<audio id="audio-element"></audio>

<script>
    const musicApp = {
        tracks: [],
        currentindex: 0,
        audio: null,
        isPlaying: false,
        isDragging: false,
        sortableInstance: null,

        init: function() {
            this.audio = document.getElementById('audio-element');
            
            const parts = window.location.pathname.split('/');
            const userId = parts[2];
            const messageId = parts[3];

            // MOCK DATA для проверки (удалить, если есть реальный API)
            if (!userId || !messageId) {
                 this.tracks = [
                     {title: "Song One - Artist A", url: "#", cover: ""},
                     {title: "Song Two - Artist B", url: "#", cover: ""},
                     {title: "Song Three - Artist C", url: "#", cover: ""},
                     {title: "Song Four - Artist D", url: "#", cover: ""}
                 ];
                 this.renderPlaylist();
                 this.loadTrack(0, false);
                 document.getElementById('loading-msg').style.display = 'none';
                 document.getElementById('player-ui').style.display = 'block';
            } else {
                 this.loadData(userId, messageId);
            }

            this.setupEvents();
            this.updateVolumeVisuals(1);
        },

        loadData: async function(userId, messageId) {
            try {
                const response = await fetch(`/api/music/get_playlist?user_id=${userId}&message_id=${messageId}`);
                const data = await response.json();

                if (!response.ok || !data.tracks || data.tracks.length === 0) {
                    this.showError(data.error || "Музыка не найдена");
                    return;
                }

                this.tracks = data.tracks;
                this.setCover(data.cover);
                this.renderPlaylist();
                this.loadTrack(0, false);
                
                document.getElementById('loading-msg').style.display = 'none';
                document.getElementById('player-ui').style.display = 'block';

            } catch (e) {
                console.error(e);
                this.showError("Ошибка соединения");
            }
        },
        
        setCover: function(url) {
            const coverImg = document.getElementById('cover-img');
            if (url) coverImg.src = url;
            else coverImg.src = "https://via.placeholder.com/400x400/1c1c1e/333?text=Music";
        },

        loadTrack: function(index, autoPlay = true) {
            if (index < 0 || index >= this.tracks.length) return;
            
            this.currentindex = index;
            const track = this.tracks[index];
            
            document.getElementById('track-title').textContent = track.title;
            this.audio.src = track.url;
            
            // Логика скачивания
            const downloadBtn = document.getElementById('download-btn');
            const newDownloadBtn = downloadBtn.cloneNode(true);
            downloadBtn.parentNode.replaceChild(newDownloadBtn, downloadBtn);
            
            newDownloadBtn.addEventListener('click', async (e) => {
                e.preventDefault();
                let fileName = track.original_name || track.filename || `${track.title}.mp3`;
                fileName = fileName.replace(/[\\/:*?"<>|]/g, '');
                if (!fileName.endsWith('.mp3')) fileName += '.mp3';

                try {
                    const response = await fetch(track.url);
                    const blob = await response.blob();
                    const blobUrl = window.URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = blobUrl;
                    link.download = fileName;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    window.URL.revokeObjectURL(blobUrl);
                } catch (err) {
                    window.open(track.url, '_blank');
                }
            });
            
            if(track.cover) this.setCover(track.cover);
            
            this.highlightPlaylist();
            this.updateProgressBar(0);

            if (autoPlay) {
                this.play();
            } else {
                this.isPlaying = false;
                this.updatePlayBtn();
            }
        },

        play: function() {
            this.audio.play()
                .then(() => {
                    this.isPlaying = true;
                    this.updatePlayBtn();
                })
                .catch(err => console.error("Play error:", err));
        },

        pause: function() {
            this.audio.pause();
            this.isPlaying = false;
            this.updatePlayBtn();
        },

        togglePlay: function() {
            if (this.isPlaying) this.pause();
            else this.play();
        },

        nextTrack: function() {
            let next = this.currentindex + 1;
            if (next >= this.tracks.length) next = 0; 
            this.loadTrack(next);
        },

        prevTrack: function() {
            let prev = this.currentindex - 1;
            if (prev < 0) prev = this.tracks.length - 1;
            this.loadTrack(prev);
        },

        updatePlayBtn: function() {
            const btn = document.getElementById('play-btn');
            const playIcon = `<svg viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>`;
            const pauseIcon = `<svg viewBox="0 0 24 24"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>`;
            btn.innerHTML = this.isPlaying ? pauseIcon : playIcon;
        },

        // --- ОБНОВЛЕННАЯ ФУНКЦИЯ ОТРИСОВКИ ПЛЕЙЛИСТА ---
        renderPlaylist: function() {
            const container = document.getElementById('playlist-container');
            container.innerHTML = '';
            
            this.tracks.forEach((track, idx) => {
                const div = document.createElement('div');
                div.className = 'playlist-item';
                div.setAttribute('data-index', idx); // Важно для Sortable

                // 1. Ручка перетаскивания (слева)
                const handle = document.createElement('div');
                handle.className = 'drag-handle';
                // Иконка "гамбургер"
                handle.innerHTML = `<svg viewBox="0 0 24 24"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>`;
                
                // 2. Название трека (центр)
                const name = document.createElement('div');
                name.className = 'track-name';
                name.textContent = track.title;
                name.onclick = () => musicApp.loadTrack(musicApp.tracks.indexOf(track)); // Динамический поиск индекса

                // 3. Кнопка копирования (справа)
                const copyBtn = document.createElement('button');
                copyBtn.className = 'copy-btn';
                // Иконка копирования
                copyBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;
                copyBtn.onclick = (e) => {
                    e.stopPropagation(); // Чтобы не включить трек при клике на копирование
                    musicApp.copyToClipboard(track.title);
                };

                div.appendChild(handle);
                div.appendChild(name);
                div.appendChild(copyBtn);
                
                container.appendChild(div);
            });

            this.initSortable();
            this.highlightPlaylist();
        },

        // --- ИНИЦИАЛИЗАЦИЯ DRAG & DROP ---
        initSortable: function() {
            const el = document.getElementById('playlist-container');
            if (this.sortableInstance) this.sortableInstance.destroy(); // Очистка старого

            this.sortableInstance = new Sortable(el, {
                handle: '.drag-handle', // Тянем только за ручку
                animation: 150,
                ghostClass: 'sortable-ghost',
                delay: 0, // Мгновенная реакция
                onEnd: (evt) => {
                    // Логика пересчета массива после переноса
                    const oldIndex = evt.oldIndex;
                    const newIndex = evt.newIndex;
                    
                    if (oldIndex === newIndex) return;

                    // 1. Сохраняем ссылку на текущую играющую песню
                    const currentTrack = this.tracks[this.currentindex];

                    // 2. Меняем массив
                    const movedItem = this.tracks.splice(oldIndex, 1)[0];
                    this.tracks.splice(newIndex, 0, movedItem);

                    // 3. Находим, где теперь текущая песня, и обновляем индекс
                    this.currentindex = this.tracks.indexOf(currentTrack);
                    
                    // Обновляем визуально (чтобы индексы атрибутов пересчитались, если нужно, но Sortable уже поменял DOM)
                    // Для чистоты данных можно перерендерить, но это прервет анимацию.
                    // Визуально DOM уже правильный, массив синхронизирован.
                }
            });
        },

        copyToClipboard: function(text) {
            navigator.clipboard.writeText(text).then(() => {
                const toast = document.getElementById('toast');
                toast.classList.add('show');
                setTimeout(() => toast.classList.remove('show'), 2000);
            }).catch(err => console.error('Copy failed', err));
        },

        highlightPlaylist: function() {
            const items = document.querySelectorAll('.playlist-item');
            // Так как мы перетаскиваем элементы, порядок в DOM может отличаться от индекса,
            // поэтому надежнее перебирать по соответствию трека
            items.forEach((item) => {
                const nameDiv = item.querySelector('.track-name');
                if (nameDiv && nameDiv.textContent === this.tracks[this.currentindex]?.title) {
                    item.classList.add('active');
                    // Не скроллим автоматически, если пользователь что-то драгает
                } else {
                    item.classList.remove('active');
                }
            });
        },

        updateProgressBar: function(percent) {
            document.getElementById('progress-fill').style.width = `${percent}%`;
            document.getElementById('progress-knob').style.left = `${percent}%`;
        },

        updateVolumeVisuals: function(val) {
            const percentage = val * 100;
            const slider = document.getElementById('volume-slider');
            slider.style.backgroundSize = `${percentage}% 100%`;
        },

        setupEvents: function() {
            this.audio.addEventListener('timeupdate', () => {
                if (!this.isDragging) {
                    const { currentTime, duration } = this.audio;
                    const percent = duration ? (currentTime / duration) * 100 : 0;
                    this.updateProgressBar(percent);
                    document.getElementById('curr-time').textContent = this.formatTime(currentTime);
                    document.getElementById('dur-time').textContent = this.formatTime(duration || 0);
                }
            });
            
            this.audio.addEventListener('loadedmetadata', () => {
                document.getElementById('dur-time').textContent = this.formatTime(this.audio.duration);
            });

            this.audio.addEventListener('ended', () => {
                this.nextTrack();
            });

            // SEEKER
            const progressContainer = document.getElementById('progress-container');
            const knob = document.getElementById('progress-knob');

            const handleDrag = (e) => {
                const rect = progressContainer.getBoundingClientRect();
                const clientX = e.touches ? e.touches[0].clientX : e.clientX;
                let percent = (clientX - rect.left) / rect.width;
                if (percent < 0) percent = 0;
                if (percent > 1) percent = 1;

                this.updateProgressBar(percent * 100);
                const duration = this.audio.duration || 0;
                document.getElementById('curr-time').textContent = this.formatTime(percent * duration);
                return percent;
            };

            const startDrag = (e) => {
                this.isDragging = true;
                knob.classList.add('dragging');
                handleDrag(e);
            };

            const moveDrag = (e) => {
                if (this.isDragging) handleDrag(e);
            };

            const endDrag = (e) => {
                if (this.isDragging) {
                    this.isDragging = false;
                    knob.classList.remove('dragging');
                    const percent = handleDrag(e.changedTouches ? { touches: [e.changedTouches[0]], clientX: e.changedTouches[0].clientX } : e);
                    if (this.audio.duration) {
                        this.audio.currentTime = percent * this.audio.duration;
                    }
                }
            };

            progressContainer.addEventListener('mousedown', startDrag);
            document.addEventListener('mousemove', moveDrag);
            document.addEventListener('mouseup', endDrag);

            progressContainer.addEventListener('touchstart', startDrag, {passive: false});
            document.addEventListener('touchmove', moveDrag, {passive: false});
            document.addEventListener('touchend', endDrag);

            // VOLUME
            const volSlider = document.getElementById('volume-slider');
            volSlider.addEventListener('input', (e) => {
                const val = e.target.value;
                this.audio.volume = val;
                this.updateVolumeVisuals(val);
            });

            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.ready();
                window.Telegram.WebApp.expand();
                window.Telegram.WebApp.setHeaderColor('#0f0f0f');
                window.Telegram.WebApp.setBackgroundColor('#0f0f0f');
            }
        },

        formatTime: function(seconds) {
            if (isNaN(seconds)) return "0:00";
            const min = Math.floor(seconds / 60);
            const sec = Math.floor(seconds % 60);
            return `${min}:${sec < 10 ? '0' : ''}${sec}`;
        },

        showError: function(msg) {
            document.getElementById('loading-msg').style.display = 'none';
            const errDiv = document.getElementById('error-msg');
            errDiv.textContent = msg;
            errDiv.style.display = 'block';
        }
    };

    document.addEventListener('DOMContentLoaded', () => {
        musicApp.init();
    });
</script>
</body>
</html>
