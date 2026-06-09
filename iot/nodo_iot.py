import serial
# pyrefly: ignore [missing-import]
import pynmea2
import requests
import time
from collections import deque
import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

# Configuration
URL_NGROK = os.getenv("URL_NGROK", "https://tu-subdominio-defecto.ngrok-free.dev/api/gps")
VEHICULO_ID = os.getenv("VEHICULO_ID", "L1")
RUTA_ID = os.getenv("RUTA_ID", "L1")
PUERTO_SERIAL = os.getenv("PUERTO_SERIAL", "/dev/serial0")
BAUD_RATE = int(os.getenv("BAUD_RATE", "9600"))

buffer_positions = deque(maxlen=1000)

def enviar_payload(payload):
    """
    Realiza la peticion POST hacia el backend.
    Devuelve True si el envio fue exitoso (HTTP 200), False en caso contrario.
    """
    try:
        respuesta = requests.post(URL_NGROK, json=payload, timeout=5)
        if respuesta.status_code == 200:
            return True
        elif respuesta.status_code == 429:
            print("[WARN] Rate limit superado en el servidor.")
            return False
        else:
            print(f"[ERROR] Servidor respondio con codigo: {respuesta.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Fallo en la conexion HTTP: {e}")
        return False

def procesar_buffer():
    """
    Intenta vaciar la cola enviando los datos acumulados en orden cronologico.
    Se detiene inmediatamente si el servidor sigue inaccesible.
    """
    while buffer_positions:
        siguiente_payload = buffer_positions[0]
        if enviar_payload(siguiente_payload):
            buffer_positions.popleft()
            print(f"[BUFFER] Punto recuperado enviado. Quedan {len(buffer_positions)} en cola.")
            time.sleep(0.5)
        else:
            print("[BUFFER] El servidor sigue sin responder. Manteniendo datos en cola.")
            break

def main():
    try:
        ser = serial.Serial(PUERTO_SERIAL, baudrate=BAUD_RATE, timeout=1)
        print(f"[START] Escuchando GPS en {PUERTO_SERIAL} a {BAUD_RATE} baudios...")

        while True:
            linea = ser.readline().decode('ascii', errors='replace')

            if linea.startswith('$GPGGA') or linea.startswith('$GPRMC'):
                try:
                    msg = pynmea2.parse(linea)

                    if msg.latitude != 0.0 and msg.longitude != 0.0:
                        lat = float(msg.latitude)
                        lon = float(msg.longitude)

                        payload = {
                            "id": VEHICULO_ID,
                            "lat": lat,
                            "lon": lon,
                            "route_id": RUTA_ID
                        }

                        if buffer_positions:
                            buffer_positions.append(payload)
                            print(f"[WARN] Red inestable. Guardando posicion en buffer (Total: {len(buffer_positions)})")
                            procesar_buffer()
                        else:
                            if enviar_payload(payload):
                                print(f"[INFO] Enviado en tiempo real - Lat: {lat:.6f}, Lon: {lon:.6f}")
                            else:
                                buffer_positions.append(payload)
                                print(f"[WARN] Envio fallido. Almacenando en buffer (Total: {len(buffer_positions)})")

                    time.sleep(3)

                except pynmea2.ParseError:
                    pass

    except KeyboardInterrupt:
        print("\n[STOP] Programa detenido por el usuario.")
    except Exception as e:
        print(f"[CRITICAL] Error no controlado: {e}")

if __name__ == '__main__':
    main()