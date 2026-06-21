# Referencia de la API HTTP

Para integrar el cerebro en Python con el carrito, debes interactuar con los dos servidores HTTP expuestos por el ESP32-CAM.

La IP por defecto (estando conectados al WiFi `ESP32_Carrito_Vision`) es **`192.168.4.1`**.

## Servidor de Streaming (Puerto 81)

Este servidor transmite el flujo de video en vivo. 

* **Endpoint:** `GET http://192.168.4.1:81/stream`
* **Tipo de Respuesta:** `multipart/x-mixed-replace`
* **Formato de fotograma:** `image/jpeg`
* **Resolución:** 320x240 (QVGA)

### Integración en Python (OpenCV)
```python
import cv2

# Abrir el stream como si fuera una webcam
cap = cv2.VideoCapture("http://192.168.4.1:81/stream")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error leyendo el stream")
        break
        
    # Procesar frame con IA/Visión Artificial
    # ...
    
    cv2.imshow("Carrito Stream", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

## Servidor de Control de Motores (Puerto 80)

Este servidor permite controlar el movimiento del vehículo a través del driver L298N. Todas las respuestas son rápidas y asíncronas para garantizar una baja latencia.

* **Endpoints Disponibles (Todos `GET`):**
  * `http://192.168.4.1:80/adelante` - Mueve el carrito hacia adelante.
  * `http://192.168.4.1:80/atras` - Mueve el carrito en reversa.
  * `http://192.168.4.1:80/izquierda` - Gira hacia la izquierda (girando ruedas en sentido opuesto).
  * `http://192.168.4.1:80/derecha` - Gira hacia la derecha (girando ruedas en sentido opuesto).
  * `http://192.168.4.1:80/parar` - Detiene todos los motores.
  * `http://192.168.4.1:80/velocidad?v=255` - Cambia la velocidad actual de los motores (donde `v` va de `0` a `255`). Si el vehículo se está moviendo, el cambio de velocidad se aplicará inmediatamente sin necesidad de mandar de nuevo la orden de movimiento.

* **Tipo de Respuesta:** `text/plain`
* **Cuerpo de Respuesta:** `"OK"` (Status HTTP 200)

### Integración en Python (Requests)
```python
import requests
import time

URL_CONTROL = "http://<IP_DEL_CARRITO>:80"

def mover_adelante():
    requests.get(f"{URL_CONTROL}/adelante")

def parar():
    requests.get(f"{URL_CONTROL}/parar")

# Ejemplo: Mover adelante por 1 segundo
mover_adelante()
time.sleep(1.0)
parar()
```

### Integración en Frontend Web (JavaScript / Fetch)
Si estás desarrollando una interfaz web o Dashboard interactivo, puedes controlar los motores usando la API nativa `fetch` de JavaScript. Los endpoints no tienen restricciones de CORS (`Access-Control-Allow-Origin: *`), lo que significa que puedes llamarlos desde cualquier interfaz web local sin problemas.

**Ejemplo de Control de Movimiento (Botones):**
```javascript
const ipCarrito = "http://<IP_DEL_CARRITO>:80";

// Llamar a esta función al mantener presionado el botón de avanzar
function avanzar() {
  fetch(`${ipCarrito}/adelante`);
}

// Llamar a esta función al soltar cualquier botón
function detener() {
  fetch(`${ipCarrito}/parar`);
}
```

**Ejemplo de Control de Velocidad (Slider HTML):**
Si tienes un input de rango en HTML: `<input type="range" min="80" max="255" onchange="cambiarVelocidad(this.value)">`

```javascript
// La velocidad debe estar entre 0 (detenido) y 255 (potencia máxima)
function cambiarVelocidad(valor) {
  // Envia el valor al backend del ESP32
  fetch(`${ipCarrito}/velocidad?v=${valor}`)
    .then(response => {
      if(response.ok) {
        console.log(`Velocidad cambiada a: ${valor}`);
      }
    })
    .catch(err => console.error("Error al contactar con el carrito", err));
}
```
*Nota frontend:* El cambio de velocidad (`/velocidad?v=X`) se aplica instantáneamente. Es decir, si el carrito está actualmente avanzando hacia adelante y mueves el slider, el carrito ajustará su velocidad automáticamente sin necesidad de que vuelvas a llamar a `fetch('/adelante')`.
