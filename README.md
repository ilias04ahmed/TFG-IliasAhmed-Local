# TFG: Development of a Real-Time Information and Geolocating System for Ceuta's Public Transport Network

> **Read this in other languages:** [Español (Spanish)](README.es.md)
 
**Ilias Ahmed Ahmed** B.S. in Computer Engineering  
Bachelor's Thesis (Trabajo de Fin de Grado)  

---

## Project Description

This repository contains the outcome of my Bachelor's Thesis: a full-stack web application designed for the real-time management and tracking of an urban bus fleet. The core motivation behind this project is the need for a self-hosted system that eliminates reliance on costly third-party APIs, while incorporating machine learning capabilities to learn from actual route behaviors.

The primary goal is to provide both administrators and end-users with an intuitive platform to track bus locations, estimate arrival times, handle system incidents, and save favorite routes—all while minimizing latency and ensuring high availability even during network disruptions.

---

## System Architecture

The architecture is divided into three main building blocks, supplemented by an edge computing device:

### Backend (Python + Flask)
Handles core business logic, provides a RESTful API, manages live GPS data ingestion, and hosts the integrated Machine Learning modules.

### Frontend (PHP)
A lightweight web interface built in PHP using a custom MVC pattern to streamline resource consumption and facilitate swift deployments.

### Database (PostgreSQL)
The central storage system. It manages users, routes, bus stops, vehicles, live GPS logs, schedules, and incident tracking. It includes native support for geospatial queries and archives historical tracking data utilized by the machine learning engine.

### IoT Node (Python + GPS)
In addition to the three core tiers, a dedicated script runs on an on-board Raspberry Pi connected to a hardware GPS module. It parses NMEA sentences, extracts positioning metrics, and transmits them to the backend. It features an offline local buffer to prevent data loss during connection dropouts.

---

## Machine Learning Modules

### RouteLearner
An automated pipeline that extracts and identifies transit routes directly from raw GPS coordinate streams. If a bus consistently deviates from its scheduled path over a given threshold, the system automatically recalculates and updates the route network.

### TravelTimePredictor
A predictive model designed to estimate the Estimated Time of Arrival (ETA) based on historical transit data. It uses serialized `joblib` models to avoid continuous, resource-heavy retraining pipelines.

---

## Repository Structure

The project is strictly organized under the following modular directory tree:

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
```

## Core Components Breakdown

### Root Directory
- `docker-compose.yml`: Defines and orchestrates multi-container configurations, internal networks, and persistent storage volumes.
- `usage_scenario.yml`: Sets up load testing scenarios and simulation profiles to evaluate system performance under stress.
- `.env.ejemplo`: Environment variables template (used for securing database credentials, API secrets, and global configs).

### Backend (`backend/`)
- `osm_fetch.py` & `osm_routes.py`: Standalone modules that pull and parse geospatial street maps directly from the OpenStreetMap API, bypassing commercial paywalls.
- `start.sh`: Shell script handling containerized environment preparation and server boot workflows.
- `ml/`: Houses predictive services (`predictor.py` for live ETA tracking calculations and `route_learner.py` for runtime network graph modifications).

### Database (`database/`)
- `init.sql`: Creates database schemas, constraints, indexes, and enables required geospatial extensions upon initialization.
- `migration_google_auth.sql`: DB schema updates necessary to support OAuth2 Google Sign-In capabilities.

### Frontend (`frontend/`)
- `src/config/database.php`: Direct PostgreSQL abstraction wrapper using secure PHP Data Objects (PDO).
- `src/controllers/`: Application controllers isolated by domain responsibility (users, dynamic maps, administration dashboards).
- `src/public/`: Web server entry point containing `index.php` and an optimized `.htaccess` routing engine for clean URLs.
- `src/views/`: Interactive user interface files segmented by access roles (commuters vs. operators). Includes shared extensions like the support assistant found in `layout/chatbot.php`.

### IoT & Simulation (`iot/` & `versiones/`)
- `iot/nodo_iot.py`: Serial reader interface built for edge-mounted microcontrollers. It translates live GPS NMEA logs and buffers packets locally if data handshakes drop out.
- `versiones/gps_simulator.py`: Multithreaded deployment test simulator designed to broadcast mock bus positioning telemetry back into the API for testing without requiring fieldwork.

---

## System Deployment

The entire stack is Dockerized to ensure effortless execution across multiple operating systems without encountering local dependency conflicts.

### 1. Set Up Environment Variables
Initialize the target configuration file by replicating the provided template setup:

```bash
cp .env.ejemplo .env
``` 
### 2. Boot Application Containers
Compile underlying container images and launch the infrastructure services by executing:

```bash
docker-compose up --build
``` 
### 3. Application Entry Points
Once the orchestrator completes running the database entry points, map endpoints become reachable at the following addresses:

- **Web Frontend:** [http://localhost](http://localhost) (Port 80)
- **REST API Backend:** [http://localhost:5000](http://localhost:5000)
- **Database Engine:** PostgreSQL operates entirely within the secure, private Docker bridge network and is not exposed to external ports by default.