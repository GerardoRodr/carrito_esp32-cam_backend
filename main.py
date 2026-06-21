import cv2
import mediapipe as mp
import requests
import threading
import queue
import time
import math

from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

# --- CONFIGURACION ---
ESP32_IP = "192.168.0.235"  # IP del Carrito asignada por el WiFi
STREAM_URL = f"http://{ESP32_IP}:81/stream"
CONTROL_URL = f"http://{ESP32_IP}:80"

# Variables de control
comando_actual = "/parar"
ultimo_comando_enviado = ""
cola_comandos = queue.Queue()

def hilo_peticiones_http():
    """
    Este hilo corre en segundo plano y envia las peticiones HTTP al ESP32.
    """
    global ultimo_comando_enviado
    
    while True:
        try:
            comando = cola_comandos.get()
            if comando != ultimo_comando_enviado:
                try:
                    url = f"{CONTROL_URL}{comando}"
                    requests.get(url, timeout=1.0)
                    ultimo_comando_enviado = comando
                    print(f"Comando enviado exitosamente: {comando}")
                except requests.exceptions.RequestException as e:
                    print(f"Error de conexion al enviar {comando}: {e}")
                    ultimo_comando_enviado = ""
            cola_comandos.task_done()
        except Exception as e:
            print(f"Error en el worker thread: {e}")

def detectar_gesto(hand_landmarks):
    """
    Evalua los landmarks de la mano para determinar el gesto usando la API de Tasks.
    """
    tips = [4, 8, 12, 16, 20]
    pips = [2, 6, 10, 14, 18]
    estados = []
    
    x0, y0 = hand_landmarks[0].x, hand_landmarks[0].y
    x4, y4 = hand_landmarks[4].x, hand_landmarks[4].y
    x2, y2 = hand_landmarks[2].x, hand_landmarks[2].y
    
    dist_punta = math.dist([x4, y4], [x0, y0])
    dist_base = math.dist([x2, y2], [x0, y0])
    
    if dist_punta > dist_base:
        estados.append(1)
    else:
        estados.append(0)
        
    for i in range(1, 5):
        if hand_landmarks[tips[i]].y < hand_landmarks[pips[i]].y:
            estados.append(1)
        else:
            estados.append(0)
            
    total_abiertos = sum(estados)
    dedos_cuatro = sum(estados[1:5])
    
    if dedos_cuatro == 4:
        return "Mano Abierta", "/adelante"
    elif dedos_cuatro == 0:
        return "Mano Cerrada", "/parar"
    elif estados[1] == 1 and estados[2] == 0 and estados[3] == 0 and estados[4] == 0:
        return "Indice Arriba", "/atras"
    """
    ESTA VAINA VA A DAR MÁS PROBLEMAS CAUSA
    elif estados[1] == 1 and estados[2] == 1 and estados[3] == 0 and estados[4] == 0:
        return "Amor y Paz", "/izquierda"
    elif estados[1] == 0 and estados[2] == 0 and estados[3] == 0 and estados[4] == 1:
        return "Menique Arriba", "/derecha"
    """
    return "Desconocido", None

def main():
    global comando_actual
    
    hilo = threading.Thread(target=hilo_peticiones_http, daemon=True)
    hilo.start()
    
    # Configuracion de MediaPipe Tasks API
    base_options = mp_python.BaseOptions(model_asset_path='hand_landmarker.task')
    options = vision.HandLandmarkerOptions(
    base_options=base_options, 
    num_hands=1,
    min_hand_detection_confidence=0.3, # Bajamos el umbral inicial de detección al 30%
    min_hand_presence_confidence=0.3,  # Bajamos el umbral de seguimiento al 30%
    min_tracking_confidence=0.3
    )
    detector = vision.HandLandmarker.create_from_options(options)
    
    print(f"Iniciando conexion de video al stream: {STREAM_URL}...")
    cap = cv2.VideoCapture(STREAM_URL)
    
    prev_time = 0
    
    while True:
        try:
            ret, frame = cap.read()
            if not ret:
                print("No se pudo obtener frame. Reintentando...")
                time.sleep(1)
                cap.release()
                cap = cv2.VideoCapture(STREAM_URL)
                continue
                
            # Invertir el frame horizontalmente (efecto espejo)
            frame = cv2.flip(frame, 1)
                
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
            prev_time = curr_time
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            resultados = detector.detect(mp_image)
            
            nombre_gesto = "Buscando mano..."
            endpoint = None
            
            if resultados.hand_landmarks:
                for hand_landmarks in resultados.hand_landmarks:
                    h, w, _ = frame.shape
                    # Dibujar puntos clave
                    for lm in hand_landmarks:
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        cv2.circle(frame, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
                    
                    nombre_gesto, endpoint = detectar_gesto(hand_landmarks)
                    
                    if endpoint:
                        comando_actual = endpoint
                        if cola_comandos.empty():
                            cola_comandos.put(endpoint)
            else:
                comando_actual = "/parar"
                if cola_comandos.empty():
                    cola_comandos.put("/parar")
            
            cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Gesto: {nombre_gesto}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            cv2.putText(frame, f"Comando: {comando_actual}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            cv2.imshow("Control Gestual del Vehiculo", frame)
            
            tecla = cv2.waitKey(1) & 0xFF
            if tecla == ord('q') or tecla == 27: # 27 es la tecla ESC
                print("Saliendo...")
                break
                
        except KeyboardInterrupt:
            print("\nInterrupcion de teclado en terminal xdddd (Ctrl+C)")
            break
        except Exception as e:
            print(f"Error en el bucle principal: {e}")
            time.sleep(1)
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
