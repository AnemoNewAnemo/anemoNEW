const musicApp = {
    tracks: [],
    currentindex: 0,
    audio: null,
    isPlaying: false,

    init: function() {
        this.audio = document.getElementById('audio-element');
        
        // Парсим URL: /musicplayer/USER_ID/MESSAGE_ID
        // window.location.pathname вернет /musicplayer/123/123_456
        const parts = window.location.pathname.split('/');
        // parts[0] = "", parts[1] = "musicplayer", parts[2] = user_id, parts[3] = message_id
        
        const userId = parts[2];
        const messageId = parts[3];

        if (!userId || !messageId) {
            this.showError("Неверная ссылка");
            return;
        }

        this.loadData(userId, messageId);
        this.setupEvents();
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
            
            // Установка обложки
            const coverImg = document.getElementById('cover-img');
            if (data.cover) {
                coverImg.src = data.cover;
            } else {
                // Плейсхолдер, если нет обложки
                coverImg.src = "https://via.placeholder.com/400x400/333/fff?text=No+Cover";
            }

            this.renderPlaylist();
            this.loadTrack(0, false); // Загружаем первый трек, но не играем сразу (автоплей запрещен политиками браузеров без жеста)
            
            document.getElementById('loading-msg').style.display = 'none';
            document.getElementById('player-ui').style.display = 'block';

        } catch (e) {
            console.error(e);
            this.showError("Ошибка соединения");
        }
    },

    loadTrack: function(index, autoPlay = true) {
        if (index < 0 || index >= this.tracks.length) return;
        
        this.currentindex = index;
        const track = this.tracks[index];
        
        document.getElementById('track-title').textContent = track.title;
        this.audio.src = track.url;
        
        this.highlightPlaylist();

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
        if (next >= this.tracks.length) next = 0; // Зациклить
        this.loadTrack(next);
    },

    prevTrack: function() {
        let prev = this.currentindex - 1;
        if (prev < 0) prev = this.tracks.length - 1;
        this.loadTrack(prev);
    },

    updatePlayBtn: function() {
        const btn = document.getElementById('play-btn');
        btn.textContent = this.isPlaying ? '❚❚' : '▶';
    },

    renderPlaylist: function() {
        const container = document.getElementById('playlist-container');
        container.innerHTML = '';
        this.tracks.forEach((track, idx) => {
            const div = document.createElement('div');
            div.className = 'playlist-item';
            div.textContent = `${idx + 1}. ${track.title}`;
            div.onclick = () => musicApp.loadTrack(idx);
            container.appendChild(div);
        });
    },

    highlightPlaylist: function() {
        const items = document.querySelectorAll('.playlist-item');
        items.forEach((item, idx) => {
            if (idx === this.currentindex) item.classList.add('active');
            else item.classList.remove('active');
        });
    },

    setupEvents: function() {
        // Обновление прогресс-бара
        this.audio.addEventListener('timeupdate', () => {
            const { currentTime, duration } = this.audio;
            const percent = (currentTime / duration) * 100;
            document.getElementById('progress-fill').style.width = `${percent}%`;
            
            document.getElementById('curr-time').textContent = this.formatTime(currentTime);
            document.getElementById('dur-time').textContent = this.formatTime(duration || 0);
        });

        // Автопереключение при окончании
        this.audio.addEventListener('ended', () => {
            this.nextTrack();
        });

        // Клик по прогресс-бару
        document.getElementById('progress-container').addEventListener('click', (e) => {
            const width = e.currentTarget.clientWidth;
            const clickX = e.offsetX;
            const duration = this.audio.duration;
            this.audio.currentTime = (clickX / width) * duration;
        });
        
        // Интеграция с Telegram WebApp (Кнопка "Закрыть")
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.ready();
            window.Telegram.WebApp.expand(); // На весь экран
        }
    },

    formatTime: function(seconds) {
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

// Запуск при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    musicApp.init();
});