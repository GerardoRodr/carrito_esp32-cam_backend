# config.py

# Configuracion de red
ESP32_IP = "192.168.0.235"  # IP del Carrito asignada por el WiFi
STREAM_URL = f"http://{ESP32_IP}:81/stream"
CONTROL_URL = f"http://{ESP32_IP}:80"

# Tiempos de espera
HTTP_TIMEOUT = 1.0
VIDEO_RETRY_DELAY = 1.0

# Opciones de MediaPipe HandLandmarker
MODEL_ASSET_PATH = 'hand_landmarker.task'
NUM_HANDS = 1
MIN_HAND_DETECTION_CONFIDENCE = 0.3
MIN_HAND_PRESENCE_CONFIDENCE = 0.3
MIN_TRACKING_CONFIDENCE = 0.3
