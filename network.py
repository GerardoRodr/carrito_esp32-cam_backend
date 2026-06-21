import threading
import queue
import requests
from config import CONTROL_URL, HTTP_TIMEOUT

class NetworkClient:
    def __init__(self):
        self.cola_comandos = queue.Queue()
        self.ultimo_comando_enviado = ""
        self.stopped = False
        self.session = requests.Session()

    def start(self):
        hilo = threading.Thread(target=self._hilo_peticiones_http, daemon=True)
        hilo.start()
        return self

    def send_command(self, endpoint):
        """Agrega un comando a la cola si hay espacio."""
        if self.cola_comandos.empty():
            self.cola_comandos.put(endpoint)

    def _hilo_peticiones_http(self):
        """Este hilo corre en segundo plano y envia las peticiones HTTP al ESP32."""
        while not self.stopped:
            try:
                comando = self.cola_comandos.get()
                if comando != self.ultimo_comando_enviado:
                    try:
                        url = f"{CONTROL_URL}{comando}"
                        self.session.get(url, timeout=HTTP_TIMEOUT)
                        self.ultimo_comando_enviado = comando
                        print(f"Comando enviado exitosamente: {comando}")
                    except requests.exceptions.RequestException as e:
                        print(f"Error de conexion al enviar {comando}: {e}")
                        self.ultimo_comando_enviado = ""
                self.cola_comandos.task_done()
            except Exception as e:
                print(f"Error en el worker thread: {e}")

    def stop(self):
        self.stopped = True
