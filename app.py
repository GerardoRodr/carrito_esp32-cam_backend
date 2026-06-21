from flask import Flask, render_template, Response, jsonify, request
import cv2
import threading
import time
import logging

# Filtro para ignorar los logs constantes de /stats en la consola
class NoStatsFilter(logging.Filter):
    def filter(self, record):
        return '/stats' not in record.getMessage()

logging.getLogger('werkzeug').addFilter(NoStatsFilter())

from config import STREAM_URL, CONTROL_URL
from video import VideoStream
from network import NetworkClient
from gestures import GestureRecognizer

app = Flask(__name__)

# Estado global compartido entre la IA y Flask
estado = {
    "fps": 0,
    "gesto": "Buscando mano...",
    "comando": "/parar",
    "modo": "auto"
}
frame_actual = None
lock = threading.Lock()

def ia_loop():
    """Hilo demonio que ejecuta toda la logica de captura de video e IA sin parar."""
    global frame_actual, estado
    
    network_client = NetworkClient().start()
    gesture_recognizer = GestureRecognizer()
    
    print(f"Iniciando conexion de video al stream: {STREAM_URL}...")
    vs = VideoStream(STREAM_URL).start()
    
    prev_time = 0
    comando_actual = "/parar"
    
    while True:
        try:
            ret, frame = vs.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue
                
            frame = cv2.flip(frame, 1)
                
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
            prev_time = curr_time
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            resultados = gesture_recognizer.process(frame_rgb)
            
            nombre_gesto = "Buscando mano..."
            endpoint = None
            
            if resultados.hand_landmarks:
                for hand_landmarks in resultados.hand_landmarks:
                    h, w, _ = frame.shape
                    for lm in hand_landmarks:
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        cv2.circle(frame, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
                    
                    nombre_gesto, endpoint = gesture_recognizer.detectar_gesto(hand_landmarks)
                    
                    if endpoint:
                        comando_actual = endpoint
                        if estado["modo"] == "auto":
                            network_client.send_command(endpoint)
            else:
                comando_actual = "/parar"
                if estado["modo"] == "auto":
                    network_client.send_command("/parar")
            
            # En lugar de cv2.imshow, codificamos el frame para enviarlo por HTTP
            ret_encode, buffer = cv2.imencode('.jpg', frame)
            if ret_encode:
                with lock:
                    frame_actual = buffer.tobytes()
                    estado["fps"] = int(fps)
                    estado["gesto"] = nombre_gesto
                    estado["comando"] = comando_actual
                    
        except Exception as e:
            print(f"Error en el bucle principal de IA: {e}")
            time.sleep(1)

def generar_video():
    """Generador que despacha los frames procesados al cliente web via MJPEG."""
    while True:
        with lock:
            frame = frame_actual
            
        if frame is None:
            time.sleep(0.1)
            continue
            
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
               
        # Una pequeña pausa evita saturar al navegador si la IA va a >60 FPS
        time.sleep(0.03) 

@app.route('/')
def index():
    return render_template('index.html', url_carrito=CONTROL_URL)

@app.route('/set_mode')
def set_mode():
    import requests
    estado_req = request.args.get('estado', 'auto')
    with lock:
        estado["modo"] = estado_req
        # Si cambiamos a manual, paramos el carro por seguridad
        if estado_req == "manual":
            try:
                requests.get(CONTROL_URL + "/parar", timeout=1.0)
            except:
                pass
    return jsonify({"status": "ok", "modo": estado_req})

@app.route('/video_feed')
def video_feed():
    return Response(generar_video(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stats')
def stats():
    with lock:
        return jsonify(estado)

if __name__ == '__main__':
    # Lanzar la IA como un hilo en segundo plano (daemon es pa que muera al cerrar Flask xddd)
    hilo_ia = threading.Thread(target=ia_loop, daemon=True)
    hilo_ia.start()
    
    # Iniciar servidor Flask escuchando en la red local
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
