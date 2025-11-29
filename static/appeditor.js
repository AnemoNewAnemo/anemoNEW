// app.js (Обновленный)

import { Timer } from './timer.js';
import { Editor } from './editor.js';
import { HistoryApp } from './history.js';

const tg = window.Telegram.WebApp;
tg.expand();

// Настройки
const USER_ID = tg.initDataUnsafe?.user?.id || '6217936347'; // Работаем под ID 12345

const state = {
    // ... ваши старые поля
    mediaId: null,      
    title: "",
    episodes: [],       
    currentEpisode: null, 
    notes: [],          
    editingNoteId: null,
    
// НОВОЕ ПОЛЕ: Хранит ID картинок, которые УЖЕ есть в базе у текущей заметки
    currentNoteImages: [],
    // ← ДОБАВИТЬ СЮДА
    creatingMedia: false,
    
    // 💡 ДОБАВИТЬ ЭТО ПОЛЕ
    previousScreen: 'screen-menu' 
};

let editorLiveTimerInterval = null;
const Notify = {
    timeout: null,

    show(text, type = 'info') {
        const el = document.getElementById('save-status');

        el.className = 'save-status show';
        el.innerText = text;

        if (type === 'success') el.classList.add("success");
        else if (type === 'error') el.classList.add("error");

        el.classList.remove("hidden");

        clearTimeout(this.timeout);
        this.timeout = setTimeout(() => {
            el.classList.remove("show");
            setTimeout(() => {
                el.classList.add("hidden");
                el.classList.remove("success", "error");
            }, 300);
        }, 2000);
    }
};


const App = {
    uploadedFiles: [],

    init() {
        // --- Автосохранение названия при вводе ---
        let titleTypingTimer = null;
        const titleInput = document.getElementById('media-title');

        titleInput.oninput = (e) => {
            clearTimeout(titleTypingTimer);
            titleTypingTimer = setTimeout(() => {
                App.ensureMediaCreated(e.target.value);
            }, 400); // debounce 400мс
        };

        // --- Дополнительно сохраняем при потере фокуса ---
        titleInput.onchange = (e) => {
            App.ensureMediaCreated(e.target.value);
        };

        // --- Таймер ---
        Timer.init((timeString) => {
            document.getElementById('timer').innerText = timeString;
        });

        Editor.initToolbar();

        document.getElementById('btn-timer-toggle').onclick = () => this.toggleTimer();
        document.getElementById('btn-timer-reset').onclick = () => Timer.reset();
        document.getElementById('btn-timer-edit').onclick = () => this.editTimerTime();
    },


    // --- Связь с модулем History ---
    toHistory() { Timer.stop(); HistoryApp.init('view'); },
    toEditMode() { Timer.stop(); HistoryApp.init('edit'); },
    
    openEditorFromHistory(noteId) {
        console.log("➡ openEditorFromHistory() вызван с noteId:", noteId);

        const note = HistoryApp.currentMedia.entries.find(n => n.id == noteId);

        console.log("➡ Найденная note:", note);

        if (note) {

            // ⭐ Записываем ID медиа
            state.mediaId = HistoryApp.currentMedia.id;

            // ⭐ Устанавливаем текущий эпизод
            state.currentEpisode = note.episode;

            // ⭐ ВАЖНО: заполняем список эпизодов для редактора
            // Берём *все уникальные эпизоды*, присутствующие в media
            state.episodes = [...new Set(
                HistoryApp.currentMedia.entries
                    .map(e => e.episode)
                    .filter(e => e) // убираем null
            )];

            // Приводим к массиву file_ids
            if (note.file_id && !note.file_ids) {
                note.file_ids = [note.file_id];
            }

            console.log("➡ Сформированный список эпизодов:", state.episodes);

            this.toEditorView(note);
        } else {
            console.warn("⚠ note не найдена по noteId:", noteId);
        }
    },

    // Прочий код
    continueWatchingFromHistory() {
        console.group("%c▶ continueWatchingFromHistory()", "color:#6aaaff; font-weight: bold");

        console.log("🔹 HistoryApp.currentMedia:", HistoryApp.currentMedia);

        if (!HistoryApp.currentMedia) {
            console.warn("⚠ Нет выбранной записи для продолжения — возврат в меню.");
            Notify.show("Нет выбранной записи для продолжения.", "error");
            console.groupEnd();
            this.showScreen('screen-menu');
            return;
        }

        // 1. Получаем данные
        const mediaToContinue = HistoryApp.currentMedia;
        console.log("📄 Данные для продолжения (mediaToContinue):", mediaToContinue);

        // 2. Передаём в toNewView
        console.log("➡️ Передаём в toNewView():", mediaToContinue);
        this.toNewView(mediaToContinue);

        // 3. Обновляем UI
        console.log("📝 Устанавливаем название:", mediaToContinue.title);
        document.getElementById('media-title').value = mediaToContinue.title;

        // 4. Показываем экран плеера
        console.log("🖥 Переход к экрану: screen-player");
        this.showScreen('screen-player');

        console.groupEnd();
    },


    toEditorView(existingNote = null) {
        console.log("🔵 toEditorView() вызван");
        console.log("   ▶ existingNote:", existingNote);

        // --- НЕ сбрасываем mediaId, title, episodes, notes! ---
        Timer.reset();

        const noteTime = existingNote ? existingNote.timestamp : Timer.formatTime();
        console.log("   ▶ noteTime:", noteTime);
        document.getElementById('editor-timestamp').innerText = noteTime;

        // 💡 НОВОЕ: ЗАПОМИНАЕМ, ОТКУДА ПРИШЛИ
        const activeScreen = document.querySelector('.screen.active');
        state.previousScreen = activeScreen ? activeScreen.id : 'screen-menu';
        console.log("   ▶ previousScreen:", state.previousScreen);

        const noteArea = document.getElementById('note-text');
        noteArea.innerHTML = existingNote ? existingNote.text : "";

        // --- Рендер эпизодов (если есть) ---
        console.log("   ▶ episodes:", state.episodes);
        const epSelect = document.getElementById('episode-select');
        epSelect.innerHTML = "";

        if (state.episodes.length > 0) {
            epSelect.style.display = 'block';

            state.episodes.forEach(ep => {
                const opt = document.createElement('option');
                opt.value = ep;
                opt.innerText = ep;
                if (existingNote && existingNote.episode === ep) {
                    opt.selected = true;
                }
                epSelect.appendChild(opt);
            });

            console.log("   ▶ episode select rendered with items:", state.episodes);
        } else {
            epSelect.style.display = 'none';
            console.log("   ▶ episode select hidden (нет эпизодов)");
        }

        // Очистка превью
        const container = document.getElementById('preview-container');
        container.innerHTML = "";
        this.uploadedFiles = [];
        state.currentNoteImages = [];
        console.log("   ▶ preview cleared");

        // Если существующая заметка — подгружаем картинки
        if (existingNote) {
            let ids = existingNote.file_ids || [];
            if (existingNote.file_id && ids.length === 0) ids = [existingNote.file_id];

            console.log("   ▶ images to load:", ids);

            state.currentNoteImages = ids;

            ids.forEach(fid => {
                console.log("      → loading image:", fid);
                const img = document.createElement('img');
                img.src = `/api/media/get_image_url?file_id=${fid}`;
                img.className = 'preview-thumb';
                container.appendChild(img);
            });
        }

        // Настройка таймера
        const liveLabel = document.getElementById("editor-timer-live");
        const pauseBtn = document.getElementById("editor-timer-pause");

        console.log("   ▶ Timer.isRunning:", Timer.isRunning);

        if (Timer.isRunning) {
            liveLabel.style.display = "inline";
            pauseBtn.style.display = "inline-block";

            editorLiveTimerInterval = setInterval(() => {
                liveLabel.innerText = `(текущий: ${Timer.formatTime()})`;
            }, 1000);

            pauseBtn.onclick = () => {
                console.log("⏸ Pause clicked");
                Timer.stop();
                pauseBtn.style.display = "none";
            };
        } else {
            liveLabel.style.display = "none";
            pauseBtn.style.display = "none";
            clearInterval(editorLiveTimerInterval);
            editorLiveTimerInterval = null;
        }

        state.editingNoteId = existingNote ? existingNote.id : null;
        console.log("   ▶ editingNoteId:", state.editingNoteId);

        console.log("🔵 Переход на screen-editor");
        this.showScreen('screen-editor');
    },





    openQuickTagMenu() {
        if (!state.title?.trim()) {
            alert("Пожалуйста сначала укажите название");
            return;
        }
        document.getElementById("quick-tag-menu").style.display = "flex";
    },

    closeQuickTagMenu() {
        document.getElementById("quick-tag-menu").style.display = "none";
    },

    async addQuickTag(textTemplate) {
        this.closeQuickTagMenu();

        const timestamp = Timer.formatTime();
        const episode = state.currentEpisode;

        // Убеждаемся, что media создано
        const mediaId = await this.ensureMediaCreated();
        if (!mediaId) {
            alert("Ошибка: медиа не создано");
            return;
        }

        const payload = {
            user_id: USER_ID,
            media_id: mediaId,
            text: `Быстрая метка: ${textTemplate}`,
            timestamp: timestamp,
            episode: episode,
            file_id: null
        };

        try {
            const res = await fetch('/api/timer/add_entry', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (data.status === "success") {
                // Обновляем локальный список заметок
                state.notes.push({
                    id: data.entry_id,
                    text: payload.text,
                    timestamp: timestamp,
                    episode: episode,
                    file_id: null
                });

                this.renderNotesTimeline();
            } else {
                alert("Ошибка сохранения");
            }
        } catch (e) {
            console.error(e);
            alert("Ошибка связи с сервером");
        }
    },
    // --- Вспомогательная функция: Гарантирует, что Media создано в БД ---
    async ensureMediaCreated(titleOverride = null) {
        const newTitle = titleOverride || state.title || ("Новая запись " + new Date().toLocaleDateString());

        // --- Если запись существует: обновляем название ---
        if (state.mediaId) {
            if (newTitle !== state.title) {
                try {
                    Notify.show("Сохраняю название...");
                    await fetch('/api/timer/update_media_title', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            user_id: USER_ID,
                            media_id: state.mediaId,
                            title: newTitle
                        })
                    });
                    state.title = newTitle;
                    Notify.show("Название сохранено!", "success");
                } catch (e) {
                    console.error("Ошибка обновления названия:", e);
                    Notify.show("Ошибка сохранения", "error");
                }
            }
            return state.mediaId;
        }
        // ---- ПРЕДОТВРАЩАЕМ ДУБЛИ ----
        if (state.creatingMedia) return null;
        state.creatingMedia = true;
        // --- Создание нового media ---
        try {
            Notify.show("Создаю запись...");
            const res = await fetch('/api/timer/create_media', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    user_id: USER_ID,
                    title: newTitle,
                    type: state.episodes.length > 0 ? 'series' : 'movie'
                })
            });
            const data = await res.json();

            if (data.status === 'success') {
                state.mediaId = data.media_id;
                state.title = newTitle;
                console.log("Media created with ID:", state.mediaId);
                Notify.show("Создано!", "success");
                return state.mediaId;
            }
        } catch (e) {
            console.error("Error creating media:", e);
            alert("Ошибка связи с сервером");
        }
        return null;
    },

    // --- Навигация ---
    showScreen(id) {
        document.querySelectorAll('.screen').forEach(el => el.classList.remove('active'));
        document.getElementById(id).classList.add('active');
    },

    toMenu() {
        Timer.stop();
        this.updatePlayButton();
        this.showScreen('screen-menu');
    },


    toNewView(mediaData = null) {
        // Сброс состояния, только если это ДЕЙСТВИТЕЛЬНО новый просмотр
        if (!mediaData) {
            state.mediaId = null;
            state.title = "";
            state.episodes = [];
            state.currentEpisode = null;
            state.notes = [];
            state.editingNoteId = null;
            Timer.reset();
        } else {
            // Инициализация существующими данными
            state.mediaId = mediaData.id;
            state.title = mediaData.title;
            state.episodes = mediaData.episodes || [];
            state.currentEpisode = mediaData.currentEpisode || null;
            state.notes = mediaData.entries || [];
            state.editingNoteId = null;
            // 🔥 Автовосстановление списка эпизодов из заметок
            if (!mediaData.episodes || mediaData.episodes.length === 0) {
                const eps = new Set();

                state.notes.forEach(n => {
                    if (n.episode) eps.add(n.episode);
                });

                state.episodes = Array.from(eps);

                // Если есть эпизоды — активируем последний
                if (state.episodes.length > 0) {
                    state.currentEpisode = state.episodes[state.episodes.length - 1];
                }
            }            
            // Если в данных есть последняя позиция (например, `mediaData.last_position`), 
            // можно инициализировать таймер
            // Timer.setSeconds(mediaData.last_position || 0);
            
            // Важно: если мы продолжаем просмотр, запускаем таймер с 0 или с последней позиции
            Timer.reset(); 
        }

        document.getElementById('media-title').value = state.title || "";
        this.renderEpisodes();
        this.renderNotesTimeline();
        this.showScreen('screen-player');
    },


    // --- Логика Плеера ---
    updateTitle(val) {
        state.title = val;
    },

    addEpisode() {
        let num = state.episodes.length + 1;
        state.episodes.push(`Серия ${num}`);
        if (state.episodes.length === 1) this.selectEpisode(`Серия ${num}`);
        else this.renderEpisodes();
    },

    selectEpisode(epName) {
        state.currentEpisode = epName;
        this.renderEpisodes();
        this.renderNotesTimeline();
    },

    renderEpisodes() {
        // ... (Ваш код рендера эпизодов без изменений) ...
        const section = document.getElementById('episode-section');
        const list = document.getElementById('episode-list');
        list.innerHTML = '';

        if (state.episodes.length === 0) {
            section.style.display = 'none';
            return;
        }
        section.style.display = 'block';

        let movieChip = document.createElement('div');
        movieChip.className = `chip ${state.currentEpisode === null ? 'active' : ''}`;
        movieChip.innerText = "Общее / Фильм";
        movieChip.onclick = () => this.selectEpisode(null);
        list.appendChild(movieChip);

        state.episodes.forEach(ep => {
            let chip = document.createElement('div');
            chip.className = `chip ${state.currentEpisode === ep ? 'active' : ''}`;
            chip.innerText = ep;
            chip.onclick = () => this.selectEpisode(ep);
            list.appendChild(chip);
        });
    },

    // --- Таймер ---
    toggleTimer() {
        Timer.toggle();
        this.updatePlayButton();
    },
    updatePlayButton() {
        document.getElementById('btn-timer-toggle').innerText = Timer.isRunning ? '⏸ Пауза' : '▶ Старт';
    },
    editTimerTime() {
        let val = prompt("Время (ЧЧ:ММ:СС, например 01:22:14)", "0");
        if(val) Timer.setSeconds(Timer.parseInput(val));
    },

    // --- Редактор и Сохранение ---
    // --- Замени свою старую функцию openEditor на эту ---
    async openEditor(existingNote = null) {

        console.log("🔵 openEditor() START");
        console.log("➡ existingNote:", existingNote);
        console.log("➡ state.title:", state.title);

        if (!state.title?.trim()) {
            alert("Пожалуйста сначала укажите название");
            console.warn("⛔ Открытие редактора отменено — пустой title");
            return;
        }

        // 💡 НОВОЕ: ЗАПОМИНАЕМ, ОТКУДА ПРИШЛИ
        const activeScreen = document.querySelector('.screen.active');
        state.previousScreen = activeScreen ? activeScreen.id : 'screen-menu';
        
        console.log("📺 previousScreen:", state.previousScreen);

        // id заметки
        state.editingNoteId = existingNote ? existingNote.id : null;
        console.log("🆔 editingNoteId:", state.editingNoteId);

        // timestamp
        const timeVal = existingNote ? existingNote.timestamp : Timer.formatTime();
        document.getElementById('editor-timestamp').innerText = timeVal;
        console.log("⏱ timestamp:", timeVal);

        // текст
        const noteArea = document.getElementById('note-text');
        noteArea.innerHTML = existingNote ? existingNote.text : "";
        console.log("📝 text:", noteArea.innerHTML);

        // Очистка
        const container = document.getElementById('preview-container');
        container.innerHTML = ""; 
        this.uploadedFiles = [];
        state.currentNoteImages = [];

        console.log("🧹 очищен контейнер preview, uploadedFiles сброшены");

        this.showScreen('screen-editor');
        console.log("📲 экран: screen-editor");

        // ЛОГИКА ЗАГРУЗКИ КАРТИНОК
        if (existingNote) {
            let ids = existingNote.file_ids || [];

            if (existingNote.file_id && ids.length === 0) {
                ids = [existingNote.file_id];
            }

            state.currentNoteImages = ids;
            console.log("🖼 file_ids:", ids);

            if (ids.length > 0) {
                console.log(`📡 Загружаем превью для ${ids.length} изображений...`);

                const loadingLabel = document.createElement('div');
                loadingLabel.innerText = `Загрузка фото (${ids.length})...`;
                loadingLabel.style.fontSize = "12px";
                loadingLabel.id = 'loading-lbl';
                container.appendChild(loadingLabel);

                // Загружаем превью
                Promise.all(ids.map(async (fid) => {
                    console.log("⏳ fetch image for id:", fid);
                    try {
                        const res = await fetch(`/api/media/get_image_url?file_id=${fid}`);
                        const data = await res.json();
                        console.log("📥 server image response:", data);

                        if (data.url) return { url: data.url, id: fid };
                    } catch (e) {
                        console.error("❌ Ошибка загрузки изображения:", fid, e);
                    }
                    return null;
                })).then(results => {

                    console.log("📦 результаты загрузки:", results);

                    if (document.getElementById('loading-lbl')) {
                        container.removeChild(loadingLabel);
                    }

                    results.forEach(item => {
                        if (item) {
                            console.log("📸 рендер превью:", item);

                            let wrapper = document.createElement('div');
                            wrapper.className = 'img-wrapper';
                            wrapper.style.display = 'inline-block';
                            wrapper.style.position = 'relative';
                            wrapper.style.margin = '5px';

                            let img = document.createElement('img');
                            img.src = item.url;
                            img.className = 'preview-thumb';

                            wrapper.appendChild(img);
                            container.appendChild(wrapper);
                        }
                    });
                });
            }
        };

        // --- Лайв таймер ---
        console.log("⏳ Timer.isRunning:", Timer.isRunning);

        const liveLabel = document.getElementById("editor-timer-live");
        const pauseBtn = document.getElementById("editor-timer-pause");

        if (Timer.isRunning) {
            console.log("▶ Таймер работает, включаем отображение");

            liveLabel.style.display = "inline";
            pauseBtn.style.display = "inline-block";

            editorLiveTimerInterval = setInterval(() => {
                const formatted = Timer.formatTime();
                liveLabel.innerText = `(текущий: ${formatted})`;
                console.log("⏱ live timer update:", formatted);
            }, 1000);

            pauseBtn.onclick = () => {
                console.log("⏸ нажата кнопка паузы");
                Timer.stop();
                pauseBtn.style.display = "none";
            };

        } else {
            console.log("⏹ Таймер остановлен, скрываем элементы");

            liveLabel.style.display = "none";
            pauseBtn.style.display = "none";

            clearInterval(editorLiveTimerInterval);
            editorLiveTimerInterval = null;
        }

        console.log("🔵 openEditor() END");
    },


    handleFiles(input) {
        // ... (Код превью картинок без изменений) ...
        const files = Array.from(input.files);
        const container = document.getElementById('preview-container');
        files.forEach(file => {
            this.uploadedFiles.push(file);
            let reader = new FileReader();
            reader.onload = (e) => {
                let img = document.createElement('img');
                img.src = e.target.result;
                img.className = 'preview-thumb';
                container.appendChild(img);
            };
            reader.readAsDataURL(file);
        });
    },

    async saveNote() {
        clearInterval(editorLiveTimerInterval);
        editorLiveTimerInterval = null;
        if (!state.title?.trim()) {
            alert("Пожалуйста сначала укажите название");
            return;
        }        
        const text = document.getElementById('note-text').innerHTML;
        const timestamp = document.getElementById('editor-timestamp').innerText;
        
        const saveBtn = document.querySelector('.toolbar button[data-command="save"]');
        if(saveBtn) saveBtn.disabled = true;

        try {
            Notify.show("Сохраняю заметку...");
            const mediaId = await this.ensureMediaCreated();
            if (!mediaId) throw new Error("Media ID creation failed");

            // 1. ЗАГРУЗКА НОВЫХ ФАЙЛОВ
            let newFileIds = [];
            
            if (this.uploadedFiles.length > 0) {
                console.log(`Начинаю загрузку ${this.uploadedFiles.length} изображений...`);
                
                // Создаем массив промисов для параллельной загрузки
                const uploadPromises = this.uploadedFiles.map(async (file) => {
                    const formData = new FormData();
                    formData.append('image', file);
                    formData.append('user_id', USER_ID);
                    
                    try {
                        const res = await fetch('/api/media/upload_image', {
                            method: 'POST',
                            body: formData
                        });
                        const data = await res.json();
                        if (data.status === 'success') return data.file_id;
                    } catch (e) {
                        console.error("Ошибка загрузки файла:", e);
                    }
                    return null;
                });

                // Ждем пока все загрузятся
                const results = await Promise.all(uploadPromises);
                newFileIds = results.filter(id => id !== null); // Убираем ошибки
            }

            // 2. ОБЪЕДИНЕНИЕ ID (Старые + Новые)
            // Мы берем те, что уже были (state.currentNoteImages) и добавляем новые
            const finalFileIds = [...state.currentNoteImages, ...newFileIds];

            // 3. ФОРМИРОВАНИЕ ЗАПРОСА
            const payload = {
                user_id: USER_ID,
                media_id: mediaId,
                text: text,
                timestamp: timestamp,
                episode: state.currentEpisode,
                file_ids: finalFileIds // Отправляем массив!
            };

            let res;
            // РЕДАКТИРОВАНИЕ
            if (state.editingNoteId && String(state.editingNoteId).length > 5) { 
                payload.entry_id = state.editingNoteId;
                res = await fetch('/api/timer/update_entry', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
            } 
            // СОЗДАНИЕ
            else {
                res = await fetch('/api/timer/add_entry', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
            }

            const data = await res.json();
            
            if (data.status === 'success') {
                this.uploadedFiles = [];
                document.getElementById('preview-container').innerHTML = "";
                document.getElementById('note-text').innerHTML = "";
                state.currentNoteImages = [];

                Notify.show("Заметка сохранена!", "success");
                // Передаем массив ID для обновления UI
                this.refreshUIAfterSave(data.key || state.editingNoteId, text, timestamp, finalFileIds);
            } else {
                alert("Ошибка при сохранении заметки в БД");
                Notify.show("Ошибка сохранения", "error");
            }
        } catch (e) {
            console.error(e);
            alert("Произошла ошибка: " + e.message);
        } finally {
            if(saveBtn) saveBtn.disabled = false;
        }
    },
    // Вынес обновление интерфейса в отдельный метод для чистоты
        refreshUIAfterSave(noteId, text, timestamp, fileIds) {
            // Логика обновления списка заметок (timeline)
            const newNoteLocal = {
                id: noteId,
                text, 
                timestamp, 
                episode: state.currentEpisode, 
                // hasImage true, если массив не пустой
                hasImage: (fileIds && fileIds.length > 0), 
                file_ids: fileIds || []      // Сохраняем массив
            };
            
            if (state.editingNoteId) {
                 const idx = state.notes.findIndex(n => n.id === state.editingNoteId);
                 if(idx !== -1) state.notes[idx] = { ...state.notes[idx], ...newNoteLocal };
            } else {
                state.notes.push(newNoteLocal);
            }
            
            this.renderNotesTimeline();
            this.cancelEditor();
        },
    async deleteNote(noteId) {

        // Если это локальная заметка (еще не отправлена - редкий кейс, но все же)
        if (!state.mediaId) {
            state.notes = state.notes.filter(n => n.id !== noteId);
            this.renderNotesTimeline();
            return;
        }

        try {
            const res = await fetch(`/api/timer/delete_entry?user_id=${USER_ID}&media_id=${state.mediaId}&entry_id=${noteId}`, {
                method: 'DELETE'
            });
            const data = await res.json();
            if (data.status === 'success') {
                state.notes = state.notes.filter(n => n.id !== noteId);
                this.renderNotesTimeline();
            }
        } catch (e) {
            alert('Ошибка удаления');
        }
    },
    toggleHistory() {
        const listScreen = document.getElementById('screen-list');

        // Если список уже открыт — закрываем (как кнопка ←)
        if (listScreen.classList.contains('active')) {
            this.toMenu();
        } 
        // Если нет — открываем
        else {
            this.toHistory();
        }
    },
    renderNotesTimeline() {
        Editor.renderMiniTimeline(
            state.notes, 
            state.currentEpisode, 
            (note) => this.openEditor(note), 
            (id) => this.deleteNote(id)
        );
    },

    cancelEditor() {
        clearInterval(editorLiveTimerInterval);
        editorLiveTimerInterval = null;      
        
        // 💡 ИСПРАВЛЕНИЕ: ВОЗВРАЩАЕМСЯ НА ЭКРАН, С КОТОРОГО ПЕРЕШЛИ
        // Если это screen-view (история), то возвращаемся на screen-player,
        // Иначе возвращаемся на то, что сохранили, или по умолчанию на screen-player
        let screenToReturn;
        if (state.previousScreen === 'screen-view' && HistoryApp.currentMedia) {
             // Если мы пришли с экрана просмотра записи (истории), 
             // то нас интересует возврат в режим "Продолжить просмотр" (screen-player)
             screenToReturn = 'screen-player';
        } else if (state.previousScreen === 'screen-player') {
             // Если мы пришли с экрана плеера - туда и возвращаемся
             screenToReturn = 'screen-player';
        } else {
             // Если пришли откуда-то еще (напр., редактировали старую заметку из истории)
             // или state.previousScreen не установлен - возвращаемся в меню
             screenToReturn = 'screen-menu';
        }

        // Сбрасываем ID редактируемой заметки
        state.editingNoteId = null;

        this.showScreen(screenToReturn);

        // ВАЖНО: Если возвращаемся на screen-player, то нужно возобновить таймер, 
        // если он не был принудительно остановлен в редакторе
        if (screenToReturn === 'screen-player' && Timer.wasRunning) {
            Timer.start();
            this.updatePlayButton();
        }
    }


};

window.app = App;
window.timer = Timer; 
App.init();