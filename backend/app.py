# app.py
# pyrefly: ignore [missing-import]
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import time
import os
import json
import threading
import sys
from functools import wraps
from collections import deque

sys.path.append(os.path.join(os.path.dirname(__file__), 'ml'))
try:
    from ml.predictor import TravelTimePredictor
    from ml.route_learner import RouteLearner
except ImportError as e:
    print(f"Error imports ML: {e}")
    TravelTimePredictor = None
    RouteLearner = None

app = Flask(__name__)

# CONFIGURACIÓN DE SEGURIDAD Y CORS
origenes_permitidos = [
    "http://localhost",
    "http://localhost:80",
    "http://127.0.0.1"
]
CORS(app, resources={r"/api/*": {"origins": origenes_permitidos}})

@app.after_request
def cabeceras_seguridad(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


registro_peticiones = {}
lock_rate = threading.Lock()

def limpiar_registros_viejos():
    ahora = time.time()
    ips_a_borrar = []
    
    for ip, timestamps in registro_peticiones.items():
        nuevos = []
        for t in timestamps:
            if ahora - t < 60:
                nuevos.append(t)
        registro_peticiones[ip] = nuevos
        if len(nuevos) == 0:
            ips_a_borrar.append(ip)
            
    for ip in ips_a_borrar:
        if ip in registro_peticiones:
            del registro_peticiones[ip]

def verificar_rate_limit(limite=30):
    ip = request.remote_addr
    ahora = time.time()

    with lock_rate:
        limpiar_registros_viejos()
        if ip not in registro_peticiones:
            registro_peticiones[ip] = []
            
        peticiones_recientes = []
        for t in registro_peticiones[ip]:
            if ahora - t < 60:
                peticiones_recientes.append(t)

        if len(peticiones_recientes) >= limite:
            return False

        registro_peticiones[ip].append(ahora)
        return True

def rate_limit(limite=30):
    def decorador(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not verificar_rate_limit(limite):
                return jsonify({"error": "Demasiadas peticiones. Espera un momento."}), 429
            return f(*args, **kwargs)
        return wrapper
    return decorador


# MANEJO DE CONEXIÓN THREAD-SAFE
class ThreadSafeCursor:
    def __init__(self):
        self.local = threading.local()

    def _get(self):
        if not hasattr(self.local, 'cursor') or self.local.cursor.closed:
            self.local.cursor = conn.cursor()
        return self.local.cursor

    def execute(self, *args, **kwargs):
        return self._get().execute(*args, **kwargs)

    def fetchall(self, *args, **kwargs):
        return self._get().fetchall(*args, **kwargs)

    def fetchone(self, *args, **kwargs):
        return self._get().fetchone(*args, **kwargs)

    @property
    def rowcount(self):
        return self._get().rowcount

    def close(self):
        if hasattr(self.local, 'cursor') and not self.local.cursor.closed:
            self.local.cursor.close()


# INITIALIZACIÓN Y BASE DE DATOS
mem_buses = {}
use_db = False
conn = None
cursor = ThreadSafeCursor()
predictor = None
learner = None

def connect_db():
    global conn, use_db, learner, predictor
    try:
        conn = psycopg2.connect(
            host=os.getenv("DATABASE_HOST", "localhost"),
            database=os.getenv("DATABASE_NAME", "gpsdb"),
            user=os.getenv("DATABASE_USER", "postgres"),
            password=os.getenv("DATABASE_PASSWORD", "postgres")
        )
        conn.autocommit = True
        use_db = True
        print("Conectado a PostgreSQL exitosamente", flush=True)

        cursor = conn.cursor()

        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'usuarios'
            );
        """)
        db_initialized = cursor.fetchone()[0]

        if not db_initialized:
            print("Base de datos vacía. Ejecutando init.sql...", flush=True)
            
            ruta_init = os.path.join(os.path.dirname(__file__), 'database', 'init.sql')
            
            with open(ruta_init, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            cursor.execute(sql_script)
            print("Estructura y datos de Ceuta insertados con éxito.", flush=True)
        else:
            print("Base de datos ya inicializada. Omitiendo init.sql.", flush=True)

        cursor.close()

        if RouteLearner:
            learner = RouteLearner(conn)
            print("RouteLearner OK", flush=True)

        if TravelTimePredictor:
            db_config = {
                "host": os.getenv("DATABASE_HOST", "localhost"),
                "database": os.getenv("DATABASE_NAME", "gpsdb"),
                "user": os.getenv("DATABASE_USER", "postgres"),
                "password": os.getenv("DATABASE_PASSWORD", "postgres")
            }
            predictor = TravelTimePredictor(db_config)
            
            # --- AQUÍ ESTÁ EL ARREGLO ---
            # Usamos hasattr() para evitar el error de "object has no attribute"
            if hasattr(predictor, 'model_path') and not os.path.exists(predictor.model_path):
                 print("Modelo ausente. Se entrenará al recibir datos.")
            print("TravelTimePredictor OK", flush=True)
            # ----------------------------
                 
    except Exception as e:
        print(f"Error conexion BD (Fallback In-Memory): {e}")
        use_db = False

connect_db()

def load_routes():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "routes_data.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error archivo JSON: {e}")
        return {"routes": []}

ROUTES_DATA = load_routes()


# AUXILIARES
def limpiar_nombre_ruta(nombre):
    if not nombre:
        return nombre
    prefijos = [
        "Plaza de la Constitución - ", "Plaza de la Constitución-",
        "Plaza Constitución - ", "Plaza Constitución-",
        "Plaza de la Constitucion - ", "Plaza de la Constitucion-",
        "Pza. Constitución - ", "Pza Constitución - "
    ]
    for prefijo in prefijos:
        if nombre.startswith(prefijo):
            return nombre[len(prefijo):]
            
    sufijos = [
        " - Plaza de la Constitución", "- Plaza de la Constitución",
        " - Plaza de la Constitucion", "- Plaza de la Constitucion"
    ]
    for sufijo in sufijos:
        if nombre.endswith(sufijo):
            return nombre[:len(nombre) - len(sufijo)]
    return nombre


# ENDPOINTS DE LA API

@app.route("/api/stops", methods=["GET"])
def get_stops():
    if not use_db or not conn:
        return jsonify([]), 200
    try:
        cursor.execute("SELECT id, nombre, lat, lon FROM paradas")
        rows = cursor.fetchall()
        result = []
        for r in rows:
            result.append({
                "id": r[0],
                "name": r[1],
                "lat": r[2],
                "lon": r[3]
            })
        return jsonify(result)
    except Exception as e:
        print(f"Error paradas: {e}", flush=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/routes", methods=["GET"])
def get_routes():
    routes_list = []
    FALLBACK_COLORS = [
        "#EF4444", "#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", 
        "#EC4899", "#14B8A6", "#F97316", "#06B6D4", "#6366F1"
    ]
    
    def get_auto_color(rid, existing_color=None):
        if existing_color and existing_color not in ["#3B82F6", "#10B981", "#6366F1"]:
            return existing_color
        idx = sum(ord(c) for c in str(rid)) % len(FALLBACK_COLORS)
        return FALLBACK_COLORS[idx]

    if use_db and conn:
        try:
            cursor.execute("SELECT nombre, lat, lon FROM paradas")
            todas_paradas_globales = []
            for row_p in cursor.fetchall():
                todas_paradas_globales.append({
                    "name": row_p[0],
                    "lat": float(row_p[1]) if row_p[1] else 0.0,
                    "lon": float(row_p[2]) if row_p[2] else 0.0
                })

            cursor.execute("SELECT ref, nombre, color, geometria FROM rutas_estaticas")
            rows = cursor.fetchall()
            for ref, nombre, color, geometria in rows:
                try:
                    path_data = json.loads(geometria) if isinstance(geometria, str) else geometria
                except:
                    path_data = []

                paradas_estaticas_calculadas = []
                if isinstance(path_data, list) and len(path_data) > 0:
                    if not isinstance(path_data[0], list) or len(path_data[0]) == 2:
                        puntos_control = path_data
                    else:
                        puntos_control = []
                        for sub in path_data:
                            for pt in sub:
                                puntos_control.append(pt)
                    
                    for pt in puntos_control:
                        if isinstance(pt, list) and len(pt) >= 2:
                            r_lat, r_lon = float(pt[0]), float(pt[1])
                            for p in todas_paradas_globales:
                                distancia = ((p["lat"] - r_lat)**2 + (p["lon"] - r_lon)**2)**0.5
                                if distancia < 0.0018:
                                    nombres_existentes = []
                                    for x in paradas_estaticas_calculadas:
                                        nombres_existentes.append(x["name"])
                                    if p["name"] not in nombres_existentes:
                                        paradas_estaticas_calculadas.append({
                                            "name": p["name"],
                                            "lat": p["lat"],
                                            "lon": p["lon"]
                                        })

                routes_list.append({
                    "id": ref,
                    "name": limpiar_nombre_ruta(nombre) or f"Línea {ref}",
                    "color": get_auto_color(ref, color),
                    "path": path_data,
                    "stops": paradas_estaticas_calculadas
                })
        except Exception as e:
            print(f"Error rutas estaticas: {e}", flush=True)

        try:
            cursor.execute("SELECT route_id, path FROM learned_routes")
            rows = cursor.fetchall()
            for r_id, path_json in rows:
                ya_existe = False
                for r in routes_list:
                    if r["id"] == r_id:
                        ya_existe = True
                        break
                if ya_existe:
                    continue
                    
                cursor.execute("SELECT name, lat, lon FROM learned_stops WHERE route_id = %s", (r_id,))
                stops = []
                for s in cursor.fetchall():
                    stops.append({
                        "name": s[0],
                        "lat": float(s[1]) if s[1] else 0.0,
                        "lon": float(s[2]) if s[2] else 0.0
                    })
                
                try:
                    path_data_dynamic = json.loads(path_json) if isinstance(path_json, str) else path_json
                except:
                    path_data_dynamic = []

                routes_list.append({
                    "id": r_id,
                    "name": f"Línea {r_id} (Dinámica)",
                    "color": get_auto_color(r_id),
                    "path": path_data_dynamic,
                    "stops": stops
                })
        except Exception as e:
            print(f"Error rutas dinamicas: {e}", flush=True)
            
    all_routes_map = {}
    
    def add_or_merge(r):
        rid = str(r['id'])
        if rid not in all_routes_map:
            path = r.get('path', [])
            if path and isinstance(path, list) and not isinstance(path[0], list):
                path = [path]
            
            all_routes_map[rid] = {
                "id": rid,
                "name": r.get('name') or f"Línea {rid}",
                "color": r.get('color'),
                "path": path,
                "stops": r.get('stops', [])
            }
        else:
            new_path = r.get('path', [])
            if new_path:
                current_path = all_routes_map[rid]["path"]
                if isinstance(new_path, list) and isinstance(new_path[0], list):
                    current_path.extend(new_path)
                else:
                    current_path.append(new_path)
            
            new_stops = r.get('stops', [])
            if new_stops:
                current_stops = all_routes_map[rid]["stops"]
                for ns in new_stops:
                    existe_stop = False
                    for s in current_stops:
                        if s['name'] == ns['name']:
                            existe_stop = True
                            break
                    if not existe_stop:
                        current_stops.append(ns)
    
    for r in routes_list: 
        add_or_merge(r)

    results = list(all_routes_map.values())
    
    if not results:
        return jsonify({"routes": ROUTES_DATA})
        
    return jsonify({"routes": results})

@app.route("/api/gps", methods=["POST"])
@rate_limit(limite=60)
def receive_gps():
    data = request.json
    bus_id = data.get("id")
    lat = data.get("lat")
    lon = data.get("lon")
    route_id = data.get("route_id", "unknown")
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    if use_db and conn:
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO gps_data (bus_id, latitude, longitude, timestamp, route_id) VALUES (%s, %s, %s, NOW(), %s)",
                        (bus_id, lat, lon, route_id)
                    )
            conn.commit() 
        except Exception as e:
            print(f"DB Write Error: {e}")
            conn.rollback() 
    
    mem_buses[bus_id] = {
        "id": bus_id,
        "lat": lat,
        "lon": lon,
        "route_id": route_id,
        "last_update": timestamp
    }
    
    return jsonify({"status": "ok"}), 200


@app.route("/api/traccar", methods=["GET", "POST"])
@rate_limit(limite=60)
def receive_traccar_gps():
    print("\n" + "="*40, flush=True)
    print(f"NUEVA CONEXIÓN DESDE MÓVIL: {request.method}", flush=True)
    print(f"IP Origen: {request.remote_addr}", flush=True)
    
    query_data = request.args.to_dict()
    form_data = request.form.to_dict()
    json_data = request.get_json(silent=True) or {}
    
    data = {**json_data, **form_data, **query_data}
    
    if data:
        print(f"Datos recibidos: {data}", flush=True)
    else:
        print("¡OJO! No han llegado parámetros en la petición.", flush=True)

    device_id = (data.get("id") or 
                 data.get("uniqueId") or 
                 data.get("deviceid") or 
                 data.get("device_id"))
    
    lat = (data.get("lat") or 
           data.get("latitude") or 
           (data.get("location", {}) if isinstance(data.get("location"), dict) else {}).get("coords", {}).get("latitude"))
    
    lon = (data.get("lon") or 
           data.get("longitude") or 
           (data.get("location", {}) if isinstance(data.get("location"), dict) else {}).get("coords", {}).get("longitude"))
    
    if not device_id or lat is None or lon is None:
        print(f"Error: Faltan parámetros críticos (id:{device_id}, lat:{lat}, lon:{lon})", flush=True)
        return jsonify({
            "status": "error", 
            "message": "Missing parameters (need id, lat, lon)",
            "received": data
        }), 400

    device_id_clean = str(device_id).strip().upper()
    route_id = "unknown"
    if device_id_clean in ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9"]:
        route_id = device_id_clean
    
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    try:
        lat_f = float(lat)
        lon_f = float(lon)
        
        if use_db and conn:
            try:
                with conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "INSERT INTO gps_data (bus_id, latitude, longitude, timestamp, route_id) VALUES (%s, %s, %s, NOW(), %s)",
                            (device_id_clean, lat_f, lon_f, route_id)
                        )
                conn.commit()
            except Exception as db_e:
                print(f"DB Write Error (Traccar): {db_e}", flush=True)
                conn.rollback()
        
        mem_buses[device_id_clean] = {
            "id": device_id_clean,
            "lat": lat_f,
            "lon": lon_f,
            "route_id": route_id,
            "last_update": timestamp
        }
        
        if learner:
            learner.process_point(route_id if route_id != "unknown" else device_id_clean, lat_f, lon_f)

        print(f"ÉXITO: Dispositivo {device_id_clean} posicionado en ({lat_f}, {lon_f}) para ruta {route_id}", flush=True)
    except Exception as e:
        print(f"Error procesando coordenadas: {e}", flush=True)
        return "Error parseando datos", 500
    
    print("="*40 + "\n", flush=True)
    return "OK", 200


@app.route("/api/buses", methods=["GET"])
def get_active_buses():
    if use_db and conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT ON (bus_id) bus_id, latitude, longitude, route_id, timestamp
                    FROM gps_data
                    ORDER BY bus_id, timestamp DESC
                """)
                rows = cursor.fetchall()
            
            result = [
                {
                    "id": r[0],
                    "lat": float(r[1]),
                    "lon": float(r[2]),
                    "route_id": r[3],
                    "last_update": str(r[4])
                }
                for r in rows
            ]
            return jsonify(result)
        except Exception as e:
            print(f"DB Read Error: {e}")
            return jsonify(list(mem_buses.values()))
    else:
        return jsonify(list(mem_buses.values()))


@app.route("/api/last", methods=["GET"])
def get_last_positions():
    return get_active_buses()


@app.route("/api/eta/<route_id>", methods=["GET"])
def get_eta(route_id):
    if not predictor:
        return jsonify({"eta": None, "source": "unavailable"})
    
    seconds = predictor.predict_eta(route_id)
    
    return jsonify({
        "eta_seconds": seconds,
        "eta_minutes": round(seconds/60, 1) if seconds else 0,
        "source": "ai_model"
    })


@app.route("/api/record_trip", methods=["POST"])
def record_trip():
    data = request.json
    route_id = data.get("route_id")
    start_time = data.get("start_time") 
    end_time = data.get("end_time")
    duration = data.get("duration")
    
    print(f"Recording trip for {route_id}: {duration}s")

    if use_db and conn:
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO trip_history (route_id, start_time, end_time, duration_seconds) VALUES (%s, %s, %s, %s)",
                        (route_id, start_time, end_time, duration)
                    )
            conn.commit()
            
            threading.Thread(target=learner.entrenar_modelo_tiempos).start()
            
            return jsonify({"status": "recorded_and_training"})
        except Exception as e:
            print(f"Trip Save Error: {e}")
            if conn: conn.rollback()
            return jsonify({"status": "error", "error": str(e)}), 500
    
    return jsonify({"status": "db_unavailable"}), 503


@app.route("/api/avisos", methods=["GET"])
def get_avisos():
    if not use_db or not conn:
        return jsonify([]), 200
    try:
        show_all = request.args.get('all', '0') == '1'
        pagina = request.args.get('page', None)
        limite = request.args.get('limit', '10')

        try:
            limite = min(int(limite), 50)
            if pagina is not None:
                pagina = max(int(pagina), 1)
        except ValueError:
            limite = 10
            pagina = 1

        if show_all:
            base_query = """
                SELECT a.id, a.titulo, a.mensaje, a.tipo, a.linea_id, 
                       COALESCE(l.codigo, a.linea_id::varchar) AS linea_codigo, a.activo, a.creado_en, a.actualizado_en
                FROM avisos a
                LEFT JOIN lineas l ON a.linea_id::varchar = l.id::varchar
                ORDER BY a.creado_en DESC
            """
            count_query = "SELECT COUNT(*) FROM avisos"
        else:
            base_query = """
                SELECT a.id, a.titulo, a.mensaje, a.tipo, a.linea_id,
                       COALESCE(l.codigo, a.linea_id::varchar) AS linea_codigo, a.activo, a.creado_en, a.actualizado_en
                FROM avisos a
                LEFT JOIN lineas l ON a.linea_id::varchar = l.id::varchar
                WHERE a.activo = TRUE
                ORDER BY a.creado_en DESC
            """
            count_query = "SELECT COUNT(*) FROM avisos WHERE activo = TRUE"

        if pagina is None:
            with conn.cursor() as cursor:
                cursor.execute(base_query)
                rows = cursor.fetchall()
            
            result = []
            for r in rows:
                result.append({
                    "id": r[0], "titulo": r[1], "mensaje": r[2], "tipo": r[3],
                    "linea_id": r[4], "linea_codigo": r[5], "activo": r[6],
                    "creado_en": str(r[7]), "actualizado_en": str(r[8])
                })
            return jsonify(result)

        with conn.cursor() as cursor:
            cursor.execute(count_query)
            total = cursor.fetchone()[0]

            offset = (pagina - 1) * limite
            paginated_query = base_query.rstrip() + " LIMIT %s OFFSET %s"
            cursor.execute(paginated_query, (limite, offset))
            rows = cursor.fetchall()

        result = []
        for r in rows:
            result.append({
                "id": r[0], "titulo": r[1], "mensaje": r[2], "tipo": r[3],
                "linea_id": r[4], "linea_codigo": r[5], "activo": r[6],
                "creado_en": str(r[7]), "actualizado_en": str(r[8])
            })

        total_paginas = (total + limite - 1) // limite

        return jsonify({
            "items": result,
            "total": total,
            "pagina": pagina,
            "total_paginas": total_paginas,
            "hay_mas": pagina < total_paginas
        })
    except Exception as e:
        print(f"Error fetching avisos: {e}", flush=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/avisos", methods=["POST"])
@rate_limit(limite=10)
def create_aviso():
    if not use_db or not conn:
        return jsonify({"error": "DB no disponible"}), 503
    data = request.json
    if not data:
        return jsonify({"error": "Datos no validos"}), 400
    titulo = data.get("titulo", "").strip()
    mensaje = data.get("mensaje", "").strip()
    tipo = data.get("tipo", "info")
    linea_id = data.get("linea_id")
    
    if not titulo or not mensaje:
        return jsonify({"error": "Título y mensaje son obligatorios"}), 400
    
    if len(titulo) > 150:
        return jsonify({"error": "El titulo es demasiado largo (max 150)"}), 400
    if len(mensaje) > 2000:
        return jsonify({"error": "El mensaje es demasiado largo (max 2000)"}), 400
    
    tipos_validos = ['info', 'averia', 'retraso', 'cambio_ruta']
    if tipo not in tipos_validos:
        tipo = 'info'
    
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO avisos (titulo, mensaje, tipo, linea_id) 
                       VALUES (%s, %s, %s, %s) RETURNING id, creado_en""",
                    (titulo, mensaje, tipo, linea_id if linea_id else None)
                )
                row = cursor.fetchone()
        conn.commit()
        return jsonify({"status": "ok", "id": row[0], "creado_en": str(row[1])}), 201
    except Exception as e:
        print(f"Error creating aviso: {e}", flush=True)
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/avisos/<int:aviso_id>", methods=["PUT"])
def update_aviso(aviso_id):
    if not use_db or not conn:
        return jsonify({"error": "DB no disponible"}), 503
    data = request.json
    titulo = data.get("titulo", "").strip()
    mensaje = data.get("mensaje", "").strip()
    tipo = data.get("tipo", "info")
    linea_id = data.get("linea_id")
    activo = data.get("activo", True)
    
    if not titulo or not mensaje:
        return jsonify({"error": "Título y mensaje son obligatorios"}), 400
    
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """UPDATE avisos SET titulo=%s, mensaje=%s, tipo=%s, linea_id=%s, activo=%s,
                       actualizado_en=CURRENT_TIMESTAMP
                       WHERE id=%s""",
                    (titulo, mensaje, tipo, linea_id if linea_id else None, activo, aviso_id)
                )
                rows_updated = cursor.rowcount
        conn.commit()
        
        if rows_updated == 0:
            return jsonify({"error": "Aviso no encontrado"}), 404
        return jsonify({"status": "ok"})
    except Exception as e:
        print(f"Error updating aviso: {e}", flush=True)
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/avisos/<int:aviso_id>", methods=["DELETE"])
def delete_aviso(aviso_id):
    if not use_db or not conn:
        return jsonify({"error": "DB no disponible"}), 503
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM avisos WHERE id=%s", (aviso_id,))
                rows_deleted = cursor.rowcount
        conn.commit()
        
        if rows_deleted == 0:
            return jsonify({"error": "Aviso no encontrado"}), 404
        return jsonify({"status": "ok"})
    except Exception as e:
        print(f"Error deleting aviso: {e}", flush=True)
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/horarios", methods=["GET"])
def get_horarios():
    if not use_db or not conn:
        return jsonify([]), 200
    try:
        linea_id = request.args.get('linea_id')
        sentido = request.args.get('sentido')
        dia_tipo = request.args.get('dia_tipo')
        parada = request.args.get('parada')
        pagina = request.args.get('page', None)
        limite = request.args.get('limit', '20')

        try:
            limite = min(int(limite), 100)
            if pagina is not None:
                pagina = max(int(pagina), 1)
        except ValueError:
            limite = 20
            pagina = 1

        base_query = """
            SELECT h.id, h.linea_id, l.codigo, l.nombre AS linea_nombre, l.color,
                   h.parada, h.sentido, h.dia_tipo, h.hora, h.orden_parada
            FROM horarios h
            JOIN lineas l ON h.linea_id = l.id
            WHERE 1=1
        """
        count_query = """
            SELECT COUNT(*)
            FROM horarios h
            JOIN lineas l ON h.linea_id = l.id
            WHERE 1=1
        """
        params = []
        if linea_id:
            base_query += " AND h.linea_id = %s"
            count_query += " AND h.linea_id = %s"
            params.append(int(linea_id))
        if sentido:
            base_query += " AND h.sentido = %s"
            count_query += " AND h.sentido = %s"
            params.append(sentido)
        if dia_tipo:
            base_query += " AND h.dia_tipo = %s"
            count_query += " AND h.dia_tipo = %s"
            params.append(dia_tipo)
        if parada:
            base_query += " AND h.parada ILIKE %s"
            count_query += " AND h.parada ILIKE %s"
            params.append(f"%{parada}%")
        
        base_query += " ORDER BY h.linea_id, h.dia_tipo, h.sentido, h.hora, h.orden_parada"

        if pagina is None:
            with conn.cursor() as cursor:
                cursor.execute(base_query, params)
                rows = cursor.fetchall()
            
            result = []
            for r in rows:
                result.append({
                    "id": r[0], "linea_id": r[1], "linea_codigo": r[2],
                    "linea_nombre": r[3], "linea_color": r[4], "parada": r[5],
                    "sentido": r[6], "dia_tipo": r[7], "hora": str(r[8]),
                    "orden_parada": r[9]
                })
            return jsonify(result)

        with conn.cursor() as cursor:
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]

            offset = (pagina - 1) * limite
            paginated_query = base_query + " LIMIT %s OFFSET %s"
            cursor.execute(paginated_query, params + [limite, offset])
            rows = cursor.fetchall()

        result = []
        for r in rows:
            result.append({
                "id": r[0], "linea_id": r[1], "linea_codigo": r[2],
                "linea_nombre": r[3], "linea_color": r[4], "parada": r[5],
                "sentido": r[6], "dia_tipo": r[7], "hora": str(r[8]),
                "orden_parada": r[9]
            })

        total_paginas = (total + limite - 1) // limite

        return jsonify({
            "items": result,
            "total": total,
            "pagina": pagina,
            "total_paginas": total_paginas,
            "hay_mas": pagina < total_paginas
        })
    except Exception as e:
        print(f"Error fetching horarios: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/horarios/lineas", methods=["GET"])
def get_horarios_lineas():
    """Obtener resumen de líneas con sus metadatos de horarios"""
    if not use_db or not conn:
        return jsonify([]), 200
    try:
        cursor.execute("""
            SELECT l.id, l.codigo, l.nombre, l.color,
                   array_agg(DISTINCT h.dia_tipo) AS dias,
                   array_agg(DISTINCT h.sentido) AS sentidos,
                   MIN(h.hora) AS primera_salida,
                   MAX(h.hora) AS ultima_salida
            FROM lineas l
            JOIN horarios h ON h.linea_id = l.id
            GROUP BY l.id, l.codigo, l.nombre, l.color
            ORDER BY l.codigo
        """)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            result.append({
                "id": r[0],
                "codigo": r[1],
                "nombre": r[2],
                "color": r[3],
                "dias": r[4],
                "sentidos": r[5],
                "primera_salida": str(r[6]),
                "ultima_salida": str(r[7])
            })
        return jsonify(result)
    except Exception as e:
        print(f"Error fetching horarios lineas: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/horarios/paradas", methods=["GET"])
def get_horarios_paradas():
    """Obtener lista de paradas únicas para una línea"""
    if not use_db or not conn:
        return jsonify([]), 200
    try:
        linea_id = request.args.get('linea_id')
        sentido = request.args.get('sentido')
        query = """
            SELECT DISTINCT parada, MIN(orden_parada) as orden
            FROM horarios
            WHERE 1=1
        """
        params = []
        if linea_id:
            query += " AND linea_id = %s"
            params.append(int(linea_id))
        if sentido:
            query += " AND sentido = %s"
            params.append(sentido)
        query += " GROUP BY parada ORDER BY orden"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return jsonify([{"parada": r[0], "orden": r[1]} for r in rows])
    except Exception as e:
        print(f"Error fetching paradas: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/horarios", methods=["POST"])
def create_horario():
    """Crear un nuevo registro de horario"""
    if not use_db or not conn:
        return jsonify({"error": "DB no disponible"}), 503
    data = request.json
    linea_id = data.get("linea_id")
    parada = data.get("parada", "").strip()
    sentido = data.get("sentido", "ida")
    dia_tipo = data.get("dia_tipo", "L-D")
    hora = data.get("hora")
    orden_parada = data.get("orden_parada", 0)
    
    if not linea_id or not parada or not hora:
        return jsonify({"error": "linea_id, parada y hora son obligatorios"}), 400
    try:
        cursor.execute(
            """INSERT INTO horarios (linea_id, parada, sentido, dia_tipo, hora, orden_parada)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
            (linea_id, parada, sentido, dia_tipo, hora, orden_parada)
        )
        row = cursor.fetchone()
        return jsonify({"status": "ok", "id": row[0]}), 201
    except Exception as e:
        print(f"Error creating horario: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/horarios/<int:horario_id>", methods=["PUT"])
def update_horario(horario_id):
    """Actualizar un registro de horario"""
    if not use_db or not conn:
        return jsonify({"error": "DB no disponible"}), 503
    data = request.json
    try:
        cursor.execute(
            """UPDATE horarios SET linea_id=%s, parada=%s, sentido=%s, dia_tipo=%s, hora=%s, orden_parada=%s
               WHERE id=%s""",
            (data.get("linea_id"), data.get("parada"), data.get("sentido"),
             data.get("dia_tipo"), data.get("hora"), data.get("orden_parada", 0), horario_id)
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "Horario no encontrado"}), 404
        return jsonify({"status": "ok"})
    except Exception as e:
        print(f"Error updating horario: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/horarios/<int:horario_id>", methods=["DELETE"])
def delete_horario(horario_id):
    """Eliminar un registro de horario"""
    if not use_db or not conn:
        return jsonify({"error": "DB no disponible"}), 503
    try:
        cursor.execute("DELETE FROM horarios WHERE id=%s", (horario_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "Horario no encontrado"}), 404
        return jsonify({"status": "ok"})
    except Exception as e:
        print(f"Error deleting horario: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

# FAVORITOS (Rutas Guardadas)

@app.route("/api/favoritos/<int:user_id>", methods=["GET"])
def get_favoritos(user_id):
    """Obtener todas las rutas favoritas de un usuario con sus segmentos"""
    if not use_db or not conn:
        return jsonify([]), 200
    try:
        cursor.execute("""
            SELECT id, nombre, icono, creada_en
            FROM rutas_favoritas
            WHERE usuario_id = %s
            ORDER BY creada_en DESC
        """, (user_id,))
        rutas = cursor.fetchall()
        
        result = []
        for r in rutas:
            ruta_id = r[0]
            cursor.execute("""
                SELECT id, orden, linea_id, parada_origen_id, parada_destino_id,
                       parada_origen_nombre, parada_destino_nombre
                FROM segmentos_favoritos
                WHERE ruta_favorita_id = %s
                ORDER BY orden
            """, (ruta_id,))
            segmentos = [{
                "id": s[0],
                "orden": s[1],
                "linea_id": s[2],
                "parada_origen_id": s[3],
                "parada_destino_id": s[4],
                "parada_origen_nombre": s[5],
                "parada_destino_nombre": s[6]
            } for s in cursor.fetchall()]
            
            result.append({
                "id": ruta_id,
                "nombre": r[1],
                "icono": r[2],
                "creada_en": str(r[3]),
                "segmentos": segmentos
            })
        
        return jsonify(result)
    except Exception as e:
        print(f"Error fetching favoritos: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/favoritos", methods=["POST"])
def create_favorito():
    """Crear una nueva ruta favorita con sus segmentos"""
    if not use_db or not conn:
        return jsonify({"error": "DB no disponible"}), 503
    
    data = request.json
    user_id = data.get("user_id")
    nombre = data.get("nombre", "").strip()
    icono = data.get("icono", "📍")
    segmentos = data.get("segmentos", [])
    
    if not user_id or not nombre:
        return jsonify({"error": "user_id y nombre son obligatorios"}), 400
    if not segmentos:
        return jsonify({"error": "Debes añadir al menos un segmento"}), 400
    
    try:
        # Insertar ruta favorita
        cursor.execute(
            """INSERT INTO rutas_favoritas (usuario_id, nombre, icono)
               VALUES (%s, %s, %s) RETURNING id, creada_en""",
            (user_id, nombre, icono)
        )
        row = cursor.fetchone()
        ruta_id = row[0]
        
        # Insertar segmentos
        for seg in segmentos:
            cursor.execute(
                """INSERT INTO segmentos_favoritos 
                   (ruta_favorita_id, orden, linea_id, parada_origen_id, parada_destino_id,
                    parada_origen_nombre, parada_destino_nombre)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (ruta_id, seg.get("orden", 1), seg.get("linea_id"),
                 seg.get("parada_origen_id"), seg.get("parada_destino_id"),
                 seg.get("parada_origen_nombre", ""), seg.get("parada_destino_nombre", ""))
            )
        
        return jsonify({"status": "ok", "id": ruta_id, "creada_en": str(row[1])}), 201
    except Exception as e:
        print(f"Error creating favorito: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/favoritos/<int:fav_id>", methods=["PUT"])
def update_favorito(fav_id):
    """Actualizar nombre/icono de una ruta favorita"""
    if not use_db or not conn:
        return jsonify({"error": "DB no disponible"}), 503
    
    data = request.json
    nombre = data.get("nombre", "").strip()
    icono = data.get("icono", "📍")
    
    if not nombre:
        return jsonify({"error": "El nombre es obligatorio"}), 400
    
    try:
        cursor.execute(
            "UPDATE rutas_favoritas SET nombre=%s, icono=%s WHERE id=%s",
            (nombre, icono, fav_id)
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "Ruta favorita no encontrada"}), 404
        return jsonify({"status": "ok"})
    except Exception as e:
        print(f"Error updating favorito: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/favoritos/<int:fav_id>", methods=["DELETE"])
def delete_favorito(fav_id):
    """Eliminar una ruta favorita y sus segmentos"""
    if not use_db or not conn:
        return jsonify({"error": "DB no disponible"}), 503
    try:
        # Eliminar segmentos primero
        cursor.execute("DELETE FROM segmentos_favoritos WHERE ruta_favorita_id=%s", (fav_id,))
        cursor.execute("DELETE FROM rutas_favoritas WHERE id=%s", (fav_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "Ruta favorita no encontrada"}), 404
        return jsonify({"status": "ok"})
    except Exception as e:
        print(f"Error deleting favorito: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/favoritos/<int:user_id>/alertas", methods=["GET"])
def get_favoritos_alertas(user_id):
    """Obtener avisos activos que afectan a los segmentos guardados de un usuario"""
    if not use_db or not conn:
        return jsonify({"alertas": [], "count": 0}), 200
    try:
        # Avisos que afectan a líneas específicas de los segmentos del usuario
        cursor.execute("""
            SELECT DISTINCT a.id, a.titulo, a.mensaje, a.tipo, 
                   l.codigo AS linea_codigo, a.creado_en,
                   rf.id AS favorito_id, rf.nombre AS favorito_nombre
            FROM avisos a
            JOIN lineas l ON a.linea_id = l.id::varchar
            JOIN segmentos_favoritos sf ON sf.linea_id = l.codigo::varchar
            JOIN rutas_favoritas rf ON sf.ruta_favorita_id = rf.id
            WHERE a.activo = TRUE 
              AND rf.usuario_id = %s
            ORDER BY a.creado_en DESC
        """, (user_id,))
        rows_specific = cursor.fetchall()
        
        # Avisos globales (sin línea específica, afectan a todas)
        cursor.execute("""
            SELECT DISTINCT a.id, a.titulo, a.mensaje, a.tipo,
                   NULL AS linea_codigo, a.creado_en,
                   rf.id AS favorito_id, rf.nombre AS favorito_nombre
            FROM avisos a
            CROSS JOIN rutas_favoritas rf
            WHERE a.activo = TRUE 
              AND a.linea_id IS NULL
              AND rf.usuario_id = %s
            ORDER BY a.creado_en DESC
        """, (user_id,))
        rows_global = cursor.fetchall()
        
        # Combinar y formatear
        all_rows = rows_specific + rows_global
        alertas = []
        seen = set()
        
        for r in all_rows:
            key = (r[0], r[6])  # aviso_id + favorito_id
            if key in seen:
                continue
            seen.add(key)
            alertas.append({
                "aviso_id": r[0],
                "titulo": r[1],
                "mensaje": r[2],
                "tipo": r[3],
                "linea_codigo": r[4],
                "creado_en": str(r[5]),
                "favorito_id": r[6],
                "favorito_nombre": r[7]
            })
        
        # Contar favoritos afectados (únicos)
        favoritos_afectados = len(set(a["favorito_id"] for a in alertas))
        
        return jsonify({
            "alertas": alertas, 
            "count": len(alertas),
            "favoritos_afectados": favoritos_afectados
        })
    except Exception as e:
        print(f"Error fetching favoritos alertas: {e}", flush=True)
        return jsonify({"alertas": [], "count": 0, "error": str(e)}), 500

def construir_grafo_autobuses():
    grafo = {}
    if not use_db or not conn:
        return grafo
    try:
        cursor.execute("SELECT DISTINCT h1.linea_id, h1.parada_id, p1.nombre, h2.parada_id, p2.nombre FROM horarios h1 JOIN horarios h2 ON h1.linea_id = h2.linea_id AND h1.ruta_id = h2.ruta_id AND h2.orden = h1.orden + 1 JOIN paradas p1 ON h1.parada_id = p1.id JOIN paradas p2 ON h2.parada_id = p2.id")
        filas = cursor.fetchall()
        for fila in filas:
            linea_id = fila[0]
            orig_id = fila[1]
            orig_nom = fila[2]
            dest_id = fila[3]
            dest_nom = fila[4]
            if orig_id not in grafo:
                grafo[orig_id] = []
            grafo[orig_id].append({
                "linea_id": linea_id,
                "destino_id": dest_id,
                "origen_nombre": orig_nom,
                "destino_nombre": dest_nom
            })
        return grafo
    except Exception as e:
        print(str(e), flush=True)
        return {}

@app.route("/api/planificar/paradas", methods=["GET"])
def get_paradas_planificador():
    if not use_db or not conn:
        return jsonify([]), 200
    try:
        cursor.execute("SELECT DISTINCT p.id, p.nombre FROM paradas p JOIN horarios h ON p.id = h.parada_id ORDER BY p.nombre ASC")
        filas = cursor.fetchall()
        paradas = []
        for fila in filas:
            paradas.append({"id": fila[0], "nombre": fila[1]})
        return jsonify(paradas), 200
    except Exception as e:
        print(str(e), flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/planificar", methods=["POST"])
def planificar_ruta():
    data = request.json
    if not data:
        data = {}
    origen_id = data.get("parada_origen_id")
    destino_id = data.get("parada_destino_id")
    if not origen_id or not destino_id:
        return jsonify({"error": "Origen y destino son obligatorios"}), 400
    if origen_id == destino_id:
        return jsonify({"error": "El origen y el destino no pueden ser iguales"}), 400
    grafo = construir_grafo_autobuses()
    if origen_id not in grafo:
        return jsonify({"error": "La parada de origen no tiene conexiones"}), 404
    queue = deque()
    queue.append((origen_id, []))
    visitados = set()
    visitados.add(origen_id)
    ruta_encontrada = None
    while len(queue) > 0:
        nodo_actual, camino = queue.popleft()
        if nodo_actual == destino_id:
            ruta_encontrada = camino
            break
        vecinos = grafo.get(nodo_actual, [])
        for vecino in vecinos:
            paso_siguiente = vecino["destino_id"]
            if paso_siguiente not in visitados:
                visitados.add(paso_siguiente)
                nuevo_camino = list(camino)
                nuevo_camino.append(vecino)
                queue.append((paso_siguiente, nuevo_camino))
    if not ruta_encontrada:
        return jsonify({"expandido": False, "mensaje": "No se ha encontrado ninguna ruta disponible"}), 404
    itinerario_visual = []
    primer_paso = ruta_encontrada[0]
    current_tramo = {
        "linea_id": primer_paso["linea_id"],
        "origen_nombre": primer_paso["origen_nombre"],
        "destino_final_nombre": primer_paso["destino_nombre"],
        "paradas_count": 1
    }
    for i in range(1, len(ruta_encontrada)):
        paso = ruta_encontrada[i]
        if paso["linea_id"] == current_tramo["linea_id"]:
            current_tramo["destino_final_nombre"] = paso["destino_nombre"]
            current_tramo["paradas_count"] = current_tramo["paradas_count"] + 1
        else:
            itinerario_visual.append(current_tramo)
            current_tramo = {
                "linea_id": paso["linea_id"],
                "origen_nombre": paso["origen_nombre"],
                "destino_final_nombre": paso["destino_nombre"],
                "paradas_count": 1
            }
    itinerario_visual.append(current_tramo)
    segmentos_puros = []
    for idx in range(len(ruta_encontrada)):
        paso = ruta_encontrada[idx]
        segmentos_puros.append({
            "orden": idx + 1,
            "linea_id": paso["linea_id"],
            "parada_origen_id": paso["origen_id"],
            "parada_destino_id": paso["destino_id"],
            "parada_origen_nombre": paso["origen_nombre"],
            "parada_destino_nombre": paso["destino_nombre"]
        })
    return jsonify({
        "expandido": True,
        "origen_general": primer_paso["origen_nombre"],
        "destino_general": ruta_encontrada[-1]["destino_nombre"],
        "itinerario_visual": itinerario_visual,
        "segmentos_puros": segmentos_puros
    }), 200


# REPORTES (Soporte técnico / Incidencias)

@app.route("/api/reportes", methods=["POST"])
@rate_limit(limite=5)
def create_reporte():
    """Crear un nuevo reporte por parte del usuario"""
    if not use_db or not conn:
        return jsonify({"error": "DB no disponible"}), 503
    
    data = request.json
    if not data:
        return jsonify({"error": "Datos no validos"}), 400
    usuario_id = data.get("usuario_id")
    mensaje = data.get("mensaje", "").strip()
    
    if not usuario_id or not mensaje:
        return jsonify({"error": "usuario_id y mensaje son obligatorios"}), 400
    
    # Validar que el usuario_id es un numero
    try:
        usuario_id = int(usuario_id)
    except (ValueError, TypeError):
        return jsonify({"error": "usuario_id no valido"}), 400
    
    # Limitar longitud del mensaje
    if len(mensaje) > 2000:
        return jsonify({"error": "El mensaje es demasiado largo (max 2000)"}), 400
        
    try:
        cursor.execute(
            """INSERT INTO reportes (usuario_id, mensaje)
               VALUES (%s, %s) RETURNING id, creado_en""",
            (usuario_id, mensaje)
        )
        row = cursor.fetchone()
        return jsonify({"status": "ok", "id": row[0], "creado_en": str(row[1])}), 201
    except Exception as e:
        print(f"Error creating reporte: {e}", flush=True)
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route("/api/reportes/user/<int:user_id>", methods=["GET"])
def get_user_reportes(user_id):
    """Obtener los reportes de un usuario que tengan menos de 48 horas de antigüedad"""
    if not use_db or not conn:
        return jsonify([]), 200
    try:
        # Se ocultan los reportes mayores a 48 horas como pidió el usuario ('se elimine el chat al usuario')
        cursor.execute("""
            SELECT id, mensaje, respuesta_admin, estado, creado_en, actualizado_en
            FROM reportes
            WHERE usuario_id = %s AND creado_en >= NOW() - INTERVAL '48 hours'
            ORDER BY creado_en DESC
        """, (user_id,))
        rows = cursor.fetchall()
        
        result = []
        for r in rows:
            result.append({
                "id": r[0],
                "mensaje": r[1],
                "respuesta_admin": r[2],
                "estado": r[3],
                "creado_en": str(r[4]),
                "actualizado_en": str(r[5])
            })
        return jsonify(result)
    except Exception as e:
        print(f"Error fetching user reportes: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/reportes", methods=["GET"])
def get_admin_reportes():
    """Obtener reportes para admin. Soporta paginacion con ?page=1&limit=15"""
    if not use_db or not conn:
        return jsonify([]), 200
    try:
        pagina = request.args.get('page', None)
        limite = request.args.get('limit', '15')

        try:
            limite = min(int(limite), 50)
            if pagina is not None:
                pagina = max(int(pagina), 1)
        except ValueError:
            limite = 15
            pagina = 1

        base_query = """
            SELECT r.id, r.usuario_id, u.username, r.mensaje, r.respuesta_admin, 
                   r.estado, r.creado_en, r.actualizado_en
            FROM reportes r
            JOIN usuarios u ON r.usuario_id = u.id
            ORDER BY r.creado_en DESC
        """

        # Sin paginacion: devolver todo
        if pagina is None:
            cursor.execute(base_query)
            rows = cursor.fetchall()
            result = []
            for r in rows:
                result.append({
                    "id": r[0], "usuario_id": r[1], "username": r[2],
                    "mensaje": r[3], "respuesta_admin": r[4], "estado": r[5],
                    "creado_en": str(r[6]), "actualizado_en": str(r[7])
                })
            return jsonify(result)

        # Con paginacion
        cursor.execute("SELECT COUNT(*) FROM reportes")
        total = cursor.fetchone()[0]

        offset = (pagina - 1) * limite
        paginated_query = base_query.rstrip() + " LIMIT %s OFFSET %s"
        cursor.execute(paginated_query, (limite, offset))
        rows = cursor.fetchall()

        result = []
        for r in rows:
            result.append({
                "id": r[0], "usuario_id": r[1], "username": r[2],
                "mensaje": r[3], "respuesta_admin": r[4], "estado": r[5],
                "creado_en": str(r[6]), "actualizado_en": str(r[7])
            })

        total_paginas = (total + limite - 1) // limite

        return jsonify({
            "items": result,
            "total": total,
            "pagina": pagina,
            "total_paginas": total_paginas,
            "hay_mas": pagina < total_paginas
        })
    except Exception as e:
        print(f"Error fetching admin reportes: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/reportes/<int:reporte_id>", methods=["PUT"])
def update_reporte(reporte_id):
    """Actualizar estado y responder un reporte (Admin)"""
    if not use_db or not conn:
        return jsonify({"error": "DB no disponible"}), 503
    
    data = request.json
    estado = data.get("estado")
    respuesta_admin = data.get("respuesta_admin")
    
    if not estado:
        return jsonify({"error": "El estado es obligatorio"}), 400
        
    try:
        cursor.execute(
            """UPDATE reportes 
               SET estado = %s, respuesta_admin = %s, actualizado_en = CURRENT_TIMESTAMP
               WHERE id = %s""",
            (estado, respuesta_admin, reporte_id)
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "Reporte no encontrado"}), 404
        return jsonify({"status": "ok"})
    except Exception as e:
        print(f"Error updating reporte: {e}", flush=True)
        return jsonify({"error": str(e)}), 500

# CHATBOT MULTILINGÜE

# Respuestas predefinidas
FAQ_RESPUESTAS = {
    'es': {
        'greeting': '¡Hola! Soy el asistente virtual de CeutaBus. ¿En qué te puedo ayudar? (Ej: "horarios", "precios", "contacto")',
        'fallback': 'Lo siento, no entiendo tu pregunta. Prueba con palabras como "horarios", "precio", "rutas", "contacto" u "objetos perdidos".',
        'precio': 'El billete sencillo cuesta 0.85€. El bonobús de 10 viajes cuesta 6.50€.',
        'horario': 'Puedes consultar los horarios de cada línea en la sección de "Horarios" del menú superior.',
        'ruta': 'Tenemos varias líneas que recorren Ceuta. Ve a la sección "Ver Mapa en Vivo" para ver los autobuses en tiempo real.',
        'contacto': 'Para dudas o quejas, puedes usar la sección de "Soporte" si inicias sesión, o llamar al teléfono de atención: 900 123 456.',
        'perdid': 'Si has perdido algún objeto, acude a nuestra oficina central en C/ Real 12 de lunes a viernes, de 9:00 a 14:00.'
    },
    'en': {
        'greeting': 'Hello! I am the CeutaBus virtual assistant. How can I help you?',
        'fallback': 'Sorry, I don\'t understand your question. Try asking about "schedule", "price", "routes", or "contact".',
        'precio': 'A single ticket is €0.85. The 10-trip card costs €6.50.',
        'horario': 'You can check the schedules for each line in the "Schedules" section of the main menu.',
        'ruta': 'We have several lines covering Ceuta. Go to "Live Map" to see them in real time.',
        'contacto': 'For questions or complaints, use the "Support" section or call 900 123 456.',
        'perdid': 'If you lost any item, please visit our main office at C/ Real 12 from 9AM to 2PM.'
    },
    'fr': {
        'greeting': 'Bonjour ! Je suis l\'assistant virtuel CeutaBus. Comment puis-je vous aider ?',
        'fallback': 'Désolé, je ne comprends pas. Essayez "horaires", "prix", "itinéraires" ou "contact".',
        'precio': 'Le billet simple coûte 0,85 €. La carte de 10 voyages coûte 6,50 €.',
        'horario': 'Vous pouvez consulter les horaires dans la section "Horaires" du menu principal.',
        'ruta': 'Nous avons plusieurs lignes à Ceuta. Allez sur "Carte en direct" pour les voir en temps réel.',
        'contacto': 'Pour toute question, utilisez la section "Support" ou appelez le 900 123 456.',
        'perdid': 'Si vous avez perdu un objet, rendez-vous à notre bureau principal C/ Real 12 de 9h à 14h.'
    },
    'ar': {
        'greeting': 'مرحباً! أنا المساعد الافتراضي لـ CeutaBus. كيف يمكنني مساعدتك؟ (مثال: "مواعيد"، "أسعار"، "اتصال")',
        'fallback': 'عذراً، لم أفهم سؤالك. جرب "مواعيد"، "سعر"، "مسارات"، أو "اتصال".',
        'precio': 'سعر التذكرة الواحدة 0.85 يورو. بطاقة 10 رحلات تكلف 6.50 يورو.',
        'horario': 'يمكنك التحقق من المواعيد لكل خط في قسم "الجداول الزمنية".',
        'ruta': 'لدينا عدة خطوط تغطي سبتة. اذهب إلى "الخريطة المباشرة" لرؤيتها.',
        'contacto': 'للاستفسارات، استخدم قسم "الدعم" أو اتصل على 900 123 456.',
        'perdid': 'إذا فقدت شيئًا، يرجى زيارة مكتبنا الرئيسي في شارع Real 12 من 9 صباحًا إلى 2 مساءً.'
    }
}

# Palabras clave asocidas a cada respuesta
FAQ_KEYWORDS = {
    'es': {
        'precio': ['precio', 'cuesta', 'cuestan', 'billete', 'tarifa', 'bonobus', 'dinero', 'pagar'],
        'horario': ['horario', 'hora', 'cuando', 'frecuencia', 'tarda', 'retraso'],
        'ruta': ['ruta', 'linea', 'parada', 'mapa', 'donde', 'destino'],
        'contacto': ['contacto', 'telefono', 'llamar', 'queja', 'soporte', 'ayuda'],
        'perdid': ['perdido', 'olvidado', 'objeto', 'cartera', 'movil']
    },
    'en': {
        'precio': ['price', 'cost', 'ticket', 'fare', 'money', 'pay', 'much'],
        'horario': ['schedule', 'time', 'when', 'frequency', 'late'],
        'ruta': ['route', 'line', 'stop', 'map', 'where'],
        'contacto': ['contact', 'phone', 'call', 'complain', 'support', 'help'],
        'perdid': ['lost', 'forgotten', 'item', 'wallet', 'phone']
    },
    'fr': {
        'precio': ['prix', 'coûte', 'coute', 'billet', 'tarif', 'argent', 'payer'],
        'horario': ['horaire', 'heure', 'quand', 'fréquence', 'retard'],
        'ruta': ['itinéraire', 'ligne', 'arrêt', 'carte', 'où', 'ou'],
        'contacto': ['contact', 'téléphone', 'appeler', 'plainte', 'support', 'aide'],
        'perdid': ['perdu', 'oublié', 'objet', 'portefeuille', 'téléphone']
    },
    'ar': {
        'precio': ['سعر', 'يكلف', 'تذكرة', 'مال', 'دفع', 'بكم'],
        'horario': ['موعد', 'وقت', 'متى', 'جدول', 'تأخير'],
        'ruta': ['مسار', 'خط', 'موقف', 'خريطة', 'أين', 'مكان'],
        'contacto': ['اتصال', 'هاتف', 'دعم', 'مساعدة', 'شكوى'],
        'perdid': ['مفقود', 'نسيت', 'شيء', 'حقيبة', 'هاتف']
    }
}

@app.route("/api/chatbot", methods=["POST"])
@rate_limit(limite=20)  # Evitar spam
def handle_chatbot():
    """Endpoint del chatbot multilingüe"""
    data = request.json
    if not data:
        return jsonify({"error": "Petición vacía"}), 400
    
    mensaje_usuario = data.get("message", "").lower()
    idioma = data.get("language", "es")
    
    # Si piden un idioma que no tenemos, forzar espanol
    if idioma not in FAQ_RESPUESTAS:
        idioma = 'es'
        
    # Caso 1: El frontend pide el saludo inicial (mandando mensaje vacio)
    if not mensaje_usuario:
        return jsonify({"response": FAQ_RESPUESTAS[idioma]['greeting']})
    
    # Caso 2: Buscar si el mensaje contiene alguna palabra clave
    respuesta = FAQ_RESPUESTAS[idioma]['fallback']
    diccionario_palabras = FAQ_KEYWORDS[idioma]
    
    encontrado = False # Bandera clasica de bucle
    
    for intencion, palabras in diccionario_palabras.items():
        if encontrado:
            break  # Salir si ya lo encontramos
            
        for palabra in palabras:
            if palabra in mensaje_usuario:
                respuesta = FAQ_RESPUESTAS[idioma][intencion]
                encontrado = True
                break
                
    return jsonify({"response": respuesta})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
