import * as THREE from 'three';

// --- КОНФИГУРАЦИЯ И СОСТОЯНИЕ (Глобальные настройки) ---
const CONFIG = {
    colors: {
        bottom: new THREE.Color('#2b1a38'), 
        mid: new THREE.Color('#203a4c'),    
        top: new THREE.Color('#050814'),    
        firefly: new THREE.Color('#ffaa00') 
    },
    wind: { speed: 0.8, force: 0.3 },
    particles: { speed: 0.5 },
    motion: { swayAmp: 0.1, twistAmp: 0.15 },
    // НОВЫЕ НАСТРОЙКИ
    sky: {
        starDensity: 15000,
        starSize: 1.0,
        blur: 0.0, // Эффект боке (0 - нет, 1 - макс)
        cometFreq: 0.02,     // Быстрые кометы
        slowCometFreq: 0.002 // Медленные фоновые кометы
    },
    details: {
        dustCount: 4000,
        dustSize: 1.0,
        fireflyCount: 600,
        fireflySize: 1.0
    }
};

const CHUNK_SIZE = 1500;
const RENDER_DISTANCE = 1;
const FADE_DISTANCE = 1600;
// ОПТИМИЗАЦИЯ: Увеличиваем с 2 до 6, так как файлы теперь загружаются быстрее
const MAX_CONCURRENT_LOADS = 6; 
const MAX_TEXTURE_SIZE = 512;
// --- SHADERS (Шейдеры) ---


// 2. ШЕЙДЕР БУМАГИ (Ветер + Полароид)
const paperVertexShader = `
    uniform float uTime;
    uniform float uWindSpeed;
    uniform float uWindForce;
    
    uniform float uPhase;
    uniform float uSwaySpeed;
    
    uniform float uSwayAmp;  
    uniform float uTwistAmp; 

    uniform vec2 uImageScale; 

    varying vec2 vUv;
    varying float vDist;
    varying vec3 vWorldPos;

    void main() {
        vUv = uv;
        vec3 pos = position; 
        
        // Масштабирование под формат фото
        pos.xy *= uImageScale;

        // --- 1. ФИЗИКА МАЯТНИКА (Базовое качание) ---
        float swing = sin(uTime * uSwaySpeed + uPhase) * (uSwayAmp + uWindForce * 0.2);
        // Добавляем "дрожание" от порывов ветра
        float flutter = sin(uTime * 3.0 + uPhase * 2.0) * 0.05 * uWindForce;
        float totalAngle = swing + flutter;

        float c = cos(totalAngle);
        float s = sin(totalAngle);

        // Вращение вокруг точки крепления (0,0,0) - верх карточки
        float rX = pos.x * c - pos.y * s;
        float rY = pos.x * s + pos.y * c;
        pos.x = rX;
        pos.y = rY;
        
        // --- 2. ПОВОРОТ ВОКРУГ ОСИ Y (Twist) ---
        float twistAngle = sin(uTime * 0.5 + uPhase) * uTwistAmp;
        float cT = cos(twistAngle);
        float sT = sin(twistAngle);

        float finalX = pos.x * cT - pos.z * sT;
        float finalZ = pos.x * sT + pos.z * cT;
        pos.x = finalX;
        pos.z = finalZ;

        // --- 3. ИЗГИБ БУМАГИ (Paper Physics) ---
        // Работает только если у геометрии достаточно сегментов.
        // pos.y идет от 0.0 (верх) до -Height (низ).
        // Чем ниже точка, тем сильнее влияние ветра.
        
        float distFromTop = abs(pos.y); // 0 -> 1+
        
        // Волна, бегущая по бумаге
        float wave = sin(pos.x * 2.0 + uTime * 4.0 + pos.y * 3.0);
        
        // Изгиб "парусом" от ветра (центр выгибается)
        float sail = sin(pos.x * 3.14); 
        
        // Комбинируем деформации Z
        float deformation = (wave * 0.1 + sail * 0.05) * uWindForce;
        
        // Применяем деформацию с нарастанием к низу карточки
        // pow(distFromTop, 1.5) делает верх жестким, а низ гибким
        pos.z += deformation * pow(distFromTop, 1.5);
        
        // Немного сдвигаем X для эффекта "сжатия" бумаги при изгибе
        pos.x += (sin(uTime * 5.0 + pos.y * 10.0) * 0.01 * uWindForce) * distFromTop;

        vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
        gl_Position = projectionMatrix * mvPosition;
        vDist = -mvPosition.z; 
        
        vWorldPos = (modelMatrix * vec4(pos, 1.0)).xyz; 
    }
`;

const paperFragmentShader = `
    uniform sampler2D map;
    uniform vec3 uColor;
    uniform bool hasTexture;
    uniform float uTime;
    uniform float uPhase; 
    
    uniform vec3 uCamPos;
    uniform vec3 uCamDir;
    
    varying vec2 vUv;
    varying float vDist;
    varying vec3 vWorldPos;

    // --- ФУНКЦИЯ РИСОВАНИЯ ЗАГРУЗОЧНОЙ ПОЛОСЫ (Плавное заполнение) ---
    float drawProgressBar(vec2 uv, float totalTime) {
        float result = 0.0;
        
        float count = 5.0;
        float boxW = 0.04;
        float boxH = 0.012;
        float gap = 0.015;
        
        float totalWidth = (boxW * count) + (gap * (count - 1.0));
        float startX = 0.5 - (totalWidth * 0.5) + (boxW * 0.5);
        float posY = 0.40;

        // Время на один блок (в секундах)
        float timePerBlock = 6.0; 

        for(float i = 0.0; i < 5.0; i++) {
            vec2 center = vec2(startX + i * (boxW + gap), posY);
            
            // SDF для прямоугольника
            vec2 d = abs(uv - center) - vec2(boxW * 0.5, boxH * 0.5);
            float dist = max(d.x, d.y);
            
            // Контур
            float outline = 1.0 - smoothstep(0.0, 0.0015, abs(dist));
            
            // Логика заполнения
            // Вычисляем, насколько заполнен ТЕКУЩИЙ блок (от 0.0 до 1.0)
            // totalTime идет от 0 до 30. 
            // i=0 -> заполняется с 0 по 6 сек.
            // i=1 -> заполняется с 6 по 12 сек.
            float blockStart = i * timePerBlock;
            float blockEnd = (i + 1.0) * timePerBlock;
            
            float progress = clamp((totalTime - blockStart) / (blockEnd - blockStart), 0.0, 1.0);
            
            // Маска заполнения внутри бокса (слева направо)
            // uv.x должен быть меньше чем левый край + ширина * прогресс
            float boxLeft = center.x - (boxW * 0.5);
            float fillMask = step(uv.x, boxLeft + (boxW * progress));
            
            // Само "тело" блока (внутренность)
            float shape = 1.0 - smoothstep(0.0, 0.002, dist);
            
            result += max(outline, shape * fillMask);
        }
        
        return result;
    }

    void main() {
        float shadowStart = 800.0;
        float shadowEnd = 1600.0;
        float lightFactor = 1.0 - smoothstep(shadowStart, shadowEnd, vDist);
        float brightness = 0.15 + (0.85 * lightFactor);

        float opacityStart = 1500.0; 
        float opacityEnd = 2200.0;   
        float opacity = 1.0 - smoothstep(opacityStart, opacityEnd, vDist);
        if (opacity <= 0.01) discard; 

        vec3 rgbColor;

        if (hasTexture) {
            rgbColor = texture2D(map, vUv).rgb;
        } else {
            vec3 bg = vec3(0.05, 0.09, 0.18); 
            
            // Точка
            vec2 center = vec2(0.5, 0.5);
            float distToCenter = distance(vUv, center);
            float pulse = 0.5 + 0.5 * sin(uTime * 8.0); 
            float dotRadius = 0.015 + 0.005 * pulse; 
            float centerDot = 1.0 - smoothstep(dotRadius, dotRadius + 0.002, distToCenter);
            
            // Приоритет (цвет контура полосок)
            vec3 toObj = normalize(vWorldPos - uCamPos);
            float align = dot(toObj, uCamDir); 
            float dist = distance(vWorldPos, uCamPos);

            vec3 priorityColor = (align > 0.5 && dist < 1200.0) ? vec3(1.0) : vec3(1.0, 0.85, 0.0);

            // Прогресс (Медленный цикл 30 секунд)
            float localTime = uTime + uPhase * 5.0; // Phase сдвигает старт
            float t = mod(localTime, 35.0); // 30 сек заполнение + 5 сек пауза полной полоски
            
            float barsMask = drawProgressBar(vUv, t);
            
            rgbColor = bg;
            rgbColor = mix(rgbColor, vec3(1.0), centerDot); 
            rgbColor = mix(rgbColor, priorityColor, barsMask); 
        }

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
const MAX_DUST = 8000;
const MAX_FIREFLIES = 1200;
const wrapSize = 4000; 

const particleGroup = new THREE.Group();
scene.add(particleGroup);

// Пыль (Белые)
// --- ЧАСТИЦЫ (БЕСКОНЕЧНОЕ ПОЛЕ) ---
// Общий шейдер для частиц, которые всегда вокруг камеры
const infiniteParticleVertex = `
uniform float uTime;
uniform vec3 uCamPos;
uniform float uSize;
uniform float uScale;       // <-- Здесь uScale
uniform float uSizeMult;    // <-- ДОБАВЛЕНО: Объявление множителя размера

// Новые uniform-ы для физики
uniform float uWindSpeed;
uniform float uWindForce;
uniform float uPartSpeed;

attribute float size;       // <-- Здесь атрибут называется size
varying float vAlpha;

void main() {
    vec3 pos = position;
    
    // 1. ВЕТЕР
    float windOffset = uTime * uWindSpeed * 50.0;
    float vertOffset = uTime * uPartSpeed * 10.0;
    
    vec3 animatedPos = pos;
    animatedPos.x += windOffset; 
    animatedPos.y -= vertOffset; 

    // 2. ТУРБУЛЕНТНОСТЬ
    float wobbleFreq = uTime * uPartSpeed;
    float wobbleAmp = uWindForce * 200.0; 
    
    animatedPos.x += sin(wobbleFreq + pos.y * 0.01) * wobbleAmp;
    animatedPos.y += cos(wobbleFreq + pos.x * 0.01) * wobbleAmp * 0.5;

    // 3. БЕСКОНЕЧНОЕ ЗАЦИКЛИВАНИЕ
    vec3 localPos = mod(animatedPos - uCamPos + uSize * 0.5, uSize) - uSize * 0.5;
    vec3 finalPos = uCamPos + localPos;

    vec4 mvPosition = modelViewMatrix * vec4(finalPos, 1.0);
    gl_Position = projectionMatrix * mvPosition;
    
    // ИСПРАВЛЕНИЕ ОШИБОК ИМЕНОВАНИЯ:
    // Было: (aSize * uSizeMult * scale)
    // Стало: (size * uSizeMult * uScale)
    gl_PointSize = (size * uSizeMult * uScale) / -mvPosition.z;
    
    float dist = length(localPos);
    vAlpha = 1.0 - smoothstep(uSize * 0.35, uSize * 0.5, dist);
}
`;



const fireflyGeo = new THREE.BufferGeometry();
const fireflyPos = [];
const fireflyPhase = [];
const fireflySize = [];
const fireflyType = []; 

// Генерируем буфер сразу на МАКСИМАЛЬНОЕ количество
for (let i = 0; i < MAX_FIREFLIES; i++) {
    fireflyPos.push(
        (Math.random() - 0.5) * wrapSize,
        (Math.random() - 0.5) * wrapSize, 
        (Math.random() - 0.5) * wrapSize
    );
    fireflyPhase.push(Math.random() * Math.PI * 2);
    
    const isBody = Math.random() > 0.7; 
    fireflyType.push(isBody ? 1.0 : 0.0);
    fireflySize.push(isBody ? (15.0 + Math.random() * 10.0) : (3.0 + Math.random() * 4.0));
}

fireflyGeo.setAttribute('position', new THREE.Float32BufferAttribute(fireflyPos, 3));
fireflyGeo.setAttribute('phase', new THREE.Float32BufferAttribute(fireflyPhase, 1));
// ИСПРАВЛЕНИЕ 1: Имя атрибута 'size' вместо 'aSize' для совместимости с кодом шейдера
fireflyGeo.setAttribute('size', new THREE.Float32BufferAttribute(fireflySize, 1));
fireflyGeo.setAttribute('type', new THREE.Float32BufferAttribute(fireflyType, 1));

const fireflyMat = new THREE.ShaderMaterial({
    uniforms: {
        color: { value: CONFIG.colors.firefly },
        uTime: { value: 0 },
        // ИСПРАВЛЕНИЕ 2: Имя униформа 'uScale' вместо 'scale'
        uScale: { value: window.innerHeight / 2.0 },
        uCamPos: { value: new THREE.Vector3() },
        uSize: { value: wrapSize },
        uSizeMult: { value: CONFIG.details.dustSize },
        uWindSpeed: { value: CONFIG.wind.speed },
        uWindForce: { value: CONFIG.wind.force },
        uPartSpeed: { value: CONFIG.particles.speed }
    },
    vertexShader: `
        attribute float phase;
        attribute float size; // ИСПРАВЛЕНИЕ: теперь size совпадает с использованием ниже
        attribute float type;
        
        varying float vAlpha;
        varying float vType; 
        
        uniform float uTime;
        uniform float uScale; // ИСПРАВЛЕНИЕ: объявлен uScale
        uniform vec3 uCamPos;
        uniform float uSize;
        uniform float uWindSpeed;
        uniform float uWindForce;
        uniform float uPartSpeed;
        uniform float uSizeMult; 

        void main() {
            vType = type;
            vec3 pos = position;

            // Движение
            float timeScale = (type > 0.5) ? 1.0 : 2.5; 
            
            float windOffset = uTime * uWindSpeed * 60.0 * timeScale;
            float vertOffset = uTime * uPartSpeed * 15.0 * timeScale;
            
            vec3 animatedPos = pos;
            animatedPos.x += windOffset;
            animatedPos.y += vertOffset;

            // Хаотичное движение
            float wobbleSpeed = uTime * (0.5 + uPartSpeed) * timeScale;
            float wobbleAmp = (type > 0.5) ? 50.0 : 80.0;
            
            animatedPos.x += sin(wobbleSpeed + phase) * (wobbleAmp + uWindForce * 100.0);
            animatedPos.y += cos(wobbleSpeed * 0.8 + phase) * (wobbleAmp + uWindForce * 100.0);
            animatedPos.z += sin(wobbleSpeed * 0.5 + phase) * (20.0 + uWindForce * 50.0);

            // Зацикливание
            vec3 localPos = mod(animatedPos - uCamPos + uSize * 0.5, uSize) - uSize * 0.5;
            vec4 mvPosition = modelViewMatrix * vec4(uCamPos + localPos, 1.0);
            gl_Position = projectionMatrix * mvPosition;

            // Размер: теперь переменные size и uScale объявлены корректно
            gl_PointSize = (size * uSizeMult * uScale) / -mvPosition.z;
            
            // Мерцание
            float blinkSpeed = (type > 0.5) ? 3.0 : 8.0;
            float blink = sin(uTime * blinkSpeed + phase);
            
            float baseAlpha = (type > 0.5) ? (0.6 + 0.4 * blink) : (0.4 + 0.6 * blink);
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
            vec2 coord = gl_PointCoord - vec2(0.5);
            float dist = length(coord);
            if(dist > 0.5) discard;

            vec4 finalColor;
            if (vType > 0.5) {
                float core = 1.0 - smoothstep(0.05, 0.25, dist);
                float glow = exp(-dist * 4.0);
                vec3 coreColor = mix(color, vec3(1.0, 1.0, 0.8), core * 0.8);
                float strength = core + glow * 0.6;
                finalColor = vec4(coreColor, vAlpha * strength);
            } else {
                float spark = 1.0 - pow(dist * 2.0, 0.5);
                finalColor = vec4(color, vAlpha * spark);
            }
            gl_FragColor = finalColor;
        }
    `,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    depthTest: false 
});
const fireflySystem = new THREE.Points(fireflyGeo, fireflyMat);
fireflySystem.frustumCulled = false;
scene.add(fireflySystem);
fireflySystem.renderOrder = 11;


// 1. ПЫЛЬ
const dustGeo = new THREE.BufferGeometry();
const dustPos = [];
const dustSizes = [];
// Используем MAX_DUST (8000)
for (let i = 0; i < MAX_DUST; i++) {
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
        uWindSpeed: { value: 0 },
        uWindForce: { value: 0 },
        uPartSpeed: { value: 0 },
        
        // --- ДОБАВИТЬ ЭТУ СТРОКУ ---
        uSizeMult: { value: CONFIG.details.dustSize } 
    },
    vertexShader: infiniteParticleVertex,
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
    depthTest: false,
    blending: THREE.AdditiveBlending
});
const dustSystem = new THREE.Points(dustGeo, dustMat);
dustSystem.frustumCulled = false; // <--- ВАЖНО: Запрещаем Three.js прятать частицы при вылете из центра
scene.add(dustSystem);
dustSystem.renderOrder = 10;

// --- REALISTIC SKY SYSTEM (Звезды и Кометы) ---

// 1. Звездное поле (Разные цвета, мерцание)
// 1. Звездное поле (Реалистичный спектр)
const MAX_STARS = 30000; 
const starGeo = new THREE.BufferGeometry();
const starPos = [];
const starColors = [];
const starSizes = [];
const starFlashSpeed = [];
const starBrightness = []; 

// Вспомогательный цвет для вычислений
const tempColor = new THREE.Color();

// Генерируем MAX_STARS
for(let i=0; i<MAX_STARS; i++) {
    const r = 3000 + Math.random() * 2000; 
    const theta = 2 * Math.PI * Math.random();
    const phi = Math.acos(2 * Math.random() - 1);
    
    const x = r * Math.sin(phi) * Math.cos(theta);
    const y = r * Math.sin(phi) * Math.sin(theta);
    const z = r * Math.cos(phi);
    
    starPos.push(x, y, z);
    
    // --- ЛОГИКА ЦВЕТА И ЯРКОСТИ (Строгий реализм) ---
    const rand = Math.random();
    let sizeBase;
    let brightnessBase;

    // 1. ПОДАВЛЯЮЩЕЕ БОЛЬШИНСТВО (92%) - Тусклые желто-оранжевые / Белые
    // Сделали их менее насыщенными и не такими яркими
    if (rand < 0.92) {
        // Hue 35-55 (Yellow-Orange), Saturation 15-40% (бледные), Lightness средняя
        const hue = 0.1 + Math.random() * 0.05; 
        const sat = 0.15 + Math.random() * 0.25;   
        const light = 0.6 + Math.random() * 0.3; 
        tempColor.setHSL(hue, sat, light);
        
        // Размер поменьше, чтобы не рябило
        sizeBase = 8.0 + Math.random() * 5.0;   
        // Яркость намеренно снижена для фона
        brightnessBase = 0.3 + Math.random() * 0.4; 
    }
    // 2. Оранжевые гиганты (4%) - Яркие и насыщенные
    else if (rand < 0.96) {
        tempColor.setHSL(0.06 + Math.random() * 0.04, 0.9, 0.6);
        sizeBase = 16.0 + Math.random() * 6.0; 
        brightnessBase = 1.2 + Math.random() * 0.6; // Они будут выделяться в боке
    }
    // 3. Красные (2%)
    else if (rand < 0.98) {
        tempColor.setHSL(0.0 + Math.random() * 0.02, 0.8, 0.6); 
        sizeBase = 14.0 + Math.random() * 4.0;
        brightnessBase = 0.9 + Math.random() * 0.4;
    }
    // 4. Горячие Синие/Белые (1.5%)
    else if (rand < 0.995) {
        tempColor.setHSL(0.6 + Math.random() * 0.05, 0.7, 0.8);
        sizeBase = 15.0 + Math.random() * 8.0; 
        brightnessBase = 1.3 + Math.random() * 0.7; // Самые яркие
    }
    // 5. Уникальные (0.5%)
    else {
        tempColor.setHSL(0.45 + Math.random() * 0.1, 0.9, 0.6); 
        sizeBase = 18.0;
        brightnessBase = 1.5; 
    }

    starColors.push(tempColor.r, tempColor.g, tempColor.b);
    starSizes.push(sizeBase);
    starBrightness.push(brightnessBase);
    
    // Мерцание медленнее, чтобы было спокойнее
    starFlashSpeed.push(Math.random() * 1.5 + 0.1);
}

starGeo.setAttribute('position', new THREE.Float32BufferAttribute(starPos, 3));
starGeo.setAttribute('color', new THREE.Float32BufferAttribute(starColors, 3));
starGeo.setAttribute('size', new THREE.Float32BufferAttribute(starSizes, 1));
starGeo.setAttribute('speed', new THREE.Float32BufferAttribute(starFlashSpeed, 1));
starGeo.setAttribute('brightness', new THREE.Float32BufferAttribute(starBrightness, 1));
// --- ОБНОВЛЕННЫЙ ШЕЙДЕР ЗВЕЗД (REALISTIC VINTAGE BOKEH) ---

const starMat = new THREE.ShaderMaterial({
    uniforms: {
        uTime: { value: 0 },
        uScale: { value: window.innerHeight },
        uBlur: { value: CONFIG.sky.blur },
        uSizeMult: { value: CONFIG.sky.starSize },
        uResolution: { value: new THREE.Vector2(window.innerWidth, window.innerHeight) }
    },
    vertexShader: `
        attribute float size;
        attribute float speed;
        attribute float brightness;
        attribute vec3 color;
        
        varying vec3 vColor;
        varying float vAlpha;
        varying float vSpeed;
        varying vec2 vScreenPos;
        varying float vBrightness; 

        uniform float uTime;
        uniform float uScale;
        uniform float uSizeMult;
        uniform float uBlur;

        void main() {
            vColor = color;
            vSpeed = speed;
            vBrightness = brightness;
            
            vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
            gl_Position = projectionMatrix * mvPosition;
            vScreenPos = gl_Position.xy / gl_Position.w;
            
            float twinkle = sin(uTime * speed + position.x * 0.5);
            float baseAlpha = mix(0.5 + 0.5 * twinkle, 1.0, uBlur * 0.8);
            
            vAlpha = baseAlpha;

            float blurExpansion = uBlur * 300.0 * (0.6 + 0.4 * speed); 
            gl_PointSize = (size * uSizeMult + blurExpansion) * (uScale / -mvPosition.z);
        }
    `,
    fragmentShader: `
        varying vec3 vColor;
        varying float vAlpha;
        varying float vSpeed;
        varying vec2 vScreenPos;
        varying float vBrightness; 
        
        uniform float uBlur;
        uniform vec2 uResolution;

        float hexDist(vec2 p) {
            p = abs(p);
            float d = max(p.x * 0.866025 + p.y * 0.5, p.y);
            return d;
        }

        void main() {
            vec2 uv = gl_PointCoord - vec2(0.5);
            
            // Расчет позиции для искажения
            float distFromCenter = length(vScreenPos);
            float edgeFactor = smoothstep(0.7, 1.2, distFromCenter);
            
            // 1. ИСКАЖЕНИЕ (Линза)
            float distortStr = edgeFactor * edgeFactor * uBlur * 1.0;
            vec2 dirToCenter = normalize(-vScreenPos);
            vec2 distortedUV = uv - dirToCenter * dot(uv, dirToCenter) * distortStr;

            // 2. ВРАЩЕНИЕ
            float angle = vSpeed * 10.0; 
            float ca = cos(angle); float sa = sin(angle);
            mat2 rot = mat2(ca, -sa, sa, ca);
            vec2 rotUV = rot * distortedUV; 
            
            // 3. ФОРМА
            float distHex = hexDist(rotUV);
            float distCircle = length(distortedUV);
            float shapeDist = mix(distCircle, distHex, uBlur * 1.2);
            
            // --- ИСПРАВЛЕНИЕ 1: Компенсация размытия по краям ---
            // Добавляем edgeFactor в расчет мягкости, чтобы искаженные края не казались резкими
            float edgeSoftness = 0.05 + uBlur * (0.2 + edgeFactor * 0.5); 
            
            float alphaShape = 1.0 - smoothstep(0.5 - edgeSoftness, 0.5, shapeDist);
            //  --- ЦЕНТР ВЫЦВЕТАЕТ ПРИ БОЛЬШОМ BLUR ---
            float centerFade = smoothstep(
                0.0,
                0.35 + uBlur * 0.15, // радиус центра
                shapeDist
            );

            // centerFade: 0 в центре → 1 к краям
            // усиливаем эффект только при большом blur
            float blurCenterFactor = mix(1.0, centerFade, smoothstep(0.3, 1.0, uBlur));
            // 4. КОМПЕНСАЦИЯ ЯРКОСТИ (Energy Conservation)
            float energyConservation = 1.0 / (1.0 + uBlur * 2.0);
            
            // --- ИСПРАВЛЕНИЕ 2: Отсечение тусклых звезд (Anti-mess) ---
            // Порог растет вместе с блюром. 
            // 0.2 - базовый порог, 1.2 * uBlur - прирост требований к яркости
            float cullThreshold = 0.2 + uBlur * 0.55; 
            
            // Плавный срез: если яркость звезды меньше порога, она уходит в 0
            float cullFactor = smoothstep(cullThreshold, cullThreshold + 0.4, vBrightness);

            // Применяем cullFactor к итоговой прозрачности
            float finalOpacity =
                vAlpha *
                alphaShape *
                blurCenterFactor *   // ← ВАЖНО
                energyConservation *
                vBrightness *
                cullFactor;
            
            if (finalOpacity < 0.005) discard;

            // 5. ЦВЕТ И RIM ЭФФЕКТ
            vec3 finalRGB = vColor;
            float rim = smoothstep(0.35, 0.5, shapeDist);
            float luma = dot(finalRGB, vec3(0.299, 0.587, 0.114));
            vec3 chroma = finalRGB / max(luma, 0.001);

            finalRGB = mix(
                finalRGB,
                chroma * luma * (1.0 + rim * uBlur * 0.8),
                rim
            );

            gl_FragColor = vec4(finalRGB, finalOpacity);
        }
    `,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending
});

const starSystem = new THREE.Points(starGeo, starMat);
starSystem.renderOrder = -1; // Исправление: звезды рисуются первыми (фон)
scene.add(starSystem);


// --- ДОБАВИТЬ НОВЫЙ КЛАСС ---
class SlowCometSystem {
    constructor(scene) {
        // Лимит комет
        const count = 300; 
        
        // 1. ЛИНИИ (Хвосты)
        const lineGeo = new THREE.BufferGeometry();
        const linePos = new Float32Array(count * 2 * 3);
        const lineCols = new Float32Array(count * 2 * 4); 

        lineGeo.setAttribute('position', new THREE.BufferAttribute(linePos, 3));
        lineGeo.setAttribute('color', new THREE.BufferAttribute(lineCols, 4));

        this.lineMat = new THREE.LineBasicMaterial({
            vertexColors: true,
            transparent: true,
            blending: THREE.AdditiveBlending,
            depthWrite: false,
            opacity: 1.0 
        });

        this.lines = new THREE.LineSegments(lineGeo, this.lineMat);
        this.lines.renderOrder = 0; 
        this.lines.frustumCulled = false;
        scene.add(this.lines);

        // 2. ТОЧКИ (Головы с бликами)
        const headGeo = new THREE.BufferGeometry();
        const headPos = new Float32Array(count * 3);
        const headSizes = new Float32Array(count);
        const headAngles = new Float32Array(count); // Угол наклона блика
        const headColors = new Float32Array(count * 3);
        const headAlphas = new Float32Array(count);

        headGeo.setAttribute('position', new THREE.BufferAttribute(headPos, 3));
        headGeo.setAttribute('size', new THREE.BufferAttribute(headSizes, 1));
        headGeo.setAttribute('angle', new THREE.BufferAttribute(headAngles, 1));
        headGeo.setAttribute('color', new THREE.BufferAttribute(headColors, 3));
        headGeo.setAttribute('alpha', new THREE.BufferAttribute(headAlphas, 1));

        this.headMat = new THREE.ShaderMaterial({
            uniforms: {
                uScale: { value: window.innerHeight },
                uBlur: { value: 0 } // Будем обновлять
            },
            vertexShader: `
                attribute float size;
                attribute float angle;
                attribute float alpha;
                attribute vec3 color;
                varying vec3 vColor;
                varying float vAlpha;
                varying float vAngle;

                uniform float uScale;

                void main() {
                    vColor = color;
                    vAlpha = alpha;
                    vAngle = angle;
                    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
                    gl_Position = projectionMatrix * mvPosition;
                    // Размер головы увеличиваем для эффекта свечения
                    gl_PointSize = size * (uScale / -mvPosition.z);
                }
            `,
            fragmentShader: `
                varying vec3 vColor;
                varying float vAlpha;
                varying float vAngle;
                uniform float uBlur;

                void main() {
                    if (vAlpha <= 0.01) discard;
                    vec2 uv = gl_PointCoord - vec2(0.5);

                    // 1. Поворот для блика (Наклон)
                    float s = sin(vAngle);
                    float c = cos(vAngle);
                    mat2 rot = mat2(c, -s, s, c);
                    vec2 rotUV = rot * uv;

                    float dist = length(uv);

                    // 2. Яркое ядро (Сама "звезда")
                    float core = 1.0 - smoothstep(0.0, 0.15 + uBlur * 0.1, dist);
                    
                    // 3. Вытянутый мерцающий блик (Flare)
                    // Используем степень для остроты и abs для симметрии
                    float flareV = 0.015 / (abs(rotUV.x * 6.0) + 0.05);
                    float flareH = 0.002 / (abs(rotUV.y * 2.0) + 0.05); // Тонкий поперечный
                    float flare = (flareV + flareH) * (1.0 - smoothstep(0.3, 0.5, dist));
                    
                    // Собираем яркость
                    float intensity = core * 2.0 + flare * 1.5;
                    
                    // Мягкое угасание к краям спрайта
                    float circleFade = 1.0 - smoothstep(0.4, 0.5, dist);

                    vec3 finalColor = vColor * intensity;
                    gl_FragColor = vec4(finalColor, vAlpha * circleFade);
                }
            `,
            transparent: true,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });

        this.heads = new THREE.Points(headGeo, this.headMat);
        this.heads.renderOrder = 1; // Рисуем поверх хвостов
        this.heads.frustumCulled = false;
        scene.add(this.heads);


        // 3. ДАННЫЕ
        this.comets = [];
        for(let i=0; i<count; i++) {
            this.comets.push({
                active: false,
                pos: new THREE.Vector3(),
                vel: new THREE.Vector3(),
                color: new THREE.Color(),
                life: 0,
                maxLife: 0,
                index: i
            });
        }
        
        this.palette = [
            new THREE.Color('#ffaa00'), 
            new THREE.Color('#ffffff'), 
            new THREE.Color('#aaddff')  
        ];
    }

    spawn() {
        const available = this.comets.find(c => !c.active);
        if (!available) return;

        const r = 3000 + Math.random() * 2000; 
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        
        available.pos.set(
            r * Math.sin(phi) * Math.cos(theta),
            r * Math.sin(phi) * Math.sin(theta),
            r * Math.cos(phi)
        );

        const speed = 2.0 + Math.random() * 3.0; 
        const randomDir = new THREE.Vector3(Math.random()-0.5, Math.random()-0.5, Math.random()-0.5).normalize();
        available.vel.crossVectors(available.pos, randomDir).normalize().multiplyScalar(speed);

        available.color = this.palette[Math.floor(Math.random() * this.palette.length)];
        available.life = 0;
        available.maxLife = 500 + Math.random() * 300; 
        available.active = true;

        // Случайный наклон блика (например, от -45 до +45 градусов или произвольно)
        available.angle = (Math.random() - 0.5) * Math.PI; 
    }

    update(blurLevel) {
        // Обновляем юниформ блюра для голов
        this.headMat.uniforms.uBlur.value = blurLevel;

        const spawnChance = CONFIG.sky.slowCometFreq * 40.0;
        if (Math.random() < spawnChance) this.spawn();
        if (spawnChance > 1.0 && Math.random() < spawnChance * 0.5) this.spawn();

        // Атрибуты линий
        const linePosAttr = this.lines.geometry.attributes.position;
        const lineColAttr = this.lines.geometry.attributes.color;
        
        // Атрибуты голов
        const headPosAttr = this.heads.geometry.attributes.position;
        const headSizeAttr = this.heads.geometry.attributes.size;
        const headColAttr = this.heads.geometry.attributes.color;
        const headAlphaAttr = this.heads.geometry.attributes.alpha;
        const headAngleAttr = this.heads.geometry.attributes.angle;

        let needsUpdate = false;

        this.comets.forEach(c => {
            const idxLine1 = c.index * 2;     
            const idxLine2 = c.index * 2 + 1; 
            const idxHead = c.index;

            if (!c.active) {
                // Если не активна, прячем (альфа 0)
                if (headAlphaAttr.getX(idxHead) !== 0) { 
                    lineColAttr.setW(idxLine1, 0); lineColAttr.setW(idxLine2, 0);
                    headAlphaAttr.setX(idxHead, 0);
                    needsUpdate = true;
                }
                return;
            }

            c.life++;
            if (c.life > c.maxLife) {
                c.active = false;
                return;
            }

            c.pos.add(c.vel);
            
            // --- ЛИНИЯ (Хвост) ---
            const tailLen = 300.0;
            const tailPos = c.pos.clone().sub(c.vel.clone().normalize().multiplyScalar(tailLen));

            linePosAttr.setXYZ(idxLine1, tailPos.x, tailPos.y, tailPos.z);
            linePosAttr.setXYZ(idxLine2, c.pos.x, c.pos.y, c.pos.z);

            // Альфа зависит от жизни и блюра
            let progress = c.life / c.maxLife;
            let baseAlpha = Math.sin(progress * Math.PI) * 1.0; 
            
            // Хвост при блюре исчезает сильнее
            let lineAlpha = baseAlpha * (1.0 - blurLevel * 0.9);

            lineColAttr.setXYZW(idxLine2, c.color.r, c.color.g, c.color.b, lineAlpha);
            lineColAttr.setXYZW(idxLine1, c.color.r, c.color.g, c.color.b, 0.0);
            
            // --- ГОЛОВА (Точка) ---
            headPosAttr.setXYZ(idxHead, c.pos.x, c.pos.y, c.pos.z);
            headColAttr.setXYZ(idxHead, c.color.r, c.color.g, c.color.b);
            headAngleAttr.setX(idxHead, c.angle);
            
            // Размер головы растет при блюре (эффект боке)
            let size = 60.0 + (blurLevel * 100.0);
            headSizeAttr.setX(idxHead, size);
            
            // Альфа головы чуть выше хвоста
            headAlphaAttr.setX(idxHead, baseAlpha);

            needsUpdate = true;
        });

        if (needsUpdate) {
            linePosAttr.needsUpdate = true;
            lineColAttr.needsUpdate = true;
            
            headPosAttr.needsUpdate = true;
            headSizeAttr.needsUpdate = true;
            headColAttr.needsUpdate = true;
            headAlphaAttr.needsUpdate = true;
            headAngleAttr.needsUpdate = true;
        }
    }
}

// Инициализация
const slowComet = new SlowCometSystem(scene);

// 2. Система Комет (Падающие звезды)
class CometSystem {
    constructor(scene) {
        const geometry = new THREE.BufferGeometry();
        // 2 точки: Хвост и Голова
        const positions = new Float32Array(6); 
        const colors = new Float32Array(8); // r,g,b,a для 2 точек
        
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 4));

        this.material = new THREE.LineBasicMaterial({
            vertexColors: true,
            transparent: true,
            blending: THREE.AdditiveBlending,
            opacity: 0,
            linewidth: 1 // WebGL часто игнорирует это, но оставим
        });

        this.mesh = new THREE.Line(geometry, this.material);
        this.mesh.frustumCulled = false;
        scene.add(this.mesh);

        this.active = false;
        this.velocity = new THREE.Vector3();
        this.life = 0;
        this.maxLife = 0;
        
        // Палитра: Белый, Желтый, Оранжевый, Голубой, Фиолетовый
        this.palette = [
            new THREE.Color('#ffffff'),
            new THREE.Color('#ffcc00'), // Желтый
            new THREE.Color('#ff6600'), // Оранжевый
            new THREE.Color('#00ccff'), // Лазурный
            new THREE.Color('#9933ff')  // Фиолетовый
        ];
    }

    spawn(cameraPos) {
        if (this.active) return;

        // Позиция спавна
        const offset = new THREE.Vector3(
            (Math.random() - 0.5) * 2500,
            1000 + Math.random() * 800,
            (Math.random() - 0.5) * 1500 - 500
        );
        const startPos = new THREE.Vector3().copy(cameraPos).add(offset);
        
        // Характеристики
        const isSmall = Math.random() > 0.3; // 70% мелких, 30% крупных
        const speedMult = isSmall ? 1.5 : 1.0;
        
        this.velocity.set(
            (Math.random() - 0.5) * 40 * speedMult, 
            -(Math.random() * 25 + 35) * speedMult, // Быстро вниз
            (Math.random() - 0.5) * 15
        );

        // Цвет
        const color = this.palette[Math.floor(Math.random() * this.palette.length)];
        const colAttr = this.mesh.geometry.attributes.color;
        
        // Голова яркая, хвост прозрачный того же цвета
        // Tail (index 0)
        colAttr.setXYZW(0, color.r, color.g, color.b, 0.0);
        // Head (index 1)
        colAttr.setXYZW(1, color.r, color.g, color.b, isSmall ? 0.8 : 1.0);
        colAttr.needsUpdate = true;

        // Установка начальной позиции
        const posAttr = this.mesh.geometry.attributes.position;
        posAttr.setXYZ(0, startPos.x, startPos.y, startPos.z);
        posAttr.setXYZ(1, startPos.x, startPos.y, startPos.z);
        posAttr.needsUpdate = true;

        this.life = 0;
        this.maxLife = 50 + Math.random() * 40; 
        this.material.opacity = 1;
        this.active = true;
    }

    update(cameraPos) {
        // Увеличен шанс спавна: 0.003 -> 0.02 (в ~7 раз чаще)
        if (!this.active) {
            if (Math.random() < CONFIG.sky.cometFreq) { 
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

        const posAttr = this.mesh.geometry.attributes.position;
        const headX = posAttr.getX(1);
        const headY = posAttr.getY(1);
        const headZ = posAttr.getZ(1);

        const newHeadX = headX + this.velocity.x;
        const newHeadY = headY + this.velocity.y;
        const newHeadZ = headZ + this.velocity.z;

        // Хвост длиннее
        const tailLen = 20.0; 
        const tailX = newHeadX - this.velocity.x * tailLen;
        const tailY = newHeadY - this.velocity.y * tailLen;
        const tailZ = newHeadZ - this.velocity.z * tailLen;

        posAttr.setXYZ(0, tailX, tailY, tailZ);
        posAttr.setXYZ(1, newHeadX, newHeadY, newHeadZ);
        posAttr.needsUpdate = true;

        if (this.life > this.maxLife - 15) {
            this.material.opacity = (this.maxLife - this.life) / 15;
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
    activeLoads: 0,
    occupied: [],
    // НОВОЕ: Карта активных контроллеров отмены { postId: AbortController }
    activeControllers: new Map() 
};

// Максимальная дистанция для загрузки (чуть больше дальности видимости)
const MAX_LOAD_DIST = 2000;

function processLoadQueue() {
    // 1. ОЧИСТКА ОЧЕРЕДИ ОТ ДАЛЕКИХ ЗАДАЧ
    // Если пользователь улетел, убираем задачи из очереди ДО того, как они начнутся


    if (state.activeLoads >= MAX_CONCURRENT_LOADS || state.loadQueue.length === 0) return;

    // --- ЛОГИКА ПРИОРИТЕТОВ (сохранена как была) ---
    camera.updateMatrixWorld();
    const projScreenMatrix = new THREE.Matrix4();
    projScreenMatrix.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
    const frustum = new THREE.Frustum();
    frustum.setFromProjectionMatrix(projScreenMatrix);

    const cameraDir = new THREE.Vector3();
    camera.getWorldDirection(cameraDir); 
    const cameraPos = camera.position;

    const mappedQueue = state.loadQueue.map((item, index) => {
        const pos = new THREE.Vector3(item.pos[0], item.pos[1], item.pos[2]);
        const dist = pos.distanceTo(cameraPos);
        const isVisible = frustum.intersectsSphere(new THREE.Sphere(pos, 400));
        let score = isVisible ? dist : (cameraDir.dot(new THREE.Vector3().subVectors(pos, cameraPos).normalize()) > 0.4 ? 100000 + dist : 200000 + dist);
        return { index, score };
    });

    mappedQueue.sort((a, b) => a.score - b.score);
    state.loadQueue = mappedQueue.map(el => state.loadQueue[el.index]);
    // ---------------------------

    const task = state.loadQueue.shift();
    state.activeLoads++;

    // Создаем контроллер отмены
    const controller = new AbortController();
    state.activeControllers.set(task.postId, controller);

    const urlParams = new URLSearchParams(window.location.search);
    const customChannel = urlParams.get('channel_id');
    const channelParam = customChannel ? `&channel_id=${customChannel}` : '';

    // Передаем signal в fetch
    fetch(`/api/anemone/resolve_image?post_id=${task.postId}${channelParam}`, { signal: controller.signal })
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
                task.onError();
            } else if (data.found && data.url) {
                const loader = new THREE.ImageLoader();
                loader.setCrossOrigin('anonymous');
                loader.load(
                    data.url,
                    (image) => {
                        // --- ГЕНЕРАЦИЯ ПОЛАРОИДА С ТЕКСТОМ ---
                        const canvas = document.createElement('canvas');
                        const ctx = canvas.getContext('2d');

                        const cardWidth = 512;
                        const borderSide = cardWidth * 0.05;
                        const borderTop = cardWidth * 0.05; 
                        const borderBottom = cardWidth * 0.25;
                        
                        const imgRatio = image.width / image.height;
                        const drawWidth = cardWidth - (borderSide * 2);
                        const drawHeight = drawWidth / imgRatio;

                        const cardHeight = borderTop + drawHeight + borderBottom;

                        canvas.width = cardWidth;
                        canvas.height = cardHeight;

                        // 1. Подложка
                        ctx.fillStyle = '#ffffff';
                        ctx.fillRect(0, 0, canvas.width, canvas.height);

                        // 2. Изображение
                        ctx.drawImage(image, borderSide, borderTop, drawWidth, drawHeight);

                        // 3. Дата
                        if (data.date) {
                            ctx.fillStyle = '#888888';
                            ctx.font = '500 14px "Helvetica Neue", Arial, sans-serif';
                            ctx.textAlign = 'left';
                            ctx.fillText(data.date, borderSide, borderTop + drawHeight + 30);
                        }

                        // 4. Подпись
                        if (data.caption) {
                            ctx.fillStyle = '#222222';
                            ctx.font = '400 16px "Helvetica Neue", Arial, sans-serif';
                            ctx.textAlign = 'left';
                            
                            const textX = borderSide;
                            let textY = borderTop + drawHeight + 55;
                            const maxWidth = cardWidth - (borderSide * 2);
                            const lineHeight = 20;

                            const words = data.caption.split(' ');
                            let line = '';
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
                                        line = line.trim() + '...';
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

                        const tex = new THREE.CanvasTexture(canvas);
                        const totalRatio = cardWidth / cardHeight;
                        task.onSuccess(tex, totalRatio);
                        cleanupTask();
                    },
                    undefined, 
                    () => { task.onError(); cleanupTask(); }
                );
            } else {
                task.onError();
                cleanupTask();
            }
        })
        .catch((err) => {
            // Если ошибка из-за Abort, ничего не делаем, просто чистим
            if (err.name === 'AbortError') {
                // console.log('Download aborted for', task.postId);
            } else {
                task.onError();
            }
            cleanupTask();
        });

    function cleanupTask() {
        state.activeControllers.delete(task.postId);
        state.activeLoads--;
        processLoadQueue();
    }
}
// 1. Изменяем queueImageLoad, чтобы принимать позицию (pos)
function queueImageLoad(postId, pos, onSuccess, onError) {
    // Сохраняем позицию объекта для расчета приоритета
    state.loadQueue.push({ postId, pos, onSuccess, onError });
    processLoadQueue();
}



// --- ОБНОВЛЕННАЯ ФУНКЦИЯ loadChunk ---
async function loadChunk(cx, cy, cz) {
    const key = `${cx},${cy},${cz}`;
    if (state.chunks.has(key)) return;
    
    const g = new THREE.Group();
    g.position.set(cx * CHUNK_SIZE, cy * CHUNK_SIZE, cz * CHUNK_SIZE);
    scene.add(g);
    state.chunks.set(key, { group: g });

    try {
        // 1. Получаем параметры из URL браузера
        const urlParams = new URLSearchParams(window.location.search);
        
        // Читаем channel_id (если нет, сервер использует дефолтный, но параметр можно не слать)
        // Но нам нужен max_id для генерации чисел
        const maxId = urlParams.get('max_id') || 150; // Дефолт 150, если в ссылке нет

        // 2. Передаем max_id в запрос чанка
        // Обратите внимание: channel_id тут не обязателен, 
        // так как чанк просто генерирует числа. Channel нужен при resolve_image.
        const res = await fetch(`/api/anemone/get_chunk?x=${cx}&y=${cy}&z=${cz}&max_id=${maxId}`);
        const data = await res.json();
        
        if (data.items) data.items.forEach(item => createHangingArt(g, item, key));
    } catch (e) {
        console.error(e);
    }
}


// --- ОПТИМИЗАЦИЯ: ОБЩИЕ РЕСУРСЫ ---

// 1. Настройка геометрии
// High Poly: 12x12 сегментов для красивого изгиба
const realisticPaperGeometry = new THREE.PlaneGeometry(1, 1, 12, 12);
realisticPaperGeometry.translate(0, -0.5, 0);
realisticPaperGeometry.computeBoundingSphere();
realisticPaperGeometry.boundingSphere.radius = 3.0;

// Low Poly: 1x1 сегмент (всего 2 треугольника) для производительности
const simplePaperGeometry = new THREE.PlaneGeometry(1, 1);
simplePaperGeometry.translate(0, -0.5, 0);
simplePaperGeometry.computeBoundingSphere();
simplePaperGeometry.boundingSphere.radius = 3.0;

// Текущая активная геометрия (по умолчанию реалистичная)
let currentPaperGeometry = realisticPaperGeometry;

// 2. Общая геометрия для веревки
const commonLineGeometry = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(0,0,0), 
    new THREE.Vector3(0, 3000, 0)
]);

// 3. Общие Uniforms (Добавлены uCamPos и uCamDir)
const globalUniforms = {
    uTime: { value: 0 },
    uWindSpeed: { value: CONFIG.wind.speed },
    uWindForce: { value: CONFIG.wind.force },
    uSwayAmp: { value: CONFIG.motion.swayAmp },
    uTwistAmp: { value: CONFIG.motion.twistAmp },
    uCamPos: { value: new THREE.Vector3() }, // <--- НОВОЕ
    uCamDir: { value: new THREE.Vector3() }  // <--- НОВОЕ
};

function createHangingArt(group, data, chunkKey) {
    const baseScale = data.scale[0] * 1.5; 
    const geometry = currentPaperGeometry;
    const phase = Math.random() * 10;
    const swaySpeed = 0.5 + Math.random() * 0.5;

    // --- УЛУЧШЕННАЯ ЛОГИКА ПРЕДОТВРАЩЕНИЯ НАЛОЖЕНИЯ ---
    // Вектор текущей позиции
    const pos = new THREE.Vector3(data.pos[0], data.pos[1] + (baseScale / 2), data.pos[2]);
    // Увеличили радиус для проверки (чтобы карточки отталкивались сильнее)
    const radius = baseScale * 1.2; 
    const minZGap = 60; // Увеличили зазор по глубине

    // Пытаемся найти свободное место (макс. 8 попыток)
    for (let i = 0; i < 8; i++) {
        let collision = false;
        for (const item of state.occupied) {
            // Быстрый отсев далеких
            if (Math.abs(item.x - pos.x) > radius * 2.5) continue;
            if (Math.abs(item.y - pos.y) > radius * 2.5) continue;

            const dx = pos.x - item.x;
            const dy = pos.y - item.y;
            const dz = pos.z - item.z;
            const distXY = Math.sqrt(dx*dx + dy*dy);

            // Если есть пересечение
            if (distXY < (radius + item.r) && Math.abs(dz) < minZGap) {
                collision = true;
                
                // Векторное отталкивание: толкаем ОТ центра соседней карточки
                // Если позиции совпадают идеально, добавляем случайность
                let angle = Math.atan2(dy, dx);
                if (distXY < 1.0) angle = Math.random() * Math.PI * 2;

                const pushDist = (radius + item.r) - distXY + 20; // Выталкиваем + буфер
                
                pos.x += Math.cos(angle) * pushDist;
                pos.y += Math.sin(angle) * pushDist;
                
                // И немного двигаем по Z, чтобы разнести слои
                pos.z += (dz >= 0 ? 1 : -1) * 30;
                
                // Добавляем микро-шум, чтобы не выстраивались в идеальные линии
                pos.x += (Math.random() - 0.5) * 10;
                pos.y += (Math.random() - 0.5) * 10;
                break; 
            }
        }
        if (!collision) break; 
    }

    state.occupied.push({ x: pos.x, y: pos.y, z: pos.z, r: radius, chunkKey: chunkKey });
    // ----------------------------------------

    const material = new THREE.ShaderMaterial({
        vertexShader: paperVertexShader,
        fragmentShader: paperFragmentShader,
        uniforms: {
            ...globalUniforms,
            map: { value: PLACEHOLDER_TEXTURE },
            hasTexture: { value: false },
            uColor: { value: new THREE.Color(0xffffff) },
            uSizeMult: { value: CONFIG.details.fireflySize }, // <--- ДОБАВИТЬ            
            uAspectRatio: { value: 1.0 },
            uPhase: { value: phase },
            uSwaySpeed: { value: swaySpeed },
            uImageScale: { value: new THREE.Vector2(1, 1) }
        },
        side: THREE.DoubleSide,
        transparent: true,
        depthWrite: false
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.renderOrder = 5;
    mesh.position.copy(pos);
    mesh.scale.set(baseScale, baseScale, baseScale); 
    mesh.frustumCulled = true; 

    const lineMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.3 });
    const line = new THREE.Line(commonLineGeometry, lineMat);
    mesh.add(line);

    group.add(mesh);

    queueImageLoad(data.post_id, data.pos, (tex, ratio) => {
        tex.minFilter = THREE.LinearFilter;
        tex.generateMipmaps = false;
        renderer.initTexture(tex); 
        
        material.uniforms.map.value = tex;
        material.uniforms.hasTexture.value = true;
        material.uniforms.uAspectRatio.value = ratio; 

        let scaleX = 1;
        let scaleY = 1;
        if (ratio > 1) { 
            scaleX = ratio;
        } else {
            scaleY = 1 / ratio;
        }
        material.uniforms.uImageScale.value.set(scaleX, scaleY);
        
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
    if(c) { 
        scene.remove(c.group); 
        state.chunks.delete(key);
        
        // Очищаем массив занятых позиций для этого чанка
        state.occupied = state.occupied.filter(item => item.chunkKey !== key);
    }
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
// --- УПРАВЛЕНИЕ КАМЕРОЙ ---

// Хелпер для проверки: кликнули ли мы по интерфейсу?
function isUIInteraction(e) {
    // Проверяем, находится ли цель клика внутри панели, кнопки или попапа цветовой палитры
    return e.target.closest('#settings-panel') || 
           e.target.closest('#settings-btn') || 
           e.target.closest('.custom-picker-popover');
}


let isTwoFingerTouch = false; 
let initialPinchDistance = 0;
const PINCH_SENSITIVITY = 5.0; // Чем больше число, тем резче зум

// Хелпер для расчета расстояния между двумя пальцами
function getPinchDistance(e) {
    const dx = e.touches[0].clientX - e.touches[1].clientX;
    const dy = e.touches[0].clientY - e.touches[1].clientY;
    return Math.sqrt(dx * dx + dy * dy);
}

// 2. Начало касания
window.addEventListener('touchstart', (e) => {
    // Если касание двумя пальцами — инициализируем щипок
    if (e.touches.length === 2) {
        isTwoFingerTouch = true;
        initialPinchDistance = getPinchDistance(e);
        // Блокируем стандартный зум браузера
        e.preventDefault(); 
    } else if (e.touches.length === 1) {
        // Логика для одного пальца (перемещение X/Y)
        if (isUIInteraction(e)) return;
        state.isDragging = true; 
        state.lastMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    }
}, { passive: false });

// 3. Движение пальцами
window.addEventListener('touchmove', (e) => {
    // ЛОГИКА ЩИПКА (ZOOM Z)
    if (isTwoFingerTouch && e.touches.length === 2) {
        const currentDistance = getPinchDistance(e);
        
        // Разница: положительная = отдаление, отрицательная = приближение
        const delta = initialPinchDistance - currentDistance;

        // Применяем к позиции камеры по Z
        state.targetPos.z += delta * PINCH_SENSITIVITY;

        // Обновляем "старое" расстояние для следующего кадра (чтобы движение было плавным)
        initialPinchDistance = currentDistance;
        
        e.preventDefault();
        return; // Выходим, чтобы не сработал драг по X/Y
    }

    // ЛОГИКА ДРАГА (PAN X/Y)
    if (state.isDragging && e.touches.length === 1) {
        e.preventDefault(); // Блокируем скролл страницы
        const dx = e.touches[0].clientX - state.lastMouse.x;
        const dy = e.touches[0].clientY - state.lastMouse.y;
        state.targetPos.x -= dx * 2.5; 
        state.targetPos.y += dy * 2.5;
        state.lastMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    }
}, { passive: false });

// 4. Окончание касания
window.addEventListener('touchend', (e) => {
    // Если пальцев стало меньше 2, выключаем режим щипка
    if (e.touches.length < 2) {
        isTwoFingerTouch = false;
    }
    // Если убрали все пальцы, выключаем драг
    if (e.touches.length === 0) {
        state.isDragging = false;
    }
});


window.addEventListener('mousedown', e => { 
    // Если клик по интерфейсу — выходим, не запуская драг
    if (isUIInteraction(e)) return;

    state.isDragging = true; 
    state.lastMouse = { x: e.clientX, y: e.clientY }; 
    document.body.style.cursor = 'grabbing'; 
});

window.addEventListener('mouseup', () => { 
    state.isDragging = false; 
    document.body.style.cursor = 'default'; 
});

window.addEventListener('mousemove', e => {
    if (!state.isDragging) return;
    const dx = e.clientX - state.lastMouse.x;
    const dy = e.clientY - state.lastMouse.y;
    state.targetPos.x -= dx * 2.5;
    state.targetPos.y += dy * 2.5; 
    state.lastMouse = { x: e.clientX, y: e.clientY };
});

window.addEventListener('wheel', e => { 
    // Если скроллим над меню настроек — камеру не зумим
    if (isUIInteraction(e)) return;
    
    state.targetPos.z += e.deltaY * 2.0;
}, { passive: false }); // passive: false позволяет при необходимости делать preventDefault, но тут не обязательно

window.addEventListener('touchstart', e => { 
    if (e.touches.length === 1) {
        // Если тач по интерфейсу — выходим
        if (isUIInteraction(e)) return;

        state.isDragging = true; 
        state.lastMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    } 
});

window.addEventListener('touchmove', e => { 
    // isDragging не будет true, если touchstart попал по UI, поэтому тут доп. проверка не обязательна,
    // но важна проверка isDragging
    if (state.isDragging && e.touches.length === 1) {
        e.preventDefault(); // Блокируем скролл страницы на мобильных
        const dx = e.touches[0].clientX - state.lastMouse.x;
        const dy = e.touches[0].clientY - state.lastMouse.y;
        state.targetPos.x -= dx * 2.5; 
        state.targetPos.y += dy * 2.5;
        state.lastMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    }
}, { passive: false });

window.addEventListener('touchend', () => state.isDragging = false);

// --- UI INTERACTION ---
const btn = document.getElementById('settings-btn');
const panel = document.getElementById('settings-panel');
let panelOpen = false;

btn.addEventListener('click', () => {
    panelOpen = !panelOpen;
    panel.classList.toggle('active', panelOpen);
    btn.classList.toggle('active', panelOpen);
    
    // Меняем иконку: Меню <-> Крестик
    if (panelOpen) {
        btn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
    } else {
        btn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M3 6h18M3 12h18M3 18h18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
    }
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
// --- НОВЫЕ СЛУШАТЕЛИ СОБЫТИЙ ---
// --- ЛОГИКА ПЕРЕКЛЮЧЕНИЯ ФИЗИКИ БУМАГИ ---
const physicsToggle = document.getElementById('physics-toggle');

if (physicsToggle) {
    physicsToggle.addEventListener('change', (e) => {
        const isHighQuality = e.target.checked;
        
        // 1. Меняем глобальную ссылку на геометрию для НОВЫХ объектов
        currentPaperGeometry = isHighQuality ? realisticPaperGeometry : simplePaperGeometry;
        
        // 2. Обновляем ВСЕ УЖЕ СУЩЕСТВУЮЩИЕ карточки на сцене
        state.chunks.forEach(chunk => {
            chunk.group.traverse(obj => {
                // Ищем меши карточек (они имеют specific shader material)
                if (obj.isMesh && obj.material && obj.material.uniforms && obj.material.uniforms.uImageScale) {
                    obj.geometry = currentPaperGeometry;
                }
            });
        });
        
        console.log(`Physics Mode: ${isHighQuality ? 'High (Segmented)' : 'Low (Simple)'}`);
    });
}
// Небо
document.getElementById('star-density').addEventListener('input', e => CONFIG.sky.starDensity = parseInt(e.target.value));
document.getElementById('star-size').addEventListener('input', e => CONFIG.sky.starSize = parseFloat(e.target.value));
document.getElementById('sky-blur').addEventListener('input', e => CONFIG.sky.blur = parseFloat(e.target.value));

// Кометы
document.getElementById('comet-freq').addEventListener('input', e => CONFIG.sky.cometFreq = parseFloat(e.target.value));
document.getElementById('slow-comet-freq').addEventListener('input', e => CONFIG.sky.slowCometFreq = parseFloat(e.target.value));

// Частицы
document.getElementById('dust-count').addEventListener('input', e => CONFIG.details.dustCount = parseInt(e.target.value));
document.getElementById('dust-size').addEventListener('input', e => CONFIG.details.dustSize = parseFloat(e.target.value));

// Светлячки
document.getElementById('firefly-count').addEventListener('input', e => CONFIG.details.fireflyCount = parseInt(e.target.value));
document.getElementById('firefly-size').addEventListener('input', e => CONFIG.details.fireflySize = parseFloat(e.target.value));
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

// --- FILM GRAIN GENERATOR ---
function generateNoiseTexture() {
    const canvas = document.createElement('canvas');
    const size = 512;
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');
    
    // Заливаем прозрачным
    ctx.clearRect(0, 0, size, size);
    
    // Генерируем цветной шум (более кинематографично, чем ч/б)
    const imgData = ctx.createImageData(size, size);
    const data = imgData.data;
    
    for (let i = 0; i < data.length; i += 4) {
        // Серый шум с легким цветовым отклонением
        const gray = Math.random() * 255;
        data[i] = gray + (Math.random() - 0.5) * 20;     // R
        data[i+1] = gray + (Math.random() - 0.5) * 20;   // G
        data[i+2] = gray + (Math.random() - 0.5) * 20;   // B
        data[i+3] = 100 + Math.random() * 100;           // Alpha (100-200)
    }
    
    ctx.putImageData(imgData, 0, 0);
    return canvas.toDataURL();
}

// Инициализация шума
const grainEl = document.getElementById('film-grain');
if (grainEl) {
    grainEl.style.backgroundImage = `url(${generateNoiseTexture()})`;
}

// Слушатели событий для шума
const grainToggle = document.getElementById('grain-toggle');
const grainOpacity = document.getElementById('grain-opacity');

if (grainToggle && grainEl) {
    grainToggle.addEventListener('change', (e) => {
        grainEl.style.display = e.target.checked ? 'block' : 'none';
    });
}

if (grainOpacity && grainEl) {
    grainOpacity.addEventListener('input', (e) => {
        grainEl.style.opacity = e.target.value;
    });
}


const clock = new THREE.Clock();
let frameCount = 0; // <--- 1. ОБЪЯВЛЯЕМ ПЕРЕМЕННУЮ ЗДЕСЬ

function animate() {
    requestAnimationFrame(animate);
    
    frameCount++; // <--- 2. УВЕЛИЧИВАЕМ СЧЕТЧИК КАДРОВ

    // НОВОЕ: Проверка активных загрузок на дальность
    if (state.activeLoads > 0 && frameCount % 30 === 0) { // Теперь frameCount существует
        const camPos = camera.position;
        // Логика очистки (если нужна)
    }

    // УДАЛЕНО: Второй вызов requestAnimationFrame(animate); (он был лишним и вызывал бы лаги)
    
    const dt = clock.getDelta();
    const time = clock.getElapsedTime();

    // Плавное движение камеры
    state.currentPos.lerp(state.targetPos, 0.08);
    camera.position.copy(state.currentPos);
    
    // Обновление чанков (загрузка/выгрузка)
    updateChunks();
    starSystem.geometry.setDrawRange(0, CONFIG.sky.starDensity);
    starMat.uniforms.uBlur.value = CONFIG.sky.blur;
    starMat.uniforms.uSizeMult.value = CONFIG.sky.starSize;
    // --- ОБНОВЛЕНИЕ ЗВЕЗД И КОМЕТ ---
    starMat.uniforms.uTime.value = time;       
    
    // ПРИВЯЗКА К КАМЕРЕ (Эффект бесконечности)
    starSystem.position.copy(camera.position); 
    
    // Привязываем фоновые кометы к камере, чтобы не было параллакса
    slowComet.lines.position.copy(camera.position);
    slowComet.heads.position.copy(camera.position);
    
    // Логика обычных падающих комет (они остаются в мире, параллакс нужен)
    comet.update(camera.position);             

    // Обновление фоновых комет (убрали cameraPos из аргументов)
    slowComet.update(CONFIG.sky.blur);
    // Обновление глобальных Uniforms
    dustMat.uniforms.uCamPos.value.copy(camera.position);
    dustMat.uniforms.uTime.value = time;

    // 3. Частицы и Светлячки: Обновляем кол-во и размер
    dustSystem.geometry.setDrawRange(0, CONFIG.details.dustCount);
    dustMat.uniforms.uSizeMult.value = CONFIG.details.dustSize;

    fireflySystem.geometry.setDrawRange(0, CONFIG.details.fireflyCount);
    fireflyMat.uniforms.uSizeMult.value = CONFIG.details.fireflySize;


    fireflyMat.uniforms.uCamPos.value.copy(camera.position);
    fireflyMat.uniforms.uTime.value = time;

    globalUniforms.uTime.value = time;
    globalUniforms.uWindSpeed.value = CONFIG.wind.speed;
    globalUniforms.uWindForce.value = CONFIG.wind.force;
    
    // --- НОВОЕ: Обновляем данные камеры для шейдеров ---
    // Это позволяет менять цвет процентов в реальном времени при повороте камеры
    globalUniforms.uCamPos.value.copy(camera.position);
    
    // Получаем направление взгляда камеры
    const camDir = new THREE.Vector3();
    camera.getWorldDirection(camDir);
    globalUniforms.uCamDir.value.copy(camDir);

    // --- ДОБАВИТЬ ЭТОТ БЛОК (для частиц - без изменений, просто контекст) ---
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
    
    // --- ДОБАВИТЬ ЭТУ СТРОКУ ---
    starMat.uniforms.uResolution.value.set(window.innerWidth, window.innerHeight);
    
    fireflyMat.uniforms.uScale.value = window.innerHeight / 2.0;
    dustMat.uniforms.uScale.value = window.innerHeight / 2.0; 
});

