import * as THREE from 'three';

// --- КОНФИГУРАЦИЯ И СОСТОЯНИЕ (Глобальные настройки) ---
const CONFIG = {
    colors: {
        bottom: new THREE.Color('#2b1a38'), 
        mid: new THREE.Color('#203a4c'),    
        top: new THREE.Color('#050814'),    
        firefly: new THREE.Color('#ffaa00') 
    },
    wind: {
        speed: 0.8,
        force: 0.3
    },
    particles: {
        speed: 0.5
    },
    // НОВЫЙ БЛОК: Настройки движения карточек
    motion: {
        swayAmp: 0.1,  // Амплитуда раскачивания (влево-вправо)
        twistAmp: 0.15 // Амплитуда вращения (вокруг оси)
    }
};

const CHUNK_SIZE = 1500;
const RENDER_DISTANCE = 1;
const FADE_DISTANCE = 1600;
const MAX_CONCURRENT_LOADS = 2; 
const MAX_TEXTURE_SIZE = 512;
// --- SHADERS (Шейдеры) ---


// 2. ШЕЙДЕР БУМАГИ (Ветер + Полароид)
const paperVertexShader = `
    uniform float uTime;
    uniform float uWindSpeed;
    uniform float uWindForce;
    
    uniform float uPhase;
    uniform float uSwaySpeed;
    
    // Новые параметры амплитуды
    uniform float uSwayAmp;  
    uniform float uTwistAmp; 

    uniform vec2 uImageScale; 

    varying vec2 vUv;
    varying float vDist;

    void main() {
        vUv = uv;
        vec3 pos = position; 
        
        pos.xy *= uImageScale;

        // 1. ФИЗИКА МАЯТНИКА (ВЛЕВО-ВПРАВО)
        // Используем uSwayAmp вместо хардкода
        float swing = sin(uTime * uSwaySpeed + uPhase) * (uSwayAmp + uWindForce * 0.2);
        float flutter = sin(uTime * 3.0 + uPhase * 2.0) * 0.02 * uWindForce;
        float totalAngle = swing + flutter;

        float c = cos(totalAngle);
        float s = sin(totalAngle);

        float rX = pos.x * c - pos.y * s;
        float rY = pos.x * s + pos.y * c;
        
        pos.x = rX;
        pos.y = rY;
        
        // 2. ПОВОРОТ ВОКРУГ ОСИ Y (TWIST/ВГЛУБЬ)
        // Используем uTwistAmp
        float twistAngle = sin(uTime * 0.5 + uPhase) * uTwistAmp;
        float cT = cos(twistAngle);
        float sT = sin(twistAngle);

        float finalX = pos.x * cT - pos.z * sT;
        float finalZ = pos.x * sT + pos.z * cT;

        pos.x = finalX;
        pos.z = finalZ;

        vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
        gl_Position = projectionMatrix * mvPosition;
        vDist = -mvPosition.z; 
    }
`;

const paperFragmentShader = `
    uniform sampler2D map;
    uniform vec3 uColor;
    uniform bool hasTexture;
    uniform float uTime; 
    
    varying vec2 vUv;
    varying float vDist;

    void main() {
        // --- 1. ЛОГИКА ЗАТЕМНЕНИЯ (СВЕТ/ТЕНЬ) ---
        float shadowStart = 800.0;
        float shadowEnd = 1600.0;
        float lightFactor = 1.0 - smoothstep(shadowStart, shadowEnd, vDist);
        float brightness = 0.15 + (0.85 * lightFactor);

        // --- 2. ЛОГИКА ПРОЗРАЧНОСТИ ---
        float opacityStart = 1500.0; 
        float opacityEnd = 2200.0;   
        float opacity = 1.0 - smoothstep(opacityStart, opacityEnd, vDist);
        if (opacity <= 0.01) discard; 

        vec3 rgbColor;

        // --- 3. ПОЛУЧЕНИЕ ЦВЕТА ---
        if (hasTexture) {
            // Текстура уже содержит фото, рамку и текст, просто отображаем её
            rgbColor = texture2D(map, vUv).rgb;
        } else {
            // Заглушка пока грузится
            vec3 loadingBg = vec3(0.05, 0.09, 0.18); 
            float distToCenter = distance(vUv, vec2(0.5));
            float pulse = 0.5 + 0.5 * sin(uTime * 8.0); 
            float dotRadius = 0.015 + 0.01 * pulse; 
            float dot = 1.0 - smoothstep(dotRadius, dotRadius + 0.01, distToCenter);
            rgbColor = mix(loadingBg, vec3(1.0), dot);
        }

        // --- 4. ПРИМЕНЕНИЕ ЗАТЕМНЕНИЯ ---
        vec3 finalRgb = rgbColor * brightness;
        gl_FragColor = vec4(finalRgb, opacity);
    }
`;
// --- SCENE SETUP ---
const container = document.getElementById('canvas-container');
const scene = new THREE.Scene();
// ФОГ (Туман) настраиваем под цвета неба, чтобы горизонт растворялся
scene.fog = new THREE.FogExp2(CONFIG.colors.bottom, 0.0015);

const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 10, 8000);
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
// ВАЖНО: Исправляет цветопередачу текстур

container.appendChild(renderer.domElement);


// --- ЧАСТИЦЫ (Пыль и Светлячки) ---
const particleCount = 2000;
const wrapSize = 4000; // Размер области вокруг камеры
const fireflyCount = 400; 

const particleGroup = new THREE.Group();
scene.add(particleGroup);

// Пыль (Белые)
// --- ЧАСТИЦЫ (БЕСКОНЕЧНОЕ ПОЛЕ) ---
// Общий шейдер для частиц, которые всегда вокруг камеры
const infiniteParticleVertex = `
uniform float uTime;
uniform vec3 uCamPos;
uniform float uSize;
uniform float uScale;

// Новые uniform-ы для физики
uniform float uWindSpeed;
uniform float uWindForce;
uniform float uPartSpeed;

attribute float size;
varying float vAlpha;

void main() {
    vec3 pos = position;
    
    // 1. ВЕТЕР: Сдвигаем все поле частиц по X (и немного Y) со временем
    float windOffset = uTime * uWindSpeed * 50.0; // 50.0 - множитель скорости
    float vertOffset = uTime * uPartSpeed * 10.0; // Медленное падение/подъем
    
    // Применяем смещение к "мировым" координатам до зацикливания
    vec3 animatedPos = pos;
    animatedPos.x += windOffset; 
    animatedPos.y -= vertOffset; 

    // 2. ТУРБУЛЕНТНОСТЬ (Wobble): 
    // Зависит от uWindForce и uPartSpeed. Чем выше скорость, тем быстрее дрожание.
    float wobbleFreq = uTime * uPartSpeed;
    float wobbleAmp = uWindForce * 200.0; 
    
    animatedPos.x += sin(wobbleFreq + pos.y * 0.01) * wobbleAmp;
    animatedPos.y += cos(wobbleFreq + pos.x * 0.01) * wobbleAmp * 0.5;

    // 3. БЕСКОНЕЧНОЕ ЗАЦИКЛИВАНИЕ:
    // Теперь mod применяется к уже смещенным координатам
    vec3 localPos = mod(animatedPos - uCamPos + uSize * 0.5, uSize) - uSize * 0.5;
    vec3 finalPos = uCamPos + localPos;

    vec4 mvPosition = modelViewMatrix * vec4(finalPos, 1.0);
    gl_Position = projectionMatrix * mvPosition;
    
    gl_PointSize = (size * uScale) / -mvPosition.z;
    
    float dist = length(localPos);
    vAlpha = 1.0 - smoothstep(uSize * 0.35, uSize * 0.5, dist);
}
`;


const fireflyGeo = new THREE.BufferGeometry();
const fireflyPos = [];
const fireflyPhase = [];
const fireflySize = [];
const fireflyType = []; // 1.0 = Основной светлячок, 0.0 = Мелкая искра

for (let i = 0; i < fireflyCount; i++) {
    fireflyPos.push(
        (Math.random() - 0.5) * wrapSize,
        (Math.random() - 0.5) * wrapSize, 
        (Math.random() - 0.5) * wrapSize
    );
    fireflyPhase.push(Math.random() * Math.PI * 2);
    
    // 30% частиц - это крупные светлячки, остальные - мелкие искры вокруг
    const isBody = Math.random() > 0.7; 
    fireflyType.push(isBody ? 1.0 : 0.0);
    
    // Светлячки большие, искры крошечные
    fireflySize.push(isBody ? (15.0 + Math.random() * 10.0) : (3.0 + Math.random() * 4.0));
}

fireflyGeo.setAttribute('position', new THREE.Float32BufferAttribute(fireflyPos, 3));
fireflyGeo.setAttribute('phase', new THREE.Float32BufferAttribute(fireflyPhase, 1));
fireflyGeo.setAttribute('aSize', new THREE.Float32BufferAttribute(fireflySize, 1));
fireflyGeo.setAttribute('type', new THREE.Float32BufferAttribute(fireflyType, 1));

const fireflyMat = new THREE.ShaderMaterial({
    uniforms: {
        color: { value: CONFIG.colors.firefly },
        uTime: { value: 0 },
        scale: { value: window.innerHeight / 2.0 },
        uCamPos: { value: new THREE.Vector3() },
        uSize: { value: wrapSize },
        uWindSpeed: { value: CONFIG.wind.speed },
        uWindForce: { value: CONFIG.wind.force },
        uPartSpeed: { value: CONFIG.particles.speed }
    },
    vertexShader: `
        attribute float phase;
        attribute float aSize;
        attribute float type;
        
        varying float vAlpha;
        varying float vType; // Передаем тип в фрагментный шейдер
        
        uniform float uTime;
        uniform float scale;
        uniform vec3 uCamPos;
        uniform float uSize;
        uniform float uWindSpeed;
        uniform float uWindForce;
        uniform float uPartSpeed;

        void main() {
            vType = type;
            vec3 pos = position;

            // Движение
            float timeScale = (type > 0.5) ? 1.0 : 2.5; // Искры двигаются быстрее
            
            float windOffset = uTime * uWindSpeed * 60.0 * timeScale;
            float vertOffset = uTime * uPartSpeed * 15.0 * timeScale;
            
            vec3 animatedPos = pos;
            animatedPos.x += windOffset;
            animatedPos.y += vertOffset;

            // Хаотичное движение (Шум)
            // Искры (type 0) дрожат сильнее, имитируя разлет
            float wobbleSpeed = uTime * (0.5 + uPartSpeed) * timeScale;
            float wobbleAmp = (type > 0.5) ? 50.0 : 80.0; // Амплитуда
            
            animatedPos.x += sin(wobbleSpeed + phase) * (wobbleAmp + uWindForce * 100.0);
            animatedPos.y += cos(wobbleSpeed * 0.8 + phase) * (wobbleAmp + uWindForce * 100.0);
            animatedPos.z += sin(wobbleSpeed * 0.5 + phase) * (20.0 + uWindForce * 50.0);

            // Зацикливание пространства
            vec3 localPos = mod(animatedPos - uCamPos + uSize * 0.5, uSize) - uSize * 0.5;
            vec4 mvPosition = modelViewMatrix * vec4(uCamPos + localPos, 1.0);
            gl_Position = projectionMatrix * mvPosition;

            // Размер зависит от типа
            gl_PointSize = (aSize * scale) / -mvPosition.z;
            
            // Мерцание
            float blinkSpeed = (type > 0.5) ? 3.0 : 8.0; // Искры мерцают очень быстро
            float blink = sin(uTime * blinkSpeed + phase);
            
            // Базовая прозрачность
            float baseAlpha = (type > 0.5) ? (0.6 + 0.4 * blink) : (0.4 + 0.6 * blink);

            // Фейд у краев зоны видимости
            float dist = length(localPos);
            float fade = 1.0 - smoothstep(uSize * 0.4, uSize * 0.5, dist);
            
            vAlpha = baseAlpha * fade;
        }
    `,
    fragmentShader: `
        uniform vec3 color;
        varying float vAlpha;
        varying float vType;

        void main() {
            // Нормализованные координаты точки (от -0.5 до 0.5)
            vec2 coord = gl_PointCoord - vec2(0.5);
            float dist = length(coord);
            
            if(dist > 0.5) discard;

            vec4 finalColor;

            if (vType > 0.5) {
                // --- СТИЛЬ ОСНОВНОГО СВЕТЛЯЧКА (СФЕРА + СВЕЧЕНИЕ) ---
                
                // 1. Плотное белое ядро (Hot Core)
                float core = 1.0 - smoothstep(0.05, 0.25, dist);
                
                // 2. Внешнее мягкое свечение (Outer Glow)
                float glow = exp(-dist * 4.0); // Экспоненциальное затухание
                
                // Смешиваем: Ядро белое, Свечение цветное
                vec3 coreColor = mix(color, vec3(1.0, 1.0, 0.8), core * 0.8);
                
                // Итоговая яркость пикселя
                float strength = core + glow * 0.6;
                
                finalColor = vec4(coreColor, vAlpha * strength);

            } else {
                // --- СТИЛЬ ИСКРЫ (ТОЧКА + ШЛЕЙФ) ---
                // Просто острая точка, но яркая
                float spark = 1.0 - pow(dist * 2.0, 0.5);
                finalColor = vec4(color, vAlpha * spark);
            }

            gl_FragColor = finalColor;
        }
    `,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false
});

const fireflySystem = new THREE.Points(fireflyGeo, fireflyMat);
fireflySystem.frustumCulled = false;
scene.add(fireflySystem);



// 1. ПЫЛЬ
const dustGeo = new THREE.BufferGeometry();
const dustPos = [];
const dustSizes = [];
for (let i = 0; i < particleCount; i++) {
    // Просто случайные позиции в кубе
    dustPos.push(Math.random() * wrapSize, Math.random() * wrapSize, Math.random() * wrapSize);
    dustSizes.push(2.0 + Math.random() * 2.0);
}
dustGeo.setAttribute('position', new THREE.Float32BufferAttribute(dustPos, 3));
dustGeo.setAttribute('size', new THREE.Float32BufferAttribute(dustSizes, 1));

const dustMat = new THREE.ShaderMaterial({
    uniforms: {
        uColor: { value: new THREE.Color(0xffffff) },
        uCamPos: { value: new THREE.Vector3() },
        uSize: { value: wrapSize },
        uScale: { value: window.innerHeight / 2.0 },
        uTime: { value: 0 },
        // Добавляем привязку к слайдерам
        uWindSpeed: { value: 0 },
        uWindForce: { value: 0 },
        uPartSpeed: { value: 0 }
    },
    vertexShader: infiniteParticleVertex, // Используем обновленный шейдер
    fragmentShader: `
        uniform vec3 uColor;
        varying float vAlpha;
        void main() {
            vec2 coord = gl_PointCoord - vec2(0.5);
            if(length(coord) > 0.5) discard;
            gl_FragColor = vec4(uColor, vAlpha * 0.4); 
        }
    `,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending
});
const dustSystem = new THREE.Points(dustGeo, dustMat);
dustSystem.frustumCulled = false; // <--- ВАЖНО: Запрещаем Three.js прятать частицы при вылете из центра
scene.add(dustSystem);


// --- REALISTIC SKY SYSTEM (Звезды и Кометы) ---

// 1. Звездное поле (Разные цвета, мерцание)
const starCount = 15000; 
const starGeo = new THREE.BufferGeometry();
const starPos = [];
const starColors = [];
const starSizes = [];
const starFlashSpeed = [];

const starColorPalette = [
    new THREE.Color('#9db4ff'), // Голубоватый
    new THREE.Color('#ffddb4'), // Оранжеватый
    new THREE.Color('#ffffff'), // Белый
    new THREE.Color('#fcfcfc')  // Тусклый белый
];

for(let i=0; i<starCount; i++) {
    // Распределяем звезды по огромной сфере
    const r = 3000 + Math.random() * 2000; // Чуть расширили диапазон
    const theta = 2 * Math.PI * Math.random();
    const phi = Math.acos(2 * Math.random() - 1);
    
    const x = r * Math.sin(phi) * Math.cos(theta);
    const y = r * Math.sin(phi) * Math.sin(theta);
    const z = r * Math.cos(phi);
    
    starPos.push(x, y, z);
    
    const color = starColorPalette[Math.floor(Math.random() * starColorPalette.length)];
    starColors.push(color.r, color.g, color.b);
    
    // Увеличили минимальный размер с 0.5 до 1.5, чтобы их было видно
    starSizes.push(20 + Math.random() * 2.5); 
    starFlashSpeed.push(Math.random() * 3.0 + 0.2);
}

starGeo.setAttribute('position', new THREE.Float32BufferAttribute(starPos, 3));
starGeo.setAttribute('color', new THREE.Float32BufferAttribute(starColors, 3));
starGeo.setAttribute('size', new THREE.Float32BufferAttribute(starSizes, 1));
starGeo.setAttribute('speed', new THREE.Float32BufferAttribute(starFlashSpeed, 1));

const starMat = new THREE.ShaderMaterial({
    uniforms: {
        uTime: { value: 0 },
        uScale: { value: window.innerHeight }
    },
    vertexShader: `
        attribute float size;
        attribute float speed;
        attribute vec3 color;
        varying vec3 vColor;
        varying float vAlpha;
        uniform float uTime;
        uniform float uScale;
        void main() {
            vColor = color;
            vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
            gl_Position = projectionMatrix * mvPosition;
            
            // Мерцание
            float twinkle = sin(uTime * speed + position.x);
            vAlpha = 0.7 + 0.3 * twinkle; // Подняли базовую яркость
            
            gl_PointSize = size * (uScale / -mvPosition.z);
        }
    `,
    fragmentShader: `
        varying vec3 vColor;
        varying float vAlpha;
        void main() {
            vec2 coord = gl_PointCoord - vec2(0.5);
            float dist = length(coord);
            if(dist > 0.5) discard;
            
            // Более жесткое ядро, чтобы звезда читалась как точка, а не размытое пятно
            float strength = 1.0 - (dist * 2.0);
            strength = pow(strength, 1.5);
            
            gl_FragColor = vec4(vColor, vAlpha * strength);
        }
    `,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending
});

const starSystem = new THREE.Points(starGeo, starMat);
starSystem.renderOrder = -1; // Исправление: звезды рисуются первыми (фон)
scene.add(starSystem);

// 2. Система Комет (Падающие звезды)
class CometSystem {
    constructor(scene) {
        // Комета - это линия с градиентом прозрачности (голова яркая, хвост исчезает)
        const geometry = new THREE.BufferGeometry();
        // 2 точки: Голова и Хвост
        const positions = new Float32Array(6); 
        const colors = new Float32Array([
            1, 1, 1, 0.0, // Хвост (прозрачный)
            1, 1, 1, 1.0  // Голова (белая)
        ]);
        
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 4)); // r,g,b,a

        this.material = new THREE.LineBasicMaterial({
            vertexColors: true,
            transparent: true,
            blending: THREE.AdditiveBlending,
            opacity: 0
        });

        this.mesh = new THREE.Line(geometry, this.material);
        this.mesh.frustumCulled = false;
        scene.add(this.mesh);

        this.active = false;
        this.velocity = new THREE.Vector3();
        this.life = 0;
        this.maxLife = 0;
    }

    spawn(cameraPos) {
        if (this.active) return;

        // Позиция спавна: высоко и случайно вокруг камеры
        const offset = new THREE.Vector3(
            (Math.random() - 0.5) * 2000,
            800 + Math.random() * 500,
            (Math.random() - 0.5) * 1000 - 500
        );
        const startPos = new THREE.Vector3().copy(cameraPos).add(offset);
        
        // Направление: вниз и немного в сторону
        this.velocity.set(
            (Math.random() - 0.5) * 30, // X drift
            -(Math.random() * 20 + 30), // Y drop (быстро вниз)
            (Math.random() - 0.5) * 10  // Z drift
        );

        // Обновляем геометрию (ставим в начало)
        const posAttr = this.mesh.geometry.attributes.position;
        posAttr.setXYZ(0, startPos.x, startPos.y, startPos.z); // Tail
        posAttr.setXYZ(1, startPos.x, startPos.y, startPos.z); // Head
        posAttr.needsUpdate = true;

        this.life = 0;
        this.maxLife = 60 + Math.random() * 40; // Живет ~1-1.5 секунды (при 60fps)
        this.material.opacity = 1;
        this.active = true;
    }

    update(cameraPos) {
        // Шанс спавна, если не активна
        if (!this.active) {
            if (Math.random() < 0.003) { // 0.3% шанс каждый кадр
                this.spawn(cameraPos);
            }
            return;
        }

        this.life++;
        if (this.life > this.maxLife) {
            this.active = false;
            this.material.opacity = 0;
            return;
        }

        // Движение
        const posAttr = this.mesh.geometry.attributes.position;
        
        // Текущая голова
        const headX = posAttr.getX(1);
        const headY = posAttr.getY(1);
        const headZ = posAttr.getZ(1);

        // Новая позиция головы
        const newHeadX = headX + this.velocity.x;
        const newHeadY = headY + this.velocity.y;
        const newHeadZ = headZ + this.velocity.z;

        // Хвост следует за головой с задержкой (длина хвоста)
        // Просто берем старую позицию головы для хвоста, но умножаем вектор
        const tailLen = 15.0; // Длина хвоста
        const tailX = newHeadX - this.velocity.x * tailLen;
        const tailY = newHeadY - this.velocity.y * tailLen;
        const tailZ = newHeadZ - this.velocity.z * tailLen;

        posAttr.setXYZ(0, tailX, tailY, tailZ);
        posAttr.setXYZ(1, newHeadX, newHeadY, newHeadZ);
        posAttr.needsUpdate = true;

        // Плавное исчезновение в конце
        if (this.life > this.maxLife - 20) {
            this.material.opacity = (this.maxLife - this.life) / 20;
        }
    }
}

const comet = new CometSystem(scene);
// --- ЗАГРУЗКА ИЗОБРАЖЕНИЙ ---
const textureLoader = new THREE.TextureLoader();
textureLoader.setCrossOrigin('anonymous');
const PLACEHOLDER_TEXTURE = createPlaceholderTexture();

function createPlaceholderTexture() {
    const s = 64;
    const c = document.createElement('canvas');
    c.width = c.height = s;
    const ctx = c.getContext('2d');
    ctx.fillStyle = '#eee'; ctx.fillRect(0,0,s,s);
    ctx.fillStyle = '#ddd'; ctx.font='10px sans-serif'; ctx.textAlign='center'; ctx.fillText('...', s/2, s/2+3);
    return new THREE.CanvasTexture(c);
}

// --- ЛОГИКА ЧАНКОВ (Без изменений ядра, но обновлен рендер картин) ---
const state = {
    chunks: new Map(),
    targetPos: new THREE.Vector3(0, 0, 1000), 
    currentPos: new THREE.Vector3(0, 0, 1000), 
    isDragging: false,
    lastMouse: { x: 0, y: 0 },
    currentChunk: { x: null, y: null, z: null },
    loadQueue: [],
    activeLoads: 0
};

// ... Функция очереди загрузки осталась прежней (сокращена для краткости) ...
// 2. Обновленная функция обработки очереди с сортировкой
function processLoadQueue() {
    if (state.activeLoads >= MAX_CONCURRENT_LOADS || state.loadQueue.length === 0) return;

    // --- ЛОГИКА ПРИОРИТЕТОВ ---
    // Обновляем Frustum камеры для проверки видимости
    const frustum = new THREE.Frustum();
    const projScreenMatrix = new THREE.Matrix4();
    projScreenMatrix.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
    frustum.setFromProjectionMatrix(projScreenMatrix);

    const cameraDir = new THREE.Vector3();
    camera.getWorldDirection(cameraDir);

    // Сортируем очередь
    state.loadQueue.sort((a, b) => {
        const posA = new THREE.Vector3(a.pos[0], a.pos[1], a.pos[2]);
        const posB = new THREE.Vector3(b.pos[0], b.pos[1], b.pos[2]);

        // 1. Проверка на видимость в кадре (Frustum) - Самый высокий приоритет
        // Создаем маленькую сферу для проверки
        const isVisibleA = frustum.intersectsSphere(new THREE.Sphere(posA, 100));
        const isVisibleB = frustum.intersectsSphere(new THREE.Sphere(posB, 100));

        if (isVisibleA && !isVisibleB) return -1; // A важнее
        if (!isVisibleA && isVisibleB) return 1;  // B важнее

        // 2. Если оба видны или оба не видны -> Проверка: "Перед камерой" или "Сзади"
        const dirA = new THREE.Vector3().subVectors(posA, camera.position).normalize();
        const dirB = new THREE.Vector3().subVectors(posB, camera.position).normalize();
        
        const angleA = cameraDir.dot(dirA); // 1.0 = прямо по курсу, -1.0 = сзади
        const angleB = cameraDir.dot(dirB);

        // Если объект сильно спереди (> 0.5), даем ему буст
        if (angleA > 0.5 && angleB <= 0.5) return -1;
        if (angleB > 0.5 && angleA <= 0.5) return 1;

        // 3. Дистанция (Ближайшие важнее)
        const distA = posA.distanceTo(camera.position);
        const distB = posB.distanceTo(camera.position);

        return distA - distB; // Меньшая дистанция = выше в списке
    });
    // ---------------------------

    const task = state.loadQueue.shift();
    state.activeLoads++;

    // Получаем ID канала из URL
    const urlParams = new URLSearchParams(window.location.search);
    const customChannel = urlParams.get('channel_id');
    const channelParam = customChannel ? `&channel_id=${customChannel}` : '';

    fetch(`/api/anemone/resolve_image?post_id=${task.postId}${channelParam}`)
        .then(r => r.json())
        .then(data => {
            // ОБРАБОТКА ОШИБКИ ДОСТУПА
            if (data.error === 'access_denied') {
                const modal = document.getElementById('error-modal');
                const chanSpan = document.getElementById('err-channel');
                if(modal && chanSpan) {
                    chanSpan.innerText = customChannel;
                    modal.style.display = 'flex';
                }
                // Отменяем загрузку, но не ломаем очередь
                task.onError();
                state.activeLoads--;
                return; // Прерываем цепочку
            }

            if (data.found && data.url) {
                const loader = new THREE.ImageLoader();
                loader.setCrossOrigin('anonymous');
                loader.load(
                    data.url,
                    (image) => {
                        // --- ГЕНЕРАЦИЯ ПОЛАРОИДА С ТЕКСТОМ ---
                        const canvas = document.createElement('canvas');
                        const ctx = canvas.getContext('2d');

                        // Настройки размеров
                        const cardWidth = 512; // Фиксированная ширина карточки для четкости текста
                        const borderSide = cardWidth * 0.05; // 5% отступы сбоку
                        const borderTop = cardWidth * 0.05;  // 5% отступ сверху
                        const borderBottom = cardWidth * 0.25; // 25% снизу под текст
                        
                        // Вычисляем высоту картинки, сохраняя пропорции
                        const imgRatio = image.width / image.height;
                        const drawWidth = cardWidth - (borderSide * 2);
                        const drawHeight = drawWidth / imgRatio;

                        // Итоговая высота всей карточки
                        const cardHeight = borderTop + drawHeight + borderBottom;

                        canvas.width = cardWidth;
                        canvas.height = cardHeight;

                        // 1. Рисуем белую подложку
                        ctx.fillStyle = '#ffffff';
                        ctx.fillRect(0, 0, canvas.width, canvas.height);

                        // 2. Рисуем изображение
                        ctx.drawImage(image, borderSide, borderTop, drawWidth, drawHeight);

                        // 3. Рисуем Дату (серым, поменьше)
                        if (data.date) {
                            ctx.fillStyle = '#888888';
                            ctx.font = '500 14px "Helvetica Neue", Arial, sans-serif';
                            ctx.textAlign = 'left';
                            ctx.fillText(data.date, borderSide, borderTop + drawHeight + 30);
                        }

                        // 4. Рисуем Подпись (черным, с переносом строк)
                        if (data.caption) {
                            ctx.fillStyle = '#222222';
                            ctx.font = '400 16px "Helvetica Neue", Arial, sans-serif';
                            ctx.textAlign = 'left';
                            
                            const textX = borderSide;
                            let textY = borderTop + drawHeight + 55;
                            const maxWidth = cardWidth - (borderSide * 2);
                            const lineHeight = 20;

                            // Простой перенос слов
                            const words = data.caption.split(' ');
                            let line = '';
                            
                            // Ограничиваем количество строк, чтобы не вылезло (макс 3 строки)
                            let lineCount = 0;
                            const maxLines = 3;

                            for (let n = 0; n < words.length; n++) {
                                const testLine = line + words[n] + ' ';
                                const metrics = ctx.measureText(testLine);
                                const testWidth = metrics.width;
                                if (testWidth > maxWidth && n > 0) {
                                    ctx.fillText(line, textX, textY);
                                    line = words[n] + ' ';
                                    textY += lineHeight;
                                    lineCount++;
                                    if(lineCount >= maxLines) {
                                        line = line.trim() + '...'; // Многоточие
                                        break;
                                    }
                                } else {
                                    line = testLine;
                                }
                            }
                            if (lineCount < maxLines) {
                                ctx.fillText(line, textX, textY);
                            }
                        }

                        // Создаем текстуру
                        const tex = new THREE.CanvasTexture(canvas);
                        // Вычисляем новое соотношение сторон (карточка теперь выше из-за поля для текста)
                        const totalRatio = cardWidth / cardHeight;
                        
                        task.onSuccess(tex, totalRatio);
                        state.activeLoads--;
                        processLoadQueue();
                    },
                    undefined, 
                    () => { 
                        task.onError();
                        state.activeLoads--;
                        processLoadQueue();
                    }
                );
            } else {
                task.onError();
                state.activeLoads--;
                processLoadQueue();
            }
        })
        .catch(() => {
            task.onError();
            state.activeLoads--;
            processLoadQueue();
        });
}
// 1. Изменяем queueImageLoad, чтобы принимать позицию (pos)
function queueImageLoad(postId, pos, onSuccess, onError) {
    // Сохраняем позицию объекта для расчета приоритета
    state.loadQueue.push({ postId, pos, onSuccess, onError });
    processLoadQueue();
}



async function loadChunk(cx, cy, cz) {
    const key = `${cx},${cy},${cz}`;
    if (state.chunks.has(key)) return;
    const g = new THREE.Group();
    g.position.set(cx * CHUNK_SIZE, cy * CHUNK_SIZE, cz * CHUNK_SIZE);
    scene.add(g);
    state.chunks.set(key, { group: g });
    try {
        const res = await fetch(`/api/anemone/get_chunk?x=${cx}&y=${cy}&z=${cz}`);
        const data = await res.json();
        if (data.items) data.items.forEach(item => createHangingArt(g, item));
    } catch (e) {}
}


// --- ОПТИМИЗАЦИЯ: ОБЩИЕ РЕСУРСЫ ---
// 1. Общая геометрия для всех карточек (во избежание создания тысяч копий)
const commonPaperGeometry = new THREE.PlaneGeometry(1, 1); 
commonPaperGeometry.translate(0, -0.5, 0); // Сдвиг pivot point

// Расширяем границы обсчета
commonPaperGeometry.computeBoundingSphere();
commonPaperGeometry.boundingSphere.radius = 3.0;

// 2. Общая геометрия для веревки
const commonLineGeometry = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(0,0,0), 
    new THREE.Vector3(0, 3000, 0)
]);

// 3. Общие Uniforms (время и ветер обновляются централизованно)
const globalUniforms = {
    uTime: { value: 0 },
    uWindSpeed: { value: CONFIG.wind.speed },
    uWindForce: { value: CONFIG.wind.force },
    // Новые uniform-ы
    uSwayAmp: { value: CONFIG.motion.swayAmp },
    uTwistAmp: { value: CONFIG.motion.twistAmp }
};

function createHangingArt(group, data) {
    const baseScale = data.scale[0] * 1.5; 
    const geometry = commonPaperGeometry;

    const phase = Math.random() * 10;
    const swaySpeed = 0.5 + Math.random() * 0.5;

    const material = new THREE.ShaderMaterial({
        vertexShader: paperVertexShader,
        fragmentShader: paperFragmentShader,
        uniforms: {
            ...globalUniforms,
            map: { value: PLACEHOLDER_TEXTURE },
            hasTexture: { value: false },
            uColor: { value: new THREE.Color(0xffffff) },
            uAspectRatio: { value: 1.0 },
            uPhase: { value: phase },
            uSwaySpeed: { value: swaySpeed },
            // Инициализируем масштаб картинки как 1:1
            uImageScale: { value: new THREE.Vector2(1, 1) }
        },
        side: THREE.DoubleSide,
        transparent: true,
        depthWrite: false
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(data.pos[0], data.pos[1] + (baseScale / 2), data.pos[2]);
    
    // ВАЖНО: Делаем масштаб равномерным по всем осям!
    // Это предотвращает сплющивание при вращении
    mesh.scale.set(baseScale, baseScale, baseScale); 
    
    mesh.frustumCulled = true; 

    const lineMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.3 });
    const line = new THREE.Line(commonLineGeometry, lineMat);
    mesh.add(line);

    group.add(mesh);

queueImageLoad(data.post_id, data.pos, (tex, ratio) => {
        tex.minFilter = THREE.LinearFilter;
        tex.generateMipmaps = false;
        
        // --- ИСПРАВЛЕНИЕ ФРИЗОВ ---
        // Принудительно отправляем текстуру на GPU прямо сейчас, 
        // чтобы рендер не "споткнулся" об нее в следующем кадре.
        renderer.initTexture(tex); 
        
        material.uniforms.map.value = tex;
        material.uniforms.hasTexture.value = true;
        material.uniforms.uAspectRatio.value = ratio; // Для рамки полароида в frag shader

        // ВМЕСТО изменения mesh.scale, меняем uniform внутри шейдера
        let scaleX = 1;
        let scaleY = 1;

        if (ratio > 1) { 
            scaleX = ratio;
            scaleY = 1;
        } else {
            scaleX = 1;
            scaleY = 1 / ratio;
        }

        // Передаем "геометрические" размеры в шейдер
        material.uniforms.uImageScale.value.set(scaleX, scaleY);
        
        // mesh.scale трогать не нужно, он остается равномерным (baseScale, baseScale, baseScale)
        
    }, () => { 
        group.remove(mesh); 
        material.dispose();
        if(material.uniforms.map.value && material.uniforms.map.value.dispose) {
            material.uniforms.map.value.dispose();
        }
    });
}

function unloadChunk(key) {
    const c = state.chunks.get(key);
    if(c) { scene.remove(c.group); state.chunks.delete(key); }
}

function updateChunks() {
    const cx = Math.floor(state.currentPos.x/CHUNK_SIZE+0.5), cy = Math.floor(state.currentPos.y/CHUNK_SIZE+0.5), cz = Math.floor(state.currentPos.z/CHUNK_SIZE+0.5);
    if(cx!==state.currentChunk.x || cy!==state.currentChunk.y || cz!==state.currentChunk.z){
        state.currentChunk={x:cx,y:cy,z:cz};
        const active = new Set();
        for(let x=-RENDER_DISTANCE; x<=RENDER_DISTANCE; x++)
            for(let y=-RENDER_DISTANCE; y<=RENDER_DISTANCE; y++)
                for(let z=-RENDER_DISTANCE; z<=RENDER_DISTANCE; z++) {
                    loadChunk(cx+x, cy+y, cz+z); active.add(`${cx+x},${cy+y},${cz+z}`);
                }
        for(const k of state.chunks.keys()) if(!active.has(k)) unloadChunk(k);
    }
}

// --- УПРАВЛЕНИЕ КАМЕРОЙ ---
window.addEventListener('mousedown', e => { state.isDragging=true; state.lastMouse={x:e.clientX, y:e.clientY}; document.body.style.cursor='grabbing'; });
window.addEventListener('mouseup', () => { state.isDragging=false; document.body.style.cursor='default'; });
window.addEventListener('mousemove', e => {
    if(!state.isDragging) return;
    const dx = e.clientX - state.lastMouse.x;
    const dy = e.clientY - state.lastMouse.y;
    state.targetPos.x -= dx * 2.5;
    state.targetPos.y += dy * 2.5; // Инверсия Y
    state.lastMouse = {x:e.clientX, y:e.clientY};
});
window.addEventListener('wheel', e => state.targetPos.z += e.deltaY * 2.0, {passive:true});
window.addEventListener('touchstart', e => { if(e.touches.length===1){state.isDragging=true; state.lastMouse={x:e.touches[0].clientX, y:e.touches[0].clientY}} });
window.addEventListener('touchmove', e => { 
    if(state.isDragging && e.touches.length===1){
        e.preventDefault();
        const dx = e.touches[0].clientX - state.lastMouse.x;
        const dy = e.touches[0].clientY - state.lastMouse.y;
        state.targetPos.x -= dx * 2.5; state.targetPos.y += dy * 2.5;
        state.lastMouse={x:e.touches[0].clientX, y:e.touches[0].clientY};
    }
}, {passive:false});
window.addEventListener('touchend', ()=>state.isDragging=false);

// --- UI INTERACTION ---
const btn = document.getElementById('settings-btn');
const panel = document.getElementById('settings-panel');
let panelOpen = false;
btn.addEventListener('click', () => {
    panelOpen = !panelOpen;
    panel.classList.toggle('active', panelOpen);
});

// Привязка инпутов
// Привязка инпутов
// --- ФУНКЦИЯ ОБНОВЛЕНИЯ ФОНА ---
function updateBackgroundGradient() {
    const cBot = '#' + CONFIG.colors.bottom.getHexString();
    const cMid = '#' + CONFIG.colors.mid.getHexString();
    const cTop = '#' + CONFIG.colors.top.getHexString();
    
    document.body.style.backgroundImage = 
        `linear-gradient(to top, ${cBot} 0%, ${cMid} 40%, ${cTop} 100%)`;
    
    // Обновляем туман, чтобы горизонт сливался с новым цветом
    scene.fog.color.set(CONFIG.colors.bottom);
}

// Привязка инпутов
document.getElementById('col-bot').addEventListener('input', (e) => { 
    CONFIG.colors.bottom.set(e.target.value); 
    updateBackgroundGradient();
});
document.getElementById('col-mid').addEventListener('input', (e) => { 
    CONFIG.colors.mid.set(e.target.value);
    updateBackgroundGradient();
});
document.getElementById('col-top').addEventListener('input', (e) => { 
    CONFIG.colors.top.set(e.target.value);
    updateBackgroundGradient();
});
document.getElementById('col-fire').addEventListener('input', (e) => { 
    fireflyMat.uniforms.color.value.set(e.target.value);
});
// Новые обработчики для вращения
document.getElementById('sway-amp').addEventListener('input', (e) => { 
    CONFIG.motion.swayAmp = parseFloat(e.target.value);
    globalUniforms.uSwayAmp.value = CONFIG.motion.swayAmp;
});

document.getElementById('twist-amp').addEventListener('input', (e) => { 
    CONFIG.motion.twistAmp = parseFloat(e.target.value);
    globalUniforms.uTwistAmp.value = CONFIG.motion.twistAmp;
});
// Остальные слайдеры без изменений...
document.getElementById('wind-speed').addEventListener('input', (e) => CONFIG.wind.speed = parseFloat(e.target.value));
document.getElementById('wind-force').addEventListener('input', (e) => CONFIG.wind.force = parseFloat(e.target.value));
document.getElementById('part-speed').addEventListener('input', (e) => CONFIG.particles.speed = parseFloat(e.target.value));


// --- ИНТЕГРАЦИЯ COLOR PICKER ---
import { HexColorPicker } from 'https://unpkg.com/vanilla-colorful?module';

function setupColorPickers() {
    const inputs = [
        { id: 'col-bot', target: CONFIG.colors.bottom, cb: updateBackgroundGradient },
        { id: 'col-mid', target: CONFIG.colors.mid, cb: updateBackgroundGradient },
        { id: 'col-top', target: CONFIG.colors.top, cb: updateBackgroundGradient },
        { id: 'col-fire', target: null, cb: (hex) => fireflyMat.uniforms.color.value.set(hex) }
    ];

    inputs.forEach(conf => {
        const inputEl = document.getElementById(conf.id);
        if(!inputEl) return;

        // Прячем стандартный инпут
        inputEl.style.opacity = 0; 
        inputEl.style.position = 'absolute';
        inputEl.style.pointerEvents = 'none';

        // Создаем "swatch" (цветной квадратик)
        const swatch = document.createElement('div');
        swatch.style.width = '100%';
        swatch.style.height = '30px';
        swatch.style.borderRadius = '4px';
        swatch.style.backgroundColor = inputEl.value;
        swatch.style.border = '1px solid #555';
        swatch.style.cursor = 'pointer';
        inputEl.parentNode.appendChild(swatch);

        // Поповер
        const popover = document.createElement('div');
        popover.className = 'custom-picker-popover';
        document.body.appendChild(popover);

        // Сам пикер
        const picker = new HexColorPicker();
        picker.color = inputEl.value;
        popover.appendChild(picker);

        // Поле ввода HEX
        const hexInput = document.createElement('input');
        hexInput.type = 'text';
        hexInput.value = inputEl.value;
        hexInput.style.width = '100%';
        hexInput.style.marginTop = '10px';
        hexInput.style.boxSizing = 'border-box';
        hexInput.style.background = '#222';
        hexInput.style.border = '1px solid #444';
        hexInput.style.color = '#fff';
        hexInput.style.padding = '5px';
        hexInput.style.borderRadius = '4px';
        hexInput.style.textAlign = 'center';
        hexInput.style.fontFamily = 'monospace';
        popover.appendChild(hexInput);

        // Логика открытия
        swatch.addEventListener('click', (e) => {
            e.stopPropagation();
            document.querySelectorAll('.custom-picker-popover').forEach(p => p.classList.remove('active'));
            
            const rect = swatch.getBoundingClientRect();
            popover.style.top = (rect.bottom + 5) + 'px';
            popover.style.left = (rect.left) + 'px';
            if(rect.left + 200 > window.innerWidth) popover.style.left = (window.innerWidth - 220) + 'px';
            
            popover.classList.add('active');
        });

        // Функция обновления (DRY)
        const updateColor = (hex) => {
            swatch.style.backgroundColor = hex;
            inputEl.value = hex; 
            hexInput.value = hex; // Обновляем текст
            if (conf.target) conf.target.set(hex);
            if (conf.cb) conf.cb(hex);
        };

        // Событие: двигаем пикер -> меняется текст и цвет
        picker.addEventListener('color-changed', (e) => {
            // Чтобы не зацикливать обновление, проверяем фокус
            if (document.activeElement !== hexInput) {
                updateColor(e.detail.value);
            }
        });

        // Событие: вводим текст -> меняется пикер и цвет
        hexInput.addEventListener('input', (e) => {
            let hex = e.target.value;
            if (hex.startsWith('#') && (hex.length === 4 || hex.length === 7)) {
                picker.color = hex; // Это вызовет color-changed, но мы там добавили проверку фокуса
                swatch.style.backgroundColor = hex;
                inputEl.value = hex;
                if (conf.target) conf.target.set(hex);
                if (conf.cb) conf.cb(hex);
            }
        });
    });

    // Закрытие при клике вовне
    window.addEventListener('mousedown', (e) => {
        if (!e.target.closest('.custom-picker-popover') && !e.target.closest('.control-group')) {
            document.querySelectorAll('.custom-picker-popover').forEach(p => p.classList.remove('active'));
        }
    });
}

// Вызовите это один раз при старте
setupColorPickers();




// --- ANIMATION ---
const clock = new THREE.Clock();

function animate() {
    requestAnimationFrame(animate);
    
    const dt = clock.getDelta();
    const time = clock.getElapsedTime();

    // Плавное движение камеры
    state.currentPos.lerp(state.targetPos, 0.08);
    camera.position.copy(state.currentPos);
    
    // Обновление чанков (загрузка/выгрузка)
    updateChunks();

    // --- ОБНОВЛЕНИЕ ЗВЕЗД И КОМЕТ ---
    starMat.uniforms.uTime.value = time;       // <--- Анимация мерцания звезд
    starSystem.position.copy(camera.position); // <--- Звезды всегда вокруг игрока
    comet.update(camera.position);             // <--- Логика комет

    // Обновление глобальных Uniforms
    dustMat.uniforms.uCamPos.value.copy(camera.position);
    dustMat.uniforms.uTime.value = time;

    fireflyMat.uniforms.uCamPos.value.copy(camera.position);
    fireflyMat.uniforms.uTime.value = time;

    globalUniforms.uTime.value = time;
    globalUniforms.uWindSpeed.value = CONFIG.wind.speed;
    globalUniforms.uWindForce.value = CONFIG.wind.force;

    // --- ДОБАВИТЬ ЭТОТ БЛОК ---
    // Передача значений слайдеров в частицы (Пыль)
    dustMat.uniforms.uCamPos.value.copy(camera.position);
    dustMat.uniforms.uTime.value = time;
    dustMat.uniforms.uWindSpeed.value = CONFIG.wind.speed;
    dustMat.uniforms.uWindForce.value = CONFIG.wind.force;
    dustMat.uniforms.uPartSpeed.value = CONFIG.particles.speed;

    // Передача значений слайдеров в частицы (Светлячки)
    fireflyMat.uniforms.uCamPos.value.copy(camera.position);
    fireflyMat.uniforms.uTime.value = time;
    fireflyMat.uniforms.uWindSpeed.value = CONFIG.wind.speed;
    fireflyMat.uniforms.uWindForce.value = CONFIG.wind.force;
    fireflyMat.uniforms.uPartSpeed.value = CONFIG.particles.speed;

    // Рендер
    renderer.render(scene, camera);
}

animate();
setTimeout(() => document.getElementById('status').style.opacity = 0, 1000);
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth/window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    fireflyMat.uniforms.scale.value = window.innerHeight / 2.0;
});