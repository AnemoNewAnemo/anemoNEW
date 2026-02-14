// gallery.js

// Функция создания UI для фулскрина (если его нет в HTML)
function setupFullscreenUI() {
    const fsPreview = document.getElementById('fs-preview');
    if (!fsPreview) return;

    // Очищаем, чтобы пересоздать структуру правильно
    fsPreview.innerHTML = '';

    // 1. Контейнер для картинки
    const imgContainer = document.createElement('div');
    imgContainer.style.position = 'relative';
    imgContainer.style.width = '100%';
    imgContainer.style.height = '100%';
    imgContainer.style.display = 'flex';
    imgContainer.style.justifyContent = 'center';
    imgContainer.style.alignItems = 'center';

    // 2. Элемент картинки
    const img = document.createElement('img');
    img.id = 'fs-img';
    img.style.maxWidth = '95%';
    img.style.maxHeight = '95%';
    img.style.boxShadow = '0 0 50px rgba(0,0,0,0.5)';
    img.style.opacity = '0'; // Скрыта пока грузится
    img.style.transition = 'opacity 0.5s ease';
    
    // 3. Лоадер (Пульсирующий круг)
    const loader = document.createElement('div');
    loader.id = 'fs-loader';
    loader.className = 'fs-loader'; // Стили описаны в CSS

    imgContainer.appendChild(loader);
    imgContainer.appendChild(img);
    fsPreview.appendChild(imgContainer);

    // 4. Кнопка "i" (Информация)
    const infoBtn = document.createElement('div');
    infoBtn.className = 'fs-info-trigger-btn';
    infoBtn.innerHTML = `<svg viewBox="0 0 24 24"><path d="M11 7h2v2h-2zm0 4h2v6h-2zm1-9C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/></svg>`;
    fsPreview.appendChild(infoBtn);

    // 5. Панель информации
    const infoPanel = document.createElement('div');
    infoPanel.id = 'fs-info-panel';
    infoPanel.innerHTML = `
        <div class="fs-info-header">
            <div class="fs-info-title">INFO</div>
            <div class="fs-close-panel">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </div>
        </div>
        <div class="fs-info-content" id="fs-info-content-body" style="color: #ccc; font-size: 14px; line-height: 1.6;"></div>
    `;
    fsPreview.appendChild(infoPanel);

    // --- ОБРАБОТЧИКИ СОБЫТИЙ ---

    // Клик по кнопке "i"
    infoBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        infoPanel.classList.toggle('active');
    });

    // Клик по крестику внутри панели
    infoPanel.querySelector('.fs-close-panel').addEventListener('click', (e) => {
        e.stopPropagation();
        infoPanel.classList.remove('active');
    });

    // Клик внутри панели не должен закрывать превью
    infoPanel.addEventListener('click', e => e.stopPropagation());

    // Закрытие всего фулскрина по клику на фон
    fsPreview.addEventListener('click', () => {
        fsPreview.style.display = 'none';
        infoPanel.classList.remove('active');
        img.src = '';
        img.style.opacity = '0';
        loader.classList.remove('active'); // Спрятать лоадер если закрыли во время загрузки
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
}

// --- 5. Рендер с КЭШИРОВАНИЕМ ---
function renderMasonry(items, columns) {
    // === ИСПРАВЛЕНИЕ: Получаем состояние чекбокса ===
    const useProxy = document.getElementById('proxy-toggle')?.checked || false; 

    items.forEach(item => {
        if (!item.post_id) return;

        // Находим самую короткую колонку
        let minCol = columns[0];
        columns.forEach(col => {
            if (col.offsetHeight < minCol.offsetHeight) minCol = col;
        });

        const div = document.createElement('div');
        div.className = 'gallery-item';
        div.style.minHeight = '200px'; 
        
        const img = document.createElement('img');
        div.appendChild(img);

        const overlayInfo = document.createElement('div');
        overlayInfo.className = 'gallery-overlay-info';
        div.appendChild(overlayInfo);

        minCol.appendChild(div);

        // Функция применения данных к карточке
        const applyData = (d) => {
            if (!d.url || d.url.includes('via.placeholder.com')) {
                div.remove(); return;
            }

            let thumbUrl = d.url;
            // Если прокси не включен, но ссылка от wsrv, оптимизируем её для превью
            if (thumbUrl.includes('wsrv.nl')) {
                thumbUrl = thumbUrl.replace('&n=-1', '') + '&w=500&q=75&output=webp';
            }

            // Таймаут на случай битой картинки
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
                                <svg viewBox="0 0 24 24" fill="currentColor" stroke="none">
                                    <path d="M20.665 3.717l-17.73 6.837c-1.21.486-1.203 1.161-.222 1.462l4.552 1.42 10.532-6.645c.498-.303.953-.14.579.192l-8.533 7.701h-.002l-.002.001-.314 4.692c.46 0 .663-.211.921-.46l2.211-2.15 4.599 3.397c.848.467 1.457.227 1.668-.785l3.019-14.228c.309-1.239-.473-1.8-1.282-1.432z"/>
                                </svg>
                            </a>
                    </div>
                `;
                
                // Обработчики кликов (те же, что и были)
                div.addEventListener('click', (e) => {
                    if (e.target.closest('.g-btn-target') || e.target.closest('.g-btn-link')) return;
                    
                    const fsPreview = document.getElementById('fs-preview');
                    const fsImg = document.getElementById('fs-img');
                    const fsLoader = document.getElementById('fs-loader'); 
                    
                    fsPreview.style.display = 'flex';
                    fsImg.style.opacity = '0';
                    fsImg.src = '';
                    fsLoader.classList.add('active');

                    const fullData = { ...item, ...d };
                    populateFSInfo(fullData);
                    
                    const fullUrl = d.url.includes('wsrv.nl') ? d.url.replace('&w=500', '&w=1600') : d.url;
                    
                    const fullImgLoader = new Image();
                    fullImgLoader.src = fullUrl;
                    
                    fullImgLoader.onload = () => {
                        fsImg.src = fullUrl;
                        fsLoader.classList.remove('active'); 
                        fsImg.style.opacity = '1';
                    };
                    fullImgLoader.onerror = () => {
                        fsLoader.classList.remove('active');
                        alert("Ошибка загрузки полной версии");
                    };
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

        // --- ЛОГИКА КЭШИРОВАНИЯ ---
        if (RESOLVE_CACHE.has(item.post_id)) {
            applyData(RESOLVE_CACHE.get(item.post_id));
        } else {
            // ТЕПЕРЬ useProxy ОПРЕДЕЛЕН И ОШИБКИ НЕ БУДЕТ
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
