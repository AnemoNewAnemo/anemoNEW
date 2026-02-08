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
    },
    ui: {
        showDistance: true,
        showChaos: false
    },
    chaos: {
        radius: 4000 
    },
    // ОБНОВЛЕННАЯ СЕКЦИЯ СОЗВЕЗДИЙ
    constellation: {
        color: new THREE.Color('#ff5e00'), // Насыщенно оранжевый
        dotSize: 4.0,                      // Близко к максимуму
        lineWidth: 0.5,                    // Минимальный
        glowStr: 0.0                       // Свечение выключено по умолчанию
    }
};






function seededRandom(seed) {
    let t = seed += 0x6D2B79F5;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}

// Хелпер для получения числового сида из строки (для ID объекта)
function cyrb128(str) {
    let h1 = 1779033703, h2 = 3144134277,
        h3 = 1013904242, h4 = 2773480762;
    for (let i = 0, k; i < str.length; i++) {
        k = str.charCodeAt(i);
        h1 = h2 ^ Math.imul(h1 ^ k, 597399067);
        h2 = h3 ^ Math.imul(h2 ^ k, 2869860233);
        h3 = h4 ^ Math.imul(h3 ^ k, 951274213);
        h4 = h1 ^ Math.imul(h4 ^ k, 2716044179);
    }
    h1 = Math.imul(h3 ^ (h1 >>> 18), 597399067);
    h2 = Math.imul(h4 ^ (h2 >>> 22), 2869860233);
    h3 = Math.imul(h1 ^ (h3 >>> 17), 951274213);
    h4 = Math.imul(h2 ^ (h4 >>> 19), 2716044179);
    return (h1^h2^h3^h4) >>> 0;
}
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
const chaosGeo = new THREE.SphereGeometry(CONFIG.chaos.radius, 32, 16); 
const chaosMat = new THREE.MeshBasicMaterial({ 
    color: 0x334455, 
    wireframe: true, 
    transparent: true, 
    opacity: 0.15,
    blending: THREE.AdditiveBlending
});
const chaosSphere = new THREE.Mesh(chaosGeo, chaosMat);
chaosSphere.visible = false; // По умолчанию скрыто
scene.add(chaosSphere);

// --- ОБЛАЧНЫЕ КОММЕНТАРИИ И ИНТЕРАКТИВ ---
const commentsGroup = new THREE.Group();
scene.add(commentsGroup);
let commentsData = []; // Хранит данные для списка
let navigationTarget = null; // Текущая цель (Vector3)

// --- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ДЛЯ СОЗВЕЗДИЙ ---
const selectedComments = new Set(); // Хранит ID выбранных комментариев
let constellationGroup = new THREE.Group();
scene.add(constellationGroup);


// 1. Шейдер для Точек (Светящаяся звезда с белым ядром)
const constellationDotMat = new THREE.ShaderMaterial({
    uniforms: {
        uColor: { value: CONFIG.constellation.color },
        uSize: { value: CONFIG.constellation.dotSize * 30.0 },
        uGlowStr: { value: 1.0 },
        uScale: { value: window.innerHeight }
    },
    vertexShader: `
        uniform float uSize;
        uniform float uScale;
        void main() {
            vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
            gl_Position = projectionMatrix * mvPosition;
            gl_PointSize = uSize * (uScale / -mvPosition.z);
        }
    `,
    fragmentShader: `
        uniform vec3 uColor;
        uniform float uGlowStr;
        void main() {
            vec2 uv = gl_PointCoord - vec2(0.5);
            float dist = length(uv);
            if (dist > 0.5) discard;

            // Мягкое падение яркости для гало
            float strength = 1.0 - (dist * 2.0);
            strength = pow(strength, 2.0); // Делаем край более резким для "неонового" вида

            // Белое ядро (core) теперь меньше и добавляется, а не замещает цвет
            float core = smoothstep(0.0, 0.15, strength);
            
            // Основной цвет умножаем (overdrive), чтобы он "горел"
            vec3 finalColor = uColor * 1.5; 
            
            // Добавляем белое ядро поверх (аддитивно)
            finalColor += vec3(1.0) * core * 0.6;

            gl_FragColor = vec4(finalColor, strength * uGlowStr);
        }
    `,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthTest: false,
    depthWrite: false
});
// 2. Материал для Линий
// Примечание: Толщина линий > 1px в WebGL на Windows не поддерживается нативно.
// Чтобы линии были ярче, мы используем AdditiveBlending и opacity.
const constellationTubeMat = new THREE.ShaderMaterial({
    uniforms: {
        uColor: { value: CONFIG.constellation.color },
        uOpacity: { value: 0.8 },
        uGlowStr: { value: CONFIG.constellation.glowStr } // Управляется слайдером "Свечение линий"
    },
    vertexShader: `
        varying vec3 vNormal;
        varying vec3 vViewDir;
        
        void main() {
            vNormal = normalize(normalMatrix * normal);
            vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
            vViewDir = normalize(-mvPosition.xyz);
            gl_Position = projectionMatrix * mvPosition;
        }
    `,
    fragmentShader: `
        uniform vec3 uColor;
        uniform float uOpacity;
        uniform float uGlowStr;
        
        varying vec3 vNormal;
        varying vec3 vViewDir;

        void main() {
            // Расчет Френеля (1.0 в центре линии, 0.0 на краях)
            float fresnel = dot(vNormal, vViewDir);
            fresnel = clamp(fresnel, 0.0, 1.0);

            // 1. ЯДРО (Белая горячая линия внутри)
            // Чем выше степень, тем тоньше белый центр
            float core = pow(fresnel, 6.0);
            vec3 coreColor = vec3(1.0) * core * 0.8;

            // 2. СВЕЧЕНИЕ (Ореол)
            // Инвертируем френель: свечение идет по краям трубки
            float glowFactor = 1.0 - fresnel;
            // Делаем спад мягким
            glowFactor = pow(glowFactor, 2.0);
            
            // Итоговый цвет: Цвет линии + Белое ядро + Дополнительное свечение от слайдера
            vec3 finalColor = (uColor * fresnel * uOpacity) + coreColor;
            finalColor += uColor * glowFactor * uGlowStr * 5.0; // * 5.0 для усиления эффекта

            // Альфа: Прозрачность зависит от угла обзора и силы свечения
            float alpha = (uOpacity * fresnel) + (glowFactor * uGlowStr);

            gl_FragColor = vec4(finalColor, clamp(alpha, 0.0, 1.0));
        }
    `,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthTest: false,
    depthWrite: false,
    side: THREE.DoubleSide
});
// ФУНКЦИЯ ОТРИСОВКИ СОЗВЕЗДИЙ
// ФУНКЦИЯ ОТРИСОВКИ СОЗВЕЗДИЙ
function updateConstellationVisuals() {
    // 1. Очистка старой геометрии
    while(constellationGroup.children.length > 0){ 
        const obj = constellationGroup.children[0];
        if(obj.geometry) obj.geometry.dispose();
        constellationGroup.remove(obj); 
    }

    if (selectedComments.size === 0) return;

    // 2. Сбор позиций выбранных комментариев
    const selectedPoints = [];
    commentsData.forEach(c => {
        if (selectedComments.has(c.id)) {
            selectedPoints.push(new THREE.Vector3(c.pos.x, c.pos.y, c.pos.z));
        }
    });

    if (selectedPoints.length === 0) return;

    // 3. Рисуем точки (звёзды)
    const dotGeo = new THREE.BufferGeometry().setFromPoints(selectedPoints);
    const dots = new THREE.Points(dotGeo, constellationDotMat);
    dots.renderOrder = 999;
    constellationGroup.add(dots);

    // 4. Рисуем строгие линии (отдельные цилиндры)
    if (selectedPoints.length > 1) {
        const radius = CONFIG.constellation.lineWidth * 2.0;

        // Создаем общую геометрию. 
        // CylinderGeometry по умолчанию вертикальная (вдоль Y).
        // Поворачиваем её на 90 градусов по X, чтобы она легла вдоль Z.
        // Это нужно для корректной работы метода lookAt (который направляет ось Z на цель).
        const geometry = new THREE.CylinderGeometry(radius, radius, 1, 8, 1, true);
        geometry.rotateX(Math.PI / 2); 

        for (let i = 0; i < selectedPoints.length; i++) {
            const startPoint = selectedPoints[i];
            // Замыкаем последнюю точку с первой: (i + 1) % length
            const endPoint = selectedPoints[(i + 1) % selectedPoints.length];
            
            const distance = startPoint.distanceTo(endPoint);
            
            // Создаем меш для одной линии
            const lineMesh = new THREE.Mesh(geometry, constellationTubeMat);
            
            // 1. Позиция: середина между двумя звездами
            const midPoint = new THREE.Vector3().addVectors(startPoint, endPoint).multiplyScalar(0.5);
            lineMesh.position.copy(midPoint);
            
            // 2. Ориентация: смотрим на конечную точку
            lineMesh.lookAt(endPoint);
            
            // 3. Масштаб: растягиваем по оси Z (длина линии)
            // X и Y остаются 1, так как толщину мы задали в радиусе цилиндра
            lineMesh.scale.set(1, 1, distance);

            lineMesh.renderOrder = 998;
            constellationGroup.add(lineMesh);
        }
    }
}
function createTextTexture(text) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    /* ================== 1. НАСТРОЙКИ ================== */
    const fontSize = 32; 
    const font = `bold ${fontSize}px "Courier New", monospace`;
    const lineHeight = fontSize * 1.15; // Межстрочный интервал
    
    // --- НАСТРОЙКА ОТСТУПОВ ---
    // Было 30, стало 45 (горизонталь) и 55 (вертикаль). 
    // Это ~1.5 ширины символа, что дает комфортный "воздух".
    const paddingX = 85; 
    const paddingY = 105;
    
    // Размеры оригинального SVG (для пропорций ушей)
    const originalW = 430;
    const originalH = 308;
    const earHeight = 73; // Высота зоны ушей
    const bottomCurveH = 72; // Высота нижнего скругления
    
    // Минимальная ширина, чтобы уши не наехали друг на друга
    const leftEarWidth = 117; 
    const rightEarWidth = 110;
    const minBodyWidth = leftEarWidth + rightEarWidth + 20;

    ctx.font = font;

    /* ================== 2. РАСЧЕТ РАЗМЕРОВ ================== */
    const lines = text.split('\n');
    let maxTextWidth = 0;
    
    // Ищем самую широкую строку
    for (const line of lines) {
        const metrics = ctx.measureText(line);
        maxTextWidth = Math.max(maxTextWidth, Math.ceil(metrics.width));
    }

    // 1. Считаем ширину контента (Текст + Отступы слева и справа)
    let contentWidth = maxTextWidth + (paddingX * 2);
    // Если текст слишком короткий, расширяем до минимума для ушей
    if (contentWidth < minBodyWidth) {
        contentWidth = minBodyWidth;
    }

    // 2. Считаем высоту контента (Блок текста + Отступы сверху и снизу)
    const textBlockHeight = lines.length * lineHeight;
    // Высота "тела" (белой части без ушей)
    let bodyHeight = textBlockHeight + (paddingY * 2);
    
    // Минимальная высота тела (чтобы не было сплюснутым, если 1 строка)
    const minBodyHeight = originalH - earHeight;
    if (bodyHeight < minBodyHeight) {
        bodyHeight = minBodyHeight;
    }

    // Итоговые размеры канваса
    const W = Math.ceil(contentWidth);
    const H = Math.ceil(bodyHeight + earHeight);

    canvas.width = W;
    canvas.height = H;
    
    // Восстанавливаем шрифт после ресайза канваса
    ctx.font = font; 

    /* ================== 3. РИСОВАНИЕ ПУЗЫРЯ ================== */
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "rgba(255, 255, 255, 0.95)";
    
    ctx.beginPath();

    // -- Левая сторона --
    ctx.moveTo(0, H - bottomCurveH); 
    ctx.lineTo(0, 143.1); 

    // -- Левое ухо --
    ctx.bezierCurveTo(2.31, 86.8, 31.18, -8.54, 56, 0.1);
    ctx.bezierCurveTo(60.66, 2.79, 68.43, 8.52, 81.60, 25.86);
    ctx.bezierCurveTo(90.84, 38.01, 106.96, 61.95, 116.1, 73.1);

    // -- Верхняя линия (соединение ушей) --
    // Рисуем линию до начала правого уха
    const rightEarStart = W - 110; 
    ctx.lineTo(rightEarStart, 72.1);

    // -- Правое ухо (адаптивное) --
    // Координаты смещены относительно правого края W
    ctx.bezierCurveTo(W-99, 72.1, W-88, 38.1, W-80, 24);
    ctx.bezierCurveTo(W-68, 6.6, W-62, -1.7, W-46, 2);
    ctx.bezierCurveTo(W-20, 8.0, W-0.1, 116.1, W, 131.9);
    ctx.bezierCurveTo(W, 135.8, W, 139.9, W, 143.1);

    // -- Правая сторона --
    ctx.lineTo(W, H - bottomCurveH);

    // -- Нижний правый угол --
    ctx.bezierCurveTo(W, H - 32.3, W - 31.3, H, W - 71, H);

    // -- Нижняя линия --
    ctx.lineTo(71.1, H);

    // -- Нижний левый угол --
    ctx.bezierCurveTo(32.2, H, 0, H - 32.3, 0, H - bottomCurveH);

    ctx.closePath();
    ctx.fill();

    /* ================== 4. ОТРИСОВКА ТЕКСТА ================== */
    ctx.fillStyle = "#000";
    
    // Left align важен для ASCII, чтобы вертикальные линии рисунка совпадали
    ctx.textAlign = "left"; 
    ctx.textBaseline = "top"; 

    // --- Центрирование блока текста ---
    
    // 1. По вертикали:
    // Берем высоту тела (H - earHeight) и центрируем блок текста внутри него
    // startY начинается ПОСЛЕ ушей
    const bodyCenterY = earHeight + (bodyHeight / 2);
    const textStartY = bodyCenterY - (textBlockHeight / 2);

    // 2. По горизонтали:
    // (Ширина холста - Ширина самой длинной строки) / 2 = Отступ слева
    const textStartX = (W - maxTextWidth) / 2;

    lines.forEach((line, i) => {
        // Отрисовываем каждую строку с вычисленным отступом
        ctx.fillText(line, textStartX, textStartY + (i * lineHeight));
    });

    /* ================== 5. ЭКСПОРТ И ГЛАЗА ================== */
    const texture = new THREE.CanvasTexture(canvas);
    texture.minFilter = THREE.LinearFilter; 
    texture.magFilter = THREE.LinearFilter; 
    texture.needsUpdate = true;

    // Расчет UV для глаз
    // Глаза должны быть по центру белого "тела" по вертикали
    const uvY = 1.0 - (bodyCenterY / H);
    
    // По горизонтали фиксированный отступ от краев
    const eyeOffsetX = 65; 

    return {
        texture,
        aspect: W / H,
        leftEyeUV: new THREE.Vector2(eyeOffsetX / W, uvY),
        rightEyeUV: new THREE.Vector2((W - eyeOffsetX) / W, uvY)
    };
}
// 2. Добавление объекта на сцену (Кот с моргающими глазами)
function spawnCommentObject(id, text, x, y, z) {
    // Получаем текстуру и точные координаты глаз
    const { texture, aspect, leftEyeUV, rightEyeUV } = createTextTexture(text);
    
    const randomOffset = Math.random() * 100.0;

    const material = new THREE.ShaderMaterial({
        uniforms: {
            map: { value: texture },
            uAspect: { value: aspect }, // Аспект для правильной формы круга глаза
            uTime: globalUniforms.uTime,
            uOffset: { value: randomOffset },
            uLeftEye: { value: leftEyeUV },   // <--- Новое
            uRightEye: { value: rightEyeUV }, // <--- Новое
            uFogColor: { value: CONFIG.colors.bottom },
            uFogDensity: { value: 0.0015 }
        },
        vertexShader: `
            varying vec2 vUv;
            varying float vDist;
            void main() {
                vUv = uv;
                vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
                vDist = length(mvPosition.xyz);
                gl_Position = projectionMatrix * mvPosition;
            }
        `,
        fragmentShader: `
            uniform sampler2D map;
            uniform float uAspect;
            uniform float uTime;
            uniform float uOffset;
            uniform vec2 uLeftEye;  // Координаты центра левого глаза
            uniform vec2 uRightEye; // Координаты центра правого глаза
            
            uniform vec3 uFogColor;
            uniform float uFogDensity;
            
            varying vec2 vUv;
            varying float vDist;

            float eyeShape(vec2 uv, vec2 center, float radius) {
                vec2 d = uv - center;
                d.x *= uAspect; // Коррекция на соотношение сторон, чтобы круг был кругом
                return 1.0 - smoothstep(radius - 0.005, radius + 0.005, length(d));
            }

            void main() {
                vec4 texColor = texture2D(map, vUv);
                if (texColor.a < 0.1) discard;

                // Логика моргания
                float cycle = 15.0; // Длительность цикла (сек)
                float t = mod(uTime + uOffset, cycle);
                
                float eyesOpen = 0.0; // По умолчанию закрыты (спит)

                // Открывает глаза только на первые 3 секунды цикла
                if (t < 3.0) {
                    eyesOpen = 1.0; 
                    // Короткое моргание пока бодрствует (для живости)
                    if (t > 1.5 && t < 1.65) eyesOpen = 0.0; 
                }

                float eyeRadius = 0.025; // Размер глаза

                float left = eyeShape(vUv, uLeftEye, eyeRadius);
                float right = eyeShape(vUv, uRightEye, eyeRadius);
                
                float eyes = (left + right) * eyesOpen;

                // Рисуем глаза черным цветом (mix с исходным цветом)
                vec3 finalColor = mix(texColor.rgb, vec3(0.0), eyes);

                // Туман
                float fogFactor = 1.0 - exp( - vDist * vDist * uFogDensity * uFogDensity );
                gl_FragColor = vec4(mix(finalColor, uFogColor, fogFactor), texColor.a);
            }
        `,
        transparent: true,
        depthWrite: false
    });
    
    const sprite = new THREE.Sprite(material);
    const baseHeight = 60; // Немного увеличим базовый размер, так как текст мелкий
    
    sprite.scale.set(baseHeight * aspect, baseHeight, 1);
    sprite.position.set(x, y, z);
    sprite.renderOrder = 5; 
    
    sprite.userData = { id: id, text: text };
    
    commentsGroup.add(sprite);
    return sprite;
}
// 3. Загрузка комментариев при старте
function loadComments() {
    const urlParams = new URLSearchParams(window.location.search);
    const channelId = urlParams.get('channel_id') || 'default_world';

    fetch(`/api/anemone/get_comments?channel_id=${channelId}`)
        .then(r => r.json())
        .then(data => {
            commentsData = data;
            data.forEach(c => {
                spawnCommentObject(c.id, c.text, c.pos.x, c.pos.y, c.pos.z);
            });
            updateSearchList();
        })
        .catch(console.error);
}

// Запускаем загрузку сразу
loadComments();

// --- UI ЛОГИКА ---

// Открытие модалки создания
document.getElementById('add-btn').addEventListener('click', () => {
    document.getElementById('comment-modal').style.display = 'flex';
    document.getElementById('comment-text').focus();
});

document.getElementById('cancel-comment').addEventListener('click', () => {
    document.getElementById('comment-modal').style.display = 'none';
});

// Отправка нового комментария
document.getElementById('submit-comment').addEventListener('click', () => {
    const text = document.getElementById('comment-text').value;
    if (!text.trim()) return;

    // Рассчитываем позицию: 100 юнитов (1 метр условно) перед камерой
    const spawnDist = 300;
    const direction = new THREE.Vector3();
    camera.getWorldDirection(direction);
    
    const spawnPos = new THREE.Vector3().copy(camera.position).add(direction.multiplyScalar(spawnDist));

    // Сразу рисуем (оптимистичный UI)
    const tempId = 'temp_' + Date.now();
    spawnCommentObject(tempId, text, spawnPos.x, spawnPos.y, spawnPos.z);
    
    document.getElementById('comment-modal').style.display = 'none';
    document.getElementById('comment-text').value = '';

    // Отправляем на сервер
    const urlParams = new URLSearchParams(window.location.search);
    fetch('/api/anemone/add_comment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            channel_id: urlParams.get('channel_id'),
            text: text,
            x: spawnPos.x, y: spawnPos.y, z: spawnPos.z
        })
    }).then(r => r.json()).then(resp => {
        if(resp.status === 'success') {
            // Обновляем список для поиска
            commentsData.push(resp.data);
            updateSearchList();
        }
    });
});

// Логика списка поиска
const searchPanel = document.getElementById('search-panel');
document.getElementById('search-btn').addEventListener('click', () => {
    const isVisible = searchPanel.style.display === 'block';
    searchPanel.style.display = isVisible ? 'none' : 'block';
});

function updateSearchList() {
    const list = document.getElementById('search-list');
    list.innerHTML = '';
    
    if (commentsData.length === 0) {
        list.innerHTML = '<div style="padding:12px; color:#666;">Нет записей</div>';
        return;
    }

    // ИЗМЕНЕНИЕ: .slice().reverse() переворачивает копию массива (новые вверху)
    commentsData.slice().reverse().forEach(item => {
        const div = document.createElement('div');
        div.className = 'search-item';

        // Текстовая часть (клик - навигация)
        const textSpan = document.createElement('span');
        textSpan.className = 'search-text';
        const shortText = item.text.length > 25 ? item.text.substring(0, 25) + '...' : item.text;
        textSpan.innerText = shortText;
        
        // Чекбокс (клик - созвездие)
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'search-checkbox';
        checkbox.checked = selectedComments.has(item.id);
        
        // ЛОГИКА НАВИГАЦИИ (Повторный клик сбрасывает)
        textSpan.addEventListener('click', (e) => {
            e.stopPropagation(); // Чтобы не триггерить чекбокс, если вдруг вложенность изменится
            
            const targetVec = new THREE.Vector3(item.pos.x, item.pos.y, item.pos.z);
            
            // Если цель уже установлена и совпадает с текущей - сбрасываем
            if (navigationTarget && navigationTarget.equals(targetVec)) {
                navigationTarget = null;
                // Визуально можно показать, что сброшено (опционально)
            } else {
                navigationTarget = targetVec;
                searchPanel.style.display = 'none'; // Закрываем список при выборе
            }
        });

        // ЛОГИКА СОЗВЕЗДИЙ
        checkbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                selectedComments.add(item.id);
            } else {
                selectedComments.delete(item.id);
            }
            updateConstellationVisuals();
        });

        div.appendChild(textSpan);
        div.appendChild(checkbox);
        list.appendChild(div);
    });
}

// --- HUD НАВИГАЦИЯ (Внутри loop) ---
const hudArrow = document.getElementById('target-arrow');
const hudCrosshair = document.getElementById('target-crosshair');
const screenCenter = new THREE.Vector2(window.innerWidth / 2, window.innerHeight / 2);
// --- ВСТАВИТЬ ПОСЛЕ КОНФИГУРАЦИИ ---
// Добавляем стиль для текстовой подписи внутри стрелки навигации
const navStyle = document.createElement('style');
navStyle.innerHTML = `
    #target-arrow span {
        position: absolute;
        top: 50%;
        right: 40px; /* Выносим текст за пределы стрелки (влево) */
        transform: translateY(-50%) rotate(0deg) !important;
        color: white;
        font-family: monospace;
        font-size: 12px;
        text-shadow: 0 0 2px black;
        white-space: nowrap;
        pointer-events: none;
    }
    .arrow-back { filter: drop-shadow(0 0 5px red); border-bottom-color: #ff3333 !important; }
`;
document.head.appendChild(navStyle);
function updateNavigationHUD() {
    const label = document.getElementById('target-label');
    const hudArrow = document.getElementById('target-arrow');
    const hudCrosshair = document.getElementById('target-crosshair');
    
    // Скрываем всё, если цели нет
    if (!navigationTarget) {
        hudArrow.style.display = 'none';
        hudCrosshair.style.display = 'none';
        label.style.display = 'none';
        return;
    }

    // --- 1. Математика ---
    const camPos = camera.position;
    const camDir = new THREE.Vector3();
    camera.getWorldDirection(camDir);
    
    const toTarget = new THREE.Vector3().subVectors(navigationTarget, camPos);
    const distMeters = Math.round(toTarget.length());
    const dirToTargetNorm = toTarget.clone().normalize();
    
    // Проекция цели на экран
    const targetClone = navigationTarget.clone();
    targetClone.project(camera);
    
    const halfW = window.innerWidth / 2;
    const halfH = window.innerHeight / 2;
    const screenX = (targetClone.x * 0.5 + 0.5) * window.innerWidth;
    const screenY = (-targetClone.y * 0.5 + 0.5) * window.innerHeight;

    // --- 2. Логика состояний ---
    
    // Угол между взглядом и целью. Если > 0, цель спереди. Если < 0, цель сзади.
    const isFront = camDir.dot(dirToTargetNorm) > 0;
    
    // Цель на экране (с отступом)?
    const padding = 50;
    const isOnScreen = isFront && 
                       screenX > padding && screenX < window.innerWidth - padding && 
                       screenY > padding && screenY < window.innerHeight - padding;

    // Форматирование текста
    let distText = distMeters + 'm';
    if (distMeters >= 1000) distText = (distMeters / 1000).toFixed(1) + 'km';

    // Вектор от центра экрана к проекции цели (для вращения стрелки)
    let dirX = screenX - halfW;
    let dirY = screenY - halfH;

    // --- 3. Рендер сценариев ---

    // === СЦЕНАРИЙ А: ЦЕЛЬ СЗАДИ (Красное перекрестие + Красная стрелка) ===
    if (!isFront) {
        // 1. Показываем КРАСНОЕ перекрестие по центру
        hudCrosshair.style.display = 'block';
        hudCrosshair.className = 'crosshair-red';
        hudCrosshair.style.left = halfW + 'px';
        hudCrosshair.style.top = halfH + 'px';
        
        // Лейбл под перекрестием не показываем (он будет у стрелки)
        label.style.display = 'none';

        // 2. Показываем КРАСНУЮ стрелку
        hudArrow.style.display = 'block';
        hudArrow.className = 'arrow-red';
        
        // Инвертируем вектор (так как цель сзади, стрелка должна показывать "поворачивай туда")
        // Если цель сзади-справа, проекция может вести себя странно, поэтому просто инвертируем экранный вектор
        dirX = -dirX;
        dirY = -dirY;

        // Позиционируем стрелку по кругу
        positionArrow(hudArrow, dirX, dirY, halfW, halfH, distText);
    }
    
    // === СЦЕНАРИЙ Б: ЦЕЛЬ СПЕРЕДИ, НО ЗА ЭКРАНОМ (Желтая стрелка) ===
    else if (!isOnScreen) {
        // Скрываем перекрестие
        hudCrosshair.style.display = 'none';
        label.style.display = 'none';

        // Показываем ЖЕЛТУЮ стрелку
        hudArrow.style.display = 'block';
        hudArrow.className = 'arrow-yellow';

        // Позиционируем стрелку
        positionArrow(hudArrow, dirX, dirY, halfW, halfH, distText);
    }
    
    // === СЦЕНАРИЙ В: ЦЕЛЬ СПЕРЕДИ И НА ЭКРАНЕ (Желтое перекрестие) ===
    else {
        // Скрываем стрелку
        hudArrow.style.display = 'none';

        // Показываем ЖЕЛТОЕ перекрестие
        hudCrosshair.style.display = 'block';
        hudCrosshair.className = 'crosshair-yellow';
        
        // Двигаем перекрестие за целью
        hudCrosshair.style.left = screenX + 'px';
        hudCrosshair.style.top = screenY + 'px';

        // Показываем отдельный лейбл под перекрестием
        label.style.display = 'block';
        label.innerText = distText;
        label.style.left = screenX + 'px';
        label.style.top = (screenY + 30) + 'px';
        label.style.transform = 'translate(-50%, 0)'; // Центрируем текст
    }
}

// Вспомогательная функция для расчета позиции и вращения стрелки
function positionArrow(arrowEl, dx, dy, hw, hh, text) {
    const angle = Math.atan2(dy, dx);
    const radius = Math.min(hw, hh) - 80; // Отступ от края
    
    const arrowX = hw + Math.cos(angle) * radius;
    const arrowY = hh + Math.sin(angle) * radius;

    arrowEl.style.left = arrowX + 'px';
    arrowEl.style.top = arrowY + 'px';
    
    // Вращение: +90deg, т.к. CSS-стрелка смотрит вверх (border-bottom), 
    // а угол 0 - это вправо. Нужно согласовать.
    // Если CSS стрелка смотрит ВВЕРХ (border-bottom colored), то при угле 0 (вправо) она должна быть повернута на 90deg.
    const rotDeg = angle * (180 / Math.PI) + 90;
    
    arrowEl.style.transform = `translate(-50%, -50%) rotate(${rotDeg}deg)`;
    
    // Обновляем текст внутри стрелки
    // Мы ищем span внутри элемента arrowEl (в HTML это должно быть <div id="target-arrow"><span></span></div>)
    let span = arrowEl.querySelector('span');
    if (!span) {
        span = document.createElement('span');
        arrowEl.appendChild(span);
    }
    span.innerText = text;
    
    // Поворачиваем текст обратно, чтобы он всегда был горизонтально
    // Если сама стрелка повернута на X, текст поворачиваем на -X
    span.style.transform = `translateY(-50%) rotate(${-rotDeg}deg)`;
}

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


    if (state.activeLoads >= MAX_CONCURRENT_LOADS || state.loadQueue.length === 0) {
        if (state.loadQueue.length > 0 && state.activeLoads >= MAX_CONCURRENT_LOADS) {
            console.warn(`[QUEUE] STALLED? Active limit reached. Active: ${state.activeLoads}, Queue: ${state.loadQueue.length}`);
        }
        return;
    }

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
    
    const taskId = task.postId; // Для логов
    console.log(`[QUEUE] START Task ${taskId} | Active: ${state.activeLoads}`);

    const controller = new AbortController();
    state.activeControllers.set(task.postId, controller);

    const urlParams = new URLSearchParams(window.location.search);
    const customChannel = urlParams.get('channel_id');
    const channelParam = customChannel ? `&channel_id=${customChannel}` : '';

    // Передаем signal в fetch
fetch(`/api/anemone/resolve_image?post_id=${task.postId}${channelParam}`, { signal: controller.signal })
        .then(r => r.json())
        .then(data => {
            if (data.error === 'access_denied') {
                console.error(`[QUEUE] ERROR Access Denied for ${taskId}`);
                const modal = document.getElementById('error-modal');
                const chanSpan = document.getElementById('err-channel');
                if(modal && chanSpan) {
                    chanSpan.innerText = customChannel;
                    modal.style.display = 'flex';
                }
                task.onError();
                cleanupTask(); // <--- ОБЯЗАТЕЛЬНО ДОБАВИТЬ ЭТО!
                return; // Желательно выйти из функции
            } else if (data.found && data.url) {
                const loader = new THREE.ImageLoader();
                loader.setCrossOrigin('anonymous');
                loader.load(
                    data.url,
                    (image) => {
                        console.log(`[QUEUE] IMG LOADED ${taskId}`);
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
                    (err) => { 
                        console.error(`[QUEUE] IMG ERROR ${taskId}`, err);
                        task.onError(); 
                        cleanupTask(); 
                    }
                );
            } else {
                console.warn(`[QUEUE] NOT FOUND ${taskId}`);
                task.onError();
                cleanupTask();
            }
        })
        .catch((err) => {
            if (err.name === 'AbortError') {
                console.log(`[QUEUE] ABORTED ${taskId}`);
            } else {
                console.error(`[QUEUE] FETCH ERROR ${taskId}`, err);
                task.onError();
            }
            cleanupTask();
        });

    function cleanupTask() {
        console.log(`[QUEUE] FINISH Task ${taskId} | Active BEFORE: ${state.activeLoads}`);
        state.activeControllers.delete(task.postId);
        state.activeLoads--;
        console.log(`[QUEUE] FINISH Task ${taskId} | Active AFTER: ${state.activeLoads}`);
        
        // Защита от ухода в минус (на всякий случай)
        if (state.activeLoads < 0) {
             console.error('[QUEUE] CRITICAL: Active loads negative!');
             state.activeLoads = 0;
        }
        
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
        const maxId = urlParams.get('max_id') || 8509; // Дефолт 8509, если в ссылке нет

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

    // --- ИЗМЕНЕНИЕ 1: Генерируем уникальный сид для этого объекта ---
    // data.id приходит с сервера (вида "x_y_z_i"), он всегда одинаковый для объекта
    const objSeed = cyrb128(data.id || Math.random().toString()); 
    
    // Используем seededRandom вместо Math.random()
    const phase = seededRandom(objSeed) * 10;
    const swaySpeed = 0.5 + seededRandom(objSeed + 1) * 0.5; // +1 чтобы число отличалось от phase

    // Вектор текущей позиции
    const pos = new THREE.Vector3(data.pos[0], data.pos[1] + (baseScale / 2), data.pos[2]);
    const radius = baseScale * 1.2; 
    const minZGap = 60; 

    // Логика коллизий
    for (let i = 0; i < 8; i++) {
        let collision = false;
        for (const item of state.occupied) {
            // ... (код проверки дистанции тот же) ...
            if (Math.abs(item.x - pos.x) > radius * 2.5) continue;
            if (Math.abs(item.y - pos.y) > radius * 2.5) continue;

            const dx = pos.x - item.x;
            const dy = pos.y - item.y;
            const dz = pos.z - item.z;
            const distXY = Math.sqrt(dx*dx + dy*dy);

            if (distXY < (radius + item.r) && Math.abs(dz) < minZGap) {
                collision = true;
                
                let angle = Math.atan2(dy, dx);
                // --- ИЗМЕНЕНИЕ 2: Детерминированный угол ---
                if (distXY < 1.0) angle = seededRandom(objSeed + i * 100) * Math.PI * 2;

                const pushDist = (radius + item.r) - distXY + 20; 
                
                pos.x += Math.cos(angle) * pushDist;
                pos.y += Math.sin(angle) * pushDist;
                pos.z += (dz >= 0 ? 1 : -1) * 30;
                
                // --- ИЗМЕНЕНИЕ 3: Детерминированный микро-шум ---
                // Используем i в сиде, чтобы на каждой итерации цикла шум был разным, но повторяемым
                pos.x += (seededRandom(objSeed + i * 10) - 0.5) * 10;
                pos.y += (seededRandom(objSeed + i * 20) - 0.5) * 10;
                break; 
            }
        }
        if (!collision) break; 
    }

    state.occupied.push({ x: pos.x, y: pos.y, z: pos.z, r: radius, chunkKey: chunkKey });

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

// 1. Цвет (Обновляем оба материала)
document.getElementById('col-constellation').addEventListener('input', (e) => {
    const val = e.target.value;
    const col = new THREE.Color(val);
    CONFIG.constellation.color.set(col);
    
    // Обновляем униформы
    constellationDotMat.uniforms.uColor.value.copy(col);
    constellationTubeMat.uniforms.uColor.value.copy(col); // <-- Новое имя материала
});

// 2. Размер точек
document.getElementById('const-dot-size').addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    CONFIG.constellation.dotSize = val;
    constellationDotMat.uniforms.uSize.value = val * 60.0; 
});

// 3. Толщина линий (теперь перестраивает геометрию трубки)
document.getElementById('const-line-width').addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    CONFIG.constellation.lineWidth = val;
    
    // Просто вызываем перерисовку, чтобы TubeGeometry пересоздалась с новым радиусом
    updateConstellationVisuals();
});
// Слушатель для слайдера свечения
document.getElementById('const-glow-str').addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    CONFIG.constellation.glowStr = val;
    // Обновляем униформу материала
    if (constellationTubeMat.uniforms.uGlowStr) {
        constellationTubeMat.uniforms.uGlowStr.value = val;
    }
});

// Слушатель для кнопки возврата домой
document.getElementById('home-btn').addEventListener('click', () => {
    // Сбрасываем цель камеры на стартовую позицию (0, 0, 1000)
    // или ту, которая установлена в state.targetPos при инициализации
    state.targetPos.set(0, 0, 1000);
    
    // Опционально: сбросить навигационную цель
    navigationTarget = null;
    updateNavigationHUD(); // Обновить интерфейс, чтобы убрать стрелку
});


// UI Settings Listeners
document.getElementById('ui-dist-toggle').addEventListener('change', (e) => {
    CONFIG.ui.showDistance = e.target.checked;
});

document.getElementById('ui-chaos-toggle').addEventListener('change', (e) => {
    CONFIG.ui.showChaos = e.target.checked;
    chaosSphere.visible = e.target.checked;
});
// --- ИНТЕГРАЦИЯ COLOR PICKER ---
import { HexColorPicker } from 'https://unpkg.com/vanilla-colorful?module';

function setupColorPickers() {
    const inputs = [
        { id: 'col-bot', target: CONFIG.colors.bottom, cb: updateBackgroundGradient },
        { id: 'col-mid', target: CONFIG.colors.mid, cb: updateBackgroundGradient },
        { id: 'col-top', target: CONFIG.colors.top, cb: updateBackgroundGradient },
        { id: 'col-fire', target: null, cb: (hex) => fireflyMat.uniforms.color.value.set(hex) },
        { id: 'col-constellation', target: CONFIG.constellation.color, cb: (hex) => {
            constellationTubeMat.color.set(hex);
            constellationDotMat.color.set(hex);
        }},        
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
    if (constellationTubeMat) {
        const pulse = 0.7 + 0.3 * Math.sin(time * 3.0);
        constellationTubeMat.opacity = pulse;
        // Можно также слегка менять цвет, делая его ярче в пике (если нужно)
    }

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

    // Добавляем вызов навигации
    updateNavigationHUD();

    renderer.render(scene, camera);
}

animate();
setTimeout(() => document.getElementById('status').style.opacity = 0, 1000);
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth/window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    constellationDotMat.uniforms.uScale.value = window.innerHeight;    
    // --- ДОБАВИТЬ ЭТУ СТРОКУ ---
    starMat.uniforms.uResolution.value.set(window.innerWidth, window.innerHeight);
    
    fireflyMat.uniforms.uScale.value = window.innerHeight / 2.0;
    dustMat.uniforms.uScale.value = window.innerHeight / 2.0; 
});
