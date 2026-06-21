# Arquitectura del Firmware (Nodo Esclavo ESP32-CAM)

Este documento describe la arquitectura de software implementada para el nodo esclavo del carrito robótico.

## Paradigma de Diseño: Cerebro Dividido

El sistema utiliza una arquitectura de **Cerebro Dividido**, donde:
- **Computadora Externa (Cerebro):** Ejecuta scripts pesados de Python, procesamiento de Visión Artificial (OpenCV) y toma de decisiones lógicas.
- **ESP32-CAM (Músculo/Ojo):** Actúa puramente como un nodo esclavo y sensor. Su única tarea es enviar la información visual con la mínima latencia posible y obedecer instrucciones de movimiento instantáneas.

## Diagrama de Componentes

El código del ESP32-CAM ha sido modularizado para separar responsabilidades y prevenir bloqueos:

1. **`CODIGO_CARRITO_FINAL.ino` (Main):** 
   Punto de entrada de la aplicación. Configura los módulos secuencialmente y luego deja el `loop()` vacío para permitir que FreeRTOS gestione las tareas en segundo plano.

2. **`motor_control` (Módulo Físico):**
   Encargado del driver de puente H L298N.
   - Utiliza la API `ledc` de Arduino Core para ESP32 para generar señales PWM (5000Hz, 8 bits de resolución).
   - Administra funciones lógicas de alto nivel (`adelante()`, `atras()`, `izquierda()`, `derecha()`, `parar()`).

3. **`network_cam` (Módulo de Hardware/Red):**
   - Inicializa el Access Point (AP) Wi-Fi.
   - Configura la cámara OV2640 con resolución QVGA (320x240) y formato JPEG nativo, optimizada para un alto *framerate*.

4. **`http_server` (Módulo de Comunicación y Multihilo):**
   - **Puerto 80 (Control):** Escucha peticiones GET ligeras y llama a las funciones de `motor_control`. Al responder de manera asíncrona mediante la API de `esp_http_server.h`, permite una latencia muy baja (ms) para maniobras del carrito.
   - **Puerto 81 (Streaming):** Mantiene una conexión HTTP multipart persistente. Transmite buffers sucesivos de fotogramas JPEG directamente extraídos de la cámara. Al usar un puerto y un socket separados, evita que la carga de la transferencia de video bloquee los comandos del puerto 80.

## Prevención de Conflictos de Timer

Un problema muy común en la plataforma ESP32-CAM es la colisión de canales PWM. 
La cámara requiere un reloj maestro (`XCLK`) que por defecto ocupa el `LEDC_CHANNEL_0`. Para evitar que el PWM de los motores desconfigure la cámara (causando cuelgues o la pérdida de la imagen), se ha diseñado el sistema para que `motor_control` ocupe explícitamente los canales del 1 al 4, dejando el canal 0 exclusivo para la inicialización del OV2640.
