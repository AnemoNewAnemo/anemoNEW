// gallery.js

// Функция создания UI для фулскрина (если его нет в HTML)
function setupFullscreenUI() {
    const fsPreview = document.getElementById('fs-preview');
    if (!fsPreview) return;

    fsPreview.innerHTML = '';

    if (!document.getElementById('fs-zoom-style')) {
        const style = document.createElement('style');
        style.id = 'fs-zoom-style';
        style.innerHTML = `
            #fs-zoom-container {
                position: absolute; bottom: 40px; right: 50%; transform: translateX(50%); z-index: 3001;
                display: flex; align-items: center; gap: 16px;
                background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
                border: 1px solid rgba(255,255,255,0.05); border-radius: 40px;
                padding: 10px 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
            #fs-zoom-slider { 
                width: 120px; cursor: pointer; accent-color: #fff; height: 2px;
                -webkit-appearance: none; background: rgba(255,255,255,0.2); outline: none; border-radius: 2px;
            }
            #fs-zoom-slider::-webkit-slider-thumb {
                -webkit-appearance: none; width: 12px; height: 12px; background: #fff; border-radius: 50%; transition: transform 0.2s;
            }
            #fs-zoom-slider::-webkit-slider-thumb:hover { transform: scale(1.3); }
            .fs-action-btn:hover { background: rgba(255,255,255,0.1); color: #fff; transform: scale(1.05); }
            @media (max-width: 600px) {
                #fs-zoom-container { bottom: 24px; padding: 8px 16px; gap: 12px; }
                #fs-zoom-slider { width: 80px; }
            }
        `;
        document.head.appendChild(style);
    }

    const imgContainer = document.createElement('div');
    imgContainer.style.cssText = 'position:relative; width:100%; height:100%; display:flex; justify-content:center; align-items:center; overflow:hidden;';

    const img = document.createElement('img');
    img.id = 'fs-img';
    img.style.cssText = 'max-width:90%; max-height:90%; opacity:0; transition:opacity 0.6s ease; user-select:none; -webkit-user-drag:none;';
    
    const loader = document.createElement('div');
    loader.id = 'fs-loader';
    loader.className = 'fs-loader';

    imgContainer.appendChild(loader);
    imgContainer.appendChild(img);
    fsPreview.appendChild(imgContainer);

    let currentScale = 1, currentPanX = 0, currentPanY = 0;
    let isPanning = false, startPanX = 0, startPanY = 0;
    let initialPinchDistance = null, initialScale = 1, isDragged = false;

    const zoomContainer = document.createElement('div');
    zoomContainer.id = 'fs-zoom-container';

    const resetZoomBtn = document.createElement('div');
    resetZoomBtn.title = "Сбросить масштаб";
    resetZoomBtn.style.cssText = "cursor:pointer; display:flex; align-items:center; color:rgba(255,255,255,0.5); transition:0.3s;";
    resetZoomBtn.onmouseenter = (e) => e.currentTarget.style.color = '#fff';
    resetZoomBtn.onmouseleave = (e) => e.currentTarget.style.color = 'rgba(255,255,255,0.5)';
    resetZoomBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>`;

    const zoomSlider = document.createElement('input');
    zoomSlider.id = 'fs-zoom-slider';
    zoomSlider.type = 'range';
    zoomSlider.min = '1'; zoomSlider.max = '5'; zoomSlider.step = '0.1'; zoomSlider.value = '1';

    const zoomLabel = document.createElement('div');
    zoomLabel.style.cssText = "color:rgba(255,255,255,0.8); font-size:12px; font-weight:300; min-width:40px; text-align:right;";
    zoomLabel.innerText = "100%";

    zoomContainer.appendChild(resetZoomBtn);
    zoomContainer.appendChild(zoomSlider);
    zoomContainer.appendChild(zoomLabel);
    fsPreview.appendChild(zoomContainer);

    const updateImageTransform = () => {
        if (currentScale <= 1) {
            currentScale = 1;
            if (currentPanX !== 0 || currentPanY !== 0) {
                currentPanX = 0;
                currentPanY = 0;
                img.style.transition = 'transform 0.4s cubic-bezier(0.2, 0.8, 0.2, 1), opacity 0.6s ease';
                clearTimeout(window.zoomTransitionTimeout);
                window.zoomTransitionTimeout = setTimeout(() => { img.style.transition = 'opacity 0.6s ease'; }, 400);
            }
        } else {
            img.style.transition = 'opacity 0.6s ease';
        }
        img.style.transform = `translate(${currentPanX}px, ${currentPanY}px) scale(${currentScale})`;
        zoomSlider.value = currentScale;
        zoomLabel.innerText = Math.round(currentScale * 100) + '%';
        imgContainer.style.cursor = currentScale > 1 ? (isPanning ? 'grabbing' : 'grab') : 'default';
    };

    window.resetFsZoom = () => {
        currentScale = 1; currentPanX = 0; currentPanY = 0;
        img.style.transition = 'transform 0.4s cubic-bezier(0.2, 0.8, 0.2, 1), opacity 0.6s ease';
        updateImageTransform();
        clearTimeout(window.zoomTransitionTimeout);
        window.zoomTransitionTimeout = setTimeout(() => { img.style.transition = 'opacity 0.6s ease'; }, 400);
    };

    resetZoomBtn.onclick = (e) => { e.stopPropagation(); window.resetFsZoom(); };
    zoomSlider.oninput = (e) => { e.stopPropagation(); currentScale = parseFloat(e.target.value); updateImageTransform(); };
    zoomSlider.onmousedown = (e) => e.stopPropagation(); zoomSlider.ontouchstart = (e) => e.stopPropagation();
    resetZoomBtn.onmousedown = (e) => e.stopPropagation(); resetZoomBtn.ontouchstart = (e) => e.stopPropagation();

    imgContainer.addEventListener('wheel', (e) => {
        e.preventDefault();
        const zoomAmount = e.deltaY * -0.005;
        currentScale = Math.min(Math.max(1, currentScale + zoomAmount), 5);
        updateImageTransform();
    });

    imgContainer.addEventListener('mousedown', (e) => {
        if (e.target.closest('#fs-zoom-container') || e.target.closest('.fs-action-btn') || e.target.closest('#fs-prev') || e.target.closest('#fs-next')) return;
        isDragged = false;
        if (currentScale <= 1) return;
        e.preventDefault();
        isPanning = true;
        startPanX = e.clientX - currentPanX;
        startPanY = e.clientY - currentPanY;
        imgContainer.style.cursor = 'grabbing';
    });
    window.addEventListener('mousemove', (e) => {
        if (!isPanning) return;
        isDragged = true;
        currentPanX = e.clientX - startPanX;
        currentPanY = e.clientY - startPanY;
        updateImageTransform();
    });
    window.addEventListener('mouseup', () => {
        isPanning = false;
        if (currentScale > 1) imgContainer.style.cursor = 'grab';
    });

    imgContainer.addEventListener('touchstart', (e) => {
        if (e.target.closest('#fs-zoom-container') || e.target.closest('.fs-action-btn') || e.target.closest('#fs-prev') || e.target.closest('#fs-next')) return;
        isDragged = false;
        if (e.touches.length === 1 && currentScale > 1) {
            isPanning = true;
            startPanX = e.touches[0].clientX - currentPanX;
            startPanY = e.touches[0].clientY - currentPanY;
        } else if (e.touches.length === 2) {
            isPanning = false;
            initialPinchDistance = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY);
            initialScale = currentScale;
        }
    }, { passive: false });

    imgContainer.addEventListener('touchmove', (e) => {
        if (currentScale > 1 || e.touches.length === 2) e.preventDefault(); 
        isDragged = true;
        if (e.touches.length === 1 && isPanning) {
            currentPanX = e.touches[0].clientX - startPanX;
            currentPanY = e.touches[0].clientY - startPanY;
            updateImageTransform();
        } else if (e.touches.length === 2 && initialPinchDistance) {
            const currentDistance = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY);
            const scaleAmount = currentDistance / initialPinchDistance;
            currentScale = Math.min(Math.max(1, initialScale * scaleAmount), 5);
            updateImageTransform();
        }
    }, { passive: false });

    imgContainer.addEventListener('touchend', (e) => {
        isPanning = false;
        initialPinchDistance = null;
        if (e.touches.length === 1 && currentScale > 1) {
            isPanning = true;
            startPanX = e.touches[0].clientX - currentPanX;
            startPanY = e.touches[0].clientY - currentPanY;
        }
    });

    const btnStyle = `
        position: absolute; right: 40px; width: 48px; height: 48px;
        background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
        border: 1px solid rgba(255,255,255,0.05); border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; z-index: 3001; transition: all 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2); color: rgba(255,255,255,0.7);
    `;

    const closeBtn = document.createElement('div');
    closeBtn.id = 'fs-close-btn';
    closeBtn.className = 'fs-action-btn';
    closeBtn.style.cssText = btnStyle + 'top: 40px;';
    closeBtn.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
    
    const infoBtn = document.createElement('div');
    infoBtn.className = 'fs-info-trigger-btn fs-action-btn';
    infoBtn.style.cssText = btnStyle + 'top: 104px;';
    infoBtn.innerHTML = `<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`;

    const downloadBtn = document.createElement('div');
    downloadBtn.id = 'fs-download-btn';
    downloadBtn.className = 'fs-action-btn';
    downloadBtn.style.cssText = btnStyle + 'top: 168px; display: none;';
    downloadBtn.innerHTML = `<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>`;

    const navStyle = `
        position: absolute; top: 50%; transform: translateY(-50%);
        width: 80px; height: 120px; display: flex; align-items: center; justify-content: center;
        cursor: pointer; z-index: 3001; opacity: 0.3; transition: all 0.3s ease;
        color: white; font-size: 20px;
    `;
    
    const prevBtn = document.createElement('div');
    prevBtn.id = 'fs-prev';
    prevBtn.style.cssText = navStyle + 'left: 20px;';
    prevBtn.innerHTML = `<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>`;
    
    const nextBtn = document.createElement('div');
    nextBtn.id = 'fs-next';
    nextBtn.style.cssText = navStyle + 'right: 20px;';
    nextBtn.innerHTML = `<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>`;

    [prevBtn, nextBtn].forEach(btn => {
        btn.onmouseenter = () => { btn.style.opacity = '1'; btn.style.transform = `translateY(-50%) scale(1.1)`; };
        btn.onmouseleave = () => { btn.style.opacity = '0.3'; btn.style.transform = `translateY(-50%) scale(1)`; };
    });

    fsPreview.appendChild(closeBtn);
    fsPreview.appendChild(infoBtn);
    fsPreview.appendChild(downloadBtn);
    fsPreview.appendChild(prevBtn);
    fsPreview.appendChild(nextBtn);

    const infoPanel = document.createElement('div');
    infoPanel.id = 'fs-info-panel';
    infoPanel.style.cssText = `
        position: absolute; top: 0; right: 0; bottom: 0;
        width: 360px; background: rgba(10, 12, 16, 0.7);
        backdrop-filter: blur(30px); -webkit-backdrop-filter: blur(30px);
        border-left: 1px solid rgba(255,255,255,0.05);
        z-index: 3002; transform: translateX(100%);
        transition: transform 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);
        padding: 40px 30px; box-sizing: border-box;
        display: flex; flex-direction: column; box-shadow: -10px 0 40px rgba(0,0,0,0.3);
    `;
    infoPanel.innerHTML = `
        <div class="fs-info-header" style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 30px;">
            <div class="fs-info-title" style="font-size: 14px; font-weight: 300; letter-spacing: 3px; text-transform: uppercase; color: #fff;">Информация</div>
            <div class="fs-close-panel" style="cursor:pointer; opacity: 0.5; transition: 0.3s; display:flex;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </div>
        </div>
        <div class="fs-info-content" id="fs-info-content-body" style="color: #ccc; font-size: 14px; line-height: 1.6; font-weight: 300;"></div>
    `;
    fsPreview.appendChild(infoPanel);

    const closeFullscreen = () => {
        if (window.resetFsZoom) window.resetFsZoom();
        fsPreview.style.display = 'none';
        infoPanel.style.transform = 'translateX(100%)';
        img.src = '';
        img.style.opacity = '0';
        loader.classList.remove('active');
        window.currentFsIndex = -1;
    };

    closeBtn.addEventListener('click', (e) => { e.stopPropagation(); closeFullscreen(); });
    infoBtn.addEventListener('click', (e) => { 
        e.stopPropagation(); 
        const isActive = infoPanel.style.transform === 'translateX(0px)';
        infoPanel.style.transform = isActive ? 'translateX(100%)' : 'translateX(0px)';
    });
    infoPanel.querySelector('.fs-close-panel').addEventListener('click', (e) => { e.stopPropagation(); infoPanel.style.transform = 'translateX(100%)'; });
    infoPanel.querySelector('.fs-close-panel').onmouseenter = (e) => e.currentTarget.style.opacity = '1';
    infoPanel.querySelector('.fs-close-panel').onmouseleave = (e) => e.currentTarget.style.opacity = '0.5';
    infoPanel.addEventListener('click', e => e.stopPropagation());
    
    fsPreview.addEventListener('click', (e) => {
        if (isDragged) return; 
        if (e.target === fsPreview || e.target === imgContainer) closeFullscreen();
    });
}
// Функция заполнения панели данных
function populateFSInfo(data) {
    const body = document.getElementById('fs-info-content-body');
    if (!body) return;

    const safeText = (txt) => txt || '—';
    const dateStr = data.date ? data.date : 'Неизвестно';

    body.innerHTML = `
        <div class="fs-row" style="margin-bottom: 20px;">
            <div class="fs-label" style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: rgba(255,255,255,0.4); margin-bottom: 6px;">Дата</div>
            <div class="fs-text" style="color: #fff;">${dateStr}</div>
        </div>
        <div class="fs-row" style="margin-bottom: 20px;">
            <div class="fs-label" style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: rgba(255,255,255,0.4); margin-bottom: 6px;">Описание</div>
            <div class="fs-text" style="color: #fff; line-height: 1.5;">${safeText(data.caption)}</div>
        </div>
        ${data.ai_des ? `
        <div class="fs-row" style="margin-bottom: 20px;">
            <div class="fs-label" style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: rgba(255,255,255,0.4); margin-bottom: 6px;">AI Analysis</div>
            <div class="fs-text" style="color: rgba(255,255,255,0.7);">${data.ai_des}</div>
        </div>` : ''}
        ${data.ai_style ? `
        <div class="fs-row" style="margin-bottom: 20px;">
            <div class="fs-label" style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: rgba(255,255,255,0.4); margin-bottom: 6px;">Стилистика</div>
            <div class="fs-text" style="color: rgba(255,255,255,0.7); font-style: italic;">${data.ai_style}</div>
        </div>` : ''}
        <div class="fs-row" style="margin-top:40px;">
            ${data.post_link ? `<a href="${data.post_link}" target="_blank" style="display: inline-block; padding: 12px 24px; border: 1px solid rgba(255,255,255,0.2); border-radius: 30px; color: #fff; text-decoration: none; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; transition: 0.3s;" onmouseover="this.style.background='#fff'; this.style.color='#000';" onmouseout="this.style.background='transparent'; this.style.color='#fff';">Открыть в Telegram</a>` : ''}
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
        similar_to: null,
        activeController: null,
        // Новые фильтры
        filters: {
            dom_color: '', sec_color: '',
            br_min: 0, br_max: 1,
            sat_min: 0, sat_max: 1,
            date_from: '', date_to: ''
        }
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
            let url = `/api/anemone/search?q=${encodeURIComponent(state.query)}&color=${state.color}&offset=${state.offset}&limit=${state.limit}&similar_to=${state.similar_to || ''}`;
            
            // Добавляем новые параметры фильтра
            if (state.filters.dom_color) url += `&dom_color=${state.filters.dom_color}`;
            if (state.filters.sec_color) url += `&sec_color=${state.filters.sec_color}`;
            if (state.filters.br_min > 0) url += `&br_min=${state.filters.br_min}`;
            if (state.filters.br_max < 1) url += `&br_max=${state.filters.br_max}`;
            if (state.filters.sat_min > 0) url += `&sat_min=${state.filters.sat_min}`;
            if (state.filters.sat_max < 1) url += `&sat_max=${state.filters.sat_max}`;
            if (state.filters.date_from) url += `&date_from=${state.filters.date_from}`;
            if (state.filters.date_to) url += `&date_to=${state.filters.date_to}`;

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
        if (clearBtn) clearBtn.style.display = (val.length > 0 || state.similar_to) ? 'flex' : 'none';
    };

    searchInput.addEventListener('input', (e) => {
        if (state.similar_to) return; // Игнорируем ввод, если активен поиск по картинке
        const val = e.target.value;
        if (clearBtn) clearBtn.style.display = val.length > 0 ? 'flex' : 'none';
        
        clearTimeout(debounce);
        debounce = setTimeout(() => handleSearch(val), 300);
    });

    // Событие включения поиска по картинке
    window.addEventListener('search-similar', (e) => {
        state.similar_to = e.detail;
        state.query = '';
        searchInput.value = 'Поиск по картинке...';
        searchInput.readOnly = true; 
        searchInput.style.color = '#ffaa00'; // Выделяем цветом
        if (clearBtn) clearBtn.style.display = 'flex';
        
        // Сбрасываем цвета
        state.color = '';
        colorStrip.classList.remove('has-selection');
        document.querySelectorAll('.color-item').forEach(el => el.classList.remove('active'));

        loadItems(true);
    });

    // Клик по крестику
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            searchInput.value = '';
            searchInput.readOnly = false;
            searchInput.style.color = ''; // Возвращаем цвет
            clearBtn.style.display = 'none';
            state.similar_to = null;
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

    // --- 7. Логика панели фильтров ---
    const filterBtn = document.getElementById('g-filter-btn');
    const filterPanel = document.getElementById('gallery-filter-panel');
    
    if (filterBtn && filterPanel) {
        filterBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            filterPanel.classList.toggle('show');
            filterBtn.classList.toggle('active');
        });

        // Закрываем панель при клике вне её
        document.getElementById('gallery-overlay').addEventListener('click', (e) => {
            if (!filterPanel.contains(e.target) && !filterBtn.contains(e.target) && filterPanel.classList.contains('show')) {
                filterPanel.classList.remove('show');
                filterBtn.classList.remove('active');
            }
        });

        // Синхронизация значений слайдеров
        const syncSlider = (id) => {
            const el = document.getElementById(id);
            const valEl = document.getElementById(id + '-val');
            el.addEventListener('input', () => { valEl.textContent = parseFloat(el.value).toFixed(2); });
        };
        ['f-br-min', 'f-br-max', 'f-sat-min', 'f-sat-max'].forEach(syncSlider);

        // Применение фильтров
        document.getElementById('f-apply-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            state.filters = {
                dom_color: document.getElementById('f-dom-color').value,
                sec_color: document.getElementById('f-sec-color').value,
                br_min: parseFloat(document.getElementById('f-br-min').value),
                br_max: parseFloat(document.getElementById('f-br-max').value),
                sat_min: parseFloat(document.getElementById('f-sat-min').value),
                sat_max: parseFloat(document.getElementById('f-sat-max').value),
                date_from: document.getElementById('f-date-from').value,
                date_to: document.getElementById('f-date-to').value
            };
            
            filterPanel.classList.remove('show');
            filterBtn.classList.remove('active');
            
            // Подсветка кнопки если активны расширенные фильтры
            const hasFilters = state.filters.dom_color || state.filters.sec_color || 
                               state.filters.br_min > 0 || state.filters.br_max < 1 || 
                               state.filters.sat_min > 0 || state.filters.sat_max < 1 || 
                               state.filters.date_from || state.filters.date_to;
            filterBtn.style.color = hasFilters ? '#ffaa00' : 'rgba(255,255,255,0.4)';
            
            loadItems(true); // Перезагружаем галерею
        });

        // Сброс фильтров
        document.getElementById('f-reset-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            document.getElementById('f-dom-color').value = '';
            document.getElementById('f-sec-color').value = '';
            
            document.getElementById('f-br-min').value = '0'; document.getElementById('f-br-min-val').textContent = '0.00';
            document.getElementById('f-br-max').value = '1'; document.getElementById('f-br-max-val').textContent = '1.00';
            
            document.getElementById('f-sat-min').value = '0'; document.getElementById('f-sat-min-val').textContent = '0.00';
            document.getElementById('f-sat-max').value = '1'; document.getElementById('f-sat-max-val').textContent = '1.00';
            
            document.getElementById('f-date-from').value = '';
            document.getElementById('f-date-to').value = '';
            
            state.filters = { dom_color: '', sec_color: '', br_min: 0, br_max: 1, sat_min: 0, sat_max: 1, date_from: '', date_to: '' };
            filterBtn.style.color = 'rgba(255,255,255,0.4)';
            loadItems(true);
        });
        
        // Предотвращаем скролл подложки при работе с панелью
        filterPanel.addEventListener('wheel', e => e.stopPropagation(), {passive: true});
        filterPanel.addEventListener('touchmove', e => e.stopPropagation(), {passive: true});
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
    if (window.resetFsZoom) window.resetFsZoom();
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
                        <div class="g-btn-action g-btn-target">Похожее</div>
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
                    // Отправляем событие наверх, чтобы галерея пересобралась
                    window.dispatchEvent(new CustomEvent('search-similar', { detail: item.post_id }));
                    
                    // Скроллим галерею в самый верх
                    document.getElementById('g-content').scrollTop = 0;
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
