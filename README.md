# TFG: Desarrollo de un sistema que proporciona información y geolocalización del transporte público de Ceuta en tiempo real
 
**Ilias Ahmed Ahmed**  
Grado en Ingeniería Informática  
Trabajo de Fin de Grado  

---

## Descripción del proyecto

Este proyecto es el resultado de mi TFG: una aplicación web completa para la gestión y el seguimiento en tiempo real de una flota de autobuses urbanos. La idea surge de la necesidad de disponer de un sistema propio que no dependa de APIs de terceros de pago, y que además sea capaz de aprender del comportamiento real de las rutas.

El objetivo principal es ofrecer tanto a administradores como a usuarios una herramienta donde consultar la ubicación de los autobuses, estimar tiempos de llegada, gestionar incidencias y guardar rutas favoritas, minimizando la latencia y garantizando funcionamiento incluso con cortes de conexión.

---

## Arquitectura del sistema

El sistema se divide en tres bloques principales:

### Backend (Python + Flask)
Encargado de la lógica de negocio, API REST, ingesta de datos GPS y módulos de inteligencia artificial.

### Frontend (PHP)
Interfaz web desarrollada en PHP con estructura tipo MVC ligera para facilitar el despliegue.

### Base de datos (PostgreSQL)
Sistema de almacenamiento principal. Gestiona usuarios, rutas, paradas, vehículos, registros GPS, horarios e incidencias. Incluye soporte para consultas geoespaciales y almacenamiento de datos históricos para el módulo de aprendizaje automático.

### Nodo IoT (Python + GPS)
A los tres blques principales se les añade un script ejecutado en una Raspberry Pi conectada a un módulo GPS. Lee tramas NMEA, procesa la posición y la envía al backend. Si no hay conexión, almacena los datos en un buffer local.

---

## Módulos de inteligencia artificial

### RouteLearner
Sistema que detecta automáticamente rutas a partir de puntos GPS. Identifica cuando un autobús altera la ruta asignada durante un tiempo y si lo repite, reconstruye la ruta.

### TravelTimePredictor
Modelo  que predice el tiempo estimado de llegada (ETA) usando histórico de trayectos. Se guarda con joblib para evitar reentrenamiento continuo.

---


## Estructura del Repositorio

El proyecto se organiza estrictamente bajo el siguiente árbol de directorios modular:

```text
└── TFG/
    ├── docker-compose.yml
    ├── usage_scenario.yml
    ├── .env.ejemplo
    ├── backend/
    │   ├── Dockerfile
    │   ├── osm_fetch.py
    │   ├── osm_routes.py
    │   ├── requirements.txt
    │   ├── start.sh
    │   └── ml/
    │       ├── predictor.py
    │       └── route_learner.py
    ├── database/
    │   ├── init.sql
    │   └── migration_google_auth.sql
    ├── frontend/
    │   ├── Dockerfile
    │   └── src/
    │       ├── config/
    │       │   └── database.php
    │       ├── controllers/
    │       │   ├── AdminController.php
    │       │   ├── ApiController.php
    │       │   ├── AuthController.php
    │       │   ├── FavoritosController.php
    │       │   ├── HomeController.php
    │       │   ├── HorariosController.php
    │       │   ├── MapController.php
    │       │   └── ReportesController.php
    │       ├── public/
    │       │   ├── index.php
    │       │   ├── .htaccess
    │       │   └── css/
    │       │       ├── favoritos.css
    │       │       ├── global.css
    │       │       ├── home.css
    │       │       ├── horarios.css
    │       │       └── map.css
    │       └── views/
    │           ├── home.php
    │           ├── horarios.php
    │           ├── map.php
    │           ├── reportes.php
    │           ├── admin/
    │           │   ├── add_bus.php
    │           │   ├── avisos.php
    │           │   ├── dashboard.php
    │           │   ├── horarios.php
    │           │   └── reportes.php
    │           ├── auth/
    │           │   ├── login.php
    │           │   └── register.php
    │           └── layout/
    │               ├── chatbot.php
    │               ├── footer.php
    │               └── header.php
    ├── iot/
    │   └── nodo_iot.py
    └── versiones/
        ├── check_db.py
        ├── gps_simulator.py
        └── init_db.py

### Componentes Principales

**Raíz del proyecto:**
- `docker-compose.yml`: Archivo que define y levanta los contenedores, redes y volúmenes necesarios para que toda la aplicación funcione de forma conjunta.
- `usage_scenario.yml`: Configuración de escenarios y simulaciones de carga para realizar pruebas.
- `.env.ejemplo`: Plantilla para las variables de entorno (contraseñas, tokens de API y configuración general).

**Backend (`backend/`):**
- `osm_fetch.py` y `osm_routes.py`: Módulos que descargan y procesan los datos de la red vial directamente desde OpenStreetMap, evitando usar servicios de pago.
- `start.sh`: Script de arranque del servidor backend.
- `ml/`: Contiene los scripts de inteligencia artificial (`predictor.py` para calcular el tiempo estimado de llegada y `route_learner.py` para actualizar las rutas dinámicamente).

**Base de datos (`database/`):**
- `init.sql`: Script que crea las tablas, relaciones y las extensiones geoespaciales al inicializar la base de datos por primera vez.
- `migration_google_auth.sql`: Cambios en la base de datos necesarios para implementar el inicio de sesión con Google.

**Frontend (`frontend/`):**
- `src/config/database.php`: Archivo de conexión a la base de datos usando PDO.
- `src/controllers/`: Controladores de la aplicación, separados por funcionalidad (usuarios, mapas, favoritos, panel de administración).
- `src/public/`: Directorio público del servidor web. Contiene el `index.php` (punto de entrada) y utiliza `.htaccess` para las URLs amigables.
- `src/views/`: Vistas de la interfaz, organizadas según el rol del usuario (ciudadano o administrador). Incluye partes comunes como el asistente en `layout/chatbot.php`.

**IoT y Pruebas (`iot/` y `versiones/`):**
- `iot/nodo_iot.py`: Script que se ejecuta en la Raspberry Pi de los autobuses. Lee las tramas del GPS por el puerto serie, procesa la ubicación y la envía al servidor. Si se pierde la conexión, la guarda temporalmente.
- `versiones/gps_simulator.py`: Simulador que envía datos de ubicación falsos al backend para probar el sistema con varios autobuses a la vez, sin necesidad de salir a la calle a hacer pruebas.

---

## Despliegue del Sistema

El proyecto está dockerizado para facilitar su instalación y ejecución en cualquier entorno sin problemas de dependencias.

### 1. Configurar las variables de entorno
Antes de arrancar la aplicación, tienes que crear el archivo de configuración a partir de la plantilla:

```bash
cp .env.ejemplo .env
```
*(Recuerda editar el archivo `.env` resultante para configurar contraseñas seguras y añadir las credenciales de Google OAuth).*

### 2. Arrancar los servicios
Para construir las imágenes y levantar todos los contenedores, ejecuta el siguiente comando en la raíz del proyecto:

```bash
docker-compose up --build
```

### 3. Acceso a la aplicación
Una vez que los contenedores estén levantados y listos, podrás acceder a los servicios en las siguientes direcciones:

- **Frontend (Web):** [http://localhost](http://localhost) (Puerto 80)
- **Backend (API REST):** [http://localhost:5000](http://localhost:5000)
- **Base de Datos:** PostgreSQL funciona internamente dentro de la red de Docker para mayor seguridad, por lo que no está expuesto directamente hacia el exterior por defecto.