import * as THREE from 'three';

export class VideoCaptureManager {
    // 1. ДОБАВИЛИ getTerrainHeightFn В КОНСТРУКТОР
    constructor(scene, camera, renderer, globalUniforms, getTerrainHeightFn) {
        this.scene = scene;
        this.camera = camera;
        this.renderer = renderer;
        this.globalUniforms = globalUniforms;
        
        // Сохраняем ссылку на функцию генерации ландшафта
        this.getTerrainHeight = getTerrainHeightFn; 
        
        this.isRecording = false;
        this.isPreviewing = false; 
        this.virtualTime = 0;
        
        this.basePos = new THREE.Vector3();
        this.baseQuat = new THREE.Quaternion();
        
        this.previewRafId = null;
        
        this.initUI();
    }

    initUI() {
        const modalHtml = `
            <div id="video-modal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:3000; align-items:center; justify-content:center; backdrop-filter:blur(10px); font-family: 'Courier New', monospace; transition: background 0.3s, backdrop-filter 0.3s;">
                
                <!-- Обертка контента, чтобы скрывать её при предпросмотре -->
                <div id="video-modal-content" style="background:rgba(20, 20, 25, 0.95); padding:24px; border-radius:16px; width:360px; max-height:90vh; overflow-y:auto; border:1px solid rgba(255,255,255,0.1); color:#fff; box-shadow: 0 20px 60px rgba(0,0,0,0.5); scrollbar-width:thin;">
                    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:12px; margin-bottom:16px;">
                        <h3 style="margin:0; letter-spacing:2px; font-weight:bold; color:#ffaa00;">🎥 ЗАХВАТ ВИДЕО</h3>
                        <button id="close-video-modal" style="background:none; border:none; color:#aaa; cursor:pointer; font-size:20px;">✕</button>
                    </div>

                    <div style="display:flex; gap:10px; margin-bottom:12px;">
                        <div style="flex:1;"><label style="font-size:11px; color:#aaa;">Качество (Scale)</label><input type="range" id="vid-scale" min="0.5" max="3.0" step="0.25" value="1.0" style="width:100%;"></div>
                        <div style="flex:1;"><label style="font-size:11px; color:#aaa;">FPS</label>
                            <select id="vid-fps" style="width:100%; background:rgba(0,0,0,0.5); border:1px solid #444; color:#fff; padding:4px; border-radius:4px;">
                                <option value="24">24 (Кино)</option>
                                <option value="30">30 (Стандарт)</option>
                                <option value="60" selected>60 (Плавно)</option>
                            </select>
                        </div>
                    </div>
                    <div style="margin-bottom:16px;">
                        <label style="font-size:11px; color:#aaa;">Длительность (секунд): <span id="vid-dur-val" style="color:#fff;">5</span>s</label>
                        <input type="range" id="vid-duration" min="1" max="30" step="1" value="5" style="width:100%;">
                    </div>

                    <div style="border-top:1px solid rgba(255,255,255,0.1); padding-top:12px; margin-bottom:16px;">
                        <label style="font-size:12px; color:#00aaff; font-weight:bold;">ДВИЖЕНИЕ КАМЕРЫ</label>
                        <select id="vid-preset" style="width:100%; background:rgba(0,0,0,0.5); border:1px solid #444; color:#fff; padding:6px; border-radius:4px; margin-top:8px; margin-bottom:12px;">
                            <option value="static">Статика (Стоит на месте)</option>
                            <option value="pan">Вращение (Осмотр вокруг)</option>
                            <option value="fly">Пролёт (Движение вперёд)</option>
                        </select>

                        <div id="vid-speed-group" style="display:none;">
                            <label style="font-size:11px; color:#aaa;">Скорость движения/вращения</label>
                            <input type="range" id="vid-speed" min="-5" max="5" step="0.1" value="1" style="width:100%;">
                        </div>
                        <div id="vid-wobble-group" style="display:none; margin-top:8px;">
                            <label style="font-size:11px; color:#aaa;">Отклонения при пролёте (Тряска)</label>
                            <input type="range" id="vid-wobble" min="0" max="10" step="0.1" value="0" style="width:100%; margin-bottom: 8px;">
                            <label style="font-size:11px; color:#aaa; display:flex; align-items:center; gap:6px; cursor:pointer;">
                                <input type="checkbox" id="vid-follow-terrain" checked> По уровню земли (огибать рельеф)
                            </label>
                        </div>
                    </div>

                    <div style="border-top:1px solid rgba(255,255,255,0.1); padding-top:12px; margin-bottom:16px;">
                        <label style="font-size:12px; color:#ff6666; font-weight:bold;">СЛУЧАЙНЫЕ ПОВОРОТЫ (Дрожание)</label>
                        <div style="display:flex; gap:10px; margin-top:8px;">
                            <div style="flex:1;"><label style="font-size:10px; color:#aaa;">Ось X (Вверх/Вниз)</label><input type="range" id="vid-shake-x" min="0" max="0.5" step="0.01" value="0" style="width:100%;"></div>
                            <div style="flex:1;"><label style="font-size:10px; color:#aaa;">Ось Y (Влево/Вправо)</label><input type="range" id="vid-shake-y" min="0" max="0.5" step="0.01" value="0" style="width:100%;"></div>
                        </div>
                        <div style="display:flex; gap:10px; margin-top:8px;">
                            <div style="flex:1;"><label style="font-size:10px; color:#aaa;">Наклон (Крен)</label><input type="range" id="vid-shake-z" min="0" max="0.5" step="0.01" value="0" style="width:100%;"></div>
                            <div style="flex:1;"><label style="font-size:10px; color:#aaa;">Скорость тряски</label><input type="range" id="vid-shake-speed" min="0.1" max="10" step="0.1" value="2" style="width:100%;"></div>
                        </div>
                    </div>

                    <!-- Прогресс бар -->
                    <div id="vid-progress-container" style="display:none; margin-bottom:16px;">
                        <div style="font-size:11px; color:#44ff44; margin-bottom:4px; text-align:center;" id="vid-status">Рендеринг: 0%</div>
                        <div style="width:100%; height:8px; background:#222; border-radius:4px; overflow:hidden;">
                            <div id="vid-progress-bar" style="width:0%; height:100%; background:#44ff44; transition:width 0.1s;"></div>
                        </div>
                    </div>

                    <div id="vid-actions-group" style="display:flex; gap:10px;">
                        <button id="vid-preview-btn" style="flex:1; padding:12px; background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.2); color:#fff; font-weight:bold; border-radius:6px; cursor:pointer; font-size:12px; transition:0.2s;">👀 ПРЕДПРОСМОТР</button>
                        <button id="vid-start-btn" style="flex:1; padding:12px; background:#ffaa00; border:none; color:#000; font-weight:bold; border-radius:6px; cursor:pointer; font-size:12px; transition:0.2s;">🔴 ЗАПИСЬ</button>
                    </div>
                </div>

                <!-- Кнопка остановки предпросмотра -->
                <button id="vid-stop-preview-btn" style="display:none; position:fixed; bottom:40px; left:50%; transform:translateX(-50%); z-index:4000; padding:15px 30px; background:#ff4444; color:#fff; border:2px solid #ffaaaa; border-radius:30px; font-weight:bold; cursor:pointer; box-shadow: 0 10px 30px rgba(0,0,0,0.8); font-size:14px;">⏹ ОСТАНОВИТЬ ПРЕДПРОСМОТР</button>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        this.modal = document.getElementById('video-modal');
        this.modalContent = document.getElementById('video-modal-content');
        this.stopPreviewBtn = document.getElementById('vid-stop-preview-btn');
        
        // Блокировка событий для камеры
        const stopProp = (e) => e.stopPropagation();
        this.modalContent.addEventListener('mousedown', stopProp);
        this.modalContent.addEventListener('touchstart', stopProp, { passive: false });
        this.modalContent.addEventListener('touchmove', stopProp, { passive: false });
        this.modalContent.addEventListener('wheel', stopProp, { passive: false });
        this.stopPreviewBtn.addEventListener('mousedown', stopProp);
        this.stopPreviewBtn.addEventListener('touchstart', stopProp, { passive: false });

        // Привязки UI
        document.getElementById('close-video-modal').onclick = () => this.modal.style.display = 'none';
        
        const presetSelect = document.getElementById('vid-preset');
        const speedGroup = document.getElementById('vid-speed-group');
        const wobbleGroup = document.getElementById('vid-wobble-group');

        presetSelect.onchange = (e) => {
            speedGroup.style.display = e.target.value !== 'static' ? 'block' : 'none';
            wobbleGroup.style.display = e.target.value === 'fly' ? 'block' : 'none';
        };

        const durInput = document.getElementById('vid-duration');
        const durVal = document.getElementById('vid-dur-val');
        durInput.oninput = () => durVal.innerText = durInput.value;

        document.getElementById('vid-start-btn').onclick = () => this.startRecording();
        document.getElementById('vid-preview-btn').onclick = () => this.startPreview();
        this.stopPreviewBtn.onclick = () => this.stopPreview();
    }

    open() {
        if (this.isRecording || this.isPreviewing) return;
        this.modal.style.display = 'flex';
        // Сохраняем начальную позицию при открытии модалки
        this.basePos.copy(this.camera.position);
        this.baseQuat.copy(this.camera.quaternion);
    }

    // ==========================================
    // ЛОГИКА ПРЕДПРОСМОТРА
    // ==========================================
    startPreview() {
        if (this.isRecording || this.isPreviewing) return;
        this.isPreviewing = true;

        // Читаем настройки
        const duration = parseInt(document.getElementById('vid-duration').value);
        const preset = document.getElementById('vid-preset').value;
        const speed = parseFloat(document.getElementById('vid-speed').value);
        const wobble = parseFloat(document.getElementById('vid-wobble').value);
        const followTerrain = document.getElementById('vid-follow-terrain').checked;
        const shakeX = parseFloat(document.getElementById('vid-shake-x').value);
        const shakeY = parseFloat(document.getElementById('vid-shake-y').value);
        const shakeZ = parseFloat(document.getElementById('vid-shake-z').value);
        const shakeSpeed = parseFloat(document.getElementById('vid-shake-speed').value);

        // Прячем окно настроек, делаем фон прозрачным, показываем кнопку СТОП
        this.modalContent.style.display = 'none';
        this.modal.style.background = 'transparent';
        this.modal.style.backdropFilter = 'none';
        this.stopPreviewBtn.style.display = 'block';
        
        // Меняем текст кнопки, чтобы показывать обратный отсчет
        this.stopPreviewBtn.innerText = `⏹ ОСТАНОВИТЬ ПРЕДПРОСМОТР (${duration}s)`;

        // Паузим основной цикл (передаем управление этому классу)
        window.dispatchEvent(new CustomEvent('toggle-pause', { detail: true }));

        this.virtualTime = this.globalUniforms.uTime.value || 0;
        let startTime = performance.now();

        const previewLoop = (timestamp) => {
            if (!this.isPreviewing) return;

            const elapsedSec = (timestamp - startTime) / 1000;
            const remainingSec = Math.ceil(duration - elapsedSec);
            
            // Обновляем таймер на кнопке
            this.stopPreviewBtn.innerText = `⏹ ОСТАНОВИТЬ ПРЕДПРОСМОТР (${remainingSec}s)`;

            if (elapsedSec >= duration) {
                this.stopPreview();
                return;
            }

            // Двигаем камеру
            this.updateCamera(preset, speed, wobble, shakeX, shakeY, shakeZ, shakeSpeed, elapsedSec, followTerrain);

            // Рендерим кадр (используем реальный dt для плавности предпросмотра)
            window.dispatchEvent(new CustomEvent('render-offline-frame', { 
                detail: { time: this.virtualTime + elapsedSec, dt: 1/60 } 
            }));

            this.previewRafId = requestAnimationFrame(previewLoop);
        };

        this.previewRafId = requestAnimationFrame(previewLoop);
    }

    stopPreview() {
        if (!this.isPreviewing) return;
        this.isPreviewing = false;
        
        if (this.previewRafId) {
            cancelAnimationFrame(this.previewRafId);
            this.previewRafId = null;
        }

        // Возвращаем камеру на место
        this.camera.position.copy(this.basePos);
        this.camera.quaternion.copy(this.baseQuat);
        
        // Делаем один рендер, чтобы картинка обновилась
        window.dispatchEvent(new CustomEvent('render-offline-frame', { 
            detail: { time: this.virtualTime, dt: 0 } 
        }));

        // Восстанавливаем UI
        this.modalContent.style.display = 'block';
        this.modal.style.background = 'rgba(0,0,0,0.85)';
        this.modal.style.backdropFilter = 'blur(10px)';
        this.stopPreviewBtn.style.display = 'none';

        // Снимаем паузу с основного цикла (игра продолжается)
        window.dispatchEvent(new CustomEvent('toggle-pause', { detail: false }));
    }

    // ==========================================
    // ЛОГИКА ЗАПИСИ ВИДЕО
    // ==========================================
    async startRecording() {
        if (this.isPreviewing) this.stopPreview();
        this.isRecording = true;
        
        // Чтение настроек
        const scale = parseFloat(document.getElementById('vid-scale').value);
        const fps = parseInt(document.getElementById('vid-fps').value);
        const duration = parseInt(document.getElementById('vid-duration').value);
        const preset = document.getElementById('vid-preset').value;
        const speed = parseFloat(document.getElementById('vid-speed').value);
        const wobble = parseFloat(document.getElementById('vid-wobble').value);
        const followTerrain = document.getElementById('vid-follow-terrain').checked; // <--- НОВОЕ
        
        const shakeX = parseFloat(document.getElementById('vid-shake-x').value);
        const shakeY = parseFloat(document.getElementById('vid-shake-y').value);
        const shakeZ = parseFloat(document.getElementById('vid-shake-z').value);
        const shakeSpeed = parseFloat(document.getElementById('vid-shake-speed').value);

        // UI
        const actionsGroup = document.getElementById('vid-actions-group');
        const progressCont = document.getElementById('vid-progress-container');
        const progressBar = document.getElementById('vid-progress-bar');
        const statusText = document.getElementById('vid-status');
        
        actionsGroup.style.display = 'none';
        progressCont.style.display = 'block';

        // Настройка рендера (Разрешение)
        const originalPixelRatio = this.renderer.getPixelRatio();
        this.renderer.setPixelRatio(scale);
        if(window.updateParticleScales) window.updateParticleScales();

        // Подготовка потока
        const canvas = this.renderer.domElement;
        const stream = canvas.captureStream(0); // 0 = ручное управление кадрами
        const track = stream.getVideoTracks()[0];
        
        const options = { 
            mimeType: 'video/webm;codecs=vp9',
            videoBitsPerSecond: 10000000 // 10 Mbps
        };
        
        let recorder;
        try {
            recorder = new MediaRecorder(stream, options);
        } catch (e) {
            recorder = new MediaRecorder(stream); // Фолбэк
        }

        const chunks = [];
        recorder.ondataavailable = e => { if (e.data.size > 0) chunks.push(e.data); };

        // Сохраняем реальное время, переходим в виртуальное
        this.virtualTime = this.globalUniforms.uTime.value || 0;
        const dt = 1.0 / fps;
        const totalFrames = duration * fps;

        // ПАУЗА ОСНОВНОГО ЦИКЛА
        window.dispatchEvent(new CustomEvent('toggle-pause', { detail: true }));

        recorder.start();

        // СИНХРОННЫЙ РЕНДЕР ЧЕРЕЗ requestAnimationFrame
        for (let frame = 0; frame <= totalFrames; frame++) {
            
            await new Promise(resolve => {
                requestAnimationFrame(() => {
                    this.virtualTime += dt;
                    
                    // Расчет позиции камеры
                    this.updateCamera(preset, speed, wobble, shakeX, shakeY, shakeZ, shakeSpeed, frame * dt, followTerrain);

                    // Вызов внешней функции для рендера
                    window.dispatchEvent(new CustomEvent('render-offline-frame', { detail: { time: this.virtualTime, dt: dt } }));

                    // Принудительно забираем готовый кадр в видео
                    track.requestFrame();
                    resolve();
                });
            });

            // Обновляем UI каждые несколько кадров
            if (frame % 3 === 0) {
                const percent = Math.round((frame / totalFrames) * 100);
                progressBar.style.width = percent + '%';
                statusText.innerText = `Рендеринг: ${percent}% (Кадр ${frame}/${totalFrames})`;
            }
        }

        statusText.innerText = "Кодирование файла... Пожалуйста, подождите.";
        
        // Даем MediaRecorder время дожевать кадры
        await new Promise(r => setTimeout(r, 600));

        // Остановка
        recorder.stop();
        
        recorder.onstop = () => {
            const blob = new Blob(chunks, { type: 'video/webm' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            const date = new Date().toISOString().replace(/:/g, '-').slice(0, 19);
            a.download = `Anemone_Video_${date}.webm`;
            document.body.appendChild(a);
            a.click();
            URL.revokeObjectURL(url);

            // Возврат состояния
            this.renderer.setPixelRatio(originalPixelRatio);
            if(window.updateParticleScales) window.updateParticleScales();
            
            this.camera.position.copy(this.basePos);
            this.camera.quaternion.copy(this.baseQuat);
            
            actionsGroup.style.display = 'flex';
            progressCont.style.display = 'none';
            this.isRecording = false;
            
            // Снимаем паузу с основного цикла
            window.dispatchEvent(new CustomEvent('toggle-pause', { detail: false }));
        };
    }

    updateCamera(preset, speed, wobble, sX, sY, sZ, sSpeed, localTime, followTerrain) {
        // Сброс в базовую позицию
        this.camera.position.copy(this.basePos);
        this.camera.quaternion.copy(this.baseQuat);

        const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(this.baseQuat);
        const right = new THREE.Vector3(1, 0, 0).applyQuaternion(this.baseQuat);
        const up = new THREE.Vector3(0, 1, 0).applyQuaternion(this.baseQuat);

        // 1. Основное движение (Пресеты)
        if (preset === 'pan') {
            const angle = localTime * speed * 0.5;
            const panQuat = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), angle);
            this.camera.quaternion.premultiply(panQuat);
        } 
        else if (preset === 'fly') {
            const dist = localTime * speed * 50.0;
            
            let wobbleY = 0; // Вертикальная тряска
            if (wobble > 0.001) {
                const wX = Math.sin(localTime * 2.1) * wobble * 2.0;
                wobbleY = Math.cos(localTime * 1.7) * wobble * 2.0;
                this.camera.position.addScaledVector(right, wX); // Боковая тряска
            }

            // --- ОБНОВЛЕННАЯ ЛОГИКА ОГИБАНИЯ РЕЛЬЕФА ---
            // Проверяем, есть ли у нас сохраненная функция
            if (followTerrain && typeof this.getTerrainHeight === 'function') {
                
                // Вычисляем строго горизонтальный вектор полета (чтобы не втыкаться в землю)
                const forwardXZ = new THREE.Vector3(forward.x, 0, forward.z).normalize();
                
                // Защита: если камера смотрит строго вниз (90 градусов), 
                // вектор forwardXZ будет нулевым. В этом случае используем "верх" камеры.
                if (forwardXZ.lengthSq() < 0.001) {
                    forwardXZ.set(up.x, 0, up.z).normalize();
                }

                // Летим вперед над землей
                this.camera.position.addScaledVector(forwardXZ, dist);

                // Вычисляем высоты
                const startTerrainY = this.getTerrainHeight(this.basePos.x, this.basePos.z);
                const altitude = this.basePos.y - startTerrainY; // Исходная высота над землей
                const currentTerrainY = this.getTerrainHeight(this.camera.position.x, this.camera.position.z);
                
                // Применяем высоту земли + изначальную высоту + тряску
                this.camera.position.y = currentTerrainY + altitude + wobbleY;
            } else {
                // Стандартное поведение (свободный полет куда смотрим)
                this.camera.position.addScaledVector(forward, dist);
                if (wobble > 0.001) {
                    this.camera.position.addScaledVector(up, wobbleY);
                }
            }
        }

        // 2. Случайные повороты (Дрожание камеры)
        if (sX > 0 || sY > 0 || sZ > 0) {
            const euler = new THREE.Euler(0, 0, 0, 'YXZ');
            euler.x = Math.sin(localTime * sSpeed * 1.1) * sX; 
            euler.y = Math.cos(localTime * sSpeed * 0.9) * sY; 
            euler.z = Math.sin(localTime * sSpeed * 1.3) * sZ; 
            
            const shakeQuat = new THREE.Quaternion().setFromEuler(euler);
            this.camera.quaternion.multiply(shakeQuat);
        }
    }
}