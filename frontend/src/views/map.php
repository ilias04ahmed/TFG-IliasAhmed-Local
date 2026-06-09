<div class="flex h-[calc(100vh-64px)]">
    <aside class="w-80 md:w-96 lg:w-[26rem] bg-gradient-to-b from-white to-gray-50 shadow-2xl z-20 flex flex-col transition-all duration-300 transform border-r border-gray-100" id="sidebar">
        
        <div class="p-5 border-b border-gray-100 bg-white">
            <div class="flex items-center gap-3 mb-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-teal-400 flex items-center justify-center shadow-md">
                    <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-1.447-.894L15 7m0 13V7"></path>
                    </svg>
                </div>
                <div>
                    <h2 class="text-lg font-bold text-gray-800">Rutas Activas</h2>
                    <p class="text-xs text-gray-400">Mapa interactivo en tiempo real</p>
                </div>
            </div>
            <div class="flex justify-between items-center">
                <span class="text-xs text-gray-400 flex items-center gap-1">
                    <span class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                    Actualizando en vivo
                </span>
                <button id="btn-toggle-todo" class="text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-1.5 rounded-lg transition font-medium">
                    Mostrar/Ocultar Todo
                </button>
            </div>
        </div>

        <div class="flex-grow overflow-y-auto p-4 space-y-2" id="routes-list-container">
            <div class="text-gray-300 py-8 text-center">
                <svg class="w-12 h-12 mx-auto mb-2 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 7h8a2 2 0 012 2v10a2 2 0 01-2 2H8a2 2 0 01-2-2V9a2 2 0 012-2zM8 7V5a2 2 0 012-2h4a2 2 0 012 2v2M9 12h6M9 16h6"></path>
                </svg>
                <p class="text-sm">Cargando rutas...</p>
            </div>
        </div>

        <div class="p-4 border-t border-gray-100 bg-white">
            <div id="selected-bus-info" class="hidden">
                <div class="flex items-center gap-2 mb-2">
                    <span class="w-2 h-2 bg-teal-400 rounded-full animate-pulse"></span>
                    <h3 class="font-bold text-gray-700 text-sm">Próxima Llegada Estimada</h3>
                </div>
                <div class="text-xs text-gray-400 mb-2">
                    Línea <span id="eta-linea" class="font-bold text-gray-600">--</span> &middot; Autobús <span id="eta-bus" class="font-bold text-gray-600">--</span>
                </div>
                <div class="p-4 bg-gradient-to-br from-teal-50 to-blue-50 rounded-xl text-center border border-teal-100">
                    <span class="block text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-teal-600 to-blue-600" id="eta-time">-- min</span>
                    <span class="text-xs text-gray-400 mt-1 block">a tu parada más cercana</span>
                </div>
            </div>
            <div id="no-selection" class="text-center py-3">
                <p class="text-sm text-gray-400">
                    <svg class="w-6 h-6 mx-auto mb-1 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5"></path>
                    </svg>
                    Toca un autobús en el mapa para ver su ETA
                </p>
            </div>
        </div>
    </aside>

    <div class="flex-grow relative z-10">
        <div id="map" class="h-full w-full"></div>

        <button id="btn-toggle-sidebar" class="absolute top-4 left-4 z-[500] bg-white/90 backdrop-blur-sm p-2.5 rounded-xl shadow-lg md:hidden border border-gray-100 hover:bg-gray-50 transition">
            <svg class="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
            </svg>
        </button>

        <div class="absolute bottom-6 right-6 z-[500] bg-white/90 backdrop-blur-sm rounded-xl shadow-lg border border-gray-100 px-4 py-3">
            <div class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Leyenda</div>
            <div class="flex flex-col gap-1.5 text-xs text-gray-600">
                <div class="flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 shadow-sm"></span>
                    Autobús en ruta
                </div>
                <div class="flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full border-2 border-gray-400 bg-white"></span>
                    Parada de autobús
                </div>
            </div>
        </div>

        <div id="aviso-sin-buses" class="hidden absolute top-4 left-1/2 -translate-x-1/2 z-[500] bg-white/90 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200 px-4 py-2.5 flex items-center gap-2 text-sm text-gray-600">
            <svg class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            No hay autobuses activos en este momento
        </div>
    </div>
</div>

<script>
    const map = L.map('map', {
        zoomControl: false 
    }).setView([35.8883, -5.3162], 14);

    L.control.zoom({ position: 'topright' }).addTo(map);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    function createBusIcon(color) {
        return L.divIcon({
            className: 'custom-bus-icon',
            html: `<div class="bus-marker-icon" style="background: linear-gradient(135deg, ${color}, ${color}dd);" data-color="${color}">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M8 6v6m7-6v6M2 12h19.6M18 18h3s.5-1.7.8-2.8c.1-.4.2-.8.2-1.2 0-.4-.1-.8-.2-1.2l-1.4-5C20.1 6.8 19.1 6 18 6H6C4.9 6 3.9 6.8 3.6 7.8l-1.4 5c-.1.4-.2.8-.2 1.2 0 .4.1.8.2 1.2.3 1.1.8 2.8.8 2.8h3m2 0h6"></path>
                    <circle cx="7" cy="18" r="2"></circle>
                    <circle cx="17" cy="18" r="2"></circle>
                </svg>
            </div>`,
            iconSize: [36, 36],
            iconAnchor: [18, 18],
            popupAnchor: [0, -22]
        });
    }

    const globalStopIcon = L.divIcon({
        className: 'global-stop-icon',
        html: `<div class="stop-marker-icon-global"></div>`,
        iconSize: [12, 12],
        iconAnchor: [6, 6]
    });

    let capasMapa = {};
    let infoRutas = {};
    let rutasActivas = new Set();
    let todasLasRutas = [];

    function obtenerColorRuta(ruta) {
        if (ruta.color) return ruta.color;
        
        const colores = ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4'];
        let sumaCaracteres = 0;
        const idString = String(ruta.id);
        
        for (let i = 0; i < idString.length; i++) {
            sumaCaracteres += idString.charCodeAt(i);
        }
        return colores[sumaCaracteres % colores.length];
    }

    function pintarSidebarRutas(rutas) {
        const contenedor = document.getElementById('routes-list-container');
        contenedor.innerHTML = '';

        rutas.forEach(ruta => {
            const visible = rutasActivas.has(ruta.id);
            const div = document.createElement('div');
            
            div.className = `group p-3.5 rounded-xl transition-all duration-300 flex items-center justify-between cursor-pointer border-2 ${
                visible ? 'bg-white shadow-sm border-gray-100 hover:shadow-md' : 'bg-gray-50 border-transparent opacity-60 hover:opacity-80'
            }`;

            div.onclick = () => { cambiarVisibilidadRuta(ruta.id); };
            div.onmouseenter = () => { resaltarLineaMapa(ruta.id); };
            div.onmouseleave = () => { quitarResaltadoLineaMapa(ruta.id); };

            const nombreAMostrar = ruta.name || ruta.id;
            div.innerHTML = `
                <div class="flex items-center gap-3 flex-grow min-w-0 pr-2">
                    <div class="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm shadow-sm flex-shrink-0 transition-transform group-hover:scale-110"
                         style="background: ${ruta.color}">
                        ${ruta.id}
                    </div>
                    <div class="min-w-0 py-1">
                        <div class="font-bold text-gray-900 text-sm">Línea ${ruta.id}</div>
                        <div class="font-medium text-gray-500 text-xs leading-tight mt-0.5">${nombreAMostrar}</div>
                        <div class="text-[10px] uppercase font-bold tracking-wide mt-1 ${visible ? 'text-green-500' : 'text-gray-400'}">
                            ${visible ? '🟢 EN EL MAPA' : '⚫ OCULTA'}
                        </div>
                    </div>
                </div>
                <div class="flex-shrink-0 ml-2">
                    <div class="w-5 h-5 rounded-md border-2 flex items-center justify-center transition ${visible ? 'bg-blue-500 border-blue-500' : 'border-gray-300 bg-white'}">
                        ${visible ? '<svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg>' : ''}
                    </div>
                </div>
            `;
            contenedor.appendChild(div);
        });
    }

    function cambiarVisibilidadRuta(idRuta) {
        if (rutasActivas.has(idRuta)) {
            rutasActivas.delete(idRuta);
        } else {
            rutasActivas.add(idRuta);
        }
        actualizarCapasMapa();
        pintarSidebarRutas(Object.values(infoRutas));
    }

    function alternarTodasLasRutas() {
        let algunaVisible = false;
        rutasActivas.forEach(id => {
            if (infoRutas[id]) algunaVisible = true;
        });
        
        if (algunaVisible) {
            rutasActivas.clear();
        } else {
            todasLasRutas.forEach(id => rutasActivas.add(id));
        }
        actualizarCapasMapa();
        pintarSidebarRutas(Object.values(infoRutas));
    }

    function actualizarCapasMapa() {
        for (let idRuta in infoRutas) {
            const visible = rutasActivas.has(idRuta);
            const capaCamino = capasMapa['route_' + idRuta];
            const capaParadas = capasMapa['stops_' + idRuta];

            if (capaCamino) {
                if (visible && !map.hasLayer(capaCamino)) map.addLayer(capaCamino);
                else if (!visible && map.hasLayer(capaCamino)) map.removeLayer(capaCamino);
            }
            if (capaParadas) {
                if (visible && !map.hasLayer(capaParadas)) map.addLayer(capaParadas);
                else if (!visible && map.hasLayer(capaParadas)) map.removeLayer(capaParadas);
            }
        }

        for (let clave in capasMapa) {
            if (clave.startsWith('BUS_')) {
                const marcadorBus = capasMapa[clave];
                const idRutaBus = marcadorBus.options.routeId;
                
                if (infoRutas[idRutaBus] && !rutasActivas.has(idRutaBus)) {
                    if (map.hasLayer(marcadorBus)) map.removeLayer(marcadorBus);
                } else {
                    if (!map.hasLayer(marcadorBus)) map.addLayer(marcadorBus);
                }
            }
        }
    }

    function resaltarLineaMapa(idRuta) {
        if (!rutasActivas.has(idRuta)) return;
        const capa = capasMapa['route_' + idRuta];
        if (capa) {
            capa.eachLayer(linea => {
                linea.setStyle({ weight: 8, opacity: 1 });
                linea.bringToFront();
            });
        }
        const capaParadas = capasMapa['stops_' + idRuta];
        if (capaParadas) {
            capaParadas.eachLayer(marcador => {
                if (marcador._icon) marcador._icon.style.transform = 'scale(1.4)';
            });
        }
    }

    function quitarResaltadoLineaMapa(idRuta) {
        if (!rutasActivas.has(idRuta)) return;
        const capa = capasMapa['route_' + idRuta];
        if (capa) {
            capa.eachLayer(linea => {
                linea.setStyle({ weight: 5, opacity: 0.65 });
            });
        }
        const capaParadas = capasMapa['stops_' + idRuta];
        if (capaParadas) {
            capaParadas.eachLayer(marcador => {
                if (marcador._icon) marcador._icon.style.transform = 'scale(1)';
            });
        }
    }

    async function obtenerRutasServidor() {
        try {
            const res = await fetch(API_BASE + '/api/routes');
            if (!res.ok) return;
            const datos = await res.json();

            for (let clave in capasMapa) {
                if (clave.startsWith('route_') || clave.startsWith('stops_')) {
                    map.removeLayer(capasMapa[clave]);
                    delete capasMapa[clave];
                }
            }
            infoRutas = {};
            
            if (datos.routes) {
                datos.routes.forEach(ruta => {
                    const colorRuta = obtenerColorRuta(ruta);
                    ruta.color = colorRuta;
                    
                    infoRutas[ruta.id] = ruta;
                    todasLasRutas.push(ruta.id);
                    rutasActivas.add(ruta.id);

                    if (ruta.path && ruta.path.length > 0) {
                        const tramos = Array.isArray(ruta.path[0]) ? ruta.path : [ruta.path];
                        const grupoLineas = L.featureGroup();

                        tramos.forEach(tramo => {
                            const coordenadas = tramo.map(p => [p.lat, p.lon]);
                            L.polyline(coordenadas, {
                                color: colorRuta,
                                weight: 5,
                                opacity: 0.65,
                                lineCap: 'round',
                                lineJoin: 'round'
                            }).addTo(grupoLineas);
                        });
                        
                        if (rutasActivas.has(ruta.id)) grupoLineas.addTo(map);
                        capasMapa['route_' + ruta.id] = grupoLineas;
                    }

                    if (ruta.stops) {
                        const marcadoresParadas = [];
                        ruta.stops.forEach(parada => {
                            const iconoParada = L.divIcon({
                                className: 'custom-stop-icon',
                                html: `<div class="stop-marker-icon-route" style="border-color: ${ruta.color}"></div>`,
                                iconSize: [14, 14],
                                iconAnchor: [7, 7]
                            });

                            const marcador = L.marker([parada.lat, parada.lon], { icon: iconoParada, zIndexOffset: 1000 });
                            marcador.bindPopup(`
                                <div class="stop-popup">
                                    <div class="stop-popup__name">${parada.name}</div>
                                    <div class="stop-popup__badge" style="background: ${ruta.color}15;">
                                        <span class="stop-popup__badge-dot" style="background: ${ruta.color}"></span>
                                        <span class="stop-popup__badge-text" style="color: ${ruta.color}">${ruta.id}</span>
                                    </div>
                                </div>
                            `);
                            marcador.bindTooltip(parada.name, { direction: 'top', offset: [0, -10], className: 'custom-tooltip' });
                            marcadoresParadas.push(marcador);
                        });

                        const grupoParadas = L.layerGroup(marcadoresParadas);
                        if (rutasActivas.has(ruta.id)) grupoParadas.addTo(map);
                        capasMapa['stops_' + ruta.id] = grupoParadas;
                    }
                });

                todasLasRutas = Object.keys(infoRutas);
                pintarSidebarRutas(Object.values(infoRutas));
            }
        } catch (err) {
            console.error("Error al procesar rutas:", err);
        }
    }

    async function obtenerTodasLasParadas() {
        try {
            const res = await fetch(API_BASE + '/api/stops');
            if (!res.ok) return;
            const paradas = await res.json();

            const marcadores = paradas.map(parada => {
                const marcador = L.marker([parada.lat, parada.lon], { icon: globalStopIcon, zIndexOffset: 0 });
                marcador.bindPopup(`
                    <div class="global-stop-popup">
                        <div class="global-stop-popup__name">${parada.name}</div>
                        <div class="global-stop-popup__sub">Parada de Autobús</div>
                    </div>
                `);
                marcador.bindTooltip(parada.name, { direction: 'top', offset: [0, -8], className: 'custom-tooltip' });
                return marcador;
            });

            capasMapa['global_stops'] = L.layerGroup(marcadores).addTo(map);
        } catch (err) {
            console.error("Error cargando paradas generales:", err);
        }
    }

    function moverAutobusSuave(marcador, destinoLat, destinoLon, tiempoTotal) {
        const posicionInicial = marcador.getLatLng();
        const inicioLat = posicionInicial.lat;
        const inicioLon = posicionInicial.lng;

        if (Math.abs(destinoLat - inicioLat) + Math.abs(destinoLon - inicioLon) < 0.000001) return;

        const momentoInicio = performance.now();

        function actualizarPosicion(momentoActual) {
            const porcentaje = (momentoActual - momentoInicio) / tiempoTotal;

            if (porcentaje >= 1) {
                marcador.setLatLng([destinoLat, destinoLon]);
                return;
            }

            const latActual = inicioLat + (destinoLat - inicioLat) * porcentaje;
            const lonActual = inicioLon + (destinoLon - inicioLon) * porcentaje;
            marcador.setLatLng([latActual, lonActual]);

            requestAnimationFrame(actualizarPosicion);
        }

        requestAnimationFrame(actualizarPosicion);
    }

    async function refrescarPosicionBuses() {
        try {
            const res = await fetch(`${API_BASE}/api/buses?_nocache=${Date.now()}`);
            if (!res.ok) return;
            const listaBuses = await res.json();

            listaBuses.forEach(bus => {
                const colorBus = infoRutas[bus.route_id] ? infoRutas[bus.route_id].color : '#6366F1';
                const visible = rutasActivas.has(bus.route_id);

                if (!capasMapa[claveBus]) {
                    const nuevoMarcador = L.marker([bus.lat, bus.lon], {
                        icon: createBusIcon(colorBus),
                        routeId: bus.route_id
                    });

                    nuevoMarcador.addTo(map);
                    nuevoMarcador.bindPopup(`
                        <div class="bus-popup">
                            <div class="bus-popup__title" style="color: ${colorBus};">Línea ${bus.route_id}</div>
                            <div class="bus-popup__sub">Vehículo: ${bus.id}</div>
                        </div>
                    `);

                    nuevoMarcador.on('click', async () => {
                        document.getElementById('no-selection').classList.add('hidden');
                        document.getElementById('selected-bus-info').classList.remove('hidden');
                        document.getElementById('eta-time').innerText = "Calculando...";
                        document.getElementById('eta-linea').innerText = bus.route_id || '--';
                        document.getElementById('eta-bus').innerText = bus.id;

                        try {
                            const resEta = await fetch(`${API_BASE}/api/eta/${bus.route_id}`);
                            const datosEta = await resEta.json();

                            if (datosEta.eta_seconds !== null) {
                                const minutos = Math.floor(datosEta.eta_seconds / 60);
                                const segundos = Math.floor(datosEta.eta_seconds % 60);
                                let textoTiempo = "";
                                
                                if (minutos > 0) textoTiempo += minutos + " min ";
                                if (segundos > 0 || minutos === 0) textoTiempo += segundos + " seg";

                                document.getElementById('eta-time').innerText = textoTiempo.trim();
                            } else {
                                document.getElementById('eta-time').innerText = "Calculando...";
                            }
                        } catch (err) {
                            document.getElementById('eta-time').innerText = "--";
                        }
                    });

                    capasMapa[claveBus] = nuevoMarcador;
                } else {
                    const marcadorExistente = capasMapa[claveBus];
                    moverAutobusSuave(marcadorExistente, bus.lat, bus.lon, 900);

                    if (infoRutas.hasOwnProperty(bus.route_id) && !visible) {
                        if (map.hasLayer(marcadorExistente)) map.removeLayer(marcadorExistente);
                    } else {
                        if (!map.hasLayer(marcadorExistente)) map.addLayer(marcadorExistente);
                    }
                }
            });

            const aviso = document.getElementById('aviso-sin-buses');
            if (aviso) {
                if (listaBuses.length === 0) {
                    aviso.classList.remove('hidden');
                } else {
                    aviso.classList.add('hidden');
                }
            }
        } catch (err) {
            console.error("Error cargando localización de autobuses:", err);
        }
    }

    document.getElementById('btn-toggle-todo').addEventListener('click', alternarTodasLasRutas);
    document.getElementById('btn-toggle-sidebar').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('-translate-x-full');
    });

    obtenerTodasLasParadas().then(() => {
        obtenerRutasServidor();
        setInterval(refrescarPosicionBuses, 1000);
    });
</script>