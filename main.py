import cv2
import mediapipe as mp
import requests
import threading
import queue
import time
import math

# --- CONFIGURACION ---
ESP32_IP = "192.168.1.100"  # Cambiar por la IP real de tu ESP32-CAM
STREAM_URL = f"http://{ESP32_IP}:81/stream"
CONTROL_URL = f"http://{ESP32_IP}"

# Variables de control
comando_actual = "/parar"
ultimo_comando_enviado = ""
cola_comandos = queue.Queue()

def hilo_peticiones_http():
    """
    Este hilo corre en segundo plano y envia las peticiones HTTP al ESP32.
    Al usar una cola y un timeout, garantizamos que el hilo principal de video no se bloquee.
    """
    global ultimo_comando_enviado
    
    while True:
        try:
            # Espera un nuevo comando, bloqueando hasta que haya uno
            comando = cola_comandos.get()
            
            # Si es igual al ultimo enviado, no hacemos spam
            if comando != ultimo_comando_enviado:
                try:
                    url = f"{CONTROL_URL}{comando}"
                    # Timeout bajo para que si se cae la red, se recupere rapido sin encolar basura
                    requests.get(url, timeout=1.0)
                    ultimo_comando_enviado = comando
                    print(f"Comando enviado exitosamente: {comando}")
                except requests.exceptions.RequestException as e:
                    print(f"Error de conexion al enviar {comando}: {e}")
                    # En caso de error de red temporal, reseteamos el estado para reintentar luego
                    ultimo_comando_enviado = ""
                    
            cola_comandos.task_done()
        except Exception as e:
            print(f"Error en el worker thread: {e}")

def detectar_gesto(hand_landmarks):
    """
    Evalua los landmarks de la mano para determinar el gesto.
    Retorna una tupla: (Nombre del Gesto, Endpoint HTTP)
    """
    tips = [4, 8, 12, 16, 20]
    pips = [2, 6, 10, 14, 18]
    estados = []
    
    # Para el pulgar calculamos la distancia a la base de la mano (landmark 0)
    # Si la punta esta mas lejos que su primera articulacion, asumimos que esta abierto
    x0, y0 = hand_landmarks.landmark[0].x, hand_landmarks.landmark[0].y
    x4, y4 = hand_landmarks.landmark[4].x, hand_landmarks.landmark[4].y
    x2, y2 = hand_landmarks.landmark[2].x, hand_landmarks.landmark[2].y
    
    dist_punta = math.dist([x4, y4], [x0, y0])
    dist_base = math.dist([x2, y2], [x0, y0])
    
    if dist_punta > dist_base:
        estados.append(1)
    else:
        estados.append(0)
        
    # Para los demas dedos, simplemente evaluamos su posicion en el eje Y
    # (Un valor menor en Y significa que esta mas arriba en la imagen)
    for i in range(1, 5):
        if hand_landmarks.landmark[tips[i]].y < hand_landmarks.landmark[pips[i]].y:
            estados.append(1)
        else:
            estados.append(0)
            
    total_abiertos = sum(estados)
    
    # Reglas para identificar el gesto
    if total_abiertos >= 4:
        return "Mano Abierta", "/adelante"
    elif total_abiertos == 0:
        return "Puno Cerrado", "/parar"
    elif estados[1] == 1 and estados[2] == 0 and estados[3] == 0 and estados[4] == 0:
        return "Indice Arriba", "/atras"
        
    return "Desconocido", None

def main():
    global comando_actual
    
    # 1. Iniciar el hilo secundario (worker thread) en modo daemon
    hilo = threading.Thread(target=hilo_peticiones_http, daemon=True)
    hilo.start()
    
    # 2. Configuracion de MediaPipe Hands
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    
    print("Iniciando conexion de video...")
    # NOTA: Para probar con webcam local de tu PC si el carrito no esta prendido, cambia STREAM_URL por 0
    cap = cv2.VideoCapture(STREAM_URL)
    
    # Variables para el calculo de los FPS (Frames Per Second)
    prev_time = 0
    
    while True:
        try:
            ret, frame = cap.read()
            if not ret:
                print("No se pudo obtener frame del stream. Reintentando...")
                time.sleep(1)
                # Intento basico de reconexion
                cap.release()
                cap = cv2.VideoCapture(STREAM_URL)
                continue
                
            # Calcular FPS
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
            prev_time = curr_time
            
            # Convertir frame de BGR a RGB porque MediaPipe lo requiere
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            resultados = hands.process(frame_rgb)
            
            nombre_gesto = "Buscando mano..."
            endpoint = None
            
            if resultados.multi_hand_landmarks:
                for hand_landmarks in resultados.multi_hand_landmarks:
                    # Dibujar las conexiones de la mano sobre el frame original
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    # Interpretar gesto actual
                    nombre_gesto, endpoint = detectar_gesto(hand_landmarks)
                    
                    if endpoint:
                        comando_actual = endpoint
                        # Agregar comando a la cola si hay espacio y no esta saturada
                        if cola_comandos.empty():
                            cola_comandos.put(endpoint)
            else:
                # Si no hay mano visible, por seguridad enviamos el comando de parar
                comando_actual = "/parar"
                if cola_comandos.empty():
                    cola_comandos.put("/parar")
            
            # Dibujar la informacion (FPS, Gesto y Comando) en pantalla
            cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Gesto: {nombre_gesto}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            cv2.putText(frame, f"Comando: {comando_actual}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Mostrar la ventana
            cv2.imshow("Control Gestual del Vehiculo", frame)
            
            # Salir limpiamente si se presiona la tecla 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        except Exception as e:
            print(f"Error en el bucle principal: {e}")
            time.sleep(1)
            
    # Liberar recursos al terminar
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
