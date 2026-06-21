import cv2
import threading
import time
from config import VIDEO_RETRY_DELAY

class VideoStream:
    """Hilo dedicado para consumir frames constantemente y vaciar el buffer interno de OpenCV."""
    def __init__(self, src):
        self.src = src
        self.stream = cv2.VideoCapture(src)
        self.grabbed, self.frame = self.stream.read()
        self.frame_id = 0
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            try:
                grabbed, frame = self.stream.read()
                if not grabbed:
                    time.sleep(VIDEO_RETRY_DELAY)
                    self.stream.release()
                    self.stream = cv2.VideoCapture(self.src)
                    continue
                self.grabbed = grabbed
                self.frame = frame
                
                # CRITICO PARA EVITAR LAG Y SATURACION DEL CEREBRO:
                # Se asigna un identificador unico que se incrementa solo cuando 
                # realmente llego una imagen fresca desde el ESP32.
                # Esto evita que la IA procese la misma imagen multiples veces.
                self.frame_id += 1
            except Exception as e:
                time.sleep(VIDEO_RETRY_DELAY)
                
        # Liberamos el stream desde el MISMO hilo para evitar errores de asercion (libavformat)
        if self.stream:
            self.stream.release()

    def read(self):
        return self.grabbed, self.frame, self.frame_id

    def stop(self):
        self.stopped = True
