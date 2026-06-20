# Contexto del Proyecto
Actúa como un Ingeniero de Software experto en Visión Computacional (OpenCV) y Edge Computing. Estamos desarrollando la capa de procesamiento para un "Vehículo Controlado por Gestos mediante Visión Artificial por Wi-Fi". 

La arquitectura es de "Cerebro Dividido": 
1. Un ESP32-CAM actúa como nodo esclavo que transmite video en vivo (MJPEG) y expone endpoints HTTP para controlar motores (ej: `/adelante`, `/atras`, `/parar`).
2. Una computadora ejecuta el script de Python que debes desarrollar. Este script es el "cerebro".

# Objetivo
Desarrollar un script en Python que capture el flujo de video inalámbrico del ESP32-CAM, detecte la geometría de la mano en tiempo real usando `MediaPipe Hands`, e interprete gestos específicos para enviar peticiones HTTP GET al ESP32-CAM y controlar su movimiento.

# Requerimientos Técnicos
1. **Captura de Video (`cv2`):** Conectarse al stream MJPEG del ESP32-CAM (ej: `http://[IP_DEL_ESP32]:81/stream`).
2. **Procesamiento (`mediapipe`):** Implementar `mp.solutions.hands` para detectar la mano y sus *landmarks*.
3. **Lógica de Gestos:** Crear una función que determine el gesto actual basándose en las coordenadas de los dedos (ej. todos los dedos levantados = Mano Abierta, todos los dedos cerrados = Puño). *Por ahora, define al menos 3 gestos de prueba.*
4. **Comunicación (`requests`):** Enviar peticiones GET (ej: `http://[IP_DEL_ESP32]/adelante`) según el gesto detectado.
5. [cite_start]**Control de Latencia (Crítico):** El retraso debe minimizarse[cite: 55]. Las peticiones HTTP *no deben bloquear* el hilo principal de captura de video. Implementa un manejo de estado (para no enviar el mismo comando 30 veces por segundo si el gesto no ha cambiado) y utiliza un timeout bajo en `requests` o ejecución en un hilo separado/asíncrono.
6. **Interfaz Visual:** Mostrar el video en una ventana de OpenCV dibujando los *landmarks* de la mano y un texto superpuesto que indique el "Comando Actual" y los FPS del procesamiento.

# Estructura del Código Esperada
- Variables de configuración al inicio (IPs, URLs).
- Función de detección de gestos limpia y modular.
- Bucle `while True` eficiente para el procesamiento frame a frame.
- Manejo de excepciones (ej. si la conexión Wi-Fi con el carrito falla, el script no debe cerrarse abruptamente).

Por favor, genera el código completo en Python con comentarios explicativos pero simples, sin emojis y sin tildes. Obviamente en español. No necesariamente cada linea debe tener comentarios, lo dejo a tu criterio.

Recuerda que usaremos venv para ejecutar el proyecto por lo que no olvides usarlo.