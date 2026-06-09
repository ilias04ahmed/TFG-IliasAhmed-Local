<div class="relative bg-white overflow-hidden">
    <div class="max-w-7xl mx-auto">
        <div class="relative z-10 pb-8 bg-white sm:pb-16 md:pb-20 lg:max-w-2xl lg:w-full lg:pb-28 xl:pb-32">

            <svg class="hidden lg:block absolute right-0 inset-y-0 h-full w-48 text-white transform translate-x-1/2"
                viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
                <polygon points="50,0 100,0 50,100 0,100" fill="currentColor" />
            </svg>

            <main class="mt-10 mx-auto max-w-7xl px-4 sm:mt-12 sm:px-6 md:mt-16 lg:mt-20 lg:px-8 xl:mt-28">
                <div class="sm:text-center lg:text-left">
                    <h1 class="text-4xl tracking-tight font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
                        <span class="block xl:inline">Transporte Inteligente</span>
                        <span class="block text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-teal-500 xl:inline">
                            para Ceuta
                        </span>
                    </h1>
                    <p class="mt-3 text-base text-gray-500 sm:mt-5 sm:text-lg sm:max-w-xl sm:mx-auto md:mt-5 md:text-xl lg:mx-0">
                        La revolución del transporte público en tu mano. Consulta rutas en tiempo real, estima llegadas
                        y optimiza tu tiempo con nuestra plataforma de última generación.
                    </p>
                    
                    <div class="mt-5 sm:mt-8 sm:flex sm:justify-center lg:justify-start gap-3">
                        <div class="rounded-md shadow">
                            <a href="/map"
                                class="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 md:py-4 md:text-lg transition duration-300 shadow-lg transform hover:-translate-y-1">
                                Ver Mapa en Vivo
                            </a>
                        </div>
                        <div class="mt-3 sm:mt-0">
                            <a href="/horarios"
                                class="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-blue-700 bg-blue-50 hover:bg-blue-100 md:py-4 md:text-lg transition duration-300">
                                Consultar Horarios
                            </a>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    </div>

    <div class="lg:absolute lg:inset-y-0 lg:right-0 lg:w-1/2 bg-gray-50 flex items-center justify-center overflow-hidden">
        <div class="absolute w-96 h-96 bg-blue-300 rounded-full mix-blend-multiply filter blur-3xl opacity-30 top-0 left-0"></div>
        <div class="absolute w-96 h-96 bg-teal-300 rounded-full mix-blend-multiply filter blur-3xl opacity-30 bottom-0 right-0"></div>

        <div class="relative z-10 text-center transform hover:scale-105 transition duration-700">
            <div class="text-blue-600 filter drop-shadow-2xl">
                <svg class="w-48 h-48 mx-auto" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="10" y="30" width="80" height="40" rx="4" fill="currentColor" opacity="0.9" />
                    <rect x="15" y="35" width="12" height="15" rx="1" fill="white" opacity="0.8" />
                    <rect x="32" y="35" width="12" height="15" rx="1" fill="white" opacity="0.8" />
                    <rect x="49" y="35" width="12" height="15" rx="1" fill="white" opacity="0.8" />
                    <rect x="66" y="35" width="19" height="15" rx="1" fill="white" opacity="0.8" />
                    <circle cx="25" cy="72" r="6" fill="#1f2937" />
                    <circle cx="25" cy="72" r="2.5" fill="#9ca3af" />
                    <circle cx="75" cy="72" r="6" fill="#1f2937" />
                    <circle cx="75" cy="72" r="2.5" fill="#9ca3af" />
                    <rect x="10" y="55" width="80" height="2" fill="#1f2937" opacity="0.2" />
                    <rect x="12" y="60" width="4" height="2" rx="1" fill="#fbbf24" />
                </svg>
            </div>
            
            <div class="mt-8">
                <div class="inline-flex items-center px-4 py-2 rounded-full border border-gray-200 bg-white shadow-sm text-sm font-medium text-gray-500">
                    <span class="flex h-2 w-2 relative mr-2">
                        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                    Sistema Operativo y Online
                </div>
            </div>
        </div>
    </div>
</div>

<div id="avisos-publico" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 hidden">
    <div class="text-center mb-8">
        <h2 class="text-3xl font-bold text-gray-900 flex items-center justify-center gap-3">
            <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
            </svg>
            Avisos e Información
        </h2>
        <p class="mt-2 text-gray-500">Últimas novedades sobre el servicio de transporte</p>
    </div>
    
    <div id="avisos-publico-list" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"></div>
</div>

<script>
    const API_BASE = 'http://localhost:5000';
    
    const TIPO_CONFIG = {
        info: { icon: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>', label: 'Información', bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700' },
        averia: { icon: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>', label: 'Avería', bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700' },
        retraso: { icon: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>', label: 'Retraso', bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-700' },
        cambio_ruta: { icon: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>', label: 'Cambio Ruta', bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-700' }
    };

    function loadPublicAvisos() {
        fetch(`${API_BASE}/api/avisos`)
            .then(res => res.json())
            .then(avisos => {
                if (!avisos || avisos.length === 0) return;

                const container = document.getElementById('avisos-publico');
                const list = document.getElementById('avisos-publico-list');
                
                container.classList.remove('hidden');
                let htmlContent = '';

                avisos.forEach(a => {
                    const cfg = TIPO_CONFIG[a.tipo] || TIPO_CONFIG.info;
                    
                    const fecha = new Date(a.creado_en).toLocaleDateString('es-ES', {
                        day: '2-digit', month: 'short', year: 'numeric'
                    });
                    
                    let lineaTag = '';
                    if (a.linea_codigo) {
                        lineaTag = `
                            <span class="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full flex items-center gap-1">
                                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h8a2 2 0 012 2v10a2 2 0 01-2 2H8a2 2 0 01-2-2V9a2 2 0 012-2z"></path>
                                </svg> 
                                ${a.linea_codigo}
                            </span>`;
                    }

                    const tituloLimpio = escapeTexto(a.titulo);
                    const mensajeLimpio = escapeTexto(a.mensaje);

                    htmlContent += `
                        <div class="rounded-xl border ${cfg.border} ${cfg.bg} p-5 transition transform hover:-translate-y-1 hover:shadow-md">
                            <div class="flex items-center gap-2 mb-2">
                                <span class="flex-shrink-0">${cfg.icon}</span>
                                <span class="text-xs font-semibold uppercase tracking-wide ${cfg.text}">${cfg.label}</span>
                                ${lineaTag}
                            </div>
                            <h3 class="font-bold text-gray-900 text-base mb-1">${tituloLimpio}</h3>
                            <p class="text-sm text-gray-600 leading-relaxed">${mensajeLimpio}</p>
                            <p class="text-xs text-gray-400 mt-3">${fecha}</p>
                        </div>`;
                });

                list.innerHTML = htmlContent;
            })
            .catch(err => {
                console.error('Error al conectar con la API de avisos:', err);
            });
    }

    function escapeTexto(str) {
        if (!str) return '';
        return str.toString()
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    document.addEventListener('DOMContentLoaded', loadPublicAvisos);
</script>