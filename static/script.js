import * as THREE from 'three';
import { initGallery } from './gallery.js'; // <-- Добавляем это
import { SolarSystemManager, SolarPreview } from './solar_module.js'; // <-- Добавили SolarPreview
import { PLANET_PRESETS } from './planetpresets.js';
import { VideoCaptureManager } from './video_module.js';
// --- КОНФИГУРАЦИЯ И СОСТОЯНИЕ (Глобальные настройки) ---
const CONFIG = {

    cards: {
        enabled: true, // <-- ДОБАВИТЬ СЮДА
        size: 1.5,
        heightOffset: 15.0,
        spacing: 1.0
    },

    colors: {
        bottom: new THREE.Color('#6cc1d4'), 
        mid: new THREE.Color('#284f6b'),    
        top: new THREE.Color('#050814'),    
        firefly: new THREE.Color('#ffaa00') 
    },
    graphics: {
        renderScale: 0.6,
        screenshotScale: 2.0,
        grainEnabled: true,
        grainOpacity: 0.03
    },
    wind: { speed: 0.4, force: 0.55 },
    particles: { speed: 0.4 },
    motion: { swayAmp: 0.34, twistAmp: 0.31 },
    sky: {
        starDensity: 8800,
        starSize: 1.0,
        blur: 0.0, // Эффект боке (0 - нет, 1 - макс)
        cometFreq: 0.007,     // Быстрые кометы
        slowCometFreq: 0.002 // Медленные фоновые кометы
    },
    details: {
        dustCount: 1700,
        dustSize: 0.8,
        fireflyCount: 360,
        fireflySize: 1.0
    },

    lighting: {
        globalIntensity: 1.0,  // Глобальная яркость сцены (1.0 = норма)
        maxPointLights: 15,    // Сколько всего источников обрабатывать одновременно
        lightDistance: 3200.0  // Дальше этого расстояния свет отключается
    },

    cometLights: {
        enabled: true,
        affectRocks: true,
        affectGrass: true,  
        intensity: 3.5,
        range: 150.0
    },

    clouds: {
        enabled: false,
        opacity: 0.8,
        coverage: 0.5,
        softness: 0.75,
        scale: 0.0004,
        stretch: 1.0,
        speed: 4.5,
        colorZenith: new THREE.Color('#ffffff'),
        colorHorizon: new THREE.Color('#ffeebb')
    },
    cloudShadows: {
        enabled: true,
        opacity: 0.55,
        coverage: 0.55,
        softness: 0.6,
        scale: 0.0027,
        stretch: 3.0,
        speed: 2.0,
        color: new THREE.Color('#050a10')
    },

    flashlight: {
        enabled: false,
        affectGrass: true,
        affectRocks: true, 
        color: new THREE.Color('#ffffff'),
        intensity: 3.0,
        range: 5300.0,
        focus: 0.47,   
        offset: -100.0,

        // НОВЫЕ ПАРАМЕТРЫ
        radius: 0.08,    // Радиус (ширина) пятна
        animAmp: 0.05,   // Амплитуда тряски/блуждания
        animSpeed: 0.4  // Скорость блуждания
    },
    sphereLights: {
        enabled: true,
        affectRocks: true,
        affectGrass: true, 
        intensity: 0.7,
        range: 700.0
    },

    rocks: {
        enabled: true,
        count: 1000,
        size: 4.0,
        sizeVar: 0.6,
        baseColor: new THREE.Color('#141436'), 
        tipColor: new THREE.Color('#94a5c2'),  

        crystalBaseColor: new THREE.Color('#152c38'),
        crystalTipColor: new THREE.Color('#5aaacf'),
        smoothness: 1.5,
        minHeight: -3.0,
        maxHeight: 250.0,
        boulderRatio: 0.11, 

        floatAmp: 0.0,
        floatSpeed: 1.0,
        
        // --- НОВЫЕ ПАРАМЕТРЫ МХА / СНЕГА ---
        mossSpread: 0.35,
        mossColor: new THREE.Color('#b6c6e3'),

        flatShading: 0.45,
        ao: 0.55,
        crystalGloss: 0.7,
        crystalAlpha: 0.1, 
        crystalRatioSmall: 0.0,    
        crystalRatioBoulder: 0.1,  
        
        // --- НОВЫЕ ПАРАМЕТРЫ ---
        heightBias: 0.5,           // Средняя высота (0.0 - плоские, 1.0 - высокие)
        crystalIrisSpread: 0.8,    // Разброс цвета фейковых отблесков
        crystalIrisIntensity: 1.25, // Прозрачность/Сила отблесков (0 - выкл)
        // -----------------------
        
        shapeSmall: 0.5,
        shapeBoulder: 0.75,
        struct: 1.2,
        thin: 0.15,

        drawDistance: 6000.0,
        yOffset: -7.0,  
        ySpread: 0.0,

        // --- НОВЫЕ НАСТРОЙКИ ПЕНЫ НА КАМНЯХ ---
        rockFoamOpacity: 0.15,      // Прозрачность пены на камнях (0 - выкл)
        rockFoamHeight: 10.0,       // Высота налипания пены на камни
        shape: 0.5
    },

    water: {
        reflections: true,

        reflectRocks: true,  
        reflectClouds: false, 
        resolution: 512,
        intensity: 0.4,
        distortion: 0.035,
        rippleStretch: 2.0,
        blurStrength: 0.0,
        edgeDarkening: 0.1,
        distBlurStart: 800.0,
        distBlurMax: 0.0,

        // --- НОВЫЕ ПАРАМЕТРЫ ПЕНЫ ---
        foamOpacity: 0.2,                         // 0 - выключено
        foamColor: new THREE.Color('#cad9ff'),    // Цвет пены
        foamWidth: 13.0,                          // Общая ширина зоны пены
        foamCount: 2.0,                           // Количество полосок (от 1 до 4)
        foamSpacing: 3.5, 
        foamNoise: 0.5,                            // Искажения/разрывы
        shoreOpacity: 0.6,
        shoreColor: new THREE.Color('#a4b7d9')
    },
    ui: {
        showDistance: false,
        showChaos: false,
        groundMode: true,
        autoLevel: false,
        showScreenshotBtn: true,
        maxCamHeight: 250.0
    },
    chaos: {
        radius: 4000 
    },
    terrain: {
        grassColor: new THREE.Color('#1f374f'), 
        waterColor: new THREE.Color('#7992c4'),
        deepWaterColor: new THREE.Color('#000000'), // <--- ЦВЕТ БЕЗДНЫ
        waterDepthFactor: 0.045,                     // <--- СКОРОСТЬ ЗАТЕМНЕНИЯ

        peakColor: new THREE.Color('#477496'),  
        fogColor: new THREE.Color('#475a6e'),   
        snowColor: new THREE.Color('#5400ff'),
        amplitude: 205.0,       
        frequency: 0.0011,      
        offset: 65.0,          
        sharpness: 1.5,        
        showGrid: false,        
        visibility: 4200.0,    
        fogDensity: 0.0017,    
        aoStrength: 0.3,
        smoothing: 0.41,
        strataEnabled: false,      // <--- СЛОИСТОСТЬ (КАНЬОНЫ)
        strataFreq: 0.5,           // Частота полос
        strataStrength: 0.45,       // Сила эффекта

        creepingFogEnabled: false,
        creepingFogColor: new THREE.Color('#73a5d1'), 
        creepingFogHeight: 8.0,     // Насколько поднят над водой базово
        creepingFogThickness: 45.0, // Толщина слоя
        creepingFogDensity: 1.8,    // Плотность (больше 1.0 = вата, меньше 1.0 = мягкое облако)
        creepingFogShape: 0.7       // Рваность краев (0 = овал, 1 = клочья)
    },       

    grass: {
        enabled: true,
        count: 110000,          
        shape1: 1.0,
        shape2: 0.0,
        shape3: 2.0,     
        shape4: 4.0,


        // --- НОВЫЕ ПАРАМЕТРЫ УНИКАЛЬНЫХ ФОРМ (x=Базовая, y=Форма2, z=Форма3, w=Форма4) ---
        shapeMods: {
            size: new THREE.Vector4(1.0, 1.0, 1.0, 1.0),      // Высота/Размер
            width: new THREE.Vector4(1.3, 1.0, 1.0, 1.0),     // Сплющить/Растянуть
            sizeVar: new THREE.Vector4(0.4, 0.4, 0.4, 0.4),   // Вариативность размера
            colorVar: new THREE.Vector4(0.3, 0.3, 0.3, 0.3),  // Вариативность цвета
            windDamp: new THREE.Vector4(0.0, 0.0, 0.0, 0.0)   
        },           

        // --- ВНУТРИ CONFIG.grass.farShapeMods ---
        farShapeMods: {
            size: new THREE.Vector4(1.0, 1.0, 1.0, 1.0),      // Высота/Размер для LOD
            width: new THREE.Vector4(1.3, 1.0, 1.0, 1.0),     // Сплющить/Растянуть для LOD
            windDamp: new THREE.Vector4(0.0, 0.5, 0.0, 0.0)   
        },
        mouseInteract: false,
        mouseRadius: 40.0,
        mouseStrength: 1.0, 
        cameraInteract: true,     // <--- НОВОЕ: Реакция на камеру
        cameraRadius: 85.0,       // <--- НОВОЕ: Радиус отталкивания от камеры
        lodOffset: 500.0,         // <--- НОВОЕ: Смещение старта LOD ближе к камере

        mixMode: 0.0,
        // НОВЫЕ РАЗДЕЛЬНЫЕ НАСТРОЙКИ (2, 3 и 4 формы)
        altChance2: 0.3, altChance3: 0.3, altChance4: 0.3,
        struct2: 0.5, struct3: 0.5, struct4: 0.5,

        thin2: 0.0, thin3: 0.0, thin4: 0.0,
        
        baseColor: new THREE.Color('#446a87'),
        tipColor: new THREE.Color('#97afcf'),
        baseColor2: new THREE.Color('#3f3a0a'),
        tipColor2: new THREE.Color('#a8b030'),
        baseColor3: new THREE.Color('#0a1f3f'),
        tipColor3: new THREE.Color('#3060b0'),
        baseColor4: new THREE.Color('#1f3f0a'),
        tipColor4: new THREE.Color('#ffffff'), 
        
        smoothness: 1.0,         
        minHeight: 10.0,          
        maxHeight: 100.0,         
        clusterFreq: 0.05,       
        clusterThreshold: 0.45,   
        colorVar: 0.3,
        sizeVar: 0.4,
        shapeVar: 0.0,
        height: 17.0,             
        bend: 0.4,               
        bendAngle: 3.1,      
        bendChaos: 0.0,           
        drawDistance: 1150.0,    
        fogDensityMult: 1.8,      
        
        // --- ОБНОВЛЕННАЯ ФИЗИКА ВЕТРА ---
        windSpeed: 1.5,       
        swayStrength: 0.4,   
        turbulence: 0.2,      // Сила волн
        turbAmp: 1.0,         // Длина волн (Растяжение)
        turbSpeed: 1.8,       // Скорость деформации
        gustStrength: 1.5,    // Сила прижатия
        gustSize: 140.0,       // Длительность прижатия (Как долго лежит)
        gustFreq: 0.85,        // НОВОЕ: Частота порывов
        gustSmoothness: 1.0,  // <--- НОВОЕ: Плавность входа/выхода из порыва
        gustArc: 0.05,         
        gustSpeed: 1.8,   
        windChaos: 0.5,       // Влияет на паузы (затишья) и частоту

        lodEnabled: true,
        farDistance: 8000.0,
        farCount: 50000,
        farSizeMult: 1.3,
        farMixMode: 0.0,      // 0 = как спереди, 1 = микс 2 форм, 2 = микс 3 форм
        farShape1: 1.0, farShape2: 3.0, farShape3: 8.0,
        
        // НОВЫЕ РАЗДЕЛЬНЫЕ НАСТРОЙКИ ФОНА
        farAltChance2: 0.6, farAltChance3: 0.2,
        farStruct2: 0.5, farStruct3: 0.5,
        farThin2: 0.0, farThin3: 0.0
    },


    // ОБНОВЛЕННАЯ СЕКЦИЯ СОЗВЕЗДИЙ
    constellation: {
        color: new THREE.Color('#ff5e00'), // Насыщенно оранжевый
        dotSize: 4.0,                      // Близко к максимуму
        lineWidth: 0.5,                    // Минимальный
        glowStr: 0.0                       // Свечение выключено по умолчанию
    },
    spheres: {
        count: 7,            
        baseSize: 31.0,     
        moveSpeed: 1.8,      
        speed: 0.2,          
        colors: [            
            new THREE.Color('#ff0055'),
            new THREE.Color('#00ccff'),
            new THREE.Color('#ffcc00') 
        ],
        trailCount: 300,    
        trailSize: 5.0,     
        trailBlur: 0.1,      
        trailOpacity: 0.85,
        trailLength: 2.6,    // Дальность отлета
        trailSpeed: 0.9,     // Скорость
        trailTurbulence: 0.75 // Траектория
    },
    network: {
        useProxy: false // По умолчанию выключено
    },
};

// --- ГЛОБАЛЬНЫЕ UNIFORMS И НАСТРОЙКИ СВЕТА (Инициализация до вызова функций) ---
const globalUniforms = {
    uTime: { value: 0 },
    uWindSpeed: { value: CONFIG.wind.speed },
    uWindForce: { value: CONFIG.wind.force },
    uSwayAmp: { value: CONFIG.motion.swayAmp },
    uTwistAmp: { value: CONFIG.motion.twistAmp },
    uCamPos: { value: new THREE.Vector3() }, 
    uCamDir: { value: new THREE.Vector3() },
    uLightDir: { value: new THREE.Vector3() } 
};

const MAX_POINT_LIGHTS = 20; 

const createLightSet = () => {
    const positions = [];
    const colors = [];
    const params = [];
    for(let i = 0; i < MAX_POINT_LIGHTS; i++) {
        positions.push(new THREE.Vector3(0, -9999, 0));
        colors.push(new THREE.Color(0x000000)); 
        params.push(new THREE.Vector2(0, 0));
    }
    return { positions, colors, params };
};

const terrainLightSet = createLightSet();
const grassLightSet = createLightSet();
const rockLightSet = createLightSet();




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
const MAX_CONCURRENT_LOADS = 8;  
const MAX_TEXTURE_SIZE = 512;
// --- SHADERS (Шейдеры) ---

// НОВЫЙ ЧАНК: Безопасный генератор шума для GPU (без потери точности)
const terrainNoiseChunk = `
    float hash(vec2 p) {
        vec3 p3  = fract(vec3(p.xyx) * 0.1031);
        p3 += dot(p3, p3.yzx + 33.33);
        return fract((p3.x + p3.y) * p3.z);
    }

    float noise(vec2 p) {
        vec2 i = floor(p);
        vec2 f = fract(p);
        f = f * f * (3.0 - 2.0 * f);
        return mix(
            mix(hash(i + vec2(0.0, 0.0)), hash(i + vec2(1.0, 0.0)), f.x),
            mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x),
            f.y
        );
    }

    float getTerrainHeight(vec2 xz, float freq, float amp, float offset, float sharp) {
        float elev = noise(xz * freq) * amp;
        elev += noise(xz * freq * 5.0) * (amp * 0.33);
        float rawElev = elev - offset;
        if (rawElev > 0.0) return pow(rawElev / amp, sharp) * amp;
        return 0.0;
    }
`;


// НОВЫЙ ЧАНК: Быстрый текстурный шум для фрагментных шейдеров
const fastTextureNoiseChunk = `
    uniform sampler2D uNoiseTex;

    float texNoise(vec2 p) {
        // Берем целую и дробную часть координат (как в оригинальном noise)
        vec2 i = floor(p);
        vec2 f = fract(p);
        
        // Сглаживаем дробную часть для красивых плавных переходов
        f = f * f * (3.0 - 2.0 * f);
        
        // Вычисляем точную позицию в текстуре (256.0 - размер нашей текстуры)
        // + 0.5 гарантирует попадание точно в центр пикселя текстуры
        vec2 uv = (i + f + 0.5) / 256.0;
        
        return texture2D(uNoiseTex, uv).r;
    }
`;

// ОБНОВЛЕННЫЙ ЧАНК ТУМАНА (Без тяжелой математики)
const volumetricFogChunk = `
    vec4 calcVolumetricFog(vec3 camPos, vec3 worldPos, float topY, float bottomY, float density, float shape, float time, vec3 fogColor) {
        float dist = length(worldPos - camPos);
        if (dist <= 0.01) return vec4(0.0);
        
        // 1. Локальная плотность тумана на концах луча
        float hPos = 1.0 - smoothstep(bottomY, topY, worldPos.y);
        float hCam = 1.0 - smoothstep(bottomY, topY, camPos.y);
        
        // Если обе точки гарантированно выше слоя тумана — пропускаем расчет
        if (hPos <= 0.001 && hCam <= 0.001) return vec4(0.0);
        
        // 2. Расчет фактического пересечения отрезка высот луча со слоем тумана [bottomY, topY]
        float minVal = min(camPos.y, worldPos.y);
        float maxVal = max(camPos.y, worldPos.y);
        
        float overlapStart = max(minVal, bottomY);
        float overlapEnd = min(maxVal, topY);
        float overlap = max(0.0, overlapEnd - overlapStart);
        
        float totalYSpan = maxVal - minVal;
        float verticalFraction = 1.0;
        
        if (totalYSpan > 0.001) {
            verticalFraction = overlap / totalYSpan;
        } else {
            // Если луч строго горизонтальный, проверяем, находится ли он в границах тумана
            verticalFraction = (minVal >= bottomY && minVal <= topY) ? 1.0 : 0.0;
        }

        // Интегрируем плотность с учетом реальной доли пути, пройденной внутри объема тумана
        float heightFactor = verticalFraction * (hPos + hCam) * 0.5;

        // 3. Генерация пространственного шума
        float ft = time * 0.1;
        vec2 fuv = worldPos.xz * 0.0015;
        float n1 = texNoise(fuv + vec2(ft, ft * 0.5));
        float n2 = texNoise(fuv * 2.5 - vec2(ft * 1.2, 0.0));
        float n3 = texNoise(fuv * 5.0 + vec2(0.0, ft * 2.0));
        float fogNoise = (n1 * 0.5 + n2 * 0.35 + n3 * 0.15);

        // Формируем структуру краев (Shape)
        float densityMod = mix(1.0, smoothstep(0.2, 0.8, fogNoise) * 2.5, shape);
        
        // Ограничение дистанции для стабильности горизонта
        float effectiveDist = min(dist, 4000.0);
        
        // Классическое экспоненциальное затухание (без искажающего pow)
        float opticalDepth = effectiveDist * density * 0.0008 * densityMod * heightFactor;
        float alpha = 1.0 - exp(-opticalDepth);
        
        return vec4(fogColor, clamp(alpha, 0.0, 0.98));
    }
`;


function createOptimizedNoiseTexture() {
    const size = 256;
    const data = new Uint8Array(size * size * 4);
    for (let i = 0; i < data.length; i++) {
        data[i] = Math.floor(Math.random() * 256);
    }
    const tex = new THREE.DataTexture(data, size, size, THREE.RGBAFormat);
    tex.wrapS = THREE.RepeatWrapping;
    tex.wrapT = THREE.RepeatWrapping;
    // Аппаратная билинейная фильтрация (очень важно для сглаживания)
    tex.minFilter = THREE.LinearFilter;
    tex.magFilter = THREE.LinearFilter;
    tex.generateMipmaps = false;
    tex.needsUpdate = true;
    return tex;
}
const globalNoiseTex = createOptimizedNoiseTexture();

// Создаем общий объект с Uniforms для тумана, чтобы легко передавать во все шейдеры
const creepingFogUniforms = {
    uCFogEnabled: { value: CONFIG.terrain.creepingFogEnabled ? 1.0 : 0.0 },
    uCFogColor: { value: CONFIG.terrain.creepingFogColor },
    uCFogHeight: { value: CONFIG.terrain.creepingFogHeight },
    uCFogThick: { value: CONFIG.terrain.creepingFogThickness },
    uCFogDens: { value: CONFIG.terrain.creepingFogDensity },
    uCFogShape: { value: CONFIG.terrain.creepingFogShape },
    uNoiseTex: { value: globalNoiseTex },
    uNoiseTexSize: { value: 256.0 }
};

const sharedCloudUniforms = {
    uWindAngle: { value: CONFIG.grass.bendAngle }, // Синхронизация с ветром
    uIsReflectionPass: { value: 0.0 }, // Флаг прохода отражения (0.0 = нет, 1.0 = да)
    
    // Небо
    uCloudsEnabled: { value: CONFIG.clouds.enabled ? 1.0 : 0.0 },
    uCloudOpacity: { value: CONFIG.clouds.opacity },
    uCloudCoverage: { value: CONFIG.clouds.coverage },
    uCloudSoftness: { value: CONFIG.clouds.softness },
    uCloudScale: { value: CONFIG.clouds.scale },
    uCloudStretch: { value: CONFIG.clouds.stretch },
    uCloudSpeed: { value: CONFIG.clouds.speed },
    uCloudColorZenith: { value: CONFIG.clouds.colorZenith },
    uCloudColorHorizon: { value: CONFIG.clouds.colorHorizon },

    // Тени на земле
    uShadowsEnabled: { value: CONFIG.cloudShadows.enabled ? 1.0 : 0.0 },
    uShadowOpacity: { value: CONFIG.cloudShadows.opacity },
    uShadowCoverage: { value: CONFIG.cloudShadows.coverage },
    uShadowSoftness: { value: CONFIG.cloudShadows.softness },
    uShadowScale: { value: CONFIG.cloudShadows.scale },
    uShadowStretch: { value: CONFIG.cloudShadows.stretch },
    uShadowSpeed: { value: CONFIG.cloudShadows.speed },
    uShadowColor: { value: CONFIG.cloudShadows.color },
    uNoiseTex: { value: globalNoiseTex },
    uNoiseTexSize: { value: 256.0 }
};

const cloudNoiseChunk = `
    uniform float uWindAngle;
    uniform float uIsReflectionPass;
    uniform float uCloudsEnabled, uCloudOpacity, uCloudCoverage, uCloudSoftness, uCloudScale, uCloudStretch, uCloudSpeed;
    uniform vec3 uCloudColorZenith, uCloudColorHorizon;
    uniform float uShadowsEnabled, uShadowOpacity, uShadowCoverage, uShadowSoftness, uShadowScale, uShadowStretch, uShadowSpeed;
    uniform vec3 uShadowColor;

    float calcCloudProceduralNoise(vec2 uv, float scale, float coverage, float softness) {
        // Вернули классические пропорции октав, как в вашем оригинале
        float n = texNoise(uv * scale);
        n += texNoise(uv * scale * 2.1) * 0.5;
        n += texNoise(uv * scale * 4.3) * 0.25;
        n /= 1.75;
        
        float mask = smoothstep(1.0 - coverage, (1.0 - coverage) + softness + 0.001, n);
        return clamp(mask, 0.0, 1.0);
    }

    // Облака на небе
    float getCloudDensity(vec2 worldXZ, float time) {
        vec2 uv = worldXZ;
        float c = cos(uWindAngle);
        float s = sin(uWindAngle);
        mat2 rot = mat2(c, s, -s, c);
        uv = rot * uv;
        
        uv.x *= uCloudStretch; 
        uv.x -= time * uCloudSpeed * 50.0; 
        
        return calcCloudProceduralNoise(uv, uCloudScale, uCloudCoverage, uCloudSoftness);
    }

    // Тени на земле
    float getShadowDensity(vec2 worldXZ, float time) {
        vec2 uv = worldXZ;
        float c = cos(uWindAngle);
        float s = sin(uWindAngle);
        mat2 rot = mat2(c, s, -s, c);
        uv = rot * uv;
        
        uv.x *= uShadowStretch;
        uv.x -= time * uShadowSpeed * 50.0;
        
        return calcCloudProceduralNoise(uv, uShadowScale, uShadowCoverage, uShadowSoftness);
    }
`;

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
    uniform float uTime;
    uniform float uPhase; 
    
    uniform vec3 uCamPos;
    uniform vec3 uCamDir;
    
    varying vec2 vUv;
    varying float vDist;
    varying vec3 vWorldPos;

    // ОПТИМИЗАЦИЯ: Компилируем эту функцию ТОЛЬКО если текстура еще не загружена
    #ifndef HAS_TEXTURE
    float drawProgressBar(vec2 uv, float totalTime) {
        float result = 0.0;
        float count = 5.0;
        float boxW = 0.04;
        float boxH = 0.012;
        float gap = 0.015;
        
        float totalWidth = (boxW * count) + (gap * (count - 1.0));
        float startX = 0.5 - (totalWidth * 0.5) + (boxW * 0.5);
        float posY = 0.40;
        float timePerBlock = 6.0; 

        for(float i = 0.0; i < 5.0; i++) {
            vec2 center = vec2(startX + i * (boxW + gap), posY);
            vec2 d = abs(uv - center) - vec2(boxW * 0.5, boxH * 0.5);
            float dist = max(d.x, d.y);
            float outline = 1.0 - smoothstep(0.0, 0.0015, abs(dist));
            
            float blockStart = i * timePerBlock;
            float blockEnd = (i + 1.0) * timePerBlock;
            float progress = clamp((totalTime - blockStart) / (blockEnd - blockStart), 0.0, 1.0);
            
            float boxLeft = center.x - (boxW * 0.5);
            float fillMask = step(uv.x, boxLeft + (boxW * progress));
            float shape = 1.0 - smoothstep(0.0, 0.002, dist);
            result += max(outline, shape * fillMask);
        }
        return result;
    }
    #endif

    void main() {
        // Расчет прозрачности по дистанции
        float opacityStart = 1500.0; 
        float opacityEnd = 2200.0;   
        float opacity = 1.0 - smoothstep(opacityStart, opacityEnd, vDist);
        if (opacity <= 0.01) discard; 

        // --- РАСЧЕТ ТЕНЕЙ ОТ ИЗГИБОВ ---
        vec3 fdx = dFdx(vWorldPos);
        vec3 fdy = dFdy(vWorldPos);
        vec3 normal = normalize(cross(fdx, fdy));

        if (!gl_FrontFacing) {
            normal = -normal;
        }

        vec3 lightDir = normalize(vec3(-0.5, 0.8, 0.6));
        float diff = max(dot(normal, lightDir), 0.0);
        float waveShadow = 0.75 + 0.25 * diff;

        // --- ИЗМЕНЕНИЕ: БЕЛАЯ ОБРАТНАЯ СТОРОНА ---
        if (!gl_FrontFacing) {
            gl_FragColor = vec4(vec3(0.95) * waveShadow, opacity);
            return;
        }

        float shadowStart = 800.0;
        float shadowEnd = 1600.0;
        float distFactor = 1.0 - smoothstep(shadowStart, shadowEnd, vDist);
        float brightness = (0.15 + (0.85 * distFactor)) * waveShadow;

        vec3 rgbColor;

        // ОПТИМИЗАЦИЯ: Препроцессорное ветвление вместо uniform bool
        #ifdef HAS_TEXTURE
            rgbColor = texture2D(map, vUv).rgb;
        #else
            vec3 bg = vec3(0.05, 0.09, 0.18); 
            
            vec2 center = vec2(0.5, 0.5);
            float distToCenter = distance(vUv, center);
            float pulse = 0.5 + 0.5 * sin(uTime * 8.0); 
            float dotRadius = 0.015 + 0.005 * pulse; 
            float centerDot = 1.0 - smoothstep(dotRadius, dotRadius + 0.002, distToCenter);
            
            vec3 toObj = normalize(vWorldPos - uCamPos);
            float align = dot(toObj, uCamDir); 
            float dist = distance(vWorldPos, uCamPos);

            vec3 priorityColor = (align > 0.5 && dist < 1200.0) ? vec3(1.0) : vec3(1.0, 0.85, 0.0);

            float localTime = uTime + uPhase * 5.0; 
            float t = mod(localTime, 35.0); 
            
            float barsMask = drawProgressBar(vUv, t);
            
            rgbColor = bg;
            rgbColor = mix(rgbColor, vec3(1.0), centerDot); 
            rgbColor = mix(rgbColor, priorityColor, barsMask); 
        #endif

        vec3 finalRgb = rgbColor * brightness;
        gl_FragColor = vec4(finalRgb, opacity);
    }
`;
// --- SCENE SETUP ---
const container = document.getElementById('canvas-container');
const scene = new THREE.Scene();

const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 10, 8000);
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
const solarManager = new SolarSystemManager(scene, camera);
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(CONFIG.graphics.renderScale);
// ВАЖНО: Исправляет цветопередачу текстур

container.appendChild(renderer.domElement);

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

// --- СИСТЕМА ПЛЕНОЧНОГО ШУМА (WEBGL) ---
const grainGeometry = new THREE.BufferGeometry();
// Создаем треугольник, который покрывает весь экран (Screen-Space Quad)
grainGeometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array([
    -1.0, -1.0, 0.0,  3.0, -1.0, 0.0,  -1.0, 3.0, 0.0
]), 3));

const grainMaterial = new THREE.ShaderMaterial({
    uniforms: {
        uTime: { value: 0.0 },
        uOpacity: { value: CONFIG.graphics.grainOpacity || 0.12 }
    },
    vertexShader: `
        void main() {
            gl_Position = vec4(position, 1.0);
        }
    `,
    fragmentShader: `
        uniform float uTime;
        uniform float uOpacity;

        void main() {
            vec2 uv = gl_FragCoord.xy;
            // Возвращаем оригинальный, резкий попиксельный шум
            float noise = fract(sin(dot(uv, vec2(12.9898, 78.233)) + uTime * 10.0) * 43758.5453);
            gl_FragColor = vec4(vec3(noise - 0.5), uOpacity);
        }
    `,
    transparent: true,
    blending: THREE.NormalBlending, 
    depthTest: false,
    depthWrite: false
});

const filmGrainMesh = new THREE.Mesh(grainGeometry, grainMaterial);
filmGrainMesh.frustumCulled = false;
filmGrainMesh.renderOrder = 9999; // Рисуем в самую последнюю очередь
scene.add(filmGrainMesh);



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
uniform float uScale;
uniform float uSizeMult;

uniform float uWindSpeed;
uniform float uWindForce;
uniform float uPartSpeed;
uniform float uWindAngle; // <-- ДОБАВЛЕНО

// --- НОВЫЕ ПЕРЕМЕННЫЕ ДЛЯ ЗЕМЛИ ---
uniform float uGroundMode;
uniform float uAmplitude;
uniform float uFrequency;
uniform float uOffset;
uniform float uSharpness;

attribute float size;
varying float vAlpha;

// Функции шума для земли
${terrainNoiseChunk}


void main() {
    vec3 pos = position;
    
    float windOffset = uTime * uWindSpeed * 50.0;
    float vertOffset = uTime * uPartSpeed * 10.0;
    
    vec2 windDir = vec2(cos(uWindAngle), sin(uWindAngle)); // <-- Вектор направления ветра
    
    vec3 animatedPos = pos;
    animatedPos.x += windDir.x * windOffset; // Двигаем по X
    animatedPos.z += windDir.y * windOffset; // Двигаем по Z (вместо только X)
    animatedPos.y -= vertOffset;             // Падение вниз

    float wobbleFreq = uTime * uPartSpeed;
    float wobbleAmp = uWindForce * 200.0; 
    
    animatedPos.x += sin(wobbleFreq + pos.y * 0.01) * wobbleAmp;
    animatedPos.y += cos(wobbleFreq + pos.x * 0.01) * wobbleAmp * 0.5;

    vec3 localPos = mod(animatedPos - uCamPos + uSize * 0.5, uSize) - uSize * 0.5;
    vec3 finalPos = uCamPos + localPos;

    // --- НОВОЕ: ПРИВЯЗКА К РЕЛЬЕФУ ---
    if (uGroundMode > 0.5) {
        float groundY = getTerrainHeight(finalPos.xz, uFrequency, uAmplitude, uOffset, uSharpness);
        // Превращаем высоту частицы внутри куба в процент от 0 до 1
        float normalizedY = (localPos.y + uSize * 0.5) / uSize; 
        // Пыль летает от поверхности земли до +400 юнитов вверх
        finalPos.y = groundY + (normalizedY * 250.0) + 1.0; 
    }
    // --------------------------------

    vec4 mvPosition = modelViewMatrix * vec4(finalPos, 1.0);
    gl_Position = projectionMatrix * mvPosition;
    
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
        uPartSpeed: { value: CONFIG.particles.speed },
        // ДОБАВИТЬ:
        uGroundMode: { value: 0 },
        uAmplitude: { value: CONFIG.terrain.amplitude },
        uFrequency: { value: CONFIG.terrain.frequency },
        uOffset: { value: CONFIG.terrain.offset },
        uSharpness: { value: CONFIG.terrain.sharpness }
    },
    vertexShader: `
        attribute float phase;
        attribute float size;
        attribute float type;
        
        varying float vAlpha;
        varying float vType; 
        
        uniform float uTime;
        uniform float uScale;
        uniform vec3 uCamPos;
        uniform float uSize;
        uniform float uWindSpeed;
        uniform float uWindForce;
        uniform float uPartSpeed;
        uniform float uSizeMult; 

        // --- НОВЫЕ ПЕРЕМЕННЫЕ ДЛЯ ЗЕМЛИ ---
        uniform float uGroundMode;
        uniform float uAmplitude;
        uniform float uFrequency;
        uniform float uOffset;
        uniform float uSharpness;

        ${terrainNoiseChunk}


        void main() {
            vType = type;
            vec3 pos = position;

            float timeScale = (type > 0.5) ? 1.0 : 2.5; 
            float windOffset = uTime * uWindSpeed * 60.0 * timeScale;
            float vertOffset = uTime * uPartSpeed * 15.0 * timeScale;
            
            vec3 animatedPos = pos;
            animatedPos.x += windOffset;
            animatedPos.y += vertOffset;

            float wobbleSpeed = uTime * (0.5 + uPartSpeed) * timeScale;
            float wobbleAmp = (type > 0.5) ? 50.0 : 80.0;
            
            animatedPos.x += sin(wobbleSpeed + phase) * (wobbleAmp + uWindForce * 100.0);
            animatedPos.y += cos(wobbleSpeed * 0.8 + phase) * (wobbleAmp + uWindForce * 100.0);
            animatedPos.z += sin(wobbleSpeed * 0.5 + phase) * (20.0 + uWindForce * 50.0);

            vec3 localPos = mod(animatedPos - uCamPos + uSize * 0.5, uSize) - uSize * 0.5;
            vec3 finalPos = uCamPos + localPos;

            // --- НОВОЕ: ПРИВЯЗКА К РЕЛЬЕФУ ---
            if (uGroundMode > 0.5) {
                float groundY = getTerrainHeight(finalPos.xz, uFrequency, uAmplitude, uOffset, uSharpness);
                float normalizedY = (localPos.y + uSize * 0.5) / uSize;
                
                // Светлячки летают ниже пыли: от 0 до 80 юнитов (прямо в гуще травы)
                float heightRange = (type > 0.5) ? 60.0 : 100.0;
                finalPos.y = groundY + (normalizedY * heightRange) + 1.0; 
            }
            // --------------------------------

            vec4 mvPosition = modelViewMatrix * vec4(finalPos, 1.0);
            gl_Position = projectionMatrix * mvPosition;

            gl_PointSize = (size * uSizeMult * uScale) / -mvPosition.z;
            
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
        
        // ИСПРАВЛЕНИЕ: Берем стартовые значения из конфига, а не нули
        uWindSpeed: { value: CONFIG.wind.speed },
        uWindForce: { value: CONFIG.wind.force },
        uPartSpeed: { value: CONFIG.particles.speed },
        
        uSizeMult: { value: CONFIG.details.dustSize },
        uWindAngle: { value: CONFIG.grass.bendAngle },
        uGroundMode: { value: 0 },
        uAmplitude: { value: CONFIG.terrain.amplitude },
        uFrequency: { value: CONFIG.terrain.frequency },
        uOffset: { value: CONFIG.terrain.offset },
        uSharpness: { value: CONFIG.terrain.sharpness }
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
const MAX_STARS = 60000; 
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
        uResolution: { value: new THREE.Vector2(window.innerWidth, window.innerHeight) },
        uCamPos: { value: new THREE.Vector3() },
        uGroundMode: { value: 0 }, // <--- ДОБАВИТЬ ЭТУ СТРОКУ
        ...sharedCloudUniforms
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
        varying vec3 vWorldPos; // <--- НОВОЕ: Передаем мировую позицию

        uniform float uTime;
        uniform float uScale;
        uniform float uSizeMult;
        uniform float uBlur;

        void main() {
            vColor = color;
            vSpeed = speed;
            vBrightness = brightness;
            
            vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
            vWorldPos = (modelMatrix * vec4(position, 1.0)).xyz; // <--- НОВОЕ
            
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
        varying vec3 vWorldPos; // <--- НОВОЕ
        
        uniform float uBlur;
        uniform vec2 uResolution;
        uniform vec3 uCamPos; // <--- НОВОЕ
        uniform float uTime;  // <--- ДОБАВЛЕНО ИСПРАВЛЕНИЕ ЗДЕСЬ
        uniform float uGroundMode;

        // --- НОВОЕ: Инжектим шум и облака ---
        ${terrainNoiseChunk}
        ${fastTextureNoiseChunk}
        ${cloudNoiseChunk}

        float hexDist(vec2 p) {
            p = abs(p);
            float d = max(p.x * 0.866025 + p.y * 0.5, p.y);
            return d;
        }

        void main() {
            vec2 uv = gl_PointCoord - vec2(0.5);
            
            float distFromCenter = length(vScreenPos);
            float edgeFactor = smoothstep(0.7, 1.2, distFromCenter);
            
            float distortStr = edgeFactor * edgeFactor * uBlur * 1.0;
            vec2 dirToCenter = normalize(-vScreenPos);
            vec2 distortedUV = uv - dirToCenter * dot(uv, dirToCenter) * distortStr;

            float angle = vSpeed * 10.0; 
            float ca = cos(angle); float sa = sin(angle);
            mat2 rot = mat2(ca, -sa, sa, ca);
            vec2 rotUV = rot * distortedUV; 
            
            float distHex = hexDist(rotUV);
            float distCircle = length(distortedUV);
            float shapeDist = mix(distCircle, distHex, uBlur * 1.2);
            
            float edgeSoftness = 0.05 + uBlur * (0.2 + edgeFactor * 0.5); 
            float alphaShape = 1.0 - smoothstep(0.5 - edgeSoftness, 0.5, shapeDist);
            
            float centerFade = smoothstep(0.0, 0.35 + uBlur * 0.15, shapeDist);
            float blurCenterFactor = mix(1.0, centerFade, smoothstep(0.3, 1.0, uBlur));
            
            float energyConservation = 1.0 / (1.0 + uBlur * 2.0);
            float cullThreshold = 0.2 + uBlur * 0.55; 
            float cullFactor = smoothstep(cullThreshold, cullThreshold + 0.4, vBrightness);

            float finalOpacity = vAlpha * alphaShape * blurCenterFactor * energyConservation * vBrightness * cullFactor;

            vec3 viewDirToStar = normalize(vWorldPos - uCamPos);
            float horizonFade = smoothstep(0.01, 0.12, viewDirToStar.y);
            finalOpacity *= mix(1.0, horizonFade, uGroundMode);
            
            // ==========================================
            // НОВОЕ: ЗАТМЕНИЕ ЗВЁЗД ОБЛАКАМИ
            // ==========================================
            if (uCloudsEnabled > 0.5) {
                // Проецируем луч зрения на "высоту облаков" (условно 3000)
                vec3 viewDir = normalize(vWorldPos - uCamPos);
                float h = max(viewDir.y, 0.001); // Избегаем деления на 0
                vec2 skyWorldXZ = uCamPos.xz + (viewDir.xz / h) * 3000.0;
                
                // Получаем плотность облака в этой точке
                float cDens = getCloudDensity(skyWorldXZ, uTime);
                
                // Рассчитываем силу перекрытия
                float cloudOcclusion = 1.0 - clamp(cDens * uCloudOpacity * 2.5, 0.0, 1.0);
                finalOpacity *= cloudOcclusion;
            }
            // ==========================================

            if (finalOpacity < 0.005) discard;

            vec3 finalRGB = vColor;
            float rim = smoothstep(0.35, 0.5, shapeDist);
            float luma = dot(finalRGB, vec3(0.299, 0.587, 0.114));
            vec3 chroma = finalRGB / max(luma, 0.001);

            finalRGB = mix(finalRGB, chroma * luma * (1.0 + rim * uBlur * 0.8), rim);

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
        const headAngles = new Float32Array(count); 
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
                uBlur: { value: 0 } 
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

                    float s = sin(vAngle);
                    float c = cos(vAngle);
                    mat2 rot = mat2(c, -s, s, c);
                    vec2 rotUV = rot * uv;

                    float dist = length(uv);

                    float core = 1.0 - smoothstep(0.0, 0.15 + uBlur * 0.1, dist);
                    
                    float flareV = 0.015 / (abs(rotUV.x * 6.0) + 0.05);
                    float flareH = 0.002 / (abs(rotUV.y * 2.0) + 0.05); 
                    float flare = (flareV + flareH) * (1.0 - smoothstep(0.3, 0.5, dist));
                    
                    float intensity = core * 2.0 + flare * 1.5;
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
        this.heads.renderOrder = 1; 
        this.heads.frustumCulled = false;
        scene.add(this.heads);

        // 3. ДАННЫЕ КОМЕТ
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

        // --- ВНЕДРЕНИЕ СОВЕТА: КЭШИРОВАНИЕ АТРИБУТОВ ЗДЕСЬ ---
        this.linePosAttr = this.lines.geometry.attributes.position;
        this.lineColAttr = this.lines.geometry.attributes.color;
        this.headPosAttr = this.heads.geometry.attributes.position;
        this.headSizeAttr = this.heads.geometry.attributes.size;
        this.headColAttr = this.heads.geometry.attributes.color;
        this.headAlphaAttr = this.heads.geometry.attributes.alpha;
        this.headAngleAttr = this.heads.geometry.attributes.angle;
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
        available.angle = (Math.random() - 0.5) * Math.PI; 
    }

    update(blurLevel) {
        this.headMat.uniforms.uBlur.value = blurLevel;

        const spawnChance = CONFIG.sky.slowCometFreq * 40.0;
        if (Math.random() < spawnChance) this.spawn();
        if (spawnChance > 1.0 && Math.random() < spawnChance * 0.5) this.spawn();

        let needsUpdate = false;

        // В цикле используем this.linePosAttr и т.д.
        this.comets.forEach(c => {
            const idxLine1 = c.index * 2;     
            const idxLine2 = c.index * 2 + 1; 
            const idxHead = c.index;

            if (!c.active) {
                if (this.headAlphaAttr.getX(idxHead) !== 0) { 
                    this.lineColAttr.setW(idxLine1, 0); 
                    this.lineColAttr.setW(idxLine2, 0);
                    this.headAlphaAttr.setX(idxHead, 0);
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
            
            const tailLen = 300.0;
            const tailPos = c.pos.clone().sub(c.vel.clone().normalize().multiplyScalar(tailLen));

            this.linePosAttr.setXYZ(idxLine1, tailPos.x, tailPos.y, tailPos.z);
            this.linePosAttr.setXYZ(idxLine2, c.pos.x, c.pos.y, c.pos.z);

            let progress = c.life / c.maxLife;
            let baseAlpha = Math.sin(progress * Math.PI) * 1.0; 
            let lineAlpha = baseAlpha * (1.0 - blurLevel * 0.9);

            this.lineColAttr.setXYZW(idxLine2, c.color.r, c.color.g, c.color.b, lineAlpha);
            this.lineColAttr.setXYZW(idxLine1, c.color.r, c.color.g, c.color.b, 0.0);
            
            this.headPosAttr.setXYZ(idxHead, c.pos.x, c.pos.y, c.pos.z);
            this.headColAttr.setXYZ(idxHead, c.color.r, c.color.g, c.color.b);
            this.headAngleAttr.setX(idxHead, c.angle);
            
            let size = 60.0 + (blurLevel * 100.0);
            this.headSizeAttr.setX(idxHead, size);
            this.headAlphaAttr.setX(idxHead, baseAlpha);

            needsUpdate = true;
        });

        // Флаги обновления также ставим через this
        if (needsUpdate) {
            this.linePosAttr.needsUpdate = true;
            this.lineColAttr.needsUpdate = true;
            this.headPosAttr.needsUpdate = true;
            this.headSizeAttr.needsUpdate = true;
            this.headColAttr.needsUpdate = true;
            this.headAlphaAttr.needsUpdate = true;
            this.headAngleAttr.needsUpdate = true;
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

        // ==========================================
        // --- НОВАЯ ЛОГИКА: СТОЛКНОВЕНИЕ С ЗЕМЛЕЙ ---
        // ==========================================
        if (CONFIG.ui.groundMode && typeof getTerrainHeight === 'function') {
            const groundY = getTerrainHeight(newHeadX, newHeadZ);
            
            // Если комета ушла под землю
            if (newHeadY <= groundY) {
                const hitPos = new THREE.Vector3(newHeadX, groundY, newHeadZ);
                
                // Проверяем, находится ли точка удара на экране (в поле зрения камеры)
                const screenPos = hitPos.clone().project(camera);
                
                // x и y от -1 до 1 значит на экране. z < 1 значит перед камерой (не сзади)
                const isOnScreen = (
                    screenPos.z < 1.0 && 
                    screenPos.x > -1.0 && screenPos.x < 1.0 && 
                    screenPos.y > -1.0 && screenPos.y < 1.0
                );

                if (isOnScreen && typeof fallenStarSystem !== 'undefined') {
                    // Получаем цвет этой кометы
                    const colAttr = this.mesh.geometry.attributes.color;
                    const color = new THREE.Color(colAttr.getX(1), colAttr.getY(1), colAttr.getZ(1));
                    
                    // Спавним светящийся кристалл
                    fallenStarSystem.spawn(hitPos, color);
                }

                // Уничтожаем комету, так как она разбилась
                this.active = false;
                this.material.opacity = 0;
                return;
            }
        }
        // ==========================================

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


function getTerrainHeight(x, z) {
    const fract = (n) => n - Math.floor(n);
    const mix = (a, b, t) => a * (1 - t) + b * t;

    // Безопасный хэш без использования Math.sin()
    function hash(px, pz) {
        let p3x = fract(px * 0.1031);
        let p3y = fract(pz * 0.1031);
        let p3z = fract(px * 0.1031);
        
        let dotVal = (p3x * (p3y + 33.33)) + (p3y * (p3z + 33.33)) + (p3z * (p3x + 33.33));
        p3x += dotVal;
        p3y += dotVal;
        p3z += dotVal;
        
        return fract((p3x + p3y) * p3z);
    }

    function noise(px, pz) {
        let ix = Math.floor(px), iz = Math.floor(pz);
        let fx = fract(px), fz = fract(pz);
        
        // Сглаживание (Quintic curve)
        fx = fx * fx * (3.0 - 2.0 * fx);
        fz = fz * fz * (3.0 - 2.0 * fz);
        
        return mix(
            mix(hash(ix, iz),       hash(ix + 1, iz),       fx),
            mix(hash(ix, iz + 1),   hash(ix + 1, iz + 1),   fx),
            fz
        );
    }

    const freq = CONFIG.terrain.frequency;
    const amp = CONFIG.terrain.amplitude;
    const offset = CONFIG.terrain.offset;
    const sharp = CONFIG.terrain.sharpness;

    let elev = noise(x * freq, z * freq) * amp;
    elev += noise(x * freq * 5.0, z * freq * 5.0) * (amp * 0.33);
    
    let rawElev = elev - offset;
    if (rawElev > 0.0) {
        rawElev = Math.pow(rawElev / amp, sharp) * amp;
    } else {
        rawElev = 0.0; 
    }
    
    return rawElev;
}


class SkyDomeSystem {
    constructor(scene) {
        const geo = new THREE.SphereGeometry(6000, 32, 32);
        this.material = new THREE.ShaderMaterial({
            uniforms: {
                uTime: { value: 0 }, // <-- ДОБАВЛЕНО
                colorBot: { value: CONFIG.colors.bottom },
                colorMid: { value: CONFIG.colors.mid },
                colorTop: { value: CONFIG.colors.top },
                ...sharedCloudUniforms // <-- ВНЕДРЕНИЕ НАСТРОЕК
            },
            vertexShader: `
                varying vec3 vWorldDirection;
                void main() {
                    vec4 worldPosition = modelMatrix * vec4(position, 1.0);
                    vWorldDirection = normalize(worldPosition.xyz - cameraPosition); 
                    gl_Position = projectionMatrix * viewMatrix * worldPosition;
                }
            `,
            fragmentShader: `
                uniform float uTime;
                uniform vec3 colorBot;
                uniform vec3 colorMid;
                uniform vec3 colorTop;
                varying vec3 vWorldDirection;
                
                ${terrainNoiseChunk}
                ${fastTextureNoiseChunk}
                ${cloudNoiseChunk}
                
                void main() {
                    float h = vWorldDirection.y; 
                    vec3 finalColor = mix(colorBot, colorMid, smoothstep(-0.2, 0.4, h + 0.15));
                    finalColor = mix(finalColor, colorTop, smoothstep(0.2, 1.0, h + 0.15));
                    
                    // --- ОТРИСОВКА ПЛОСКИХ ОБЛАКОВ ---
                    if (uCloudsEnabled > 0.5 && h > 0.01) {
                        // Проекция: создаем воображаемый "потолок" на высоте 3000
                        vec2 skyWorldXZ = cameraPosition.xz + (vWorldDirection.xz / h) * 3000.0;
                        
                        float cDens = getCloudDensity(skyWorldXZ, uTime);
                        vec3 cColor = mix(uCloudColorHorizon, uCloudColorZenith, smoothstep(0.0, 0.5, h));
                        
                        // Растворяем облака у самого горизонта
                        float horizonFade = smoothstep(0.02, 0.1, h);
                        finalColor = mix(finalColor, cColor, cDens * uCloudOpacity * horizonFade);
                    }
                    
                    gl_FragColor = vec4(finalColor, 1.0);
                }
            `,
            side: THREE.BackSide,
            depthWrite: false
        });

        this.mesh = new THREE.Mesh(geo, this.material);
        this.mesh.renderOrder = -2;
        this.mesh.visible = false;
        scene.add(this.mesh);
    }

    update(camPos, time) {
        this.mesh.position.copy(camPos);
        this.material.uniforms.uTime.value = time; // Обновляем время
    }
}


// --- СИСТЕМА ОТРАЖЕНИЙ ---
class ReflectionSystem {
    constructor(scene, mainCamera) {
        this.scene = scene;
        this.mainCamera = mainCamera;
        
        this.renderTarget = new THREE.WebGLRenderTarget(CONFIG.water.resolution, CONFIG.water.resolution, {
            format: THREE.RGBAFormat,
            minFilter: THREE.LinearFilter,
            magFilter: THREE.LinearFilter,
            generateMipmaps: false
        });

        this.reflectionCamera = mainCamera.clone();
        
        // ОПТИМИЗАЦИЯ: Создаем объекты один раз
        this.clipPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0.0);
        this._viewDir = new THREE.Vector3();
        this._target = new THREE.Vector3();
        this._localUp = new THREE.Vector3();
    }

    resize(size) {
        this.renderTarget.setSize(size, size);
    }

    update(renderer) {
        if (!CONFIG.water.reflections) return;

        this.reflectionCamera.position.copy(this.mainCamera.position);
        this.reflectionCamera.position.y *= -1; 

        // ОПТИМИЗАЦИЯ: Без аллокаций памяти (new)
        this._viewDir.set(0, 0, -1).applyQuaternion(this.mainCamera.quaternion);
        this._viewDir.y *= -1; 
        this._target.copy(this.reflectionCamera.position).add(this._viewDir);

        this._localUp.set(0, 1, 0).applyQuaternion(this.mainCamera.quaternion);
        this._localUp.y *= -1; 

        this.reflectionCamera.up.copy(this._localUp);
        this.reflectionCamera.lookAt(this._target);

        const prevGrassNear = grassSystem.meshNear ? grassSystem.meshNear.visible : false;
        const prevGrassFar = grassSystem.meshFar ? grassSystem.meshFar.visible : false;
        const prevDust = dustSystem.visible;
        const prevFirefly = fireflySystem.visible;
        const prevRocks = rockSystem.group.visible; 
        const prevClouds = sharedCloudUniforms.uCloudsEnabled.value; 
        
        if (grassSystem.meshNear) grassSystem.meshNear.visible = false;
        if (grassSystem.meshFar) grassSystem.meshFar.visible = false; 
        dustSystem.visible = false;
        fireflySystem.visible = false;

        if (!CONFIG.water.reflectRocks) rockSystem.group.visible = false;
        if (!CONFIG.water.reflectClouds) sharedCloudUniforms.uCloudsEnabled.value = 0.0;

        const oldClipping = renderer.localClippingEnabled;
        renderer.localClippingEnabled = true;
        renderer.clippingPlanes = [this.clipPlane];

        // АКТИВИРУЕМ ОПТИМИЗАЦИЮ: сообщаем шейдерам, что начался рендер отражения
        sharedCloudUniforms.uIsReflectionPass.value = 1.0;

        renderer.setRenderTarget(this.renderTarget);
        renderer.clear();
        renderer.render(this.scene, this.reflectionCamera);
        renderer.setRenderTarget(null); 

        // ДЕАКТИВИРУЕМ ОПТИМИЗАЦИЮ: возвращаем режим обычного кадра
        sharedCloudUniforms.uIsReflectionPass.value = 0.0;

        renderer.clippingPlanes = [];
        renderer.localClippingEnabled = oldClipping;

        if (grassSystem.meshNear) grassSystem.meshNear.visible = prevGrassNear;
        if (grassSystem.meshFar) grassSystem.meshFar.visible = prevGrassFar;
        dustSystem.visible = prevDust;
        fireflySystem.visible = prevFirefly;
        
        rockSystem.group.visible = prevRocks;
        sharedCloudUniforms.uCloudsEnabled.value = prevClouds;
    }
}


class RockSystem {
    constructor(scene) {
        this.scene = scene;
        this.group = new THREE.Group();
        this.scene.add(this.group);
        this.meshSmall = null;
        this.meshBoulder = null;
        this.build();
    }

    build() {
        if (this.meshSmall) {
            this.group.remove(this.meshSmall);
            this.meshSmall.geometry.dispose();
            this.meshSmall.material.dispose();
        }
        if (this.meshBoulder) {
            this.group.remove(this.meshBoulder);
            this.meshBoulder.geometry.dispose();
            this.meshBoulder.material.dispose();
        }

        if (!CONFIG.rocks.enabled || CONFIG.rocks.count <= 0) return;

        // Вспомогательная функция для создания отдельного меша
        const createMesh = (isBoulder, count) => {
            if (count <= 0) return null;

            const shape = isBoulder ? CONFIG.rocks.shapeBoulder : CONFIG.rocks.shapeSmall;
            const detail = Math.round((1.0 - shape) * 2);
            const geometry = new THREE.IcosahedronGeometry(1, detail);
            geometry.translate(0, 0.5, 0); // Опорная точка внизу

            const material = new THREE.ShaderMaterial({
                uniforms: {
                    uTime: { value: 0 },
                    uCamPos: { value: new THREE.Vector3() },
                    uDrawDistance: { value: CONFIG.rocks.drawDistance },
                    
                    uBaseColor: { value: CONFIG.rocks.baseColor },
                    uTipColor: { value: CONFIG.rocks.tipColor },
                    
                    // НОВЫЕ UNIFORM
                    uCrystalRatio: { value: isBoulder ? CONFIG.rocks.crystalRatioBoulder : CONFIG.rocks.crystalRatioSmall },
                    uCrystalBaseColor: { value: CONFIG.rocks.crystalBaseColor },
                    uCrystalTipColor: { value: CONFIG.rocks.crystalTipColor },
                    uSmoothness: { value: CONFIG.rocks.smoothness },
                    uMinHeight: { value: CONFIG.rocks.minHeight },
                    uMaxHeight: { value: CONFIG.rocks.maxHeight },
                    
                    // --- НОВЫЕ UNIFORMS ДЛЯ ГРАНЕЙ И КРИСТАЛЛОВ ---
                    uFlatShading: { value: CONFIG.rocks.flatShading },
                    uRockAO: { value: CONFIG.rocks.ao },
                    uCrystalGloss: { value: CONFIG.rocks.crystalGloss },
                    uCrystalIrisSpread: { value: CONFIG.rocks.crystalIrisSpread },
                    uCrystalIrisIntensity: { value: CONFIG.rocks.crystalIrisIntensity },
                    uCrystalAlpha: { value: CONFIG.rocks.crystalAlpha }, // <--- ДОБАВИТЬ ЭТУ СТРОКУ

                    uRockFloatAmp: { value: CONFIG.rocks.floatAmp },
                    uRockFloatSpeed: { value: CONFIG.rocks.floatSpeed },
                    uMossSpread: { value: CONFIG.rocks.mossSpread },
                    uMossColor: { value: CONFIG.rocks.mossColor },
                    

                    // ----------------------------------------------
                    
                    uRockYOffset: { value: CONFIG.rocks.yOffset },
                    uRockYSpread: { value: CONFIG.rocks.ySpread },

                    uFoamOpacity: { value: CONFIG.water.foamOpacity },
                    uRockFoamOpacity: { value: CONFIG.rocks.rockFoamOpacity },
                    uRockFoamHeight: { value: CONFIG.rocks.rockFoamHeight },
                    uFoamColor: { value: CONFIG.water.foamColor },
                    uFoamWidth: { value: CONFIG.water.foamWidth },
                    uFoamNoise: { value: CONFIG.water.foamNoise },

                    uRockStruct: { value: CONFIG.rocks.struct },
                    uRockThin: { value: CONFIG.rocks.thin },
                    
                    uAmplitude: { value: CONFIG.terrain.amplitude },
                    uFrequency: { value: CONFIG.terrain.frequency },
                    uOffset: { value: CONFIG.terrain.offset },
                    uSharpness: { value: CONFIG.terrain.sharpness },
                    
                    uFogColor: { value: CONFIG.terrain.fogColor },
                    uFogDensity: { value: CONFIG.terrain.fogDensity },
                    uLightEnable: { value: CONFIG.flashlight.enabled ? 1.0 : 0.0 },
                    uLightColor: { value: CONFIG.flashlight.color },
                    uLightIntensity: { value: CONFIG.flashlight.intensity },
                    uLightRange: { value: CONFIG.flashlight.range },
                    uLightRadius: { value: CONFIG.flashlight.radius },
                    uLightFocus: { value: CONFIG.flashlight.focus },
                    uLightOffset: { value: CONFIG.flashlight.offset },
                    uLightDir: { value: new THREE.Vector3() },
                    uCamDir: { value: new THREE.Vector3() },

                    uGlobalLight: { value: CONFIG.lighting.globalIntensity },

                    uPointLightPos: { value: rockLightSet.positions },
                    uPointLightColor: { value: rockLightSet.colors },
                    uPointLightParams: { value: rockLightSet.params },
                    uPointLightCount: { value: 0 },

                    ...creepingFogUniforms,
                    ...sharedCloudUniforms
                },
                vertexShader: `
                    #include <clipping_planes_pars_vertex> 

                    uniform float uTime;

                    uniform vec3 uCamPos;
                    uniform float uDrawDistance;
                    uniform float uAmplitude, uFrequency, uOffset, uSharpness;
                    uniform float uMinHeight, uMaxHeight;
                    uniform float uRockYOffset, uRockYSpread;
                    
                    uniform float uRockStruct;
                    uniform float uRockThin;

                    varying vec3 vWorldPos;
                    varying vec3 vNormal;
                    uniform float uRockFloatAmp;
                    uniform float uRockFloatSpeed;
                    varying float vVisible;
                    varying float vHeightAboveGround; 
                    varying float vIsCrystal; // <--- НОВОЕ: Передаем метку кристалла

                    ${terrainNoiseChunk}

                    void main() {
                        vec4 localPos = instanceMatrix * vec4(position, 1.0);
                        vNormal = normalize(normalMatrix * mat3(instanceMatrix) * normal);
                        
                        float halfDist = uDrawDistance * 0.5;
                        vec4 localInstancePos = instanceMatrix * vec4(0.0, 0.0, 0.0, 1.0);
                        vec2 worldXZ = uCamPos.xz + mod(localInstancePos.xz - uCamPos.xz + halfDist, uDrawDistance) - halfDist;

                        // --- НОВОЕ: Определяем, кристалл это или нет ---
                        // Уникальный случайный ID для каждого камня
                        float crystalRand = fract(sin(dot(localInstancePos.xz, vec2(83.123, 12.981))) * 43758.5453);
                        vIsCrystal = crystalRand; 
                        // -----------------------------------------------

                        float cellSize = 200.0;
                        vec2 cellIndex = floor(worldXZ / cellSize);
                        vec2 cellRand = vec2(
                            fract(sin(dot(cellIndex, vec2(12.9898, 78.233))) * 43758.5453),
                            fract(sin(dot(cellIndex, vec2(39.346, 11.135))) * 43758.5453)
                        );
                        vec2 clusterCenter = (cellIndex + cellRand) * cellSize;
                        vec2 toCenter = clusterCenter - worldXZ;
                        float rockVary = fract(sin(dot(localInstancePos.xz, vec2(89.44, 23.16))) * 43758.5453);
                        float pullStrength = uRockStruct * mix(0.4, 0.95, rockVary);
                        vec2 finalWorldXZ = worldXZ + toCenter * pullStrength;

                        float groundY = getTerrainHeight(finalWorldXZ, uFrequency, uAmplitude, uOffset, uSharpness);
                        float randSpread = fract(sin(dot(localInstancePos.xz, vec2(12.9898, 78.233))) * 43758.5453) * 2.0 - 1.0;
                        float currentOffset = uRockYOffset + (randSpread * uRockYSpread);

                        float baseScale = mix(0.05, 0.002, uRockStruct); 
                        float finalScale = baseScale * mix(1.0, 0.3, uRockThin); 
                        vec2 off = vec2(400.0, -200.0);
                        float islandNoise = noise(finalWorldXZ * finalScale + off) * 0.8 + noise(finalWorldXZ * finalScale * 2.5 - off) * 0.2;
                        float threshold = mix(0.3, 0.8, uRockThin);
                        float islandMask = smoothstep(threshold - 0.1, threshold + 0.1, islandNoise);

                        float spawnProbability = mix(1.0, islandMask, uRockStruct);
                        float localRand = fract(sin(dot(localInstancePos.xz, vec2(71.9898, 38.233))) * 43758.5453);

                        float distToCam = length(finalWorldXZ - uCamPos.xz);
                        float edgeFade = 1.0 - smoothstep(halfDist * 0.8, halfDist, distToCam);

                        vVisible = edgeFade > 0.01 ? 1.0 : 0.0;

                        if (groundY < uMinHeight || groundY > uMaxHeight || localRand > spawnProbability) {
                            vVisible = 0.0;
                        }

                        vec3 vertexOffset = localPos.xyz - localInstancePos.xyz;
                        vec3 scaledVertexOffset = vertexOffset * edgeFade * (vVisible > 0.5 ? 1.0 : 0.0);

                        // --- НОВАЯ ЛОГИКА ЛЕВИТАЦИИ ---
                        vec3 floatOffset = vec3(0.0);
                        if (uRockFloatAmp > 0.0) {
                            float t = uTime * uRockFloatSpeed;
                            // Используем localRand (он уже есть выше в коде) как уникальный сид фазы для каждого камня
                            float phase = localRand * 100.0;
                            // Вертикальное покачивание
                            floatOffset.y = sin(t + phase) * uRockFloatAmp;
                            // Хаотичные отклонения по осям X и Z
                            floatOffset.x = sin(t * 0.8 + phase * 1.5) * (uRockFloatAmp * 0.3);
                            floatOffset.z = cos(t * 0.9 + phase * 2.1) * (uRockFloatAmp * 0.3);
                        }

                        vec3 finalWorldPos = vec3(finalWorldXZ.x, groundY + currentOffset, finalWorldXZ.y) + scaledVertexOffset + floatOffset;
                        vWorldPos = finalWorldPos;

                        float scaleY = length(vec3(instanceMatrix[0][1], instanceMatrix[1][1], instanceMatrix[2][1]));
                        vHeightAboveGround = (finalWorldPos.y - (groundY + currentOffset)) / max(scaleY * 1.5, 1.0);

                        vec4 mvPosition = viewMatrix * vec4(finalWorldPos, 1.0);
                        gl_Position = projectionMatrix * mvPosition;
                        #include <clipping_planes_vertex> 
                    }
                `,
                fragmentShader: `
                    #include <clipping_planes_pars_fragment> 
                    
                    uniform float uTime;
                    uniform vec3 uBaseColor;
                    uniform vec3 uTipColor;
                    uniform float uSmoothness;
                    
                    // --- НОВЫЕ UNIFORMS (ОБЪЯВЛЕНЫ) ---
                    uniform float uFlatShading;
                    uniform float uRockAO;
                    uniform float uCrystalGloss;
                    uniform float uCrystalRatio;
                    uniform float uCrystalIrisSpread;
                    uniform float uCrystalIrisIntensity;
                    // ----------------------------------

                    uniform vec3 uCamPos;
                    uniform vec3 uFogColor;
                    uniform float uFogDensity;
                    uniform vec3 uCrystalBaseColor;
                    uniform vec3 uCrystalTipColor;

                    uniform float uLightEnable;
                    uniform vec3 uLightColor;
                    uniform float uLightIntensity;
                    uniform float uLightRange;
                    uniform float uLightRadius;
                    uniform float uLightFocus;
                    uniform float uLightOffset;
                    uniform vec3 uLightDir;
                    uniform vec3 uCamDir;
                    uniform float uCrystalAlpha;

                    uniform float uFoamOpacity;
                    uniform vec3 uFoamColor;
                    uniform float uFoamWidth;
                    uniform float uFoamNoise;
                    uniform float uRockFoamOpacity;
                    uniform float uRockFoamHeight;

                    uniform float uMossSpread;
                    uniform vec3 uMossColor;

                    uniform float uGlobalLight;

                    #define MAX_POINT_LIGHTS 20
                    uniform vec3 uPointLightPos[MAX_POINT_LIGHTS];
                    uniform vec3 uPointLightColor[MAX_POINT_LIGHTS];
                    uniform vec2 uPointLightParams[MAX_POINT_LIGHTS]; // x: intensity, y: range
                    uniform float uPointLightCount;

                    ${terrainNoiseChunk}
                    ${fastTextureNoiseChunk} 

                    ${volumetricFogChunk}
                    ${cloudNoiseChunk}
                    uniform float uCFogEnabled;
                    uniform vec3 uCFogColor;
                    uniform float uCFogHeight;
                    uniform float uCFogThick;
                    uniform float uCFogDens;
                    uniform float uCFogShape;

                    varying vec3 vWorldPos;
                    varying vec3 vNormal;
                    varying float vVisible;
                    varying float vHeightAboveGround;
                    varying float vIsCrystal;

                    void main() {
                        #include <clipping_planes_fragment> 
                        if (vVisible < 0.5) discard;

                        vec3 smoothNormal = normalize(vNormal);
                        vec3 fdx = dFdx(vWorldPos);
                        vec3 fdy = dFdy(vWorldPos);
                        vec3 flatNormal = normalize(cross(fdx, fdy));
                        if (!gl_FrontFacing) flatNormal = -flatNormal;
                        vec3 norm = normalize(mix(smoothNormal, flatNormal, uFlatShading));

                        float mixFactor = clamp(vHeightAboveGround + 0.1, 0.0, 1.0);
                        mixFactor = pow(mixFactor, uSmoothness);
                        // Умножение на step(0.0001, uCrystalRatio) гарантирует строгое обнуление маски при нулевом ползунке
                        float isCrystalMask = step(vIsCrystal, uCrystalRatio) * step(0.0001, uCrystalRatio);
                        
                        vec3 actualBaseColor = mix(uBaseColor, uCrystalBaseColor, isCrystalMask);
                        vec3 actualTipColor = mix(uTipColor, uCrystalTipColor, isCrystalMask);
                        
                        vec3 finalColor = mix(actualBaseColor, actualTipColor, mixFactor);
                        finalColor *= clamp(vHeightAboveGround + 0.3, 0.0, 1.0);
                        
                        

                        float surfaceAO = clamp(norm.y * 0.5 + 0.5, 0.0, 1.0); 
                        float appliedAO = mix(1.0, surfaceAO, uRockAO);
                        finalColor *= appliedAO;

                        float currentGloss = mix(0.3, uCrystalGloss * 4.0, isCrystalMask);
                        float currentShininess = mix(16.0, 128.0, isCrystalMask);

                        finalColor += finalColor * isCrystalMask * uCrystalGloss * 0.5;

                        vec3 viewDir = normalize(uCamPos - vWorldPos);
                        vec3 shiftVec = vec3(0.0, 2.09, 4.18); 
                        vec3 prism = 0.5 + 0.5 * cos((dot(flatNormal, viewDir) * 10.0 + vIsCrystal * 50.0) * uCrystalIrisSpread + shiftVec);
                        vec3 irisColor = mix(vec3(1.0), prism, clamp(uCrystalIrisSpread, 0.0, 1.0));
                        vec3 baseRockColor = mix(actualBaseColor, actualTipColor, mixFactor); // Для иризации

                        // --- НОВОЕ: ПРОЕКЦИОННЫЙ МОХ / СНЕГ ---
                        // ==========================================
                        if (uMossSpread > 0.0) {
                            // Насколько сильно поверхность смотрит строго вверх (1.0 = верх, 0.0 = вбок/вниз)
                            float upFactor = clamp(smoothNormal.y, 0.0, 1.0);
                            
                            // Добавляем шум из мировых координат для "рваного" органичного края
                            // Используем уже существующую функцию noise()
                            float mossNoise = texNoise(vWorldPos.xz * 0.4) * 0.4 + 0.6; 
                            
                            // Смещение порога: если spread=1, покрывает почти всё, если 0.1 - только плоские макушки
                            float threshold = 1.0 - (uMossSpread * 0.95);
                            float mossMask = smoothstep(threshold - 0.15, threshold + 0.05, upFactor * mossNoise);
                            
                            // Применяем цвет
                            finalColor = mix(finalColor, uMossColor, mossMask * uMossSpread);
                            
                            // Гасим глянец под мхом, делаем его матовым
                            currentGloss = mix(currentGloss, 0.0, mossMask);
                            currentShininess = mix(currentShininess, 1.0, mossMask);
                        }
                        
                        vec3 addedLight = vec3(0.0);
                        
                        // СВЕТ ОТ ПРОЖЕКТОРА
                        if (uLightEnable > 0.5) {
                            vec3 actualLightPos = uCamPos + uCamDir * uLightOffset;
                            vec3 toPixel = vWorldPos - actualLightPos;
                            float distToPixel = length(toPixel);
                            if (distToPixel < uLightRange) {
                                vec3 dirToPixel = normalize(toPixel);
                                float spotEffect = dot(uLightDir, dirToPixel);
                                
                                float outerAngle = mix(0.99, 0.5, uLightRadius);
                                float innerAngle = mix(outerAngle, 1.0, uLightFocus);
                                
                                if (spotEffect > outerAngle) {
                                    float spotMask = smoothstep(outerAngle, innerAngle, spotEffect);
                                    float attenuation = pow(clamp(1.0 - (distToPixel / uLightRange), 0.0, 1.0), 2.0);
                                    float diffuse = max(dot(norm, -dirToPixel), 0.0);
                                    vec3 halfVector = normalize(-dirToPixel + viewDir);
                                    float specular = pow(max(dot(norm, halfVector), 0.0), currentShininess) * currentGloss;

                                    // Дополнительный мощный блик от источника света
                                    float fakeIris = pow(max(dot(norm, halfVector), 0.0), 6.0) * uCrystalIrisIntensity * isCrystalMask;
                                    vec3 irisGlow = baseRockColor * irisColor * fakeIris * 5.0;

                                    addedLight += uLightColor * uLightIntensity * attenuation * spotMask * (diffuse + specular + 0.1);
                                    addedLight += irisGlow * uLightIntensity * attenuation * spotMask;
                                }
                            }
                        }

                        // СВЕТ ОТ СФЕР
                        if (uPointLightCount > 0.0) {
                            for(int i = 0; i < MAX_POINT_LIGHTS; i++) {
                                if (float(i) >= uPointLightCount) break;
                                
                                vec3 toLight = uPointLightPos[i] - vWorldPos;
                                float distToLight = length(toLight);
                                float pIntensity = uPointLightParams[i].x;
                                float pRange = uPointLightParams[i].y;
                                
                                if (distToLight < pRange) {
                                    vec3 dirToLight = toLight / distToLight;
                                    float attenuation = clamp(1.0 - (distToLight / pRange), 0.0, 1.0);
                                    attenuation *= attenuation;
                                    
                                    // У камней нормаль называется 'norm', всё верно
                                    float diffuse = max(dot(norm, dirToLight), 0.0); 
                                    addedLight += uPointLightColor[i] * pIntensity * attenuation * (0.4 + diffuse * 0.6);
                                    
                                    // Блики на кристаллах от цветных источников
                                    if (isCrystalMask > 0.5) {
                                        vec3 halfVector = normalize(dirToLight + viewDir);
                                        float specular = pow(max(dot(norm, halfVector), 0.0), currentShininess) * currentGloss;
                                        float fakeIris = pow(max(dot(norm, halfVector), 0.0), 6.0) * uCrystalIrisIntensity;
                                        vec3 irisGlow = baseRockColor * irisColor * fakeIris * 5.0;
                                        
                                        addedLight += uPointLightColor[i] * pIntensity * attenuation * specular;
                                        addedLight += irisGlow * pIntensity * attenuation;
                                    }
                                }
                            }
                        }
                        vec3 lightMix = mix(finalColor * 2.0, vec3(1.0), 0.6); 
                        finalColor += addedLight * lightMix;

                        // =========================================================================
                        // НОВАЯ НЕЗАВИСИМАЯ ИРИЗАЦИЯ КРИСТАЛЛОВ (БЕЗ СВЕТА)
                        // =========================================================================
                        if (isCrystalMask > 0.5 && uCrystalIrisIntensity > 0.001) {
                            // Насколько прямо грань смотрит на камеру (1.0 = прямо, 0.0 = боком)
                            float facingCamera = abs(dot(flatNormal, viewDir));
                            
                            // Усиливаем свечение граней, смотрящих на нас, но оставляем базовый уровень (0.2) для остальных
                            float viewGlow = pow(facingCamera, 1.5) * 0.8 + 0.2;
                            
                            // Сила иризации
                            float ambientIrisStrength = viewGlow * uCrystalIrisIntensity;
                            
                            // Смешиваем переливающийся цвет
                            vec3 ambientIrisGlow = baseRockColor * irisColor * ambientIrisStrength * (1.0 + uCrystalGloss * 2.0);
                            
                            finalColor += ambientIrisGlow;
                        }
                        // =========================================================================

                        if (uCFogEnabled > 0.5) {
                            float fogTop = uCFogHeight + uCFogThick;
                            vec4 vFog = calcVolumetricFog(uCamPos, vWorldPos, fogTop, uCFogHeight, uCFogDens, uCFogShape, uTime, uCFogColor);
                            float distFade = smoothstep(0.0, 150.0, length(vWorldPos.xz - uCamPos.xz));
                            finalColor = mix(finalColor, vFog.rgb, vFog.a * distFade);
                        }

                        float dist = length(vWorldPos.xz - uCamPos.xz);
                        float fogFactor = clamp(1.0 - exp(-pow(dist * uFogDensity, 2.0)), 0.0, 1.0);
                        // --- ПРИМЕНЕНИЕ ТЕНЕЙ ОТ ОБЛАКОВ ---
                        if (uShadowsEnabled > 0.5 && uIsReflectionPass < 0.5) {
                            float shadowDens = getShadowDensity(vWorldPos.xz, uTime);
                            finalColor = mix(finalColor, uShadowColor, shadowDens * uShadowOpacity);
                        }


                        finalColor = mix(finalColor, uFogColor, fogFactor);

                        if (uRockFoamOpacity > 0.0 && vWorldPos.y >= -1.0 && vWorldPos.y < 20.0) {
                            vec2 safeXZ = mod(vWorldPos.xz, 10000.0); 
                            float h = max(0.0, vWorldPos.y); 
                            float t = uTime * 2.0;
                            float wavePhase = (safeXZ.x * 0.6 + safeXZ.y * 0.8) - t;
                            float wave = sin(wavePhase) * 0.5 + 0.5;
                            float n1 = texNoise(safeXZ * 3.0 - t * 0.5);
                            float n2 = texNoise(safeXZ * 10.0 + t * 0.8);
                            float combinedNoise = (n1 * 0.7 + n2 * 0.3);
                            float splashHeight = 0.5 + (uRockFoamHeight * 0.35) + (wave * 2.5);
                            splashHeight += combinedNoise * uFoamNoise * 4.0; 
                            float wetMask = 1.0 - smoothstep(splashHeight * 0.3, splashHeight + 2.5, h);
                            finalColor *= mix(1.0, 0.35, wetMask * uRockFoamOpacity); 
                            if (h < splashHeight) {
                                float foamAlpha = 1.0 - smoothstep(splashHeight * 0.1, splashHeight, h);
                                float bubbles = smoothstep(0.1, 0.8, combinedNoise + foamAlpha);
                                float waterLine = 1.0 - smoothstep(0.0, 0.6, h);
                                float rockFoamMask = clamp((foamAlpha * bubbles + waterLine * 0.8) * uRockFoamOpacity * 1.5, 0.0, 1.0);
                                finalColor = mix(finalColor, uFoamColor, rockFoamMask);
                            }
                        }

                        // РАСЧЕТ ПРОЗРАЧНОСТИ КРИСТАЛЛОВ
                        float finalAlpha = 1.0 - (uCrystalAlpha * isCrystalMask);

                        finalColor *= uGlobalLight;

                        gl_FragColor = vec4(finalColor, finalAlpha); // <--- ИЗМЕНЕН ИТОГОВЫЙ ЦВЕТ
                    }
                `,
                side: THREE.DoubleSide,
                clipping: true,
                transparent: true,      // <--- ДОБАВИТЬ ЭТО
                depthWrite: true        // <--- ДОБАВИТЬ ЭТО (помогает избежать багов сортировки instancedMesh)
            });

            const mesh = new THREE.InstancedMesh(geometry, material, count);
            mesh.frustumCulled = false;

            const dummy = new THREE.Object3D();
            const drawDist = CONFIG.rocks.drawDistance;

            for (let i = 0; i < count; i++) {
                dummy.position.set(
                    (Math.random() - 0.5) * drawDist,
                    0,
                    (Math.random() - 0.5) * drawDist
                );
                
                dummy.rotation.set(
                    (Math.random() - 0.5) * 0.6,
                    Math.random() * Math.PI * 2, 
                    (Math.random() - 0.5) * 0.6  
                );

                let baseSize = CONFIG.rocks.size;
                baseSize *= mix(1.0 - CONFIG.rocks.sizeVar, 1.0 + CONFIG.rocks.sizeVar, Math.random());
                
                if (isBoulder) baseSize *= (3.0 + Math.random() * 5.0);

                const crystalFactor = shape; 
                let scaleX, scaleY, scaleZ;

                // Базовая форма (шарообразная)
                const sphereX = 0.8 + Math.random() * 0.4;
                const sphereY = 0.8 + Math.random() * 0.4;
                const sphereZ = 0.8 + Math.random() * 0.4;

                // Если ползунок больше 0, начинаем примешивать разнообразные угловатые формы
                if (crystalFactor > 0.01) {
                    const randType = Math.random();
                    let targetX, targetY, targetZ;

                    if (randType < 0.25) {
                        // 1. Вытянутый кристалл / Столб (тонкий и высокий)
                        targetX = 0.3 + Math.random() * 0.4;
                        targetY = 1.5 + Math.random() * 3.0;
                        targetZ = 0.3 + Math.random() * 0.4;
                    } else if (randType < 0.5) {
                        // 2. Плоская плита (широкая, но низкая)
                        targetX = 1.2 + Math.random() * 1.5;
                        targetY = 0.15 + Math.random() * 0.3;
                        targetZ = 1.2 + Math.random() * 1.5;
                    } else if (randType < 0.75) {
                        // 3. Отвесная стена / Скала (широкая по одной оси, высокая, тонкая по другой)
                        targetX = 1.0 + Math.random() * 1.5;
                        targetY = 1.0 + Math.random() * 2.0;
                        targetZ = 0.2 + Math.random() * 0.4;
                    } else {
                        // 4. Хаотичная угловатая глыба
                        targetX = 0.5 + Math.random() * 1.5;
                        targetY = 0.5 + Math.random() * 1.5;
                        targetZ = 0.5 + Math.random() * 1.5;
                    }

                    // Плавно смешиваем шарообразную форму с выбранной случайной формой
                    scaleX = baseSize * mix(sphereX, targetX, crystalFactor);
                    scaleY = baseSize * mix(sphereY, targetY, crystalFactor);
                    scaleZ = baseSize * mix(sphereZ, targetZ, crystalFactor);
                } else {
                    // Если ползунок на 0, оставляем обычные шары
                    scaleX = baseSize * sphereX;
                    scaleY = baseSize * sphereY;
                    scaleZ = baseSize * sphereZ;
                }
                // --- ЛОГИКА СРЕДНЕЙ ВЫСОТЫ (ПЛОСКИЕ / ВЫСОКИЕ) ---
                let hBias = CONFIG.rocks.heightBias;
                
                // Если ползунок влево (< 0.5), сплющиваем высоту и немного расширяем камни.
                // Если ползунок вправо (> 0.5), вытягиваем высоту.
                let heightMod = (hBias <= 0.5) 
                    ? mix(0.1, 1.0, hBias * 2.0)  // От 10% до 100% высоты
                    : mix(1.0, 5.0, (hBias - 0.5) * 2.0); // От 100% до 500% высоты
                
                // Для плоских камней слегка увеличиваем их ширину, чтобы они выглядели как плиты
                let widthMod = (hBias <= 0.5) ? mix(1.5, 1.0, hBias * 2.0) : 1.0;

                scaleX *= widthMod;
                scaleZ *= widthMod;
                scaleY *= heightMod;
                // -------------------------------------------------

                dummy.scale.set(scaleX, scaleY, scaleZ);
                dummy.updateMatrix();
                mesh.setMatrixAt(i, dummy.matrix);
            }

            mesh.instanceMatrix.needsUpdate = true;
            this.group.add(mesh);
            return mesh;
        };

        // Вычисляем количество и строим
        const boulderCount = Math.floor(CONFIG.rocks.count * CONFIG.rocks.boulderRatio);
        const smallCount = CONFIG.rocks.count - boulderCount;

        this.meshSmall = createMesh(false, smallCount);
        this.meshBoulder = createMesh(true, boulderCount);

        this.updateVisibility();
    }

    updateVisibility() {
        this.group.visible = CONFIG.ui.groundMode && CONFIG.rocks.enabled;
    }

    update(camPos, time) {
        if (!this.group.visible) return;
        
        const updateMat = (mesh) => {
            if (!mesh) return;
            const mat = mesh.material;
            mat.uniforms.uTime.value = time;
            mat.uniforms.uCamPos.value.copy(camPos);
            
            // Синхронизация с общими настройками
            mat.uniforms.uAmplitude.value = CONFIG.terrain.amplitude;
            mat.uniforms.uFrequency.value = CONFIG.terrain.frequency;
            mat.uniforms.uOffset.value = CONFIG.terrain.offset;
            mat.uniforms.uSharpness.value = CONFIG.terrain.sharpness;
            mat.uniforms.uFogColor.value.copy(CONFIG.terrain.fogColor);
            mat.uniforms.uFogDensity.value = CONFIG.terrain.fogDensity;

            mat.uniforms.uFoamOpacity.value = CONFIG.water.foamOpacity;
            mat.uniforms.uRockFoamOpacity.value = CONFIG.rocks.rockFoamOpacity;
            mat.uniforms.uRockFoamHeight.value = CONFIG.rocks.rockFoamHeight;
            mat.uniforms.uFoamColor.value.copy(CONFIG.water.foamColor);
            mat.uniforms.uFoamWidth.value = CONFIG.water.foamWidth;
            mat.uniforms.uFoamNoise.value = CONFIG.water.foamNoise;
            
            // Группировка
            mat.uniforms.uRockStruct.value = CONFIG.rocks.struct;
            mat.uniforms.uRockThin.value = CONFIG.rocks.thin;

            // Освещение
            mat.uniforms.uLightEnable.value = (CONFIG.flashlight.enabled && CONFIG.flashlight.affectRocks) ? 1.0 : 0.0;
            mat.uniforms.uLightDir.value.copy(globalUniforms.uLightDir.value);
            mat.uniforms.uCamDir.value.copy(globalUniforms.uCamDir.value);
            mat.uniforms.uLightRadius.value = CONFIG.flashlight.radius;
            mat.uniforms.uLightFocus.value = CONFIG.flashlight.focus;
            mat.uniforms.uLightOffset.value = CONFIG.flashlight.offset;
            
            // Сферы (ИСПРАВЛЕНО)
            // УДАЛЕН СТАРЫЙ КОД СФЕР. 
            // Теперь свет управляется глобальным массивом в функции animate(),
            // поэтому здесь обновлять ничего, связанного с точечным светом, не нужно!
        };

        updateMat(this.meshSmall);
        updateMat(this.meshBoulder);
    }
}
// Вспомогательная функция (если у вас её еще нет глобально)
function mix(a, b, t) { return a * (1 - t) + b * t; }


// --- СИСТЕМА УПАВШИХ ЗВЕЗД (КРИСТАЛЛОВ НА ЗЕМЛЕ) ---
class FallenStarSystem {
    constructor(scene) {
        this.scene = scene;
        this.group = new THREE.Group();
        this.scene.add(this.group);
        
        this.stars = [];
        this.maxStars = 20; 
        
        // Увеличиваем базовый радиус кристалла до 6.5
        this.geometry = new THREE.OctahedronGeometry(6.5, 0); 
    }

    spawn(pos, color) {
        // Если лимит превышен, удаляем самый старый камень
        if (this.stars.length >= this.maxStars) {
            const oldStar = this.stars.shift();
            this.group.remove(oldStar);
            oldStar.material.dispose();
            // Удаляем ореол
            oldStar.children.forEach(c => {
                if (c.material && c.material !== haloMaterial) c.material.dispose();
            });
        }

        // Материал самого камня (яркий, не реагирует на тени)
        const coreColor = color.clone().multiplyScalar(2.5);
        
        // Материал самого камня
        const mat = new THREE.MeshBasicMaterial({ 
            color: coreColor, 
            transparent: true,
            opacity: 1.0
        });
        
        const mesh = new THREE.Mesh(this.geometry, mat);
        
        // Рандомный поворот, чтобы выглядело естественно воткнувшимся в землю
        mesh.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, Math.random() * Math.PI);
        
        // Слегка приподнимаем, чтобы центр не был под текстурой земли
        mesh.position.copy(pos);
        mesh.position.y += 3.0; 

        // Создаем спрайт свечения (ореол) вокруг камня
        const halo = new THREE.Sprite(haloMaterial.clone());
        halo.material.color.copy(color);
        // Уменьшаем визуальный размер свечения в 3-4 раза
        halo.scale.set(30, 30, 1); 
        mesh.add(halo);

        // Сохраняем время появления для анимации пульсации
        mesh.userData = { spawnTime: performance.now() / 1000 };

        this.group.add(mesh);
        this.stars.push(mesh);
    }

    update(time) {
        const currentTime = performance.now() / 1000;
        
        // Проходим по массиву с конца, чтобы безопасно удалять элементы
        for (let i = this.stars.length - 1; i >= 0; i--) {
            const star = this.stars[i];
            const age = currentTime - star.userData.spawnTime; // Время жизни в секундах

            // 1. Удаление после 60 секунд (вместо 20.0)
            if (age > 60.0) {
                this.group.remove(star);
                star.material.dispose();
                if (star.children[0]) {
                    star.children[0].material.dispose();
                }
                this.stars.splice(i, 1);
                continue;
            }

            // 2. Анимация затухания перед исчезновением (последние 2 секунды)
            let fade = 1.0;
            if (age > 58.0) { // Начинаем затухание на 58-й секунде (вместо 13.0)
                fade = (60.0 - age) / 2.0; // Плавный переход от 1.0 к 0.0 (вместо 15.0)
            }

            const t = time * 2.0 + star.userData.spawnTime;
            const pulse = 0.85 + 0.15 * Math.sin(t);
            
            // Применяем размер и прозрачность
            star.scale.set(pulse * fade, pulse * fade, pulse * fade);
            star.material.opacity = fade; 
            
            // Гало
            if (star.children[0]) {
                star.children[0].material.opacity = (0.6 + 0.4 * Math.sin(t * 4.0)) * fade;
            }
        }
    }
}






// Универсальная функция заполнения конкретного набора с учетом чекбоксов
function populateLightSet(lightSet, affectSpheres, affectComets) {
    let count = 0;
    const maxLights = Math.min(CONFIG.lighting.maxPointLights, MAX_POINT_LIGHTS);
    const lightDist = CONFIG.lighting.lightDistance;

    // 1. СФЕРЫ ХРАНИТЕЛИ
    if (affectSpheres && CONFIG.sphereLights.enabled && sphereSystem.items.length > 0) {
        for(let i = 0; i < sphereSystem.items.length; i++) {
            if (i >= sphereSystem.activeCount || count >= maxLights) break; 
            
            // Отсечение по дистанции
            if (sphereSystem.items[i].pos.distanceTo(camera.position) > lightDist) continue;

            lightSet.positions[count].copy(sphereSystem.items[i].pos);
            lightSet.colors[count].copy(sphereSystem.items[i].color);
            lightSet.params[count].set(CONFIG.sphereLights.intensity, CONFIG.sphereLights.range);
            count++;
        }
    }

    // 2. УПАВШИЕ КОМЕТЫ (Кристаллы на земле)
    if (affectComets && CONFIG.cometLights.enabled && fallenStarSystem.stars.length > 0) {
        for(let i = 0; i < fallenStarSystem.stars.length; i++) {
            if (count >= maxLights) break;
            
            const star = fallenStarSystem.stars[i];
            if (star.position.distanceTo(camera.position) > lightDist) continue;

            lightSet.positions[count].copy(star.position);
            lightSet.colors[count].copy(star.material.color).multiplyScalar(0.15);
            lightSet.params[count].set(CONFIG.cometLights.intensity, CONFIG.cometLights.range);
            count++;
        }
    }
    
    // Очищаем неиспользованные слоты (сдвигаем старые координаты под землю)
    for(let i = count; i < MAX_POINT_LIGHTS; i++) {
        lightSet.positions[i].set(0, -9999, 0);
        lightSet.colors[i].set(0x000000);
        lightSet.params[i].set(0, 0);
    }

    return count;
}

// Инициализация модуля видео
const videoManager = new VideoCaptureManager(scene, camera, renderer, globalUniforms, getTerrainHeight);

document.getElementById('video-btn')?.addEventListener('click', () => {
    videoManager.open();
});
const reflectionSystem = new ReflectionSystem(scene, camera);

const skyDome = new SkyDomeSystem(scene);

class TerrainSystem {
    constructor(scene) {
        const geo = new THREE.PlaneGeometry(16000, 16000, 256, 256);
        geo.rotateX(-Math.PI / 2);

        this.material = new THREE.ShaderMaterial({
            uniforms: {
                uTime: { value: 0 },
                uCamPos: { value: new THREE.Vector3() },
                uCamDir: { value: new THREE.Vector3() },
                uColorGrass: { value: CONFIG.terrain.grassColor }, 
                uColorWater: { value: CONFIG.terrain.waterColor },
                uColorPeak: { value: CONFIG.terrain.peakColor },
                uFogColor: { value: CONFIG.terrain.fogColor },
                uAmplitude: { value: CONFIG.terrain.amplitude },
                uFrequency: { value: CONFIG.terrain.frequency },
                uOffset: { value: CONFIG.terrain.offset },
                uSharpness: { value: CONFIG.terrain.sharpness },
                uShowGrid: { value: CONFIG.terrain.showGrid ? 1.0 : 0.0 },
                uVisibility: { value: CONFIG.terrain.visibility },
                uFogDensity: { value: CONFIG.terrain.fogDensity },
                uAoStrength: { value: CONFIG.terrain.aoStrength },
                uSmoothing: { value: CONFIG.terrain.smoothing },

                uColorDeepWater: { value: CONFIG.terrain.deepWaterColor }, // <--- НОВОЕ
                uWaterDepthFactor: { value: CONFIG.terrain.waterDepthFactor }, // <--- НОВОЕ
                uStrataEnabled: { value: CONFIG.terrain.strataEnabled ? 1.0 : 0.0 }, // <--- НОВОЕ
                uStrataFreq: { value: CONFIG.terrain.strataFreq }, // <--- НОВОЕ
                uStrataStrength: { value: CONFIG.terrain.strataStrength }, // <--- НОВОЕ

                uShoreOpacity: { value: CONFIG.water.shoreOpacity },
                uShoreColor: { value: CONFIG.water.shoreColor },

                uFoamOpacity: { value: CONFIG.water.foamOpacity },
                uFoamColor: { value: CONFIG.water.foamColor },
                uFoamWidth: { value: CONFIG.water.foamWidth },
                uFoamCount: { value: CONFIG.water.foamCount },
                uFoamSpacing: { value: CONFIG.water.foamSpacing }, // <--- ДОБАВИТЬ ЭТУ СТРОКУ
                uFoamNoise: { value: CONFIG.water.foamNoise },

                uLightRadius: { value: CONFIG.flashlight.radius },
                uLightDir: { value: new THREE.Vector3() },

                uLightFocus: { value: CONFIG.flashlight.focus },
                uLightOffset: { value: CONFIG.flashlight.offset },

                uGlobalLight: { value: CONFIG.lighting.globalIntensity },

                uPointLightPos: { value: terrainLightSet.positions },
                uPointLightColor: { value: terrainLightSet.colors },
                uPointLightParams: { value: terrainLightSet.params },
                uPointLightCount: { value: 0 },

                uCFogEnabled: { value: CONFIG.terrain.creepingFogEnabled ? 1.0 : 0.0 },
                uCFogColor: { value: CONFIG.terrain.creepingFogColor },
                uCFogHeight: { value: CONFIG.terrain.creepingFogHeight },
                uCFogThick: { value: CONFIG.terrain.creepingFogThickness },
                uCFogDens: { value: CONFIG.terrain.creepingFogDensity },
                uCFogShape: { value: CONFIG.terrain.creepingFogShape },
                ...creepingFogUniforms,
                ...sharedCloudUniforms,

                uReflectionMap: { value: reflectionSystem.renderTarget.texture },
                uReflectEnabled: { value: CONFIG.water.reflections ? 1.0 : 0.0 },
                uReflectIntensity: { value: CONFIG.water.intensity },
                uReflectDist: { value: CONFIG.water.distortion },
                
                // --- НОВЫЕ UNIFORMS ---
                uReflectStretch: { value: CONFIG.water.rippleStretch },
                uReflectBlur: { value: CONFIG.water.blurStrength },
                uReflectEdgeDark: { value: CONFIG.water.edgeDarkening },
                uReflectDistStart: { value: CONFIG.water.distBlurStart },
                uReflectDistMax: { value: CONFIG.water.distBlurMax },

                uColorSnow: { value: CONFIG.terrain.snowColor },
                
                uLightEnable: { value: CONFIG.flashlight.enabled ? 1.0 : 0.0 },
                uLightColor: { value: CONFIG.flashlight.color },
                uLightIntensity: { value: CONFIG.flashlight.intensity },
                uLightRange: { value: CONFIG.flashlight.range }
            },
            vertexShader: `
                #include <clipping_planes_pars_vertex> // <--- 1. ДОБАВИТЬ В САМОЕ НАЧАЛО ШЕЙДЕРА
                uniform float uTime;
                uniform vec3 uCamPos;
                uniform float uAmplitude;
                uniform float uFrequency;
                uniform float uOffset;
                uniform float uSharpness;


                
                varying vec2 vUv;
                varying float vElevation;
                varying float vRawElevation; 
                varying vec3 vWorldPos;

                ${terrainNoiseChunk}
                varying vec4 vScreenPos;

                void main() {
                    vUv = uv;
                    vec3 pos = position;
                    
                    float stepSize = 62.5; 
                    pos.x += floor(uCamPos.x / stepSize) * stepSize;
                    pos.z += floor(uCamPos.z / stepSize) * stepSize;
                    
                    vWorldPos = pos;

                    float elev = noise(pos.xz * uFrequency) * uAmplitude;
                    elev += noise(pos.xz * uFrequency * 5.0) * (uAmplitude * 0.33);
                    
                    float rawElev = elev - uOffset;
                    vRawElevation = rawElev; 
                    
                    float finalElev = 0.0;
                    if (rawElev > 0.0) {
                        finalElev = pow(rawElev / uAmplitude, uSharpness) * uAmplitude;
                    }
                    
                    pos.y += finalElev;
                    vElevation = finalElev;

                    // --- ИЗМЕНЕННЫЙ КОНЕЦ ---
                    vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
                    vScreenPos = projectionMatrix * mvPosition;
                    gl_Position = vScreenPos;
                    #include <clipping_planes_vertex> // <--- 2. ДОБАВИТЬ ПЕРЕД ЗАКРЫВАЮЩЕЙ СКОБКОЙ
                }
            `,
            fragmentShader: `
                #include <clipping_planes_pars_fragment> // <--- 1. ДОБАВИТЬ В САМОЕ НАЧАЛО
                
                ${terrainNoiseChunk}
                ${fastTextureNoiseChunk} // <-- Добавили
                ${volumetricFogChunk} 
                ${cloudNoiseChunk}

                uniform float uTime; 
                uniform vec3 uColorGrass;
                uniform vec3 uColorWater;
                uniform vec3 uColorPeak;
                uniform vec3 uFogColor;
                uniform float uShowGrid;
                uniform vec3 uColorSnow;
                uniform float uVisibility;
                uniform float uFogDensity;
                uniform float uAmplitude;
                uniform float uAoStrength;
                uniform float uSmoothing;
                uniform vec3 uColorDeepWater;
                uniform float uWaterDepthFactor;
                uniform float uStrataEnabled;
                uniform float uStrataFreq;
                uniform float uStrataStrength;

                uniform float uFoamOpacity;
                uniform vec3 uFoamColor;
                uniform float uFoamWidth;
                uniform float uFoamCount;
                uniform float uFoamNoise;
                 uniform float uFoamSpacing;

                // ===================================
                // ДОБАВЬТЕ ЭТИ ДВЕ СТРОКИ СЮДА:
                uniform float uShoreOpacity;
                uniform vec3 uShoreColor;
                // ===================================

                uniform float uLightFocus;

                uniform float uLightOffset;

                uniform sampler2D uReflectionMap;
                uniform float uReflectEnabled;
                uniform float uReflectIntensity;
                uniform float uReflectDist;

                uniform float uGlobalLight;

                #define MAX_POINT_LIGHTS 20
                uniform vec3 uPointLightPos[MAX_POINT_LIGHTS];
                uniform vec3 uPointLightColor[MAX_POINT_LIGHTS];
                uniform vec2 uPointLightParams[MAX_POINT_LIGHTS]; // x: intensity, y: range
                uniform float uPointLightCount;             
                
                // --- НОВЫЕ UNIFORMS ---
                uniform float uReflectStretch;
                uniform float uReflectBlur;
                uniform float uReflectEdgeDark;
                uniform float uReflectDistStart;
                uniform float uReflectDistMax;

                varying vec4 vScreenPos;
                
                uniform float uLightEnable;
                uniform vec3 uLightColor;
                uniform float uLightIntensity;
                uniform float uLightRange;
                uniform vec3 uCamDir;
                // --- ДОБАВЛЕННЫЕ СТРОКИ ---
                uniform vec3 uLightDir;
                uniform float uLightRadius;

                uniform float uCFogEnabled;
                uniform vec3 uCFogColor;
                uniform float uCFogHeight;
                uniform float uCFogThick;
                uniform float uCFogDens;
                uniform float uCFogShape;
                
                varying float vElevation;
                varying float vRawElevation;
                varying vec3 vWorldPos;
                
                void main() {
                    #include <clipping_planes_fragment> // <--- 2. ДОБАВИТЬ СРАЗУ ПОСЛЕ void main() {
                    
                    vec3 finalColor;
                    vec2 safeXZ = mod(vWorldPos.xz, 10000.0);
                    
                    float blendWidth = max(0.1, uSmoothing * 15.0);
                    float waterMask = smoothstep(blendWidth, 0.0, vElevation);
                    float heightFactor = clamp(vElevation / (uAmplitude * 1.5), 0.0, 1.0);

                    vec3 groundColor;
                    if (heightFactor < 0.45) {
                        groundColor = mix(uColorGrass, uColorPeak, heightFactor / 0.45);
                    } else {
                        groundColor = mix(uColorPeak, uColorSnow, (heightFactor - 0.45) / 0.55);
                    }

                    vec3 normal = normalize(vec3(-dFdx(vElevation), 1.0, -dFdy(vElevation)));
                    float slopeFactor = normal.y; 

                    // ==========================================
                    // НОВОЕ: СЛОИСТОСТЬ (STRATA) ДЛЯ ГОР
                    // ==========================================
                    if (uStrataEnabled > 0.5 && vElevation > 0.0) {
                        // 1. Делаем резкие "ступеньки" (полосы) вместо мягкого градиента
                        float strata = sin(vWorldPos.y * uStrataFreq);
                        float strataMask = smoothstep(0.0, 0.15, strata); // Резкая граница слоев
                        
                        // 2. Расширяем маску склонов, чтобы слои были видны не только на отвесных скалах
                        float wallMask = smoothstep(0.98, 0.45, slopeFactor);
                        
                        // 3. Создаем контрастный цвет для слоев (высветляем базу и делаем чуть теплее/пыльнее)
                        vec3 strataColor = groundColor * 1.8 + vec3(0.05, 0.03, 0.0);
                        
                        // 4. Смешиваем базовый цвет скалы с цветом слоев
                        groundColor = mix(groundColor, strataColor, strataMask * uStrataStrength * wallMask);
                    }
                    float valley = 1.0 - smoothstep(0.0, uAmplitude * 0.5, vElevation);
                    
                    float ao = mix(1.0, slopeFactor, uAoStrength * 0.9); 
                    ao -= valley * uAoStrength * 0.4;                    
                    groundColor *= clamp(ao, 0.15, 1.0);

                    float distCamXZ = length(vWorldPos.xz - cameraPosition.xz);
                    if (distCamXZ > uVisibility) discard;
                    float fogFactor = clamp(1.0 - exp(-pow(distCamXZ * uFogDensity, 2.0)), 0.0, 1.0);
                    
                    vec3 currentWaterColor = uColorWater;

                    if (waterMask > 0.0) {
                        // ==========================================
                        // НОВОЕ: ОБЪЕМ ВОДЫ (БЕЗДНА)
                        // ==========================================
                        float depth = max(0.0, -vRawElevation);
                        float depthMix = clamp(depth * uWaterDepthFactor, 0.0, 1.0);
                        currentWaterColor = mix(uColorWater, uColorDeepWater, depthMix);
                        // --- ИСКАЖЕНИЯ С РАСТЯЖЕНИЕМ ---
                        float t = uTime * 0.6; 
                        vec2 wavePos = safeXZ * vec2(1.0, 1.0 / max(0.1, uReflectStretch));
                        
                        float wave1 = sin(wavePos.x * 0.015 + t) * cos(wavePos.y * 0.012 - t * 0.8);
                        float wave2 = sin(wavePos.x * 0.04 - t * 1.2) * sin(wavePos.y * 0.05 + t * 1.1);
                        float fineNoise = texNoise(safeXZ * 0.1 - vec2(t, t)) - 0.5;
                        
                        float distScale = clamp(300.0 / max(1.0, distCamXZ), 0.1, 1.0);
                        vec2 rippleDistort = vec2(wave1 + fineNoise, wave2 + fineNoise) * uReflectDist * 0.2 * distScale;

                        if (uReflectEnabled > 0.5) {
                            vec2 refUv = (vScreenPos.xy / vScreenPos.w) * 0.5 + 0.5;
                            
                            // =====================================================
                            // ИСПРАВЛЕНИЕ: ИНВЕРСИЯ X ДЛЯ ОТРАЖЕНИЙ
                            // Убирает эффект "обратного движения" (параллакса)
                            // =====================================================
                            refUv.x = 1.0 - refUv.x;
                            
                            refUv += rippleDistort;
                            refUv = clamp(refUv, 0.001, 0.999);
                            
                            // --- ПРОИЗВОДИТЕЛЬНЫЙ 5-ТОЧЕЧНЫЙ БЛЮР С УЧЕТОМ ДАЛЬНОСТИ ---
                            float distBlurFactor = smoothstep(uReflectDistStart, uReflectDistStart + 2000.0, distCamXZ);
                            float totalSpread = (uReflectBlur * 0.01) + (distBlurFactor * uReflectDistMax);

                            vec3 reflection;
                            // Если размытие нулевое - делаем ОДИН sample вместо ПЯТИ
                            if (totalSpread < 0.001) {
                                reflection = texture2D(uReflectionMap, refUv).rgb;
                            } else {
                                reflection  = texture2D(uReflectionMap, refUv).rgb * 0.36;
                                reflection += texture2D(uReflectionMap, refUv + vec2(totalSpread, 0.0)).rgb * 0.16;
                                reflection += texture2D(uReflectionMap, refUv - vec2(totalSpread, 0.0)).rgb * 0.16;
                                reflection += texture2D(uReflectionMap, refUv + vec2(0.0, totalSpread)).rgb * 0.16;
                                reflection += texture2D(uReflectionMap, refUv - vec2(0.0, totalSpread)).rgb * 0.16;
                            }

                            currentWaterColor = mix(uColorWater, reflection, uReflectIntensity);
                        }
                        
                        // --- ЗАТЕМНЕНИЕ БЕРЕГОВ (EDGE DARKENING) ---
                        // Абсолютная глубина воды (0 на берегу, растет к центру)
                        
                        // Чем больше ползунок uReflectEdgeDark, тем шире зона затемнения
                        float shoreWidth = max(1.0, uAmplitude * uReflectEdgeDark * 2.0);
                        float shoreFactor = 1.0 - smoothstep(0.0, shoreWidth, depth);
                        
                        // Смешиваем текущий цвет с очень темным синим/черным по краям
                        currentWaterColor = mix(currentWaterColor, currentWaterColor * 0.15, shoreFactor * clamp(uReflectEdgeDark * 1.5, 0.0, 1.0));
                        if (uFoamOpacity > 0.0 || uShoreOpacity > 0.0) {
                            vec3 combinedFoamColor = currentWaterColor;
                            
                            // 1. БАЗОВАЯ КРОМКА БЕРЕГА (Shore Foam)
                            if (uShoreOpacity > 0.0) {
                                // Плавный градиент от берега (depth == 0)
                                float shoreFade = 1.0 - smoothstep(0.0, uFoamWidth * 0.4, depth);
                                // Шум для неровного края
                                float shoreNoise = texNoise(safeXZ * 0.2 - uTime * 0.2);
                                shoreFade *= mix(1.0, smoothstep(-0.5, 0.5, shoreNoise), uFoamNoise * 0.5);
                                
                                combinedFoamColor = mix(combinedFoamColor, uShoreColor, shoreFade * uShoreOpacity);
                            }

                            // 2. ДИНАМИЧЕСКИЕ ЛИНИИ ВОЛН (Wave Lines)
                            if (uFoamOpacity > 0.0) {
                                float waveMask = 0.0;
                                float numLines = max(1.0, uFoamCount);
                                
                                float spacing = uFoamSpacing;
                                float wDepth = depth + texNoise(safeXZ * 0.1 + uTime * 0.3) * uFoamWidth * uFoamNoise * 0.3;

                                for (float i = 0.0; i < 4.0; i++) {
                                    if (i >= uFoamCount) break;

                                    // Сдвиг +0.8 отдаляет накатывающие волны от береговой базы, чтобы они не слипались
                                    float targetDepth = (i + 0.8) * spacing; 
                                    float thickness = spacing * 0.3 * (1.0 - (i / numLines) * 0.5);

                                    float lineNoise = texNoise(safeXZ * 0.2 + vec2(uTime * 0.8, i * 12.0));
                                    float currentThickness = thickness * mix(1.0, lineNoise * 2.5, uFoamNoise);

                                    float distToLine = abs(wDepth - targetDepth);
                                    float line = 1.0 - smoothstep(currentThickness * 0.1, currentThickness, distToLine);

                                    float breakNoise = texNoise(safeXZ * 0.04 - vec2(uTime * 0.2, i * 7.0));
                                    float breakMask = smoothstep(uFoamNoise * 0.6, 1.0, breakNoise + 0.4);

                                    waveMask += line * mix(1.0, breakMask, uFoamNoise);
                                }
                                
                                waveMask = clamp(waveMask, 0.0, 1.0);
                                float zoneFade = 1.0 - smoothstep(uFoamWidth * 0.5, uFoamWidth * 1.2, depth);
                                waveMask *= zoneFade * uFoamOpacity;

                                combinedFoamColor = mix(combinedFoamColor, uFoamColor, waveMask);
                            }
                            
                            currentWaterColor = combinedFoamColor;
                        }
                    }

                    finalColor = mix(groundColor, currentWaterColor, waterMask);
                                        
                    vec3 addedLight = vec3(0.0);

                    if (uLightEnable > 0.5) {
                        vec3 actualLightPos = cameraPosition + uCamDir * uLightOffset;
                        vec3 toPixel = vWorldPos - actualLightPos;
                        float distToPixel = length(toPixel);
                        
                        if (distToPixel < uLightRange) {
                            vec3 dirToPixel = normalize(toPixel);
                            float spotEffect = dot(uLightDir, dirToPixel); 
                            
                            float outerAngle = mix(0.99, 0.5, uLightRadius);
                            float innerAngle = mix(outerAngle, 1.0, uLightFocus);
                            
                            if (spotEffect > outerAngle) { 
                                float spotMask = smoothstep(outerAngle, innerAngle, spotEffect);
                                float attenuation = pow(clamp(1.0 - (distToPixel / uLightRange), 0.0, 1.0), 2.0); 
                                float diffuse = max(dot(normal, -dirToPixel), 0.0);
                                finalColor += uLightColor * uLightIntensity * attenuation * spotMask * (0.3 + diffuse * 0.7);
                            }
                        }
                    }

                    if (uPointLightCount > 0.0) {
                        for(int i = 0; i < MAX_POINT_LIGHTS; i++) {
                            if (float(i) >= uPointLightCount) break;
                            
                            vec3 toLight = uPointLightPos[i] - vWorldPos;
                            float distToLight = length(toLight);
                            float pIntensity = uPointLightParams[i].x;
                            float pRange = uPointLightParams[i].y;
                            
                            if (distToLight < pRange) {
                                vec3 dirToLight = toLight / distToLight;
                                float attenuation = clamp(1.0 - (distToLight / pRange), 0.0, 1.0);
                                attenuation *= attenuation;
                                
                                // Для земли используем переменную 'normal', а не 'norm'
                                float diffuse = max(dot(normal, dirToLight), 0.0);
                                addedLight += uPointLightColor[i] * pIntensity * attenuation * (0.4 + diffuse * 0.6);
                            }
                        }
                    }

                    finalColor += addedLight; // Применяем весь собранный свет к земле


                    if (uShowGrid > 0.5) {
                        vec2 grid = abs(fract(vWorldPos.xz * 0.05) - 0.5);
                        float line = 1.0 - step(0.02, min(grid.x, grid.y));
                        finalColor += vec3(0.05, 0.1, 0.15) * line * (1.0 - clamp(vElevation/20.0, 0.0, 1.0));
                    }

                    // ==========================================
                    // --- СТЕЛЯЩИЙСЯ ТУМАН (CREEPING FOG) ---
                    // ==========================================
                    if (uCFogEnabled > 0.5) {
                        float fogTop = uCFogHeight + uCFogThick;
                        float fogBottom = uCFogHeight;
                        
                        vec4 vFog = calcVolumetricFog(
                            cameraPosition, 
                            vWorldPos, 
                            fogTop, 
                            fogBottom, 
                            uCFogDens, 
                            uCFogShape, 
                            uTime, 
                            uCFogColor
                        );
                        
                        // Слегка растворяем вблизи камеры, чтобы не перекрывало экран
                        float distFade = smoothstep(0.0, 150.0, length(vWorldPos.xz - cameraPosition.xz));
                        finalColor = mix(finalColor, vFog.rgb, vFog.a * distFade);
                    }
                    // ==========================================

                    // --- ПРИМЕНЕНИЕ ТЕНЕЙ ОТ ОБЛАКОВ ---
                    if (uShadowsEnabled > 0.5 && uIsReflectionPass < 0.5) {
                        float shadowDens = getShadowDensity(vWorldPos.xz, uTime);
                        finalColor = mix(finalColor, uShadowColor, shadowDens * uShadowOpacity);
                    }


                    finalColor = mix(finalColor, uFogColor, fogFactor); // Глобальный туман

                    finalColor *= uGlobalLight;
                    gl_FragColor = vec4(finalColor, 1.0);
                }
            `,
            transparent: false, 
            wireframe: false, 
            depthWrite: true,
            clipping: true // <--- ДОБАВЛЯЕМ ЭТУ СТРОКУ
        });

        this.mesh = new THREE.Mesh(geo, this.material);
        this.mesh.visible = false;
        this.mesh.frustumCulled = false;


        this.mesh.matrixAutoUpdate = false; 
        this.mesh.updateMatrix();

        scene.add(this.mesh);
    }
    update(camPos, camDir, time, lightDir) { // Добавили lightDir
        if (!this.mesh.visible) return;
        this.material.uniforms.uCamPos.value.copy(camPos);
        this.material.uniforms.uCamDir.value.copy(camDir); 
        this.material.uniforms.uLightDir.value.copy(lightDir); // Передаем луч
        this.material.uniforms.uTime.value = time;
    }
}
const terrainSystem = new TerrainSystem(scene);



// --- ГЕНЕРАТОР ОБЪЕМНОЙ ГЕОМЕТРИИ (Cross-Quad) ---
function createCrossQuadGeometry(width, height, wSegments, hSegments) {
    const geo1 = new THREE.PlaneGeometry(width, height, wSegments, hSegments);
    const geo2 = new THREE.PlaneGeometry(width, height, wSegments, hSegments);
    geo2.rotateY(Math.PI / 2); // Поворачиваем вторую плоскость на 90 градусов
    
    // Сливаем массивы позиций и UV вручную
    const pos1 = geo1.attributes.position.array;
    const pos2 = geo2.attributes.position.array;
    const uv1 = geo1.attributes.uv.array;
    const uv2 = geo2.attributes.uv.array;
    
    const pos = new Float32Array(pos1.length + pos2.length);
    pos.set(pos1, 0); pos.set(pos2, pos1.length);
    
    const uv = new Float32Array(uv1.length + uv2.length);
    uv.set(uv1, 0); uv.set(uv2, uv1.length);
    
    const idx1 = geo1.index.array;
    const idx2 = geo2.index.array;
    const idx = new Uint16Array(idx1.length + idx2.length);
    idx.set(idx1, 0);
    const offset = pos1.length / 3;
    for(let i = 0; i < idx2.length; i++) {
        idx[idx1.length + i] = idx2[i] + offset;
    }
    
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    geo.setIndex(new THREE.BufferAttribute(idx, 1));
    return geo;
}

class GrassSystem {
    constructor(scene) {
        this.scene = scene;
        this.meshNear = null;
        this.meshFar = null;
        this.build(); 
    }

    // Вспомогательная функция для генерации материалов
    createMaterial(isFar) {
        return new THREE.ShaderMaterial({
            uniforms: {
                uTime: { value: 0 },
                uCamPos: { value: new THREE.Vector3() },
                uBaseColor: { value: CONFIG.grass.baseColor },
                uTipColor: { value: CONFIG.grass.tipColor },
                uSmoothness: { value: CONFIG.grass.smoothness },
                uAmplitude: { value: CONFIG.terrain.amplitude },
                uFrequency: { value: CONFIG.terrain.frequency },
                uOffset: { value: CONFIG.terrain.offset },
                uSharpness: { value: CONFIG.terrain.sharpness },
                uMinHeight: { value: CONFIG.grass.minHeight },
                uMaxHeight: { value: CONFIG.grass.maxHeight },
                uGrassHeight: { value: CONFIG.grass.height }, // Глобальная высота
                uBend: { value: CONFIG.grass.bend },
                uBendAngle: { value: CONFIG.grass.bendAngle },
                uBendChaos: { value: CONFIG.grass.bendChaos },

                uCameraInteract: { value: CONFIG.grass.cameraInteract ? 1.0 : 0.0 }, // <--- НОВОЕ
                uCameraRadius: { value: CONFIG.grass.cameraRadius }, // <--- НОВОЕ

                uLightRadius: { value: CONFIG.flashlight.radius },
                uLightDir: { value: new THREE.Vector3() },

                uLightFocus: { value: CONFIG.flashlight.focus },
                uLightOffset: { value: CONFIG.flashlight.offset },

                uLightEnable: { value: CONFIG.flashlight.affectGrass ? 1.0 : 0.0 },
                uLightColor: { value: CONFIG.flashlight.color },
                uLightIntensity: { value: CONFIG.flashlight.intensity },
                uLightRange: { value: CONFIG.flashlight.range },
                uCamDir: { value: new THREE.Vector3() }, // Для прожектора
                uShapeWindDamp: { value: isFar ? CONFIG.grass.farShapeMods.windDamp : CONFIG.grass.shapeMods.windDamp },

                uGlobalLight: { value: CONFIG.lighting.globalIntensity },

                uPointLightPos: { value: grassLightSet.positions },
                uPointLightColor: { value: grassLightSet.colors },
                uPointLightParams: { value: grassLightSet.params },
                uPointLightCount: { value: 0 },

                uMouseRayOrigin: { value: new THREE.Vector3() },
                uMouseRayDir: { value: new THREE.Vector3() },
                uMouseRadius: { value: CONFIG.grass.mouseRadius },
                uMouseStrength: { value: CONFIG.grass.mouseStrength },
                uMouseEnabled: { value: CONFIG.grass.mouseInteract ? 1.0 : 0.0 },
                
                uShape1: { value: CONFIG.grass.shape1 },
                uShape2: { value: CONFIG.grass.shape2 },
                uShape3: { value: CONFIG.grass.shape3 },
                uShape4: { value: CONFIG.grass.shape4 },

                uFarMixMode: { value: CONFIG.grass.farMixMode },
                uFarShape1: { value: CONFIG.grass.farShape1 },
                uFarShape2: { value: CONFIG.grass.farShape2 },
                uFarShape3: { value: CONFIG.grass.farShape3 },

                uShapeChances: { value: new THREE.Vector4(0, CONFIG.grass.altChance2, CONFIG.grass.altChance3, CONFIG.grass.altChance4) },
                uShapeStructs: { value: new THREE.Vector4(0, CONFIG.grass.struct2, CONFIG.grass.struct3, CONFIG.grass.struct4) },
                uShapeThins: { value: new THREE.Vector4(0, CONFIG.grass.thin2, CONFIG.grass.thin3, CONFIG.grass.thin4) },
                
                uFarShapeChances: { value: new THREE.Vector4(0, CONFIG.grass.farAltChance2, CONFIG.grass.farAltChance3, 0) },
                uFarShapeStructs: { value: new THREE.Vector4(0, CONFIG.grass.farStruct2, CONFIG.grass.farStruct3, 0) },
                uFarShapeThins: { value: new THREE.Vector4(0, CONFIG.grass.farThin2, CONFIG.grass.farThin3, 0) },
                
                // --- НОВЫЕ УНИФОРМЫ ДЛЯ УНИКАЛЬНЫХ НАСТРОЕК ФОРМ ---
                uShapeSizes: { value: isFar ? CONFIG.grass.farShapeMods.size : CONFIG.grass.shapeMods.size },
                uShapeWidths: { value: isFar ? CONFIG.grass.farShapeMods.width : CONFIG.grass.shapeMods.width },
                uShapeSizeVars: { value: CONFIG.grass.shapeMods.sizeVar },
                uShapeColorVars: { value: CONFIG.grass.shapeMods.colorVar },
                uShapeSizeVars: { value: CONFIG.grass.shapeMods.sizeVar },
                uShapeColorVars: { value: CONFIG.grass.shapeMods.colorVar },

                uShapeVar: { value: CONFIG.grass.shapeVar },

                uMixMode: { value: CONFIG.grass.mixMode },

                uBaseColor2: { value: CONFIG.grass.baseColor2 },
                uTipColor2: { value: CONFIG.grass.tipColor2 },
                uBaseColor3: { value: CONFIG.grass.baseColor3 },
                uTipColor3: { value: CONFIG.grass.tipColor3 },
                uBaseColor4: { value: CONFIG.grass.baseColor4 },
                uTipColor4: { value: CONFIG.grass.tipColor4 },
                uClusterFreq: { value: CONFIG.grass.clusterFreq },
                uClusterThreshold: { value: CONFIG.grass.clusterThreshold },
                uFogColor: { value: CONFIG.terrain.fogColor },
                uFogDensity: { value: CONFIG.terrain.fogDensity },
                uFogMult: { value: CONFIG.grass.fogDensityMult },
                uGrassWindSpeed: { value: CONFIG.grass.windSpeed },
                uGrassSwayStrength: { value: CONFIG.grass.swayStrength },
                uGrassTurbulence: { value: CONFIG.grass.turbulence },
                uGrassGustStrength: { value: CONFIG.grass.gustStrength },
                uGrassGustSize: { value: CONFIG.grass.gustSize },
                uGrassGustFreq: { value: CONFIG.grass.gustFreq }, 
                uGrassGustSmoothness: { value: CONFIG.grass.gustSmoothness },
                uGrassGustArc: { value: CONFIG.grass.gustArc },
                uGrassGustSpeed: { value: CONFIG.grass.gustSpeed }, // <--- ДОБАВИТЬ ЭТУ СТРОКУ
                uGrassWindChaos: { value: CONFIG.grass.windChaos },
                uGrassTurbAmp: { value: CONFIG.grass.turbAmp },
                uGrassTurbSpeed: { value: CONFIG.grass.turbSpeed },

                ...creepingFogUniforms,
                ...sharedCloudUniforms,

                uDrawDistance: { value: isFar ? CONFIG.grass.farDistance : CONFIG.grass.drawDistance },
                uInnerRadius: { value: isFar ? CONFIG.grass.drawDistance : 0.0 }, 
                uSizeMult: { value: isFar ? CONFIG.grass.farSizeMult : 1.0 },     
                uIsFar: { value: isFar ? 1.0 : 0.0 }
            },
            vertexShader: `
                uniform float uTime;
                uniform vec3 uCamPos;
                uniform float uAmplitude, uFrequency, uOffset, uSharpness;
                uniform float uMinHeight, uMaxHeight, uGrassHeight;
                uniform float uBend, uBendAngle, uBendChaos;
                uniform float uShape1, uShape2, uShape3, uShape4;
                uniform float uFarMixMode, uFarShape1, uFarShape2, uFarShape3;
                uniform vec4 uShapeChances, uShapeStructs, uShapeThins;
                uniform vec4 uFarShapeChances, uFarShapeStructs, uFarShapeThins;
                uniform vec4 uShapeSizes, uShapeWidths, uShapeSizeVars;
                uniform float uMixMode, uClusterFreq, uClusterThreshold, uDrawDistance;
                uniform float uGrassWindSpeed, uGrassSwayStrength, uGrassTurbulence;
                uniform float uGrassGustStrength, uGrassGustSize, uGrassGustFreq, uGrassGustSmoothness, uGrassGustArc, uGrassGustSpeed;
                uniform float uGrassWindChaos, uGrassTurbAmp, uGrassTurbSpeed;
                uniform float uInnerRadius, uSizeMult, uIsFar;
                uniform vec3 uMouseRayOrigin, uMouseRayDir;
                uniform float uMouseRadius, uMouseStrength, uMouseEnabled, uShapeVar;

                uniform vec4 uShapeWindDamp;

                // ДЛЯ ОПТИМИЗАЦИИ ТУМАНА И ТЕНЕЙ ВЕРШИН
                uniform float uCFogEnabled;
                uniform vec3 uCFogColor;
                uniform float uCFogHeight;
                uniform float uCFogThick;
                uniform float uCFogDens;
                uniform float uCFogShape;
                uniform float uCameraInteract;
                uniform float uCameraRadius;
                uniform vec3 uCamDir;

                varying float vHash, vV, vU, vShape, vColorIdx;
                varying vec3 vWorldPos;
                
                // ПЕРЕДАЕМ ГОТОВЫЕ ДАННЫЕ В FRAGMENT
                varying vec4 vFogData;
                varying float vShadowData;

                ${terrainNoiseChunk}
                ${fastTextureNoiseChunk}
                ${volumetricFogChunk}
                ${cloudNoiseChunk}

                float hash12(vec2 p) {
                    vec3 p3  = fract(vec3(p.xyx) * vec3(0.1031, 0.11369, 0.13787));
                    p3 += dot(p3, p3.yzx + 33.33);
                    return fract((p3.x + p3.y) * p3.z);
                }

                void main() {
                    vU = uv.x; vV = uv.y;
                    vec3 pos = position;

                    float halfDist = uDrawDistance * 0.5;
                    vec4 localInstancePos = instanceMatrix * vec4(0.0, 0.0, 0.0, 1.0);
                    vec2 worldXZ = uCamPos.xz + mod(localInstancePos.xz - uCamPos.xz + halfDist, uDrawDistance) - halfDist;
                    vec2 safeXZ = mod(worldXZ, 20000.0);
                    vec2 seedXZ = floor(safeXZ * 2.0);

                    vHash = hash12(seedXZ);
                    float sizeRand = hash12(seedXZ + vec2(17.3, 31.7));
                    float shapeRand = hash12(seedXZ + vec2(43.1, 79.9));

                    float currentShape = uShape1;
                    float colorIndex = 0.0; 
                    bool useCustomFar = (uIsFar > 0.5 && uFarMixMode > 0.0);
                    float activeMixMode = useCustomFar ? uFarMixMode : uMixMode;

                    if (useCustomFar) currentShape = uFarShape1;

                    if (activeMixMode > 0.5) {
                        // --- Вычисления для 2 формы (считаются всегда, если mixMode > 0) ---
                        vec2 off2 = vec2(100.0, 200.0);
                        float currentShape2 = useCustomFar ? uFarShape2 : uShape2;
                        float baseChance2 = useCustomFar ? uFarShapeChances.y : uShapeChances.y;
                        float activeChance2 = pow(baseChance2, 3.0) * ((currentShape2 > 7.5) ? 0.015 : 1.0);
                        float activeStruct2 = useCustomFar ? uFarShapeStructs.y : uShapeStructs.y;
                        float activeThin2   = useCustomFar ? uFarShapeThins.y : uShapeThins.y;
                        float islandNoise2 = noise(safeXZ * (mix(0.1, 0.002, activeStruct2) * mix(1.0, 0.15, activeThin2)) + off2) * 0.8 + noise(safeXZ * (mix(0.1, 0.002, activeStruct2) * mix(1.0, 0.15, activeThin2)) * 2.5 - off2) * 0.2;
                        float threshold2 = mix(0.2, 0.85, activeThin2);
                        bool cond2 = (hash12(seedXZ + vec2(112.4, 235.1)) < activeChance2) && (mix(1.0, smoothstep(threshold2 - 0.05, threshold2 + 0.05, islandNoise2), activeStruct2) > 0.5);

                        bool cond3 = false;
                        bool cond4 = false;

                        // --- Вычисления для 3 формы (считаются ТОЛЬКО если mixMode >= 2) ---
                        if (activeMixMode >= 1.5) {
                            vec2 off3 = vec2(-150.0, 50.0);
                            float currentShape3 = useCustomFar ? uFarShape3 : uShape3;
                            float baseChance3 = useCustomFar ? uFarShapeChances.z : uShapeChances.z;
                            float activeChance3 = pow(baseChance3, 3.0) * ((currentShape3 > 7.5) ? 0.015 : 1.0);
                            float activeStruct3 = useCustomFar ? uFarShapeStructs.z : uShapeStructs.z;
                            float activeThin3   = useCustomFar ? uFarShapeThins.z : uShapeThins.z;
                            float islandNoise3 = noise(safeXZ * (mix(0.1, 0.002, activeStruct3) * mix(1.0, 0.15, activeThin3)) + off3) * 0.8 + noise(safeXZ * (mix(0.1, 0.002, activeStruct3) * mix(1.0, 0.15, activeThin3)) * 2.5 - off3) * 0.2;
                            float threshold3 = mix(0.2, 0.85, activeThin3);
                            cond3 = (hash12(seedXZ + vec2(341.7, 981.3)) < activeChance3) && (mix(1.0, smoothstep(threshold3 - 0.05, threshold3 + 0.05, islandNoise3), activeStruct3) > 0.5);
                        }

                        // --- Вычисления для 4 формы (считаются ТОЛЬКО если mixMode >= 3 и это не дальний план) ---
                        if (!useCustomFar && activeMixMode >= 2.5) {
                            vec2 off4 = vec2(300.0, -100.0);
                            float activeChance4 = pow(uShapeChances.w, 3.0) * ((uShape4 > 7.5) ? 0.015 : 1.0);
                            float islandNoise4 = noise(safeXZ * (mix(0.1, 0.002, uShapeStructs.w) * mix(1.0, 0.15, uShapeThins.w)) + off4) * 0.8 + noise(safeXZ * (mix(0.1, 0.002, uShapeStructs.w) * mix(1.0, 0.15, uShapeThins.w)) * 2.5 - off4) * 0.2;
                            float threshold4 = mix(0.2, 0.85, uShapeThins.w);
                            cond4 = (hash12(seedXZ + vec2(512.9, 73.4)) < activeChance4) && (mix(1.0, smoothstep(threshold4 - 0.05, threshold4 + 0.05, islandNoise4), uShapeStructs.w) > 0.5);
                        }

                        // --- Итоговое назначение ---
                        if (useCustomFar) {
                            if (activeMixMode >= 1.0 && cond2) { currentShape = uFarShape2; colorIndex = 1.0; } 
                            else if (activeMixMode >= 2.0 && cond3) { currentShape = uFarShape3; colorIndex = 2.0; }
                        } else {
                            if (activeMixMode >= 1.0 && cond2) { currentShape = uShape2; colorIndex = 1.0; } 
                            else if (activeMixMode >= 2.0 && cond3) { currentShape = uShape3; colorIndex = 2.0; } 
                            else if (activeMixMode >= 3.0 && cond4) { currentShape = uShape4; colorIndex = 3.0; }
                        }
                    }
                    vShape = currentShape; vColorIdx = colorIndex;

                    // Вычисляем коэффициент ослабления ветра для данной формы (x, y, z или w)
                    float myWindDamp = (colorIndex < 0.5) ? uShapeWindDamp.x : ((colorIndex < 1.5) ? uShapeWindDamp.y : ((colorIndex < 2.5) ? uShapeWindDamp.z : uShapeWindDamp.w));
                    float windMult = clamp(1.0 - myWindDamp, 0.0, 1.0);

                    float mySize = (colorIndex < 0.5) ? uShapeSizes.x : ((colorIndex < 1.5) ? uShapeSizes.y : ((colorIndex < 2.5) ? uShapeSizes.z : uShapeSizes.w));
                    float myWidth = (colorIndex < 0.5) ? uShapeWidths.x : ((colorIndex < 1.5) ? uShapeWidths.y : ((colorIndex < 2.5) ? uShapeWidths.z : uShapeWidths.w));
                    float mySizeVar = (colorIndex < 0.5) ? uShapeSizeVars.x : ((colorIndex < 1.5) ? uShapeSizeVars.y : ((colorIndex < 2.5) ? uShapeSizeVars.z : uShapeSizeVars.w));

                    float widthMod = 1.0; float heightMod = 1.0;
                    if (currentShape < 0.5) { widthMod = pow(1.0 - vV, 2.0); } else if (currentShape < 1.5) { widthMod = (1.0 - vV); } else if (currentShape < 2.5) { widthMod = 1.0; } else if (currentShape < 3.5) { heightMod = 2.5; widthMod = (vV <= 0.75) ? 0.3 : mix(0.3, 1.5, (vV - 0.75) / 0.25); } else if (currentShape < 4.5) { widthMod = (vV <= 0.75) ? 0.15 : 2.0; } else if (currentShape < 5.5) { widthMod = (vV <= 0.8) ? 0.6 : 1.5; } else if (currentShape < 6.5) { heightMod = 2.0; widthMod = 3.5; } else if (currentShape < 7.5) { heightMod = 2.5; widthMod = 4.5; } else if (currentShape < 8.5) { heightMod = 10.0; widthMod = 7.0; } else { heightMod = 13.0; widthMod = 5.0; }

                    pos.x *= (widthMod * myWidth); pos.y *= (heightMod * mySize);
                    pos = mat3(instanceMatrix) * pos * uSizeMult;
                    pos.y *= mix(1.0 - mySizeVar * 0.4, 1.0 + mySizeVar * 1.5, sizeRand); 
                    pos.x *= mix(1.0 - uShapeVar * 0.6, 1.0 + uShapeVar * 1.5, shapeRand);

                    float windResistance = (currentShape > 7.5 && currentShape < 9.5) ? 0.15 : 1.0;
                    float finalAngle = uBendAngle + (vHash - 0.5) * uBendChaos * 6.28318;
                    vec2 staticBendDir = vec2(cos(finalAngle), sin(finalAngle));
                    vec2 windDir = vec2(cos(uBendAngle), sin(uBendAngle));
                    
                    float sway = (sin(dot(safeXZ, windDir) * 0.02 - (uTime * uGrassWindSpeed - vV * 1.5)) * 0.5 + 0.5) * uGrassSwayStrength * windResistance * windMult;
                    float turb = ((noise(safeXZ / max(0.1, uGrassTurbAmp * 5.0) + uTime * uGrassTurbSpeed * 0.5)) * 2.0 - 1.0) * uGrassTurbulence * windResistance * windMult;

                    float finalGust = 0.0;
                    if (uGrassGustFreq > 0.001) {
                        if (uIsFar < 0.5) {
                            float freqScale = mix(0.0003, 0.015, pow(uGrassGustFreq, 2.0));
                            float threshold = mix(0.95, -0.2, clamp(uGrassGustSize / 300.0, 0.0, 1.0));
                            float softness = mix(0.01, 0.8, uGrassGustSmoothness);
                            float gustTime = uTime * uGrassGustSpeed * (0.5 + uGrassWindSpeed * 0.2);
                            float combinedGust = mix(smoothstep(threshold, threshold + softness, noise(safeXZ * freqScale * 0.8 - windDir * gustTime)), smoothstep(threshold, threshold + softness, sin((dot(safeXZ, windDir) + noise(safeXZ * 0.005) * 80.0) * freqScale - gustTime) * 0.5 + 0.5), uGrassGustArc);
                            // Применяем ослабление ветра к порывам
                            finalGust = combinedGust * uGrassGustStrength * mix(1.0, smoothstep(mix(0.75, 0.2, uGrassGustFreq), mix(0.75, 0.2, uGrassGustFreq) + 0.2, noise(safeXZ * 0.001 + uTime * 0.05)), uGrassWindChaos) * windResistance * windMult; 
                        } else {
                            // Применяем ослабление ветра к порывам на дальнем плане
                            finalGust = smoothstep(mix(0.8, 0.1, clamp(uGrassGustSize / 300.0, 0.0, 1.0)), 1.0, sin(uTime * uGrassGustSpeed * 0.5 + dot(safeXZ, windDir) * 0.01) * 0.5 + 0.5) * uGrassGustStrength * 0.5 * windResistance * windMult;
                        }
                    }

                    float actualBend = uBend * mix(1.0, windResistance, 0.5); 
                    float angle = clamp((actualBend + sway + finalGust + turb * (1.0 + finalGust * 0.5)) * (vV * vV * (3.0 - 2.0 * vV)) * (heightMod > 1.5 ? 1.2 : 1.0), -1.5, 1.5);
                    vec2 finalDir = mix(staticBendDir, windDir, smoothstep(0.0, 0.5, finalGust));

                    float groundY = getTerrainHeight(worldXZ, uFrequency, uAmplitude, uOffset, uSharpness);

                    if (uMouseEnabled > 0.5 && uMouseRayDir.y < -0.01) {
                        float tVal = (groundY - uMouseRayOrigin.y) / uMouseRayDir.y;
                        if (tVal > 0.0 && tVal < uDrawDistance) {
                            vec2 toBladeXZ = worldXZ - (uMouseRayOrigin + uMouseRayDir * tVal).xz + vec2(0.001);
                            float distToCenter = length(toBladeXZ);
                            
                            if (distToCenter < uMouseRadius) {
                                float overrideWeight = clamp(smoothstep(0.0, 1.0, 1.0 - (distToCenter / uMouseRadius)) * uMouseStrength * 1.5, 0.0, 1.0);
                                
                                // --- ЭКСПЕРИМЕНТ: ВЕЕР ОТ КУРСОРА (220 градусов) ---
                                vec2 camForward = normalize(uCamDir.xz);
                                vec2 pushDir = normalize(toBladeXZ);
                                
                                // Скалярное произведение покажет угол между взглядом камеры и направлением наклона
                                float dotP = dot(camForward, pushDir);
                                
                                // cos(110 градусов) ≈ -0.342. 
                                // Если скалярное произведение меньше -0.342, трава пытается наклониться к камере 
                                // (попадает в слепую зону 140 градусов)
                                if (dotP < -0.342) {
                                    // Силой выгибаем вектор наклона вперед, по ходу взгляда камеры
                                    pushDir = normalize(pushDir + camForward * 1.5);
                                }
                                // ----------------------------------------------------

                                angle = mix(angle, 1.5 * (vV * vV * (3.0 - 2.0 * vV)), overrideWeight);
                                finalDir = normalize(mix(finalDir, pushDir, overrideWeight));
                            }
                        }
                    }
                    if (uCameraInteract > 0.5) {
                        vec2 toCamXZ = worldXZ - uCamPos.xz;
                        float distToCam = length(toCamXZ);
                        if (distToCam < uCameraRadius) {
                            float camWeight = clamp(smoothstep(0.0, 1.0, 1.0 - (distToCam / uCameraRadius)) * uMouseStrength * 2.0, 0.0, 1.0);
                            
                            // --- ЭКСПЕРИМЕНТ: ВЕЕР НА 220 ГРАДУСОВ ---
                            vec2 camForward = normalize(uCamDir.xz);
                            vec2 pushDir = normalize(toCamXZ);
                            
                            // Находим угол между взглядом и травинкой (-1 = сзади, 1 = спереди)
                            float dotP = dot(camForward, pushDir);
                            
                            // cos(110 градусов) ≈ -0.342. 
                            // Если dotP меньше -0.342, травинка находится в слепой зоне 140 градусов позади
                            if (dotP < -0.342) {
                                // Искусственно загибаем вектор отталкивания вперед
                                pushDir = normalize(pushDir + camForward * 1.5);
                            }
                            // ------------------------------------------

                            angle = mix(angle, 1.5 * (vV * vV * (3.0 - 2.0 * vV)), camWeight);
                            finalDir = normalize(mix(finalDir, pushDir, camWeight));
                        }
                    }
                    float curY = pos.y; 
                    pos.x += finalDir.x * sin(angle) * curY;
                    pos.z += finalDir.y * sin(angle) * curY;
                    pos.y = curY * cos(angle);

                    pos *= (smoothstep(uMinHeight - 2.0, uMinHeight + 2.0, groundY) * (1.0 - smoothstep(uMaxHeight - 5.0, uMaxHeight, groundY)) * smoothstep(uClusterThreshold - 0.1, uClusterThreshold + 0.1, noise(safeXZ * uClusterFreq)) * uGrassHeight);
                    
                    float distToCamXZ = length(worldXZ - uCamPos.xz);
                    pos *= (1.0 - smoothstep(halfDist * 0.75, halfDist, distToCamXZ)) * ((uIsFar > 0.5) ? smoothstep(uInnerRadius * 0.8, uInnerRadius, distToCamXZ) : 1.0);

                    vec3 finalWorldPos = vec3(worldXZ.x, groundY, worldXZ.y) + pos;
                    vWorldPos = finalWorldPos; 

                    // === ОПТИМИЗАЦИЯ: ВЫЧИСЛЕНИЯ ТУМАНА И ТЕНЕЙ ДЛЯ ВСЕЙ ТРАВИНКИ ОДИН РАЗ ===
                    vFogData = vec4(0.0);
                    if (uCFogEnabled > 0.5) {
                        vFogData = calcVolumetricFog(uCamPos, finalWorldPos, uCFogHeight + uCFogThick, uCFogHeight, uCFogDens, uCFogShape, uTime, uCFogColor);
                    }
                    vShadowData = (uShadowsEnabled > 0.5 && uIsReflectionPass < 0.5) ? getShadowDensity(finalWorldPos.xz, uTime) : 0.0;
                    // =========================================================================

                    gl_Position = projectionMatrix * viewMatrix * vec4(finalWorldPos, 1.0);
                }
            `,
            fragmentShader: `
                uniform vec3 uBaseColor, uTipColor, uCamPos, uFogColor;
                uniform vec3 uBaseColor2, uTipColor2, uBaseColor3, uTipColor3, uBaseColor4, uTipColor4;
                uniform vec4 uShapeColorVars; 
                uniform float uSmoothness, uFogDensity, uFogMult;

                // ИСПОЛЬЗУЕМ ДАННЫЕ ИЗ ВЕРШИН
                varying vec4 vFogData;
                varying float vShadowData;
                uniform float uCFogEnabled;
                uniform float uShadowsEnabled;
                uniform vec3 uShadowColor;
                uniform float uShadowOpacity;

                varying float vHash, vU, vV, vShape, vColorIdx;
                varying vec3 vWorldPos;

                uniform float uGlobalLight;

                #define MAX_POINT_LIGHTS 20
                uniform vec3 uPointLightPos[MAX_POINT_LIGHTS];
                uniform vec3 uPointLightColor[MAX_POINT_LIGHTS];
                uniform vec2 uPointLightParams[MAX_POINT_LIGHTS]; // x: intensity, y: range
                uniform float uPointLightCount;

                uniform float uLightEnable;
                uniform vec3 uLightColor;
                uniform float uLightIntensity;
                uniform float uLightRange;
                uniform vec3 uLightDir;
                uniform float uLightRadius;
                uniform float uLightFocus;
                uniform float uLightOffset;
                uniform vec3 uCamDir;

                void main() {
                    float u = vU * 2.0 - 1.0; 
                    
                    // РАННЕЕ ОТСЕЧЕНИЕ (САМАЯ ВАЖНАЯ ОПТИМИЗАЦИЯ FRAGMENT SHADER)
                    if (vShape < 1.5) {
                        if (abs(u) > ((vShape < 0.5) ? pow(1.0 - vV, 2.0) : (1.0 - vV))) discard; 
                    }

                    float mixFactor = pow(vV, uSmoothness);
                    float brightness = 0.3 + 0.7 * vV;
                    
                    if (vShape > 2.5) {
                        if (vShape < 3.5) {
                            float polyWidth = (vV <= 0.75) ? 0.3 : mix(0.3, 1.5, (vV - 0.75) / 0.25);
                            float distFromCenter = abs(u) * polyWidth;
                            if (vV < 0.75) {
                                if (distFromCenter > 0.04) discard; 
                                mixFactor = 0.0; brightness = 0.4 + 0.3 * vV;
                            } else {
                                float localV = (vV - 0.75) / 0.25; 
                                float headWidth = mix(0.04, sin(localV * 3.14159) * 0.55 + sin(vV * 120.0 + vHash * 50.0) * 0.12, smoothstep(0.0, 0.1, localV));
                                if (distFromCenter > headWidth) discard;
                                mixFactor = 1.0; 
                                brightness = 0.4 + (pow(1.0 - (distFromCenter / headWidth), 0.5) * 0.6) + sin(vV * 80.0) * 0.1; 
                            }
                        } 
                        else if (vShape < 4.5) {
                            if (vV < 0.75) {
                                if (abs(u) > 0.02) discard; mixFactor = 0.0;
                            } else {
                                float dist = length(vec2(u, (vV - 0.75) / 0.25) - vec2(0.0, 0.5));
                                if (dist > 0.45 + sin(atan(((vV - 0.75) / 0.25) - 0.5, u) * 40.0 + vHash * 100.0) * 0.05) discard;
                                mixFactor = 1.0; 
                                brightness = 0.5 + smoothstep(0.45, 0.2, dist) * 0.5 + fract(sin(dot(vec2(u, (vV - 0.75) / 0.25), vec2(12.9, 78.2))) * 43758.5) * 0.3;
                            }
                        } 
                        else if (vShape < 5.5) {
                            if (vV < 0.8) {
                                if (abs(u) > 0.03 + max(0.0, sin(vV * 15.0 + vHash * 10.0) * 0.3 * (1.0 - vV))) discard; mixFactor = 0.0;
                            } else {
                                float dist = length(vec2(u, (vV - 0.8) / 0.2) - vec2(0.0, 0.5));
                                float petals = 0.35 + 0.15 * sin(atan(((vV - 0.8) / 0.2) - 0.5, u) * 5.0 + vHash * 5.0);
                                if (dist > petals) discard;
                                mixFactor = 1.0;
                                brightness = 0.6 + 0.4 * (1.0 - dist / petals) - smoothstep(0.15, 0.0, dist) * 0.3;
                            }
                        }
                        else if (vShape < 6.5) {
                            float dist = length(vec2(u, (vV - 0.4) * 1.3)); 
                            if (dist > 0.42 + sin(atan(vV - 0.4, u) * 12.0 + vHash * 10.0) * 0.08 + sin(atan(vV - 0.4, u) * 27.0) * 0.04) discard;
                            mixFactor = smoothstep(0.0, 0.8, vV);
                            brightness = 0.35 + 0.5 * (1.0 - dist) - smoothstep(0.4, 0.0, dist) * 0.1;
                        }
                        else if (vShape < 7.5) {
                            float minDist = min(min(length(vec2(u, (vV - 0.35) * 1.5)), length(vec2(u - 0.25, (vV - 0.25) * 1.3))), length(vec2(u + 0.25, (vV - 0.25) * 1.3))) - (sin(atan(vV - 0.3, u) * 25.0 + vHash * 30.0) * 0.04 + sin(atan(vV - 0.3, u) * 45.0) * 0.02);
                            if (minDist > 0.35) discard;
                            mixFactor = smoothstep(0.0, 0.8, vV);
                            brightness = 0.25 + (smoothstep(0.35, 0.0, minDist) * 0.5 * smoothstep(0.0, 0.6, vV));
                        }
                        else if (vShape < 8.5) {
                            if (vV < 0.3) {
                                float trunkWidth = 0.04 - (vV * 0.02) + 0.15 * exp(-vV * 18.0);
                                if (abs(u) > trunkWidth) discard;
                                mixFactor = 0.0; 
                                brightness = 0.15 + pow(1.0 - (abs(u) / trunkWidth), 0.5) * 0.3 + sin(u * 50.0 + vV * 30.0 + vHash * 10.0) * 0.1;
                            } else {
                                float localV = (vV - 0.3) / 0.7;
                                float minDist = min(min(min(length(vec2(u, (localV - 0.4) * 1.2)), length(vec2(u - 0.3, (localV - 0.3) * 1.3))), min(length(vec2(u + 0.3, (localV - 0.3) * 1.3)), length(vec2(u - 0.2, (localV - 0.6) * 1.4)))), min(length(vec2(u + 0.2, (localV - 0.6) * 1.4)), length(vec2(u, (localV - 0.8) * 1.5)))) - (sin(atan(localV - 0.4, u) * 18.0 + vHash * 50.0) * 0.06 + sin(atan(localV - 0.4, u) * 40.0) * 0.03);
                                if (minDist > 0.32) discard;
                                mixFactor = 1.0; 
                                brightness = 0.2 + (smoothstep(0.32, 0.05, minDist) * 0.5 * smoothstep(0.0, 0.7, localV));
                            }
                        }
                        else {
                            if (vV < 0.15) {
                                float trunkWidth = 0.03 - (vV * 0.01) + 0.15 * exp(-vV * 25.0);
                                if (abs(u) > trunkWidth) discard;
                                mixFactor = 0.0; 
                                brightness = 0.12 + pow(1.0 - (abs(u) / trunkWidth), 0.5) * 0.25 + sin(u * 50.0 + vV * 30.0 + vHash * 10.0) * 0.1;
                            } else {
                                float localV = (vV - 0.15) / 0.85; 
                                float layerV = fract(localV * 6.0); 
                                float finalShape = (1.0 - pow(layerV, 0.8)) * (1.0 - (floor(localV * 6.0) / 6.0)) * 0.45 + sin(layerV * 3.1415) * 0.05 + sin(vV * 40.0 + vHash * 20.0) * 0.03 + sin(u * 30.0) * 0.02;
                                if (abs(u) > finalShape) discard;
                                mixFactor = 1.0; 
                                brightness = 0.18 + (smoothstep(0.0, 0.4, layerV) * 0.35) + (smoothstep(finalShape, finalShape * 0.4, abs(u)) * 0.25) + (smoothstep(0.0, 1.0, localV) * 0.2);
                            }
                        }
                    }

                    // --- ТОЛЬКО ДЛЯ ВЫЖИВШИХ ПИКСЕЛЕЙ ---
                    vec3 baseC = (vColorIdx < 0.5) ? uBaseColor : ((vColorIdx < 1.5) ? uBaseColor2 : ((vColorIdx < 2.5) ? uBaseColor3 : uBaseColor4));
                    vec3 tipC = (vColorIdx < 0.5) ? uTipColor : ((vColorIdx < 1.5) ? uTipColor2 : ((vColorIdx < 2.5) ? uTipColor3 : uTipColor4));

                    float myColVar = (vColorIdx < 0.5) ? uShapeColorVars.x : ((vColorIdx < 1.5) ? uShapeColorVars.y : ((vColorIdx < 2.5) ? uShapeColorVars.z : uShapeColorVars.w));
                    if (myColVar > 0.0) {
                        float varStrength = myColVar * myColVar; 
                        float h1 = fract(sin(vHash * 11.11) * 43758.5) - 0.5;
                        float h2 = fract(sin(vHash * 22.22) * 43758.5) - 0.5;

                        if (vShape > 7.5) {
                            vec3 treeHue = vec3(h2 * 0.8, h2 * 0.4 + h1 * 0.2, -abs(h2) * 0.4) * (varStrength * 1.5);
                            baseC = clamp(baseC + treeHue + h1 * varStrength * 0.5, 0.0, 1.0);
                            tipC  = clamp(tipC + treeHue + h1 * varStrength * 0.75, 0.0, 1.0);
                        } else {
                            vec3 hueShift = vec3(h2 * 0.4, h2 * 0.15, -h2 * 0.3) * varStrength;
                            baseC = clamp(baseC + hueShift + h1 * varStrength * 0.4, 0.0, 1.0);
                            tipC  = clamp(tipC + hueShift + (h1 * varStrength * 0.6), 0.0, 1.0);
                        }
                    }

                    vec3 finalColor = mix(baseC, tipC, mixFactor) * brightness; 
                    vec3 addedLight = vec3(0.0);
                    
                    if (uLightEnable > 0.5) {
                        vec3 toPixel = vWorldPos - (uCamPos + uCamDir * uLightOffset);
                        float distToPixel = length(toPixel);
                        if (distToPixel < uLightRange) {
                            vec3 dirToPixel = normalize(toPixel);
                            float spotEffect = dot(uLightDir, dirToPixel);
                            
                            float outerAngle = mix(0.99, 0.5, uLightRadius);
                            float innerAngle = mix(outerAngle, 1.0, uLightFocus);
                            
                            if (spotEffect > outerAngle) {
                                float spotMask = smoothstep(outerAngle, innerAngle, spotEffect);
                                float attenuation = pow(clamp(1.0 - (distToPixel / uLightRange), 0.0, 1.0), 2.0);
                                addedLight += uLightColor * uLightIntensity * attenuation * spotMask;
                            }
                        }
                    }

                    if (uPointLightCount > 0.0) {
                        for(int i = 0; i < MAX_POINT_LIGHTS; i++) {
                            if (float(i) >= uPointLightCount) break;
                            
                            vec3 toLight = uPointLightPos[i] - vWorldPos;
                            float distToLight = length(toLight);
                            float pIntensity = uPointLightParams[i].x;
                            float pRange = uPointLightParams[i].y;
                            
                            if (distToLight < pRange) {
                                float attenuation = clamp(1.0 - (distToLight / pRange), 0.0, 1.0);
                                attenuation *= attenuation;
                                
                                // Для травы диффузии от нормалей нет, просто мягко освещаем
                                addedLight += uPointLightColor[i] * pIntensity * attenuation * 0.5;
                            }
                        }
                    }

                    finalColor += addedLight * (mix(baseC, tipC, mixFactor) * 2.0 + vec3(0.15));                 
                    
                    // --- ИСПОЛЬЗУЕМ ВЫЧИСЛЕННЫЙ ТУМАН ИЗ ВЕРШИН ---
                    if (uCFogEnabled > 0.5) {
                        float distFade = smoothstep(0.0, 150.0, length(vWorldPos.xz - uCamPos.xz));
                        finalColor = mix(finalColor, vFogData.rgb, vFogData.a * distFade);
                    }

                    float dist = length(vWorldPos.xz - uCamPos.xz);
                    
                    if (uShadowsEnabled > 0.5) {
                        finalColor = mix(finalColor, uShadowColor, vShadowData * uShadowOpacity);
                    }

                    finalColor = mix(finalColor, uFogColor, clamp(1.0 - exp(-pow(dist * uFogDensity * uFogMult, 2.0)), 0.0, 1.0));

                    finalColor *= uGlobalLight;
                    gl_FragColor = vec4(finalColor, 1.0);
                }
            `,
                        side: THREE.DoubleSide,
            transparent: false,
            depthWrite: true
        });
    }

    build() {
        if (this.meshNear) {
            this.scene.remove(this.meshNear);
            this.meshNear.geometry.dispose();
            this.materialNear.dispose();
        }
        if (this.meshFar) {
            this.scene.remove(this.meshFar);
            this.meshFar.geometry.dispose();
            this.materialFar.dispose();
        }

        // --- 1. БЛИЖНИЙ СЛОЙ (ВЫСОКАЯ ДЕТАЛИЗАЦИЯ + CROSS-QUAD) ---
        const geoNear = createCrossQuadGeometry(0.5, 1.0, 1, 4);
        geoNear.translate(0, 0.5, 0); // Поднимаем опорную точку вниз
        this.materialNear = this.createMaterial(false);
        
        this.meshNear = new THREE.InstancedMesh(geoNear, this.materialNear, CONFIG.grass.count);
        this.meshNear.frustumCulled = false;
        
        const dummy = new THREE.Object3D();
        for (let i = 0; i < CONFIG.grass.count; i++) {
            dummy.position.set((Math.random() - 0.5) * CONFIG.grass.drawDistance, 0, (Math.random() - 0.5) * CONFIG.grass.drawDistance);
            dummy.rotation.y = Math.random() * Math.PI * 2;
            const scaleVar = 0.8 + Math.random() * 0.4;
            dummy.scale.set(scaleVar, scaleVar, scaleVar);
            dummy.updateMatrix();
            this.meshNear.setMatrixAt(i, dummy.matrix);
        }
        this.meshNear.instanceMatrix.needsUpdate = true;
        this.scene.add(this.meshNear);

        // --- 2. ДАЛЬНИЙ СЛОЙ (LOD - CROSS-QUAD НИЗКОЙ ДЕТАЛИЗАЦИИ) ---
        const geoFar = createCrossQuadGeometry(0.5, 1.0, 1, 1);
        geoFar.translate(0, 0.5, 0);
        this.materialFar = this.createMaterial(true);

        this.meshFar = new THREE.InstancedMesh(geoFar, this.materialFar, CONFIG.grass.farCount);
        this.meshFar.frustumCulled = false;

        for (let i = 0; i < CONFIG.grass.farCount; i++) {
            dummy.position.set((Math.random() - 0.5) * CONFIG.grass.farDistance, 0, (Math.random() - 0.5) * CONFIG.grass.farDistance);
            dummy.rotation.y = Math.random() * Math.PI * 2;
            const scaleVar = 0.8 + Math.random() * 0.4;
            dummy.scale.set(scaleVar, scaleVar, scaleVar);
            dummy.updateMatrix();
            this.meshFar.setMatrixAt(i, dummy.matrix);
        }
        this.meshFar.instanceMatrix.needsUpdate = true;
        this.scene.add(this.meshFar);

        this.updateVisibility();
    }

    updateVisibility() {
        const isVisible = CONFIG.ui.groundMode && CONFIG.grass.enabled;
        if(this.meshNear) this.meshNear.visible = isVisible;
        if(this.meshFar) this.meshFar.visible = isVisible && CONFIG.grass.lodEnabled;
    }

    // Обновление параметров в реальном времени
    _grassRaycaster = new THREE.Raycaster();

    update(camPos, time) {
        if (!this.meshNear || !this.meshNear.visible) return;

        const updateMat = (mat, isFar) => {
            // ОПТИМИЗАЦИЯ: Используем глобальный экземпляр
            this._grassRaycaster.setFromCamera(pointerNDC, camera);
            
            mat.uniforms.uMouseRayOrigin.value.copy(this._grassRaycaster.ray.origin);
            mat.uniforms.uMouseRayDir.value.copy(this._grassRaycaster.ray.direction);
            
            mat.uniforms.uMouseEnabled.value = CONFIG.grass.mouseInteract ? 1.0 : 0.0;
            mat.uniforms.uMouseRadius.value = CONFIG.grass.mouseRadius;
            mat.uniforms.uMouseStrength.value = CONFIG.grass.mouseStrength;

            mat.uniforms.uLightDir.value.copy(globalUniforms.uLightDir.value);
            mat.uniforms.uLightRadius.value = CONFIG.flashlight.radius;

            mat.uniforms.uShapeChances.value.set(0, CONFIG.grass.altChance2, CONFIG.grass.altChance3, CONFIG.grass.altChance4);
            mat.uniforms.uShapeStructs.value.set(0, CONFIG.grass.struct2, CONFIG.grass.struct3, CONFIG.grass.struct4);
            mat.uniforms.uShapeThins.value.set(0, CONFIG.grass.thin2, CONFIG.grass.thin3, CONFIG.grass.thin4);
            
            if (isFar) {
                mat.uniforms.uFarShapeChances.value.set(0, CONFIG.grass.farAltChance2, CONFIG.grass.farAltChance3, 0);
                mat.uniforms.uFarShapeStructs.value.set(0, CONFIG.grass.farStruct2, CONFIG.grass.farStruct3, 0);
                mat.uniforms.uFarShapeThins.value.set(0, CONFIG.grass.farThin2, CONFIG.grass.farThin3, 0);
                
                // БЕЗОПАСНАЯ ПЕРЕДАЧА: Передаем вектор ослабления ветра для дальнего плана
                if (mat.uniforms.uShapeWindDamp && mat.uniforms.uShapeWindDamp.value && CONFIG.grass.farShapeMods.windDamp) {
                    mat.uniforms.uShapeWindDamp.value.set(
                        CONFIG.grass.farShapeMods.windDamp.x || 0,
                        CONFIG.grass.farShapeMods.windDamp.y || 0,
                        CONFIG.grass.farShapeMods.windDamp.z || 0,
                        CONFIG.grass.farShapeMods.windDamp.w || 0
                    );
                }
            } else {
                // БЕЗОПАСНАЯ ПЕРЕДАЧА: Передаем вектор ослабления ветра для ближнего плана
                if (mat.uniforms.uShapeWindDamp && mat.uniforms.uShapeWindDamp.value && CONFIG.grass.shapeMods.windDamp) {
                    mat.uniforms.uShapeWindDamp.value.set(
                        CONFIG.grass.shapeMods.windDamp.x || 0,
                        CONFIG.grass.shapeMods.windDamp.y || 0,
                        CONFIG.grass.shapeMods.windDamp.z || 0,
                        CONFIG.grass.shapeMods.windDamp.w || 0
                    );
                }
            }

            mat.uniforms.uCamPos.value.copy(camPos);
            mat.uniforms.uCamDir.value.copy(globalUniforms.uCamDir.value);
            mat.uniforms.uTime.value = time;

            mat.uniforms.uAmplitude.value = CONFIG.terrain.amplitude;
            mat.uniforms.uFrequency.value = CONFIG.terrain.frequency;
            mat.uniforms.uOffset.value = CONFIG.terrain.offset;
            mat.uniforms.uSharpness.value = CONFIG.terrain.sharpness;
            mat.uniforms.uFogColor.value.copy(CONFIG.terrain.fogColor);
            mat.uniforms.uFogDensity.value = CONFIG.terrain.fogDensity;
            mat.uniforms.uGrassGustFreq.value = CONFIG.grass.gustFreq; 
            mat.uniforms.uGrassGustSmoothness.value = CONFIG.grass.gustSmoothness;
            mat.uniforms.uGrassGustSpeed.value = CONFIG.grass.gustSpeed;

            mat.uniforms.uShape4.value = CONFIG.grass.shape4;
            
            mat.uniforms.uDrawDistance.value = isFar ? CONFIG.grass.farDistance : CONFIG.grass.drawDistance;
            if (isFar) {
                // ВЫЧИТАЕМ ОФСЕТ, ЧТОБЫ LOD НАЧИНАЛСЯ БЛИЖЕ К КАМЕРЕ
                mat.uniforms.uInnerRadius.value = Math.max(0.0, CONFIG.grass.drawDistance - CONFIG.grass.lodOffset); 
                mat.uniforms.uSizeMult.value = CONFIG.grass.farSizeMult;
            }

            // Также передаем настройки камеры для расталкивания:
            mat.uniforms.uCameraInteract.value = CONFIG.grass.cameraInteract ? 1.0 : 0.0;
            mat.uniforms.uCameraRadius.value = CONFIG.grass.cameraRadius;
        };

        updateMat(this.materialNear, false);
        if (CONFIG.grass.lodEnabled && this.meshFar) updateMat(this.materialFar, true);
    }
}

const grassSystem = new GrassSystem(scene); // <-- НОВОЕ
const rockSystem = new RockSystem(scene);

const comet = new CometSystem(scene);
const fallenStarSystem = new FallenStarSystem(scene); // <--- ДОБАВИТЬ ЭТО
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

// Переменная для подсчёта собранных звёзд с сохранением прогресса в браузере
let collectedStarsCount = parseInt(localStorage.getItem('collected_stars_count') || '0');
const floatingTexts = [];

// Функция создания всплывающего в 3D пространстве текста "+! (кол-во)"
function spawnFloatingText(text, pos) {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 128;
    const ctx = canvas.getContext('2d');
    
    ctx.fillStyle = '#ffaa00'; // Оранжево-желтый цвет
    ctx.font = 'bold 32px "Courier New", monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, 128, 64);

    const texture = new THREE.CanvasTexture(canvas);
    const mat = new THREE.SpriteMaterial({ 
        map: texture, 
        transparent: true, 
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        depthTest: false
    });
    
    const sprite = new THREE.Sprite(mat);
    sprite.position.copy(pos);
    sprite.position.y += 12.0; // Спавним чуть выше центра звезды
    sprite.scale.set(40, 20, 1);
    sprite.renderOrder = 1000;
    
    sprite.userData = {
        life: 1.0,      // Время жизни (от 1.0 до 0.0)
        speedY: 25.0    // Скорость подъёма вверх
    };
    
    scene.add(sprite);
    floatingTexts.push(sprite);
}

// Функция обновления анимации всплывающих текстов (вызывается в animate)
function updateFloatingTexts(dt) {
    for (let i = floatingTexts.length - 1; i >= 0; i--) {
        const sprite = floatingTexts[i];
        sprite.position.y += sprite.userData.speedY * dt;
        sprite.userData.life -= dt * 0.6; // Полное исчезновение примерно за 1.6 секунды
        sprite.material.opacity = Math.max(0, sprite.userData.life);
        
        if (sprite.userData.life <= 0) {
            scene.remove(sprite);
            sprite.material.map.dispose();
            sprite.material.dispose();
            floatingTexts.splice(i, 1);
        }
    }
}


// Максимальная дистанция для загрузки (чуть больше дальности видимости)
const MAX_LOAD_DIST = 2000;
let isStartupMode = true;
setTimeout(() => { 
    isStartupMode = false; 
    //console.log("[LOADER] Startup mode ended. Kill switch armed.");
}, 10000); // 10 секунд "тишины" на старте
const state = {
    chunks: new Map(),
    targetPos: new THREE.Vector3(0, 0, 1000), 
    currentPos: new THREE.Vector3(0, 0, 1000), 
    isDragging: false,
    isLooking: false,
    lastMouse: { x: 0, y: 0 },
    currentChunk: { x: null, y: null, z: null },
    
    // ДОБАВЛЕНЫ q и e
    keys: { w: false, a: false, s: false, d: false, up: false, down: false, left: false, right: false, q: false, e: false },
    
    look: {
        targetX: 0, 
        targetY: 0, 
        targetZ: 0, // <-- ДОБАВЛЕНО
        currentX: 0, 
        currentY: 0,
        currentZ: 0 // <-- ДОБАВЛЕНО
    },

    joystick: {
        left: { x: 0, y: 0, active: false },
        right: { x: 0, y: 0, active: false }
    },

    loadQueue: [],
    activeTasks: new Map(),
    queueTimeout: null
};

// Функция оценки важности задачи (меньше = важнее)
function getTaskScore(pos, cameraPos, cameraDir, frustum) {
    const p = new THREE.Vector3(pos[0], pos[1], pos[2]);
    const dist = p.distanceTo(cameraPos);
    
    // Проверка на попадание в камеру (с небольшим запасом radius 50)
    const isVisible = frustum.intersectsSphere(new THREE.Sphere(p, 50));
    
    if (isVisible) {
        // ПРИОРИТЕТ 1: На экране.
        // Оценка равна дистанции (0...2000). Чем ближе, тем меньше число, тем важнее.
        return dist; 
    } else {
        // Проверяем, спереди ли оно
        const toItem = new THREE.Vector3().subVectors(p, cameraPos).normalize();
        const dot = cameraDir.dot(toItem);
        
        if (dot > 0.5) { 
            // ПРИОРИТЕТ 2: Спереди, но за кадром (или далеко).
            // Добавляем 100 000, чтобы они грузились строго после видимых.
            return 100000 + dist; 
        } else {
            // ПРИОРИТЕТ 3: Сзади.
            // Добавляем 500 000. Грузим в последнюю очередь.
            return 500000 + dist;
        }
    }
}

// Главная функция управления очередью
function processLoadQueue() {
    // 1. Подготовка данных
    camera.updateMatrixWorld();
    const projScreenMatrix = new THREE.Matrix4();
    projScreenMatrix.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
    const frustum = new THREE.Frustum();
    frustum.setFromProjectionMatrix(projScreenMatrix);

    const cameraDir = new THREE.Vector3();
    camera.getWorldDirection(cameraDir);
    const cameraPos = camera.position;

    // 2. Сортировка очереди (пересчитываем приоритеты)
    state.loadQueue.forEach(item => {
        item.score = getTaskScore(item.pos, cameraPos, cameraDir, frustum);
    });
    state.loadQueue.sort((a, b) => a.score - b.score);

    // 3. АГРЕССИВНАЯ ОТМЕНА (KILL SWITCH)
    // ИЗМЕНЕНИЕ: Не используем Kill Switch в режиме старта (isStartupMode)
    if (!isStartupMode && state.activeTasks.size >= MAX_CONCURRENT_LOADS && state.loadQueue.length > 0) {
        const bestCandidate = state.loadQueue[0]; 
        
        let worstActiveId = null;
        let worstActiveScore = -1;

        // Ищем кандидата на убийство
        for (const [id, task] of state.activeTasks) {
            // Не убиваем задачи, которые живут меньше 2 секунд
            if (Date.now() - task.startTime < 2000) continue;

            // Пересчитываем скор для активной задачи
            const currentScore = getTaskScore(task.pos, cameraPos, cameraDir, frustum);
            
            if (currentScore > worstActiveScore) {
                worstActiveScore = currentScore;
                worstActiveId = id;
            }
        }

        // Логика отмены: убиваем только если выигрыш в приоритете существенный
        if (worstActiveId && worstActiveScore > bestCandidate.score + 3000) {
            //console.warn(`[LOADER KILL] Aborting ${worstActiveId} for ${bestCandidate.postId}`);
            const taskToKill = state.activeTasks.get(worstActiveId);
            if (taskToKill && taskToKill.controller) {
                taskToKill.controller.abort();
            }
            return; 
        }
    }

    // 4. Запуск новых задач
    while (state.activeTasks.size < MAX_CONCURRENT_LOADS && state.loadQueue.length > 0) {
        const task = state.loadQueue.shift();
        runTask(task);
    }
}

// --- ЗАМЕНИТЬ ФУНКЦИЮ runTask ЦЕЛИКОМ ---
function runTask(task) {
    const controller = new AbortController();
    const taskId = task.postId;
    
    // --- ДИНАМИЧЕСКИЙ ТАЙМАУТ ---
    // Проверяем видимость прямо перед стартом задачи
    const p = new THREE.Vector3(task.pos[0], task.pos[1], task.pos[2]);
    camera.updateMatrixWorld(); 
    const frustum = new THREE.Frustum().setFromProjectionMatrix(
        new THREE.Matrix4().multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse)
    );
    const isUrgent = frustum.intersectsSphere(new THREE.Sphere(p, 50));

    // Если срочно (на экране) - ждем всего 4 сек API, иначе 20 сек
    const apiTimeoutMs = isUrgent ? 4000 : 20000;
    // Если срочно - ждем картинку 6 сек, иначе 15 сек
    const imgTimeoutMs = isUrgent ? 6000 : 15000;

    const safetyTimeout = setTimeout(() => {
        if (state.activeTasks.has(taskId)) {
            const t = state.activeTasks.get(taskId);
            // Если это срочная задача - помечаем красным, что "слишком медленно"
            const msg = isUrgent ? '[URGENT TIMEOUT]' : '[WATCHDOG]';
            //console.warn(`${msg} Force killing stuck task: ${taskId}`);
            
            controller.abort();
            if (task.onStatus) task.onStatus('TIMEOUT', '#ff3333');
            
            // Вызываем ошибку, чтобы запустить механизм замены ID
            if (t && t.onError) t.onError(true); // true = fatal, меняем сразу
            
            finishTask(taskId);
        }
    }, apiTimeoutMs + imgTimeoutMs); // Общий предохранитель

    state.activeTasks.set(taskId, {
        controller: controller,
        pos: task.pos,
        startTime: Date.now(),
        timeoutId: safetyTimeout,
        onError: task.onError
    });

    if (task.onStatus) task.onStatus(isUrgent ? '!!! URGENT !!!' : `API REQ: ${taskId}`, isUrgent ? '#ff00ff' : '#ffff00');

    const urlParams = new URLSearchParams(window.location.search);
    const customChannel = urlParams.get('channel_id');
    const channelParam = customChannel ? `&channel_id=${customChannel}` : '';
    
    // ДОБАВЛЕНО: Параметр прокси
    const proxyParam = `&use_proxy=${CONFIG.network.useProxy}`;

    // Измененная строка запроса:
    fetch(`/api/anemone/resolve_image?post_id=${taskId}${channelParam}${proxyParam}`, { signal: controller.signal })
        .then(r => r.json())
        .then(data => {
            if (data.error === 'access_denied') {
                if (task.onStatus) task.onStatus('ERR: ACCESS DENIED', '#ff0000');
                task.onError(true); // Fatal
                finishTask(taskId); 
                return;
            }
            
            if (data.found && data.url) {
                if (controller.signal.aborted) return;

                if (task.onStatus) task.onStatus('LOADING IMG...', '#00ffff');

                const loader = new THREE.ImageLoader();
                loader.setCrossOrigin('anonymous');
                
                // Таймер чисто на загрузку картинки
                const imgTimeout = setTimeout(() => {
                    if (controller.signal.aborted) return;
                    //console.warn(`[IMG TIMEOUT] ${taskId} took too long.`);
                    if (task.onStatus) task.onStatus('IMG TIMEOUT', '#ff0000');
                    task.onError(true); // Считаем фатальным, меняем ID
                    finishTask(taskId);
                }, imgTimeoutMs);                

                loader.load(
                    data.url,
                    (image) => {
                        clearTimeout(imgTimeout);
                        if (controller.signal.aborted) return;
                        
                        if (task.onStatus) task.onStatus('GENERATING...', '#00ff00');
                        
                        // --- ГЕНЕРАЦИЯ ПОЛАРОИДА (без изменений) ---
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
                        ctx.fillStyle = '#ffffff';
                        ctx.fillRect(0, 0, canvas.width, canvas.height);
                        ctx.drawImage(image, borderSide, borderTop, drawWidth, drawHeight);
                        
                        if (data.date) {
                            ctx.fillStyle = '#888888';
                            ctx.font = '500 14px "Helvetica Neue", Arial, sans-serif';
                            ctx.textAlign = 'left';
                            ctx.fillText(data.date, borderSide, borderTop + drawHeight + 30);
                        }
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
                                if (metrics.width > maxWidth && n > 0) {
                                    ctx.fillText(line, textX, textY);
                                    line = words[n] + ' ';
                                    textY += lineHeight;
                                    lineCount++;
                                    if(lineCount >= maxLines) { line = line.trim() + '...'; break; }
                                } else { line = testLine; }
                            }
                            if (lineCount < maxLines) ctx.fillText(line, textX, textY);
                        }

                        const tex = new THREE.CanvasTexture(canvas);
                        const totalRatio = cardWidth / cardHeight;
                        
                        if (task.onStatus) task.onStatus(`OK`, '#00ff00');
                        
                        task.onSuccess(tex, totalRatio);
                        finishTask(taskId);
                    },
                    undefined, 
                    (err) => {
                        clearTimeout(imgTimeout);
                        if (task.onStatus) task.onStatus('IMG ERR', '#ff0000');
                        // Если ошибка загрузки картинки и это срочно - меняем ID сразу
                        task.onError(isUrgent); 
                        finishTask(taskId);
                    }
                );
            } else {
                if (task.onStatus) task.onStatus('API: NOT FOUND', '#ff0000');
                // Если не найдено - это всегда фатально
                task.onError(true); 
                finishTask(taskId);
            }
        })
        .catch((err) => {
            if (err.name === 'AbortError') {
                if (task.onStatus) task.onStatus('ABORTED', '#ffaa00');
            } else {
                if (task.onStatus) task.onStatus('FETCH ERR', '#ff0000');
                task.onError(isUrgent); // Если срочно - фатально
            }
            finishTask(taskId);
        });
}
function finishTask(id) {
    // Безопасное получение
    if (!state.activeTasks.has(id)) {
        // Если задачи уже нет, просто запускаем очередь дальше (на всякий случай)
        // Делаем это асинхронно, чтобы избежать переполнения стека
        setTimeout(processLoadQueue, 0); 
        return;
    }

    const task = state.activeTasks.get(id);
    if (task && task.timeoutId) {
        clearTimeout(task.timeoutId); // Убираем таймер
    }
    
    state.activeTasks.delete(id);
    
    // ВАЖНО: Небольшая задержка перед следующим, чтобы дать браузеру выдохнуть
    setTimeout(processLoadQueue, 10);
}
// Добавляем задачу и сразу вызываем обработчик
function queueImageLoad(postId, pos, onSuccess, onError) {
    // Проверка дубликатов в очереди
    if (state.loadQueue.some(t => t.postId === postId)) return;
    // Проверка дубликатов в активных (уже грузится)
    if (state.activeTasks.has(postId)) return;

    state.loadQueue.push({ 
        postId, 
        pos, 
        onSuccess, 
        onError,
        score: 0 // Будет рассчитано в processLoadQueue
    });
    
    // Дебаунс, чтобы не сортировать 100 раз при генерации чанка
    if (!state.queueTimeout) {
        state.queueTimeout = setTimeout(() => {
            state.queueTimeout = null;
            processLoadQueue();
        }, 50);
    }
}
// --- МАТЕРИАЛ ДЛЯ ОРЕОЛА (HALO) ---
const haloMaterial = new THREE.SpriteMaterial({
    map: new THREE.CanvasTexture((() => {
        const canvas = document.createElement('canvas');
        canvas.width = 128; 
        canvas.height = 128;
        const ctx = canvas.getContext('2d');
        
        // Рисуем "Glow" - плотный центр, мягкие края
        const grad = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
        
        // Центр: горячий белый
        grad.addColorStop(0.0, 'rgba(255, 255, 255, 1.0)');
        // Ближнее ядро: очень плотный белый с оттенком
        grad.addColorStop(0.2, 'rgba(255, 255, 255, 0.9)'); 
        // Основное тело света
        grad.addColorStop(0.4, 'rgba(255, 255, 255, 0.4)');
        // Мягкий хвост
        grad.addColorStop(1.0, 'rgba(255, 255, 255, 0.0)');
        
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, 128, 128);
        return canvas;
    })()),
    blending: THREE.AdditiveBlending,
    depthWrite: false, 
    transparent: true,
    opacity: 1.0 // Увеличили прозрачность материала (альфа управляется текстурой)
});
class FloatingSphereSystem {
    constructor(scene, camera) {
        this.scene = scene;
        this.camera = camera;
        
        this.activeCount = CONFIG.spheres.count;
        this.trailLimit = CONFIG.spheres.trailCount;
        this.maxTrailParticles = 2000; 
        
        this.sprites = []; 
        this.halos = [];   
        this.items = [];   

        this.baseSphereMat = new THREE.ShaderMaterial({
            uniforms: {
                uColor: { value: new THREE.Color() },
                uTime: { value: 0 },
                uFadeStart: { value: 2400.0 },
                uFadeEnd: { value: 1000.0 }
            },
            vertexShader: `
                varying vec3 vNormal;
                varying vec3 vViewDir;
                varying float vDist;
                void main() {
                    vNormal = normalize(normalMatrix * normal);
                    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
                    vViewDir = normalize(-mvPosition.xyz);
                    gl_Position = projectionMatrix * mvPosition;
                    vDist = length(mvPosition.xyz); 
                }
            `,
            fragmentShader: `
                uniform vec3 uColor;
                uniform float uFadeStart;
                uniform float uFadeEnd;
                varying vec3 vNormal;
                varying vec3 vViewDir;
                varying float vDist;
                
                void main() {
                    float viewDot = dot(vNormal, vViewDir);
                    viewDot = clamp(viewDot, 0.0, 1.0);
                    float coreIntensity = pow(viewDot, 0.8); 
                    vec3 finalColor = mix(uColor, vec3(1.0), coreIntensity * 0.8);
                    finalColor *= 1.5;
                    float softEdge = smoothstep(0.0, 0.4, viewDot);
                    float distAlpha = smoothstep(uFadeStart, uFadeEnd, vDist);
                    gl_FragColor = vec4(finalColor, softEdge * distAlpha);
                }
            `,
            transparent: true,
            blending: THREE.AdditiveBlending, 
            depthWrite: false, 
            side: THREE.FrontSide
        });

        const tGeo = new THREE.BufferGeometry();
        tGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(this.maxTrailParticles * 3), 3));
        tGeo.setAttribute('color', new THREE.BufferAttribute(new Float32Array(this.maxTrailParticles * 3), 3));
        tGeo.setAttribute('opacity', new THREE.BufferAttribute(new Float32Array(this.maxTrailParticles), 1));
        
        this.trailMat = new THREE.ShaderMaterial({
            uniforms: {
                uScale: { value: window.innerHeight },
                uSize: { value: CONFIG.spheres.trailSize },
                uBlur: { value: CONFIG.spheres.trailBlur },
                uOpacity: { value: CONFIG.spheres.trailOpacity },
                uFadeStart: { value: 2400.0 }, // <-- Настройки дистанции как у самих сфер
                uFadeEnd: { value: 1000.0 }
            },
            vertexShader: `
                attribute float opacity;
                attribute vec3 color;
                varying vec3 vColor;
                varying float vOpacity;
                varying float vDist; // <-- Добавлено
                uniform float uScale;
                uniform float uSize;
                void main() {
                    vColor = color;
                    vOpacity = opacity;
                    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
                    gl_Position = projectionMatrix * mvPosition;
                    vDist = length(mvPosition.xyz); // <-- Расчет дистанции для тумана
                    gl_PointSize = (uSize * opacity) * (uScale / -mvPosition.z);
                }
            `,
            fragmentShader: `
                varying vec3 vColor;
                varying float vOpacity;
                varying float vDist; // <-- Добавлено
                uniform float uBlur;
                uniform float uOpacity;
                uniform float uFadeStart; // <-- Добавлено
                uniform float uFadeEnd;   // <-- Добавлено
                void main() {
                    if (vOpacity <= 0.01) discard;
                    vec2 uv = gl_PointCoord - vec2(0.5);
                    float dist = length(uv);
                    if (dist > 0.5) discard;
                    
                    float strength = 1.0 - (dist * 2.0);
                    strength = clamp(pow(strength, uBlur), 0.0, 1.0);
                    
                    // Применяем отсечение по дальности (туман), синхронно с ядром сферы
                    float distAlpha = smoothstep(uFadeStart, uFadeEnd, vDist);
                    
                    gl_FragColor = vec4(vColor, strength * vOpacity * uOpacity * distAlpha);
                }
            `,
            transparent: true,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });
        
        this.trails = new THREE.Points(tGeo, this.trailMat);
        this.trails.frustumCulled = false;
        scene.add(this.trails);
        this.trailItems = []; 
        
        this.initSpheres();
    }

    initSpheres() {
        this.sprites.forEach(s => { this.scene.remove(s); if(s.geometry) s.geometry.dispose(); });
        this.halos.forEach(h => { this.scene.remove(h); if(h.material && h.material !== haloMaterial) h.material.dispose(); });

        this.sprites = [];
        this.halos = [];
        this.items = [];

        const geometry = new THREE.SphereGeometry(1, 32, 32); 
        const center = this.camera.position;
        const maxBuffer = 30; 

        for(let i=0; i<maxBuffer; i++) {
            const itemData = {
                pos: new THREE.Vector3(),
                vel: new THREE.Vector3(),
                scaleMult: 1.0, 
                color: new THREE.Color(),
                phase: Math.random() * Math.PI * 2
            };
            
            this.randomizeItem(itemData, center, 5000); 
            this.items.push(itemData);

            const mat = this.baseSphereMat.clone();
            mat.uniforms.uColor.value.copy(itemData.color);
            const mesh = new THREE.Mesh(geometry, mat);
            
            const initialSize = CONFIG.spheres.baseSize * itemData.scaleMult;
            mesh.scale.set(initialSize, initialSize, initialSize);
            mesh.position.copy(itemData.pos);
            mesh.visible = i < this.activeCount;
            this.scene.add(mesh);
            this.sprites.push(mesh); 
            
            const halo = new THREE.Sprite(haloMaterial.clone());
            halo.material.color.copy(itemData.color); 
            const haloSize = initialSize * 5.0; 
            
            halo.scale.set(haloSize, haloSize, 1);
            halo.position.copy(itemData.pos);
            halo.visible = i < this.activeCount;
            this.scene.add(halo);
            this.halos.push(halo);
        }
    }

    randomizeItem(item, centerPos, range) {
        item.pos.set(
            centerPos.x + (Math.random() - 0.5) * range,
            centerPos.y + (Math.random() - 0.5) * 2000, 
            centerPos.z + (Math.random() - 0.5) * range
        );
        item.vel.set((Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4);
        item.scaleMult = 0.5 + Math.random() * 1.3;
        item.color = CONFIG.spheres.colors[Math.floor(Math.random() * 3)];
    }

    respawnItem(item) {
        item.pos.y = this.camera.position.y + (Math.random() - 0.5) * 2000;
        item.pos.z += (Math.random() - 0.5) * 500;
        item.pos.x += (Math.random() - 0.5) * 500;
        item.scaleMult = 0.5 + Math.random() * 1.3;
        item.color = CONFIG.spheres.colors[Math.floor(Math.random() * 3)];
    }

    update() {
        const time = performance.now() / 1000;
        const center = this.camera.position;
        const range = 5000; 
        const halfRange = range / 2;
        const configBaseSize = CONFIG.spheres.baseSize;

        for(let i=0; i<this.sprites.length; i++) {
            const mesh = this.sprites[i];
            const halo = this.halos[i];
            const item = this.items[i];
            
            const isVisible = i < this.activeCount;
            mesh.visible = isVisible;
            halo.visible = isVisible;
            
            if (!isVisible) continue;

            mesh.material.uniforms.uTime.value = time;
            mesh.material.uniforms.uColor.value.copy(item.color);
            halo.material.color.copy(item.color);
            
            item.pos.add(item.vel.clone().multiplyScalar(CONFIG.spheres.moveSpeed));

            let dx = item.pos.x - center.x;
            let dz = item.pos.z - center.z;
            let dy = item.pos.y - center.y;
            
            let didWrap = false;
            if (dx > halfRange) { item.pos.x -= range; didWrap = true; } 
            else if (dx < -halfRange) { item.pos.x += range; didWrap = true; }
            if (dz > halfRange) { item.pos.z -= range; didWrap = true; } 
            else if (dz < -halfRange) { item.pos.z += range; didWrap = true; }
            if (dy > 2500) { item.pos.y -= 5000; didWrap = true; }
            else if (dy < -2500) { item.pos.y += 5000; didWrap = true; }

            if (didWrap) this.respawnItem(item);

            mesh.position.copy(item.pos);
            halo.position.copy(item.pos);
            
            const targetSize = configBaseSize * item.scaleMult;
            if (Math.abs(mesh.scale.x - targetSize) > 0.01) {
                mesh.scale.set(targetSize, targetSize, targetSize);
                halo.scale.set(targetSize * 5.0, targetSize * 5.0, 1);
            }

            // МАТЕМАТИКА СПАВНА ЧАСТИЦ (Теперь ползунок количества работает)
            if (this.trailLimit > 0) {
                const distToCam = mesh.position.distanceTo(center);
                if (distToCam < 2300) { 
                    // Считаем, сколько частиц нужно выпустить в этом кадре, чтобы поддерживать лимит
                    const lifeDecay = 0.015 / Math.max(0.1, CONFIG.spheres.trailLength);
                    const lifeFrames = 1.0 / lifeDecay; 
                    const neededPerFrame = this.trailLimit / (lifeFrames * this.activeCount);
                    
                    let spawnCount = Math.floor(neededPerFrame);
                    if (Math.random() < (neededPerFrame - spawnCount)) spawnCount++;
                    
                    for(let k = 0; k < spawnCount; k++) {
                        this.spawnTrail(item.pos, item.color, targetSize); 
                    }
                }
            }
        }
        this.updateTrails(time);
    }

    spawnTrail(sourcePos, color, radius) {
        let p = this.trailItems.find(t => t.life <= 0);
        if (!p) {
            if (this.trailItems.length < this.maxTrailParticles) {
                // Добавили seed для уникальной траектории каждой частицы
                p = { pos: new THREE.Vector3(), vel: new THREE.Vector3(), life: 0, color: new THREE.Color(), seed: Math.random() * 100 };
                this.trailItems.push(p);
            } else return;
        }

        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2.0 * Math.random() - 1.0);
        
        const x = Math.sin(phi) * Math.cos(theta);
        const y = Math.sin(phi) * Math.sin(theta);
        const z = Math.cos(phi);

        p.pos.set(x, y, z).multiplyScalar(radius).add(sourcePos);
        
        // Применяем настройку Скорости
        const spd = Math.max(0.1, CONFIG.spheres.trailSpeed);
        p.vel.set(x * 0.4 * spd, (0.4 + Math.random() * 0.6) * spd, z * 0.4 * spd); 

        p.life = 1.0; 
        p.color.copy(color);
        p.seed = Math.random() * 100; // Обновляем сид
    }

    updateTrails(time) {
        const tPos = this.trails.geometry.attributes.position;
        const tCol = this.trails.geometry.attributes.color;
        const tOp = this.trails.geometry.attributes.opacity;

        const limit = Math.min(this.trailLimit, this.trailItems.length);
        const lifeDecay = 0.015 / Math.max(0.1, CONFIG.spheres.trailLength);
        const turb = CONFIG.spheres.trailTurbulence;

        for(let i=0; i<this.maxTrailParticles; i++) {
            if (i < limit) {
                const p = this.trailItems[i];
                if (p.life > 0) {
                    // ФИЗИКА ТРАЕКТОРИИ (Волны и искажения)
                    if (turb > 0.001) {
                        // Раскачиваем частицу (усиливается к концу жизни)
                        const tForce = turb * (1.2 - p.life) * 0.03;
                        p.vel.x += Math.sin(time * 8.0 + p.seed) * tForce;
                        p.vel.z += Math.cos(time * 6.7 + p.seed) * tForce;
                    }

                    p.pos.add(p.vel);
                    p.life -= lifeDecay;
                    
                    tPos.setXYZ(i, p.pos.x, p.pos.y, p.pos.z);
                    tCol.setXYZ(i, p.color.r, p.color.g, p.color.b);
                    tOp.setX(i, Math.max(0, p.life));
                } else {
                    tOp.setX(i, 0);
                }
            } else {
                tOp.setX(i, 0);
            }
        }
        tPos.needsUpdate = true;
        tCol.needsUpdate = true;
        tOp.needsUpdate = true;
    }
    
    refresh() {
        this.activeCount = CONFIG.spheres.count;
        this.trailLimit = CONFIG.spheres.trailCount;
        
        if (this.trailMat) {
            this.trailMat.uniforms.uSize.value = CONFIG.spheres.trailSize;
            this.trailMat.uniforms.uBlur.value = CONFIG.spheres.trailBlur;
            this.trailMat.uniforms.uOpacity.value = CONFIG.spheres.trailOpacity;
        }
        
        // ВНИМАНИЕ: Цикл назначения случайных цветов здесь удален.
        // Теперь цвет сфер при настройке шлейфов не будет скакать.
    }
}
// ВАЖНО: Добавьте этот вызов в ваш основной цикл animate(), 
// чтобы пересчитывать приоритеты когда камера движется
setInterval(() => {
    // Если очередь переполнена, не вмешиваемся, даем ей разгрестись
    if (state.loadQueue.length > 5 || state.activeTasks.size >= MAX_CONCURRENT_LOADS) return;

    // Сканируем все загруженные чанки
    let restartedCount = 0;
    
    state.chunks.forEach(chunk => {
        if (!chunk.group) return;
        
        chunk.group.traverse(obj => {
            if (obj.isMesh && obj.userData && obj.userData.reload) {
                // Проверяем: это заглушка? (hasTexture == false)
                const uniforms = obj.material.uniforms;
                if (uniforms && uniforms.hasTexture && !uniforms.hasTexture.value) {
                    
                    const pid = obj.userData.postId;
                    
                    // Проверяем: грузится ли оно прямо сейчас?
                    const isQueued = state.loadQueue.some(t => t.postId === pid);
                    const isActive = state.activeTasks.has(pid);
                    
                    // Если это заглушка И она нигде не числится в работе — она зависла.
                    if (!isQueued && !isActive) {
                        // ПЕРЕЗАПУСКАЕМ!
                        obj.userData.reload();
                        restartedCount++;
                    }
                }
            }
        });
    });

    if (restartedCount > 0) {
        //console.log(`🐕 Watchdog: Restarted ${restartedCount} stuck placeholders.`);
    }
}, 2000); // Проверка каждые 2 секунды

// --- КОНЕЦ НОВОГО БЛОКА ---
const sphereSystem = new FloatingSphereSystem(scene, camera);

// --- ОБНОВЛЕННАЯ ФУНКЦИЯ loadChunk ---
async function loadChunk(cx, cy, cz) {
    const key = `${cx},${cy},${cz}`;
    if (state.chunks.has(key)) return;
    
    const g = new THREE.Group();
    g.position.set(cx * CHUNK_SIZE, cy * CHUNK_SIZE, cz * CHUNK_SIZE);
    scene.add(g);
    state.chunks.set(key, { group: g });

    try {
        const urlParams = new URLSearchParams(window.location.search);
        const maxId = urlParams.get('max_id') || 8509;
        const channelId = urlParams.get('channel_id') || 'default_world';

        const res = await fetch(`/api/anemone/get_chunk?x=${cx}&y=${cy}&z=${cz}&max_id=${maxId}&channel_id=${channelId}`);
        
        // --- ИСПРАВЛЕНИЕ: Безопасный парсинг ответа ---
        const text = await res.text(); // Сначала читаем как текст
        let data;
        try {
            data = JSON.parse(text); // Пробуем распарсить
        } catch (e) {
            console.warn(`[API ОШИБКА] Чанк ${key} вернул не JSON. Ответ сервера:`, text.substring(0, 100));
            return; // Выходим из функции, чтобы не крашить сцену
        }
        
        if (data && data.items) {
            data.items.forEach(item => createHangingArt(g, item, key));
        }
    } catch (e) {
        console.error(`[СЕТЕВАЯ ОШИБКА] Не удалось загрузить чанк ${key}:`, e);
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



const PostRecovery = {
    // Хранит кол-во ошибок для каждого ID: { 101: 1, 101: 2, ... }
    failures: new Map(),
    // Кэш замен, чтобы не пересчитывать (оптимизация)
    replacements: new Map(),
    // Максимум ID в вашей базе (для формулы математического кольца)
    MAX_ID: 8509, 
    // Лимит попыток перед заменой
    RETRY_LIMIT: 2, 

    /**
     * Возвращает True, если нужно попробовать этот ID еще раз.
     * Возвращает False, если пора менять ID.
     */
    registerFailure: function(id) {
        const current = this.failures.get(id) || 0;
        const next = current + 1;
        this.failures.set(id, next);
        
        // Если ошибок меньше лимита - пробуем снова этот же ID
        return next <= this.RETRY_LIMIT;
    },

    /**
     * Детерминированная магия.
     * Вычисляет "следующий" ID на основе "плохого" ID.
     * Формула всегда выдает один и тот же результат для одного и того же входа.
     */
    getReplacement: function(badId) {
        // Если мы уже знаем замену, возвращаем её
        if (this.replacements.has(badId)) {
            return this.replacements.get(badId);
        }

        // Псевдо-случайный скачок (Linear Congruential Generator)
        // Используем простые числа для хорошего разброса, чтобы не попадать в соседние (возможно тоже удаленные) ID
        // Формула: (ID * Большое_Простое_Число + Смещение) % Макс_ID
        let nextId = (badId * 48271 + 1) % this.MAX_ID;
        
        if (nextId === 0) nextId = 1; // ID не может быть 0
        if (nextId === badId) nextId += 1; // Защита от самозамыкания

        // Запоминаем связь "Плохой -> Новый"
        this.replacements.set(badId, nextId);
        return nextId;
    }
};


function createHangingArt(group, data, chunkKey) {
    const baseScale = data.scale[0] * CONFIG.cards.size; 
    const geometry = currentPaperGeometry;
    const objSeed = cyrb128(data.id || Math.random().toString());
    const phase = seededRandom(objSeed) * 10;
    const swaySpeed = 0.5 + seededRandom(objSeed + 1) * 0.5;
    
    // Применяем отдаление (spacing) к локальным координатам чанка
    const localX = data.pos[0] * CONFIG.cards.spacing;
    const localZ = data.pos[2] * CONFIG.cards.spacing;
    
    let targetY = data.pos[1] + (baseScale / 2);
    let isHiddenByGroundMode = false; 

    if (CONFIG.ui.groundMode) {
        if ((objSeed % 100) > 25) {
            isHiddenByGroundMode = true;
        }

        // Вычисляем АБСОЛЮТНУЮ позицию с учетом spacing
        const worldX = group.position.x + localX;
        const worldZ = group.position.z + localZ;
        const tHeight = getTerrainHeight(worldX, worldZ);
        
        // Используем CONFIG.cards.heightOffset
        const absoluteY = tHeight + baseScale + CONFIG.cards.heightOffset + (objSeed % 100) / 10.0; 
        targetY = absoluteY - group.position.y;
    }
    const pos = new THREE.Vector3(localX, targetY, localZ);
    // -------------------------------------
    
    const material = new THREE.ShaderMaterial({
        vertexShader: paperVertexShader,
        // По умолчанию компилируем шейдер БЕЗ текстуры (показываем лоадер)
        fragmentShader: paperFragmentShader,
        uniforms: {
            ...globalUniforms,
            map: { value: PLACEHOLDER_TEXTURE },
            uColor: { value: new THREE.Color(0xffffff) },
            uSizeMult: { value: CONFIG.details.fireflySize },          
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

    // ДОБАВИТЬ ЭТИ СТРОКИ: Сохраняем исходники для динамического обновления ползунками
    mesh.userData.origLocalX = data.pos[0];
    mesh.userData.origLocalY = data.pos[1];
    mesh.userData.origLocalZ = data.pos[2];
    mesh.userData.origScale = data.scale[0];

    mesh.position.copy(pos);
    mesh.scale.set(baseScale, baseScale, baseScale); 
    mesh.frustumCulled = true;

    mesh.matrixAutoUpdate = false;
    mesh.updateMatrix();

    // ЗАМЕНИТЕ СЛЕДУЮЩИЙ БЛОК НАСТРОЙКИ ВИДИМОСТИ:
    const isVisible = CONFIG.cards.enabled && !isHiddenByGroundMode;
    mesh.visible = isVisible;

    const lineMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.3 });
    const line = new THREE.Line(commonLineGeometry, lineMat);
    
    line.matrixAutoUpdate = false;
    line.updateMatrix();
    
    line.visible = isVisible;
    
    mesh.add(line);
    group.add(mesh);

    // --- ЛОГИКА ЗАГРУЗКИ (ВЫНЕСЕНА В ФУНКЦИЮ) ---
    const startLoading = () => {
        const currentPostId = mesh.userData.postId;

        queueImageLoad(currentPostId, data.pos, 
            // onSuccess
            (tex, ratio) => {
                if (PostRecovery.failures.has(currentPostId)) {
                    PostRecovery.failures.delete(currentPostId);
                }
                tex.minFilter = THREE.LinearFilter;
                tex.generateMipmaps = false;
                renderer.initTexture(tex); 

                if (mesh.material) { 
                    mesh.material.uniforms.map.value = tex;
                    mesh.material.uniforms.uAspectRatio.value = ratio; 
                    let scaleX = 1, scaleY = 1;
                    if (ratio > 1) scaleX = ratio;
                    else scaleY = 1 / ratio;
                    mesh.material.uniforms.uImageScale.value.set(scaleX, scaleY);
                    
                    // ДОБАВИТЬ ЭТИ 2 СТРОКИ:
                    mesh.material.defines = { HAS_TEXTURE: "" };
                    mesh.material.needsUpdate = true; // Заставит Three.js вырезать код лоадера
                }
            }, 
            // onError
            (isFatal = false) => { 
                // --- АГРЕССИВНАЯ ЗАМЕНА ДЛЯ ВИДИМЫХ ---
                // Проверяем видимость объекта
                const p = new THREE.Vector3(data.pos[0], data.pos[1], data.pos[2]);
                const frustum = new THREE.Frustum().setFromProjectionMatrix(
                    new THREE.Matrix4().multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse)
                );
                // Если объект на экране, мы считаем любую ошибку ФАТАЛЬНОЙ, 
                // чтобы не тратить время на повторную попытку мертвого ID.
                const isVisible = frustum.intersectsSphere(new THREE.Sphere(p, 50));
                
                if (isVisible) isFatal = true;

                // 1. Регистрируем ошибку
                const shouldRetrySame = PostRecovery.registerFailure(currentPostId);

                if (shouldRetrySame && !isFatal) {
                    // Фоновая задача, можно попробовать еще раз тот же ID
                    // Важно: перезапуск через watchdog
                } else {
                    // Видимая задача или лимит исчерпан -> МЕНЯЕМ ID
                    const newId = PostRecovery.getReplacement(currentPostId);

                    mesh.userData.postId = newId;
                    
                    const newSeed = cyrb128(newId.toString());
                    if(mesh.material.uniforms.uPhase) {
                        mesh.material.uniforms.uPhase.value = seededRandom(newSeed) * 10;
                    }

                    setTimeout(startLoading, 50);
                }
            }
        );
    };

    // Сохраняем функцию перезапуска в меш
    mesh.userData.reload = startLoading;

    // Запускаем первую попытку
    startLoading();
}

function unloadChunk(key) {
    const c = state.chunks.get(key);
    if(c) { 
        // --- НАЧАЛО ИСПРАВЛЕНИЯ ПАМЯТИ ---
        // Проходим по всем объектам внутри удаляемого чанка
        c.group.traverse(obj => {
            if (obj.isMesh) {
                // 1. Очистка материала
                if (obj.material) {
                    // Если у материала есть текстура (фотография), удаляем её из GPU
                    if (obj.material.uniforms && obj.material.uniforms.map && obj.material.uniforms.map.value) {
                        // Проверяем, что это не глобальная заглушка, чтобы не сломать остальные
                        if (obj.material.uniforms.map.value !== PLACEHOLDER_TEXTURE) {
                            obj.material.uniforms.map.value.dispose();
                        }
                    }
                    // Удаляем сам шейдерный материал
                    obj.material.dispose();
                }
                
                // 2. Очистка геометрии
                // В вашем коде геометрия общая (realisticPaperGeometry), её удалять НЕЛЬЗЯ.
                // Но если вы добавляли Line (веревку) с уникальной геометрией, удаляем её:
                if (obj.geometry && obj.geometry !== realisticPaperGeometry && obj.geometry !== simplePaperGeometry && obj.geometry !== commonLineGeometry) {
                     obj.geometry.dispose();
                }
            }
            // Если это объект Line (веревка)
            if (obj.isLine) {
                 if (obj.material) obj.material.dispose();
                 // Геометрия веревки у вас commonLineGeometry, её не трогаем
            }
        });
        // --- КОНЕЦ ИСПРАВЛЕНИЯ ---

        scene.remove(c.group); 
        state.chunks.delete(key);
    }
}

let lastChunkUpdate = 0;
function updateChunks() {
    const now = performance.now();
    // Обновляем сетку чанков только раз в 250 мс
    if (now - lastChunkUpdate < 250) return;
    lastChunkUpdate = now;

    const cx = Math.floor(state.currentPos.x/CHUNK_SIZE+0.5);
    const cy = Math.floor(state.currentPos.y/CHUNK_SIZE+0.5);
    const cz = Math.floor(state.currentPos.z/CHUNK_SIZE+0.5);
    
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
    // Проверяем, находится ли цель клика внутри панелей или кнопок
    return e.target.closest('#settings-panel') || 
           e.target.closest('#settings-btn') || 
           e.target.closest('.custom-picker-popover') ||
           e.target.closest('#search-panel') ||  // <--- Добавлено
           e.target.closest('#search-btn') ||    // <--- Добавлено
           e.target.closest('#comment-modal') || // <--- Добавлено (на случай скролла внутри модалки)
           e.target.closest('#add-btn');         // <--- Добавлено
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



window.addEventListener('keydown', (e) => {
    switch(e.code) {
        case 'KeyW': state.keys.w = true; break;
        case 'KeyS': state.keys.s = true; break;
        case 'KeyA': state.keys.a = true; break;
        case 'KeyD': state.keys.d = true; break;
        case 'ArrowUp': state.keys.up = true; break;
        case 'ArrowDown': state.keys.down = true; break;
        case 'ArrowLeft': state.keys.left = true; break;
        case 'ArrowRight': state.keys.right = true; break;
        case 'KeyQ': state.keys.q = true; break;
        case 'KeyE': state.keys.e = true; break;    
    }
});

window.addEventListener('keyup', (e) => {
    switch(e.code) {
        case 'KeyW': state.keys.w = false; break;
        case 'KeyS': state.keys.s = false; break;
        case 'KeyA': state.keys.a = false; break;
        case 'KeyD': state.keys.d = false; break;
        case 'ArrowUp': state.keys.up = false; break;
        case 'ArrowDown': state.keys.down = false; break;
        case 'ArrowLeft': state.keys.left = false; break;
        case 'ArrowRight': state.keys.right = false; break;
        case 'KeyQ': state.keys.q = false; break;
        case 'KeyE': state.keys.e = false; break;    
    }
});
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
// Слушатель внешних событий навигации (например, из галереи)
window.addEventListener('set-navigation-target', (e) => {
    const { x, y, z } = e.detail;
    navigationTarget = new THREE.Vector3(x, y, z);
    updateNavigationHUD();
    console.log(`New Target Set: ${x}, ${y}, ${z}`);
});

window.addEventListener('contextmenu', e => e.preventDefault());


// Координаты курсора для шейдера (-1 до 1). -999 значит курсор убран.
const pointerNDC = new THREE.Vector2(-999, -999);

// Обновляем позицию при движении мыши
window.addEventListener('mousemove', e => {
    pointerNDC.x = (e.clientX / window.innerWidth) * 2 - 1;
    pointerNDC.y = -(e.clientY / window.innerHeight) * 2 + 1;
});

// Убираем курсор, когда мышь уходит с экрана
window.addEventListener('mouseout', () => {
    pointerNDC.set(-999, -999);
});

// Поддержка для сенсорных экранов (пальцев)
window.addEventListener('touchmove', e => {
    if (e.touches.length > 0) {
        pointerNDC.x = (e.touches[0].clientX / window.innerWidth) * 2 - 1;
        pointerNDC.y = -(e.touches[0].clientY / window.innerHeight) * 2 + 1;
    }
}, { passive: false });

window.addEventListener('touchend', e => {
    if (e.touches.length === 0) pointerNDC.set(-999, -999);
});

window.addEventListener('mousedown', e => { 
    if (isUIInteraction(e)) return;

    // Левая кнопка (0) - Перемещение (Drag)
    if (e.button === 0) {
        state.isDragging = true; 
        state.lastMouse = { x: e.clientX, y: e.clientY }; 
        document.body.style.cursor = 'grabbing'; 
    }
    
    // Правая кнопка (2) - Осмотр (Look)
    if (e.button === 2) {
        state.isLooking = true;
        document.body.style.cursor = 'all-scroll';
    }
});

window.addEventListener('mouseup', () => { 
    state.isDragging = false; 
    state.isLooking = false; // При отпускании камера начнет возвращаться в центр
    document.body.style.cursor = 'default'; 
});

window.addEventListener('mousemove', e => {
    // Логика перетаскивания (Pan) - ЛКМ
    if (state.isDragging) {
        const dx = e.clientX - state.lastMouse.x;
        const dy = e.clientY - state.lastMouse.y;
        state.targetPos.x -= dx * 2.5;
        state.targetPos.y += dy * 2.5; 
        state.lastMouse = { x: e.clientX, y: e.clientY };
    }

    // Логика осмотра (Look) - ПКМ
    if (state.isLooking) {
        const sensitivity = 0.003;
        // Инвертируем или нет - зависит от предпочтений, обычно так:
        state.look.targetX -= e.movementX * sensitivity; 
        state.look.targetY -= e.movementY * sensitivity;

        // Ограничиваем угол наклона вверх/вниз (чтобы не сломать шею)
        const maxAngle = Math.PI / 4; // 45 градусов
        state.look.targetY = Math.max(-maxAngle, Math.min(maxAngle, state.look.targetY));
    }
});

window.addEventListener('wheel', e => { 
    // Если скроллим над меню настроек — камеру не зумим
    if (isUIInteraction(e)) return;
    
    state.targetPos.z += e.deltaY * 2.0;
}, { passive: false }); // passive: false позволяет при необходимости делать preventDefault, но тут не обязательно

window.addEventListener('touchstart', e => { 
    if (e.touches.length === 1) {
        if (isUIInteraction(e)) return;

        // Переводим координаты касания в NDC формат
        mouse.x = (e.touches[0].clientX / window.innerWidth) * 2 - 1;
        mouse.y = -(e.touches[0].clientY / window.innerHeight) * 2 + 1;
        raycaster.setFromCamera(mouse, camera);

        // Проверяем, не нажал ли пользователь на упавшую звезду
        const starIntersects = raycaster.intersectObjects(fallenStarSystem.group.children, false);
        if (starIntersects.length > 0) {
            const clickedMesh = starIntersects[0].object;
            collectFallenStar(clickedMesh);
            e.preventDefault(); // Предотвращаем начало перетаскивания (drag)
            return;
        }

        state.isDragging = true; 
        state.lastMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    } 
}, { passive: false });

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

// --- ЛОГИКА ВЫЕЗЖАЮЩЕГО МЕНЮ ---
const expandBtn = document.getElementById('expand-btn');
const sideControls = document.getElementById('side-controls');
let menuExpanded = false;

expandBtn.addEventListener('click', () => {
    menuExpanded = !menuExpanded;
    sideControls.classList.toggle('active', menuExpanded);
    expandBtn.classList.toggle('active', menuExpanded);
});


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
    
    // Обновляем CSS фон
    document.body.style.backgroundImage = 
        `linear-gradient(to top, ${cBot} 0%, ${cMid} 40%, ${cTop} 100%)`;
    
    // Обновляем 3D Небо
    skyDome.material.uniforms.colorBot.value.copy(CONFIG.colors.bottom);
    skyDome.material.uniforms.colorMid.value.copy(CONFIG.colors.mid);
    skyDome.material.uniforms.colorTop.value.copy(CONFIG.colors.top);

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


function updateCardsOnTerrainChange() {
    if (!CONFIG.ui.groundMode) return;
    updateAllCards(); // Используем универсальную функцию!
}
// --- СЛУШАТЕЛИ ДЛЯ НОВОГО СМЕШИВАНИЯ ФОРМ ---
const grassMixMode = document.getElementById('grass-mix-mode');
const grassMixExtras = document.getElementById('grass-mix-extras');

if (grassMixMode) { 
    grassMixMode.addEventListener('change', (e) => {
        CONFIG.grass.mixMode = parseFloat(e.target.value);
        
        if (grassMixExtras) {
            grassMixExtras.style.display = CONFIG.grass.mixMode > 0 ? 'block' : 'none';
            
            const mixCol1 = document.getElementById('grass-mix-colors-1');
            const mixCol2 = document.getElementById('grass-mix-colors-2');
            const mixCol3 = document.getElementById('grass-mix-colors-3'); // <--- ДОБАВЛЕНО
            
            if (mixCol1) mixCol1.style.display = CONFIG.grass.mixMode >= 1 ? 'block' : 'none';
            if (mixCol2) mixCol2.style.display = CONFIG.grass.mixMode >= 2 ? 'block' : 'none';
            if (mixCol3) mixCol3.style.display = CONFIG.grass.mixMode >= 3 ? 'block' : 'none'; // <--- ДОБАВЛЕНО
        }
        
        if (grassSystem.materialNear) grassSystem.materialNear.uniforms.uMixMode.value = CONFIG.grass.mixMode;
        if (grassSystem.materialFar) grassSystem.materialFar.uniforms.uMixMode.value = CONFIG.grass.mixMode;
    });
}

// Слушатели для ландшафта
// Переключатель вкл/выкл
// Переключатель вкл/выкл
// --- ОБНОВЛЕННАЯ ТУРБУЛЕНТНОСТЬ С РАСКРЫВАЮЩИМСЯ МЕНЮ ---
const turbMain = document.getElementById('grass-turb');
const turbExtras = document.getElementById('turb-extras');

const updateTurbUI = () => {
    if (parseFloat(turbMain.value) > 0) {
        turbExtras.style.display = 'block';
    } else {
        turbExtras.style.display = 'none';
    }
};

turbMain.addEventListener('input', (e) => {
    CONFIG.grass.turbulence = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uGrassTurbulence.value = CONFIG.grass.turbulence;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uGrassTurbulence.value = CONFIG.grass.turbulence;
    updateTurbUI();
});
updateTurbUI(); // Вызов при старте

// Обработчик авто-выравнивания камеры
document.getElementById('ui-auto-level').addEventListener('change', (e) => {
    CONFIG.ui.autoLevel = e.target.checked;
});
document.getElementById('render-resolution')?.addEventListener('input', (e) => {
    CONFIG.graphics.renderScale = parseFloat(e.target.value);
    renderer.setPixelRatio(CONFIG.graphics.renderScale);
    
    // !!! ДОБАВЛЕНО: Сразу корректируем размер пыли/звезд при изменении скейла !!!
    updateParticleScales(); 
});
// Включение/выключение травы
document.getElementById('grass-toggle').addEventListener('change', (e) => {
    CONFIG.grass.enabled = e.target.checked;
    grassSystem.updateVisibility(); 
});
// --- ОБЩИЕ ПРЕСЕТЫ КАЧЕСТВА / ПРОИЗВОДИТЕЛЬНОСТИ ---
document.getElementById('grass-quality-preset')?.addEventListener('change', (e) => {
    const quality = e.target.value;
    const dpr = window.devicePixelRatio || 1;

    // Сохраняем значения в зависимости от пресета
    switch (quality) {
        case 'ultra': 
            CONFIG.graphics.renderScale = Math.min(dpr, 2);
            CONFIG.grass.count = 300000;
            CONFIG.grass.drawDistance = 1200;
            CONFIG.grass.lodEnabled = true;
            CONFIG.grass.farCount = 150000;
            CONFIG.grass.farDistance = 3000;
            break;
            
        case 'high':
            CONFIG.graphics.renderScale = Math.min(dpr, 1.5);
            CONFIG.grass.count = 200000;
            CONFIG.grass.drawDistance = 1000;
            CONFIG.grass.lodEnabled = true;
            CONFIG.grass.farCount = 100000;
            CONFIG.grass.farDistance = 2500;
            break;
            
        case 'medium': 
            CONFIG.graphics.renderScale = Math.min(dpr, 1.0);
            CONFIG.grass.count = 100000;
            CONFIG.grass.drawDistance = 800;
            CONFIG.grass.lodEnabled = true;
            CONFIG.grass.farCount = 50000;
            CONFIG.grass.farDistance = 2000;
            break;
            
        case 'low': 
            CONFIG.graphics.renderScale = 0.75; 
            CONFIG.grass.count = 50000;
            CONFIG.grass.drawDistance = 600;
            CONFIG.grass.lodEnabled = false; 
            break;
            
        case 'potato': 
            CONFIG.graphics.renderScale = 0.5; 
            CONFIG.grass.count = 20000;
            CONFIG.grass.drawDistance = 400;
            CONFIG.grass.lodEnabled = false;
            break;
    }

    // Применяем вычисленное разрешение к рендеру
    renderer.setPixelRatio(CONFIG.graphics.renderScale);
    // 1. Обновляем все ползунки в интерфейсе, чтобы они отражали новую реальность
    if (typeof syncUIToConfig === 'function') syncUIToConfig();

    // 2. Мгновенно обновляем униформы дистанции для шейдеров
    if (grassSystem.materialNear) grassSystem.materialNear.uniforms.uDrawDistance.value = CONFIG.grass.drawDistance;
    if (grassSystem.materialFar) grassSystem.materialFar.uniforms.uDrawDistance.value = CONFIG.grass.farDistance;

    // 3. Обновляем видимость LOD'ов
    grassSystem.updateVisibility();

    // 4. Полностью пересоздаем геометрию травы с новым количеством
    debounceGrassRebuild();
});


function updateAllCards() {
    state.chunks.forEach(chunk => {
        chunk.group.traverse(obj => {
            if (obj.isMesh && obj.userData.origScale !== undefined) {
                const localX = obj.userData.origLocalX * CONFIG.cards.spacing;
                const localZ = obj.userData.origLocalZ * CONFIG.cards.spacing;
                const baseScale = obj.userData.origScale * CONFIG.cards.size;

                obj.scale.set(baseScale, baseScale, baseScale);

                let isHiddenByGroundMode = false;
                if (CONFIG.ui.groundMode) {
                    const seedVal = cyrb128(obj.userData.postId || '1') % 100;
                    if (seedVal > 25) {
                        isHiddenByGroundMode = true;
                    }
                    const worldX = chunk.group.position.x + localX;
                    const worldZ = chunk.group.position.z + localZ;
                    const tHeight = getTerrainHeight(worldX, worldZ);
                    
                    const absoluteY = tHeight + baseScale + CONFIG.cards.heightOffset + (cyrb128(obj.userData.postId || '1') % 100) / 10.0;
                    
                    obj.position.set(localX, absoluteY - chunk.group.position.y, localZ);
                    obj.userData.originalY = absoluteY - chunk.group.position.y;
                } else {
                    const targetY = obj.userData.origLocalY + (baseScale / 2);
                    obj.position.set(localX, targetY, localZ);
                }
                
                // ПРИМЕНЕНИЕ ТЕКУЩЕГО СОСТОЯНИЯ ОТОБРАЖЕНИЯ:
                const shouldBeVisible = CONFIG.cards.enabled && !isHiddenByGroundMode;
                obj.visible = shouldBeVisible;
                
                obj.updateMatrix();
                
                obj.children.forEach(child => {
                    if (child.isLine) {
                        child.visible = shouldBeVisible;
                        child.updateMatrix();
                    }
                });
            }
        });
    });
}

function updateCardsVisibility() {
    state.chunks.forEach(chunk => {
        chunk.group.traverse(obj => {
            if (obj.isMesh && obj.userData.origScale !== undefined) {
                let isHiddenByGroundMode = false;
                if (CONFIG.ui.groundMode) {
                    const seedVal = cyrb128(obj.userData.postId || '1') % 100;
                    if (seedVal > 25) {
                        isHiddenByGroundMode = true;
                    }
                }
                const isVisible = CONFIG.cards.enabled && !isHiddenByGroundMode;
                obj.visible = isVisible;
                obj.children.forEach(c => {
                    if (c.isLine) c.visible = isVisible;
                });
            }
        });
    });
}

document.getElementById('cards-toggle')?.addEventListener('change', (e) => {
    CONFIG.cards.enabled = e.target.checked;
    updateCardsVisibility();
});

document.getElementById('grass-gust-smooth').addEventListener('input', (e) => {
    CONFIG.grass.gustSmoothness = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uGrassGustSmoothness.value = CONFIG.grass.gustSmoothness;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uGrassGustSmoothness.value = CONFIG.grass.gustSmoothness;
});
document.getElementById('grass-shape-4')?.addEventListener('change', (e) => {
    CONFIG.grass.shape4 = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uShape4.value = CONFIG.grass.shape4;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uShape4.value = CONFIG.grass.shape4;
});


// --- СЛУШАТЕЛИ ДЛЯ ВОДЫ ---
document.getElementById('reflect-toggle')?.addEventListener('change', (e) => {
    CONFIG.water.reflections = e.target.checked;
    terrainSystem.material.uniforms.uReflectEnabled.value = e.target.checked ? 1.0 : 0.0;
});
document.getElementById('reflect-res')?.addEventListener('change', (e) => {
    CONFIG.water.resolution = parseInt(e.target.value);
    reflectionSystem.resize(CONFIG.water.resolution);
});
document.getElementById('reflect-intensity')?.addEventListener('input', (e) => {
    CONFIG.water.intensity = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uReflectIntensity.value = CONFIG.water.intensity;
});
document.getElementById('reflect-distortion')?.addEventListener('input', (e) => {
    CONFIG.water.distortion = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uReflectDist.value = CONFIG.water.distortion;
});


// --- СЛУШАТЕЛИ КАМНЕЙ И БУЛЫЖНИКОВ ---
let rockRebuildTimeout;
function debounceRockRebuild() {
    clearTimeout(rockRebuildTimeout);
    rockRebuildTimeout = setTimeout(() => {
        rockSystem.build(); // Пересоздает геометрию при смене количества/формы
    }, 250);
}

document.getElementById('rock-toggle')?.addEventListener('change', (e) => {
    CONFIG.rocks.enabled = e.target.checked;
    rockSystem.updateVisibility();
    debounceRockRebuild(); // Перестраивает сетки при активации/деактивации
});
document.getElementById('rock-count')?.addEventListener('input', (e) => {
    CONFIG.rocks.count = parseInt(e.target.value);
    debounceRockRebuild();
});

document.getElementById('rock-size')?.addEventListener('input', (e) => {
    CONFIG.rocks.size = parseFloat(e.target.value);
    debounceRockRebuild();
});

document.getElementById('rock-size-var')?.addEventListener('input', (e) => {
    CONFIG.rocks.sizeVar = parseFloat(e.target.value);
    debounceRockRebuild();
});

document.getElementById('rock-boulder-ratio')?.addEventListener('input', (e) => {
    CONFIG.rocks.boulderRatio = parseFloat(e.target.value);
    debounceRockRebuild();
});

document.getElementById('rock-shape')?.addEventListener('input', (e) => {
    CONFIG.rocks.shape = parseFloat(e.target.value);
    debounceRockRebuild(); // Форма меняет тип геометрии (Icosahedron detail)
});
document.getElementById('card-size')?.addEventListener('input', (e) => {
    CONFIG.cards.size = parseFloat(e.target.value);
    updateAllCards();
});

document.getElementById('card-height')?.addEventListener('input', (e) => {
    CONFIG.cards.heightOffset = parseFloat(e.target.value);
    if (CONFIG.ui.groundMode) updateAllCards(); // Применяется только на земле
});

document.getElementById('card-spacing')?.addEventListener('input', (e) => {
    CONFIG.cards.spacing = parseFloat(e.target.value);
    updateAllCards();
});
// Настройки, которые применяются МГНОВЕННО (через Uniforms), без пересоздания:
document.getElementById('rock-smooth')?.addEventListener('input', (e) => {
    CONFIG.rocks.smoothness = parseFloat(e.target.value);
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uSmoothness.value = CONFIG.rocks.smoothness;
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uSmoothness.value = CONFIG.rocks.smoothness;
});
document.getElementById('rock-min-h')?.addEventListener('input', (e) => {
    CONFIG.rocks.minHeight = parseFloat(e.target.value);
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uMinHeight.value = CONFIG.rocks.minHeight;
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uMinHeight.value = CONFIG.rocks.minHeight;
});

document.getElementById('rock-max-h')?.addEventListener('input', (e) => {
    CONFIG.rocks.maxHeight = parseFloat(e.target.value);
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uMaxHeight.value = CONFIG.rocks.maxHeight;
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uMaxHeight.value = CONFIG.rocks.maxHeight;
});

document.getElementById('rock-foam-opacity')?.addEventListener('input', (e) => {
    CONFIG.rocks.rockFoamOpacity = parseFloat(e.target.value);
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uRockFoamOpacity.value = CONFIG.rocks.rockFoamOpacity;
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uRockFoamOpacity.value = CONFIG.rocks.rockFoamOpacity;
});

document.getElementById('rock-foam-height')?.addEventListener('input', (e) => {
    CONFIG.rocks.rockFoamHeight = parseFloat(e.target.value);
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uRockFoamHeight.value = CONFIG.rocks.rockFoamHeight;
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uRockFoamHeight.value = CONFIG.rocks.rockFoamHeight;
});

document.getElementById('reflect-stretch')?.addEventListener('input', (e) => {
    CONFIG.water.rippleStretch = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uReflectStretch.value = CONFIG.water.rippleStretch;
});
document.getElementById('reflect-blur')?.addEventListener('input', (e) => {
    CONFIG.water.blurStrength = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uReflectBlur.value = CONFIG.water.blurStrength;
});
document.getElementById('reflect-edge-dark')?.addEventListener('input', (e) => {
    CONFIG.water.edgeDarkening = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uReflectEdgeDark.value = CONFIG.water.edgeDarkening;
});
document.getElementById('reflect-dist-start')?.addEventListener('input', (e) => {
    CONFIG.water.distBlurStart = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uReflectDistStart.value = CONFIG.water.distBlurStart;
});
document.getElementById('reflect-dist-blur')?.addEventListener('input', (e) => {
    CONFIG.water.distBlurMax = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uReflectDistMax.value = CONFIG.water.distBlurMax;
});

document.getElementById('light-radius').addEventListener('input', (e) => {
    CONFIG.flashlight.radius = parseFloat(e.target.value);
});
document.getElementById('light-anim-amp').addEventListener('input', (e) => {
    CONFIG.flashlight.animAmp = parseFloat(e.target.value);
});
document.getElementById('light-anim-speed').addEventListener('input', (e) => {
    CONFIG.flashlight.animSpeed = parseFloat(e.target.value);
});

// --- СЛУШАТЕЛИ ДЛЯ КАСТОМНОГО ДАЛЬНЕГО ФОНА ---
const grassFarMixMode = document.getElementById('grass-far-mix-mode');
const grassFarMixExtras = document.getElementById('grass-far-mix-extras');

if (grassFarMixMode) {
    grassFarMixMode.addEventListener('change', (e) => {
        CONFIG.grass.farMixMode = parseFloat(e.target.value);
        
        if (grassFarMixExtras) {
            grassFarMixExtras.style.display = CONFIG.grass.farMixMode > 0 ? 'block' : 'none';
            
            const shape3Box = document.getElementById('far-shape-3-box');
            if (shape3Box) {
                shape3Box.style.display = CONFIG.grass.farMixMode >= 2 ? 'block' : 'none';
            }
        }
        
        if (grassSystem.materialFar) grassSystem.materialFar.uniforms.uFarMixMode.value = CONFIG.grass.farMixMode;
    });
}

document.getElementById('grass-mouse-toggle')?.addEventListener('change', (e) => {
    CONFIG.grass.mouseInteract = e.target.checked;
});

document.getElementById('grass-mouse-radius')?.addEventListener('input', (e) => {
    CONFIG.grass.mouseRadius = parseFloat(e.target.value);
});

document.getElementById('grass-mouse-strength')?.addEventListener('input', (e) => {
    CONFIG.grass.mouseStrength = parseFloat(e.target.value);
});

document.getElementById('grass-far-shape-1')?.addEventListener('change', (e) => {
    CONFIG.grass.farShape1 = parseFloat(e.target.value);
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uFarShape1.value = CONFIG.grass.farShape1;
});
document.getElementById('grass-far-shape-2')?.addEventListener('change', (e) => {
    CONFIG.grass.farShape2 = parseFloat(e.target.value);
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uFarShape2.value = CONFIG.grass.farShape2;
});
document.getElementById('grass-far-shape-3')?.addEventListener('change', (e) => {
    CONFIG.grass.farShape3 = parseFloat(e.target.value);
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uFarShape3.value = CONFIG.grass.farShape3;
});
document.getElementById('grass-far-alt-chance')?.addEventListener('input', (e) => {
    CONFIG.grass.farAltChance = parseFloat(e.target.value);
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uFarAltChance.value = CONFIG.grass.farAltChance;
});
document.getElementById('grass-far-struct')?.addEventListener('input', (e) => {
    CONFIG.grass.farStruct = parseFloat(e.target.value);
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uFarStruct.value = CONFIG.grass.farStruct;
});
document.getElementById('sphere-move-speed')?.addEventListener('input', (e) => {
    CONFIG.spheres.moveSpeed = parseFloat(e.target.value);
});

document.getElementById('rock-float-amp')?.addEventListener('input', (e) => {
    CONFIG.rocks.floatAmp = parseFloat(e.target.value);
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uRockFloatAmp.value = CONFIG.rocks.floatAmp;
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uRockFloatAmp.value = CONFIG.rocks.floatAmp;
});

document.getElementById('rock-float-speed')?.addEventListener('input', (e) => {
    CONFIG.rocks.floatSpeed = parseFloat(e.target.value);
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uRockFloatSpeed.value = CONFIG.rocks.floatSpeed;
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uRockFloatSpeed.value = CONFIG.rocks.floatSpeed;
});

document.getElementById('rock-moss-spread')?.addEventListener('input', (e) => {
    CONFIG.rocks.mossSpread = parseFloat(e.target.value);
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uMossSpread.value = CONFIG.rocks.mossSpread;
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uMossSpread.value = CONFIG.rocks.mossSpread;
});
document.getElementById('sphere-light-grass-toggle')?.addEventListener('change', (e) => {
    CONFIG.sphereLights.affectGrass = e.target.checked;
});

document.getElementById('comet-light-grass-toggle')?.addEventListener('change', (e) => {
    CONFIG.cometLights.affectGrass = e.target.checked;
});
document.getElementById('rock-crystal-ratio-small')?.addEventListener('input', (e) => {
    CONFIG.rocks.crystalRatioSmall = parseFloat(e.target.value);
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uCrystalRatio.value = CONFIG.rocks.crystalRatioSmall;
});

document.getElementById('rock-crystal-ratio-boulder')?.addEventListener('input', (e) => {
    CONFIG.rocks.crystalRatioBoulder = parseFloat(e.target.value);
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uCrystalRatio.value = CONFIG.rocks.crystalRatioBoulder;
});

// --- Слушатели для конкретных форм травы ---
document.getElementById('grass-shape-1').addEventListener('change', (e) => {
    CONFIG.grass.shape1 = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uShape1.value = CONFIG.grass.shape1;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uShape1.value = CONFIG.grass.shape1;
});

// --- СЛУШАТЕЛИ УНИКАЛЬНЫХ НАСТРОЕК ДЛЯ КАЖДОЙ ФОРМЫ ---
for (let i = 1; i <= 4; i++) {
    const comp = i === 1 ? 'x' : i === 2 ? 'y' : i === 3 ? 'z' : 'w';
    
    document.getElementById(`s${i}-size`)?.addEventListener('input', (e) => {
        CONFIG.grass.shapeMods.size[comp] = parseFloat(e.target.value);
        // ИСПРАВЛЕНИЕ: Никакого Rebuild! Просто передаем новое число в шейдер
        if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uShapeSizes.value[comp] = CONFIG.grass.shapeMods.size[comp];
        if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uShapeSizes.value[comp] = CONFIG.grass.shapeMods.size[comp];
    });

    document.getElementById(`s${i}-winddamp`)?.addEventListener('input', (e) => {
        CONFIG.grass.shapeMods.windDamp[comp] = parseFloat(e.target.value);
        if(grassSystem.meshNear) grassSystem.meshNear.material.uniforms.uShapeWindDamp.value[comp] = CONFIG.grass.shapeMods.windDamp[comp];
        if(grassSystem.meshFar) grassSystem.meshFar.material.uniforms.uShapeWindDamp.value[comp] = CONFIG.grass.shapeMods.windDamp[comp];
    });
    
    document.getElementById(`s${i}-width`)?.addEventListener('input', (e) => {
        CONFIG.grass.shapeMods.width[comp] = parseFloat(e.target.value);
        // ИСПРАВЛЕНИЕ: Никакого Rebuild!
        if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uShapeWidths.value[comp] = CONFIG.grass.shapeMods.width[comp];
        if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uShapeWidths.value[comp] = CONFIG.grass.shapeMods.width[comp];
    });
    
    document.getElementById(`s${i}-sizevar`)?.addEventListener('input', (e) => {
        CONFIG.grass.shapeMods.sizeVar[comp] = parseFloat(e.target.value);
        if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uShapeSizeVars.value[comp] = CONFIG.grass.shapeMods.sizeVar[comp];
        if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uShapeSizeVars.value[comp] = CONFIG.grass.shapeMods.sizeVar[comp];
    });
    
    document.getElementById(`s${i}-colvar`)?.addEventListener('input', (e) => {
        CONFIG.grass.shapeMods.colorVar[comp] = parseFloat(e.target.value);
        if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uShapeColorVars.value[comp] = CONFIG.grass.shapeMods.colorVar[comp];
        if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uShapeColorVars.value[comp] = CONFIG.grass.shapeMods.colorVar[comp];
    });
}

document.getElementById('grass-shape-2').addEventListener('change', (e) => {
    CONFIG.grass.shape2 = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uShape2.value = CONFIG.grass.shape2;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uShape2.value = CONFIG.grass.shape2;
});
// --- РЯДОМ С ДРУГИМИ СЛУШАТЕЛЯМИ ДАЛЬНЕГО ПЛАНА (LOD) ---
document.getElementById('far-s2-winddamp')?.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    CONFIG.grass.farShapeMods.windDamp.y = val;
    if (grassSystem.materialFar) {
        grassSystem.materialFar.uniforms.uShapeWindDamp.value.y = val;
    }
});

document.getElementById('far-s3-winddamp')?.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    CONFIG.grass.farShapeMods.windDamp.z = val;
    if (grassSystem.materialFar) {
        grassSystem.materialFar.uniforms.uShapeWindDamp.value.z = val;
    }
});
document.getElementById('grass-shape-3').addEventListener('change', (e) => {
    CONFIG.grass.shape3 = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uShape3.value = CONFIG.grass.shape3;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uShape3.value = CONFIG.grass.shape3;
});

// --- НОВЫЕ СЛУШАТЕЛИ РАЗДЕЛЬНЫХ ОСТРОВКОВ ---
['s2', 's3', 's4'].forEach((prefix, i) => {
    document.getElementById(`${prefix}-chance`)?.addEventListener('input', (e) => {
        CONFIG.grass[`altChance${i+2}`] = parseFloat(e.target.value);
    });
    document.getElementById(`${prefix}-struct`)?.addEventListener('input', (e) => {
        CONFIG.grass[`struct${i+2}`] = parseFloat(e.target.value);
    });
});

['far-s2', 'far-s3'].forEach((prefix, i) => {
    document.getElementById(`${prefix}-chance`)?.addEventListener('input', (e) => {
        CONFIG.grass[`farAltChance${i+2}`] = parseFloat(e.target.value);
    });
    document.getElementById(`${prefix}-struct`)?.addEventListener('input', (e) => {
        CONFIG.grass[`farStruct${i+2}`] = parseFloat(e.target.value);
    });
});
// Слушатели для вариативности травы
document.getElementById('grass-color-var').addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    CONFIG.grass.colorVar = val;
    
    // БЕЗОПАСНОЕ ПРИСВОЕНИЕ: работает и с THREE.Vector4, и с обычными объектами после JSON-импорта
    CONFIG.grass.shapeMods.colorVar.x = val;
    CONFIG.grass.shapeMods.colorVar.y = val;
    CONFIG.grass.shapeMods.colorVar.z = val;
    CONFIG.grass.shapeMods.colorVar.w = val;
    
    // Обновление униформов шейдера (внутри Three.js это всегда 100% Vector4, поэтому .set() безопасен)
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uShapeColorVars.value.set(val, val, val, val);
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uShapeColorVars.value.set(val, val, val, val);
});

// --- СЛУШАТЕЛИ ОБЛАКОВ (НЕБО) ---
document.getElementById('clouds-toggle')?.addEventListener('change', e => { CONFIG.clouds.enabled = e.target.checked; sharedCloudUniforms.uCloudsEnabled.value = e.target.checked ? 1.0 : 0.0; });
document.getElementById('clouds-opacity')?.addEventListener('input', e => { CONFIG.clouds.opacity = parseFloat(e.target.value); sharedCloudUniforms.uCloudOpacity.value = CONFIG.clouds.opacity; });
document.getElementById('clouds-coverage')?.addEventListener('input', e => { CONFIG.clouds.coverage = parseFloat(e.target.value); sharedCloudUniforms.uCloudCoverage.value = CONFIG.clouds.coverage; });
document.getElementById('clouds-softness')?.addEventListener('input', e => { CONFIG.clouds.softness = parseFloat(e.target.value); sharedCloudUniforms.uCloudSoftness.value = CONFIG.clouds.softness; });
document.getElementById('clouds-scale')?.addEventListener('input', e => { CONFIG.clouds.scale = parseFloat(e.target.value); sharedCloudUniforms.uCloudScale.value = CONFIG.clouds.scale; });
document.getElementById('clouds-stretch')?.addEventListener('input', e => { CONFIG.clouds.stretch = parseFloat(e.target.value); sharedCloudUniforms.uCloudStretch.value = CONFIG.clouds.stretch; });
document.getElementById('clouds-speed')?.addEventListener('input', e => { CONFIG.clouds.speed = parseFloat(e.target.value); sharedCloudUniforms.uCloudSpeed.value = CONFIG.clouds.speed; });

// --- СЛУШАТЕЛИ ТЕНЕЙ (ЗЕМЛЯ) ---
document.getElementById('shadows-toggle')?.addEventListener('change', e => { CONFIG.cloudShadows.enabled = e.target.checked; sharedCloudUniforms.uShadowsEnabled.value = e.target.checked ? 1.0 : 0.0; });
document.getElementById('shadow-opacity')?.addEventListener('input', e => { CONFIG.cloudShadows.opacity = parseFloat(e.target.value); sharedCloudUniforms.uShadowOpacity.value = CONFIG.cloudShadows.opacity; });
document.getElementById('shadow-coverage')?.addEventListener('input', e => { CONFIG.cloudShadows.coverage = parseFloat(e.target.value); sharedCloudUniforms.uShadowCoverage.value = CONFIG.cloudShadows.coverage; });
document.getElementById('shadow-softness')?.addEventListener('input', e => { CONFIG.cloudShadows.softness = parseFloat(e.target.value); sharedCloudUniforms.uShadowSoftness.value = CONFIG.cloudShadows.softness; });
document.getElementById('shadow-scale')?.addEventListener('input', e => { CONFIG.cloudShadows.scale = parseFloat(e.target.value); sharedCloudUniforms.uShadowScale.value = CONFIG.cloudShadows.scale; });
document.getElementById('shadow-stretch')?.addEventListener('input', e => { CONFIG.cloudShadows.stretch = parseFloat(e.target.value); sharedCloudUniforms.uShadowStretch.value = CONFIG.cloudShadows.stretch; });
document.getElementById('shadow-speed')?.addEventListener('input', e => { CONFIG.cloudShadows.speed = parseFloat(e.target.value); sharedCloudUniforms.uShadowSpeed.value = CONFIG.cloudShadows.speed; });



document.getElementById('grass-size-var').addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    CONFIG.grass.sizeVar = val;
    
    // Применяем глобальное разнообразие ко ВСЕМ формам сразу (как с цветом)
    CONFIG.grass.shapeMods.sizeVar.x = val;
    CONFIG.grass.shapeMods.sizeVar.y = val;
    CONFIG.grass.shapeMods.sizeVar.z = val;
    CONFIG.grass.shapeMods.sizeVar.w = val;
    
    // Обновляем шейдеры
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uShapeSizeVars.value.set(val, val, val, val);
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uShapeSizeVars.value.set(val, val, val, val);
});

document.getElementById('grass-shape-var').addEventListener('input', (e) => {
    CONFIG.grass.shapeVar = parseFloat(e.target.value);
    // Обновляем новую переменную uShapeVar в шейдере
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uShapeVar.value = CONFIG.grass.shapeVar;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uShapeVar.value = CONFIG.grass.shapeVar;
});

// Таймер для предотвращения зависания при перетаскивании ползунка
let grassRebuildTimeout;
function debounceGrassRebuild() {
    clearTimeout(grassRebuildTimeout);
    grassRebuildTimeout = setTimeout(() => {
        grassSystem.build(); // Полностью пересоздает траву с новыми параметрами
    }, 250); // Ждем 250мс после того, как ползунок остановился
}

// Плотность (Количество)
document.getElementById('grass-count')?.addEventListener('input', (e) => {
    CONFIG.grass.count = parseInt(e.target.value);
    debounceGrassRebuild();
});

// Дальность отрисовки (Главная)
document.getElementById('grass-distance')?.addEventListener('input', (e) => {
    CONFIG.grass.drawDistance = parseFloat(e.target.value);
    // Обновляем юниформ сразу для плавности
    if (grassSystem.materialNear) grassSystem.materialNear.uniforms.uDrawDistance.value = CONFIG.grass.drawDistance;
    // Но также нужно перестроить зону посадки
    debounceGrassRebuild();
});

// Включить/Выключить LOD
document.getElementById('grass-lod-toggle')?.addEventListener('change', (e) => {
    CONFIG.grass.lodEnabled = e.target.checked;
    grassSystem.updateVisibility(); // Это легкая операция, вызываем сразу
});

// Дальность фона (LOD)
document.getElementById('grass-far-dist')?.addEventListener('input', (e) => {
    CONFIG.grass.farDistance = parseFloat(e.target.value);
    if (grassSystem.materialFar) grassSystem.materialFar.uniforms.uDrawDistance.value = CONFIG.grass.farDistance;
    debounceGrassRebuild();
});

// Кол-во фоновой травы (LOD)
document.getElementById('grass-far-count')?.addEventListener('input', (e) => {
    CONFIG.grass.farCount = parseInt(e.target.value);
    debounceGrassRebuild();
});

document.getElementById('reflect-rocks-toggle')?.addEventListener('change', (e) => {
    CONFIG.water.reflectRocks = e.target.checked;
});
document.getElementById('reflect-clouds-toggle')?.addEventListener('change', (e) => {
    CONFIG.water.reflectClouds = e.target.checked;
});

// LOD Настройки (Дальняя трава)
document.getElementById('grass-far-size')?.addEventListener('input', (e) => {
    CONFIG.grass.farSizeMult = parseFloat(e.target.value);
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uSizeMult.value = CONFIG.grass.farSizeMult;
});

// Анимация ветра и турбулентности
document.getElementById('grass-turb-amp').addEventListener('input', (e) => {
    CONFIG.grass.turbAmp = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uGrassTurbAmp.value = CONFIG.grass.turbAmp;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uGrassTurbAmp.value = CONFIG.grass.turbAmp;
});

document.getElementById('grass-gust-freq').addEventListener('input', (e) => {
    CONFIG.grass.gustFreq = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uGrassGustFreq.value = CONFIG.grass.gustFreq;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uGrassGustFreq.value = CONFIG.grass.gustFreq;
});
document.getElementById('grass-turb-speed').addEventListener('input', (e) => {
    CONFIG.grass.turbSpeed = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uGrassTurbSpeed.value = CONFIG.grass.turbSpeed;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uGrassTurbSpeed.value = CONFIG.grass.turbSpeed;
});
document.getElementById('grass-gust-size').addEventListener('input', (e) => {
    CONFIG.grass.gustSize = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uGrassGustSize.value = CONFIG.grass.gustSize;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uGrassGustSize.value = CONFIG.grass.gustSize;
});
document.getElementById('grass-gust-arc').addEventListener('input', (e) => {
    CONFIG.grass.gustArc = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uGrassGustArc.value = CONFIG.grass.gustArc;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uGrassGustArc.value = CONFIG.grass.gustArc;
});
document.getElementById('grass-wind-chaos').addEventListener('input', (e) => {
    CONFIG.grass.windChaos = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uGrassWindChaos.value = CONFIG.grass.windChaos;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uGrassWindChaos.value = CONFIG.grass.windChaos;
});
document.getElementById('grass-wind-speed').addEventListener('input', (e) => {
    CONFIG.grass.windSpeed = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uGrassWindSpeed.value = CONFIG.grass.windSpeed;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uGrassWindSpeed.value = CONFIG.grass.windSpeed;
});
document.getElementById('grass-sway').addEventListener('input', (e) => {
    CONFIG.grass.swayStrength = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uGrassSwayStrength.value = CONFIG.grass.swayStrength;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uGrassSwayStrength.value = CONFIG.grass.swayStrength;
});
document.getElementById('grass-gust-str').addEventListener('input', (e) => {
    CONFIG.grass.gustStrength = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uGrassGustStrength.value = CONFIG.grass.gustStrength;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uGrassGustStrength.value = CONFIG.grass.gustStrength;
});


// --- НОВЫЕ СЛУШАТЕЛИ ДЛЯ ГРАНЕЙ И КРИСТАЛЛОВ ---
document.getElementById('rock-flat')?.addEventListener('input', (e) => {
    CONFIG.rocks.flatShading = parseFloat(e.target.value);
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uFlatShading.value = CONFIG.rocks.flatShading;
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uFlatShading.value = CONFIG.rocks.flatShading;
});
document.getElementById('rock-ao')?.addEventListener('input', (e) => {
    CONFIG.rocks.ao = parseFloat(e.target.value);
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uRockAO.value = CONFIG.rocks.ao;
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uRockAO.value = CONFIG.rocks.ao;
});
document.getElementById('rock-crystal-gloss')?.addEventListener('input', (e) => {
    CONFIG.rocks.crystalGloss = parseFloat(e.target.value);
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uCrystalGloss.value = CONFIG.rocks.crystalGloss;
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uCrystalGloss.value = CONFIG.rocks.crystalGloss;
});
document.getElementById('grass-gust-speed').addEventListener('input', (e) => {
    CONFIG.grass.gustSpeed = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uGrassGustSpeed.value = CONFIG.grass.gustSpeed;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uGrassGustSpeed.value = CONFIG.grass.gustSpeed;
});

// Свет от сфер
// ДОБАВЛЕНО ДЛЯ КАМНЕЙ
document.getElementById('light-rock-toggle').addEventListener('change', (e) => {
    CONFIG.flashlight.affectRocks = e.target.checked;
    const val = (CONFIG.flashlight.enabled && CONFIG.flashlight.affectRocks) ? 1.0 : 0.0;
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uLightEnable.value = val;
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uLightEnable.value = val;
});

document.getElementById('rock-crystal-alpha')?.addEventListener('input', (e) => {
    CONFIG.rocks.crystalAlpha = parseFloat(e.target.value);
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uCrystalAlpha.value = CONFIG.rocks.crystalAlpha;
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uCrystalAlpha.value = CONFIG.rocks.crystalAlpha;
});

// Дальность прорисовки (требует ребилда позиций)
document.getElementById('rock-dist')?.addEventListener('input', (e) => {
    CONFIG.rocks.drawDistance = parseFloat(e.target.value);
    debounceRockRebuild();
});

// Средняя высота (требует ребилда геометрии)
document.getElementById('rock-height-bias')?.addEventListener('input', (e) => {
    CONFIG.rocks.heightBias = parseFloat(e.target.value);
    debounceRockRebuild();
});

// Настройки фейковых отблесков (МГНОВЕННЫЕ через uniform)
document.getElementById('rock-iris-int')?.addEventListener('input', (e) => {
    CONFIG.rocks.crystalIrisIntensity = parseFloat(e.target.value);
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uCrystalIrisIntensity.value = CONFIG.rocks.crystalIrisIntensity;
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uCrystalIrisIntensity.value = CONFIG.rocks.crystalIrisIntensity;
});

document.getElementById('rock-iris-spread')?.addEventListener('input', (e) => {
    CONFIG.rocks.crystalIrisSpread = parseFloat(e.target.value);
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uCrystalIrisSpread.value = CONFIG.rocks.crystalIrisSpread;
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uCrystalIrisSpread.value = CONFIG.rocks.crystalIrisSpread;
});

// --- ОБНОВЛЕННЫЙ БЛОК СФЕР ---
// --- ОБНОВЛЕННЫЙ БЛОК СФЕР ---
document.getElementById('sphere-light-toggle').addEventListener('change', (e) => {
    CONFIG.sphereLights.enabled = e.target.checked;
});

document.getElementById('sphere-light-rock-toggle').addEventListener('change', (e) => {
    CONFIG.sphereLights.affectRocks = e.target.checked;
});

document.getElementById('sphere-light-intensity').addEventListener('input', (e) => {
    CONFIG.sphereLights.intensity = parseFloat(e.target.value);
});

document.getElementById('sphere-light-range').addEventListener('input', (e) => {
    CONFIG.sphereLights.range = parseFloat(e.target.value);
});

// Островки и прореживание
document.getElementById('rock-struct')?.addEventListener('input', (e) => {
    CONFIG.rocks.struct = parseFloat(e.target.value);
    // Обновляем напрямую в шейдере без ребилда
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uRockStruct.value = CONFIG.rocks.struct;
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uRockStruct.value = CONFIG.rocks.struct;
});

document.getElementById('rock-thin')?.addEventListener('input', (e) => {
    CONFIG.rocks.thin = parseFloat(e.target.value);
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uRockThin.value = CONFIG.rocks.thin;
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uRockThin.value = CONFIG.rocks.thin;
});

// Формы (требуют ребилда, так как меняется геометрия меша)
document.getElementById('rock-shape-small')?.addEventListener('input', (e) => {
    CONFIG.rocks.shapeSmall = parseFloat(e.target.value);
    debounceRockRebuild(); 
});

document.getElementById('rock-shape-boulder')?.addEventListener('input', (e) => {
    CONFIG.rocks.shapeBoulder = parseFloat(e.target.value);
    debounceRockRebuild(); 
});

// Форма 2 дальнего плана (LOD 2)
document.getElementById('far-s2-size')?.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    CONFIG.grass.farShapeMods.size.y = val;
    if (grassSystem.materialFar) {
        grassSystem.materialFar.uniforms.uShapeSizes.value.y = val;
    }
});

document.getElementById('far-s2-width')?.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    CONFIG.grass.farShapeMods.width.y = val;
    if (grassSystem.materialFar) {
        grassSystem.materialFar.uniforms.uShapeWidths.value.y = val;
    }
});

// Форма 3 дальнего плана (LOD 3)
document.getElementById('far-s3-size')?.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    CONFIG.grass.farShapeMods.size.z = val;
    if (grassSystem.materialFar) {
        grassSystem.materialFar.uniforms.uShapeSizes.value.z = val;
    }
});

document.getElementById('far-s3-width')?.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    CONFIG.grass.farShapeMods.width.z = val;
    if (grassSystem.materialFar) {
        grassSystem.materialFar.uniforms.uShapeWidths.value.z = val;
    }
});

// Туман
document.getElementById('grass-fog-mult').addEventListener('input', (e) => {
    CONFIG.grass.fogDensityMult = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uFogMult.value = CONFIG.grass.fogDensityMult;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uFogMult.value = CONFIG.grass.fogDensityMult;
});
// --- НОВЫЕ СЛУШАТЕЛИ РАЗДЕЛЬНЫХ ОСТРОВКОВ И ПРОРЕЖИВАНИЯ ---
['s2', 's3', 's4'].forEach((prefix, i) => {
    document.getElementById(`${prefix}-chance`)?.addEventListener('input', (e) => {
        CONFIG.grass[`altChance${i+2}`] = parseFloat(e.target.value);
    });
    document.getElementById(`${prefix}-struct`)?.addEventListener('input', (e) => {
        CONFIG.grass[`struct${i+2}`] = parseFloat(e.target.value);
    });
    // ДОБАВЛЕННЫЙ СЛУШАТЕЛЬ ПРОРЕЖИВАНИЯ
    document.getElementById(`${prefix}-thin`)?.addEventListener('input', (e) => {
        CONFIG.grass[`thin${i+2}`] = parseFloat(e.target.value);
    });
});

['far-s2', 'far-s3'].forEach((prefix, i) => {
    document.getElementById(`${prefix}-chance`)?.addEventListener('input', (e) => {
        CONFIG.grass[`farAltChance${i+2}`] = parseFloat(e.target.value);
    });
    document.getElementById(`${prefix}-struct`)?.addEventListener('input', (e) => {
        CONFIG.grass[`farStruct${i+2}`] = parseFloat(e.target.value);
    });
    // ДОБАВЛЕННЫЙ СЛУШАТЕЛЬ ПРОРЕЖИВАНИЯ ДЛЯ ФОНА
    document.getElementById(`${prefix}-thin`)?.addEventListener('input', (e) => {
        CONFIG.grass[`farThin${i+2}`] = parseFloat(e.target.value);
    });
});
// Изгиб
document.getElementById('grass-bend').addEventListener('input', (e) => {
    CONFIG.grass.bend = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uBend.value = CONFIG.grass.bend;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uBend.value = CONFIG.grass.bend;
});
document.getElementById('grass-bend-angle').addEventListener('input', (e) => {
    CONFIG.grass.bendAngle = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uBendAngle.value = CONFIG.grass.bendAngle;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uBendAngle.value = CONFIG.grass.bendAngle;
});
document.getElementById('grass-bend-chaos').addEventListener('input', (e) => {
    CONFIG.grass.bendChaos = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uBendChaos.value = CONFIG.grass.bendChaos;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uBendChaos.value = CONFIG.grass.bendChaos;
});

document.getElementById('foam-opacity')?.addEventListener('input', (e) => {
    CONFIG.water.foamOpacity = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uFoamOpacity.value = CONFIG.water.foamOpacity;
});

document.getElementById('shore-opacity')?.addEventListener('input', (e) => {
    CONFIG.water.shoreOpacity = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uShoreOpacity.value = CONFIG.water.shoreOpacity;
});
document.getElementById('foam-width')?.addEventListener('input', (e) => {
    CONFIG.water.foamWidth = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uFoamWidth.value = CONFIG.water.foamWidth;
});
document.getElementById('foam-count')?.addEventListener('input', (e) => {
    CONFIG.water.foamCount = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uFoamCount.value = CONFIG.water.foamCount;
});
document.getElementById('foam-noise')?.addEventListener('input', (e) => {
    CONFIG.water.foamNoise = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uFoamNoise.value = CONFIG.water.foamNoise;
});

document.getElementById('sphere-trail-length')?.addEventListener('input', (e) => {
    CONFIG.spheres.trailLength = parseFloat(e.target.value);
});

document.getElementById('sphere-trail-speed')?.addEventListener('input', (e) => {
    CONFIG.spheres.trailSpeed = parseFloat(e.target.value);
});

document.getElementById('sphere-trail-turb')?.addEventListener('input', (e) => {
    CONFIG.spheres.trailTurbulence = parseFloat(e.target.value);
});

// --- ОБРАБОТЧИКИ НАСТРОЕК ШЛЕЙФА СФЕР ---
document.getElementById('sphere-trail-count')?.addEventListener('input', (e) => {
    CONFIG.spheres.trailCount = parseInt(e.target.value);
    sphereSystem.refresh();
});

document.getElementById('sphere-trail-size')?.addEventListener('input', (e) => {
    CONFIG.spheres.trailSize = parseFloat(e.target.value);
    sphereSystem.refresh();
});

document.getElementById('sphere-trail-blur')?.addEventListener('input', (e) => {
    CONFIG.spheres.trailBlur = parseFloat(e.target.value);
    sphereSystem.refresh();
});

document.getElementById('sphere-trail-opacity')?.addEventListener('input', (e) => {
    CONFIG.spheres.trailOpacity = parseFloat(e.target.value);
    sphereSystem.refresh();
});
// Размеры и зоны роста
document.getElementById('grass-height').addEventListener('input', (e) => {
    CONFIG.grass.height = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uGrassHeight.value = CONFIG.grass.height;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uGrassHeight.value = CONFIG.grass.height;
});
document.getElementById('grass-smooth').addEventListener('input', (e) => {
    CONFIG.grass.smoothness = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uSmoothness.value = CONFIG.grass.smoothness;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uSmoothness.value = CONFIG.grass.smoothness;
});
document.getElementById('grass-cluster-thresh').addEventListener('input', (e) => {
    CONFIG.grass.clusterThreshold = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uClusterThreshold.value = CONFIG.grass.clusterThreshold;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uClusterThreshold.value = CONFIG.grass.clusterThreshold;
});
document.getElementById('grass-min-h').addEventListener('input', (e) => {
    CONFIG.grass.minHeight = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uMinHeight.value = CONFIG.grass.minHeight;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uMinHeight.value = CONFIG.grass.minHeight;
});
document.getElementById('grass-max-h').addEventListener('input', (e) => {
    CONFIG.grass.maxHeight = parseFloat(e.target.value);
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uMaxHeight.value = CONFIG.grass.maxHeight;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uMaxHeight.value = CONFIG.grass.maxHeight;
});
document.getElementById('foam-spacing')?.addEventListener('input', (e) => {
    CONFIG.water.foamSpacing = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uFoamSpacing.value = CONFIG.water.foamSpacing;
});
// Добавьте цвета в функцию setupColorPickers():

// Слушатели для ландшафта
document.getElementById('terr-smooth').addEventListener('input', (e) => {
    CONFIG.terrain.smoothing = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uSmoothing.value = CONFIG.terrain.smoothing;
});


// --- ГЛОБАЛЬНОЕ ОСВЕЩЕНИЕ ---
document.getElementById('global-light-intensity').addEventListener('input', (e) => {
    CONFIG.lighting.globalIntensity = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uGlobalLight.value = CONFIG.lighting.globalIntensity;
    if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uGlobalLight.value = CONFIG.lighting.globalIntensity;
    if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uGlobalLight.value = CONFIG.lighting.globalIntensity;
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uGlobalLight.value = CONFIG.lighting.globalIntensity;
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uGlobalLight.value = CONFIG.lighting.globalIntensity;
});

document.getElementById('global-max-lights').addEventListener('input', (e) => {
    CONFIG.lighting.maxPointLights = parseInt(e.target.value);
});

document.getElementById('global-light-dist').addEventListener('input', (e) => {
    CONFIG.lighting.lightDistance = parseFloat(e.target.value);
});


// --- СВЕТ КОМЕТ ---
document.getElementById('comet-light-toggle').addEventListener('change', (e) => {
    CONFIG.cometLights.enabled = e.target.checked;
});
document.getElementById('comet-light-rock-toggle').addEventListener('change', (e) => {
    CONFIG.cometLights.affectRocks = e.target.checked;
});
document.getElementById('comet-light-intensity').addEventListener('input', (e) => {
    CONFIG.cometLights.intensity = parseFloat(e.target.value);
});
document.getElementById('comet-light-range').addEventListener('input', (e) => {
    CONFIG.cometLights.range = parseFloat(e.target.value);
});

document.getElementById('rock-y-offset')?.addEventListener('input', (e) => {
    CONFIG.rocks.yOffset = parseFloat(e.target.value);
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uRockYOffset.value = CONFIG.rocks.yOffset;
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uRockYOffset.value = CONFIG.rocks.yOffset;
});

document.getElementById('rock-y-spread')?.addEventListener('input', (e) => {
    CONFIG.rocks.ySpread = parseFloat(e.target.value);
    if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uRockYSpread.value = CONFIG.rocks.ySpread;
    if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uRockYSpread.value = CONFIG.rocks.ySpread;
});

// --- ОБНОВЛЕННЫЙ БЛОК ПРОЖЕКТОРА ---
document.getElementById('light-toggle').addEventListener('change', (e) => {
    CONFIG.flashlight.enabled = e.target.checked;
});

document.getElementById('light-grass-toggle').addEventListener('change', (e) => {
    CONFIG.flashlight.affectGrass = e.target.checked;
});

document.getElementById('light-rock-toggle').addEventListener('change', (e) => {
    CONFIG.flashlight.affectRocks = e.target.checked;
});

document.getElementById('light-intensity').addEventListener('input', (e) => {
    CONFIG.flashlight.intensity = parseFloat(e.target.value);
});

document.getElementById('light-range').addEventListener('input', (e) => {
    CONFIG.flashlight.range = parseFloat(e.target.value);
});

document.getElementById('light-focus').addEventListener('input', (e) => {
    CONFIG.flashlight.focus = parseFloat(e.target.value);
});

document.getElementById('light-offset').addEventListener('input', (e) => {
    CONFIG.flashlight.offset = parseFloat(e.target.value);
});

document.getElementById('water-depth-factor')?.addEventListener('input', (e) => {
    CONFIG.terrain.waterDepthFactor = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uWaterDepthFactor.value = CONFIG.terrain.waterDepthFactor;
});

document.getElementById('terr-strata-toggle')?.addEventListener('change', (e) => {
    CONFIG.terrain.strataEnabled = e.target.checked;
    terrainSystem.material.uniforms.uStrataEnabled.value = e.target.checked ? 1.0 : 0.0;
});
document.getElementById('terr-strata-freq')?.addEventListener('input', (e) => {
    CONFIG.terrain.strataFreq = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uStrataFreq.value = CONFIG.terrain.strataFreq;
});
document.getElementById('terr-strata-str')?.addEventListener('input', (e) => {
    CONFIG.terrain.strataStrength = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uStrataStrength.value = CONFIG.terrain.strataStrength;
});

document.getElementById('grass-cam-toggle')?.addEventListener('change', (e) => {
    CONFIG.grass.cameraInteract = e.target.checked;
});
document.getElementById('grass-cam-radius')?.addEventListener('input', (e) => {
    CONFIG.grass.cameraRadius = parseFloat(e.target.value);
});

document.getElementById('grass-lod-offset')?.addEventListener('input', (e) => {
    CONFIG.grass.lodOffset = parseFloat(e.target.value);
    // Изменение смещения требует пересборки травы, чтобы заново рассчитать радиусы спавна
    if (typeof debounceGrassRebuild === 'function') debounceGrassRebuild();
});

document.getElementById('terr-amp').addEventListener('input', (e) => {
    CONFIG.terrain.amplitude = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uAmplitude.value = CONFIG.terrain.amplitude;
    updateCardsOnTerrainChange();
});
document.getElementById('terr-freq').addEventListener('input', (e) => {
    CONFIG.terrain.frequency = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uFrequency.value = CONFIG.terrain.frequency;
    updateCardsOnTerrainChange();
});
document.getElementById('terr-offset').addEventListener('input', (e) => {
    CONFIG.terrain.offset = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uOffset.value = CONFIG.terrain.offset;
    updateCardsOnTerrainChange();
});
document.getElementById('terr-sharp').addEventListener('input', (e) => {
    CONFIG.terrain.sharpness = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uSharpness.value = CONFIG.terrain.sharpness;
    updateCardsOnTerrainChange();
});
document.getElementById('terr-grid').addEventListener('change', (e) => {
    CONFIG.terrain.showGrid = e.target.checked;
    terrainSystem.material.uniforms.uShowGrid.value = e.target.checked ? 1.0 : 0.0;
});

// НОВЫЕ СЛУШАТЕЛИ ЛАНДШАФТА
document.getElementById('terr-ao').addEventListener('input', (e) => {
    CONFIG.terrain.aoStrength = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uAoStrength.value = CONFIG.terrain.aoStrength;
});
document.getElementById('terr-dist').addEventListener('input', (e) => {
    CONFIG.terrain.visibility = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uVisibility.value = CONFIG.terrain.visibility;
});
document.getElementById('terr-fog-dens').addEventListener('input', (e) => {
    CONFIG.terrain.fogDensity = parseFloat(e.target.value);
    terrainSystem.material.uniforms.uFogDensity.value = CONFIG.terrain.fogDensity;
    // Обновляем также глобальный туман сцены
    if (CONFIG.ui.groundMode) scene.fog.density = CONFIG.terrain.fogDensity;
});

// --- СЛУШАТЕЛИ СТЕЛЯЩЕГОСЯ ТУМАНА ---
document.getElementById('c-fog-toggle')?.addEventListener('change', (e) => {
    CONFIG.terrain.creepingFogEnabled = e.target.checked;
    creepingFogUniforms.uCFogEnabled.value = e.target.checked ? 1.0 : 0.0;
});
document.getElementById('c-fog-height')?.addEventListener('input', (e) => {
    CONFIG.terrain.creepingFogHeight = parseFloat(e.target.value);
    creepingFogUniforms.uCFogHeight.value = CONFIG.terrain.creepingFogHeight;
});
document.getElementById('c-fog-thick')?.addEventListener('input', (e) => {
    CONFIG.terrain.creepingFogThickness = parseFloat(e.target.value);
    creepingFogUniforms.uCFogThick.value = CONFIG.terrain.creepingFogThickness;
});
document.getElementById('c-fog-dens')?.addEventListener('input', (e) => {
    CONFIG.terrain.creepingFogDensity = parseFloat(e.target.value);
    creepingFogUniforms.uCFogDens.value = CONFIG.terrain.creepingFogDensity;
});
document.getElementById('c-fog-shape')?.addEventListener('input', (e) => {
    CONFIG.terrain.creepingFogShape = parseFloat(e.target.value);
    creepingFogUniforms.uCFogShape.value = CONFIG.terrain.creepingFogShape;
});




// Небо
document.getElementById('star-density').addEventListener('input', e => CONFIG.sky.starDensity = parseInt(e.target.value));
document.getElementById('star-size').addEventListener('input', e => CONFIG.sky.starSize = parseFloat(e.target.value));
document.getElementById('sky-blur').addEventListener('input', e => CONFIG.sky.blur = parseFloat(e.target.value));

// Кометы
document.getElementById('comet-freq').addEventListener('input', e => CONFIG.sky.cometFreq = parseFloat(e.target.value));
document.getElementById('slow-comet-freq').addEventListener('input', e => CONFIG.sky.slowCometFreq = parseFloat(e.target.value));


// Слушатели для сфер
document.getElementById('sphere-count').addEventListener('input', (e) => {
    CONFIG.spheres.count = parseInt(e.target.value);
    sphereSystem.refresh(); // Нужно обновить activeCount
});
document.getElementById('sphere-size').addEventListener('input', (e) => {
    CONFIG.spheres.baseSize = parseFloat(e.target.value);
    sphereSystem.refresh();
});

// Настройка видимости джойстиков
document.getElementById('ui-joystick-toggle').addEventListener('change', (e) => {
    const zones = document.querySelectorAll('.joystick-zone');
    zones.forEach(el => {
        if (e.target.checked) el.classList.add('visible');
        else el.classList.remove('visible');
    });
});

// Настройка размера джойстиков
document.getElementById('ui-joystick-size').addEventListener('input', (e) => {
    const size = e.target.value;
    const knobSize = size * 0.4; // Кноб всегда 40% от размера
    document.documentElement.style.setProperty('--joy-size', size + 'px');
    document.documentElement.style.setProperty('--joy-knob', knobSize + 'px');
});

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
// Слушатель для прокси-загрузки
const proxyToggle = document.getElementById('proxy-toggle');
if (proxyToggle) {
    proxyToggle.addEventListener('change', (e) => {
        CONFIG.network.useProxy = e.target.checked;
        console.log(`Proxy Mode: ${CONFIG.network.useProxy ? 'ON' : 'OFF'}`);
    });
}
// Слушатель для кнопки возврата домой
document.getElementById('home-btn').addEventListener('click', () => {
    // Сбрасываем цель камеры на стартовую позицию (0, 0, 1000)
    // или ту, которая установлена в state.targetPos при инициализации
    state.targetPos.set(0, 0, 1000);
    
    // Опционально: сбросить навигационную цель
    navigationTarget = null;
    updateNavigationHUD(); // Обновить интерфейс, чтобы убрать стрелку
});





document.getElementById('dev-copy-sky')?.addEventListener('click', (e) => {
    const bot = '#' + CONFIG.colors.bottom.getHexString();
    const mid = '#' + CONFIG.colors.mid.getHexString();
    const top = '#' + CONFIG.colors.top.getHexString();
    
    // Формируем строку пригодную для вставки в массив SKY_PALETTES
    const str = `{ bot: '${bot}', mid: '${mid}', top: '${top}' },`;
    
    navigator.clipboard.writeText(str).then(() => {
        const origText = e.target.innerText;
        e.target.innerText = 'СКОПИРОВАНО!';
        e.target.style.background = 'rgba(68, 255, 68, 0.2)';
        e.target.style.borderColor = '#44ff44';
        
        setTimeout(() => {
            e.target.innerText = origText;
            e.target.style.background = 'rgba(255, 255, 255, 0.1)';
            e.target.style.borderColor = 'rgba(255,255,255,0.3)';
        }, 1500);
    });
});

// =========================================================
// СИСТЕМА ГЕНЕРАЦИИ СЛУЧАЙНЫХ ПЛАНЕТ
// =========================================================

// Заготовленные палитры неба (можете пополнять)
const SKY_PALETTES = [
    { bot: '#6cc1d4', mid: '#284f6b', top: '#050814' }, // Земля (стандарт)
    { bot: '#a986c4', mid: '#36448f', top: '#01030a' }, // Марс / Пустыня
    { bot: '#901aeb', mid: '#85368f', top: '#f00d0d' }, // Токсичная
    { bot: '#1aebac', mid: '#36598f', top: '#f00d0d' }, // Магическая
    { bot: '#c7eb1a', mid: '#8f3678', top: '#00040f' }, // Закат
    { bot: '#c7eb1a', mid: '#36598f', top: '#00040f' },
    { bot: '#eb8b1a', mid: '#36598f', top: '#00040f' },
    { bot: '#ffffff', mid: '#ffffff', top: '#0047ff' },
    { bot: '#000000', mid: '#000000', top: '#ffabab' },
    { bot: '#631480', mid: '#3d7ad6', top: '#ffa3a3' },
    { bot: '#a8e0ff', mid: '#3d7ad6', top: '#8aaecf' },
    { bot: '#fff13b', mid: '#2bb048', top: '#6aabe8' },
    { bot: '#0024a6', mid: '#b02b2b', top: '#d6e86a' },
    { bot: '#1b2754', mid: '#1c2f69', top: '#8f96b8' },
    { bot: '#7a968e', mid: '#29324d', top: '#63898a' },
    { bot: '#87967a', mid: '#313b57', top: '#403b28' },
    { bot: '#967a7a', mid: '#333157', top: '#282f40' },
    { bot: '#ff00fc', mid: '#812bbd', top: '#282f40' },
    { bot: '#8fff00', mid: '#741bb3', top: '#1a3961' },
    { bot: '#ffd600', mid: '#cc5c00', top: '#ffffff' },
    { bot: '#ffffff', mid: '#cc5c00', top: '#3d0028' },
    { bot: '#ffffff', mid: '#b6cc00', top: '#00043d' },
    { bot: '#ffffff', mid: '#00cccc', top: '#000112' },
    { bot: '#ffffff', mid: '#8500cc', top: '#000112' },
    { bot: '#000000', mid: '#8500cc', top: '#ffffff' },
    { bot: '#000000', mid: '#008fcc', top: '#ffffff' },
    { bot: '#000000', mid: '#cc9900', top: '#ffffff' },
    { bot: '#e3ff00', mid: '#cc9900', top: '#000000' },
    { bot: '#00f0ff', mid: '#854646', top: '#232b99' }, // Мертвая луна
];

// Утилиты для рандома и умной работы с цветом
const R = {
    range: (min, max) => min + Math.random() * (max - min),
    int: (min, max) => Math.floor(min + Math.random() * (max - min + 1)),
    bool: (chance = 0.5) => Math.random() < chance,
    // Конвертация HSL в HEX для генерации идеальных палитр
    hslToHex: (h, s, l) => {
        const c = new THREE.Color();
        c.setHSL(h % 1.0, clamp(s, 0, 1), clamp(l, 0, 1));
        return '#' + c.getHexString();
    }
};

function clamp(val, min, max) { return Math.max(min, Math.min(max, val)); }

document.getElementById('btn-random-planet')?.addEventListener('click', () => {
    const level = parseInt(document.getElementById('random-level').value);
    const limitHeavy = document.getElementById('random-limit-heavy').checked;
    
    // Добавляем функцию скошенного рандома (сдвигает вероятность к минимальному значению)
    R.skewed = (min, max, power) => min + Math.pow(Math.random(), power) * (max - min);
    
    // 1. ВЫБИРАЕМ НЕБО КАК БАЗУ ДЛЯ ВСЕЙ ПЛАНЕТЫ
    const sky = SKY_PALETTES[R.int(0, SKY_PALETTES.length - 1)];
    const horizonColor = new THREE.Color(sky.bot);
    const horizonHSL = { h: 0, s: 0, l: 0 };
    horizonColor.getHSL(horizonHSL);

    // 2. ВЫБИРАЕМ ЦВЕТОВУЮ ГАРМОНИЮ
    let hueOffset = 0;
    if (level === 1) hueOffset = R.range(-0.1, 0.1); 
    else if (level === 2) hueOffset = R.bool(0.5) ? 0.5 : (0.5 + R.range(-0.15, 0.15)); 
    else if (level === 3) hueOffset = (R.bool(0.5) ? 0.33 : 0.66) + R.range(-0.05, 0.05);
    else {
        horizonHSL.h = R.range(0, 1);
        hueOffset = R.range(0, 1);
        horizonHSL.s = R.range(0.8, 1.0); 
    }

    const groundHue = (horizonHSL.h + hueOffset) % 1.0;

    // --- 1. ВОДА (Отвязка от земли) ---
    let waterHue = (groundHue + R.range(-0.1, 0.1)) % 1.0; // Ур 1: В тон земле
    if (level === 2) waterHue = (groundHue + R.range(-0.3, 0.3)) % 1.0; // Ур 2: Заметный сдвиг
    if (level >= 3)  waterHue = R.range(0, 1.0); // Ур 3-4: Любой цвет воды

    // --- 2. СТЕЛЯЩИЙСЯ ТУМАН (Отвязка от воды) ---
    let creepFogHue = waterHue; // Ур 1: Строго цвет воды (испарения)
    if (level === 2) creepFogHue = (waterHue + R.range(-0.15, 0.15)) % 1.0;
    if (level >= 3)  creepFogHue = R.range(0, 1.0);

    // --- 3. КРИСТАЛЛЫ И СВЕТЛЯЧКИ (Отвязка от комплементарности неба) ---
    let crystalHue = (horizonHSL.h + 0.5) % 1.0; // Ур 1: Строго противоположно небу
    if (level === 2) crystalHue = (horizonHSL.h + 0.5 + R.range(-0.2, 0.2)) % 1.0;
    if (level >= 3)  crystalHue = R.range(0, 1.0);

    // --- 4. КАМНИ И СКАЛЫ (Появление цвета) ---
    let rockHue = (groundHue + 0.5) % 1.0;
    let rockMaxSat = 0.1; // Ур 1: Почти серые (макс 10% насыщенности)
    if (level === 2) { rockHue = (groundHue + 0.5 + R.range(-0.2, 0.2)) % 1.0; rockMaxSat = 0.25; } // Легкий оттенок
    if (level === 3) { rockHue = R.range(0, 1.0); rockMaxSat = 0.6; } // Цветные скалы
    if (level === 4) { rockHue = R.range(0, 1.0); rockMaxSat = 1.0; } // Неоновые/вырвиглазные скалы

    // --- 5. ОБЛАКА (Отвязка от зенита и горизонта) ---
    const topColor = new THREE.Color(sky.top);
    const botColor = new THREE.Color(sky.bot);
    const topHSL = {}; topColor.getHSL(topHSL);
    const botHSL = {}; botColor.getHSL(botHSL);

    let cloudZenithHue = topHSL.h;
    let cloudHorizonHue = botHSL.h;
    let cloudSatMult = 1.0;

    if (level === 2) {
        cloudZenithHue = (topHSL.h + R.range(-0.1, 0.1)) % 1.0;
        cloudHorizonHue = (botHSL.h + R.range(-0.1, 0.1)) % 1.0;
    } else if (level === 3) {
        cloudZenithHue = (topHSL.h + R.range(-0.4, 0.4)) % 1.0;
        cloudHorizonHue = (botHSL.h + R.range(-0.4, 0.4)) % 1.0;
        cloudSatMult = 1.5; // Облака становятся более насыщенными
    } else if (level === 4) {
        cloudZenithHue = R.range(0, 1.0);
        cloudHorizonHue = R.range(0, 1.0);
    }
    const cloudZenithColor = R.hslToHex(cloudZenithHue, topHSL.s * cloudSatMult, Math.max(0.3, topHSL.l));
    const cloudHorizonColor = R.hslToHex(cloudHorizonHue, botHSL.s * cloudSatMult, Math.max(0.2, botHSL.l));

    // --- 6. ТРАВА И ФЛОРА (Уже обсуждали) ---
    let floraOffset = R.range(-0.05, 0.05); 
    let floraSpread = 0.1;                  
    if (level === 2) { floraOffset = R.range(-0.2, 0.2); floraSpread = 0.25; } 
    else if (level >= 3) { floraOffset = R.range(0.1, 0.9); floraSpread = R.range(0.3, 0.5); }

    // --- ГЕНЕРАТОРЫ ЦВЕТОВ (Учитывают новые переменные) ---
    const getGround = () => R.hslToHex(groundHue, horizonHSL.s * R.range(0.5, 0.9), R.range(0.05, 0.15));
    const getGrassTip = () => R.hslToHex(groundHue + floraOffset, horizonHSL.s * R.range(0.6, 1.0), R.range(0.3, 0.6));
    const getWater = () => R.hslToHex(waterHue, horizonHSL.s * R.range(0.5, 0.9), R.range(0.1, 0.3));
    const getDeepWater = () => {
        if (level === 4) return R.hslToHex(R.range(0, 1.0), R.range(0.2, 1.0), R.range(0.01, 0.15)); // В хаосе бездна может быть яркой
        return R.hslToHex(waterHue, horizonHSL.s * 0.4, 0.02);
    };
    const getCreepingFog = () => R.hslToHex(creepFogHue, horizonHSL.s * R.range(0.4, 0.8), R.range(0.1, 0.4));
    const getRockBase = () => R.hslToHex(rockHue, R.range(0.0, rockMaxSat), R.range(0.02, 0.1));
    const getRockTip = () => R.hslToHex(rockHue, R.range(0.05, rockMaxSat + 0.1), R.range(0.2, 0.4));
    const getCrystal = () => R.hslToHex(crystalHue, R.range(0.7, 1.0), R.range(0.4, 0.7));
    
    // УМНЫЙ ЦВЕТ ТУМАНА
    const getFog = () => {
        if (level === 1) return R.hslToHex(horizonHSL.h, horizonHSL.s * R.range(0.5, 0.8), R.range(0.1, 0.25));
        if (level === 2) return R.hslToHex(mixHue(horizonHSL.h, groundHue, 0.3), horizonHSL.s * R.range(0.3, 0.6), R.range(0.15, 0.3));
        if (level === 3) return R.hslToHex(mixHue(horizonHSL.h, groundHue, 0.5), horizonHSL.s * 0.4, R.range(0.2, 0.4));
        return R.hslToHex(R.range(0, 1.0), R.range(0.1, 0.9), R.range(0.1, 0.6)); // Ур 4: Абсолютно случайный туман
    };

    function mixHue(h1, h2, t) {
        let diff = h2 - h1;
        if (diff > 0.5) diff -= 1.0;
        else if (diff < -0.5) diff += 1.0;
        return (h1 + diff * t + 1.0) % 1.0;
    }

    const BIOMES = {
        earthy: [0, 1, 5, 7],     
        alien: [2, 4, 6],         
        harsh: [0, 1, 3],         
        forest: [1, 7, 8, 9]      
    };
    
    let activeBiome;
    if (level === 1) activeBiome = R.bool(0.7) ? BIOMES.earthy : BIOMES.forest;
    else if (level === 2) activeBiome = R.bool(0.5) ? BIOMES.alien : BIOMES.harsh;
    else if (level === 3) activeBiome = R.bool(0.3) ? BIOMES.forest : BIOMES.alien;
    else activeBiome = [0,1,2,3,4,5,6,7,8,9];

    const pickShape = () => activeBiome[R.int(0, activeBiome.length - 1)];
    const s1 = pickShape(); const s2 = pickShape(); const s3 = pickShape(); const s4 = pickShape();
    const fs1 = s1; const fs2 = pickShape(); const fs3 = pickShape();

    const getChance = (shape) => (shape >= 8) ? R.range(0.01, 0.08) : R.range(0.1, 0.6);

    const maxGrass = limitHeavy ? 150000 : 300000;
    const maxFarGrass = limitHeavy ? 50000 : 150000;
    const dev = level === 1 ? 0.1 : (level === 2 ? 0.3 : 0.6);

    const newConf = {
        colors: {
            bottom: sky.bot, mid: sky.mid, top: sky.top,
            firefly: getCrystal() 
        },
        terrain: {
            visibility: 7000.0,
            amplitude: level === 4 ? R.range(50, 400) : 205 + R.range(-100, 100) * dev,
            frequency: level === 4 ? R.range(0.0005, 0.003) : 0.0011 + R.range(-0.0005, 0.0005) * dev,
            offset: level === 4 ? R.range(0, 100) : 65 + R.range(-40, 40) * dev,
            sharpness: level === 4 ? R.range(0.5, 2.5) : 1.5 + R.range(-0.5, 0.5) * dev,
            grassColor: getGround(), 
            waterColor: getWater(),
            deepWaterColor: getDeepWater(),
            peakColor: getRockTip(), 
            fogColor: getFog(), 
            fogDensity: R.skewed(0.0005, 0.004, 3.5), 
            snowColor: level >= 3 ? R.hslToHex(waterHue, 0.5, 0.9) : '#ffffff', 
            creepingFogEnabled: level >= 2 ? R.bool(0.6) : false,
            creepingFogColor: getCreepingFog(), // <--- ИЗМЕНЕНО
            creepingFogHeight: R.range(0, 20),
            creepingFogThickness: R.range(10, 80),
            creepingFogDensity: R.range(0.5, 2.5)
        },
        water: {
            resolution: 512,
            reflections: level >= 2 ? R.bool(0.7) : false,
            intensity: level >= 2 ? R.range(0.2, 0.8) : 0.4,
            distortion: level >= 2 ? R.range(0.01, 0.08) : 0.035,
            foamOpacity: R.range(0, 0.5),
            foamColor: R.hslToHex(waterHue, 0.5, 0.8), // Пена в тон воде, но светлая
            shoreOpacity: R.range(0, 1.0)
        },
        clouds: {
            enabled: level >= 2 ? R.bool(0.6) : false,
            opacity: R.range(0.3, 0.95),
            coverage: R.range(0.2, 0.7),
            softness: R.range(0.2, 0.9),
            scale: R.range(0.0002, 0.0015),
            stretch: R.range(1.0, 5.0),
            speed: R.range(0.5, 5.0),
            colorZenith: cloudZenithColor,   // <--- ИЗМЕНЕНО
            colorHorizon: cloudHorizonColor  // <--- ИЗМЕНЕНО
        },
        cloudShadows: {
            enabled: level >= 2 ? R.bool(0.7) : false,
            opacity: R.range(0.2, 0.8),
            speed: R.range(0.5, 5.0)
        },
        grass: {
            drawDistance: 2000.0,
            farDistance: 6000.0,
            mouseInteract: false,
            count: R.int(30000, maxGrass),
            farCount: R.int(10000, maxFarGrass),
            lodEnabled: true,

            fogDensityMult: R.skewed(0.5, 3.5, 3.0), 
            
            mixMode: level === 1 ? 0 : (level === 2 ? R.int(0,1) : (level === 3 ? R.int(0,2) : R.int(0,3))),
            farMixMode: level <= 2 ? 0 : (level === 3 ? R.int(0,1) : R.int(0,2)),
            
            shape1: s1, shape2: s2, shape3: s3, shape4: s4,
            farShape1: fs1, farShape2: fs2, farShape3: fs3,
            altChance2: getChance(s2), altChance3: getChance(s3), altChance4: getChance(s4),
            farAltChance2: getChance(fs2), farAltChance3: getChance(fs3),
            
            // Цветовая вариация флоры (база земли + светлый кончик)
            baseColor: getGround(), tipColor: getGrassTip(),
            baseColor2: getGround(), tipColor2: R.hslToHex(groundHue + floraOffset + floraSpread, horizonHSL.s, R.range(0.4,0.7)), // <--- ИЗМЕНЕНО
            baseColor3: getGround(), tipColor3: R.hslToHex(groundHue + floraOffset - floraSpread, horizonHSL.s, R.range(0.4,0.7)), // <--- ИЗМЕНЕНО
            
            height: level === 4 ? R.range(2, 35) : 17 + R.range(-10, 10) * dev,
            bend: R.range(0.1, 0.8),
            windSpeed: R.range(0.5, 3.5),
            turbulence: R.range(0.0, 1.0)
        },
        rocks: {
            drawDistance: 6000.0,
            count: R.int(100, 800),
            size: level === 4 ? R.range(1, 15) : 4.0 + R.range(-2, 5) * dev,
            boulderRatio: R.range(0.0, 0.25),
            shapeSmall: R.range(0, 1), shapeBoulder: R.range(0, 1),
            baseColor: getRockBase(), 
            tipColor: getRockTip(), 
            mossColor: getGrassTip(), // Мох берет цвет основной травы!
            mossSpread: R.range(0, 0.8),
            crystalRatioSmall: level >= 2 ? R.range(0, 0.5) : 0,
            crystalRatioBoulder: level >= 2 ? R.range(0, 0.8) : 0,
            crystalBaseColor: getRockBase(), 
            crystalTipColor: getCrystal(), // Кристаллы светятся акцентным цветом
            floatAmp: level >= 3 ? R.range(0, 50) : 0,
            ySpread: level >= 3 ? R.range(0, 300) : 0
        },
        lighting: {
            lightDistance: 3500.0,
            maxPointLights: 20,
            globalIntensity: level === 4 ? R.range(0.5, 1.7) : 1.0
        },
        cometLights: { enabled: level >= 2 ? R.bool() : false, intensity: R.range(0.5, 4.0) },
        sphereLights: { enabled: level >= 3 ? R.bool() : false, intensity: R.range(0.5, 3.0) },
        flashlight: { enabled: level === 4 ? R.bool() : false, color: getCrystal(), intensity: R.range(1.0, 5.0), radius: R.range(0.05, 0.8) },
        spheres: {
            count: R.int(1, 15),
            colors: [getCrystal(), R.hslToHex(horizonHSL.h, 1.0, 0.8), '#ffffff'], // Сферы в тон атмосфере
            trailCount: level === 4 ? R.int(100, 1500) : 0
        },
        sky: {
            starDensity: R.int(5000, 40000), starSize: R.range(0.5, 2.0), cometFreq: R.range(0, 0.05)
        },
        details: { dustCount: R.int(500, 5000), fireflyCount: R.int(0, 1000) }
    };

    // Применяем новый пресет
    importConfigFromJSON(JSON.stringify(newConf));
});





// ВСТАВЬТЕ ЭТУ ФУНКЦИЮ ПЕРЕД ОБРАБОТЧИКОМ 'ground-mode-btn':
function applyGroundModeVisuals() {
    const btn = document.getElementById('ground-mode-btn');
    btn.style.background = CONFIG.ui.groundMode ? 'rgba(40, 180, 100, 0.3)' : '';
    btn.style.borderColor = CONFIG.ui.groundMode ? '#28b464' : '';

    skyDome.mesh.visible = CONFIG.ui.groundMode;
    terrainSystem.mesh.visible = CONFIG.ui.groundMode;
    grassSystem.updateVisibility();
    rockSystem.updateVisibility();

    if (CONFIG.ui.groundMode) {
        document.body.style.backgroundImage = 'none';
        document.body.style.backgroundColor = '#000000';
        
        scene.fog.density = CONFIG.terrain.fogDensity;
        scene.fog.color.copy(CONFIG.terrain.fogColor);
        
        state.chunks.forEach(chunk => {
            chunk.group.traverse(obj => {
                if (obj.isMesh && obj.userData.originalY === undefined && obj.material && obj.material.uniforms.uImageScale) {
                    obj.userData.originalY = obj.position.y;
                    const seedVal = cyrb128(obj.userData.postId || '1') % 100;
                    if (seedVal > 25) {
                        obj.visible = false;
                        obj.children.forEach(c => { if(c.isLine) c.visible = false; });
                    }
                    const worldPos = new THREE.Vector3();
                    obj.getWorldPosition(worldPos);
                    const tHeight = getTerrainHeight(worldPos.x, worldPos.z);
                    const baseScale = obj.scale.y; 
                    const absoluteNewY = tHeight + baseScale + 15.0 + (cyrb128(obj.userData.postId || '1') % 100) / 10.0;
                    obj.position.y = absoluteNewY - chunk.group.position.y;
                    
                    // Обновляем измененную матрицу
                    obj.updateMatrix();
                }
            });
        });
    } else {
        updateBackgroundGradient();
        scene.fog.density = 0.0015;
        scene.fog.color.copy(CONFIG.colors.bottom);
        
        state.chunks.forEach(chunk => {
            chunk.group.traverse(obj => {
                if (obj.isMesh && obj.userData.origScale !== undefined && obj.userData.originalY === undefined) {
                    // Запоминаем космическую высоту перед изменением
                    obj.userData.originalY = obj.position.y; 
                    const seedVal = cyrb128(obj.userData.postId || '1') % 100;
                    if (seedVal > 25) {
                        obj.visible = false;
                        obj.children.forEach(c => { if(c.isLine) c.visible = false; });
                    }
                }
            });
        });
        updateAllCards(); // Пересчитываем координаты под землю
    }
}


// И ЗАМЕНИТЕ ЕГО НА КОРОТКИЙ ВАРИАНТ:
document.getElementById('ground-mode-btn').addEventListener('click', (e) => {
    CONFIG.ui.groundMode = !CONFIG.ui.groundMode;
    // Изменяем высоту камеры только при РУЧНОМ клике (чтобы при загрузке пресета она не прыгала резко)
    if (CONFIG.ui.groundMode) {
        const startHeight = getTerrainHeight(state.targetPos.x, state.targetPos.z);
        state.targetPos.y = startHeight + 40.0; 
    }
    applyGroundModeVisuals();
});

// UI Settings Listeners
document.getElementById('ui-dist-toggle').addEventListener('change', (e) => {
    CONFIG.ui.showDistance = e.target.checked;
});
// ВСТАВИТЬ СЮДА:
document.getElementById('ui-max-cam-height')?.addEventListener('input', (e) => {
    CONFIG.ui.maxCamHeight = parseFloat(e.target.value);
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
        { id: 'sphere-col-1', target: CONFIG.spheres.colors[0], cb: () => sphereSystem.refresh() },
        { id: 'sphere-col-2', target: CONFIG.spheres.colors[1], cb: () => sphereSystem.refresh() },
        { id: 'sphere-col-3', target: CONFIG.spheres.colors[2], cb: () => sphereSystem.refresh() },        
        { id: 'col-fire', target: null, cb: (hex) => fireflyMat.uniforms.color.value.set(hex) },
        { id: 'col-constellation', target: CONFIG.constellation.color, cb: (hex) => {
            constellationTubeMat.color.set(hex);
            constellationDotMat.color.set(hex);
        }},
        { id: 'col-grass', target: CONFIG.terrain.grassColor, cb: () => {
            terrainSystem.material.uniforms.uColorGrass.value.copy(CONFIG.terrain.grassColor);
        }},
        { id: 'col-water', target: CONFIG.terrain.waterColor, cb: () => {
            terrainSystem.material.uniforms.uColorWater.value.copy(CONFIG.terrain.waterColor);
        }},
        { id: 'col-peak', target: CONFIG.terrain.peakColor, cb: () => {
            terrainSystem.material.uniforms.uColorPeak.value.copy(CONFIG.terrain.peakColor);
        }},
        // --- ДОБАВЛЕН ЦВЕТ СНЕГА (ПИКОВ) СЮДА ---
        { id: 'col-snow', target: CONFIG.terrain.snowColor, cb: () => {
            if(terrainSystem.material) terrainSystem.material.uniforms.uColorSnow.value.copy(CONFIG.terrain.snowColor);
        }},

        { id: 'col-shore', target: CONFIG.water.shoreColor, cb: () => {
            terrainSystem.material.uniforms.uShoreColor.value.copy(CONFIG.water.shoreColor);
        }},

        { id: 'col-crystal-base', target: CONFIG.rocks.crystalBaseColor, cb: () => {
            if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uCrystalBaseColor.value.copy(CONFIG.rocks.crystalBaseColor);
            if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uCrystalBaseColor.value.copy(CONFIG.rocks.crystalBaseColor);
        }},
        { id: 'col-crystal-tip', target: CONFIG.rocks.crystalTipColor, cb: () => {
            if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uCrystalTipColor.value.copy(CONFIG.rocks.crystalTipColor);
            if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uCrystalTipColor.value.copy(CONFIG.rocks.crystalTipColor);
        }},

        { id: 'col-cloud-zenith', target: CONFIG.clouds.colorZenith, cb: () => sharedCloudUniforms.uCloudColorZenith.value.copy(CONFIG.clouds.colorZenith) },
        { id: 'col-cloud-horizon', target: CONFIG.clouds.colorHorizon, cb: () => sharedCloudUniforms.uCloudColorHorizon.value.copy(CONFIG.clouds.colorHorizon) },
        { id: 'col-shadow', target: CONFIG.clouds.shadowColor, cb: () => sharedCloudUniforms.uShadowColor.value.copy(CONFIG.clouds.shadowColor) },

        { id: 'col-water-deep', target: CONFIG.terrain.deepWaterColor, cb: () => {
            terrainSystem.material.uniforms.uColorDeepWater.value.copy(CONFIG.terrain.deepWaterColor);
        }},

        { id: 'col-rock-moss', target: CONFIG.rocks.mossColor, cb: () => {
            if(rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uMossColor.value.copy(CONFIG.rocks.mossColor);
            if(rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uMossColor.value.copy(CONFIG.rocks.mossColor);
        }},



        { id: 'col-grass-base-2', target: CONFIG.grass.baseColor2, cb: () => {
            if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uBaseColor2.value.copy(CONFIG.grass.baseColor2);
            if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uBaseColor2.value.copy(CONFIG.grass.baseColor2);
        }},
        { id: 'col-grass-tip-2', target: CONFIG.grass.tipColor2, cb: () => {
            if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uTipColor2.value.copy(CONFIG.grass.tipColor2);
            if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uTipColor2.value.copy(CONFIG.grass.tipColor2);
        }},
        { id: 'col-grass-base-3', target: CONFIG.grass.baseColor3, cb: () => {
            if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uBaseColor3.value.copy(CONFIG.grass.baseColor3);
            if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uBaseColor3.value.copy(CONFIG.grass.baseColor3);
        }},
        { id: 'col-grass-tip-3', target: CONFIG.grass.tipColor3, cb: () => {
            if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uTipColor3.value.copy(CONFIG.grass.tipColor3);
            if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uTipColor3.value.copy(CONFIG.grass.tipColor3);
        }},
        { id: 'col-grass-base-4', target: CONFIG.grass.baseColor4, cb: () => {
            if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uBaseColor4.value.copy(CONFIG.grass.baseColor4);
            if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uBaseColor4.value.copy(CONFIG.grass.baseColor4);
        }},
        { id: 'col-grass-tip-4', target: CONFIG.grass.tipColor4, cb: () => {
            if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uTipColor4.value.copy(CONFIG.grass.tipColor4);
            if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uTipColor4.value.copy(CONFIG.grass.tipColor4);
        }},
        { id: 'col-terr-fog', target: CONFIG.terrain.fogColor, cb: () => {
            terrainSystem.material.uniforms.uFogColor.value.copy(CONFIG.terrain.fogColor);
            if (CONFIG.ui.groundMode) scene.fog.color.copy(CONFIG.terrain.fogColor);
        }},

        { id: 'col-rock-base', target: CONFIG.rocks.baseColor, cb: () => {
            if(rockSystem.mesh) rockSystem.mesh.material.uniforms.uBaseColor.value.copy(CONFIG.rocks.baseColor);
        }},

        { id: 'col-foam', target: CONFIG.water.foamColor, cb: () => {
            terrainSystem.material.uniforms.uFoamColor.value.copy(CONFIG.water.foamColor);
        }},
        { id: 'col-rock-tip', target: CONFIG.rocks.tipColor, cb: () => {
            if(rockSystem.mesh) rockSystem.mesh.material.uniforms.uTipColor.value.copy(CONFIG.rocks.tipColor);
        }},
        { id: 'col-grass-base', target: CONFIG.grass.baseColor, cb: () => {
            if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uBaseColor.value.copy(CONFIG.grass.baseColor);
            if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uBaseColor.value.copy(CONFIG.grass.baseColor);
        }},
        { id: 'col-grass-tip', target: CONFIG.grass.tipColor, cb: () => {
            if(grassSystem.materialNear) grassSystem.materialNear.uniforms.uTipColor.value.copy(CONFIG.grass.tipColor);
            if(grassSystem.materialFar) grassSystem.materialFar.uniforms.uTipColor.value.copy(CONFIG.grass.tipColor);
        }},
        { id: 'col-cfog', target: CONFIG.terrain.creepingFogColor, cb: () => {
            creepingFogUniforms.uCFogColor.value.copy(CONFIG.terrain.creepingFogColor);
        }},
        { id: 'col-light', target: CONFIG.flashlight.color, cb: () => {
            // Обновление теперь происходит централизованно в цикле рендеринга
        }}
    ];

    inputs.forEach(conf => {
        const inputEl = document.getElementById(conf.id);
        if(!inputEl) return;

        // Прячем стандартный инпут
        inputEl.style.opacity = 0; 
        inputEl.style.position = 'absolute';
        inputEl.style.pointerEvents = 'none';
        // Добавляем пикеры для сфер в массив inputs функции setupColorPickers()
        // Или, если вы не хотите лезть внутрь той функции, просто добавьте их вручную:
        const sphereColors = [
            { id: 'sphere-col-1', idx: 0 },
            { id: 'sphere-col-2', idx: 1 },
            { id: 'sphere-col-3', idx: 2 }
        ];

        sphereColors.forEach(conf => {
            const el = document.getElementById(conf.id);
            // Логика аналогична вашей функции setupColorPickers, 
            // здесь упрощенный вариант обновления конфига:
            el.addEventListener('change', (e) => {
                CONFIG.spheres.colors[conf.idx].set(e.target.value);
                sphereSystem.refresh();
            });
            // Если вы используете ваш кастомный пикер, добавьте эти ID в массив inputs внутри setupColorPickers
        });



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

if (grainToggle) {
    grainToggle.addEventListener('change', (e) => {
        CONFIG.graphics.grainEnabled = e.target.checked;
        filmGrainMesh.visible = e.target.checked;
    });
}

if (grainOpacity) {
    grainOpacity.addEventListener('input', (e) => {
        CONFIG.graphics.grainOpacity = parseFloat(e.target.value);
        grainMaterial.uniforms.uOpacity.value = CONFIG.graphics.grainOpacity;
    });
}

const clock = new THREE.Clock();
let frameCount = 0; 
let isRenderPaused = false; // <--- 1. Флаг паузы

// <--- 2. Слушатель переключения паузы из галереи
window.addEventListener('toggle-pause', (e) => {
    isRenderPaused = e.detail;
    if (!isRenderPaused) {
        // Сбрасываем накопленное время, чтобы физика не "скакнула" при возобновлении
        clock.getDelta(); 
    }
});




// Авто-лог при старте, если через 5 секунд всё еще висит
setTimeout(() => {
    if (state.activeTasks.size > 0 && state.activeTasks.size === MAX_CONCURRENT_LOADS) {
        console.error("⚠️ POTENTIAL DEADLOCK DETECTED AT STARTUP");
        window.AnemoneDebug.status();
    }
}, 5000);

// --- СИСТЕМА ДЖОЙСТИКОВ ---
function initTouchControls() {
    // 1. Стили с CSS переменными для размеров
    const style = document.createElement('style');
    // По умолчанию 100px зона (было 140px) и 40px стик (было 50px)
    style.innerHTML = `
        :root {
            --joy-size: 100px;
            --joy-knob: 40px;
        }
        .joystick-zone {
            position: fixed; bottom: 40px; 
            width: var(--joy-size); height: var(--joy-size);
            z-index: 1000; display: none; /* Скрыто по CSS, управляется JS */
            user-select: none; -webkit-user-select: none; touch-action: none;
            transition: opacity 0.3s;
        }
        .joystick-zone.left { left: 40px; }
        .joystick-zone.right { right: 40px; }
        .joystick-knob {
            position: absolute; left: 50%; top: 50%; 
            width: var(--joy-knob); height: var(--joy-knob);
            margin-left: calc(var(--joy-knob) / -2);
            margin-top: calc(var(--joy-knob) / -2);
            background: rgba(255, 255, 255, 0.3);
            border: 2px solid rgba(255, 255, 255, 0.5); border-radius: 50%;
            pointer-events: none; transition: transform 0.1s;
        }
        .joystick-base {
            width: 100%; height: 100%; border-radius: 50%;
            background: rgba(0, 0, 0, 0.2); border: 2px solid rgba(255, 255, 255, 0.1);
        }
        /* Показываем только на тач-устройствах ЕСЛИ включен класс visible */
        @media (pointer: coarse) { 
            .joystick-zone.visible { display: block; } 
        }
    `;
    document.head.appendChild(style);

    // 2. HTML
    const createStick = (cls) => {
        const zone = document.createElement('div');
        zone.className = `joystick-zone ${cls} visible`; // Добавили класс visible по умолчанию
        zone.innerHTML = '<div class="joystick-base"></div><div class="joystick-knob"></div>';
        document.body.appendChild(zone);
        return { zone, knob: zone.querySelector('.joystick-knob') };
    };

    const leftStick = createStick('left');
    const rightStick = createStick('right');

    // 3. Обработчики событий (без изменений логики движения)
    const handleStick = (stickObj, stateKey, isLook) => {
        let touchId = null;
        
        // Динамический расчет радиуса при касании (чтобы работало после ресайза)
        const getMaxDist = () => {
            return stickObj.zone.clientWidth / 2 - 10; 
        };

        stickObj.zone.addEventListener('touchstart', (e) => {
            e.preventDefault(); e.stopPropagation();
            if (touchId !== null) return;
            const touch = e.changedTouches[0];
            touchId = touch.identifier;
            state.joystick[stateKey].active = true;
            if (isLook) state.isLooking = true; 
        }, { passive: false });

        const onMove = (e) => {
            if (touchId === null) return;
            for (let i = 0; i < e.changedTouches.length; i++) {
                if (e.changedTouches[i].identifier === touchId) {
                    const t = e.changedTouches[i];
                    const rect = stickObj.zone.getBoundingClientRect();
                    const centerX = rect.left + rect.width / 2;
                    const centerY = rect.top + rect.height / 2;
                    const maxDist = getMaxDist(); // Используем актуальный размер

                    let dx = t.clientX - centerX;
                    let dy = t.clientY - centerY;
                    const dist = Math.sqrt(dx*dx + dy*dy);
                    
                    if (dist > maxDist) {
                        dx = (dx / dist) * maxDist;
                        dy = (dy / dist) * maxDist;
                    }
                    
                    stickObj.knob.style.transform = `translate(${dx}px, ${dy}px)`;
                    state.joystick[stateKey].x = dx / maxDist;
                    state.joystick[stateKey].y = dy / maxDist;
                    break;
                }
            }
        };

        const onEnd = (e) => {
            for (let i = 0; i < e.changedTouches.length; i++) {
                if (e.changedTouches[i].identifier === touchId) {
                    touchId = null;
                    state.joystick[stateKey].active = false;
                    state.joystick[stateKey].x = 0;
                    state.joystick[stateKey].y = 0;
                    stickObj.knob.style.transform = `translate(0px, 0px)`;
                    if (isLook) state.isLooking = false;
                    break;
                }
            }
        };

        stickObj.zone.addEventListener('touchmove', (e) => { e.preventDefault(); e.stopPropagation(); onMove(e); }, { passive: false });
        stickObj.zone.addEventListener('touchend', onEnd);
        stickObj.zone.addEventListener('touchcancel', onEnd);
    };

    handleStick(leftStick, 'left', false);
    handleStick(rightStick, 'right', true);
}

// Запускаем инициализацию
initTouchControls();

// --- СИСТЕМА МОНИТОРИНГА (FPS) ---
let showStats = false;
let fpsFrames = 0;
let fpsLastTime = performance.now();

const statFps = document.getElementById('stat-fps');
const statCalls = document.getElementById('stat-calls');
const statTris = document.getElementById('stat-tris');
const statsPanel = document.getElementById('stats-panel');

document.getElementById('ui-fps-toggle')?.addEventListener('change', (e) => {
    showStats = e.target.checked;
    if (statsPanel) statsPanel.style.display = showStats ? 'block' : 'none';
});

function updateParticleScales() {
    // Получаем реальный физический множитель пикселей
    const currentPixelRatio = renderer.getPixelRatio();
    // Вычисляем масштаб с учетом плотности пикселей
    const fullScale = window.innerHeight * currentPixelRatio;
    const halfScale = fullScale / 2.0;

    // Обновляем все ShaderMaterial, использующие gl_PointSize
    if (typeof constellationDotMat !== 'undefined') constellationDotMat.uniforms.uScale.value = fullScale;
    if (typeof starMat !== 'undefined') starMat.uniforms.uScale.value = fullScale;
    if (typeof slowComet !== 'undefined' && slowComet.headMat) slowComet.headMat.uniforms.uScale.value = fullScale;
    if (typeof fireflyMat !== 'undefined') fireflyMat.uniforms.uScale.value = halfScale;
    if (typeof dustMat !== 'undefined') dustMat.uniforms.uScale.value = halfScale;
    if (typeof sphereSystem !== 'undefined' && sphereSystem.trailMat) sphereSystem.trailMat.uniforms.uScale.value = fullScale;
}


function collectFallenStar(mesh) {
    // Находим индекс звезды в системе упавших звезд
    const index = fallenStarSystem.stars.indexOf(mesh);
    if (index === -1) return;

    const pos = mesh.position.clone();

    // 1. Удаляем звезду из массива и сцены (освещение погаснет автоматически на следующем кадре)
    fallenStarSystem.stars.splice(index, 1);
    fallenStarSystem.group.remove(mesh);
    
    // Очищаем ресурсы удаленной геометрии и материалов
    mesh.children.forEach(child => {
        if (child.material) child.material.dispose();
    });
    if (mesh.material) mesh.material.dispose();

    // 2. Увеличиваем счётчик и сохраняем его в localStorage
    collectedStarsCount++;
    localStorage.setItem('collected_stars_count', collectedStarsCount.toString());

    // 3. Создаем всплывающий текст обратной связи
    spawnFloatingText(`+! (${collectedStarsCount})`, pos);

    // 4. Проверка круглых чисел для создания облачка "мяу"
    const milestones = {
        30: "мяу",
        100: "мяу-мяу",
        200: "мяу-мяу-мяу",
        500: "мяу-мяу-мяу-мяу",
        1000: "мяу-мяу-мяу-мяу-мяу"
    };

    if (milestones[collectedStarsCount]) {
        const textBubble = milestones[collectedStarsCount];
        const localBubbleId = 'milestone_' + Date.now();
        
        // Создаем облачко в 3D сцене (используя вашу существующую функцию spawnCommentObject)
        // Облачко остаётся на месте сбора и не отправляется на сервер
        spawnCommentObject(localBubbleId, textBubble, pos.x, pos.y + 15.0, pos.z);
    }
}

// Вспомогательная функция для применения настроек фонарика без аллокации памяти
function applyFlashlightToMaterial(mat, enable) {
    if (!mat || !mat.uniforms) return;
    const u = mat.uniforms;
    if (u.uLightEnable) u.uLightEnable.value = enable;
    if (u.uLightColor) u.uLightColor.value.copy(CONFIG.flashlight.color);
    if (u.uLightIntensity) u.uLightIntensity.value = CONFIG.flashlight.intensity;
    if (u.uLightRange) u.uLightRange.value = CONFIG.flashlight.range;
    if (u.uLightRadius) u.uLightRadius.value = CONFIG.flashlight.radius;
    if (u.uLightFocus) u.uLightFocus.value = CONFIG.flashlight.focus;
    if (u.uLightOffset) u.uLightOffset.value = CONFIG.flashlight.offset;
    if (u.uLightDir) u.uLightDir.value.copy(globalUniforms.uLightDir.value);
    if (u.uCamDir) u.uCamDir.value.copy(globalUniforms.uCamDir.value);
    if (u.uCamPos) u.uCamPos.value.copy(camera.position);
}

function updateFlashlightUniforms() {
    const enabled = CONFIG.flashlight.enabled;

    // 1. Ландшафт
    if (terrainSystem && terrainSystem.mesh && terrainSystem.mesh.visible) {
        applyFlashlightToMaterial(terrainSystem.material, enabled ? 1.0 : 0.0);
    }
    
    // 2. Трава
    if (grassSystem) {
        if (grassSystem.meshNear && grassSystem.meshNear.visible) {
            applyFlashlightToMaterial(grassSystem.materialNear, (enabled && CONFIG.flashlight.affectGrass) ? 1.0 : 0.0);
        }
        if (grassSystem.meshFar && grassSystem.meshFar.visible && CONFIG.grass.lodEnabled) {
            applyFlashlightToMaterial(grassSystem.materialFar, (enabled && CONFIG.flashlight.affectGrass) ? 1.0 : 0.0);
        }
    }
    
    // 3. Камни
    if (rockSystem && rockSystem.group.visible) {
        if (rockSystem.meshSmall) {
            applyFlashlightToMaterial(rockSystem.meshSmall.material, (enabled && CONFIG.flashlight.affectRocks) ? 1.0 : 0.0);
        }
        if (rockSystem.meshBoulder) {
            applyFlashlightToMaterial(rockSystem.meshBoulder.material, (enabled && CONFIG.flashlight.affectRocks) ? 1.0 : 0.0);
        }
    }
}

// --- ДОБАВИТЬ ЭТО ПЕРЕД ФУНКЦИЕЙ animate() ---
// Глобальные векторы для переиспользования (ОПТИМИЗАЦИЯ ПАМЯТИ)
const _forward = new THREE.Vector3();
const _right = new THREE.Vector3();
const _camDir = new THREE.Vector3();
const _lightDir = new THREE.Vector3();
const _rightVec = new THREE.Vector3();
const _upVec = new THREE.Vector3();


// Этот эвент вызывается модулем видео при рендере каждого кадра.
// Он заменяет собой функцию animate(), но использует фиксированное виртуальное время.
window.addEventListener('render-offline-frame', (e) => {
    const time = e.detail.time;
    
    // 1. Обновляем время во всех шейдерах и системах
    globalUniforms.uTime.value = time;
    grainMaterial.uniforms.uTime.value = time;
    
    starMat.uniforms.uTime.value = time;     
    dustMat.uniforms.uTime.value = time;
    fireflyMat.uniforms.uTime.value = time;
    
    // 2. Обновляем логику систем
    skyDome.update(camera.position, time);
    slowComet.update(CONFIG.sky.blur);
    fallenStarSystem.update(time);
    
    // Вектора и освещение
    camera.getWorldDirection(_camDir);
    globalUniforms.uCamDir.value.copy(_camDir);
    _lightDir.copy(_camDir);
    globalUniforms.uLightDir.value.copy(_lightDir);
    
    terrainSystem.update(camera.position, _camDir, time, _lightDir);
    grassSystem.update(camera.position, time);
    rockSystem.update(camera.position, time);
    solarManager.update(time);
    sphereSystem.update(); // Внутри использует performance.now(), но для офлайна это терпимо, либо можно передать time туда
    
    // 3. Выполняем отрисовку
    reflectionSystem.update(renderer); 
    renderer.render(scene, camera);
});


function animate() {
    requestAnimationFrame(animate);
    if (isRenderPaused) return;

    if (showStats) {
        fpsFrames++;
        const now = performance.now();
        if (now >= fpsLastTime + 1000) {
            const fps = Math.round((fpsFrames * 1000) / (now - fpsLastTime));
            statFps.innerText = fps;
            statFps.style.color = fps >= 50 ? '#44ff44' : (fps >= 30 ? '#ffff00' : '#ff4444');
            statCalls.innerText = renderer.info.render.calls;
            statTris.innerText = renderer.info.render.triangles.toLocaleString('ru-RU');
            fpsFrames = 0;
            fpsLastTime = now;
        }
    }

    frameCount++; 
    const dt = clock.getDelta();
    const time = clock.getElapsedTime();

    const moveSpeed = 15.0; 
    
    // СТАЛО: Используем заранее созданные векторы вместо "new THREE.Vector3()"
    camera.getWorldDirection(_forward);
    _right.crossVectors(_forward, camera.up).normalize();

    let inputZ = 0;
    let inputX = 0;

    if (state.keys.w || state.keys.up) inputZ += 1;
    if (state.keys.s || state.keys.down) inputZ -= 1;
    if (state.keys.d || state.keys.right) inputX += 1;
    if (state.keys.a || state.keys.left) inputX -= 1;

    if (state.joystick.left.active) {
        inputZ -= state.joystick.left.y; 
        inputX += state.joystick.left.x;
    }

    // Применяем движение
    if (Math.abs(inputZ) > 0.01) state.targetPos.addScaledVector(_forward, inputZ * moveSpeed);
    if (Math.abs(inputX) > 0.01) state.targetPos.addScaledVector(_right, inputX * moveSpeed);

    // ... (весь код вращения камеры state.look оставляем без изменений) ...
    if (state.joystick.right.active) {
        const lookSpeed = 0.01;
        state.look.targetX -= state.joystick.right.x * lookSpeed;
        state.look.targetY -= state.joystick.right.y * lookSpeed;
        const maxAngle = Math.PI / 4;
        state.look.targetY = Math.max(-maxAngle, Math.min(maxAngle, state.look.targetY));
    }
    const rollSpeed = 0.02;
    const maxRoll = Math.PI / 4;
    if (state.keys.q) state.look.targetZ += rollSpeed;
    if (state.keys.e) state.look.targetZ -= rollSpeed;
    if (CONFIG.ui.autoLevel) { 
        if (!state.isLooking) {
            state.look.targetX *= 0.9; 
            state.look.targetY *= 0.9;
        }
        if (!state.keys.q && !state.keys.e) state.look.targetZ *= 0.9;
    }
    state.look.targetZ = Math.max(-maxRoll, Math.min(maxRoll, state.look.targetZ));
    const lookSmoothness = 0.2;
    state.look.currentX += (state.look.targetX - state.look.currentX) * lookSmoothness;
    state.look.currentY += (state.look.targetY - state.look.currentY) * lookSmoothness;
    state.look.currentZ += (state.look.targetZ - state.look.currentZ) * lookSmoothness;
    camera.rotation.set(state.look.currentY, state.look.currentX, state.look.currentZ);

    if (CONFIG.ui.groundMode) {
        const currentTerrainHeight = getTerrainHeight(state.targetPos.x, state.targetPos.z);
        const minCamHeight = currentTerrainHeight + 40.0; 
        
        // БЫЛО: const maxCamHeight = currentTerrainHeight + 250.0; 
        // СТАЛО:
        const maxCamHeight = currentTerrainHeight + CONFIG.ui.maxCamHeight; 
        
        state.targetPos.y = Math.max(minCamHeight, Math.min(state.targetPos.y, maxCamHeight));
    }
    skyDome.update(camera.position, time);
    state.currentPos.lerp(state.targetPos, 0.08);
    camera.position.copy(state.currentPos);
    updateChunks();

    starSystem.geometry.setDrawRange(0, CONFIG.sky.starDensity);
    starMat.uniforms.uBlur.value = CONFIG.sky.blur;
    starMat.uniforms.uSizeMult.value = CONFIG.sky.starSize;
    starMat.uniforms.uTime.value = time;     
    starMat.uniforms.uCamPos.value.copy(camera.position);  
    starSystem.position.copy(camera.position); 
    
    slowComet.lines.position.copy(camera.position);
    slowComet.heads.position.copy(camera.position);
    comet.update(camera.position);    
    slowComet.update(CONFIG.sky.blur);
    fallenStarSystem.update(time);
    updateFloatingTexts(dt);

    dustMat.uniforms.uCamPos.value.copy(camera.position);
    dustMat.uniforms.uTime.value = time;
    // ДОБАВИТЬ ЭТО: Передача скорости в реальном времени
    dustMat.uniforms.uWindSpeed.value = CONFIG.wind.speed;
    dustMat.uniforms.uWindForce.value = CONFIG.wind.force;
    dustMat.uniforms.uPartSpeed.value = CONFIG.particles.speed;

    dustSystem.geometry.setDrawRange(0, CONFIG.details.dustCount);
    dustMat.uniforms.uSizeMult.value = CONFIG.details.dustSize;

    fireflySystem.geometry.setDrawRange(0, CONFIG.details.fireflyCount);
    fireflyMat.uniforms.uSizeMult.value = CONFIG.details.fireflySize;

    globalUniforms.uTime.value = time;
    grainMaterial.uniforms.uTime.value = time;
    if (constellationTubeMat) {
        const pulse = 0.7 + 0.3 * Math.sin(time * 3.0);
        constellationTubeMat.opacity = pulse;
    }

    globalUniforms.uWindSpeed.value = CONFIG.wind.speed;
    globalUniforms.uWindForce.value = CONFIG.wind.force;
    sharedCloudUniforms.uWindAngle.value = CONFIG.grass.bendAngle;
    
    globalUniforms.uCamPos.value.copy(camera.position);
    
    // СТАЛО: Переиспользуем векторы
    camera.getWorldDirection(_camDir);
    globalUniforms.uCamDir.value.copy(_camDir);

    _lightDir.copy(_camDir);
    if (CONFIG.flashlight.animAmp > 0.001) {
        const t = time * CONFIG.flashlight.animSpeed;
        const offsetX = (Math.sin(t * 1.3) + Math.sin(t * 0.7)) * 0.5 * CONFIG.flashlight.animAmp;
        const offsetY = (Math.cos(t * 1.1) + Math.sin(t * 0.5)) * 0.5 * CONFIG.flashlight.animAmp;

        _rightVec.crossVectors(_camDir, camera.up).normalize();
        _upVec.crossVectors(_rightVec, _camDir).normalize();

        _lightDir.add(_rightVec.multiplyScalar(offsetX));
        _lightDir.add(_upVec.multiplyScalar(offsetY));
        _lightDir.normalize();
    }
    globalUniforms.uLightDir.value.copy(_lightDir);
    
    // Дальше все вызовы без изменений
    terrainSystem.update(camera.position, _camDir, time, _lightDir);
    grassSystem.update(camera.position, time);
    rockSystem.update(camera.position, time);
    updateFlashlightUniforms(); // <-- Добавлено для синхронизации
    solarManager.update(time);

    const isGround = CONFIG.ui.groundMode ? 1.0 : 0.0;
    dustMat.uniforms.uGroundMode.value = isGround;
    starMat.uniforms.uGroundMode.value = isGround;
    dustMat.uniforms.uAmplitude.value = CONFIG.terrain.amplitude;
    dustMat.uniforms.uFrequency.value = CONFIG.terrain.frequency;
    dustMat.uniforms.uOffset.value = CONFIG.terrain.offset;
    dustMat.uniforms.uSharpness.value = CONFIG.terrain.sharpness;

    fireflyMat.uniforms.uCamPos.value.copy(camera.position);
    fireflyMat.uniforms.uTime.value = time;
    fireflyMat.uniforms.uWindSpeed.value = CONFIG.wind.speed;
    fireflyMat.uniforms.uWindForce.value = CONFIG.wind.force;
    fireflyMat.uniforms.uPartSpeed.value = CONFIG.particles.speed;
    fireflyMat.uniforms.uGroundMode.value = isGround;
    fireflyMat.uniforms.uAmplitude.value = CONFIG.terrain.amplitude;
    fireflyMat.uniforms.uFrequency.value = CONFIG.terrain.frequency;
    fireflyMat.uniforms.uOffset.value = CONFIG.terrain.offset;
    fireflyMat.uniforms.uSharpness.value = CONFIG.terrain.sharpness;

    updateNavigationHUD();
    sphereSystem.update();

        const activeTerrainLights = populateLightSet(terrainLightSet, true, true); 
    const activeGrassLights = populateLightSet(grassLightSet, CONFIG.sphereLights.affectGrass, CONFIG.cometLights.affectGrass);
    const activeRockLights = populateLightSet(rockLightSet, CONFIG.sphereLights.affectRocks, CONFIG.cometLights.affectRocks);

    // Передаем точное количество разрешенных источников в материалы
    terrainSystem.material.uniforms.uPointLightCount.value = activeTerrainLights;
    
    if (grassSystem.materialNear) grassSystem.materialNear.uniforms.uPointLightCount.value = activeGrassLights;
    if (grassSystem.materialFar) grassSystem.materialFar.uniforms.uPointLightCount.value = activeGrassLights;
    
    if (rockSystem.meshSmall) rockSystem.meshSmall.material.uniforms.uPointLightCount.value = activeRockLights;
    if (rockSystem.meshBoulder) rockSystem.meshBoulder.material.uniforms.uPointLightCount.value = activeRockLights;

    reflectionSystem.update(renderer); 
    renderer.render(scene, camera);
}


// --- ЛОГИКА СКРИНШОТОВ ---
// --- ЛОГИКА СКРИНШОТОВ ---
const screenshotBtn = document.getElementById('screenshot-btn');

document.getElementById('ui-screenshot-toggle')?.addEventListener('change', (e) => {
    CONFIG.ui.showScreenshotBtn = e.target.checked;
    screenshotBtn.style.display = e.target.checked ? 'flex' : 'none';
});

document.getElementById('ui-screenshot-scale')?.addEventListener('input', (e) => {
    CONFIG.graphics.screenshotScale = parseFloat(e.target.value);
});

screenshotBtn?.addEventListener('click', () => {
    // Временно скрываем курсор и мигаем кнопкой
    const originalOpacity = screenshotBtn.style.opacity;
    screenshotBtn.style.opacity = '0.5';
    
    // Сохраняем текущие параметры рендера
    const origPixelRatio = renderer.getPixelRatio();
    const w = window.innerWidth;
    const h = window.innerHeight;

    // Устанавливаем целевое разрешение скриншота (без изменения размера CSS)
    renderer.setPixelRatio(CONFIG.graphics.screenshotScale);
    renderer.setSize(w, h, false);
    
    // !!! ДОБАВЛЕНО: Обновляем размеры точек под высокое разрешение !!!
    updateParticleScales(); 

    // Принудительно рендерим кадр
    renderer.render(scene, camera);

    // Получаем DataURL картинки
    const dataURL = renderer.domElement.toDataURL('image/png');

    // Возвращаем настройки рендера обратно
    renderer.setPixelRatio(origPixelRatio);
    renderer.setSize(w, h);
    
    // !!! ДОБАВЛЕНО: Возвращаем размеры точек под обычное разрешение !!!
    updateParticleScales();

    // Создаем ссылку для скачивания
    const link = document.createElement('a');
    const date = new Date().toISOString().replace(/:/g, '-').slice(0, 19);
    link.download = `Anemone_Screenshot_${date}.png`;
    link.href = dataURL;
    link.click();

    // Возвращаем кнопку
    setTimeout(() => { screenshotBtn.style.opacity = originalOpacity; }, 200);
});



applyGroundModeVisuals();

animate();
setTimeout(() => document.getElementById('status').style.opacity = 0, 1000);
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    starMat.uniforms.uResolution.value.set(window.innerWidth, window.innerHeight);
    
    updateParticleScales(); 
});
syncUIToConfig();
initGallery();
updateParticleScales();

// --- ЛОГИКА КЛИКОВ И РЕДАКТОРА (Добавить в конец script.js) ---

// 1. Raycaster для клика по звездам в 3D
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

window.addEventListener('mousedown', (e) => {
    if (isUIInteraction(e)) return;
    if (e.button === 0) { // Левый клик
        mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
        mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
        raycaster.setFromCamera(mouse, camera);
        
        // 1. Проверяем клик по космическим системам
        const solarIntersects = raycaster.intersectObjects(solarManager.getClickableStars());
        if (solarIntersects.length > 0) {
            const starId = solarIntersects[0].object.userData.systemId;
            openSolarEditor(starId);
            state.isDragging = false; 
            e.stopPropagation();
            return;
        }

        // 2. Проверяем клик по упавшим на землю звёздам
        // Проверяем только прямых потомков (меши OctahedronGeometry), игнорируя спрайты-ореолы
        const starIntersects = raycaster.intersectObjects(fallenStarSystem.group.children, false);
        if (starIntersects.length > 0) {
            const clickedMesh = starIntersects[0].object;
            collectFallenStar(clickedMesh);
            state.isDragging = false;
            e.stopPropagation();
            return;
        }
    }
});

// 2. Логика Интерфейса Модального окна
const solarModal = document.getElementById('solar-modal');
const solarListView = document.getElementById('solar-list-view');
const solarEditView = document.getElementById('solar-edit-view');
let currentEditingSystemId = null;
let currentPlanetsData = [];

// Открыть модалку со списком
let solarPreview = null;

// Функция для сбора текущих данных из UI редактора
function getSolarFormData() {
    return {
        name: document.getElementById('solar-name').value || 'Новая система',
        pos: currentEditingSystemId ? solarManager.systems.get(currentEditingSystemId).data.pos : {x: 0, y: 0, z: 0},
        star: {
            size: parseFloat(document.getElementById('solar-star-size').value),
            bright: parseFloat(document.getElementById('solar-star-bright').value),
            color: document.getElementById('solar-star-color').value,
            glowColor: document.getElementById('solar-glow-color').value
        },
        showOrbits: document.getElementById('solar-show-orbits').checked,
        labels: {
            show: document.getElementById('solar-show-labels').checked,
            size: parseFloat(document.getElementById('solar-label-size').value),
            color: document.getElementById('solar-label-color').value
        },
        planets: currentPlanetsData
    };
}

// Триггер обновления превью при любом изменении
function updatePreview() {
    if (solarPreview && solarPreview.active) {
        solarPreview.updateData(getSolarFormData(), solarManager);
    }
}

// Открыть модалку со списком
document.getElementById('solar-btn').addEventListener('click', () => {
    solarModal.style.display = 'flex';
    solarListView.style.display = 'block';
    solarEditView.style.display = 'none';
    
    // ПАУЗА ОСНОВНОГО РЕНДЕРА
    window.dispatchEvent(new CustomEvent('toggle-pause', { detail: true }));

    // ... (остальной код вывода списка видимых систем без изменений) ...
    camera.updateMatrixWorld();
    const frustum = new THREE.Frustum().setFromProjectionMatrix(
        new THREE.Matrix4().multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse)
    );
    const visible = solarManager.getVisibleSystems(frustum);
    
    const listDiv = document.getElementById('visible-solar-list');
    listDiv.innerHTML = visible.length === 0 ? '<div style="color:#666; font-size:12px;">В поле зрения нет систем</div>' : '';
    
    visible.forEach(sys => {
        const btn = document.createElement('button');
        btn.innerText = `Редактировать: ${sys.name}`;
        btn.style.cssText = "width:100%; padding:10px; background:rgba(255,255,255,0.1); border:none; border-radius:6px; color:#fff; cursor:pointer; text-align:left; font-weight:bold;";
        btn.onclick = () => openSolarEditor(sys.id);
        listDiv.appendChild(btn);
    });
});

document.getElementById('close-solar-modal').addEventListener('click', () => {
    solarModal.style.display = 'none';
    if(solarPreview) solarPreview.stop();
    // ВОЗОБНОВЛЕНИЕ ОСНОВНОГО РЕНДЕРА
    window.dispatchEvent(new CustomEvent('toggle-pause', { detail: false }));
});

// Открыть редактор (создание или редактирование)
window.openSolarEditor = function(systemId = null) {
    // --- ИСПРАВЛЕНИЕ: Сбрасываем залипшее управление камеры ---
    state.isDragging = false;
    state.isLooking = false;
    if(state.keys) for (let k in state.keys) state.keys[k] = false;
    
    currentEditingSystemId = systemId;
    solarModal.style.display = 'flex';
    solarListView.style.display = 'none';
    solarEditView.style.display = 'flex';
    
    const isNew = !systemId;
    document.getElementById('solar-delete-btn').style.display = isNew ? 'none' : 'block';
    
    let data;
    if (isNew) {
        data = {
            name: "Новая система",
            star: { size: 60, bright: 1.0, color: "#ffaa00", glowColor: "#ffaa00" },
            showOrbits: true,
            labels: { show: true, size: 30, color: "#ffffff" },
            planets: []
        };
    } else {
        const sys = solarManager.systems.get(systemId);
        data = {
            name: sys.data.name, 
            star: { 
                size: sys.data.star.size, bright: sys.data.star.brightness || sys.data.star.bright, 
                color: sys.data.star.color, glowColor: sys.data.star.glowColor || sys.data.star.color 
            },
            showOrbits: sys.data.showOrbits, 
            labels: sys.data.labels || { show: false, size: 30, color: "#ffffff" },
            planets: JSON.parse(JSON.stringify(sys.data.planets || []))
        };
    }

    // Заполнение UI
    document.getElementById('solar-name').value = data.name;
    document.getElementById('solar-star-size').value = data.star.size;
    document.getElementById('solar-star-bright').value = data.star.bright;
    document.getElementById('solar-star-color').value = data.star.color;
    document.getElementById('solar-glow-color').value = data.star.glowColor;
    document.getElementById('solar-show-orbits').checked = data.showOrbits;
    document.getElementById('solar-show-labels').checked = data.labels.show;
    document.getElementById('solar-label-size').value = data.labels.size;
    document.getElementById('solar-label-color').value = data.labels.color;
    
    currentPlanetsData = data.planets;
    renderPlanetsUI();

    // Запуск превью
    if(!solarPreview) solarPreview = new SolarPreview();
    
    // Сбрасываем позицию камеры превью на стандартную при каждом открытии
    solarPreview.camera.position.set(0, 1500, 2500);
    
    solarPreview.resize();
    solarPreview.start();
    updatePreview();
};

document.getElementById('solar-save-btn').addEventListener('click', async (e) => {
    e.stopPropagation(); // Блокируем клик, чтобы не задел холст
    const payload = getSolarFormData();
    
    // Передаем правильную позицию, если новая система
    if (!currentEditingSystemId) {
        const dir = new THREE.Vector3(); camera.getWorldDirection(dir);
        const p = new THREE.Vector3().copy(camera.position).add(dir.multiplyScalar(800));
        payload.pos = {x: p.x, y: p.y, z: p.z};
    }

    document.getElementById('solar-save-btn').innerText = "...";
    await solarManager.saveSystem(currentEditingSystemId, payload);
    document.getElementById('solar-save-btn').innerText = "СОХРАНИТЬ";
    
    solarModal.style.display = 'none';
    if(solarPreview) solarPreview.stop();
    
    // --- ИСПРАВЛЕНИЕ: Еще раз сбрасываем, чтобы после закрытия не было рывков ---
    state.isDragging = false;
    state.isLooking = false;
    
    window.dispatchEvent(new CustomEvent('toggle-pause', { detail: false }));
});

// Привязка слушателей на все базовые поля, чтобы превью обновлялось
['solar-name', 'solar-star-size', 'solar-star-bright', 'solar-star-color', 'solar-glow-color', 
 'solar-show-orbits', 'solar-show-labels', 'solar-label-size', 'solar-label-color'].forEach(id => {
    document.getElementById(id).addEventListener('input', updatePreview);
    document.getElementById(id).addEventListener('change', updatePreview);
});
document.getElementById('create-new-solar')?.addEventListener('click', () => {
    window.openSolarEditor(null);
});

// Обработчик кнопки "Добавить планету"
document.getElementById('add-planet-btn')?.addEventListener('click', () => {
    currentPlanetsData.push({
        name: "Новая планета",
        size: 15,
        orbit: 150 + (currentPlanetsData.length * 80),
        speed: 0.5,
        glow: 0,
        color: "#00aaff"
    });
    renderPlanetsUI();
    updatePreview();
});

document.getElementById('solar-delete-btn')?.addEventListener('click', async () => {
    if (confirm("Точно удалить систему?")) {
        await solarManager.deleteSystem(currentEditingSystemId);
        solarModal.style.display = 'none';
        if(solarPreview) solarPreview.stop();
        window.dispatchEvent(new CustomEvent('toggle-pause', { detail: false }));
    }
});
// Обновленный рендер списка планет (с привязкой к updatePreview)
function renderPlanetsUI() {
    const cont = document.getElementById('planets-container');
    cont.innerHTML = '';
    currentPlanetsData.forEach((p, idx) => {
        const div = document.createElement('div');
        div.style.cssText = "background:rgba(0,0,0,0.4); padding:10px; border-radius:6px; border:1px solid rgba(255,255,255,0.05);";
        div.innerHTML = `
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <input type="text" value="${p.name || 'Планета'}" data-key="name" data-idx="${idx}" placeholder="Имя планеты" style="background:none; border:none; color:#fff; font-weight:bold; width:120px; outline:none; border-bottom:1px solid #444;">
                <button class="del-planet" data-idx="${idx}" style="background:none; border:none; color:#ff4444; cursor:pointer;">✖</button>
            </div>
            <div style="display:flex; gap:10px; align-items:center; margin-bottom:6px;">
                <div style="flex:1;"><label style="font-size:10px;color:#aaa;">Размер</label><input type="range" data-key="size" data-idx="${idx}" min="5" max="50" step="1" value="${p.size}" style="width:100%;"></div>
                <div style="flex:1;"><label style="font-size:10px;color:#aaa;">Орбита</label><input type="range" data-key="orbit" data-idx="${idx}" min="100" max="1500" step="10" value="${p.orbit}" style="width:100%;"></div>
            </div>
            <div style="display:flex; gap:10px; align-items:center;">
                <div style="flex:1;"><label style="font-size:10px;color:#aaa;">Скорость</label><input type="range" data-key="speed" data-idx="${idx}" min="0.1" max="5" step="0.1" value="${p.speed}" style="width:100%;"></div>
                <div style="flex:1;"><label style="font-size:10px;color:#aaa;">Свечение</label><input type="range" data-key="glow" data-idx="${idx}" min="0" max="2" step="0.1" value="${p.glow || 0}" style="width:100%;"></div>
                <!-- ИСПРАВЛЕННЫЙ ИНПУТ ЦВЕТА -->
                <input type="color" data-key="color" data-idx="${idx}" value="${p.color}" style="width:24px; height:24px; cursor:pointer; padding:0; border:1px solid #555; border-radius:4px; background:#000;">
            </div>
        `;
        cont.appendChild(div);
    });

    // Привязываем события
    cont.querySelectorAll('input').forEach(inp => {
        inp.addEventListener('input', (e) => {
            const idx = e.target.getAttribute('data-idx');
            const key = e.target.getAttribute('data-key');
            currentPlanetsData[idx][key] = e.target.value;
            updatePreview(); 
        });
    });
    cont.querySelectorAll('.del-planet').forEach(btn => {
        btn.addEventListener('click', (e) => {
            currentPlanetsData.splice(e.target.getAttribute('data-idx'), 1);
            renderPlanetsUI();
            updatePreview();
        });
    });
}



document.getElementById('solar-delete-btn').addEventListener('click', async () => {
    if (confirm("Точно удалить систему?")) {
        await solarManager.deleteSystem(currentEditingSystemId);
        solarModal.style.display = 'none';
        if(solarPreview) solarPreview.stop();
        window.dispatchEvent(new CustomEvent('toggle-pause', { detail: false }));
    }
});

// =========================================================
// СИСТЕМА СОХРАНЕНИЯ И ЗАГРУЗКИ НАСТРОЕК (EXPORT / IMPORT)
// =========================================================

// Функция для сериализации CONFIG (превращаем THREE.Color в HEX-строки)
function exportConfigToJSON() {
    const exportObj = {};
    for (const [category, values] of Object.entries(CONFIG)) {
        exportObj[category] = {};
        for (const [key, val] of Object.entries(values)) {
            if (val && val.isColor) {
                exportObj[category][key] = '#' + val.getHexString();
            } else if (Array.isArray(val) && val[0]?.isColor) {
                // Специальный случай для массива цветов сфер
                exportObj[category][key] = val.map(c => '#' + c.getHexString());
            } else {
                exportObj[category][key] = val;
            }
        }
    }
    return JSON.stringify(exportObj, null, 2);
}

// Функция для парсинга и применения JSON к CONFIG
function importConfigFromJSON(jsonString) {
    try {
        const parsed = JSON.parse(jsonString);

        for (const [category, values] of Object.entries(parsed)) {
            if (CONFIG[category]) {
                for (const [key, val] of Object.entries(values)) {
                    if (CONFIG[category][key] !== undefined) {
                        if (CONFIG[category][key].isColor) {
                            CONFIG[category][key].set(val);
                        } else if (CONFIG[category][key].isVector4) {
                            // Восстанавливаем Vector4 без перезаписи инстанса класса
                            CONFIG[category][key].set(val.x, val.y, val.z, val.w);
                        } else if (Array.isArray(CONFIG[category][key]) && CONFIG[category][key][0]?.isColor) {
                                val.forEach((hex, i) => {
                                    if (CONFIG[category][key][i]) CONFIG[category][key][i].set(hex);
                                });
                            } else if (typeof CONFIG[category][key] === 'object' && !Array.isArray(CONFIG[category][key])) {
                                // --- ИСПРАВЛЕНИЕ: Глубокое слияние для shapeMods и farShapeMods ---
                                for (const [subKey, subVal] of Object.entries(val)) {
                                    if (CONFIG[category][key][subKey] !== undefined) {
                                        if (CONFIG[category][key][subKey].isVector4) {
                                            // Восстанавливаем Vector4, подставляя 0 если значение отсутствует (для старых пресетов)
                                            CONFIG[category][key][subKey].set(
                                                subVal.x || 0, 
                                                subVal.y || 0, 
                                                subVal.z || 0, 
                                                subVal.w || 0
                                            );
                                        } else {
                                            CONFIG[category][key][subKey] = subVal;
                                        }
                                    }
                                }
                            } else {
                                CONFIG[category][key] = val;
                            }
                    }
                }
            }
        }
        
        syncUIToConfig(); // Синхронизируем интерфейс с новыми данными
        
        // 1. Принудительное обновление специфических систем
        if(typeof updateBackgroundGradient === 'function') updateBackgroundGradient();
        if(typeof updateCardsOnTerrainChange === 'function') updateCardsOnTerrainChange();
        if(typeof sphereSystem !== 'undefined') sphereSystem.refresh();
        
        // 2. ИСПРАВЛЕНИЕ: Раскрытие UI менюшек для травы
        // Искусственно вызываем событие 'change', чтобы сработали скрытые слушатели
        const grassMixEl = document.getElementById('grass-mix-mode');
        if (grassMixEl) grassMixEl.dispatchEvent(new Event('change'));
        
        const grassFarMixEl = document.getElementById('grass-far-mix-mode');
        if (grassFarMixEl) grassFarMixEl.dispatchEvent(new Event('change'));
        
        if (typeof updateTurbUI === 'function') updateTurbUI();

        // 3. ИСПРАВЛЕНИЕ: Корректное применение Режима Земли
        applyGroundModeVisuals();
        
        // Полностью перестраиваем траву и камни, чтобы применились все геометрии и LOD
        if (typeof debounceGrassRebuild === 'function') debounceGrassRebuild();
        if (typeof debounceRockRebuild === 'function') debounceRockRebuild();

        alert('Настройки успешно применены!');
    } catch (e) {
        console.error("Ошибка импорта настроек:", e);
        alert('Не удалось загрузить настройки. Проверьте формат данных.');
    }
}

// Функция, которая "проходится" по всем инпутам и обновляет их согласно CONFIG
function syncUIToConfig() {
    // Карта: ID элемента -> [категория, ключ, это_чекбокс?]
    const uiMap = {
        'wind-speed': ['wind', 'speed'], 'wind-force': ['wind', 'force'], 'part-speed': ['particles', 'speed'], 'render-resolution': ['graphics', 'renderScale'],
        'sway-amp': ['motion', 'swayAmp'], 'twist-amp': ['motion', 'twistAmp'],
        'star-density': ['sky', 'starDensity'], 'star-size': ['sky', 'starSize'], 'sky-blur': ['sky', 'blur'],
        'comet-freq': ['sky', 'cometFreq'], 'slow-comet-freq': ['sky', 'slowCometFreq'],
        'dust-count': ['details', 'dustCount'], 'dust-size': ['details', 'dustSize'],
        'firefly-count': ['details', 'fireflyCount'], 'firefly-size': ['details', 'fireflySize'],
        'ui-dist-toggle': ['ui', 'showDistance', true], 'ui-chaos-toggle': ['ui', 'showChaos', true],
        'ui-auto-level': ['ui', 'autoLevel', true],
        'ui-max-cam-height': ['ui', 'maxCamHeight'],
        'grass-mouse-toggle': ['grass', 'mouseInteract', true],
        'grass-mouse-radius': ['grass', 'mouseRadius'],
        'grass-mouse-strength': ['grass', 'mouseStrength'],
        'grass-far-mix-mode': ['grass', 'farMixMode'],
        'grass-far-shape-1': ['grass', 'farShape1'],

        'rock-toggle': ['rocks', 'enabled', true],
        'rock-count': ['rocks', 'count'],
        'rock-size': ['rocks', 'size'],
        'rock-size-var': ['rocks', 'sizeVar'],
        'rock-boulder-ratio': ['rocks', 'boulderRatio'],
        'rock-shape': ['rocks', 'shape'],
        'rock-y-offset': ['rocks', 'yOffset'], // <--- ДОБАВИТЬ ЭТО
        'rock-y-spread': ['rocks', 'ySpread'], // <--- ДОБАВИТЬ ЭТО
        'rock-smooth': ['rocks', 'smoothness'],
        'rock-min-h': ['rocks', 'minHeight'],
        'rock-max-h': ['rocks', 'maxHeight'],
        'cards-toggle': ['cards', 'enabled', true],

        'sphere-trail-count': ['spheres', 'trailCount'],
        'sphere-trail-size': ['spheres', 'trailSize'],
        'sphere-trail-blur': ['spheres', 'trailBlur'],
        'sphere-trail-opacity': ['spheres', 'trailOpacity'],

        'rock-foam-opacity': ['rocks', 'rockFoamOpacity'],
        'rock-foam-height': ['rocks', 'rockFoamHeight'],

        'sphere-trail-length': ['spheres', 'trailLength'],
        'sphere-trail-speed': ['spheres', 'trailSpeed'],
        'sphere-trail-turb': ['spheres', 'trailTurbulence'],

        'foam-opacity': ['water', 'foamOpacity'],
        'foam-width': ['water', 'foamWidth'],
        'foam-count': ['water', 'foamCount'],
        'foam-spacing': ['water', 'foamSpacing'],
        'foam-noise': ['water', 'foamNoise'],
        'water-depth-factor': ['terrain', 'waterDepthFactor'],
        'terr-strata-toggle': ['terrain', 'strataEnabled', true],
        'terr-strata-freq': ['terrain', 'strataFreq'],
        'terr-strata-str': ['terrain', 'strataStrength'],
        'grass-cam-toggle': ['grass', 'cameraInteract', true],
        'grass-cam-radius': ['grass', 'cameraRadius'],
        'grass-lod-offset': ['grass', 'lodOffset'],

        'reflect-toggle': ['water', 'reflections', true],
        'reflect-res': ['water', 'resolution'],
        'reflect-intensity': ['water', 'intensity'],
        'reflect-distortion': ['water', 'distortion'],
        'grass-gust-speed': ['grass', 'gustSpeed'],

        'rock-dist': ['rocks', 'drawDistance'],
        'rock-height-bias': ['rocks', 'heightBias'],
        'rock-iris-int': ['rocks', 'crystalIrisIntensity'],
        'rock-iris-spread': ['rocks', 'crystalIrisSpread'],

        'rock-flat': ['rocks', 'flatShading'],
        'rock-ao': ['rocks', 'ao'],
        'rock-crystal-gloss': ['rocks', 'crystalGloss'],

        'rock-crystal-alpha': ['rocks', 'crystalAlpha'], 


        'clouds-toggle': ['clouds', 'enabled', true],
        'clouds-opacity': ['clouds', 'opacity'],
        'clouds-coverage': ['clouds', 'coverage'],
        'clouds-softness': ['clouds', 'softness'],
        'clouds-scale': ['clouds', 'scale'],
        'clouds-stretch': ['clouds', 'stretch'],
        'clouds-speed': ['clouds', 'speed'],
        
        'shadows-toggle': ['cloudShadows', 'enabled', true],
        'shadow-opacity': ['cloudShadows', 'opacity'],
        'shadow-coverage': ['cloudShadows', 'coverage'],
        'shadow-softness': ['cloudShadows', 'softness'],
        'shadow-scale': ['cloudShadows', 'scale'],
        'shadow-stretch': ['cloudShadows', 'stretch'],
        'shadow-speed': ['cloudShadows', 'speed'],
        // Заодно добавим пленочное зерно, его там тоже не было
        'grain-toggle': ['graphics', 'grainEnabled', true],
        'grain-opacity': ['graphics', 'grainOpacity'],

        'grass-far-shape-2': ['grass', 'farShape2'],
        'c-fog-toggle': ['terrain', 'creepingFogEnabled', true],
        'c-fog-height': ['terrain', 'creepingFogHeight'],
        'c-fog-thick': ['terrain', 'creepingFogThickness'],
        'c-fog-dens': ['terrain', 'creepingFogDensity'],
        'c-fog-shape': ['terrain', 'creepingFogShape'],
        'grass-far-shape-3': ['grass', 'farShape3'],
        'rock-shape-small': ['rocks', 'shapeSmall'],
        'rock-shape-boulder': ['rocks', 'shapeBoulder'],
        'rock-float-amp': ['rocks', 'floatAmp'],
        'rock-float-speed': ['rocks', 'floatSpeed'],
        'rock-moss-spread': ['rocks', 'mossSpread'],
        'card-size': ['cards', 'size'],
        'card-height': ['cards', 'heightOffset'],
        'card-spacing': ['cards', 'spacing'],
        'rock-struct': ['rocks', 'struct'],
        'rock-thin': ['rocks', 'thin'],
        'grass-far-alt-chance': ['grass', 'farAltChance'],
        'light-grass-toggle': ['flashlight', 'affectGrass', true],
        'light-rock-toggle': ['flashlight', 'affectRocks', true], // <--- ДОБАВЛЕНО
        'sphere-light-toggle': ['sphereLights', 'enabled', true],
        'sphere-light-rock-toggle': ['sphereLights', 'affectRocks', true], // <--- ДОБАВЛЕНО
        'sphere-light-intensity': ['sphereLights', 'intensity'],
        'far-s2-winddamp': ['grass', 'farAltChance'],
        'sphere-light-range': ['sphereLights', 'range'],
        'reflect-stretch': ['water', 'rippleStretch'],
        'reflect-blur': ['water', 'blurStrength'],
        'reflect-edge-dark': ['water', 'edgeDarkening'],
        'reflect-dist-start': ['water', 'distBlurStart'],
        'sphere-light-grass-toggle': ['sphereLights', 'affectGrass', true],
        'comet-light-grass-toggle': ['cometLights', 'affectGrass', true],
        'ui-screenshot-toggle': ['ui', 'showScreenshotBtn', true],
        'ui-screenshot-scale': ['graphics', 'screenshotScale'],
        'shore-opacity': ['water', 'shoreOpacity'],
        'sphere-move-speed': ['spheres', 'moveSpeed'],
        'rock-crystal-ratio-small': ['rocks', 'crystalRatioSmall'],
        'rock-crystal-ratio-boulder': ['rocks', 'crystalRatioBoulder'],
        'reflect-dist-blur': ['water', 'distBlurMax'],
        'grass-far-struct': ['grass', 'farStruct'],
        'terr-amp': ['terrain', 'amplitude'], 'terr-freq': ['terrain', 'frequency'],
        'terr-offset': ['terrain', 'offset'], 'terr-sharp': ['terrain', 'sharpness'],
        'terr-grid': ['terrain', 'showGrid', true], 'terr-dist': ['terrain', 'visibility'],
        'terr-fog-dens': ['terrain', 'fogDensity'], 'terr-ao': ['terrain', 'aoStrength'],

        'global-light-intensity': ['lighting', 'globalIntensity'],
        'global-max-lights': ['lighting', 'maxPointLights'],
        'global-light-dist': ['lighting', 'lightDistance'],

        'comet-light-toggle': ['cometLights', 'enabled', true],
        'comet-light-rock-toggle': ['cometLights', 'affectRocks', true],
        'comet-light-intensity': ['cometLights', 'intensity'],
        'comet-light-range': ['cometLights', 'range'],
        'terr-smooth': ['terrain', 'smoothing'],
        'grass-toggle': ['grass', 'enabled', true], 'grass-count': ['grass', 'count'],
        'grass-shape-1': ['grass', 'shape1'], 'grass-shape-2': ['grass', 'shape2'], 'grass-shape-3': ['grass', 'shape3'], 'grass-shape-4': ['grass', 'shape4'],
        'grass-mix-mode': ['grass', 'mixMode'], 'grass-smooth': ['grass', 'smoothness'],
        's2-chance': ['grass', 'altChance2'], 's2-struct': ['grass', 'struct2'], 's2-thin': ['grass', 'thin2'],
        's3-chance': ['grass', 'altChance3'], 's3-struct': ['grass', 'struct3'], 's3-thin': ['grass', 'thin3'],
        's4-chance': ['grass', 'altChance4'], 's4-struct': ['grass', 'struct4'], 's4-thin': ['grass', 'thin4'],
        'far-s2-chance': ['grass', 'farAltChance2'], 'far-s2-struct': ['grass', 'farStruct2'], 'far-s2-thin': ['grass', 'farThin2'],
        'far-s3-chance': ['grass', 'farAltChance3'], 'far-s3-struct': ['grass', 'farStruct3'], 'far-s3-thin': ['grass', 'farThin3'],
        'grass-min-h': ['grass', 'minHeight'], 'grass-max-h': ['grass', 'maxHeight'],
        'grass-cluster-thresh': ['grass', 'clusterThreshold'], 'grass-color-var': ['grass', 'colorVar'],
        'grass-size-var': ['grass', 'sizeVar'], 'grass-shape-var': ['grass', 'shapeVar'],
        'grass-height': ['grass', 'height'], 'grass-bend': ['grass', 'bend'],
        'grass-bend-angle': ['grass', 'bendAngle'], 'grass-bend-chaos': ['grass', 'bendChaos'],
        'grass-distance': ['grass', 'drawDistance'], 'grass-fog-mult': ['grass', 'fogDensityMult'],
        'grass-wind-speed': ['grass', 'windSpeed'], 'grass-sway': ['grass', 'swayStrength'],
        'grass-turb': ['grass', 'turbulence'], 'grass-turb-amp': ['grass', 'turbAmp'],
        'grass-turb-speed': ['grass', 'turbSpeed'], 'grass-gust-str': ['grass', 'gustStrength'],
        'grass-gust-size': ['grass', 'gustSize'], 'grass-gust-freq': ['grass', 'gustFreq'], 'grass-gust-smooth': ['grass', 'gustSmoothness'], 'grass-gust-arc': ['grass', 'gustArc'],
        'grass-wind-chaos': ['grass', 'windChaos'], 'grass-lod-toggle': ['grass', 'lodEnabled', true],
        'grass-far-dist': ['grass', 'farDistance'], 'grass-far-count': ['grass', 'farCount'],
        'grass-far-size': ['grass', 'farSizeMult'],
        'light-toggle': ['flashlight', 'enabled', true], 'light-intensity': ['flashlight', 'intensity'],
        'light-radius': ['flashlight', 'radius'],
        'light-anim-amp': ['flashlight', 'animAmp'],
        'light-anim-speed': ['flashlight', 'animSpeed'],
        'reflect-rocks-toggle': ['water', 'reflectRocks', true],
        'reflect-clouds-toggle': ['water', 'reflectClouds', true],
        'light-range': ['flashlight', 'range'],
        'const-dot-size': ['constellation', 'dotSize'], 'const-line-width': ['constellation', 'lineWidth'],
        'const-glow-str': ['constellation', 'glowStr'],
        'sphere-count': ['spheres', 'count'], 'sphere-size': ['spheres', 'baseSize'],
        'proxy-toggle': ['network', 'useProxy', true]
    };

    const colorMap = {
        'col-bot': ['colors', 'bottom'], 'col-mid': ['colors', 'mid'], 'col-top': ['colors', 'top'],
        'col-fire': ['colors', 'firefly'], 'col-grass': ['terrain', 'grassColor'],
        'col-cfog': ['terrain', 'creepingFogColor'],
        'col-rock-base': ['rocks', 'baseColor'],
        'col-crystal-base': ['rocks', 'crystalBaseColor'],
        'col-crystal-tip': ['rocks', 'crystalTipColor'],
        'col-rock-tip': ['rocks', 'tipColor'],
        'col-foam': ['water', 'foamColor'],
        'col-cloud-zenith': ['clouds', 'colorZenith'],
        'col-rock-moss': ['rocks', 'mossColor'],
        'col-cloud-horizon': ['clouds', 'colorHorizon'],
        'col-shadow': ['cloudShadows', 'color'],
        'col-shore': ['water', 'shoreColor'],
        'col-water-deep': ['terrain', 'deepWaterColor'],
        'col-water': ['terrain', 'waterColor'], 'col-peak': ['terrain', 'peakColor'],
        'col-terr-fog': ['terrain', 'fogColor'], 'col-snow': ['terrain', 'snowColor'],
        'col-grass-base': ['grass', 'baseColor'], 'col-grass-tip': ['grass', 'tipColor'],
        'col-grass-base-2': ['grass', 'baseColor2'], 'col-grass-tip-2': ['grass', 'tipColor2'],
        'col-grass-base-3': ['grass', 'baseColor3'], 'col-grass-tip-3': ['grass', 'tipColor3'], 'col-grass-base-4': ['grass', 'baseColor4'], 'col-grass-tip-4': ['grass', 'tipColor4'],
        'col-light': ['flashlight', 'color'], 'col-constellation': ['constellation', 'color']
    };



    // Обновляем ползунки и чекбоксы
    for (const [id, path] of Object.entries(uiMap)) {
        const el = document.getElementById(id);
        if (!el) continue;
        const val = CONFIG[path[0]][path[1]];

        if (path[2]) { // Чекбокс
            if (el.checked !== val) {
                el.checked = val;
                el.dispatchEvent(new Event('change', { bubbles: true }));
            }
        } else { // Ползунок
            if (el.value != val) {
                el.value = val;
                el.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
    }

    // Обновляем одиночные цвета
    for (const [id, path] of Object.entries(colorMap)) {
        const el = document.getElementById(id);
        if (!el) continue;
        const hex = '#' + CONFIG[path[0]][path[1]].getHexString();
        if (el.value !== hex) {
            el.value = hex;
            el.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }

    // Обновляем цвета сфер (массив)
    for (let i = 0; i < 3; i++) {
        const el = document.getElementById(`sphere-col-${i + 1}`);
        if (!el) continue;
        const hex = '#' + CONFIG.spheres.colors[i].getHexString();
        if (el.value !== hex) {
            el.value = hex;
            el.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }
     for (let i = 1; i <= 4; i++) {
         const comp = i === 1 ? 'x' : i === 2 ? 'y' : i === 3 ? 'z' : 'w';
         
         const sizeEl = document.getElementById(`s${i}-size`);
         if (sizeEl) {
             sizeEl.value = CONFIG.grass.shapeMods.size[comp];
             sizeEl.dispatchEvent(new Event('input', { bubbles: true }));
         }
         
         const widthEl = document.getElementById(`s${i}-width`);
         if (widthEl) {
             widthEl.value = CONFIG.grass.shapeMods.width[comp];
             widthEl.dispatchEvent(new Event('input', { bubbles: true }));
         }

         // --- ДОБАВЬТЕ ЭТОТ БЛОК ДЛЯ СИНХРОНИЗАЦИИ ОСЛАБЛЕНИЯ ВЕТРА ---
         const farWindDampEl = document.getElementById(`far-s${i}-winddamp`);
         if (farWindDampEl && CONFIG.grass.farShapeMods.windDamp) {
             farWindDampEl.value = CONFIG.grass.farShapeMods.windDamp[comp] || 0;
             farWindDampEl.dispatchEvent(new Event('input', { bubbles: true }));
         }
     }

     // И для дальних форм (LOD 2 и 3)
     for (let i = 2; i <= 3; i++) {
         const comp = i === 2 ? 'y' : 'z';
         
         const farSizeEl = document.getElementById(`far-s${i}-size`);
         if (farSizeEl) {
             farSizeEl.value = CONFIG.grass.farShapeMods.size[comp];
             farSizeEl.dispatchEvent(new Event('input', { bubbles: true }));
         }
         
         const farWidthEl = document.getElementById(`far-s${i}-width`);
         if (farWidthEl) {
             farWidthEl.value = CONFIG.grass.farShapeMods.width[comp];
             farWidthEl.dispatchEvent(new Event('input', { bubbles: true }));
         }

         // --- ДОБАВЬТЕ ЭТОТ БЛОК ДЛЯ СИНХРОНИЗАЦИИ ОСЛАБЛЕНИЯ ВЕТРА LOD ---
         const farWindDampEl = document.getElementById(`far-s${i}-winddamp`);
         if (farWindDampEl) {
             farWindDampEl.value = CONFIG.grass.farShapeMods.windDamp[comp];
             farWindDampEl.dispatchEvent(new Event('input', { bubbles: true }));
         }
     }

}
// =========================================================
// СИСТЕМА ПРЕСЕТОВ ПЛАНЕТ ИЗ ВЫПАДАЮЩИХ СПИСКОВ
// =========================================================
function initPresetsSystem() {
    const selectNoFlora = document.getElementById('preset-no-flora');
    const selectFlora = document.getElementById('preset-flora');

    if (!selectNoFlora || !selectFlora) return;

    // 1. Заполняем список "Без флоры"
    PLANET_PRESETS.noFlora.forEach((preset, index) => {
        const option = document.createElement('option');
        option.value = `noFlora_${index}`;
        option.textContent = preset.name;
        selectNoFlora.appendChild(option);
    });

    // 2. Заполняем список "С флорой" (Легкие)
    PLANET_PRESETS.flora.forEach((preset, index) => {
        const option = document.createElement('option');
        option.value = `flora_${index}`;
        option.textContent = preset.name;
        selectFlora.appendChild(option);
    });

    // 3. Добавляем "Тяжелые пресеты" в тот же список через <optgroup>
    if (PLANET_PRESETS.heavyFlora && PLANET_PRESETS.heavyFlora.length > 0) {
        const optgroup = document.createElement('optgroup');
        optgroup.label = "▬▬ ТЯЖЕЛЫЕ ПРЕСЕТЫ (-FPS) ▬▬";
        optgroup.style.color = "#ff6666"; // Красный заголовок группы

        PLANET_PRESETS.heavyFlora.forEach((preset, index) => {
            const option = document.createElement('option');
            option.value = `heavyFlora_${index}`;
            option.textContent = preset.name;
            option.style.color = "#ffffff"; // Возвращаем белый цвет самому пресету
            optgroup.appendChild(option);
        });
        selectFlora.appendChild(optgroup);
    }

    // Обработчик загрузки пресета
    const applyPreset = (groupName, index) => {
        const preset = PLANET_PRESETS[groupName][index];
        if (preset && preset.data) {
            // Превращаем JS-объект пресета в JSON строку и отдаем вашей рабочей функции
            const jsonString = JSON.stringify(preset.data);
            importConfigFromJSON(jsonString);
            
            // Если в вашей функции importConfigFromJSON есть alert('Успешно'), 
            // вы можете убрать его оттуда и сделать кастомные уведомления, либо оставить как есть.
        }
    };

    // Слушатели переключения
    selectNoFlora.addEventListener('change', (e) => {
        if (!e.target.value) return;
        const [group, index] = e.target.value.split('_');
        selectFlora.value = ""; // Сбрасываем второй список (чтобы визуально активен был один)
        applyPreset(group, parseInt(index));
    });

    selectFlora.addEventListener('change', (e) => {
        if (!e.target.value) return;
        const [group, index] = e.target.value.split('_');
        selectNoFlora.value = ""; // Сбрасываем первый список
        applyPreset(group, parseInt(index));
    });
}

// Запускаем инициализацию при загрузке DOM
document.addEventListener('DOMContentLoaded', initPresetsSystem);
// ПРИВЯЗКА КНОПОК
document.addEventListener('DOMContentLoaded', () => {
    // 1. СОХРАНИТЬ В ФАЙЛ
    const saveBtn = document.getElementById('cfg-save-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(exportConfigToJSON());
            const downloadAnchorNode = document.createElement('a');
            downloadAnchorNode.setAttribute("href", dataStr);
            downloadAnchorNode.setAttribute("download", "anemone_preset.json");
            document.body.appendChild(downloadAnchorNode);
            downloadAnchorNode.click();
            downloadAnchorNode.remove();
        });
    }

    // 2. ЗАГРУЗИТЬ ИЗ ФАЙЛА
    const loadBtn = document.getElementById('cfg-load-btn');
    const fileInput = document.getElementById('cfg-file-input');
    if (loadBtn && fileInput) {
        loadBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (event) => importConfigFromJSON(event.target.result);
            reader.readAsText(file);
            fileInput.value = ''; // Сбрасываем инпут
        });
    }

    // 3. КОПИРОВАТЬ В БУФЕР
    const copyBtn = document.getElementById('cfg-copy-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(exportConfigToJSON())
                .then(() => {
                    const originalText = copyBtn.innerText;
                    copyBtn.innerText = "Скопировано!";
                    copyBtn.style.borderColor = "#44ff44";
                    setTimeout(() => {
                        copyBtn.innerText = originalText;
                        copyBtn.style.borderColor = "rgba(255,255,255,0.2)";
                    }, 2000);
                })
                .catch(err => alert("Не удалось скопировать. Нажмите 'Сохранить файл'."));
        });
    }

    // 4. ВСТАВИТЬ ИЗ БУФЕРА
    const pasteBtn = document.getElementById('cfg-paste-btn');
    if (pasteBtn) {
        pasteBtn.addEventListener('click', () => {
            navigator.clipboard.readText()
                .then(text => {
                    if (!text || !text.includes('{')) throw new Error("Буфер пуст или не содержит настроек");
                    importConfigFromJSON(text);
                })
                .catch(err => alert("Не удалось вставить настройки из буфера обмена. Убедитесь, что вы скопировали корректный код."));
        });
    }
});
