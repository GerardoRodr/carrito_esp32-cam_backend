# Guía de Configuración y Uso

Sigue esta guía para cargar el firmware y probar tu carrito controlado por visión.

## 1. Conexiones de Hardware

Asegúrate de que los componentes estén conectados correctamente según el mapeo de pines definido en `motor_control.cpp`.

| Pin ESP32-CAM | Entrada del Motor (L298N) |
|:-------------:|:-------------------------:|
| GPIO 13       | IN1                       |
| GPIO 15       | IN2                       |
| GPIO 14       | IN3                       |
| GPIO 2        | IN4                       |

> [!WARNING]
> Recuerda que el ESP32 y el driver de motores deben compartir la tierra física (`GND`), incluso si son alimentados por baterías separadas, de lo contrario los motores no responderán correctamente a las señales PWM.

## 2. Instalación del Firmware

Para cargar el firmware a la tarjeta ESP32-CAM:

1. Abre `CODIGO_CARRITO_FINAL.ino` en **Arduino IDE** (Versión 2.x recomendada).
2. Asegúrate de tener instalado el paquete de placas `esp32` por Espressif Systems en el Gestor de Placas.
3. Ve a **Herramientas > Placa** y selecciona `AI Thinker ESP32-CAM`.
4. Ve a **Herramientas > Partition Scheme** y selecciona `Huge APP (3MB No OTA/1MB SPIFFS)` si la opción está disponible (necesaria por el tamaño de las librerías de red y cámara).
5. Conecta el ESP32-CAM a través del adaptador serial FTDI (recuerda puentear los pines `IO0` a `GND` al encenderlo para ponerlo en modo de programación).
6. Presiona el botón de **Subir** (Upload) en el Arduino IDE.
7. Una vez subido el código, quita el puente entre `IO0` y `GND` y presiona el botón físico de `RST` (Reset) en la placa.

## 3. Conexión Inicial y Pruebas

Una vez el carrito está encendido:

1. Ve a las configuraciones de Red/Wi-Fi de tu computadora (el "cerebro").
2. Busca y conéctate a la red llamada **`ESP32_Carrito_Vision`**.
3. Ingresa la contraseña: **`password123`**.
4. Abre tu navegador web e ingresa a `http://192.168.4.1:81/stream`. Deberías ver un recuadro negro o directamente la transmisión de video en vivo de tu carrito.
5. Abre una pestaña nueva e ingresa a `http://192.168.4.1:80/adelante`. Deberías ver en la página que dice `OK` y los motores de tu carrito deberían comenzar a girar.
6. Ingresa a `http://192.168.4.1:80/parar` para detener los motores.

## 4. Uso del Sistema Completo

Ahora que sabes que funciona manualmente, puedes utilizar los scripts de Python mencionados en `api_reference.md` para implementar tu sistema de autonomía y control lógico en tiempo real.
