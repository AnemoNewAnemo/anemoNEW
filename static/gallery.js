// gallery.js

// Функция создания UI для фулскрина (если его нет в HTML)
function setupFullscreenUI() {
    const fsPreview = document.getElementById('fs-preview');
    if (!fsPreview) return;

    fsPreview.innerHTML = '';

    // 1. Контейнер для картинки
    const imgContainer = document.createElement('div');
    imgContainer.style.cssText = 'position:relative; width:100%; height:100%; display:flex; justify-content:center; align-items:center;';

    // Элемент картинки
    const img = document.createElement('img');
    img.id = 'fs-img';
    img.style.cssText = 'max-width:95%; max-height:95%; box-shadow:0 0 50px rgba(0,0,0,0.5); opacity:0; transition:opacity 0.5s ease;';
    
    // Лоадер
    const loader = document.createElement('div');
    loader.id = 'fs-loader';
    loader.className = 'fs-loader';

    imgContainer.appendChild(loader);
    imgContainer.appendChild(img);
    fsPreview.appendChild(imgContainer);

    // --- КНОПКИ УПРАВЛЕНИЯ (Справа в столбик) ---
    
    // Общий стиль для круглых кнопок справа
    const btnStyle = `
        position: absolute; right: 30px; width: 50px; height: 50px;
        background: rgba(20, 20, 25, 0.6); backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.15); border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; z-index: 3001; transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3); color: #eee;
    `;

    // 1. Кнопка ЗАКРЫТЬ (Самая верхняя)
    const closeBtn = document.createElement('div');
    closeBtn.id = 'fs-close-btn';
    closeBtn.style.cssText = btnStyle + 'top: 30px;';
    closeBtn.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
    
    // 2. Кнопка ИНФО (Ниже закрытия)
    const infoBtn = document.createElement('div');
    infoBtn.className = 'fs-info-trigger-btn'; // Оставляем класс для совместимости стилей
    infoBtn.style.cssText = btnStyle + 'top: 90px;';
    infoBtn.innerHTML = `<svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M11 7h2v2h-2zm0 4h2v6h-2zm1-9C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/></svg>`;

    // 3. Кнопка СКАЧАТЬ (Ниже инфо) - показывается только если есть ссылка
    const downloadBtn = document.createElement('div');
    downloadBtn.id = 'fs-download-btn';
    downloadBtn.style.cssText = btnStyle + 'top: 150px; display: none;'; // Скрыта по умолчанию
    downloadBtn.innerHTML = `<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>`;

    // --- КНОПКИ НАВИГАЦИИ (Стрелки) ---
    const navStyle = `
        position: absolute; top: 50%; transform: translateY(-50%);
        width: 60px; height: 100px; display: flex; align-items: center; justify-content: center;
        cursor: pointer; z-index: 3001; opacity: 0.5; transition: opacity 0.2s;
        color: white; font-size: 20px;
    `;
    
    const prevBtn = document.createElement('div');
    prevBtn.id = 'fs-prev';
    prevBtn.style.cssText = navStyle + 'left: 10px;';
    prevBtn.innerHTML = `<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>`;
    
    const nextBtn = document.createElement('div');
    nextBtn.id = 'fs-next';
    nextBtn.style.cssText = navStyle + 'right: 10px;';
    nextBtn.innerHTML = `<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>`;

    // Эффекты ховера для навигации
    [prevBtn, nextBtn].forEach(btn => {
        btn.onmouseenter = () => btn.style.opacity = '1';
        btn.onmouseleave = () => btn.style.opacity = '0.5';
    });

    // Добавляем все элементы
    fsPreview.appendChild(closeBtn);
    fsPreview.appendChild(infoBtn);
    fsPreview.appendChild(downloadBtn);
    fsPreview.appendChild(prevBtn);
    fsPreview.appendChild(nextBtn);

    // 5. Панель информации (без изменений)
    const infoPanel = document.createElement('div');
    infoPanel.id = 'fs-info-panel';
    infoPanel.innerHTML = `
        <div class="fs-info-header">
            <div class="fs-info-title">INFO</div>
            <div class="fs-close-panel" style="cursor:pointer;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </div>
        </div>
        <div class="fs-info-content" id="fs-info-content-body" style="color: #ccc; font-size: 14px; line-height: 1.6;"></div>
    `;
    fsPreview.appendChild(infoPanel);

    // --- ОБРАБОТЧИКИ ---
    
    const closeFullscreen = () => {
        fsPreview.style.display = 'none';
        infoPanel.classList.remove('active');
        img.src = '';
        img.style.opacity = '0';
        loader.classList.remove('active');
        window.currentFsIndex = -1; // Сброс индекса
    };

    closeBtn.addEventListener('click', (e) => { e.stopPropagation(); closeFullscreen(); });
    infoBtn.addEventListener('click', (e) => { e.stopPropagation(); infoPanel.classList.toggle('active'); });
    infoPanel.querySelector('.fs-close-panel').addEventListener('click', (e) => { e.stopPropagation(); infoPanel.classList.remove('active'); });
    infoPanel.addEventListener('click', e => e.stopPropagation());
    
    // Перехват кликов по стрелкам будет в renderMasonry (через глобальную функцию)
    // Фоновый клик
    fsPreview.addEventListener('click', (e) => {
        if(e.target === fsPreview || e.target === imgContainer) closeFullscreen();
    });
}
// Функция заполнения панели данных
function populateFSInfo(data) {
    const body = document.getElementById('fs-info-content-body');
    if (!body) return;

    const safeText = (txt) => txt || '—';
    const dateStr = data.date ? data.date : 'Неизвестно';

    body.innerHTML = `
        <div class="fs-row">
            <div class="fs-label">Дата</div>
            <div class="fs-text" style="color:#aaa">${dateStr}</div>
        </div>
        <div class="fs-row">
            <div class="fs-label">Описание</div>
            <div class="fs-text">${safeText(data.caption)}</div>
        </div>
        ${data.ai_des ? `
        <div class="fs-row">
            <div class="fs-label">AI Analysis</div>
            <div class="fs-text" style="font-size:12px; color:#ccc;">${data.ai_des}</div>
        </div>` : ''}
        ${data.ai_style ? `
        <div class="fs-row">
            <div class="fs-label">Стилистика</div>
            <div class="fs-text" style="font-style:italic; color:#888;">${data.ai_style}</div>
        </div>` : ''}
        <div class="fs-row" style="margin-top:30px;">
            ${data.post_link ? `<a href="${data.post_link}" target="_blank" class="fs-btn-link">Открыть в Telegram</a>` : ''}
        </div>
    `;
}

// --- Основная функция инициализации ---

// --- КЭШ ДЛЯ УСКОРЕНИЯ (Хранит результаты resolve_image) ---
const RESOLVE_CACHE = new Map();

// --- Основная функция инициализации ---
export function initGallery() {
    // 0. Настройка фулскрин UI
    setupFullscreenUI();

    const overlay = document.getElementById('gallery-overlay');
    const content = document.getElementById('g-content');
    const searchInput = document.getElementById('g-search-input');
    const searchContainer = document.querySelector('.gallery-search'); // Родитель инпута
    const colorStrip = document.getElementById('color-strip');
    
    // --- 1. ДОБАВЛЕНИЕ КНОПКИ ОЧИСТКИ И ЛОАДЕРА ---
    
    // Создаем крестик очистки, если его нет
    let clearBtn = document.getElementById('g-search-clear');
    if (!clearBtn && searchContainer) {
        clearBtn = document.createElement('div');
        clearBtn.id = 'g-search-clear';
        clearBtn.innerHTML = `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
        searchContainer.appendChild(clearBtn);
    }

    // Создаем лоадер поиска, если его нет
    let galleryLoader = document.getElementById('gallery-loader');
    if (!galleryLoader) {
        galleryLoader = document.createElement('div');
        galleryLoader.id = 'gallery-loader';
        // Вставляем лоадер в тело галереи, чтобы он был по центру списка
        document.querySelector('.gallery-body').appendChild(galleryLoader);
    }

    // --- 2. Настройка колонок (Masonry) ---
    let colCount = window.innerWidth > 1200 ? 5 : window.innerWidth > 900 ? 4 : window.innerWidth > 600 ? 3 : 2;
    let columns = [];

    function setupColumns() {
        content.innerHTML = '';
        columns = [];
        for (let i = 0; i < colCount; i++) {
            const col = document.createElement('div');
            col.className = 'masonry-col';
            content.appendChild(col);
            columns.push(col);
        }
    }
    setupColumns();

    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            const newCount = window.innerWidth > 1200 ? 5 : window.innerWidth > 900 ? 4 : window.innerWidth > 600 ? 3 : 2;
            if (newCount !== colCount) {
                colCount = newCount;
                setupColumns();
                loadItems(true); 
            }
        }, 300);
    });

    // --- 3. Состояние галереи ---
    let state = {
        offset: 0,
        limit: 20,
        isLoading: false,
        hasMore: true,
        query: '',
        color: '',
        activeController: null
    };

    const sentinel = document.createElement('div');
    sentinel.style.width = '100%'; sentinel.style.height = '20px';

    const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && state.hasMore && !state.isLoading) {
            loadItems(false);
        }
    }, { root: content, rootMargin: '200px' });

    // --- 4. Загрузка (С УПРАВЛЕНИЕМ ЛОАДЕРОМ) ---
    async function loadItems(reset = false) {
        if (state.isLoading) return;
        state.isLoading = true;

        // Показываем лоадер только если это новая загрузка (поиск/фильтр), а не скролл
        if (reset) {
            galleryLoader.style.display = 'block';
            state.offset = 0;
            state.hasMore = true;
            columns.forEach(col => col.innerHTML = '');
        }

        if (state.activeController) state.activeController.abort();
        state.activeController = new AbortController();

        try {
            const url = `/api/anemone/search?q=${encodeURIComponent(state.query)}&color=${state.color}&offset=${state.offset}&limit=${state.limit}`;
            const res = await fetch(url, { signal: state.activeController.signal });
            const data = await res.json();

            // Скрываем лоадер как только получили список (картинки грузятся асинхронно)
            galleryLoader.style.display = 'none';

            if (!data.items || data.items.length === 0) {
                state.hasMore = false;
                observer.unobserve(sentinel);
            } else {
                renderMasonry(data.items, columns); // Передаем columns
                state.offset += data.items.length;
                
                if (data.items.length < state.limit) {
                    state.hasMore = false;
                    observer.unobserve(sentinel);
                } else {
                    // Добавляем sentinel в самую короткую или последнюю колонку
                    const lastCol = columns[columns.length - 1];
                    lastCol.appendChild(sentinel);
                    observer.observe(sentinel);
                }
            }
        } catch (e) {
            if (e.name !== 'AbortError') console.error(e);
            galleryLoader.style.display = 'none'; // Скрыть при ошибке
        } finally {
            state.isLoading = false;
        }
    }

    // --- 5. Drag Scroll ---
    function enableDragScroll(element) {
        let isDown = false;
        let startX, startY, scrollLeft, scrollTop;

        element.addEventListener('mousedown', (e) => {
            isDown = true;
            element.style.cursor = 'grabbing';
            startX = e.pageX - element.offsetLeft;
            startY = e.pageY - element.offsetTop;
            scrollLeft = element.scrollLeft;
            scrollTop = element.scrollTop;
        });

        const stopDrag = () => { isDown = false; element.style.cursor = 'grab'; };
        element.addEventListener('mouseleave', stopDrag);
        element.addEventListener('mouseup', stopDrag);

        element.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            e.preventDefault();
            const x = e.pageX - element.offsetLeft;
            const y = e.pageY - element.offsetTop;
            const walkX = (x - startX) * 1.5; 
            const walkY = (y - startY) * 1.5;
            
            element.scrollLeft = scrollLeft - walkX;
            if(element === content) { 
                element.scrollTop = scrollTop - walkY;
            }
        });
    }

    enableDragScroll(colorStrip);
    enableDragScroll(content);

    colorStrip.addEventListener('wheel', (e) => {
        if (e.deltaY !== 0) {
            e.preventDefault();
            colorStrip.scrollLeft += e.deltaY;
        }
    }, { passive: false });

    // --- 6. UI события ---
    
    // Клик по цвету
    colorStrip.addEventListener('click', (e) => {
        const item = e.target.closest('.color-item');
        if (!item) return;
        const selectedColor = item.dataset.color;

        if (state.color === selectedColor) {
            state.color = '';
            colorStrip.classList.remove('has-selection');
            document.querySelectorAll('.color-item').forEach(el => el.classList.remove('active'));
        } else {
            state.color = selectedColor;
            colorStrip.classList.add('has-selection');
            document.querySelectorAll('.color-item').forEach(el => el.classList.remove('active'));
            item.classList.add('active');
        }
        loadItems(true);
    });

    // Поиск + Логика крестика
    let debounce;
    const handleSearch = (val) => {
        state.query = val;
        loadItems(true);
        // Показываем крестик, если есть текст
        if (clearBtn) clearBtn.style.display = val.length > 0 ? 'block' : 'none';
    };

    searchInput.addEventListener('input', (e) => {
        const val = e.target.value;
        if (clearBtn) clearBtn.style.display = val.length > 0 ? 'block' : 'none';
        
        clearTimeout(debounce);
        // Уменьшили таймер до 300мс для скорости
        debounce = setTimeout(() => {
            handleSearch(val);
        }, 300);
    });

    // Клик по крестику
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            searchInput.value = '';
            clearBtn.style.display = 'none';
            handleSearch('');
        });
    }

    const galleryBtn = document.getElementById('gallery-btn');
    if (galleryBtn) {
        galleryBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            overlay.style.display = 'flex';
            window.dispatchEvent(new CustomEvent('toggle-pause', { detail: true })); // <--- ПАУЗА ВКЛ
            if (state.offset === 0) loadItems(true);
        });
    }
    const closeBtn = document.getElementById('g-close-btn');
    if (closeBtn) closeBtn.addEventListener('click', () => {
        overlay.style.display = 'none';
        window.dispatchEvent(new CustomEvent('toggle-pause', { detail: false })); // <--- ПАУЗА ВЫКЛ
    });
    const stopProp = (e) => e.stopPropagation();
    overlay.addEventListener('wheel', stopProp, { passive: true });
    overlay.addEventListener('touchstart', stopProp, { passive: true });
    overlay.addEventListener('touchmove', stopProp, { passive: true });
    overlay.addEventListener('touchend', stopProp, { passive: true });
    overlay.addEventListener('mousedown', stopProp);
    overlay.addEventListener('mouseup', stopProp);
    overlay.addEventListener('click', stopProp);

    const urlParams = new URLSearchParams(window.location.search);

    // Логика для чекбокса "Серверная загрузка" (?proxy=true)
    if (urlParams.get('proxy') === 'true') {
        const proxyToggle = document.getElementById('proxy-toggle');
        if (proxyToggle) {
            proxyToggle.checked = true;
            // Важно: вызываем событие change, чтобы обновился и глобальный CONFIG в основном скрипте
            proxyToggle.dispatchEvent(new Event('change'));
        }
    }

    // Логика для мгновенного открытия галереи (?gallery=true)
    if (urlParams.get('gallery') === 'true') {
        const overlay = document.getElementById('gallery-overlay');
        if (overlay) {
            overlay.style.display = 'flex';
            // Ставим сцену на паузу, как при клике на кнопку
            window.dispatchEvent(new CustomEvent('toggle-pause', { detail: true }));
            // Запускаем загрузку
            if (state.offset === 0) loadItems(true);
        }
    }
} // <--- Это закрывающая скобка функции initGallery

// Глобальная переменная для хранения текущего списка
let currentGalleryItems = [];
window.currentFsIndex = -1;

function openGalleryFullscreen(index) {
    if (index < 0 || index >= currentGalleryItems.length) return;
    
    window.currentFsIndex = index;
    const item = currentGalleryItems[index];
    
    const fsPreview = document.getElementById('fs-preview');
    const fsImg = document.getElementById('fs-img');
    const fsLoader = document.getElementById('fs-loader'); 
    const downloadBtn = document.getElementById('fs-download-btn');
    
    fsPreview.style.display = 'flex';
    fsImg.style.opacity = '0';
    fsImg.src = '';
    fsLoader.classList.add('active');

    // Обновляем информацию
    populateFSInfo(item);
    
    // Логика кнопки скачивания (Telegra.ph)
    if (item.original_link) {
        downloadBtn.style.display = 'flex';
        downloadBtn.onclick = (e) => {
            e.stopPropagation();
            window.open(item.original_link, '_blank');
        };
        downloadBtn.title = "Скачать оригинал";
    } else {
        downloadBtn.style.display = 'none';
    }

    // Загрузка полного изображения
    // Если есть данные из кэша resolve, берем url оттуда, иначе item.url (обычно там thumbnail)
    // Для высокого качества лучше использовать отдельный запрос resolve или менять параметры wsrv
    let fullUrl = item.url;
    if (RESOLVE_CACHE.has(item.post_id)) {
        fullUrl = RESOLVE_CACHE.get(item.post_id).url;
    }
    
    // Улучшаем качество если это wsrv
    if (fullUrl.includes('wsrv.nl')) {
        fullUrl = fullUrl.replace('&w=500', '&w=1600').replace('&w=1000', '&w=1600');
    }

    const fullImgLoader = new Image();
    fullImgLoader.src = fullUrl;
    
    fullImgLoader.onload = () => {
        fsImg.src = fullUrl;
        fsLoader.classList.remove('active'); 
        fsImg.style.opacity = '1';
    };
    fullImgLoader.onerror = () => {
        fsLoader.classList.remove('active');
        // alert("Ошибка загрузки");
    };
}

// Навешиваем обработчики на стрелки (один раз при инициализации скрипта)
document.addEventListener('DOMContentLoaded', () => {
    const prev = document.getElementById('fs-prev');
    const next = document.getElementById('fs-next');
    
    // Проверка на существование, т.к. setupFullscreenUI вызывается позже
    // Лучше использовать делегирование или проверить внутри click
    document.addEventListener('click', (e) => {
        if (e.target.closest('#fs-prev')) {
            e.stopPropagation();
            if (window.currentFsIndex > 0) openGalleryFullscreen(window.currentFsIndex - 1);
        }
        if (e.target.closest('#fs-next')) {
            e.stopPropagation();
            if (window.currentFsIndex < currentGalleryItems.length - 1) openGalleryFullscreen(window.currentFsIndex + 1);
        }
    });
    
    // Стрелки клавиатуры
    document.addEventListener('keydown', (e) => {
        const fsPreview = document.getElementById('fs-preview');
        if (fsPreview.style.display === 'flex') {
            if (e.key === 'ArrowLeft' && window.currentFsIndex > 0) openGalleryFullscreen(window.currentFsIndex - 1);
            if (e.key === 'ArrowRight' && window.currentFsIndex < currentGalleryItems.length - 1) openGalleryFullscreen(window.currentFsIndex + 1);
            if (e.key === 'Escape') document.getElementById('fs-close-btn').click();
        }
    });
});


// --- 5. Рендер с КЭШИРОВАНИЕМ ---
function renderMasonry(items, columns) {
    const useProxy = document.getElementById('proxy-toggle')?.checked || false; 

    // --- ВАЖНО: Обновляем глобальный список для навигации ---
    // Если это первая страница, перезаписываем, если подгрузка - добавляем?
    // В текущей реализации loadItems очищает колонки при reset=true.
    // Для корректной работы стрелок при подгрузке нужно хитро объединять массивы.
    // Упрощение: мы просто пушим новые items в currentGalleryItems, если это не сброс.
    
    // Проверка: это новые данные или добавление? 
    // Поскольку renderMasonry вызывается с куском данных (chunk), нам нужно понимать контекст.
    // Самый простой способ: в loadItems при reset=true делать currentGalleryItems = [];
    // А здесь делать currentGalleryItems.push(...items).
    // НО: renderMasonry вызывается внутри loadItems. 
    // Давай изменим это прямо здесь, предполагая, что items - это ТОЛЬКО ЧТО загруженные.
    
    // Однако индексы в DOM и в массиве должны совпадать.
    // ПРИМЕЧАНИЕ: Чтобы не ломать архитектуру, добавим проверку в loadItems (см. ниже),
    // а здесь просто будем использовать items как есть, но нам нужен GLOBAL OFFSET.
    
    // РЕШЕНИЕ: Привяжем данные прямо к DOM элементу div.gallery-item
    
    items.forEach((item, index) => {
        if (!item.post_id) return;

        let minCol = columns[0];
        columns.forEach(col => { if (col.offsetHeight < minCol.offsetHeight) minCol = col; });

        const div = document.createElement('div');
        div.className = 'gallery-item';
        div.style.minHeight = '200px'; 
        
        // Сохраняем данные для клика
        div.__galleryItem = item;
        
        const img = document.createElement('img');
        div.appendChild(img);

        const overlayInfo = document.createElement('div');
        overlayInfo.className = 'gallery-overlay-info';
        div.appendChild(overlayInfo);

        minCol.appendChild(div);

        const applyData = (d) => {
            if (!d.url || d.url.includes('via.placeholder.com')) { div.remove(); return; }

            // Обновляем данные item с учетом resolve (url, sizes)
            Object.assign(item, d); // Важно обновить объект, чтобы в фулскрине была правильная ссылка
            
            let thumbUrl = d.url;
            if (thumbUrl.includes('wsrv.nl')) {
                thumbUrl = thumbUrl.replace('&n=-1', '') + '&w=500&q=75&output=webp';
            }

            const safetyTimeout = setTimeout(() => { if(!img.complete) div.remove(); }, 8000); 

            img.src = thumbUrl;
            img.onload = () => {
                clearTimeout(safetyTimeout);
                div.classList.add('loaded');
                div.style.minHeight = 'auto';

                const captionText = d.caption ? d.caption.slice(0, 60) + (d.caption.length > 60 ? '...' : '') : 'Без описания';
                const linkUrl = d.post_link || item.post_link || '#';
                const linkStyle = (linkUrl === '#') ? 'display:none' : '';

                overlayInfo.innerHTML = `
                    <div class="g-caption-preview">${captionText}</div>
                    <div class="g-actions">
                        <div class="g-btn-action g-btn-target">Цель</div>
                        <a href="${linkUrl}" target="_blank" class="g-btn-action g-btn-link" style="${linkStyle}" onclick="event.stopPropagation();">
                            <svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M20.665 3.717l-17.73 6.837c-1.21.486-1.203 1.161-.222 1.462l4.552 1.42 10.532-6.645c.498-.303.953-.14.579.192l-8.533 7.701h-.002l-.002.001-.314 4.692c.46 0 .663-.211.921-.46l2.211-2.15 4.599 3.397c.848.467 1.457.227 1.668-.785l3.019-14.228c.309-1.239-.473-1.8-1.282-1.432z"/></svg>
                        </a>
                    </div>
                `;
                
                // --- ОБРАБОТЧИК КЛИКА ПО КАРТИНКЕ ---
                div.addEventListener('click', (e) => {
                    if (e.target.closest('.g-btn-target') || e.target.closest('.g-btn-link')) return;
                    
                    // Собираем актуальный список всех элементов в DOM для правильной навигации
                    // Это нужно, потому что Masonry перемешивает порядок в DOM (разные колонки), 
                    // но нам нужен логический порядок или визуальный? 
                    // Для простоты соберем currentGalleryItems из всех .gallery-item в DOM
                    
                    const allDivs = Array.from(document.querySelectorAll('.gallery-item'));
                    currentGalleryItems = allDivs.map(el => el.__galleryItem).filter(x => x);
                    
                    // Находим индекс текущего
                    const myIndex = allDivs.indexOf(div);
                    
                    openGalleryFullscreen(myIndex);
                });

                const targetBtn = overlayInfo.querySelector('.g-btn-target');
                targetBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    let cx = 0, cy = 0, cz = 0;
                    if (window.camera) { cx = window.camera.position.x; cy = window.camera.position.y; cz = window.camera.position.z; }

                    targetBtn.innerText = "Поиск...";
                    fetch(`/api/anemone/locate_post?post_id=${item.post_id}&x=${cx}&y=${cy}&z=${cz}&channel_id=@anemonn`)
                        .then(res => res.json())
                        .then(locData => {
                            if (locData.found && locData.pos) {
                                window.dispatchEvent(new CustomEvent('set-navigation-target', {
                                    detail: { x: locData.pos.x, y: locData.pos.y, z: locData.pos.z }
                                }));
                                document.getElementById('gallery-overlay').style.display = 'none';
                                window.dispatchEvent(new CustomEvent('toggle-pause', { detail: false })); 
                            } else {
                                alert("Объект далеко.");
                            }
                        })
                        .finally(() => { targetBtn.innerText = "Цель"; });
                });
            };
            img.onerror = () => div.remove();
        };

        if (RESOLVE_CACHE.has(item.post_id)) {
            applyData(RESOLVE_CACHE.get(item.post_id));
        } else {
            fetch(`/api/anemone/resolve_image?post_id=${item.post_id}&channel_id=@anemonn&use_proxy=${useProxy}`)
                .then(r => r.json())
                .then(d => {
                    RESOLVE_CACHE.set(item.post_id, d);
                    applyData(d);
                })
                .catch(() => div.remove());
        }
    });
}
