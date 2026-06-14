export const PLANET_PRESETS = {
    // 1. ПРЕСЕТЫ БЕЗ РАСТИТЕЛЬНОСТИ
    noFlora: [
        {
            name: "Безжизненный Марс",
            data: {
                // ПРИМЕР: Сюда вставляете скопированный JSON пресета
                "colors": {
                    "bottom": "#3d1e1e",
                    "mid": "#210f0f",
                    "top": "#000000"
                },
                "grass": {
                    "enabled": false
                }
                // ... и так далее
            }
        },
        {
            name: "Ледяной спутник",
            data: {
                // Вставляете настройки...
            }
        }
    ],

    // 2. ПРЕСЕТЫ С ФЛОРОЙ (Легкие/Средние)
    flora: [
        {
            name: "Зеленая Долина",
            data: {
                  "colors": {
                    "bottom": "#fff2c4",
                    "mid": "#7490e3",
                    "top": "#aab8f0",
                    "firefly": "#ffaa00"
                  },
                  "graphics": {
                    "renderScale": 0.8,
                    "screenshotScale": 2,
                    "grainEnabled": true,
                    "grainOpacity": 0.11
                  },
                  "wind": {
                    "speed": 0.2,
                    "force": 0.2
                  },
                  "particles": {
                    "speed": 0.2
                  },
                  "motion": {
                    "swayAmp": 0.1,
                    "twistAmp": 0.29
                  },
                  "sky": {
                    "starDensity": 8100,
                    "starSize": 1.1,
                    "blur": 0,
                    "cometFreq": 0.014,
                    "slowCometFreq": 0
                  },
                  "details": {
                    "dustCount": 800,
                    "dustSize": 1.1,
                    "fireflyCount": 240,
                    "fireflySize": 0.9
                  },
                  "flashlight": {
                    "enabled": false,
                    "color": "#ffffff",
                    "intensity": 2,
                    "range": 2000,
                    "affectGrass": false,
                    "affectRocks": false,
                    "radius": 0.51,
                    "animAmp": 0.25,
                    "animSpeed": 2.6
                  },
                  "sphereLights": {
                    "enabled": false,
                    "affectRocks": false,
                    "intensity": 1.5,
                    "range": 800
                  },
                  "rocks": {
                    "enabled": true,
                    "count": 1000,
                    "size": 3,
                    "sizeVar": 0.6,
                    "baseColor": "#1a1a24",
                    "tipColor": "#4a5568",
                    "crystalBaseColor": "#2a1538",
                    "crystalTipColor": "#9b59b6",
                    "smoothness": 1,
                    "minHeight": 0,
                    "maxHeight": 120,
                    "boulderRatio": 0.05,
                    "flatShading": 0,
                    "ao": 0.5,
                    "crystalGloss": 0,
                    "crystalAlpha": 0,
                    "crystalRatioSmall": 0,
                    "crystalRatioBoulder": 0,
                    "heightBias": 0.5,
                    "crystalIrisSpread": 0.5,
                    "crystalIrisIntensity": 0,
                    "shapeSmall": 0.5,
                    "shapeBoulder": 0.5,
                    "struct": 0.5,
                    "thin": 0,
                    "drawDistance": 2500,
                    "yOffset": -1,
                    "ySpread": 0,
                    "rockFoamOpacity": 0,
                    "rockFoamHeight": 10,
                    "shape": 0.5
                  },
                  "water": {
                    "reflections": false,
                    "resolution": 512,
                    "intensity": 0.6,
                    "distortion": 0.03,
                    "rippleStretch": 2,
                    "blurStrength": 0,
                    "edgeDarkening": 0.4,
                    "distBlurStart": 800,
                    "distBlurMax": 0,
                    "foamOpacity": 0,
                    "foamColor": "#ffffff",
                    "foamWidth": 10,
                    "foamCount": 2,
                    "foamSpacing": 5,
                    "foamNoise": 0.5,
                    "shoreOpacity": 0.5,
                    "shoreColor": "#aaddff"
                  },
                  "ui": {
                    "showDistance": false,
                    "showChaos": false,
                    "groundMode": true,
                    "autoLevel": false,
                    "showScreenshotBtn": true
                  },
                  "chaos": {
                    "radius": 4000
                  },
                  "terrain": {
                    "grassColor": "#dbd2bd",
                    "waterColor": "#ffeecf",
                    "peakColor": "#523d3d",
                    "fogColor": "#898891",
                    "snowColor": "#ffffff",
                    "amplitude": 95,
                    "frequency": 0.0021,
                    "offset": 30,
                    "sharpness": 1,
                    "showGrid": false,
                    "visibility": 5900,
                    "fogDensity": 0.0005,
                    "aoStrength": 0.6,
                    "smoothing": 0.51,
                    "creepingFogEnabled": true,
                    "creepingFogColor": "#0a1b2a",
                    "creepingFogHeight": 5,
                    "creepingFogThickness": 30,
                    "creepingFogDensity": 0.8,
                    "creepingFogShape": 0.7
                  },
                  "grass": {
                    "enabled": true,
                    "count": 110000,
                    "shape1": 6,
                    "shape2": 5,
                    "shape3": 2,
                    "shape4": 4,
                    "shapeMods": {
                      "size": {
                        "x": 1,
                        "y": 0.6,
                        "z": 1,
                        "w": 1
                      },
                      "width": {
                        "x": 0.7,
                        "y": 0.4,
                        "z": 1,
                        "w": 1
                      },
                      "sizeVar": {
                        "x": 0.25,
                        "y": 0.55,
                        "z": 0.25,
                        "w": 0.25
                      },
                      "colorVar": {
                        "x": 0,
                        "y": 0.4,
                        "z": 0.4,
                        "w": 0.4
                      }
                    },
                    "farShapeMods": {
                      "size": {
                        "x": 1,
                        "y": 0.5,
                        "z": 1,
                        "w": 1
                      },
                      "width": {
                        "x": 0.7,
                        "y": 1.9,
                        "z": 1,
                        "w": 1
                      }
                    },
                    "mouseInteract": true,
                    "mouseRadius": 57,
                    "mouseStrength": 1.5,
                    "mixMode": 1,
                    "altChance2": 1,
                    "altChance3": 0.3,
                    "altChance4": 0.3,
                    "struct2": 0.7,
                    "struct3": 0.5,
                    "struct4": 0.5,
                    "thin2": 0.6,
                    "thin3": 0,
                    "thin4": 0,
                    "baseColor": "#2e3f47",
                    "tipColor": "#8a96b0",
                    "baseColor2": "#3f3a0a",
                    "tipColor2": "#b6b8ff",
                    "baseColor3": "#0a1f3f",
                    "tipColor3": "#3060b0",
                    "baseColor4": "#1f3f0a",
                    "tipColor4": "#ffffff",
                    "smoothness": 1.7,
                    "minHeight": 2,
                    "maxHeight": 40,
                    "clusterFreq": 0.05,
                    "clusterThreshold": 0.4,
                    "colorVar": 0.4,
                    "sizeVar": 0.25,
                    "shapeVar": 0.5,
                    "height": 17,
                    "bend": 0,
                    "bendAngle": 3.5,
                    "bendChaos": 0,
                    "drawDistance": 4000,
                    "fogDensityMult": 1.5,
                    "windSpeed": 0.6,
                    "swayStrength": 0.45,
                    "turbulence": 0.2,
                    "turbAmp": 1,
                    "turbSpeed": 1.5,
                    "gustStrength": 1,
                    "gustSize": 180,
                    "gustFreq": 1,
                    "gustSmoothness": 1,
                    "gustArc": 0.1,
                    "gustSpeed": 1.9,
                    "windChaos": 0,
                    "lodEnabled": true,
                    "farDistance": 12000,
                    "farCount": 40000,
                    "farSizeMult": 2.5,
                    "farMixMode": 1,
                    "farShape1": 6,
                    "farShape2": 8,
                    "farShape3": 8,
                    "farAltChance2": 1,
                    "farAltChance3": 0.2,
                    "farStruct2": 1,
                    "farStruct3": 0.5,
                    "farThin2": 0.4,
                    "farThin3": 0
                  },
                  "constellation": {
                    "color": "#ff5e00",
                    "dotSize": 4,
                    "lineWidth": 0.5,
                    "glowStr": 0
                  },
                  "spheres": {
                    "count": 3,
                    "baseSize": 45,
                    "moveSpeed": 1,
                    "speed": 0.2,
                    "colors": [
                      "#ff0055",
                      "#00ccff",
                      "#ffcc00"
                    ],
                    "trailCount": 0,
                    "trailSize": 40,
                    "trailBlur": 1.5,
                    "trailOpacity": 1,
                    "trailLength": 1,
                    "trailSpeed": 1,
                    "trailTurbulence": 0
                  },
                  "network": {
                    "useProxy": false
                  }
            }
        }
    ],

    // 3. ТЯЖЕЛЫЕ ПРЕСЕТЫ С ФЛОРОЙ (Будут отделены заголовком)
    heavyFlora: [
        {
            name: "Инопланетные джунгли (Ультра)",
            data: {
                // Вставляете настройки...
            }
        }
    ]
};