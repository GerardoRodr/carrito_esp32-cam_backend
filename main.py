import cv2
import time
from config import STREAM_URL
from video import VideoStream
from network import NetworkClient
from gestures import GestureRecognizer

def main():
    comando_actual = "/parar"
    
    # Iniciar cliente de red en segundo plano
    network_client = NetworkClient().start()
    
    # Iniciar reconocedor de gestos (MediaPipe)
    gesture_recognizer = GestureRecognizer()
    
    # Iniciar captura de video en hilo dedicado
    print(f"Iniciando conexion de video al stream: {STREAM_URL}...")
    vs = VideoStream(STREAM_URL).start()
    
    prev_time = 0
    
    while True:
        try:
            ret, frame = vs.read()
            if not ret or frame is None:
                # Esperar un poco si aun no hay frame disponible
                time.sleep(0.01)
                continue
                
            # Invertir el frame horizontalmente (efecto espejo)
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
                    # Dibujar puntos clave
                    for lm in hand_landmarks:
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        cv2.circle(frame, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
                    
                    nombre_gesto, endpoint = gesture_recognizer.detectar_gesto(hand_landmarks)
                    
                    if endpoint:
                        comando_actual = endpoint
                        network_client.send_command(endpoint)
            else:
                comando_actual = "/parar"
                network_client.send_command("/parar")
            
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
            
    vs.stop()
    network_client.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
