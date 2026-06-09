import json
from datetime import datetime
import math
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
# pyrefly: ignore [missing-import]
import joblib
import os

class RouteLearner:
    def __init__(self, db_conn):
        self.db_conn = db_conn
        self.sesiones = {} 
        self.tiempo_parada = 30
        self.radio_parada = 0.0002
        self.radio_bucle = 0.0005
        self.puntos_minimos = 10
        self.ruta_modelo = os.path.join(os.path.dirname(__file__), 'eta_model.pkl')

    def process_point(self, route_id, lat, lon):
        ahora = datetime.now()
        
        if route_id not in self.sesiones:
            self.sesiones[route_id] = {
                "puntos": [],
                "paradas": [],
                "inicio": (lat, lon),
                "ultimo_punto": (lat, lon, ahora),
                "posible_parada": None,
                "aprendiendo": True
            }
            return

        sesion = self.sesiones[route_id]
        lat_anterior, lon_anterior, tiempo_anterior = sesion["ultimo_punto"]
        
        distancia = math.sqrt((lat - lat_anterior)**2 + (lon - lon_anterior)**2)
        
        if distancia < self.radio_parada:
            if sesion["posible_parada"] is None:
                sesion["posible_parada"] = (lat, lon, ahora)
            else:
                lat_parada, lon_parada, tiempo_inicio_parada = sesion["posible_parada"]
                tiempo_espera = (ahora - tiempo_inicio_parada).total_seconds()
                
                if tiempo_espera >= self.tiempo_parada:
                    parada_ya_existe = False
                    for p in sesion["paradas"]:
                        distancia_a_parada = math.sqrt((lat - p[0])**2 + (lon - p[1])**2)
                        if distancia_a_parada < self.radio_parada:
                            parada_ya_existe = True
                            break
                            
                    if not parada_ya_existe:
                        nombre_parada = f"Parada Detectada {len(sesion['paradas']) + 1}"
                        sesion["paradas"].append((lat, lon, nombre_parada))
                        sesion["posible_parada"] = None
        else:
            sesion["posible_parada"] = None
            sesion["puntos"].append([lat, lon])

        lat_inicio, lon_inicio = sesion["inicio"]
        distancia_al_inicio = math.sqrt((lat - lat_inicio)**2 + (lon - lon_inicio)**2)
        
        if distancia_al_inicio < self.radio_bucle and len(sesion["puntos"]) > self.puntos_minimos:
            self.guardar_ruta_aprendida(route_id, sesion["puntos"], sesion["paradas"])
            sesion["puntos"] = []
            sesion["aprendiendo"] = False

        sesion["ultimo_punto"] = (lat, lon, ahora)

    def guardar_ruta_aprendida(self, route_id, puntos, paradas):
        try:
            cursor = self.db_conn.cursor()
            path_json = json.dumps(puntos)
            
            cursor.execute("""
                INSERT INTO learned_routes (route_id, path, last_update)
                VALUES (%s, %s, NOW())
                ON CONFLICT (route_id) DO UPDATE SET path = %s, last_update = NOW()
            """, (route_id, path_json, path_json))
            
            for lat, lon, nombre in paradas:
                cursor.execute("""
                    INSERT INTO learned_stops (route_id, name, lat, lon)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT ON CONSTRAINT unique_stop_per_route DO NOTHING
                """, (route_id, nombre, lat, lon))
            
            self.db_conn.commit()
        except Exception as e:
            print(e)
            self.db_conn.rollback()

    def entrenar_modelo_tiempos(self):
        try:
            query = """
                SELECT route_id, 
                       EXTRACT(HOUR FROM start_time) as hour, 
                       EXTRACT(DOW FROM start_time) as day_of_week, 
                       duration_seconds
                FROM trip_history
            """
            df = pd.read_sql(query, self.db_conn)

            if len(df) < 2:
                return False

            df = pd.get_dummies(df, columns=['route_id'])
            
            X = df.drop('duration_seconds', axis=1)
            y = df['duration_seconds']

            modelo_rf = RandomForestRegressor(n_estimators=100, random_state=42)
            modelo_rf.fit(X, y)

            joblib.dump({'model': modelo_rf, 'columns': X.columns.tolist()}, self.ruta_modelo)
            return True

        except Exception as e:
            print(e)
            return False