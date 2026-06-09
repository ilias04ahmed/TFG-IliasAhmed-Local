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

Descripción Detallada de Componentes Críticos

Raíz del Proyecto:

- docker-compose.yml: Archivo de orquestación encargado de configurar las redes virtuales internas, los volúmenes de almacenamiento y compilar de forma unificada las imágenes del ecosistema multi-servicio.

- usage_scenario.yml: Archivo de configuración que parametriza escenarios de prueba y flujos de simulación de carga del sistema.

- .env.ejemplo: Plantilla centralizada de variables de entorno (credenciales criptográficas, tokens de APIs externas y configuraciones de red).

Servicio Backend (backend/):

- osm_fetch.py / osm_routes.py: Módulos de integración geográfica orientados a conectar, descargar e interpretar redes viales complejas directamente desde la API Overpass de OpenStreetMap sin intermediarios comerciales.

- start.sh: Script bash de inicialización automatizada del servidor web adaptativo.

- ml/: Contiene el núcleo analítico predictivo (predictor.py para cálculos síncronos de ETA y route_learner.py para la actualización dinámica de recorridos).

Persistencia (database/):

- init.sql: Script de DDL y DML encargado de levantar el esquema relacional, tipos específicos, restricciones espaciales y los triggers geográficos iniciales.

- migration_google_auth.sql: Modificaciones estructurales para dotar a la base de datos de soporte a la federación de identidades mediante Google OAuth.

Servicio Web (frontend/):

- src/config/database.php: Abstracción de conexión a la persistencia mediante controladores PDO parametrizados.

- src/controllers/: Controladores lógicos encapsulados por dominio que gestionan la seguridad (AuthController), la interacción espacial (MapController), las preferencias del ciudadano (FavoritosController) y las auditorías de administración (AdminController).

- src/public/: Punto de entrada único del servidor web apoyado en un archivo .htaccess para forzar el enrutamiento amigable (Pretty URLs) hacia el front controller (index.php).

- src/views/: Plantillas estructuradas de interfaz de usuario organizadas por privilegios, incluyendo módulos transversales en el directorio layout/ como un asistente automatizado (chatbot.php).

Entorno IoT y Validación (iot/ y versiones/):

- iot/nodo_iot.py: Componente de software destinado al hardware físico embarcado. Gestiona la conexión serie UART con el chipset satelital, realiza el análisis (parsing) de sentencias NMEA 0183 y controla el almacenamiento local intermedio en modo offline.

- versiones/gps_simulator.py: Módulo de testing automatizado capaz de emular el comportamiento dinámico de múltiples autobuses de manera simultánea, inyectando telemetría artificial al backend para estresar el sistema y validar el rendimiento de los modelos sin requerir despliegues físicos en ruta.

Requisitos y Despliegue del Sistema
El entorno de ejecución completo se encuentra empaquetado bajo arquitecturas de contenedores aislados de grado industrial, garantizando la portabilidad absoluta del sistema con independencia del sistema operativo anfitrión.

Paso 1: Configuración del Entorno Seguro
Antes de proceder con el arranque, es imperativo instanciar el archivo de configuración global a partir de la plantilla provista en la raíz:

Bash
cp .env.ejemplo .env
(Nota: Es obligatorio editar el archivo .env resultante para definir contraseñas robustas de base de datos y los identificadores correspondientes del servicio de autenticación federada).

Paso 2: Compilación y Lanzamiento General
Para compilar las imágenes personalizadas desde los archivos de definición Dockerfile, enlazar las redes internas expuestas y levantar todos los servicios integrados en modo persistente, ejecute en su terminal:


docker-compose up --build
Puntos de Acceso Operacionales
Una vez que el orquestador valide el estado de salud de todos los contenedores (health checks), los servicios estarán disponibles en la máquina local bajo las siguientes interfaces de red:

Plataforma Web (Frontend Ciudadano/Administración): http://localhost (Puerto estándar HTTP 80)

Núcleo Operacional (API REST Backend): http://localhost:5000

Motor de Persistencia Relacional: Puerto aislado interno de PostgreSQL integrado de forma privada dentro de la red del contenedor para mitigar vectores de ataque externos.