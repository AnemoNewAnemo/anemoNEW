import * as THREE from 'three';

// Хелпер для создания текстовых лейблов
export function createTextSprite(text, size, color) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const fontSize = 48; // Рисуем крупно для четкости
    ctx.font = `bold ${fontSize}px sans-serif`;
    const metrics = ctx.measureText(text);
    
    canvas.width = Math.max(metrics.width + 20, 64);
    canvas.height = fontSize + 20;

    ctx.font = `bold ${fontSize}px sans-serif`;
    ctx.fillStyle = color;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, canvas.width / 2, canvas.height / 2);

    const tex = new THREE.CanvasTexture(canvas);
    tex.minFilter = THREE.LinearFilter;
    const spriteMat = new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false });
    const sprite = new THREE.Sprite(spriteMat);
    
    const aspect = canvas.width / canvas.height;
    sprite.scale.set(aspect * size, size, 1);
    return sprite;
}

// Класс для окна предпросмотра
export class SolarPreview {
    constructor() {
        this.canvas = document.getElementById('solar-preview-canvas');
        this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas, antialias: true, alpha: true });
        this.scene = new THREE.Scene();
        
        this.scene.add(new THREE.AmbientLight(0xffffff, 0.4));

        this.camera = new THREE.PerspectiveCamera(45, this.canvas.clientWidth / this.canvas.clientHeight, 1, 10000);
        this.camera.position.set(0, 1500, 2500); 
        this.camera.lookAt(0, 0, 0);
        
        this.active = false;
        this.systemGroup = new THREE.Group();
        this.scene.add(this.systemGroup);
        this.time = 0;
        this.planets = [];

        // --- Управление камерой превью (Pan и Zoom) ---
        this.isDragging = false;
        this.previousMousePosition = { x: 0, y: 0 };
        
        // Зум (колесико мыши)
        this.canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            this.camera.position.z += e.deltaY * 2.0;
            this.camera.position.z = Math.max(500, Math.min(this.camera.position.z, 8000)); // Ограничения зума
        }, { passive: false });

        // Панорамирование (мышь)
        this.canvas.addEventListener('mousedown', (e) => {
            if (e.button === 2 || e.button === 0) { // Правая или левая кнопка
                this.isDragging = true;
                this.previousMousePosition = { x: e.offsetX, y: e.offsetY };
            }
        });
        
        this.canvas.addEventListener('mousemove', (e) => {
            if (this.isDragging) {
                const deltaX = e.offsetX - this.previousMousePosition.x;
                const deltaY = e.offsetY - this.previousMousePosition.y;
                
                this.camera.position.x -= deltaX * 3.0;
                this.camera.position.y += deltaY * 3.0; // Инверсия для естественного движения
                
                this.previousMousePosition = { x: e.offsetX, y: e.offsetY };
            }
        });
        
        window.addEventListener('mouseup', () => { this.isDragging = false; });
        this.canvas.addEventListener('contextmenu', e => e.preventDefault());

        // Тач-события (мобильные телефоны - свайп и щипок)
        this.initialPinchDist = 0;
        this.canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            if (e.touches.length === 1) {
                this.isDragging = true;
                this.previousMousePosition = { x: e.touches[0].clientX, y: e.touches[0].clientY };
            } else if (e.touches.length === 2) {
                this.initialPinchDist = Math.hypot(
                    e.touches[0].clientX - e.touches[1].clientX,
                    e.touches[0].clientY - e.touches[1].clientY
                );
            }
        }, { passive: false });
        
        this.canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            if (e.touches.length === 1 && this.isDragging) {
                const deltaX = e.touches[0].clientX - this.previousMousePosition.x;
                const deltaY = e.touches[0].clientY - this.previousMousePosition.y;
                this.camera.position.x -= deltaX * 3.0;
                this.camera.position.y += deltaY * 3.0;
                this.previousMousePosition = { x: e.touches[0].clientX, y: e.touches[0].clientY };
            } else if (e.touches.length === 2) {
                const dist = Math.hypot(
                    e.touches[0].clientX - e.touches[1].clientX,
                    e.touches[0].clientY - e.touches[1].clientY
                );
                const delta = this.initialPinchDist - dist;
                this.camera.position.z += delta * 5.0;
                this.camera.position.z = Math.max(500, Math.min(this.camera.position.z, 8000));
                this.initialPinchDist = dist;
            }
        }, { passive: false });
        
        this.canvas.addEventListener('touchend', () => { this.isDragging = false; });
    }

    start() {
        this.active = true;
        const animate = () => {
            if (!this.active) return;
            requestAnimationFrame(animate);
            this.time += 0.016; 
            
            this.planets.forEach(p => {
                p.mesh.position.x = Math.cos(this.time * p.speed) * p.orbit;
                p.mesh.position.z = Math.sin(this.time * p.speed) * p.orbit;
                p.mesh.rotation.y += p.speed * 2.0;
                
                if (p.label) {
                    p.label.position.copy(p.mesh.position);
                    p.label.position.y += p.size + (p.labelSize / 2) + 5;
                }
            });
            this.renderer.render(this.scene, this.camera);
        };
        animate();
    }

    stop() { this.active = false; }

    resize() {
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.renderer.setSize(rect.width, rect.height, false);
        this.camera.aspect = rect.width / rect.height;
        this.camera.updateProjectionMatrix();
    }

    updateData(sysData, managerInstance) {
        while(this.systemGroup.children.length > 0) {
            this.systemGroup.remove(this.systemGroup.children[0]);
        }
        this.planets = [];
        managerInstance.buildSystemLogic(sysData, this.systemGroup, this.planets, true);
    }
}

export class SolarSystemManager {
    constructor(scene, camera) {
        this.scene = scene;
        this.camera = camera;
        this.systems = new Map();
        this.channelId = new URLSearchParams(window.location.search).get('channel_id') || 'default_world';
        
        this.orbitMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.15 });

        this.starMat = new THREE.ShaderMaterial({
            uniforms: {
                uColor: { value: new THREE.Color() },
                uFadeStart: { value: 2400.0 },
                uFadeEnd: { value: 1000.0 }
            },
            vertexShader: `
                varying vec3 vNormal; varying vec3 vViewDir; varying float vDist;
                void main() {
                    vNormal = normalize(normalMatrix * normal);
                    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
                    vViewDir = normalize(-mvPosition.xyz);
                    gl_Position = projectionMatrix * mvPosition;
                    vDist = length(mvPosition.xyz); 
                }
            `,
            fragmentShader: `
                uniform vec3 uColor; uniform float uFadeStart; uniform float uFadeEnd;
                varying vec3 vNormal; varying vec3 vViewDir; varying float vDist;
                void main() {
                    float viewDot = clamp(dot(vNormal, vViewDir), 0.0, 1.0);
                    vec3 finalColor = mix(uColor, vec3(1.0), pow(viewDot, 0.8) * 0.8) * 1.5;
                    
                    // ИСПРАВЛЕНИЕ: WebGL падает, если первый аргумент smoothstep больше второго.
                    // Меняем их местами и инвертируем результат
                    float distAlpha = 1.0 - smoothstep(uFadeEnd, uFadeStart, vDist);
                    
                    gl_FragColor = vec4(finalColor, smoothstep(0.0, 0.4, viewDot) * distAlpha);
                }
            `,
            transparent: true, blending: THREE.AdditiveBlending, depthWrite: false
        });

        this.haloMat = new THREE.SpriteMaterial({
            map: new THREE.CanvasTexture((() => {
                const c = document.createElement('canvas'); c.width = c.height = 128;
                const ctx = c.getContext('2d');
                const grad = ctx.createRadialGradient(64,64,0, 64,64,64);
                grad.addColorStop(0.0, 'rgba(255, 255, 255, 1.0)');
                grad.addColorStop(0.2, 'rgba(255, 255, 255, 0.8)');
                grad.addColorStop(0.4, 'rgba(255, 255, 255, 0.3)');
                grad.addColorStop(1.0, 'rgba(255, 255, 255, 0.0)');
                ctx.fillStyle = grad; ctx.fillRect(0,0,128,128); return c;
            })()),
            blending: THREE.AdditiveBlending, depthWrite: false, transparent: true
        });

        this.ambientLight = new THREE.AmbientLight(0xffffff, 0.05);
        this.scene.add(this.ambientLight);
        
        this.load();
    }

    async load() {
        try {
            const res = await fetch(`/api/solar/get?channel_id=${this.channelId}`);
            const data = await res.json();
            data.forEach(sys => this.buildSystem(sys));
        } catch (e) { console.error("Error loading solar systems", e); }
    }

    // Вспомогательная логика сборки (чтобы использовать и для мира, и для превью)
    buildSystemLogic(sysData, parentGroup, planetsArray, isPreview = false) {
        // Безопасные дефолтные значения
        const starBrightness = parseFloat(sysData.star.brightness || sysData.star.bright) || 1.0;
        const labelsConf = sysData.labels || { show: false, size: 30, color: '#ffffff' };
        const glowColor = sysData.star.glowColor || sysData.star.color;

        // 1. Создаем Звезду
        const starColor = new THREE.Color(sysData.star.color);
        const sMat = this.starMat.clone();
        sMat.uniforms.uColor.value = starColor;
        
        const starMesh = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 32), sMat);
        starMesh.scale.setScalar(sysData.star.size);
        if (!isPreview) starMesh.userData = { isStar: true, systemId: sysData.id, name: sysData.name };
        parentGroup.add(starMesh);

        // Ореол
        const halo = new THREE.Sprite(this.haloMat.clone());
        halo.material.color = new THREE.Color(glowColor); // Цвет ореола
        halo.scale.setScalar(sysData.star.size * 4.0 * starBrightness);
        parentGroup.add(halo);

        // Источник света
        const light = new THREE.PointLight(starColor, starBrightness * 2.0, 5000);
        parentGroup.add(light);

        // Текст Звезды
        if (labelsConf.show && sysData.name) {
            const starLabel = createTextSprite(sysData.name, labelsConf.size * 1.5, labelsConf.color);
            starLabel.position.y = parseFloat(sysData.star.size) + (labelsConf.size) + 10;
            parentGroup.add(starLabel);
        }

        // 2. Создаем Планеты и Орбиты
        (sysData.planets || []).forEach(pData => {
            const orbitSize = parseFloat(pData.orbit);
            const pSize = parseFloat(pData.size);

            // Орбита
            if (sysData.showOrbits) {
                const orbitGeo = new THREE.BufferGeometry().setFromPoints(
                    new THREE.Path().absarc(0, 0, orbitSize, 0, Math.PI * 2).getPoints(64)
                );
                const orbitLine = new THREE.LineLoop(orbitGeo, this.orbitMat);
                orbitLine.rotation.x = Math.PI / 2; 
                parentGroup.add(orbitLine);
            }

            // Планета
            const pColor = new THREE.Color(pData.color);
            const pMat = new THREE.MeshStandardMaterial({
                color: pColor,
                roughness: 0.8,
                emissive: pColor,
                emissiveIntensity: parseFloat(pData.glow) || 0.0
            });
            const pMesh = new THREE.Mesh(new THREE.SphereGeometry(pSize, 32, 32), pMat);
            parentGroup.add(pMesh);

            // Текст Планеты
            let pLabel = null;
            if (labelsConf.show && pData.name) {
                pLabel = createTextSprite(pData.name, labelsConf.size, labelsConf.color);
                parentGroup.add(pLabel);
            }

            planetsArray.push({ 
                mesh: pMesh, 
                orbit: orbitSize, 
                speed: parseFloat(pData.speed),
                label: pLabel,
                size: pSize,
                labelSize: parseFloat(labelsConf.size)
            });
        });

        return starMesh;
    }

    buildSystem(sysData) {
        if (this.systems.has(sysData.id)) {
            const old = this.systems.get(sysData.id);
            this.scene.remove(old.group);
        }

        const group = new THREE.Group();
        group.position.set(sysData.pos.x, sysData.pos.y, sysData.pos.z);
        const planetsData = [];

        const starMesh = this.buildSystemLogic(sysData, group, planetsData, false);

        this.scene.add(group);
        this.systems.set(sysData.id, { data: sysData, group, starMesh, planets: planetsData });
    }

    update(time) {
        this.systems.forEach(sys => {
            sys.planets.forEach(p => {
                p.mesh.position.x = Math.cos(time * p.speed) * p.orbit;
                p.mesh.position.z = Math.sin(time * p.speed) * p.orbit;
                p.mesh.rotation.y += p.speed * 2.0;
                
                // Обновляем позицию текста, если он есть
                if (p.label) {
                    p.label.position.copy(p.mesh.position);
                    p.label.position.y += p.size + (p.labelSize / 2) + 5;
                }
            });
        });
    }

    getClickableStars() {
        return Array.from(this.systems.values()).map(s => s.starMesh);
    }

    getVisibleSystems(frustum) {
        const visible = [];
        this.systems.forEach(sys => {
            if (frustum.intersectsObject(sys.starMesh)) {
                visible.push({ id: sys.data.id, name: sys.data.name });
            }
        });
        return visible;
    }

    async saveSystem(id, data) {
        const isNew = !id;
        const url = isNew ? '/api/solar/create' : '/api/solar/update';
        const payload = isNew ? { channel_id: this.channelId, system_data: data } 
                              : { channel_id: this.channelId, system_id: id, system_data: data };
        
        const res = await fetch(url, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const respData = await res.json();
        
        if (respData.status === 'success') {
            const finalId = isNew ? respData.data.id : id;
            data.id = finalId;
            this.buildSystem(data);
            return finalId;
        }
        return null;
    }

    async deleteSystem(id) {
        await fetch(`/api/solar/delete?channel_id=${this.channelId}&system_id=${id}`, { method: 'DELETE' });
        const sys = this.systems.get(id);
        if (sys) this.scene.remove(sys.group);
        this.systems.delete(id);
    }
}