-- Tabla de usuarios (Administradores)
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    email VARCHAR(100) UNIQUE,
    google_id VARCHAR(100) UNIQUE,
    role VARCHAR(20) DEFAULT 'admin'
);

-- Tabla de las lineas de autobus
CREATE TABLE lineas (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(10) UNIQUE NOT NULL,
    nombre VARCHAR(100),
    color VARCHAR(7),
    creada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Paradas de la red de transporte
CREATE TABLE paradas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL
);
 
-- Rutas sacadas de OpenStreetMap (Geometria)
CREATE TABLE IF NOT EXISTS rutas_estaticas (
    id SERIAL PRIMARY KEY,
    osm_id BIGINT UNIQUE,
    nombre VARCHAR(100),
    ref VARCHAR(10),
    color VARCHAR(7),
    geometria JSONB
);

-- Flota de autobuses de la empresa
CREATE TABLE autobuses (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    linea_id INTEGER REFERENCES lineas(id),
    matricula VARCHAR(20),
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Historial y ultima posicion GPS de los buses (Requerido por la API)
CREATE TABLE IF NOT EXISTS gps_data (
    id BIGSERIAL PRIMARY KEY,
    bus_id VARCHAR(50) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    route_id VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_gps_data_bus_time ON gps_data (bus_id, timestamp DESC);

-- Rutas dinamicas aprendidas por el sistema (Requerido por RouteLearner)
CREATE TABLE IF NOT EXISTS learned_routes (
    id SERIAL PRIMARY KEY,
    route_id VARCHAR(50) NOT NULL,
    path JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_learned_routes_route_id ON learned_routes (route_id);

-- Historico de trayectos para el modulo de predicciones de IA
CREATE TABLE IF NOT EXISTS trip_history (
    id SERIAL PRIMARY KEY,
    route_id VARCHAR(50) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration_seconds INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tablon de avisos e incidencias del servicio
CREATE TABLE IF NOT EXISTS avisos (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    mensaje TEXT NOT NULL,
    tipo VARCHAR(30) DEFAULT 'info',
    linea_id VARCHAR(50),
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rutas favoritas de los usuarios de la app
CREATE TABLE IF NOT EXISTS rutas_favoritas (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre VARCHAR(100) NOT NULL,
    icono VARCHAR(10) DEFAULT '📍',
    creada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tramos de lineas guardados en favoritos (Origen -> Destino)
CREATE TABLE IF NOT EXISTS segmentos_favoritos (
    id SERIAL PRIMARY KEY,
    ruta_favorita_id INTEGER NOT NULL REFERENCES rutas_favoritas(id) ON DELETE CASCADE,
    orden INTEGER NOT NULL,
    linea_id VARCHAR(10) NOT NULL,
    parada_origen_id VARCHAR(10) NOT NULL,
    parada_destino_id VARCHAR(10) NOT NULL,
    parada_origen_nombre VARCHAR(100),
    parada_destino_nombre VARCHAR(100)
);

-- Horarios teoricos de las paradas
CREATE TABLE IF NOT EXISTS horarios (
    id SERIAL PRIMARY KEY,
    linea_id INTEGER NOT NULL REFERENCES lineas(id) ON DELETE CASCADE,
    parada VARCHAR(150) NOT NULL,
    sentido VARCHAR(10) NOT NULL DEFAULT 'ida',
    dia_tipo VARCHAR(20) NOT NULL DEFAULT 'L-D',
    hora TIME NOT NULL,
    orden_parada INTEGER NOT NULL DEFAULT 0
);

-- Buzon de quejas o reportes enviados por los usuarios
CREATE TABLE IF NOT EXISTS reportes (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    mensaje TEXT NOT NULL,
    respuesta_admin TEXT DEFAULT NULL,
    estado VARCHAR(20) DEFAULT 'pendiente',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Datos iniciales básicos requeridos para las FK
INSERT INTO lineas (codigo, nombre, color) VALUES 
('L1', 'Línea 1', '#FF0000'),
('L7', 'Línea 7', '#0000FF')
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO autobuses (codigo, linea_id, matricula) VALUES 
('BUS_01', 1, '8899-KLS'),
('BUS_02', 2, '1234-BBC');

INSERT INTO usuarios (username, password_hash) VALUES
('admin', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi');


-- Bucle para generar automaticamente las horas de la Linea 1 (7:30 a 21:30)
DO $$
DECLARE
    hora_base TIME;
    offsets INT[] := ARRAY[0,1,2,3,4,6,8,9,10,11,12,14,16,18,19,20,22,23,24,26,28,30,32,34,36,38,40,42,44,46,48,50];
    paradas TEXT[] := ARRAY[
        'Plaza de la constitución',
        'Calle Real - La Campana',
        'Calle Real - Lope de Vega',
        'Calle Real - Electrónica Valero',
        'Juan I de Portugal',
        'Pozo Rayo (Campus Universitario)',
        'Escuelas Prácticas',
        'Recinto Sur - Depósito de agua',
        'Recinto Sur - Hostal Cateto',
        'C/ Sevilla',
        'Recinto Sur - Local Social',
        'Batería del pintor',
        'Recinto Sur - Local Social',
        'C/ Sevilla',
        'Recinto Sur - Hostal Cateto',
        'Recinto Sur - Depósito de agua',
        'Sarchal - Rotonda de la Virgen',
        'Sarchal -. Caminito de Ronda',
        'Sarchal - Urbanización Monte Hacho',
        'Casa Lola - Campus Universitario',
        'Asamblea Cruz Roja - Maresco',
        'San Amaro- Tanatorio',
        'Parque de San Amaro',
        'San Amaro - Acceso escalera',
        'Cementerio',
        'San Amaro - Bolera',
        'Parque de San Aamaro',
        'San Amaro - Tanatorio',
        'Antiguo -Hospital Cruz Roja',
        'Marina Española - Patio Paramo',
        'Marina Española - Gobierno Militar',
        'Plaza de la constitución'
    ];
    t TIME;
    i INT;
BEGIN
    hora_base := '07:30'::TIME;
    WHILE hora_base <= '21:30'::TIME LOOP
        FOR i IN 1..array_length(paradas, 1) LOOP
            t := hora_base + (offsets[i] || ' minutes')::INTERVAL;
            INSERT INTO horarios (linea_id, parada, sentido, dia_tipo, hora, orden_parada)
            VALUES (1, paradas[i], 'ida', 'L-D', t, i);
        END LOOP;
        hora_base := hora_base + '1 hour'::INTERVAL;
    END LOOP;
END $$;


-- Bucle para generar las horas de la Linea 7 (L-V cada 15m y S-D cada 25m)
DO $$
DECLARE
    paradas TEXT[] := ARRAY[
        'Plaza de la Constitución',
        'Juan Pablo II – Puente del Cristo',
        'Puertas del Campo',
        'Avenida de África – CEIP Ciudad de Ceuta',
        'Avenida de África – Colegio Juan Morejón',
        'Avenida Reyes Católicos – Nueva Galería',
        'Avenida Reyes Católicos – Pinturas Dris',
        'Avenida Reyes Católicos – Miramar Alto',
        'Avenida Cadi Iyad (Arcos Quebrados)',
        'Loma Colmenar (Pisos de Colores)',
        'Hospital Universitario',
        'C/ Doctora Soraya (Pisos Blancos)',
        'C/ Doctora Soraya (Embolsamiento)',
        'Arcos Quebrados',
        'Frontera (cambio de sentido)',
        'Avenida Reyes Católicos – Miramar Bajo',
        'Avenida Reyes Católicos – Miramar Alto',
        'Avenida Reyes Católicos – Pinturas Dris',
        'Avenida Reyes Católicos – El Gallo',
        'Cruce del Morro',
        'Avenida de África – Mezquita',
        'Avenida de África – Instituto Siete Colinas',
        'Avenida de España (Bar Noray)',
        'Avenida Martínez Catena (C.N. Caballa)',
        'Plaza de la Constitución'
    ];
    offsets INT[] := ARRAY[0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,31,32,33,34,35,36,37,38,40];
    hora_base TIME;
    i INT;
    t TIME;
BEGIN
    -- Horas de diario (Lunes a Viernes)
    hora_base := '07:15'::TIME;
    WHILE hora_base <= '22:30'::TIME LOOP
        FOR i IN 1..array_length(paradas, 1) LOOP
            t := hora_base + (offsets[i] || ' minutes')::INTERVAL;
            INSERT INTO horarios (linea_id, parada, sentido, dia_tipo, hora, orden_parada)
            VALUES (2, paradas[i], 'ida', 'L-V', t, i);
        END LOOP;
        hora_base := hora_base + '15 minutes'::INTERVAL;
    END LOOP;

    -- Horas del fin de semana (Sabados y Domingos)
    hora_base := '07:00'::TIME;
    WHILE hora_base <= '22:30'::TIME LOOP
        FOR i IN 1..array_length(paradas, 1) LOOP
            t := hora_base + (offsets[i] || ' minutes')::INTERVAL;
            INSERT INTO horarios (linea_id, parada, sentido, dia_tipo, hora, orden_parada)
            VALUES (2, paradas[i], 'ida', 'S', t, i);
            INSERT INTO horarios (linea_id, parada, sentido, dia_tipo, hora, orden_parada)
            VALUES (2, paradas[i], 'ida', 'D', t, i);
        END LOOP;
        hora_base := hora_base + '25 minutes'::INTERVAL;
    END LOOP;
END $$;