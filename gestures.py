import math
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import mediapipe as mp
import config

class GestureRecognizer:
    def __init__(self):
        base_options = mp_python.BaseOptions(model_asset_path=config.MODEL_ASSET_PATH)
        options = vision.HandLandmarkerOptions(
            base_options=base_options, 
            num_hands=config.NUM_HANDS,
            min_hand_detection_confidence=config.MIN_HAND_DETECTION_CONFIDENCE,
            min_hand_presence_confidence=config.MIN_HAND_PRESENCE_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

    def process(self, frame_rgb):
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        return self.detector.detect(mp_image)

    @staticmethod
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
                
        dedos_cuatro = sum(estados[1:5])
        
        if dedos_cuatro == 4:
            return "Mano Abierta", "/adelante"
        elif dedos_cuatro == 0:
            return "Mano Cerrada", "/parar"
        elif estados[1] == 1 and estados[2] == 0 and estados[3] == 0 and estados[4] == 0:
            return "Indice Arriba", "/atras"
            
        return "Desconocido", None
