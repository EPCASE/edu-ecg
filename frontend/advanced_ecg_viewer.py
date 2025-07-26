import os

def create_advanced_ecg_viewer(image_path, title, container_width=None):
    """
    Génère le HTML complet pour le visualiseur ECG avancé (SECUREV1) :
    - Responsive
    - Affichage toujours entier sans scroll
    - Zoom molette
    - Caliper avancé avec mesures précises
    """
    import base64
    from PIL import Image
    import io

    # Charger et encoder l'image
    if isinstance(image_path, str):
        with open(image_path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode()
        image = Image.open(image_path)
    else:
        img_buffer = io.BytesIO()
        image_path.save(img_buffer, format="PNG")
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        image = image_path

    img_width, img_height = image.size
    aspect_ratio = img_height / img_width

    if container_width is not None:
        available_width = container_width
    else:
        available_width = 1400

    natural_height = int(available_width * aspect_ratio)

    if container_width is not None:
        final_width = available_width
        final_height = natural_height
    else:
        final_width = available_width
        final_height = natural_height
        if final_height > 2000:
            final_height = 2000
            final_width = int(final_height / aspect_ratio)

    final_height = max(250, final_height)
    viewer_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8'>
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            width: 100vw;
            height: 100vh;
            box-sizing: border-box;
            background: transparent;
            overflow: hidden;
        }}
        .ecg-viewer-container {{
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            width: 100vw;
            height: 100vh;
            margin: 0;
            border: none;
            border-radius: 0;
            overflow: hidden;
            background: transparent;
            box-shadow: none;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .ecg-viewer-canvas {{
            width: 100vw;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            cursor: crosshair;
        }}
        .ecg-image {{
            max-width: 100vw;
            max-height: 100vh;
            width: auto;
            height: auto;
            object-fit: contain;
            user-drag: none;
            user-select: none;
            pointer-events: none;
            display: block;
            transform-origin: center center;
            transition: transform 0.1s ease-out;
        }}
        .caliper-line {{
            position: absolute;
            background: #ff0000;
            z-index: 20;
            display: none;
            pointer-events: none;
        }}
        .caliper-line.main {{
            height: 2px;
        }}
        .caliper-end-bar {{
            position: absolute;
            background: #ff0000;
            z-index: 21;
            display: none;
            pointer-events: none;
        }}
        .caliper-end-bar.vertical {{
            width: 2px;
            height: 12px;
            margin-top: -6px;
        }}
        .caliper-end-bar.horizontal {{
            width: 12px;
            height: 2px;
            margin-left: -6px;
        }}
        .measure-label {{
            position: absolute;
            background: rgba(255,255,255,0.95);
            color: #000;
            border: 1px solid #ff0000;
            border-radius: 4px;
            padding: 4px 8px;
            font-family: monospace;
            font-size: 12px;
            font-weight: bold;
            z-index: 22;
            display: none;
            white-space: nowrap;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            pointer-events: none;
        }}
        .zoom-info {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
            z-index: 100;
            transition: opacity 0.3s ease;
        }}
        .zoom-info.hidden {{
            opacity: 0;
        }}
        .help-info {{
            position: absolute;
            bottom: 10px;
            left: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 11px;
            z-index: 100;
            line-height: 1.4;
            transition: opacity 0.3s ease;
        }}
        .help-info.hidden {{
            opacity: 0;
        }}
        .calibration-info {{
            position: absolute;
            top: 10px;
            left: 60px;
            background: rgba(255,0,0,0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
            font-weight: bold;
            z-index: 101;
            display: none;
            transition: opacity 0.3s ease;
        }}
        .calibration-info.hidden {{
            opacity: 0 !important;
        }}
        .mini-toolbar {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(255,255,255,0.98);
            border: 1px solid rgba(0,0,0,0.1);
            border-radius: 12px;
            padding: 8px;
            display: flex;
            gap: 8px;
            z-index: 100;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1), 0 1px 3px rgba(0,0,0,0.08);
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            opacity: 1;
        }}
        .mini-toolbar.hidden {{
            opacity: 0;
            pointer-events: none;
        }}
        .toolbar-btn {{
            width: 40px;
            height: 40px;
            border: 1px solid rgba(0,0,0,0.08);
            border-radius: 10px;
            background: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            transition: all 0.2s ease;
            color: #444;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-weight: 500;
            position: relative;
            overflow: hidden;
        }}
        .toolbar-btn::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, transparent, rgba(0,0,0,0.03));
            opacity: 0;
            transition: opacity 0.2s ease;
        }}
        .toolbar-btn:hover {{
            background: #f8f9fa;
            border-color: rgba(0,0,0,0.12);
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .toolbar-btn:hover::before {{
            opacity: 1;
        }}
        .toolbar-btn:active {{
            transform: translateY(0);
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }}
        .toolbar-btn.active {{
            background: linear-gradient(135deg, #ff6b6b, #ff5252);
            color: white;
            border-color: transparent;
            box-shadow: 0 2px 8px rgba(255,82,82,0.3);
        }}
        .toolbar-btn.active:hover {{
            background: linear-gradient(135deg, #ff5252, #ff4444);
            box-shadow: 0 4px 12px rgba(255,82,82,0.4);
        }}
        .toolbar-separator {{
            width: 1px;
            height: 24px;
            background: rgba(0,0,0,0.1);
            margin: 0 4px;
            align-self: center;
        }}
        .toolbar-btn .icon {{
            font-size: 18px;
            line-height: 1;
        }}
        .toolbar-btn .tooltip {{
            position: absolute;
            bottom: -32px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 12px;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s ease;
            z-index: 1000;
        }}
        .toolbar-btn:hover .tooltip {{
            opacity: 1;
        }}
        .fullscreen-mode .mini-toolbar {{
            background: rgba(30,30,30,0.9);
            border-color: rgba(255,255,255,0.1);
        }}
        .fullscreen-mode .toolbar-btn {{
            background: rgba(50,50,50,0.9);
            color: #ddd;
            border-color: rgba(255,255,255,0.1);
        }}
        .fullscreen-mode .toolbar-btn:hover {{
            background: rgba(70,70,70,0.9);
            border-color: rgba(255,255,255,0.2);
        }}
    </style>
</head>
<body>
    <div class="ecg-viewer-container" id="viewer-container">
        <div class="ecg-viewer-canvas" id="canvas">
            <img class="ecg-image" id="ecg-img" src="data:image/png;base64,{img_base64}" alt="{title}" draggable="false">
            <div id="caliper" style="position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:10;">
                <div id="caliper-line" class="caliper-line main"></div>
                <div id="caliper-start-bar" class="caliper-end-bar"></div>
                <div id="caliper-end-bar" class="caliper-end-bar"></div>
                <div id="measure-label" class="measure-label"></div>
            </div>
            <div class="mini-toolbar">
                <button class="toolbar-btn" id="calibration-btn" title="Mode calibration 1000ms">
                    <span class="icon">📏</span>
                    <span class="tooltip">Calibration 1000ms</span>
                </button>
                <div class="toolbar-separator"></div>
                <button class="toolbar-btn" id="fullscreen-btn" title="Mode plein écran">
                    <span class="icon">⛶</span>
                    <span class="tooltip">Plein écran</span>
                </button>
            </div>
            <div id="zoom-info" class="zoom-info">Zoom: 100%</div>
            <div id="calibration-info" class="calibration-info">MODE CALIBRATION - Mesurez 1000 ms (5 grands carreaux)</div>
            <div id="help-info" class="help-info">
                Clic gauche : Zoom | Clic droit : Mesurer | Double-clic : Reset
            </div>
        </div>
    </div>
    <script>
    // Configuration ECG
    let ECG_CONFIG = {{
        pixelsPerMm: 3.78,  // Standard ECG: 1mm = 3.78 pixels (sera ajusté par calibration)
        mmPerMv: 10,        // Standard ECG: 10mm = 1mV
        paperSpeed: 25,     // Standard: 25mm/s
        gridSize: 5         // 5mm major grid
    }};
    
    // Variables globales
    let calibrationMode = false;
    let calibrationMeasurement = null;
    let scale = 1.0;
    let zoomEnabled = false;
    let caliperActive = false;
    let caliperStart = null;
    let caliperEnd = null;
    let caliperPersistent = false;
    let caliperDragging = false;
    let dragOffset = null;
    let resetTimeout = null;
    let isFullscreen = false;
    let hideUITimeout = null;
    let isUIHidden = false;
    
    // Constantes
    const MIN_SCALE = 0.5;
    const MAX_SCALE = 5.0;
    const ZOOM_SPEED = 0.1;
    const HIDE_UI_DELAY = 3000;
    
    // Fonction pour masquer l'interface
    function hideUI() {{
        if (!isUIHidden) {{
            isUIHidden = true;
            document.getElementById('zoom-info').classList.add('hidden');
            document.getElementById('help-info').classList.add('hidden');
            const calibInfo = document.getElementById('calibration-info');
            if (calibInfo.style.display !== 'none') {{
                calibInfo.classList.add('hidden');
            }}
            document.querySelector('.mini-toolbar').style.opacity = '0.3';
            document.getElementById('canvas').style.cursor = 'none';
        }}
    }}
    
    // Fonction pour afficher l'interface
    function showUI() {{
        if (isUIHidden) {{
            isUIHidden = false;
            document.getElementById('zoom-info').classList.remove('hidden');
            document.getElementById('help-info').classList.remove('hidden');
            document.getElementById('calibration-info').classList.remove('hidden');
            document.querySelector('.mini-toolbar').style.opacity = '1';
            document.getElementById('canvas').style.cursor = 'crosshair';
        }}
        
        if (hideUITimeout) {{
            clearTimeout(hideUITimeout);
        }}
        
        if (!caliperActive && !caliperDragging && !calibrationMode) {{
            hideUITimeout = setTimeout(hideUI, HIDE_UI_DELAY);
        }}
    }}
    
    // Fonction pour basculer le plein écran
    function toggleFullscreen() {{
        const viewerContainer = document.getElementById('viewer-container');
        if (!isFullscreen) {{
            if (viewerContainer.requestFullscreen) {{
                viewerContainer.requestFullscreen();
            }} else if (viewerContainer.webkitRequestFullscreen) {{
                viewerContainer.webkitRequestFullscreen();
            }} else if (viewerContainer.msRequestFullscreen) {{
                viewerContainer.msRequestFullscreen();
            }}
        }} else {{
            if (document.exitFullscreen) {{
                document.exitFullscreen();
            }} else if (document.webkitExitFullscreen) {{
                document.webkitExitFullscreen();
            }} else if (document.msExitFullscreen) {{
                document.msExitFullscreen();
            }}
        }}
    }}
    
    function handleFullscreenChange() {{
        isFullscreen = !!(document.fullscreenElement || 
                         document.webkitFullscreenElement || 
                         document.msFullscreenElement);
        
        const fullscreenBtn = document.getElementById('fullscreen-btn');
        if (isFullscreen) {{
            fullscreenBtn.innerHTML = '<span class="icon">⛶</span><span class="tooltip">Quitter plein écran</span>';
            document.body.classList.add('fullscreen-mode');
        }} else {{
            fullscreenBtn.innerHTML = '<span class="icon">⛶</span><span class="tooltip">Plein écran</span>';
            document.body.classList.remove('fullscreen-mode');
        }}
    }}
    
    function updateTransform() {{
        document.getElementById('ecg-img').style.transform = 'scale(' + scale + ')';
        document.getElementById('zoom-info').textContent = 'Zoom: ' + Math.round(scale * 100) + '%';
    }}
    
    function setCaliperVisible(visible) {{
        const display = visible ? 'block' : 'none';
        document.getElementById('caliper-line').style.display = display;
        document.getElementById('caliper-start-bar').style.display = display;
        document.getElementById('caliper-end-bar').style.display = display;
        document.getElementById('measure-label').style.display = display;
    }}
    
    function updateCaliper(x1, y1, x2, y2) {{
        y2 = y1;
        const dx = x2 - x1;
        const length = Math.abs(dx);
        
        const caliperLine = document.getElementById('caliper-line');
        caliperLine.style.left = Math.min(x1, x2) + 'px';
        caliperLine.style.top = (y1 - 1) + 'px';
        caliperLine.style.width = length + 'px';
        caliperLine.style.height = '2px';
        
        const caliperStartBar = document.getElementById('caliper-start-bar');
        caliperStartBar.className = 'caliper-end-bar vertical';
        caliperStartBar.style.left = (x1 - 1) + 'px';
        caliperStartBar.style.top = y1 + 'px';
        
        const caliperEndBar = document.getElementById('caliper-end-bar');
        caliperEndBar.className = 'caliper-end-bar vertical';
        caliperEndBar.style.left = (x2 - 1) + 'px';
        caliperEndBar.style.top = y2 + 'px';
        
        const pixelDistance = length / scale;
        const mmDistance = pixelDistance / ECG_CONFIG.pixelsPerMm;
        const timeMs = mmDistance * 40;
        
        const measureLabel = document.getElementById('measure-label');
        if (calibrationMode) {{
            measureLabel.textContent = 'Calibration: ' + timeMs.toFixed(0) + ' ms (cible: 1000 ms)';
            measureLabel.style.background = 'rgba(255,200,0,0.95)';
            calibrationMeasurement = {{ pixels: pixelDistance, targetMs: 1000 }};
        }} else {{
            measureLabel.textContent = timeMs.toFixed(0) + ' ms';
            measureLabel.style.background = 'rgba(255,255,255,0.95)';
        }}
        
        measureLabel.style.left = ((x1 + x2) / 2 - 50) + 'px';
        measureLabel.style.top = (y1 - 30) + 'px';
        
        if (!caliperActive) {{
            caliperStart = {{x: x1, y: y1}};
            caliperEnd = {{x: x2, y: y2}};
        }}
    }}
    
    function resetCaliper() {{
        if (resetTimeout) {{
            clearTimeout(resetTimeout);
            resetTimeout = null;
        }}
        caliperActive = false;
        caliperStart = null;
        caliperEnd = null;
        caliperPersistent = false;
        setCaliperVisible(false);
    }}
    
    function isClickOnCaliper(x, y) {{
        if (!caliperPersistent || !caliperStart || !caliperEnd) return false;
        const minX = Math.min(caliperStart.x, caliperEnd.x) - 10;
        const maxX = Math.max(caliperStart.x, caliperEnd.x) + 10;
        const minY = caliperStart.y - 20;
        const maxY = caliperStart.y + 20;
        return x >= minX && x <= maxX && y >= minY && y <= maxY;
    }}
    
    // Initialisation des événements
    document.addEventListener('DOMContentLoaded', function() {{
        const canvas = document.getElementById('canvas');
        const toolbar = document.querySelector('.mini-toolbar');
        
        // Événements de souris pour UI
        canvas.addEventListener('mousemove', showUI);
        canvas.addEventListener('mouseenter', showUI);
        
        canvas.addEventListener('mouseleave', function(e) {{
            if (hideUITimeout) clearTimeout(hideUITimeout);
            if (!caliperActive && !caliperDragging) hideUI();
            if (zoomEnabled) {{
                zoomEnabled = false;
                scale = 1.0;
                updateTransform();
                document.getElementById('zoom-info').style.background = 'rgba(0,0,0,0.7)';
            }}
        }});
        
        toolbar.addEventListener('mouseenter', function(e) {{
            if (hideUITimeout) clearTimeout(hideUITimeout);
            showUI();
        }});
        
        toolbar.addEventListener('mouseleave', function(e) {{
            if (!caliperActive && !caliperDragging && !calibrationMode) {{
                hideUITimeout = setTimeout(hideUI, HIDE_UI_DELAY);
            }}
        }});
        
        // Boutons
        document.getElementById('fullscreen-btn').addEventListener('click', toggleFullscreen);
        
        document.getElementById('calibration-btn').addEventListener('click', function() {{
            calibrationMode = !calibrationMode;
            const calibInfo = document.getElementById('calibration-info');
            calibInfo.style.display = calibrationMode ? 'block' : 'none';
            this.classList.toggle('active', calibrationMode);
            if (calibrationMode) {{
                resetCaliper();
                if (hideUITimeout) clearTimeout(hideUITimeout);
            }} else {{
                if (!caliperActive && !caliperDragging) {{
                    hideUITimeout = setTimeout(hideUI, HIDE_UI_DELAY);
                }}
            }}
        }});
        
        // Événements plein écran
        document.addEventListener('fullscreenchange', handleFullscreenChange);
        document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
        document.addEventListener('msfullscreenchange', handleFullscreenChange);
        
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'F11') {{
                e.preventDefault();
                toggleFullscreen();
            }}
        }});
        
        // Zoom
        canvas.addEventListener('wheel', function(e) {{
            if (zoomEnabled) {{
                e.preventDefault();
                const delta = e.deltaY < 0 ? ZOOM_SPEED : -ZOOM_SPEED;
                const newScale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, scale + delta));
                if (newScale !== scale) {{
                    scale = newScale;
                    updateTransform();
                }}
            }}
        }}, {{ passive: false }});
        
        // Clic gauche pour zoom
        canvas.addEventListener('click', function(e) {{
            if (e.button === 0 && !caliperActive && !caliperDragging) {{
                const rect = canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                if (!isClickOnCaliper(x, y) && !zoomEnabled) {{
                    zoomEnabled = true;
                    document.getElementById('zoom-info').style.background = 'rgba(0,128,0,0.7)';
                }}
            }}
        }});
        
        // Clic droit pour caliper
        canvas.addEventListener('contextmenu', function(e) {{
            e.preventDefault();
        }});
        
        canvas.addEventListener('mousedown', function(e) {{
            if (hideUITimeout) clearTimeout(hideUITimeout);
            
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            if (e.button === 0 && isClickOnCaliper(x, y)) {{
                e.preventDefault();
                caliperDragging = true;
                const centerX = (caliperStart.x + caliperEnd.x) / 2;
                dragOffset = {{ x: x - centerX, y: y - caliperStart.y }};
                canvas.style.cursor = 'move';
                
                const moveHandler = function(ev) {{
                    if (!caliperDragging) return;
                    const newX = ev.clientX - rect.left;
                    const newY = ev.clientY - rect.top;
                    const centerX = newX - dragOffset.x;
                    const halfWidth = Math.abs(caliperEnd.x - caliperStart.x) / 2;
                    updateCaliper(centerX - halfWidth, newY - dragOffset.y, centerX + halfWidth, newY - dragOffset.y);
                }};
                
                const upHandler = function(ev) {{
                    if (!caliperDragging) return;
                    document.removeEventListener('mousemove', moveHandler);
                    document.removeEventListener('mouseup', upHandler);
                    caliperDragging = false;
                    canvas.style.cursor = 'crosshair';
                }};
                
                document.addEventListener('mousemove', moveHandler);
                document.addEventListener('mouseup', upHandler);
                
            }} else if (e.button === 2) {{
                e.preventDefault();
                if (resetTimeout) {{
                    clearTimeout(resetTimeout);
                    resetTimeout = null;
                }}
                
                caliperActive = true;
                caliperPersistent = false;
                caliperStart = {{x: x, y: y}};
                setCaliperVisible(true);
                updateCaliper(x, y, x, y);
                
                const moveHandler = function(ev) {{
                    if (!caliperActive) return;
                    const x2 = ev.clientX - rect.left;
                    const y2 = ev.clientY - rect.top;
                    updateCaliper(caliperStart.x, caliperStart.y, x2, y2);
                }};
                
                const upHandler = function(ev) {{
                    if (!caliperActive) return;
                    document.removeEventListener('mousemove', moveHandler);
                    document.removeEventListener('mouseup', upHandler);
                    
                    const x2 = ev.clientX - rect.left;
                    const y2 = ev.clientY - rect.top;
                    caliperEnd = {{x: x2, y: y2}};
                    caliperActive = false;
                    caliperPersistent = true;
                    
                    if (calibrationMode && calibrationMeasurement) {{
                        const measuredPixels = calibrationMeasurement.pixels;
                        const targetMs = calibrationMeasurement.targetMs;
                        const targetMm = targetMs / 40;
                        ECG_CONFIG.pixelsPerMm = measuredPixels / targetMm;
                        
                        calibrationMode = false;
                        document.getElementById('calibration-info').style.display = 'none';
                        document.getElementById('calibration-btn').classList.remove('active');
                        
                        const measureLabel = document.getElementById('measure-label');
                        const calibrationMsg = 'Calibration mise à jour: ' + ECG_CONFIG.pixelsPerMm.toFixed(2) + ' pixels/mm';
                        measureLabel.textContent = calibrationMsg;
                        setTimeout(() => {{
                            const pixelDistance = Math.abs(caliperEnd.x - caliperStart.x) / scale;
                            const mmDistance = pixelDistance / ECG_CONFIG.pixelsPerMm;
                            const timeMs = mmDistance * 40;
                            measureLabel.textContent = timeMs.toFixed(0) + ' ms';
                        }}, 2000);
                    }}
                }};
                
                document.addEventListener('mousemove', moveHandler);
                document.addEventListener('mouseup', upHandler);
            }}
        }});
        
        canvas.addEventListener('mouseup', function(e) {{
            if (!caliperActive && !caliperDragging && !calibrationMode) {{
                hideUITimeout = setTimeout(hideUI, HIDE_UI_DELAY);
            }}
        }});
        
        // Double-clic pour reset
        canvas.addEventListener('dblclick', function(e) {{
            e.preventDefault();
            resetCaliper();
            scale = 1.0;
            updateTransform();
            zoomEnabled = false;
            document.getElementById('zoom-info').style.background = 'rgba(0,0,0,0.7)';
            calibrationMode = false;
            document.getElementById('calibration-info').style.display = 'none';
            document.getElementById('calibration-btn').classList.remove('active');
        }});
        
        // Démarrer le timer initial
        hideUITimeout = setTimeout(hideUI, HIDE_UI_DELAY);
    }});
    </script>
</body>
</html>
"""
    return viewer_html