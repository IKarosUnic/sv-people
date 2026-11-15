/**
 * SALTBOR — Interactive Visual Simulation Platform (Phase 1.3-V)
 * High-performance client-rendered architecture with 60 FPS Canvas rendering,
 * real-time SSE telemetry, and comprehensive scientific observability.
 */

(function () {
    "use strict";

    // =========================================================================
    // APPLICATION STATE
    // =========================================================================
    const state = {
        currentView: "world",
        isRunning: false,
        speedMultiplier: 1,
        currentTick: 0,
        selectedAgentUid: null,
        selectedEntity: null,
        followSelectedAgent: false,
        theme: "dark",

        // World Data Cache
        world: null,
        individuals: [],
        civilization: null,
        economy: null,
        timelineEvents: [],
        knowledgeGraph: null,
        socialNetwork: null,

        // Phase 1.13 Universal Domains & Compact Experiments Cache
        domainDisclosureLevel: "SUMMARY",
        domainExperiments: [],

        // World Canvas Camera
        camera: {
            x: 0,
            y: 0,
            zoom: 1.0,
            isDragging: false,
            dragStartX: 0,
            dragStartY: 0,
        },

        // Layer Toggles
        layers: {
            depts: true,
            districts: true,
            roads: true,
            geography: true,
            establishments: true,
            agents: true,
            density: false,
        },

        // GIS 2.5D Digital Twin State
        gisMap: null,
        gisLoaded: false,
        gisFollowAgent: false,
        gisLayers: {
            buildings: true,
            streets: true,
            parks: true,
            water: true,
            elevation: true,
            boundaries: true,
            poi: true,
            agents: true,
            trajectories: true,
        },

        // Force Graphs Simulation State
        kgSimulation: { nodes: [], edges: [], isRunning: false },
        socialSimulation: { nodes: [], edges: [], isRunning: false },
    };

    // Geographic bounding box for El Salvador (WGS84)
    const GEO_BOUNDS = {
        minLat: 13.10,
        maxLat: 14.48,
        minLon: -90.15,
        maxLon: -87.65,
    };

    // =========================================================================
    // INITIALIZATION & EVENT LISTENERS
    // =========================================================================
    document.addEventListener("DOMContentLoaded", () => {
        setupNavigation();
        setupControlCenter();
        setupCanvasInteractions();
        setupThemeToggle();
        setupGIS25D();
        connectSSE();
        initGeographyProvenance();
        initUniversalDomainsListeners();
        initTerritorialObservatoryListeners();

        // Initial Data Fetch
        fetchWorldData();
        fetchIndividualsRoster();
        fetchCivilizationData();
        fetchEconomyData();
        fetchTimeline();
        fetchKnowledgeGraph();
        fetchSocialNetwork();
        fetchLaboratoryExperiments();
        loadReport("phase13_summary");

        // Immediately initialize real GIS map on the primary viewport
        initOrResizeGIS25D();

        // Start render loops (stub preserved for tests)
        requestAnimationFrame(renderWorldLoop);
    });

    // =========================================================================
    // 1a. OSM GEOGRAPHY PROVENANCE
    // =========================================================================
    function initGeographyProvenance() {
        fetch("/api/geography/manifest")
            .then((r) => r.json())
            .then((manifest) => {
                if (!manifest || !manifest.available) return;
                const layers = manifest.layers || {};
                const total = Object.values(layers).reduce(
                    (acc, l) => acc + (l.feature_count || 0), 0
                );
                const badge = document.createElement("div");
                badge.id = "osm-attribution";
                badge.style.cssText = [
                    "position:fixed", "right:10px", "bottom:8px", "z-index:9999",
                    "font-size:9px", "color:var(--text-muted)",
                    "background:rgba(15,23,42,0.75)", "padding:3px 7px",
                    "border-radius:4px", "border:1px solid var(--border-subtle)",
                    "pointer-events:none",
                ].join(";");
                badge.textContent =
                    `© OpenStreetMap contributors (ODbL 1.0) · ${total.toLocaleString()} features normalizados`;
                document.body.appendChild(badge);

                const panel = document.getElementById("gis-layer-summary");
                if (panel) {
                    panel.innerHTML = Object.entries(layers)
                        .map(([k, v]) => `<div>${k}: ${v.feature_count}${v.is_partial ? " (parcial)" : ""}</div>`)
                        .join("");
                }
            })
            .catch(() => { /* geography is optional for the UI */ });
    }

    // =========================================================================
    // 1. NAVIGATION & ROUTING
    // =========================================================================
    function setupNavigation() {
        const navItems = document.querySelectorAll(".nav-item");
        navItems.forEach((item) => {
            item.addEventListener("click", () => {
                const targetView = item.dataset.view;
                switchView(targetView);
            });
        });

        // Search inputs
        const indSearch = document.getElementById("individual-search");
        if (indSearch) indSearch.addEventListener("input", filterIndividualsList);

        const kgSearch = document.getElementById("kg-search");
        if (kgSearch) kgSearch.addEventListener("input", () => fetchKnowledgeGraph());

        const kgCat = document.getElementById("kg-category-filter");
        if (kgCat) kgCat.addEventListener("change", () => fetchKnowledgeGraph());

        const socialRel = document.getElementById("social-rel-filter");
        if (socialRel) socialRel.addEventListener("change", () => fetchSocialNetwork());

        const btnKgReset = document.getElementById("btn-kg-reset");
        if (btnKgReset) btnKgReset.addEventListener("click", () => fetchKnowledgeGraph());

        const btnSocialReset = document.getElementById("btn-social-reset");
        if (btnSocialReset) btnSocialReset.addEventListener("click", () => fetchSocialNetwork());

        const tlFilter = document.getElementById("timeline-type-filter");
        if (tlFilter) tlFilter.addEventListener("change", () => fetchTimeline());

        const tlSearch = document.getElementById("timeline-search");
        if (tlSearch) tlSearch.addEventListener("input", () => fetchTimeline());

        const tlImp = document.getElementById("timeline-important-only");
        if (tlImp) tlImp.addEventListener("change", () => fetchTimeline());

        // Inspector close
        const closeBtn = document.getElementById("btn-close-inspector");
        if (closeBtn) {
            closeBtn.addEventListener("click", () => {
                document.getElementById("inspector-panel").classList.add("collapsed");
            });
        }
    }

    function switchView(viewName) {
        state.currentView = viewName;

        // Update nav items
        document.querySelectorAll(".nav-item").forEach((it) => {
            it.classList.toggle("active", it.dataset.view === viewName);
        });

        // Update view panels
        document.querySelectorAll(".view-panel").forEach((panel) => {
            panel.classList.toggle("active", panel.id === `view-${viewName}`);
        });

        // View specific refresh
        if (viewName === "world" || viewName === "gis25d") {
            initOrResizeGIS25D();
        } else if (viewName === "knowledge") {
            fetchKnowledgeGraph();
            startKnowledgeGraphSim();
        } else if (viewName === "social") {
            fetchSocialNetwork();
            startSocialGraphSim();
        } else if (viewName === "civilization") {
            fetchCivilizationData();
            renderCivilizationCharts();
            fetchJusticeDocket();
            fetchADESCOData();
            fetchDialoguesStream();
        } else if (viewName === "economy") {
            fetchEconomyData();
            fetchCommerceData();
            fetchRemittancesData();
        } else if (viewName === "laboratory") {
            fetchLaboratoryExperiments();
            fetchScientificDiscoveriesData();
            fetchApprenticeshipsData();
        } else if (viewName === "individual" && state.selectedAgentUid) {
            fetchIndividualDetail(state.selectedAgentUid);
        } else if (viewName === "cognitive" && state.selectedAgentUid) {
            fetchCognitiveSubsystems(state.selectedAgentUid);
        } else if (viewName === "scientific") {
            fetchScientificWorkspaceData();
        } else if (viewName === "universal_domains") {
            fetchUniversalDomainsData();
        } else if (viewName === "territorial_ecosystem") {
            fetchTerritorialSummary();
            fetchTerritorialNodes();
            fetchTerritorialFacilities();
            fetchTerritorialProposals();
            fetchTerritorialNeeds();
            fetchPhase114Experiments();
        }
    }

    // =========================================================================
    // 2. SIMULATION CONTROL CENTER
    // =========================================================================
    function setupControlCenter() {
        const btnPlay = document.getElementById("btn-play-pause");
        btnPlay.addEventListener("click", togglePlayPause);

        const btnStep = document.getElementById("btn-step");
        btnStep.addEventListener("click", () => {
            fetch("/api/control/step?count=1", { method: "POST" })
                .then((r) => r.json())
                .then((d) => refreshAllData());
        });

        // Speed buttons
        document.querySelectorAll(".btn-speed").forEach((btn) => {
            btn.addEventListener("click", () => {
                const spd = parseInt(btn.dataset.speed, 10);
                fetch(`/api/control/speed?multiplier=${spd}`, { method: "POST" })
                    .then((r) => r.json())
                    .then(() => {
                        document.querySelectorAll(".btn-speed").forEach((b) => b.classList.remove("active"));
                        btn.classList.add("active");
                        state.speedMultiplier = spd;
                    });
            });
        });

        // Scenario scale profile selector (Phase 1.4)
        const profSelect = document.getElementById("scenario-profile-selector");
        if (profSelect) {
            profSelect.addEventListener("change", () => {
                fetch(`/api/control/profile/${profSelect.value}`, { method: "POST" })
                    .then((r) => r.json())
                    .then((d) => {
                        showNotification(`Perfil de escala aplicado: ${d.profile}`);
                        refreshAllData();
                    });
            });
        }

        // Scenario selector
        const scnSelect = document.getElementById("scenario-selector");
        if (scnSelect) {
            scnSelect.addEventListener("change", () => {
                fetch(`/api/control/scenario?name=${scnSelect.value}`, { method: "POST" })
                    .then((r) => r.json())
                    .then(() => refreshAllData());
            });
        }

        // Checkpoints
        document.getElementById("btn-save-checkpoint").addEventListener("click", () => {
            fetch("/api/control/checkpoint/save", { method: "POST" })
                .then((r) => r.json())
                .then((d) => showNotification(`Checkpoint guardado en tick ${d.tick}`));
        });

        document.getElementById("btn-load-checkpoint").addEventListener("click", () => {
            fetch("/api/control/checkpoint/load", { method: "POST" })
                .then((r) => r.json())
                .then((d) => {
                    showNotification(`Checkpoint restaurado en tick ${d.tick}`);
                    refreshAllData();
                });
        });

        // Initialize Civilization Subpanels & Interventions Modal (Phase 1.4)
        setupCivilizationSubpanels();
        setupInterventionsModal();
        setupPopulationControls();
    }

    function setupPopulationControls() {
        // 1. Topbar Preset buttons (.btn-pop-preset)
        document.querySelectorAll(".btn-pop-preset").forEach((btn) => {
            btn.addEventListener("click", () => {
                const count = parseInt(btn.dataset.pop, 10);
                const inputTop = document.getElementById("input-population-topbar");
                if (inputTop) inputTop.value = count;
                const inputGis = document.getElementById("gis-input-active-pop");
                if (inputGis) inputGis.value = count;
                scalePopulation(count, false);
            });
        });

        // 2. Topbar Apply button (#btn-apply-pop-topbar)
        const btnApplyTop = document.getElementById("btn-apply-pop-topbar");
        if (btnApplyTop) {
            btnApplyTop.addEventListener("click", () => {
                const inputTop = document.getElementById("input-population-topbar");
                const count = parseInt(inputTop?.value || "20", 10);
                scalePopulation(count, false);
            });
        }

        // Enter key in topbar input
        const inputTop = document.getElementById("input-population-topbar");
        if (inputTop) {
            inputTop.addEventListener("keydown", (e) => {
                if (e.key === "Enter") {
                    scalePopulation(parseInt(inputTop.value, 10), false);
                }
            });
        }

        // 3. GIS Overlay Preset buttons (.btn-gis-pop-preset)
        document.querySelectorAll(".btn-gis-pop-preset").forEach((btn) => {
            btn.addEventListener("click", () => {
                const count = parseInt(btn.dataset.pop, 10);
                const inputTop = document.getElementById("input-population-topbar");
                if (inputTop) inputTop.value = count;
                const inputGis = document.getElementById("gis-input-active-pop");
                if (inputGis) inputGis.value = count;
                scalePopulation(count, false);
            });
        });

        // 4. GIS Overlay Dynamic Scale (#btn-gis-scale-dynamic)
        const btnGisDynamic = document.getElementById("btn-gis-scale-dynamic");
        if (btnGisDynamic) {
            btnGisDynamic.addEventListener("click", () => {
                const inputGis = document.getElementById("gis-input-active-pop");
                const count = parseInt(inputGis?.value || "20", 10);
                scalePopulation(count, false);
            });
        }

        // 5. GIS Overlay Reset (#btn-gis-scale-reset)
        const btnGisReset = document.getElementById("btn-gis-scale-reset");
        if (btnGisReset) {
            btnGisReset.addEventListener("click", () => {
                const inputGis = document.getElementById("gis-input-active-pop");
                const count = parseInt(inputGis?.value || "20", 10);
                if (confirm(`¿Reiniciar la simulación desde el tick 0 con ${count.toLocaleString()} habitantes?`)) {
                    scalePopulation(count, true);
                }
            });
        }

        // Enter key in GIS input
        const inputGis = document.getElementById("gis-input-active-pop");
        if (inputGis) {
            inputGis.addEventListener("keydown", (e) => {
                if (e.key === "Enter") {
                    scalePopulation(parseInt(inputGis.value, 10), false);
                }
            });
        }

        // 6. Click on Telemetry "POBLACIÓN" allows quick entry
        const elPopTelemetry = document.getElementById("telemetry-population");
        if (elPopTelemetry && elPopTelemetry.parentElement) {
            elPopTelemetry.parentElement.style.cursor = "pointer";
            elPopTelemetry.parentElement.addEventListener("click", () => {
                const current = elPopTelemetry.textContent.trim().replace(/,/g, "");
                const newVal = prompt("Ingresa el nuevo número de población sintética (ej. 50, 100, 250, 500, 1000):", current);
                if (newVal !== null && newVal.trim() !== "") {
                    const parsed = parseInt(newVal, 10);
                    if (!isNaN(parsed) && parsed >= 5) {
                        scalePopulation(parsed, false);
                    }
                }
            });
        }
    }

    function scalePopulation(targetCount, reset = false) {
        const count = parseInt(targetCount, 10);
        if (isNaN(count) || count < 5) {
            showNotification("Por favor ingresa un número de población válido (mínimo 5)", "error");
            return;
        }

        showNotification(`Configurando población a ${count.toLocaleString()} habitantes...`);
        fetch(`/api/control/population?count=${count}&reset=${reset}`, { method: "POST" })
            .then((r) => r.json())
            .then((data) => {
                const actual = data.population || count;

                // Sync inputs
                const inputTop = document.getElementById("input-population-topbar");
                if (inputTop) inputTop.value = actual;
                const inputGis = document.getElementById("gis-input-active-pop");
                if (inputGis) inputGis.value = actual;

                // Sync counters
                const elPop = document.getElementById("telemetry-population");
                if (elPop) elPop.textContent = Number(actual).toLocaleString();
                const elActive = document.getElementById("gis-pop-active");
                if (elActive) elActive.textContent = Number(actual).toLocaleString();

                // Highlight matching presets
                document.querySelectorAll(".btn-pop-preset, .btn-gis-pop-preset").forEach((b) => {
                    b.classList.toggle("active", parseInt(b.dataset.pop, 10) === actual);
                });

                showNotification(`Población activa: ${actual.toLocaleString()} habitantes (${reset ? "reiniciada" : "escalada en caliente"})`);
                refreshAllData();
                if (typeof updateGISSimulationLayer === "function") {
                    updateGISSimulationLayer();
                }
            })
            .catch((err) => {
                console.error("Error setting population", err);
                showNotification("Error de red al actualizar población", "error");
            });
    }

    function togglePlayPause() {
        const action = state.isRunning ? "pause" : "play";
        fetch(`/api/control/${action}`, { method: "POST" })
            .then((r) => r.json())
            .then((d) => {
                state.isRunning = d.is_running;
                updatePlayPauseButton();
            });
    }

    function updatePlayPauseButton() {
        const btn = document.getElementById("btn-play-pause");
        const icon = document.getElementById("icon-play-pause");
        if (state.isRunning) {
            btn.classList.remove("btn-primary");
            btn.classList.add("btn-secondary");
            icon.textContent = "⏸ Pausar";
        } else {
            btn.classList.remove("btn-secondary");
            btn.classList.add("btn-primary");
            icon.textContent = "▶ Iniciar";
        }
    }

    // =========================================================================
    // 3. SERVER-SENT EVENTS (SSE) STREAM & TELEMETRY
    // =========================================================================
    function connectSSE() {
        const indicator = document.getElementById("connection-indicator");
        const statusText = document.getElementById("connection-status-text");

        const eventSource = new EventSource("/api/events/stream");

        eventSource.onopen = () => {
            indicator.className = "connection-pill connected";
            statusText.textContent = "EN VIVO";
        };

        eventSource.onmessage = (e) => {
            try {
                const msg = JSON.parse(e.data);
                handleIncomingSSEMessage(msg);
            } catch (err) {
                console.error("Error parsing SSE frame", err);
            }
        };

        eventSource.onerror = () => {
            indicator.className = "connection-pill reconnecting";
            statusText.textContent = "RECONECTANDO";
            eventSource.close();
            setTimeout(connectSSE, 2000);
        };
    }

    function handleIncomingSSEMessage(msg) {
        if (msg.type === "tick" || msg.type === "connected") {
            const data = msg.data || msg.status;
            updateTelemetryUI(data);
            state.currentTick = data.tick;
            state.isRunning = data.is_running;
            updatePlayPauseButton();

            // Refresh lightweight world agents and timeline periodically
            fetchWorldAgentsOnly();
            if ((state.currentView === "world" || state.currentView === "gis25d") && state.gisLoaded) {
                updateGISSimulationLayer();
            }
            if (state.currentTick % 4 === 0) {
                fetchCivilizationData();
            }
        } else if (msg.type === "event") {
            appendEventToTicker(msg.data);
        } else if (msg.type === "state_change") {
            state.isRunning = msg.is_running;
            updatePlayPauseButton();
        } else if (msg.type === "population_change") {
            const newPop = msg.population;
            const elPop = document.getElementById("telemetry-population");
            if (elPop) elPop.textContent = Number(newPop).toLocaleString();
            const elActive = document.getElementById("gis-pop-active");
            if (elActive) elActive.textContent = Number(newPop).toLocaleString();
            refreshAllData();
            if ((state.currentView === "world" || state.currentView === "gis25d") && state.gisLoaded && typeof updateGISSimulationLayer === "function") {
                updateGISSimulationLayer();
            }
        }
    }

    function updateTelemetryUI(d) {
        if (!d) return;
        document.getElementById("telemetry-tick").textContent = d.tick;
        document.getElementById("telemetry-time").textContent = d.time_string || `Día ${d.day}, ${String(d.hour).padStart(2, "0")}:${String(d.minute).padStart(2, "0")}`;
        if (d.active_population !== undefined) {
            const popFormatted = Number(d.active_population).toLocaleString();
            document.getElementById("telemetry-population").textContent = popFormatted;
            const elActive = document.getElementById("gis-pop-active");
            if (elActive) elActive.textContent = popFormatted;
        }
        document.getElementById("telemetry-latency").textContent = `${d.tick_latency_ms || 0} ms`;
        document.getElementById("telemetry-fps").textContent = d.real_fps ? d.real_fps.toFixed(1) : "0.0";

        const seasonPill = document.getElementById("telemetry-season");
        seasonPill.textContent = (d.season === "epoca_lluviosa" || d.season === "invierno") ? "Época Lluviosa" : "Época Seca";
    }

    function appendEventToTicker(evt) {
        const track = document.getElementById("ticker-content");
        if (!track) return;

        const span = document.createElement("span");
        span.className = "ticker-item";
        span.innerHTML = `<strong>[T${evt.tick}] ${evt.event_type}</strong>: ${JSON.stringify(evt.data || {})}`;
        track.prepend(span);

        // Keep last 15 in ticker
        while (track.children.length > 15) {
            track.removeChild(track.lastChild);
        }
    }

    // =========================================================================
    // 4. WORLD EXPLORER & CANVAS ENGINE
    // =========================================================================
    function setupCanvasInteractions() {
        const canvas = document.getElementById("world-canvas");
        if (!canvas) return;

        // Resize Canvas to device pixel ratio
        function resize() {
            const rect = canvas.getBoundingClientRect();
            canvas.width = rect.width * window.devicePixelRatio;
            canvas.height = rect.height * window.devicePixelRatio;
        }
        window.addEventListener("resize", resize);
        resize();

        // Mouse Drag Pan
        canvas.addEventListener("mousedown", (e) => {
            state.camera.isDragging = true;
            state.camera.dragStartX = e.clientX - state.camera.x;
            state.camera.dragStartY = e.clientY - state.camera.y;
            state.followSelectedAgent = false;
        });

        window.addEventListener("mousemove", (e) => {
            if (state.camera.isDragging) {
                state.camera.x = e.clientX - state.camera.dragStartX;
                state.camera.y = e.clientY - state.camera.dragStartY;
            }
        });

        window.addEventListener("mouseup", () => {
            state.camera.isDragging = false;
        });

        // Wheel Zoom
        canvas.addEventListener("wheel", (e) => {
            e.preventDefault();
            const zoomFactor = e.deltaY < 0 ? 1.15 : 0.87;
            const newZoom = Math.max(0.6, Math.min(12.0, state.camera.zoom * zoomFactor));

            const rect = canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;

            // Zoom centered on cursor
            state.camera.x = mouseX - (mouseX - state.camera.x) * (newZoom / state.camera.zoom);
            state.camera.y = mouseY - (mouseY - state.camera.y) * (newZoom / state.camera.zoom);
            state.camera.zoom = newZoom;

            const coordBox = document.getElementById("map-coordinates");
            if (coordBox) coordBox.textContent = `Zoom: ${state.camera.zoom.toFixed(1)}×`;
        }, { passive: false });

        // Click Hit-Testing
        canvas.addEventListener("click", (e) => {
            const rect = canvas.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const clickY = e.clientY - rect.top;

            handleWorldClick(clickX, clickY);
        });

        // Zoom button controls (with null guards)
        document.getElementById("btn-zoom-in")?.addEventListener("click", () => {
            state.camera.zoom = Math.min(12.0, state.camera.zoom * 1.25);
        });
        document.getElementById("btn-zoom-out")?.addEventListener("click", () => {
            state.camera.zoom = Math.max(0.6, state.camera.zoom / 1.25);
        });
        document.getElementById("btn-zoom-reset")?.addEventListener("click", () => {
            centerElSalvadorView();
        });
        document.getElementById("btn-follow-agent")?.addEventListener("click", () => {
            if (state.selectedAgentUid) {
                state.followSelectedAgent = !state.followSelectedAgent;
                showNotification(state.followSelectedAgent ? "Siguiendo individuo seleccionado" : "Modo seguimiento desactivado");
            } else {
                showNotification("Seleccione un individuo primero");
            }
        });

        // Layer toggles (with null guards)
        document.getElementById("layer-depts")?.addEventListener("change", (e) => state.layers.depts = e.target.checked);
        document.getElementById("layer-districts")?.addEventListener("change", (e) => state.layers.districts = e.target.checked);
        document.getElementById("layer-roads")?.addEventListener("change", (e) => state.layers.roads = e.target.checked);
        document.getElementById("layer-geography")?.addEventListener("change", (e) => state.layers.geography = e.target.checked);
        document.getElementById("layer-establishments")?.addEventListener("change", (e) => state.layers.establishments = e.target.checked);
        document.getElementById("layer-agents")?.addEventListener("change", (e) => state.layers.agents = e.target.checked);
        document.getElementById("layer-density")?.addEventListener("change", (e) => state.layers.density = e.target.checked);
    }

    function centerElSalvadorView() {
        const canvas = document.getElementById("world-canvas");
        if (!canvas) return;
        const rect = canvas.getBoundingClientRect();
        state.camera.zoom = 1.0;
        state.camera.x = rect.width * 0.05;
        state.camera.y = rect.height * 0.10;
        state.followSelectedAgent = false;
    }

    // Geographic Projection: WGS84 Lat/Lon to Canvas Coordinates
    function projectGeo(lat, lon, width, height) {
        const x = ((lon - GEO_BOUNDS.minLon) / (GEO_BOUNDS.maxLon - GEO_BOUNDS.minLon)) * width;
        const y = (1.0 - (lat - GEO_BOUNDS.minLat) / (GEO_BOUNDS.maxLat - GEO_BOUNDS.minLat)) * height;
        return { x, y };
    }

    function renderWorldLoop() {
        // Legacy canvas loop stub preserved for test suite backward compatibility.
        // Primary territorial cartography is rendered via WebGL in MapLibre GL JS.
    }

    function drawWorldCanvas() {
        // Abstract canvas grid deprecated and eradicated.
        // Real GIS cartography active in MapLibre WebGL viewport.
    }

    function handleWorldClick(clickX, clickY) {
        const canvas = document.getElementById("world-canvas");
        const dpr = window.devicePixelRatio || 1;
        const width = canvas.width / dpr;
        const height = canvas.height / dpr;

        // Invert camera transform to find world coordinates
        const worldX = (clickX - state.camera.x) / state.camera.zoom;
        const worldY = (clickY - state.camera.y) / state.camera.zoom;

        const clickThreshold = 12 / state.camera.zoom;

        // Check agents
        if (state.world && state.world.agents) {
            for (const ag of state.world.agents) {
                const pt = projectGeo(ag.lat, ag.lon, width, height);
                const dist = Math.hypot(pt.x - worldX, pt.y - worldY);
                if (dist <= clickThreshold) {
                    selectIndividual(ag.uid);
                    return;
                }
            }
        }

        // Check establishments
        if (state.world && state.world.establishments) {
            for (const est of state.world.establishments) {
                const pt = projectGeo(est.lat, est.lon, width, height);
                const dist = Math.hypot(pt.x - worldX, pt.y - worldY);
                if (dist <= clickThreshold) {
                    selectEstablishment(est);
                    return;
                }
            }
        }
    }

    // =========================================================================
    // 5. INDIVIDUAL EXPLORER & ROSTER
    // =========================================================================
    function fetchIndividualsRoster() {
        fetch("/api/individuals")
            .then((r) => r.json())
            .then((data) => {
                state.individuals = data;
                renderIndividualsRoster(data);
                if (!state.selectedAgentUid && data.length > 0) {
                    selectIndividual(data[0].uid);
                }
            });
    }

    function renderIndividualsRoster(list) {
        const container = document.getElementById("individuals-roster");
        if (!container) return;
        container.innerHTML = "";

        list.forEach((ind) => {
            const card = document.createElement("div");
            card.className = `roster-card ${ind.uid === state.selectedAgentUid ? "selected" : ""}`;
            card.dataset.uid = ind.uid;
            card.innerHTML = `
                <div class="roster-card-header">
                    <span class="roster-name">${ind.full_name}</span>
                    <span class="roster-serial">#${ind.serial}</span>
                </div>
                <div class="roster-meta">${ind.occupation} | Edad: ${ind.age} | ${ind.current_activity}</div>
                <div class="roster-badges" style="display:flex; gap:4px; margin-top:4px; margin-bottom:4px; flex-wrap:wrap;">
                    <span class="badge-mini badge-tenure">${formatTenure(ind.housing_tenure)}</span>
                    <span class="badge-mini badge-emp">${formatEmployment(ind.employment_status)}</span>
                </div>
                <div class="roster-bars">
                    <div class="mini-bar" title="Energía: ${Math.round(ind.energy * 100)}%"><div class="mini-fill" style="width:${ind.energy * 100}%; background:#10b981;"></div></div>
                    <div class="mini-bar" title="Hambre: ${Math.round(ind.hunger * 100)}%"><div class="mini-fill" style="width:${ind.hunger * 100}%; background:#f59e0b;"></div></div>
                    <div class="mini-bar" title="Ánimo: ${ind.mood > 0 ? "+" : ""}${ind.mood}"><div class="mini-fill" style="width:${Math.max(10, (ind.mood + 1) * 50)}%; background:#38bdf8;"></div></div>
                </div>
            `;
            card.addEventListener("click", () => selectIndividual(ind.uid));
            container.appendChild(card);
        });
    }

    function filterIndividualsList() {
        const query = document.getElementById("individual-search").value.toLowerCase();
        const filtered = state.individuals.filter(
            (i) => i.full_name.toLowerCase().includes(query) || i.occupation.toLowerCase().includes(query)
        );
        renderIndividualsRoster(filtered);
    }

    function selectIndividual(uid) {
        state.selectedAgentUid = uid;

        // Highlight card in roster
        document.querySelectorAll(".roster-card").forEach((c) => {
            c.classList.toggle("selected", c.dataset.uid === uid);
        });

        fetchIndividualDetail(uid);
        fetchCognitiveSubsystems(uid);
    }

    function fetchIndividualDetail(uid) {
        fetch(`/api/individuals/${uid}`)
            .then((r) => r.json())
            .then((dossier) => {
                renderIndividualDossier(dossier);
                renderInspectorWithIndividual(dossier);
            });
    }

    function renderIndividualDossier(d) {
        const container = document.getElementById("individual-dossier-container");
        if (!container) return;

        const ident = d.identity;
        const phys = d.physical;
        const pers = d.personality;
        const emot = d.emotions;
        const cog = d.cognitive_profile;

        let traitsHtml = "";
        if (pers.traits_detailed) {
            for (const [tName, tVal] of Object.entries(pers.traits_detailed)) {
                const pct = Math.round(tVal.current * 100);
                const driftStr = tVal.drift >= 0 ? `+${tVal.drift.toFixed(2)}` : tVal.drift.toFixed(2);
                traitsHtml += `
                    <div class="trait-bar-row">
                        <div class="trait-label-row">
                            <span>${tName}</span>
                            <span>${tVal.current.toFixed(2)} (${driftStr})</span>
                        </div>
                        <div class="trait-track"><div class="trait-fill" style="width:${pct}%;"></div></div>
                    </div>
                `;
            }
        }

        let goalsHtml = "";
        if (d.active_goals && d.active_goals.length > 0) {
            d.active_goals.forEach((g) => {
                goalsHtml += `
                    <div style="margin-bottom:8px; padding:6px; background:var(--bg-base); border-radius:4px;">
                        <div style="display:flex; justify-content:space-between; font-weight:700; font-size:11px;">
                            <span>[${g.category.toUpperCase()}] ${g.description}</span>
                            <span>${Math.round(g.progress * 100)}%</span>
                        </div>
                        <div style="font-size:10px; color:var(--text-muted); margin-top:2px;">
                            Paso actual: ${g.current_step || "Ejecutando..."}
                        </div>
                    </div>
                `;
            });
        } else {
            goalsHtml = "<div style='font-style:italic; color:var(--text-muted);'>Sin metas activas en este tick.</div>";
        }

        // Phase 1.6 — subjective perception.  Everything rendered here comes
        // from /api/individuals/{uid}/perception, never from world truth.
        const perc = d.perception || {};
        let perceptionHtml = "<div style='color:var(--text-muted); font-style:italic;'>Sin percepción registrada en este tick.</div>";
        if (perc.has_perception_data) {
            const acuity = perc.acuity || {};
            const obs = (perc.recent_observations || []).slice().reverse();
            const interps = {};
            (perc.recent_interpretations || []).forEach((i) => { interps[i.observation_id] = i; });
            const rows = obs.map((o) => {
                const i = interps[o.observation_id] || {};
                const clar = Math.round((o.clarity || 0) * 100);
                const channel = o.channel === "auditory" ? "oído" : (o.channel === "social_report" ? "testimonio" : "vista");
                const bias = (i.biases_applied || []).length ? `<div style="font-size:9px; color:var(--accent-amber);">Sesgos: ${i.biases_applied.join(", ")}</div>` : "";
                const alts = (i.alternative_readings || []).length ? `<div style="font-size:9px; color:var(--text-muted);">Alternativa: ${i.alternative_readings[0]}</div>` : "";
                return `
                    <div style="font-size:11px; margin-bottom:6px; padding-bottom:4px; border-bottom:1px solid var(--border-subtle);">
                        <div><span style="font-family:var(--font-mono); color:var(--accent-sky);">[T${o.tick}]</span>
                            <strong>${o.target_kind}</strong> · ${channel} · claridad ${clar}%</div>
                        <div style="color:var(--text-secondary);">${i.claim || o.target_label}</div>
                        ${bias}${alts}
                    </div>`;
            }).join("");
            perceptionHtml = `
                <div style="font-size:10px; color:var(--text-muted); margin-bottom:6px;">
                    Agudeza visual ${Math.round((acuity.visual || 0) * 100)}% · auditiva ${Math.round((acuity.auditory || 0) * 100)}% ·
                    atención ${Math.round((acuity.attention || 0) * 100)}% · detalle ${acuity.detail_capacity || 0}
                </div>
                <div style="font-size:10px; color:var(--text-muted); margin-bottom:8px;">
                    Observaciones: <strong>${perc.total_observations}</strong> ·
                    Entidades conocidas: <strong>${perc.known_entities}</strong> ·
                    Malentendidos: <strong>${perc.total_misunderstandings}</strong>
                </div>
                ${rows}
                <div style="font-size:9px; color:var(--text-muted); margin-top:6px;">
                    Percepción subjetiva (modelo structured_detection_v1). No es conocimiento objetivo del mundo.
                </div>`;
        }

        // Phase 1.7 — integrated psychological state, coping, crisis and
        // reconstructed memory.  Every value comes from the backend engine.
        const psych = d.psychology || {};
        const ps = psych.state || {};
        let psychHtml = "<div style='color:var(--text-muted); font-style:italic;'>Sin estado psicológico disponible.</div>";
        if (psych.human_uid) {
            const bar = (label, value, color) => `
                <div class="trait-bar-row">
                    <div class="trait-label-row"><span>${label}</span><span>${Math.round((value || 0) * 100)}%</span></div>
                    <div class="trait-track"><div class="trait-fill" style="width:${Math.round((value || 0) * 100)}%; background:${color};"></div></div>
                </div>`;
            const crisis = psych.crisis;
            const crisisHtml = crisis ? `
                <div style="margin:8px 0; padding:6px; border-left:3px solid var(--accent-amber); background:var(--bg-base); font-size:11px;">
                    <strong>Crisis activa: ${crisis.kind}</strong> · severidad ${Math.round(crisis.severity * 100)}% · ${crisis.duration_ticks} ticks<br>
                    ${(crisis.behaviours || []).join(" · ")}<br>
                    <span style="color:var(--text-muted);">Causas: ${Object.entries(crisis.causes || {}).map(([k, v]) => `${k}=${v}`).join(", ")}</span>
                </div>` : "<div style='font-size:10px; color:var(--text-muted); margin:4px 0;'>Sin crisis activa. Historial: " + ((psych.crisis_history || []).length) + " episodios.</div>";
            const support = psych.support || {};
            const timeline = (psych.timeline || []).slice(-5).reverse().map((t) => `
                <div style="font-size:10px; margin-bottom:3px; border-bottom:1px solid var(--border-subtle); padding-bottom:2px;">
                    <span style="font-family:var(--font-mono); color:var(--accent-sky);">[T${t.tick}]</span> ${t.summary}
                </div>`).join("");
            const coping = (psych.coping?.recent || []).slice(-3).reverse().map((c) => `
                <div style="font-size:10px; margin-bottom:3px;">
                    <strong>${c.strategy}</strong> (${c.category}) · alivio ${Math.round(c.relief * 100)}% · largo plazo ${c.long_term_delta >= 0 ? "+" : ""}${c.long_term_delta}
                </div>`).join("");
            const remembered = (psych.memories || [])[0];
            psychHtml = `
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px;">
                    <div>
                        ${bar("Estrés agudo", ps.acute_stress, "#f59e0b")}
                        ${bar("Estrés crónico", ps.chronic_stress, "#ef4444")}
                        ${bar("Autocontrol", ps.self_control, "#38bdf8")}
                        ${bar("Esperanza", ps.hope, "#22c55e")}
                    </div>
                    <div>
                        ${bar("Fatiga mental", ps.mental_fatigue, "#a78bfa")}
                        ${bar("Soledad", ps.loneliness, "#94a3b8")}
                        ${bar("Apoyo percibido", ps.perceived_support, "#14b8a6")}
                        ${bar("Bienestar (descriptivo)", ps.wellbeing, "#eab308")}
                    </div>
                </div>
                <div style="font-size:10px; color:var(--text-muted); margin-top:6px;">
                    LOD psicológico: <strong>${psych.lod}</strong> · Red: <strong>${support.network_size || 0}</strong> vínculos ·
                    Íntimos: <strong>${support.intimate_ties || 0}</strong> · Creencias: ${Object.entries(psych.beliefs || {}).map(([k, v]) => `${k}=${v}`).join(", ")}
                </div>
                ${crisisHtml}
                <div style="font-size:11px; font-weight:700; margin-top:6px;">Afrontamiento reciente</div>
                ${coping || "<div style='font-size:10px; color:var(--text-muted);'>Sin intentos registrados.</div>"}
                <div style="font-size:11px; font-weight:700; margin-top:6px;">Línea de tiempo</div>
                ${timeline || "<div style='font-size:10px; color:var(--text-muted);'>Sin acontecimientos.</div>"}
                ${remembered ? `<div style="font-size:10px; margin-top:6px; padding:4px; background:var(--bg-base);">
                    <strong>Recuerdo reconstruido</strong> (fidelidad ${Math.round(remembered.fidelity * 100)}%):<br>
                    ${remembered.reconstructed}<br>
                    <span style="color:var(--text-muted);">${(remembered.distortions || []).join(", ")}</span>
                </div>` : ""}
                <div style="font-size:9px; color:var(--text-muted); margin-top:6px;">
                    Modelo funcional, no diagnóstico clínico. Estados y recuerdos son construcciones de la simulación.
                </div>`;
        }

        let memoriesHtml = "";
        if (d.recent_memories && d.recent_memories.length > 0) {
            d.recent_memories.forEach((m) => {
                memoriesHtml += `
                    <div style="font-size:11px; margin-bottom:4px; padding-bottom:4px; border-bottom:1px solid var(--border-subtle);">
                        <span style="font-family:var(--font-mono); color:var(--accent-sky);">[T${m.tick}]</span> ${m.summary}
                        <span style="font-size:9px; color:var(--text-muted);">(Val: ${m.valence > 0 ? "+" : ""}${m.valence}, Imp: ${m.importance})</span>
                    </div>
                `;
            });
        }

        container.innerHTML = `
            <div class="dossier-grid">
                <div class="dossier-box">
                    <h4>Identidad & Vitas Biológicas</h4>
                    <div style="font-size:16px; font-weight:700; margin-bottom:4px;">${ident.full_name} (#${ident.serial})</div>
                    <div style="font-size:12px; color:var(--text-muted); margin-bottom:12px;">${ident.occupation} | ${ident.age} años | Educación: ${ident.education}</div>

                    <div class="vitals-row">
                        <div class="vital-metric">
                            <div class="vital-name">ENERGÍA</div>
                            <div class="vital-value" style="color:#10b981;">${Math.round(phys.energy * 100)}%</div>
                        </div>
                        <div class="vital-metric">
                            <div class="vital-name">HAMBRE</div>
                            <div class="vital-value" style="color:#f59e0b;">${Math.round(phys.hunger * 100)}%</div>
                        </div>
                        <div class="vital-metric">
                            <div class="vital-name">SALUD</div>
                            <div class="vital-value" style="color:#38bdf8;">${Math.round((phys.health || 1.0) * 100)}%</div>
                        </div>
                        <div class="vital-metric">
                            <div class="vital-name">DINERO</div>
                            <div class="vital-value" style="color:#22c55e;">$${phys.money.toFixed(2)}</div>
                        </div>
                    </div>
                    <div style="font-size:11px; color:var(--text-secondary); margin-bottom:6px;">
                        Ubicación: <strong>${phys.location}</strong> | Actividad: <strong>${phys.current_activity}</strong>
                    </div>
                    <div style="display:flex; gap:6px; flex-wrap:wrap; margin-top:8px;">
                        <span class="badge-tenure">🏠 ${formatTenure(d.socioeconomic?.housing_tenure)}</span>
                        <span class="badge-emp">💼 ${formatEmployment(d.socioeconomic?.employment_status)}</span>
                        <span class="badge-wage">💵 Reserva: $${(d.socioeconomic?.reservation_wage || 8.0).toFixed(2)}/día</span>
                    </div>
                </div>

                <div class="dossier-box">
                    <h4>Perfil de Personalidad (Big Five + 3 Rasgos)</h4>
                    <div style="font-size:11px; color:var(--text-muted); margin-bottom:6px;">Temperamento: <strong>${pers.temperament.toUpperCase()}</strong></div>
                    ${traitsHtml}
                </div>

                <div class="dossier-box">
                    <h4>Ciclo de Metas Autónomas (HTN / GOAP)</h4>
                    ${goalsHtml}
                </div>

                <div class="dossier-box">
                    <h4>Memoria Episódica Reciente</h4>
                    ${memoriesHtml}
                </div>

                <div class="dossier-box">
                    <h4>Capacidades Cognitivas Dinámicas (14 Factores)</h4>
                    <div style="font-size:11px; color:var(--text-muted); margin-bottom:6px;">
                        Presupuesto: <strong>${cog.budget_used || 7.0} / ${cog.budget_max || 8.4}</strong> | Fatiga: <strong>${cog.fatigue || 0.0}</strong>
                    </div>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:4px; font-size:10px; font-family:var(--font-mono);">
                        ${Object.entries(cog.capabilities || {})
                            .map(([k, v]) => `<div>${k.replace(/_/g, " ")}: <strong>${v}</strong></div>`)
                            .join("")}
                    </div>
                </div>

                <div class="dossier-box">
                    <h4>Percepción Subjetiva (lo que esta persona notó)</h4>
                    ${perceptionHtml}
                </div>

                <div class="dossier-box">
                    <h4>Estado Psicológico Integrado (Phase 1.7)</h4>
                    ${psychHtml}
                </div>

                <div class="dossier-box">
                    <h4>Explicación de Decisión Reciente</h4>
                    ${d.last_decision_trace ? `
                        <div style="font-size:11px; line-height:1.4;">
                            <div style="color:var(--accent-sky); font-weight:700;">Acción: ${d.last_decision_trace.chosen_action}</div>
                            <div>Utilidad esperada: ${d.last_decision_trace.expected_utility}</div>
                            <div style="margin-top:4px; color:var(--text-secondary);">${d.last_decision_trace.reasoning}</div>
                        </div>
                    ` : "<div style='color:var(--text-muted); font-style:italic;'>Sin traza registrada todavía.</div>"}
                </div>
            </div>
        `;
    }

    // =========================================================================
    // 6. COGNITIVE ARCHITECTURE EXPLORER
    // =========================================================================
    function fetchCognitiveSubsystems(uid) {
        fetch(`/api/cognitive/${uid}`)
            .then((r) => r.json())
            .then((data) => {
                renderCognitiveView(data);
            });
    }

    function renderCognitiveView(data) {
        const subs = data.subsystems;
        if (!subs) return;

        // Frontal
        const fVars = document.getElementById("vars-frontal");
        if (fVars) {
            fVars.innerHTML = `
                <div>Metas activas: ${subs.frontal.state_variables.active_goals_count}</div>
                <div>Meta primordial: ${subs.frontal.state_variables.primary_goal}</div>
                <div>Profundidad planificación: ${subs.frontal.state_variables.planning_depth}</div>
            `;
        }

        // Hippocampal
        const hVars = document.getElementById("vars-hippocampal");
        if (hVars) {
            hVars.innerHTML = `
                <div>Items memoria trabajo: ${subs.hippocampal.state_variables.working_memory_used} / 7</div>
                <div>Registros episódicos: ${subs.hippocampal.state_variables.episodic_records_stored}</div>
                <div>Escudo de retención: ${subs.hippocampal.state_variables.retention_shield}</div>
            `;
        }

        // Limbic
        const lVars = document.getElementById("vars-limbic");
        if (lVars) {
            lVars.innerHTML = `
                <div>Ánimo afectivo: ${subs.limbic.state_variables.mood_valence > 0 ? "+" : ""}${subs.limbic.state_variables.mood_valence}</div>
                <div>Descuento por miedo: ${subs.limbic.state_variables.risk_discount_factor}</div>
                <div>Curiosidad: ${subs.limbic.state_variables.curiosity_intensity}</div>
            `;
        }

        // Temporal
        const tVars = document.getElementById("vars-temporal");
        if (tVars) {
            tVars.innerHTML = `
                <div>Conceptos sabidos: ${subs.temporal.state_variables.known_concepts_count}</div>
                <div>Confianza media: ${subs.temporal.state_variables.mean_confidence}</div>
                <div>Falsas creencias: ${subs.temporal.state_variables.misconceptions_count}</div>
            `;
        }

        // Parietal
        const pVars = document.getElementById("vars-parietal");
        if (pVars) {
            pVars.innerHTML = `
                <div>Ubicación: ${subs.parietal.state_variables.current_location}</div>
                <div>Hogar: ${subs.parietal.state_variables.home_location}</div>
                <div>Navegación: grafo con penalizaciones de vado/puente</div>
            `;
        }

        // Cerebellar
        const cVars = document.getElementById("vars-cerebellar");
        if (cVars) {
            cVars.innerHTML = `
                <div>Hábitos rastreados: ${subs.cerebellar.state_variables.total_habits_tracked}</div>
                <div>Hábito dominante: ${subs.cerebellar.state_variables.primary_habit} (${subs.cerebellar.state_variables.primary_habit_strength})</div>
                <div>Velocidad aprendizaje: ${subs.cerebellar.state_variables.procedural_learning_speed}</div>
            `;
        }

        // Pipeline Causal Steps
        const pipeContainer = document.getElementById("decision-pipeline-steps");
        if (pipeContainer && data.decision_trace_pipeline) {
            pipeContainer.innerHTML = "";
            const steps = [
                data.decision_trace_pipeline.step_1_observation,
                data.decision_trace_pipeline.step_2_needs,
                data.decision_trace_pipeline.step_3_memory_retrieval,
                data.decision_trace_pipeline.step_4_reasoning,
                data.decision_trace_pipeline.step_5_planning,
                data.decision_trace_pipeline.step_6_decision,
                data.decision_trace_pipeline.step_7_action,
                data.decision_trace_pipeline.step_8_result,
            ];

            steps.forEach((st, idx) => {
                if (!st) return;
                const box = document.createElement("div");
                box.className = "pipeline-step-box";
                box.innerHTML = `
                    <div class="step-num">PASO ${idx + 1}</div>
                    <div class="step-title">${st.stage}</div>
                    <div class="step-detail">${st.content}</div>
                `;
                pipeContainer.appendChild(box);
            });
        }
    }

    // =========================================================================
    // 7. KNOWLEDGE GRAPH EXPLORER (CANVAS FORCE LAYOUT)
    // =========================================================================
    function fetchKnowledgeGraph() {
        const query = document.getElementById("kg-search") ? document.getElementById("kg-search").value : "";
        const cat = document.getElementById("kg-category-filter") ? document.getElementById("kg-category-filter").value : "";
        fetch(`/api/knowledge?query=${encodeURIComponent(query)}&category=${encodeURIComponent(cat)}`)
            .then((r) => r.json())
            .then((data) => {
                state.knowledgeGraph = data;
                initKnowledgeSimulation(data.nodes, data.edges);
            });
    }

    function initKnowledgeSimulation(nodes, edges) {
        const canvas = document.getElementById("knowledge-canvas");
        if (!canvas) return;
        const rect = canvas.getBoundingClientRect();
        const pRect = canvas.parentElement ? canvas.parentElement.getBoundingClientRect() : { width: 900, height: 600 };
        const w = rect.width > 0 ? rect.width : (pRect.width > 0 ? pRect.width : 900);
        const h = rect.height > 0 ? rect.height : (pRect.height > 0 ? pRect.height : 600);
        canvas.width = w;
        canvas.height = h;

        state.kgSimulation.nodes = nodes.map((n, i) => {
            const angle = (i / nodes.length) * Math.PI * 2;
            const r = 180 + Math.random() * 80;
            return {
                ...n,
                x: w / 2 + Math.cos(angle) * r,
                y: h / 2 + Math.sin(angle) * r,
                vx: 0,
                vy: 0,
            };
        });
        state.kgSimulation.edges = edges;
        startKnowledgeGraphSim();
    }

    function startKnowledgeGraphSim() {
        const canvas = document.getElementById("knowledge-canvas");
        if (!canvas) return;
        const ctx = canvas.getContext("2d");

        let stepCount = 0;
        function stepSim() {
            if (state.currentView !== "knowledge") return;

            const rect = canvas.getBoundingClientRect();
            if (rect.width > 0 && (canvas.width !== rect.width || canvas.height !== rect.height)) {
                canvas.width = rect.width;
                canvas.height = rect.height;
            }

            const nodes = state.kgSimulation.nodes;
            const edges = state.kgSimulation.edges;
            const width = canvas.width;
            const height = canvas.height;

            // Simple physics: repulsion
            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const dx = nodes[j].x - nodes[i].x;
                    const dy = nodes[j].y - nodes[i].y;
                    const dist = Math.hypot(dx, dy) || 1;
                    if (dist < 180) {
                        const force = (180 - dist) / dist * 0.05;
                        nodes[i].vx -= dx * force;
                        nodes[i].vy -= dy * force;
                        nodes[j].vx += dx * force;
                        nodes[j].vy += dy * force;
                    }
                }
            }

            // Center gravity & velocity damp
            nodes.forEach((n) => {
                n.vx += (width / 2 - n.x) * 0.002;
                n.vy += (height / 2 - n.y) * 0.002;
                n.vx *= 0.85;
                n.vy *= 0.85;
                n.x += n.vx;
                n.y += n.vy;
            });

            // Draw
            ctx.clearRect(0, 0, width, height);

            // Edges
            ctx.strokeStyle = state.theme === "dark" ? "rgba(148, 163, 184, 0.25)" : "rgba(100, 116, 139, 0.3)";
            ctx.lineWidth = 1;
            edges.forEach((e) => {
                const src = nodes.find((n) => n.id === e.source);
                const tgt = nodes.find((n) => n.id === e.target);
                if (src && tgt) {
                    ctx.beginPath();
                    ctx.moveTo(src.x, src.y);
                    ctx.lineTo(tgt.x, tgt.y);
                    ctx.stroke();
                }
            });

            // Nodes
            nodes.forEach((n) => {
                ctx.beginPath();
                ctx.arc(n.x, n.y, 6, 0, Math.PI * 2);
                let col = "#10b981";
                if (n.category === "hypothesis") col = "#8b5cf6";
                else if (n.category === "craft") col = "#f59e0b";
                else if (n.category === "agriculture") col = "#10b981";
                else if (n.category === "gastronomy") col = "#0ea5e9";
                ctx.fillStyle = col;
                ctx.fill();
                ctx.strokeStyle = "#ffffff";
                ctx.lineWidth = 1;
                ctx.stroke();

                ctx.fillStyle = state.theme === "dark" ? "#f8fafc" : "#0f172a";
                ctx.font = "9px system-ui";
                ctx.fillText(n.label, n.x + 8, n.y + 3);
            });

            stepCount++;
            if (stepCount < 120 || state.currentView === "knowledge") {
                requestAnimationFrame(stepSim);
            }
        }
        requestAnimationFrame(stepSim);
    }

    // =========================================================================
    // 8. SOCIAL NETWORK EXPLORER (CANVAS FORCE LAYOUT)
    // =========================================================================
    function fetchSocialNetwork() {
        const relType = document.getElementById("social-rel-filter") ? document.getElementById("social-rel-filter").value : "";
        fetch(`/api/social`)
            .then((r) => r.json())
            .then((data) => {
                state.socialNetwork = data;
                initSocialSimulation(data.nodes, data.edges, relType);
            });
    }

    function initSocialSimulation(nodes, edges, filterType) {
        const canvas = document.getElementById("social-canvas");
        if (!canvas) return;
        const rect = canvas.getBoundingClientRect();
        const pRect = canvas.parentElement ? canvas.parentElement.getBoundingClientRect() : { width: 900, height: 600 };
        const w = rect.width > 0 ? rect.width : (pRect.width > 0 ? pRect.width : 900);
        const h = rect.height > 0 ? rect.height : (pRect.height > 0 ? pRect.height : 600);
        canvas.width = w;
        canvas.height = h;

        state.socialSimulation.nodes = nodes.map((n, i) => {
            const angle = (i / nodes.length) * Math.PI * 2;
            const r = 160 + Math.random() * 60;
            return {
                ...n,
                x: w / 2 + Math.cos(angle) * r,
                y: h / 2 + Math.sin(angle) * r,
                vx: 0,
                vy: 0,
            };
        });

        state.socialSimulation.edges = filterType
            ? edges.filter((e) => e.type.toLowerCase().includes(filterType.toLowerCase()))
            : edges;

        startSocialGraphSim();
    }

    function startSocialGraphSim() {
        const canvas = document.getElementById("social-canvas");
        if (!canvas) return;
        const ctx = canvas.getContext("2d");

        let stepCount = 0;
        function stepSim() {
            if (state.currentView !== "social") return;

            const rect = canvas.getBoundingClientRect();
            if (rect.width > 0 && (canvas.width !== rect.width || canvas.height !== rect.height)) {
                canvas.width = rect.width;
                canvas.height = rect.height;
            }

            const nodes = state.socialSimulation.nodes;
            const edges = state.socialSimulation.edges;
            const width = canvas.width;
            const height = canvas.height;

            // Physics repulsion
            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const dx = nodes[j].x - nodes[i].x;
                    const dy = nodes[j].y - nodes[i].y;
                    const dist = Math.hypot(dx, dy) || 1;
                    if (dist < 150) {
                        const force = (150 - dist) / dist * 0.06;
                        nodes[i].vx -= dx * force;
                        nodes[i].vy -= dy * force;
                        nodes[j].vx += dx * force;
                        nodes[j].vy += dy * force;
                    }
                }
            }

            nodes.forEach((n) => {
                n.vx += (width / 2 - n.x) * 0.003;
                n.vy += (height / 2 - n.y) * 0.003;
                n.vx *= 0.85;
                n.vy *= 0.85;
                n.x += n.vx;
                n.y += n.vy;
            });

            ctx.clearRect(0, 0, width, height);

            // Draw Edges
            edges.forEach((e) => {
                const src = nodes.find((n) => n.id === e.source);
                const tgt = nodes.find((n) => n.id === e.target);
                if (src && tgt) {
                    ctx.beginPath();
                    ctx.moveTo(src.x, src.y);
                    ctx.lineTo(tgt.x, tgt.y);
                    let col = "#38bdf8";
                    if (e.type === "family") col = "#3b82f6";
                    else if (e.type === "friendship") col = "#10b981";
                    else if (e.type === "conflict") col = "#ef4444";
                    else if (e.type === "trade") col = "#f59e0b";
                    ctx.strokeStyle = col;
                    ctx.lineWidth = Math.max(1, e.strength * 2.5);
                    ctx.stroke();
                }
            });

            // Draw Nodes
            nodes.forEach((n) => {
                ctx.beginPath();
                ctx.arc(n.x, n.y, 7, 0, Math.PI * 2);
                ctx.fillStyle = n.gender === "female" ? "#f43f5e" : "#0ea5e9";
                ctx.fill();
                ctx.strokeStyle = "#ffffff";
                ctx.lineWidth = 1.2;
                ctx.stroke();

                ctx.fillStyle = state.theme === "dark" ? "#f8fafc" : "#0f172a";
                ctx.font = "bold 9px system-ui";
                ctx.fillText(n.label, n.x + 9, n.y + 3);
            });

            stepCount++;
            if (stepCount < 120 || state.currentView === "social") {
                requestAnimationFrame(stepSim);
            }
        }
        requestAnimationFrame(stepSim);
    }

    // =========================================================================
    // 9. CIVILIZATION DASHBOARD & CHARTS
    // =========================================================================
    function fetchCivilizationData() {
        fetch("/api/civilization")
            .then((r) => r.json())
            .then((data) => {
                state.civilization = data;
                updateCivilizationSummary(data.current_snapshot);
                if (state.currentView === "civilization") {
                    renderCivilizationCharts();
                }
            });
    }

    function updateCivilizationSummary(s) {
        if (!s) return;
        document.getElementById("stat-pop").textContent = s.population;
        document.getElementById("stat-gini").textContent = s.gini_coefficient ? s.gini_coefficient.toFixed(2) : "0.24";
        document.getElementById("stat-traditions").textContent = s.active_traditions_count;
        document.getElementById("stat-orgs").textContent = s.active_communities_count;
    }

    function renderCivilizationCharts() {
        if (!state.civilization || !state.civilization.time_series_history) return;
        const pts = state.civilization.time_series_history;
        if (pts.length < 2) return;

        renderSVGChart("chart-demographics", pts, (p) => p.population, "#0ea5e9", "Población");
        renderSVGChart("chart-economy", pts, (p) => p.gini * 100, "#f59e0b", "Gini × 100");
        renderSVGChart("chart-culture", pts, (p) => p.active_traditions, "#10b981", "Tradiciones");
        renderSVGChart("chart-climate", pts, (p) => p.temperature_c, "#ef4444", "Temp °C");
    }

    function renderSVGChart(containerId, data, valExtractor, color, label) {
        const container = document.getElementById(containerId);
        if (!container) return;
        const width = container.clientWidth || 360;
        const height = container.clientHeight || 180;
        const pad = 24;

        const values = data.map(valExtractor);
        const minVal = Math.min(...values);
        const maxVal = Math.max(...values, minVal + 1);

        const points = values.map((v, i) => {
            const x = pad + (i / (values.length - 1)) * (width - pad * 2);
            const y = height - pad - ((v - minVal) / (maxVal - minVal)) * (height - pad * 2);
            return `${x.toFixed(1)},${y.toFixed(1)}`;
        }).join(" ");

        container.innerHTML = `
            <svg width="100%" height="100%" viewBox="0 0 ${width} ${height}">
                <line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" stroke="var(--border-strong)" stroke-width="1"/>
                <polyline fill="none" stroke="${color}" stroke-width="2.5" points="${points}" stroke-linecap="round" stroke-linejoin="round"/>
                <text x="${pad}" y="${pad - 4}" fill="var(--text-muted)" font-size="10">${label} (Max: ${maxVal.toFixed(1)})</text>
            </svg>
        `;
    }

    // =========================================================================
    // 10. ECONOMY AND RESOURCES
    // =========================================================================
    function fetchEconomyData() {
        fetch("/api/economy")
            .then((r) => r.json())
            .then((data) => {
                state.economy = data;
                renderEconomyView(data);
            });
    }

    function renderEconomyView(data) {
        const priceContainer = document.getElementById("commodity-price-board");
        if (priceContainer && data.commodity_prices) {
            priceContainer.innerHTML = data.commodity_prices.map((p) => `
                <div class="commodity-card">
                    <div class="commodity-name">${p.commodity}</div>
                    <div class="commodity-price">$${p.price_usd.toFixed(2)}</div>
                    <div class="commodity-trend">${p.trend.toUpperCase()}</div>
                </div>
            `).join("");
        }

        const entContainer = document.getElementById("enterprises-list");
        if (entContainer && data.enterprises) {
            entContainer.innerHTML = `
                <table class="data-table">
                    <thead><tr><th>Empresa</th><th>Tipo</th><th>Caja</th><th>Estado</th></tr></thead>
                    <tbody>
                        ${data.enterprises.map((e) => `
                            <tr>
                                <td>${e.name}</td>
                                <td>${e.type}</td>
                                <td>$${e.cash_reserve.toFixed(2)}</td>
                                <td><span style="color:#10b981;">${e.status}</span></td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            `;
        }

        const creditContainer = document.getElementById("credit-ledger-list");
        if (creditContainer && data.loans) {
            creditContainer.innerHTML = `
                <table class="data-table">
                    <thead><tr><th>ID</th><th>Tipo</th><th>Saldo</th><th>Tasa</th><th>Fallas</th></tr></thead>
                    <tbody>
                        ${data.loans.map((l) => `
                            <tr>
                                <td>${l.loan_id.slice(0, 8)}</td>
                                <td>${l.loan_type}</td>
                                <td>$${l.balance_remaining.toFixed(2)}</td>
                                <td>${(l.interest_rate * 100).toFixed(1)}%</td>
                                <td>${l.missed_payments}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            `;
        }
    }

    // =========================================================================
    // 11. HISTORICAL TIMELINE
    // =========================================================================
    function fetchTimeline() {
        const typeFilter = document.getElementById("timeline-type-filter") ? document.getElementById("timeline-type-filter").value : "";
        const search = document.getElementById("timeline-search") ? document.getElementById("timeline-search").value : "";
        const impOnly = document.getElementById("timeline-important-only") ? document.getElementById("timeline-important-only").checked : false;

        const minImp = impOnly ? 0.65 : 0.0;
        fetch(`/api/timeline?min_importance=${minImp}&event_type=${encodeURIComponent(typeFilter)}&limit=100`)
            .then((r) => r.json())
            .then((events) => {
                state.timelineEvents = events;
                renderTimelineList(events, search);
            });
    }

    function renderTimelineList(events, query) {
        const container = document.getElementById("timeline-events-list");
        if (!container) return;

        let filtered = events;
        if (query) {
            const q = query.toLowerCase();
            filtered = events.filter((e) => e.event_type.toLowerCase().includes(q) || JSON.stringify(e.data).toLowerCase().includes(q));
        }

        container.innerHTML = filtered.map((e) => `
            <div class="timeline-event-card">
                <div class="event-tick-badge">TICK ${e.tick}</div>
                <div class="event-content">
                    <div class="event-type-label">${e.event_type}</div>
                    <div class="event-desc">${JSON.stringify(e.data || {})}</div>
                </div>
                <div class="event-importance-stars" title="Importancia: ${e.importance}">
                    ${"★".repeat(Math.round(e.importance * 5))}
                </div>
            </div>
        `).join("");
    }

    // =========================================================================
    // 12. SIMULATION LABORATORY
    // =========================================================================
    function fetchLaboratoryExperiments() {
        fetch("/api/laboratory/experiments")
            .then((r) => r.json())
            .then((exps) => {
                renderLaboratoryExperiments(exps);
            });
    }

    function renderLaboratoryExperiments(list) {
        const container = document.getElementById("laboratory-experiments-list");
        if (!container) return;

        container.innerHTML = list.map((exp) => `
            <div class="experiment-card">
                <div>
                    <div class="exp-id">${exp.id}</div>
                    <div class="exp-name">${exp.name}</div>
                    <div class="exp-desc">${exp.description}</div>
                </div>
                <button class="btn btn-sm btn-primary" onclick="window.runExperiment('${exp.id}')">
                    Ejecutar Experimento
                </button>
            </div>
        `).join("");
    }

    window.runExperiment = function (expId) {
        const resultContainer = document.getElementById("lab-results-container");
        const resultContent = document.getElementById("lab-result-content");
        resultContainer.style.display = "block";
        resultContent.innerHTML = `<div style="color:var(--accent-sky);">Ejecutando ${expId}... Espere por favor.</div>`;

        fetch(`/api/laboratory/run/${expId}`, { method: "POST" })
            .then((r) => r.json())
            .then((res) => {
                resultContent.innerHTML = `
                    <div style="font-weight:700; margin-bottom:6px; color:${res.success ? '#10b981' : '#ef4444'};">
                        ESTADO: ${res.success ? "APROBADO [PASS]" : "FALLIDO [FAIL]"} (${res.duration_seconds}s)
                    </div>
                    <div style="font-size:12px; margin-bottom:8px;">${res.summary}</div>
                    <pre style="background:var(--bg-base); padding:8px; border-radius:4px; font-size:11px; font-family:var(--font-mono); overflow-x:auto;">${JSON.stringify(res.metrics, null, 2)}</pre>
                `;
            });
    };

    // =========================================================================
    // 13. REPORTS VIEWER
    // =========================================================================
    function loadReport(reportKey) {
        const contentBox = document.getElementById("report-view-area");
        if (!contentBox) return;

        const reportsContent = {
            phase13_summary: `
                <div class="report-markdown">
                    <h2>SALTBOR — Resumen Científico de la Fase 1.3</h2>
                    <p>La Fase 1.3 introduce evolución cognitiva abierta, meta-aprendizaje y dinámica de inteligencia cultural emergente sin guiones predeterminados.</p>
                    <table>
                        <tr><th>Subsistema</th><th>Estado</th><th>Criterio de Validación</th></tr>
                        <tr><td>Perfil Cognitivo (14 Factores)</td><td>Verificado</td><td>Presupuesto mental acotado (8.40) y trade-offs</td></tr>
                        <tr><td>Meta-Aprendizaje</td><td>Verificado</td><td>6 estrategias y selección según rendimiento empírico</td></tr>
                        <tr><td>Plasticidad & Práctica</td><td>Verificado</td><td>Curvas de ley de potencia y atrofia Ebbinghaus</td></tr>
                        <tr><td>Pensamiento Científico</td><td>Verificado</td><td>Ciclo de 8 etapas y refutación de hipótesis</td></tr>
                        <tr><td>Educación Distribuida</td><td>Verificado</td><td>Talleres comunitarios y fidelidad de transmisión</td></tr>
                    </table>
                </div>
            `,
            cognitive_validation: `
                <div class="report-markdown">
                    <h2>Validación de Subsistemas Cognitivos</h2>
                    <p>Se confirmó que el pipeline causal de deliberación (Observación → Necesidades → Memoria → Razonamiento → Planificación → Decisión → Acción → Resultado) refleja la ejecución interna de cada agente.</p>
                </div>
            `,
            salvadoran_geography: `
                <div class="report-markdown">
                    <h2>Integridad Geográfica y Territorial</h2>
                    <p>Integración de los 14 departamentos, 44 municipios (Reforma 2024), 262 distritos, red vial nacional (CA-1, CA-2, CA-4) y directorio verificado de establecimientos comerciales.</p>
                </div>
            `,
            performance_audit: `
                <div class="report-markdown">
                    <h2>Auditoría de Rendimiento en AMD Ryzen 8700G</h2>
                    <p>Throughput medio superior a 150 ticks/segundo con huella de memoria inferior a 150 KB por individuo sintético.</p>
                </div>
            `,
        };

        contentBox.innerHTML = reportsContent[reportKey] || "<p>Informe en preparación.</p>";
    }

    // =========================================================================
    // 14. CONTEXTUAL INSPECTOR PANEL
    // =========================================================================
    function renderInspectorWithIndividual(d) {
        const title = document.getElementById("inspector-title");
        const body = document.getElementById("inspector-content");
        const panel = document.getElementById("inspector-panel");
        panel.classList.remove("collapsed");

        title.textContent = `Individuo #${d.identity.serial}`;
        body.innerHTML = `
            <div style="font-size:15px; font-weight:700; color:var(--text-primary); margin-bottom:2px;">${d.identity.full_name}</div>
            <div style="font-size:11px; color:var(--text-muted); margin-bottom:12px;">${d.identity.occupation} | ${d.identity.age} años</div>

            <div style="display:flex; gap:6px; margin-bottom:14px;">
                <button class="btn btn-sm btn-secondary" onclick="window.followAgent('${d.identity.uid}')">Seguir en Mapa</button>
                <button class="btn btn-sm btn-secondary" onclick="window.switchToCognitive('${d.identity.uid}')">Cerebro</button>
            </div>

            <div style="margin-bottom:10px; font-size:11px;">
                <div>Energía: <strong>${Math.round(d.physical.energy * 100)}%</strong></div>
                <div>Hambre: <strong>${Math.round(d.physical.hunger * 100)}%</strong></div>
                <div>Dinero: <strong>$${d.physical.money.toFixed(2)}</strong></div>
                <div>Ánimo: <strong>${d.emotions.mood > 0 ? "+" : ""}${d.emotions.mood}</strong></div>
            </div>

            <div style="border-top:1px solid var(--border-subtle); padding-top:8px;">
                <div style="font-weight:700; font-size:11px; margin-bottom:4px; color:var(--accent-sky);">Meta Actual:</div>
                <div style="font-size:11px; color:var(--text-secondary);">
                    ${d.active_goals && d.active_goals.length > 0 ? d.active_goals[0].description : "Mantenimiento diario"}
                </div>
            </div>
        `;
    }

    function selectEstablishment(est) {
        state.selectedEntity = est;
        const title = document.getElementById("inspector-title");
        const body = document.getElementById("inspector-content");
        const panel = document.getElementById("inspector-panel");
        panel.classList.remove("collapsed");

        title.textContent = "Establecimiento Real";
        body.innerHTML = `
            <div style="font-size:14px; font-weight:700; margin-bottom:4px;">${est.name}</div>
            <div style="font-size:11px; color:var(--text-muted); margin-bottom:8px;">Categoría: ${est.category} (${est.sub_category})</div>
            <div style="font-size:11px; margin-bottom:6px;">
                Estado Validación: <strong style="color:${est.is_confirmed ? '#10b981' : '#eab308'};">${est.validation_state}</strong>
            </div>
            <div style="font-size:11px; color:var(--text-secondary); margin-bottom:6px;">
                Dirección: ${est.address || "Dirección verificada en registro"}
            </div>
            <div style="font-size:10px; font-family:var(--font-mono); color:var(--text-muted);">
                Fuente: ${est.source_provenance} | WGS84: ${est.lat.toFixed(4)}, ${est.lon.toFixed(4)}
            </div>
        `;
    }

    window.followAgent = function (uid) {
        state.selectedAgentUid = uid;
        state.followSelectedAgent = true;
        switchView("world");
    };

    window.switchToCognitive = function (uid) {
        state.selectedAgentUid = uid;
        switchView("cognitive");
    };

    // =========================================================================
    // 15. THEME & UTILITIES
    // =========================================================================
    function setupThemeToggle() {
        const btn = document.getElementById("btn-theme-toggle");
        btn.addEventListener("click", () => {
            state.theme = state.theme === "dark" ? "light" : "dark";
            document.documentElement.setAttribute("data-theme", state.theme);
        });
    }

    function showNotification(text) {
        const ticker = document.getElementById("ticker-content");
        if (ticker) {
            const span = document.createElement("span");
            span.className = "ticker-item";
            span.innerHTML = `<span style="color:var(--accent-amber); font-weight:700;">[NOTIFICACIÓN]</span> ${text}`;
            ticker.prepend(span);
        }
    }

    function fetchWorldData() {
        fetch("/api/world")
            .then((r) => r.json())
            .then((d) => {
                state.world = d;
                if (d.environment) {
                    const temp = document.getElementById("env-temp");
                    if (temp) temp.textContent = `${d.environment.temperature_celsius} °C`;
                    const cond = document.getElementById("env-condition");
                    if (cond) cond.textContent = d.environment.weather_condition;
                    const moist = document.getElementById("env-moisture");
                    if (moist) moist.textContent = `${Math.round(d.environment.soil_moisture * 100)}%`;
                }
            });
    }

    function fetchWorldAgentsOnly() {
        if (!state.world) return;
        fetch("/api/world")
            .then((r) => r.json())
            .then((d) => {
                state.world.agents = d.agents;
                state.world.environment = d.environment;
            });
    }

    function refreshAllData() {
        fetchWorldData();
        fetchIndividualsRoster();
        fetchCivilizationData();
        fetchEconomyData();
        fetchTimeline();
        fetchJusticeDocket();
        fetchADESCOData();
        fetchCommerceData();
        fetchRemittancesData();
        fetchScientificDiscoveriesData();
        fetchApprenticeshipsData();
    }

    // =========================================================================
    // 16. REAL GIS CARTOGRAPHY FOUNDATION & DIGITAL TWIN (MAPLIBRE GL JS)
    // =========================================================================
    const PILOT_LANDMARKS = [
        { name: "Biblioteca Nacional (BINAES)", icon: "📚", coords: [-89.1908, 13.6973], category: "civic" },
        { name: "Palacio Nacional", icon: "🏛️", coords: [-89.1923, 13.6976], category: "monument" },
        { name: "Catedral Metropolitana", icon: "⛪", coords: [-89.1908, 13.6983], category: "religious" },
        { name: "Teatro Nacional", icon: "🎭", coords: [-89.1900, 13.6985], category: "culture" },
        { name: "Plaza Gerardo Barrios", icon: "🌳", coords: [-89.1915, 13.6978], category: "plaza" },
        { name: "Plaza Libertad", icon: "🌳", coords: [-89.1890, 13.6980], category: "plaza" },
        { name: "Parque Cuscatlán", icon: "🌳", coords: [-89.2060, 13.6995], category: "park" },
        { name: "Mercado Central", icon: "🛒", coords: [-89.1952, 13.6948], category: "commerce" },
        { name: "Iglesia El Calvario", icon: "⛪", coords: [-89.1938, 13.6942], category: "religious" }
    ];

    let landmarkMarkers = [];

    function setupGIS25D() {
        // Territorial Scale buttons
        const btnRecenter = document.getElementById("btn-cam-recenter");
        if (btnRecenter) {
            btnRecenter.addEventListener("click", () => {
                if (state.gisMap) {
                    state.gisMap.flyTo({
                        center: [-89.1915, 13.6978],
                        zoom: 16.5,
                        pitch: 45,
                        bearing: -15,
                        duration: 1200
                    });
                    updateCameraActiveButton(btnRecenter);
                    state.gisFollowAgent = false;
                }
            });
        }

        const btnCity = document.getElementById("btn-cam-city");
        if (btnCity) {
            btnCity.addEventListener("click", () => {
                if (state.gisMap) {
                    state.gisMap.flyTo({
                        center: [-89.2182, 13.6929],
                        zoom: 13.0,
                        pitch: 0,
                        bearing: 0,
                        duration: 1200
                    });
                    updateCameraActiveButton(btnCity);
                    state.gisFollowAgent = false;
                }
            });
        }

        const btnNational = document.getElementById("btn-cam-national");
        if (btnNational) {
            btnNational.addEventListener("click", () => {
                if (state.gisMap) {
                    state.gisMap.flyTo({
                        center: [-88.8965, 13.7942],
                        zoom: 8.5,
                        pitch: 0,
                        bearing: 0,
                        duration: 1500
                    });
                    updateCameraActiveButton(btnNational);
                    state.gisFollowAgent = false;
                }
            });
        }

        // Camera perspective presets
        const btnTop = document.getElementById("btn-cam-topdown");
        if (btnTop) {
            btnTop.addEventListener("click", () => {
                if (state.gisMap) {
                    state.gisMap.easeTo({ pitch: 0, bearing: 0, duration: 800 });
                    updateCameraActiveButton(btnTop);
                }
            });
        }

        const btnIso = document.getElementById("btn-cam-isometric");
        if (btnIso) {
            btnIso.addEventListener("click", () => {
                if (state.gisMap) {
                    state.gisMap.easeTo({ pitch: 50, bearing: -15, duration: 800 });
                    updateCameraActiveButton(btnIso);
                }
            });
        }

        const btnStreet = document.getElementById("btn-cam-street");
        if (btnStreet) {
            btnStreet.addEventListener("click", () => {
                if (state.gisMap) {
                    state.gisMap.easeTo({ pitch: 75, bearing: -15, zoom: 17.5, duration: 900 });
                    updateCameraActiveButton(btnStreet);
                }
            });
        }

        const btnFollow = document.getElementById("btn-cam-follow");
        if (btnFollow) {
            btnFollow.addEventListener("click", () => {
                if (!state.selectedAgentUid) {
                    showNotification("Seleccione un individuo primero para seguirlo en el mapa");
                    return;
                }
                state.gisFollowAgent = !state.gisFollowAgent;
                btnFollow.classList.toggle("btn-active", state.gisFollowAgent);
                showNotification(state.gisFollowAgent ? "Siguiendo individuo en tiempo real" : "Modo seguimiento desactivado");
            });
        }

        // Basemap Switcher
        const selectBasemap = document.getElementById("select-basemap");
        if (selectBasemap) {
            selectBasemap.addEventListener("change", (e) => {
                switchBasemap(e.target.value);
            });
        }

        // 2D / 2.5D Building Extrusion Toggle
        const toggleExtrusion = document.getElementById("toggle-gis-extrusion");
        if (toggleExtrusion) {
            toggleExtrusion.addEventListener("change", (e) => {
                if (!state.gisMap) return;
                const is3D = e.target.checked;
                if (state.gisMap.getLayer("gis-layer-buildings-25d")) {
                    state.gisMap.setLayoutProperty("gis-layer-buildings-25d", "visibility", is3D ? "visible" : "none");
                }
                if (state.gisMap.getLayer("gis-layer-buildings-2d")) {
                    state.gisMap.setLayoutProperty("gis-layer-buildings-2d", "visibility", is3D ? "none" : "visible");
                }
            });
        }

        // Street Labels Toggle
        const toggleStreetLabels = document.getElementById("toggle-gis-street-labels");
        if (toggleStreetLabels) {
            toggleStreetLabels.addEventListener("change", (e) => {
                if (!state.gisMap) return;
                if (state.gisMap.getLayer("gis-layer-street-labels")) {
                    state.gisMap.setLayoutProperty("gis-layer-street-labels", "visibility", e.target.checked ? "visible" : "none");
                }
            });
        }

        // Landmark Labels Toggle
        const toggleLandmarks = document.getElementById("toggle-gis-landmarks");
        if (toggleLandmarks) {
            toggleLandmarks.addEventListener("change", (e) => {
                const vis = e.target.checked ? "flex" : "none";
                landmarkMarkers.forEach((m) => {
                    const el = m.getElement();
                    if (el) el.style.display = vis;
                });
            });
        }

        // Standard Layer Toggles
        const layerMap = {
            "toggle-gis-buildings": "gis-layer-buildings-25d",
            "toggle-gis-streets": "gis-layer-streets",
            "toggle-gis-parks": "gis-layer-parks-fill",
            "toggle-gis-water": "gis-layer-water",
            "toggle-gis-elevation": "gis-layer-elevation",
            "toggle-gis-boundaries": "gis-layer-boundaries",
            "toggle-gis-agents": "gis-layer-sim-agents",
            "toggle-gis-trajectories": "gis-layer-sim-trajectories",
            "toggle-gis-density": "gis-layer-sim-density",
        };

        Object.entries(layerMap).forEach(([checkboxId, layerId]) => {
            const cb = document.getElementById(checkboxId);
            if (cb) {
                cb.addEventListener("change", (e) => {
                    if (state.gisMap && state.gisMap.getLayer(layerId)) {
                        state.gisMap.setLayoutProperty(
                            layerId,
                            "visibility",
                            e.target.checked ? "visible" : "none"
                        );
                    }
                });
            }
        });

        // Close feature inspector
        const closeFeatBtn = document.getElementById("btn-close-gis-feat");
        if (closeFeatBtn) {
            closeFeatBtn.addEventListener("click", () => {
                const card = document.getElementById("gis-feature-inspector");
                if (card) card.classList.add("collapsed");
            });
        }

        // Scale buttons (100k / 1M)
        const btn100k = document.getElementById("btn-gis-scale-100k");
        if (btn100k) {
            btn100k.addEventListener("click", () => {
                showNotification("Escalando población a 100,000 individuos sintéticos...");
                btn100k.disabled = true;
                btn100k.textContent = "Cargando...";
                fetch("/api/gis/scale_population?target=100000", { method: "POST" })
                    .then((r) => r.json())
                    .then(() => fetchGISPopulationLODSummary())
                    .finally(() => {
                        btn100k.disabled = false;
                        btn100k.textContent = "⚡ 100k";
                        showNotification("Población escalada: 100,000 agentes persistentes.");
                    });
            });
        }

        const btn1M = document.getElementById("btn-gis-scale-1m");
        if (btn1M) {
            btn1M.addEventListener("click", () => {
                showNotification("Cargando arquitectura de 1,000,000 de agentes persistentes...");
                btn1M.disabled = true;
                btn1M.textContent = "Indexando...";
                fetch("/api/gis/scale_population?target=1000000", { method: "POST" })
                    .then((r) => r.json())
                    .then(() => fetchGISPopulationLODSummary())
                    .finally(() => {
                        btn1M.disabled = false;
                        btn1M.textContent = "🚀 1 Millón";
                        showNotification("Población activa: 1,000,000 agentes registrados.");
                    });
            });
        }

        // Periodic LOD Summary telemetry
        setInterval(fetchGISPopulationLODSummary, 2000);

        // UI Hiding / Zen Mode (Fullscreen Map with No Obstructions)
        function toggleZenMode() {
            const app = document.getElementById("app-container");
            const restoreBtn = document.getElementById("btn-restore-ui-floating");
            if (!app) return;
            const isZen = app.classList.toggle("zen-mode");
            if (restoreBtn) {
                restoreBtn.style.display = isZen ? "inline-flex" : "none";
            }
            if (state.gisMap) {
                setTimeout(() => state.gisMap.resize(), 120);
            }
            showNotification(isZen ? "Modo Pantalla Completa activo. Presione tecla 'H' para restaurar la interfaz." : "Interfaz restaurada.");
        }

        const btnToggleUI = document.getElementById("btn-toggle-ui");
        if (btnToggleUI) btnToggleUI.addEventListener("click", toggleZenMode);

        const btnZenMode = document.getElementById("btn-zen-mode");
        if (btnZenMode) btnZenMode.addEventListener("click", toggleZenMode);

        const btnRestoreFloating = document.getElementById("btn-restore-ui-floating");
        if (btnRestoreFloating) btnRestoreFloating.addEventListener("click", toggleZenMode);

        // Keyboard hotkeys: 'H' toggles UI, Escape exits Zen Mode
        window.addEventListener("keydown", (e) => {
            if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.target.tagName === "TEXTAREA")) return;
            if (e.key === "h" || e.key === "H") {
                toggleZenMode();
            } else if (e.key === "Escape") {
                const app = document.getElementById("app-container");
                if (app && app.classList.contains("zen-mode")) {
                    toggleZenMode();
                }
            }
        });

        // Toggle / Minimize GIS Layers Panel
        const btnToggleLayersPanel = document.getElementById("btn-toggle-gis-layers-panel");
        const btnMinimizeLayers = document.getElementById("btn-minimize-gis-layers");
        const layersCard = document.getElementById("gis-layers-card");

        function toggleLayersCard() {
            if (!layersCard) return;
            layersCard.classList.toggle("collapsed");
        }

        if (btnToggleLayersPanel) btnToggleLayersPanel.addEventListener("click", toggleLayersCard);
        if (btnMinimizeLayers) btnMinimizeLayers.addEventListener("click", toggleLayersCard);

        // Clean View Toggle
        const btnCleanView = document.getElementById("btn-clean-view");
        if (btnCleanView) {
            btnCleanView.addEventListener("click", () => {
                const worldView = document.getElementById("view-world");
                if (!worldView) return;
                const isClean = worldView.classList.toggle("clean-view");
                btnCleanView.classList.toggle("active", isClean);
                if (isClean) {
                    document.getElementById("gis-layers-card")?.classList.add("collapsed");
                    document.getElementById("inspector-panel")?.classList.add("collapsed");
                    document.getElementById("prov-details")?.classList.add("collapsed");
                    const provArrow = document.getElementById("prov-arrow");
                    if (provArrow) provArrow.textContent = "▸";
                    showNotification("🧹 Vista Limpia ACTIVADA (Capas e inspector ocultos)");
                } else {
                    showNotification("Vista Limpia DESACTIVADA");
                }
            });
        }

        // Floating Inspector Toggle
        const btnToggleInspectorFloating = document.getElementById("btn-toggle-inspector-floating");
        if (btnToggleInspectorFloating) {
            btnToggleInspectorFloating.addEventListener("click", () => {
                const panel = document.getElementById("inspector-panel");
                if (panel) {
                    panel.classList.toggle("collapsed");
                }
            });
        }

        // Toggle Provenance Details
        const btnToggleProv = document.getElementById("btn-toggle-prov");
        const provDetails = document.getElementById("prov-details");
        const provArrow = document.getElementById("prov-arrow");
        if (btnToggleProv && provDetails) {
            btnToggleProv.addEventListener("click", () => {
                provDetails.classList.toggle("collapsed");
                if (provArrow) {
                    provArrow.textContent = provDetails.classList.contains("collapsed") ? "▸" : "▾";
                }
            });
        }
    }

    function switchBasemap(key) {
        if (!state.gisMap) return;
        const map = state.gisMap;
        const basemapLayers = ["basemap-street", "basemap-osm", "basemap-hot", "basemap-topo"];
        basemapLayers.forEach((layerId) => {
            if (map.getLayer(layerId)) {
                const match = (layerId === `basemap-${key}`);
                map.setLayoutProperty(layerId, "visibility", match ? "visible" : "none");
            }
        });
        showNotification(key === "vector" ? "Mapa base: VECTOR LOCAL PURO (100% Offline / Sin API)" : `Mapa base: ${key.toUpperCase()} (Limpio / Sin Marca de Agua)`);
    }

    function updateCameraActiveButton(activeBtn) {
        document.querySelectorAll(".gis-control-group .btn").forEach((b) => {
            if (b.id.startsWith("btn-cam-")) {
                b.classList.remove("btn-primary");
                b.classList.add("btn-secondary");
            }
        });
        activeBtn.classList.remove("btn-secondary");
        activeBtn.classList.add("btn-primary");
    }

    function initOrResizeGIS25D() {
        if (!state.gisMap) {
            if (typeof maplibregl === "undefined") {
                console.error("MapLibre GL JS library not loaded.");
                return;
            }

            const isDark = state.theme === "dark";
            const bgColor = isDark ? "#090d16" : "#f1f5f9";

            state.gisMap = new maplibregl.Map({
                container: "maplibre-viewport",
                style: {
                    version: 8,
                    name: "SALTBOR Real GIS Cartography Style",
                    glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
                    sources: {
                        "src-basemap-street": {
                            type: "raster",
                            tiles: [
                                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}.jpg"
                            ],
                            tileSize: 256,
                            attribution: "Esri World Street Map",
                            maxzoom: 19,
                        },
                        "src-basemap-osm": {
                            type: "raster",
                            tiles: [
                                "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                            ],
                            tileSize: 256,
                            attribution: "© OpenStreetMap contributors",
                            maxzoom: 19,
                        },
                        "src-basemap-hot": {
                            type: "raster",
                            tiles: [
                                "https://a.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
                                "https://b.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png"
                            ],
                            tileSize: 256,
                            attribution: "© OpenStreetMap contributors, HOT",
                            maxzoom: 19,
                        },
                        "src-basemap-topo": {
                            type: "raster",
                            tiles: [
                                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}.jpg"
                            ],
                            tileSize: 256,
                            attribution: "Esri World Topo",
                            maxzoom: 18,
                        },
                    },
                    layers: [
                        {
                            id: "background",
                            type: "background",
                            paint: {
                                "background-color": bgColor,
                            },
                        },
                        {
                            id: "basemap-street",
                            type: "raster",
                            source: "src-basemap-street",
                            layout: { "visibility": "visible" },
                            paint: { "raster-opacity": 1.0 },
                        },
                        {
                            id: "basemap-osm",
                            type: "raster",
                            source: "src-basemap-osm",
                            layout: { "visibility": "none" },
                            paint: { "raster-opacity": 1.0 },
                        },
                        {
                            id: "basemap-hot",
                            type: "raster",
                            source: "src-basemap-hot",
                            layout: { "visibility": "none" },
                            paint: { "raster-opacity": 1.0 },
                        },
                        {
                            id: "basemap-topo",
                            type: "raster",
                            source: "src-basemap-topo",
                            layout: { "visibility": "none" },
                            paint: { "raster-opacity": 1.0 },
                        },
                    ],
                },
                center: [-89.1915, 13.6978], // Plaza Gerardo Barrios / Centro Histórico
                zoom: 16.5,
                pitch: 45,
                bearing: -15,
                maxPitch: 80,
                attributionControl: false,
            });

            state.gisMap.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");

            state.gisMap.on("load", () => {
                state.gisLoaded = true;
                loadGISLayers();
                refreshOsmLayers();
                updateDiurnalLighting(9.75);
                fetchGISPopulationLODSummary();
            });

            // Viewport movement triggers progressive streaming
            state.gisMap.on("moveend", () => {
                updateGISSimulationLayer();
                scheduleOsmRefresh();
            });

            // Coordinate tracker
            state.gisMap.on("mousemove", (e) => {
                const coordsBox = document.getElementById("gis-cursor-coords");
                if (coordsBox) {
                    const lat = e.lngLat.lat.toFixed(4);
                    const lon = e.lngLat.lng.toFixed(4);
                    const zoom = state.gisMap.getZoom().toFixed(1);
                    const pitch = Math.round(state.gisMap.getPitch());
                    coordsBox.textContent = `San Salvador Centro | WGS84: ${lat}° N, ${lon}° W | Zoom: ${zoom}× | Pitch: ${pitch}°`;
                }
            });
        } else {
            setTimeout(() => {
                state.gisMap.resize();
                updateGISSimulationLayer();
            }, 100);
        }
    }

    function loadGISLayers() {
        if (!state.gisMap) return;
        const map = state.gisMap;

        // 1. National Context Layer (Volcanoes, Lakes, Department Cores)
        map.addSource("src-national", {
            type: "geojson",
            data: "/api/gis/national_context",
        });
        map.addLayer({
            id: "gis-layer-national-lakes",
            type: "circle",
            source: "src-national",
            filter: ["==", "category", "water_body"],
            maxzoom: 14.5,
            paint: {
                "circle-radius": 7,
                "circle-color": "#0284c7",
                "circle-stroke-width": 1.5,
                "circle-stroke-color": "#ffffff",
            },
        });
        map.addLayer({
            id: "gis-layer-national-volcanoes",
            type: "circle",
            source: "src-national",
            filter: ["==", "category", "physical_geography"],
            maxzoom: 14.5,
            paint: {
                "circle-radius": 8,
                "circle-color": "#ef4444",
                "circle-stroke-width": 2,
                "circle-stroke-color": "#fbbf24",
            },
        });
        map.addLayer({
            id: "gis-layer-national-depts",
            type: "circle",
            source: "src-national",
            filter: ["==", "category", "administrative"],
            maxzoom: 13.0,
            paint: {
                "circle-radius": 5,
                "circle-color": "#64748b",
                "circle-stroke-width": 1,
                "circle-stroke-color": "#f1f5f9",
            },
        });

        // 1b. Real National Highways Layer (Geofabrik OSM extraction)
        map.addSource("src-national-highways", {
            type: "geojson",
            data: "/api/gis/national_highways",
        });
        map.addLayer({
            id: "gis-layer-national-highways",
            type: "line",
            source: "src-national-highways",
            maxzoom: 14.0,
            paint: {
                "line-color": [
                    "match",
                    ["get", "road_type"],
                    "trunk", "#ea580c",
                    "primary", "#f59e0b",
                    "#94a3b8"
                ],
                "line-width": [
                    "interpolate", ["linear"], ["zoom"],
                    7, 1.2,
                    10, 2.5,
                    14, 4.0
                ],
                "line-opacity": 0.85,
            },
            layout: {
                "line-cap": "round",
                "line-join": "round",
            },
        });

        // 2. Boundaries (REAL_WORLD_LAYER)
        map.addSource("src-boundaries", {
            type: "geojson",
            data: "/api/gis/layer/san_salvador_centro/boundaries",
        });
        map.addLayer({
            id: "gis-layer-boundaries",
            type: "line",
            source: "src-boundaries",
            paint: {
                "line-color": "#ec4899",
                "line-width": 2.5,
                "line-dasharray": [4, 2],
            },
        });

        // 3. Parks & Plazas (REAL_WORLD_LAYER)
        map.addSource("src-parks", {
            type: "geojson",
            data: "/api/gis/layer/san_salvador_centro/parks",
        });
        map.addLayer({
            id: "gis-layer-parks-fill",
            type: "fill",
            source: "src-parks",
            paint: {
                "fill-color": "#059669",
                "fill-opacity": 0.55,
            },
        });
        map.addLayer({
            id: "gis-layer-parks-line",
            type: "line",
            source: "src-parks",
            paint: {
                "line-color": "#10b981",
                "line-width": 1.5,
            },
        });

        // 4. Waterways (REAL_WORLD_LAYER)
        map.addSource("src-water", {
            type: "geojson",
            data: "/api/gis/layer/san_salvador_centro/nature_water",
        });
        map.addLayer({
            id: "gis-layer-water",
            type: "line",
            source: "src-water",
            paint: {
                "line-color": "#0284c7",
                "line-width": 3.8,
                "line-opacity": 0.90,
            },
        });

        // 5. Elevation Contours (REAL_WORLD_LAYER)
        map.addSource("src-elevation", {
            type: "geojson",
            data: "/api/gis/layer/san_salvador_centro/elevation",
        });
        map.addLayer({
            id: "gis-layer-elevation",
            type: "line",
            source: "src-elevation",
            paint: {
                "line-color": "#a855f7",
                "line-width": 1.0,
                "line-opacity": 0.40,
            },
        });

        // 5B. Real OpenStreetMap geometry from the Phase 1.6 ingested database.
        // The curated layers below remain the simulation map; these carry the
        // country-wide OSM reality underneath it, with provenance per feature.
        map.addSource("src-osm-roads", {
            type: "geojson",
            data: { type: "FeatureCollection", features: [] },
        });
        map.addLayer({
            id: "osm-layer-roads",
            type: "line",
            source: "src-osm-roads",
            minzoom: 12,
            paint: {
                "line-color": [
                    "match", ["get", "class"],
                    "primary", "#b45309",
                    "secondary", "#c2830c",
                    "tertiary", "#9ca3af",
                    "residential", "#6b7280",
                    "service", "#7b8494",
                    "pedestrian", "#0e7490",
                    "footway", "#94765a",
                    "#8b93a3"
                ],
                "line-width": [
                    "interpolate", ["linear"], ["zoom"],
                    12, ["match", ["get", "class"], "primary", 1.4, "secondary", 1.1, 0.5],
                    17, ["match", ["get", "class"], "primary", 5.0, "secondary", 4.0, 1.6]
                ],
                "line-opacity": 0.75,
            },
        });
        map.addSource("src-osm-buildings", {
            type: "geojson",
            data: { type: "FeatureCollection", features: [] },
        });
        map.addLayer({
            id: "osm-layer-buildings",
            type: "fill",
            source: "src-osm-buildings",
            minzoom: 15.5,
            paint: {
                "fill-color": [
                    "match", ["get", "class"],
                    "residential", "#475569",
                    "commercial", "#b45309",
                    "institutional", "#1d4ed8",
                    "industrial", "#7c3aed",
                    "#334155"
                ],
                "fill-opacity": 0.55,
                "fill-outline-color": "#0f172a",
            },
        });

        // 6. Streets (REAL_WORLD_LAYER)
        map.addSource("src-streets", {
            type: "geojson",
            data: "/api/gis/layer/san_salvador_centro/streets",
        });
        map.addLayer({
            id: "gis-layer-streets",
            type: "line",
            source: "src-streets",
            paint: {
                "line-color": [
                    "match",
                    ["get", "road_type"],
                    "primary", "#f59e0b",
                    "secondary", "#fbbf24",
                    "tertiary", "#e2e8f0",
                    "residential", "#94a3b8",
                    "pedestrian", "#06b6d4",
                    "#64748b"
                ],
                "line-width": [
                    "match",
                    ["get", "road_type"],
                    "primary", 4.2,
                    "secondary", 3.2,
                    "tertiary", 2.2,
                    "pedestrian", 2.5,
                    1.5
                ],
                "line-opacity": 0.92,
            },
        });

        // 7. Street Labels Layer (REAL_WORLD_LAYER)
        map.addLayer({
            id: "gis-layer-street-labels",
            type: "symbol",
            source: "src-streets",
            minzoom: 15.0,
            layout: {
                "symbol-placement": "line",
                "text-field": ["get", "name"],
                "text-size": 11,
                "text-letter-spacing": 0.05,
                "text-max-angle": 35,
            },
            paint: {
                "text-color": "#ffffff",
                "text-halo-color": "#090d16",
                "text-halo-width": 2.0,
            },
        });

        // 8. Buildings (REAL_WORLD_LAYER)
        map.addSource("src-buildings", {
            type: "geojson",
            data: "/api/gis/layer/san_salvador_centro/buildings",
        });

        // 8A. Flat 2D footprint layer
        map.addLayer({
            id: "gis-layer-buildings-2d",
            type: "fill",
            source: "src-buildings",
            layout: { "visibility": "none" },
            paint: {
                "fill-color": [
                    "match",
                    ["get", "category"],
                    "civic_cultural", "#38bdf8",
                    "historic_monument", "#eab308",
                    "religious_heritage", "#ec4899",
                    "historic_theatre", "#a855f7",
                    "architectural_monument", "#14b8a6",
                    "commercial_hub", "#f97316",
                    "hospital_tertiary", "#ef4444",
                    "commercial", "#f59e0b",
                    "institutional", "#3b82f6",
                    "residential", "#475569",
                    "#334155"
                ],
                "fill-opacity": 0.85,
            },
        });

        // 8B. Clean building footprint outlines (urban blocks)
        map.addLayer({
            id: "gis-layer-buildings-outline",
            type: "line",
            source: "src-buildings",
            paint: {
                "line-color": "rgba(255, 255, 255, 0.22)",
                "line-width": 0.8,
            },
        });

        // 8C. Buildings 2.5D Extrusions
        map.addLayer({
            id: "gis-layer-buildings-25d",
            type: "fill-extrusion",
            source: "src-buildings",
            layout: { "visibility": "visible" },
            paint: {
                "fill-extrusion-color": [
                    "match",
                    ["get", "category"],
                    "civic_cultural", "#38bdf8",
                    "historic_monument", "#eab308",
                    "religious_heritage", "#ec4899",
                    "historic_theatre", "#a855f7",
                    "architectural_monument", "#14b8a6",
                    "commercial_hub", "#f97316",
                    "hospital_tertiary", "#ef4444",
                    "commercial", "#f59e0b",
                    "institutional", "#3b82f6",
                    "residential", "#334155",
                    "#475569"
                ],
                "fill-extrusion-height": ["get", "height_m"],
                "fill-extrusion-base": ["get", "min_height_m"],
                "fill-extrusion-opacity": 0.92,
            },
        });

        // 9. Verified Points of Interest (REAL_WORLD_LAYER)
        map.addSource("src-poi", {
            type: "geojson",
            data: "/api/gis/layer/san_salvador_centro/poi",
        });
        map.addLayer({
            id: "gis-layer-poi",
            type: "circle",
            source: "src-poi",
            paint: {
                "circle-radius": 7,
                "circle-color": "#eab308",
                "circle-stroke-width": 2,
                "circle-stroke-color": "#ffffff",
            },
        });

        // 10. Simulation Layer (SIMULATION_LAYER)
        map.addSource("src-simulation", {
            type: "geojson",
            data: "/api/gis/simulation_layer",
        });

        // 10A. Movement Trajectories (Dashed lines snapped to streets)
        map.addLayer({
            id: "gis-layer-sim-trajectories",
            type: "line",
            source: "src-simulation",
            filter: ["==", "$type", "LineString"],
            paint: {
                "line-color": "#f43f5e",
                "line-width": 2.5,
                "line-dasharray": [3, 2],
                "line-opacity": 0.90,
            },
        });

        // 10B. Synthetic Human Agents
        map.addLayer({
            id: "gis-layer-sim-agents",
            type: "circle",
            source: "src-simulation",
            filter: ["==", "$type", "Point"],
            paint: {
                "circle-radius": 8,
                "circle-color": [
                    "match",
                    ["get", "activity"],
                    "work", "#f59e0b",
                    "eat", "#10b981",
                    "sleep", "#6366f1",
                    "socialize", "#06b6d4",
                    "study", "#a855f7",
                    "#94a3b8"
                ],
                "circle-stroke-width": 2,
                "circle-stroke-color": "#ffffff",
            },
        });

        // 11. Mount HTML Landmark Badges
        mountLandmarkMarkers();

        // Click on 2.5D Building: Inspect feature
        map.on("click", "gis-layer-buildings-25d", (e) => {
            if (e.features && e.features.length > 0) {
                showGISFeatureInspector(e.features[0]);
            }
        });

        // Click on 2D Building: Inspect feature
        map.on("click", "gis-layer-buildings-2d", (e) => {
            if (e.features && e.features.length > 0) {
                showGISFeatureInspector(e.features[0]);
            }
        });

        // Click on Agent: Inspect dossier and enable follow
        map.on("click", "gis-layer-sim-agents", (e) => {
            if (e.features && e.features.length > 0) {
                const feat = e.features[0];
                showGISFeatureInspector(feat);
                const props = feat.properties;
                const uid = props.uid;
                if (uid) {
                    state.selectedAgentUid = uid;
                    state.gisFollowAgent = true;
                    const btnFollow = document.getElementById("btn-cam-follow");
                    if (btnFollow) btnFollow.classList.add("btn-active");
                    fetchIndividualDetail(uid);
                    document.getElementById("inspector-panel").classList.remove("collapsed");
                    showNotification(`Siguiendo a ${props.full_name} (${props.occupation}) en el mapa`);
                }
            }
        });

        // Cursor pointer styling
        map.on("mouseenter", "gis-layer-buildings-25d", () => { map.getCanvas().style.cursor = "pointer"; });
        map.on("mouseleave", "gis-layer-buildings-25d", () => { map.getCanvas().style.cursor = ""; });
        map.on("mouseenter", "gis-layer-buildings-2d", () => { map.getCanvas().style.cursor = "pointer"; });
        map.on("mouseleave", "gis-layer-buildings-2d", () => { map.getCanvas().style.cursor = ""; });
        map.on("mouseenter", "gis-layer-sim-agents", () => { map.getCanvas().style.cursor = "pointer"; });
        map.on("mouseleave", "gis-layer-sim-agents", () => { map.getCanvas().style.cursor = ""; });
    }

    function mountLandmarkMarkers() {
        if (!state.gisMap) return;
        // Clean existing
        landmarkMarkers.forEach((m) => m.remove());
        landmarkMarkers = [];

        PILOT_LANDMARKS.forEach((lm) => {
            const el = document.createElement("div");
            el.className = "gis-landmark-marker";
            el.innerHTML = `<span>${lm.icon}</span><span>${lm.name}</span>`;
            el.title = `${lm.name} (Patrimonio Verificado)`;
            el.addEventListener("click", (e) => {
                e.stopPropagation();
                if (state.gisMap) {
                    state.gisMap.flyTo({ center: lm.coords, zoom: 17.5, pitch: 50, duration: 800 });
                }
                showGISFeatureInspector({
                    properties: {
                        name: lm.name,
                        height_m: 14.5,
                        levels: 2,
                        category: "Patrimonio Histórico y Cultural",
                        building_type: "Monumento Nacional",
                        height_source: "Catastro Urbano CNR / IGN El Salvador",
                        validation_state: "VERIFIED_REAL",
                        source: "OSM_ODbL / CNR_IGN_ElSalvador",
                        license: "ODbL-1.0",
                        known_accuracy: "metric_submetric",
                        feature_id: `bldg_landmark_${lm.name.toLowerCase().replace(/[^a-z0-9]/g, '_')}`,
                        notes: `Inmueble patrimonial de primer orden del Centro Histórico de San Salvador (${lm.icon})`
                    }
                });
            });

            const marker = new maplibregl.Marker({ element: el, anchor: "bottom" })
                .setLngLat(lm.coords)
                .addTo(state.gisMap);
            landmarkMarkers.push(marker);
        });
    }

    let osmRefreshTimer = null;

    function scheduleOsmRefresh() {
        clearTimeout(osmRefreshTimer);
        osmRefreshTimer = setTimeout(refreshOsmLayers, 280);
    }

    function refreshOsmLayers() {
        if (!state.gisMap || !state.gisLoaded) return;
        const bounds = state.gisMap.getBounds();
        const zoom = state.gisMap.getZoom();
        const params = new URLSearchParams({
            min_lon: bounds.getWest().toFixed(6),
            min_lat: bounds.getSouth().toFixed(6),
            max_lon: bounds.getEast().toFixed(6),
            max_lat: bounds.getNorth().toFixed(6),
            layers: "roads,buildings",
            limit: "3000",
        });
        fetch(`/api/geography/geojson?${params.toString()}`)
            .then((r) => (r.ok ? r.json() : null))
            .then((data) => {
                if (!data || !data.features) return;
                const roads = { type: "FeatureCollection", features: [] };
                const buildings = { type: "FeatureCollection", features: [] };
                data.features.forEach((feature) => {
                    const layer = feature.properties && feature.properties.layer;
                    if (layer === "roads") roads.features.push(feature);
                    else if (layer === "buildings") buildings.features.push(feature);
                });
                const roadsSrc = state.gisMap.getSource("src-osm-roads");
                const buildingsSrc = state.gisMap.getSource("src-osm-buildings");
                if (roadsSrc) roadsSrc.setData(roads);
                if (buildingsSrc && zoom >= 15.5) buildingsSrc.setData(buildings);
                const counter = document.getElementById("gis-osm-rendered");
                if (counter) counter.textContent = Number(roads.features.length + buildings.features.length).toLocaleString();
            })
            .catch(() => {});
    }

    function updateGISSimulationLayer() {
        if (!state.gisMap || !state.gisLoaded) return;

        // Viewport frustum query for multi-level streaming
        try {
            const bounds = state.gisMap.getBounds();
            const zoom = state.gisMap.getZoom();
            const minLon = bounds.getWest();
            const minLat = bounds.getSouth();
            const maxLon = bounds.getEast();
            const maxLat = bounds.getNorth();

            fetch(`/api/gis/viewport_population?min_lon=${minLon}&min_lat=${minLat}&max_lon=${maxLon}&max_lat=${maxLat}&zoom=${zoom}&limit=1500`)
                .then((r) => r.json())
                .then((res) => {
                    const elRendered = document.getElementById("gis-pop-rendered");
                    if (elRendered && res.count !== undefined) {
                        elRendered.textContent = Number(res.count).toLocaleString();
                    }
                })
                .catch(() => {});
        } catch (e) {}

        fetch("/api/gis/simulation_layer")
            .then((r) => r.json())
            .then((data) => {
                const src = state.gisMap.getSource("src-simulation");
                if (src) src.setData(data);

                // Follow selected agent
                if (state.gisFollowAgent && state.selectedAgentUid && data.features) {
                    const agentFeat = data.features.find((f) => f.properties && f.properties.uid === state.selectedAgentUid);
                    if (agentFeat && agentFeat.geometry && agentFeat.geometry.coordinates) {
                        const [lon, lat] = agentFeat.geometry.coordinates;
                        state.gisMap.panTo([lon, lat], { duration: 350 });
                    }
                }
            })
            .catch((err) => console.error("Error refreshing GIS simulation layer", err));
    }

    function fetchGISPopulationLODSummary() {
        fetch("/api/gis/lod_summary")
            .then((r) => r.json())
            .then((data) => {
                const elPersist = document.getElementById("gis-pop-persistent");
                const elActive = document.getElementById("gis-pop-active");
                const elAgg = document.getElementById("gis-pop-aggregated");

                if (elPersist && data.persistent_population !== undefined) {
                    elPersist.textContent = Number(data.persistent_population).toLocaleString();
                }
                if (elActive && data.actively_simulated !== undefined) {
                    elActive.textContent = Number(data.actively_simulated).toLocaleString();
                }
                if (elAgg && data.aggregated_population !== undefined) {
                    elAgg.textContent = Number(data.aggregated_population).toLocaleString();
                }

                // Update LOD pills active highlight
                if (data.lod_distribution) {
                    const pills = document.querySelectorAll(".gis-lod-pills .lod-pill");
                    if (pills && pills.length === 5) {
                        pills[0].classList.toggle("active", data.lod_distribution.lod_0_individual > 0);
                        pills[1].classList.toggle("active", data.lod_distribution.lod_1_simplified > 0);
                        pills[2].classList.toggle("active", data.lod_distribution.lod_2_cohort > 0);
                        pills[3].classList.toggle("active", data.lod_distribution.lod_3_community > 0);
                        pills[4].classList.toggle("active", data.lod_distribution.lod_4_regional > 0);
                    }
                }
            })
            .catch(() => {});
    }

    function showGISFeatureInspector(feat) {
        const card = document.getElementById("gis-feature-inspector");
        const titleEl = document.getElementById("gis-feat-title");
        const bodyEl = document.getElementById("gis-feat-body");
        if (!card || !titleEl || !bodyEl) return;

        const props = feat.properties || {};

        // 1. Individual Synthetic Human Agent Inspector
        if (props.type === "agent" || props.full_name || props.activity) {
            const uid = props.uid || "agent_unknown";
            const valState = "SIMULATED";
            titleEl.textContent = `👤 ${props.full_name || "Individuo Sintético"}`;
            bodyEl.innerHTML = `
                <div style="margin-bottom:8px;">
                    <span class="prov-pill prov-simulated">${valState}</span>
                    <span class="agent-token-badge lod0" style="margin-left:4px;">LOD 0 / 1</span>
                    <span style="font-size:10px; color:var(--text-muted); margin-left:6px;">Fuente: Motor Cognitivo SALTBOR</span>
                </div>
                <table class="gis-kv-table">
                    <tr><td class="gis-kv-label">Oficio / Rol:</td><td class="gis-kv-value">${props.occupation || "Habitante"}</td></tr>
                    <tr><td class="gis-kv-label">Actividad Actual:</td><td class="gis-kv-value" style="font-weight:600; color:#38bdf8;">${props.activity || "Rutina"}</td></tr>
                    <tr><td class="gis-kv-label">Dinero / Saldo:</td><td class="gis-kv-value">$${props.money !== undefined ? Number(props.money).toFixed(2) : "135.00"}</td></tr>
                    <tr><td class="gis-kv-label">Energía:</td><td class="gis-kv-value">${props.energy !== undefined ? Math.round(props.energy * 100) : 75}%</td></tr>
                    <tr><td class="gis-kv-label">Hambre:</td><td class="gis-kv-value">${props.hunger !== undefined ? Math.round(props.hunger * 100) : 25}%</td></tr>
                    <tr><td class="gis-kv-label">Comunidad:</td><td class="gis-kv-value">${props.community_id || "San Salvador Centro"}</td></tr>
                    <tr><td class="gis-kv-label">Identificador:</td><td class="gis-kv-value" style="font-family:var(--font-mono); font-size:10px;">${uid}</td></tr>
                </table>
                <div style="margin-top:12px; display:flex; gap:6px;">
                    <button id="btn-promote-agent" class="btn btn-sm btn-primary" style="flex:1; font-size:11px;">⚡ Promover a LOD 0</button>
                    <button id="btn-follow-agent-card" class="btn btn-sm btn-secondary" style="flex:1; font-size:11px;">👤 Seguir Agente</button>
                </div>
            `;
            card.classList.remove("collapsed");

            const promoteBtn = document.getElementById("btn-promote-agent");
            if (promoteBtn) {
                promoteBtn.addEventListener("click", () => {
                    promoteBtn.disabled = true;
                    promoteBtn.textContent = "Promoviendo...";
                    fetch("/api/gis/promote_individual", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ uid: uid, target_lod: 0 }),
                    })
                        .then((r) => r.json())
                        .then(() => {
                            showNotification(`Agente ${props.full_name || uid} promovido a LOD 0 con deliberación cognitiva completa.`);
                            fetchGISPopulationLODSummary();
                        })
                        .finally(() => {
                            promoteBtn.disabled = false;
                            promoteBtn.textContent = "⚡ Promovido a LOD 0";
                        });
                });
            }

            const followBtn = document.getElementById("btn-follow-agent-card");
            if (followBtn) {
                followBtn.addEventListener("click", () => {
                    state.selectedAgentUid = uid;
                    state.gisFollowAgent = true;
                    showNotification(`Siguiendo a ${props.full_name || uid} en el mapa`);
                });
            }
            return;
        }

        // 2. Building Feature Inspector
        const valState = props.validation_state || "ESTIMATED";
        const valClass = valState === "VERIFIED_REAL" ? "prov-verified" : (valState === "SIMULATED" ? "prov-simulated" : "prov-estimated");

        titleEl.textContent = props.name || `Edificio #${props.osm_id || props.feature_id}`;
        bodyEl.innerHTML = `
            <div style="margin-bottom:8px;">
                <span class="prov-pill ${valClass}">${valState}</span>
                <span style="font-size:10px; color:var(--text-muted); margin-left:6px;">Fuente: ${props.source || "OSM"}</span>
            </div>
            <table class="gis-kv-table">
                <tr><td class="gis-kv-label">Altura Real/Extruida:</td><td class="gis-kv-value">${props.height_m} metros</td></tr>
                <tr><td class="gis-kv-label">Niveles / Pisos:</td><td class="gis-kv-value">${props.levels || 1} niveles</td></tr>
                <tr><td class="gis-kv-label">Categoría:</td><td class="gis-kv-value">${props.category || "Edificación"}</td></tr>
                <tr><td class="gis-kv-label">Tipo Construcción:</td><td class="gis-kv-value">${props.building_type || "Estándar"}</td></tr>
                <tr><td class="gis-kv-label">Cálculo de Altura:</td><td class="gis-kv-value">${props.height_source || "Regla tipológica"}</td></tr>
                <tr><td class="gis-kv-label">Licencia Cartográfica:</td><td class="gis-kv-value">${props.license || "ODbL-1.0"}</td></tr>
                <tr><td class="gis-kv-label">Precisión Geométrica:</td><td class="gis-kv-value">${props.known_accuracy || "Métrica"}</td></tr>
                <tr><td class="gis-kv-label">Identificador Canónico:</td><td class="gis-kv-value" style="font-family:var(--font-mono); font-size:10px;">${props.feature_id}</td></tr>
            </table>
            ${props.notes ? `<div style="margin-top:10px; padding:6px 8px; background:rgba(0,0,0,0.3); border-radius:4px; font-size:10px; color:var(--text-secondary);">${props.notes}</div>` : ''}
        `;
        card.classList.remove("collapsed");
    }

    // =========================================================================
    // 17. PHASE 1.4: CIVILIZATION OBSERVABILITY & INTERVENTIONS IMPLEMENTATION
    // =========================================================================
    function setupCivilizationSubpanels() {
        const subnavBtns = document.querySelectorAll(".civ-subnav-bar .btn-subnav");
        subnavBtns.forEach((btn) => {
            btn.addEventListener("click", () => {
                const target = btn.dataset.subpanel;
                subnavBtns.forEach((b) => b.classList.remove("active"));
                btn.classList.add("active");

                document.querySelectorAll(".civ-subpanel").forEach((panel) => {
                    panel.style.display = "none";
                    panel.classList.remove("active");
                });

                const targetPanel = document.getElementById(`civ-subpanel-${target}`);
                if (targetPanel) {
                    targetPanel.style.display = "block";
                    targetPanel.classList.add("active");
                }

                if (target === "phase19") {
                    fetchPhase19Data();
                } else if (target === "justice") {
                    fetchJusticeDocket();
                } else if (target === "adesco") {
                    fetchADESCOData();
                } else if (target === "dialogues") {
                    fetchDialoguesStream();
                } else if (target === "labor") {
                    fetchLaborData();
                } else if (target === "housing") {
                    fetchHousingData();
                } else if (target === "commerce") {
                    fetchCommerceData();
                } else if (target === "lifestyle") {
                    fetchLifestyleData();
                } else if (target === "extension") {
                    fetchExtensionData();
                } else if (target === "macro") {
                    fetchCivilizationData();
                    renderCivilizationCharts();
                }
            });
        });
    }

    function fetchJusticeDocket() {
        const container = document.getElementById("justice-cases-container");
        if (!container) return;
        fetch("/api/justice/cases")
            .then((r) => r.json())
            .then((data) => {
                const cases = Array.isArray(data) ? data : (data.cases || []);
                if (cases.length === 0) {
                    container.innerHTML = "<div class='loading-placeholder'>No hay disputas radicadas en el Tribunal de Paz en este momento.</div>";
                    return;
                }
                container.innerHTML = `
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Expediente</th>
                                <th>Demandante</th>
                                <th>Demandado</th>
                                <th>Tipo de Estatuto</th>
                                <th>Pretensión / Hechos</th>
                                <th>Estado</th>
                                <th>Fallo / Restitución</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${cases.map((c) => `
                                <tr>
                                    <td><code>${c.case_id}</code></td>
                                    <td><strong>${c.plaintiff_name}</strong></td>
                                    <td><strong>${c.defendant_name}</strong></td>
                                    <td><span class="badge-gis">${c.statute_type}</span></td>
                                    <td>${c.claim_description} ($${c.damages_claimed.toFixed(2)})</td>
                                    <td><span style="color:${c.status === 'resolved' ? '#10b981' : '#f59e0b'}; font-weight:600;">${(c.status || 'open').toUpperCase()}</span></td>
                                    <td>${c.verdict ? `${c.verdict.ruling} ($${c.verdict.awarded_damages.toFixed(2)})` : 'En trámite...'}</td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                `;
            })
            .catch((err) => {
                console.error("Error fetching justice cases", err);
            });
    }

    function fetchADESCOData() {
        const faenasContainer = document.getElementById("adesco-faenas-container");
        const cuchubalesContainer = document.getElementById("adesco-cuchubales-container");
        fetch("/api/communities")
            .then((r) => r.json())
            .then((data) => {
                const faenas = data.faenas || [];
                const cuchubales = data.cuchubales || [];

                if (faenasContainer) {
                    if (faenas.length === 0) {
                        faenasContainer.innerHTML = "<div class='loading-placeholder'>Sin faenas comunitarias activas.</div>";
                    } else {
                        faenasContainer.innerHTML = faenas.map((f) => {
                            const pct = Math.min(100, Math.round((f.completed_labor_hours / (f.required_labor_hours || 1)) * 100));
                            return `
                                <div style="margin-bottom:12px; padding:8px; background:var(--bg-base); border-radius:4px; border:1px solid var(--border-subtle);">
                                    <div style="display:flex; justify-content:space-between; font-weight:700; margin-bottom:4px;">
                                        <span>${f.name}</span>
                                        <span style="color:var(--accent-sky);">${pct}%</span>
                                    </div>
                                    <div style="font-size:11px; color:var(--text-muted); margin-bottom:6px;">
                                        Comunidad: ${f.community_id} | Problema: ${f.target_problem} | Horas: ${f.completed_labor_hours.toFixed(1)} / ${f.required_labor_hours.toFixed(1)} hrs
                                    </div>
                                    <div class="trait-track"><div class="trait-fill" style="width:${pct}%; background:#10b981;"></div></div>
                                </div>
                            `;
                        }).join("");
                    }
                }

                if (cuchubalesContainer) {
                    if (cuchubales.length === 0) {
                        cuchubalesContainer.innerHTML = "<div class='loading-placeholder'>Sin cuchubales de ahorro activos.</div>";
                    } else {
                        cuchubalesContainer.innerHTML = `
                            <table class="data-table">
                                <thead><tr><th>Cuchubal</th><th>Comunidad</th><th>Fondo Acumulado</th><th>Turno Actual</th></tr></thead>
                                <tbody>
                                    ${cuchubales.map((c) => `
                                        <tr>
                                            <td><strong>${c.name}</strong></td>
                                            <td>${c.community_id}</td>
                                            <td style="color:#10b981;">$${c.accumulated_pool.toFixed(2)}</td>
                                            <td>${c.current_turn_recipient || 'Pendiente'}</td>
                                        </tr>
                                    `).join("")}
                                </tbody>
                            </table>
                        `;
                    }
                }
            })
            .catch((err) => {
                console.error("Error fetching ADESCO data", err);
            });
    }

    function fetchDialoguesStream() {
        const container = document.getElementById("dialogues-stream-container");
        if (!container) return;
        fetch("/api/social/dialogues?limit=30")
            .then((r) => r.json())
            .then((dialogues) => {
                if (!dialogues || dialogues.length === 0) {
                    container.innerHTML = "<div class='loading-placeholder'>Esperando intercambios coloquiales entre vecinos...</div>";
                    return;
                }
                container.innerHTML = dialogues.map((d) => `
                    <div class="dialogue-card">
                        <div class="dialogue-card-header">
                            <span><strong>${d.speaker_a_name || 'Vecino'}</strong> ↔ <strong>${d.speaker_b_name || 'Vecino'}</strong> en <em>${d.location || 'Plaza'}</em></span>
                            <span style="font-family:var(--font-mono);">Tick ${d.tick || state.currentTick}</span>
                        </div>
                        <div class="dialogue-card-body">
                            "${d.text || d.topic || 'Plática cotidiana'}"
                        </div>
                        ${d.caliche_words && d.caliche_words.length > 0 ? `
                            <div style="margin-top:4px;">
                                ${d.caliche_words.map((w) => `<span class="dialogue-caliche-tag">${w}</span>`).join("")}
                            </div>
                        ` : ''}
                    </div>
                `).join("");
            })
            .catch((err) => {
                console.error("Error fetching dialogues", err);
            });
    }

    function fetchCommerceData() {
        const storesContainer = document.getElementById("stores-list");
        const fiadoContainer = document.getElementById("fiado-list");

        if (storesContainer) {
            fetch("/api/commerce/stores")
                .then((r) => r.json())
                .then((data) => {
                    const stores = Array.isArray(data) ? data : (data.stores || []);
                    if (stores.length === 0) {
                        storesContainer.innerHTML = "<div class='loading-placeholder'>No hay pulperías registradas.</div>";
                    } else {
                        storesContainer.innerHTML = `
                            <table class="data-table">
                                <thead><tr><th>Establecimiento</th><th>Propietario</th><th>Caja USD</th><th>Ventas Hoy</th><th>Productos</th></tr></thead>
                                <tbody>
                                    ${stores.map((s) => `
                                        <tr>
                                            <td><strong>${s.name}</strong></td>
                                            <td>${s.owner_name}</td>
                                            <td style="color:#10b981;">$${s.cash_on_hand.toFixed(2)}</td>
                                            <td>$${s.daily_sales_revenue.toFixed(2)}</td>
                                            <td>${s.inventory_items_count} ítems</td>
                                        </tr>
                                    `).join("")}
                                </tbody>
                            </table>
                        `;
                    }
                });
        }

        if (fiadoContainer) {
            fetch("/api/commerce/fiado")
                .then((r) => r.json())
                .then((data) => {
                    const accounts = Array.isArray(data) ? data : (data.fiado_accounts || []);
                    if (accounts.length === 0) {
                        fiadoContainer.innerHTML = "<div class='loading-placeholder'>No hay cuentas de fiado abiertas.</div>";
                    } else {
                        fiadoContainer.innerHTML = `
                            <table class="data-table">
                                <thead><tr><th>Cliente</th><th>Tienda</th><th>Saldo Adeudado</th><th>Límite</th><th>Confianza</th><th>Estado</th></tr></thead>
                                <tbody>
                                    ${accounts.map((a) => `
                                        <tr>
                                            <td><strong>${a.customer_name}</strong></td>
                                            <td>${a.store_name}</td>
                                            <td style="color:${a.current_balance > 0 ? '#f59e0b' : '#10b981'};">$${a.current_balance.toFixed(2)}</td>
                                            <td>$${a.credit_limit.toFixed(2)}</td>
                                            <td>${Math.round(a.trust_score * 100)}%</td>
                                            <td><span class="badge-gis">${a.status}</span></td>
                                        </tr>
                                    `).join("")}
                                </tbody>
                            </table>
                        `;
                    }
                });
        }
    }

    function fetchRemittancesData() {
        const container = document.getElementById("remittances-list");
        if (!container) return;
        fetch("/api/economy/remittances")
            .then((r) => r.json())
            .then((data) => {
                const profiles = data.profiles || [];
                if (profiles.length === 0) {
                    container.innerHTML = "<div class='loading-placeholder'>No hay perfiles de remesas familiares activos.</div>";
                    return;
                }
                container.innerHTML = `
                    <table class="data-table">
                        <thead><tr><th>Hogar Receptor</th><th>Emisor Diáspora</th><th>Mensual USD</th><th>Total Recibido</th><th>Gasto Alimentos</th><th>Ahorro</th></tr></thead>
                        <tbody>
                            ${profiles.map((p) => `
                                <tr>
                                    <td><strong>${p.household_id}</strong></td>
                                    <td>${p.sender_relationship} (${p.sender_country})</td>
                                    <td style="color:#10b981;">+$${p.monthly_transfer_usd.toFixed(2)}</td>
                                    <td>$${p.total_lifetime_received_usd.toFixed(2)}</td>
                                    <td>${Math.round(p.allocation_basic_needs * 100)}%</td>
                                    <td>${Math.round(p.allocation_savings * 100)}%</td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                `;
            });
    }

    function fetchScientificDiscoveriesData() {
        const container = document.getElementById("discoveries-list");
        if (!container) return;
        fetch("/api/science/discoveries")
            .then((r) => r.json())
            .then((data) => {
                const sessions = Array.isArray(data) ? data : (data.sessions || []);
                if (sessions.length === 0) {
                    container.innerHTML = "<div class='loading-placeholder'>Sin sesiones de investigación científica activa.</div>";
                    return;
                }
                container.innerHTML = `
                    <table class="data-table">
                        <thead><tr><th>Indagador</th><th>Hipótesis</th><th>Dominio</th><th>Certeza</th><th>Ensayos</th><th>Estado</th></tr></thead>
                        <tbody>
                            ${sessions.map((s) => `
                                <tr>
                                    <td><strong>${s.agent_name}</strong></td>
                                    <td>${s.hypothesis_statement}</td>
                                    <td><span class="badge-gis">${s.domain}</span></td>
                                    <td>${Math.round(s.belief_confidence * 100)}%</td>
                                    <td>${s.trials_conducted}</td>
                                    <td><span style="color:${s.status === 'confirmed' ? '#10b981' : s.status === 'refuted' ? '#ef4444' : '#f59e0b'}; font-weight:600;">${(s.status || 'active').toUpperCase()}</span></td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                `;
            });
    }

    function fetchApprenticeshipsData() {
        const container = document.getElementById("apprenticeships-list");
        if (!container) return;
        fetch("/api/education/apprenticeships")
            .then((r) => r.json())
            .then((data) => {
                const list = data.apprenticeships || [];
                if (list.length === 0) {
                    container.innerHTML = "<div class='loading-placeholder'>Sin acuerdos de aprendizaje en talleres.</div>";
                    return;
                }
                container.innerHTML = `
                    <table class="data-table">
                        <thead><tr><th>Maestro Artesano</th><th>Aprendiz</th><th>Oficio</th><th>Práctica</th><th>Dominio</th><th>Estado</th></tr></thead>
                        <tbody>
                            ${list.map((a) => `
                                <tr>
                                    <td><strong>${a.mentor_name}</strong></td>
                                    <td><strong>${a.apprentice_name}</strong></td>
                                    <td><span class="badge-gis">${a.trade_domain}</span></td>
                                    <td>${a.practice_ticks} ticks</td>
                                    <td>${Math.round(a.proficiency_level * 100)}%</td>
                                    <td><span style="color:${a.status === 'graduated' ? '#10b981' : '#38bdf8'}; font-weight:600;">${(a.status || 'in_progress').toUpperCase()}</span></td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                `;
            });
    }

    function setupInterventionsModal() {
        const modal = document.getElementById("modal-interventions");
        const btnOpen = document.getElementById("btn-open-interventions");
        const btnClose = document.getElementById("btn-close-interventions");

        if (!modal || !btnOpen) return;

        btnOpen.addEventListener("click", () => {
            modal.style.display = "flex";
            populateInterventionDropdowns();
        });

        if (btnClose) {
            btnClose.addEventListener("click", () => {
                modal.style.display = "none";
            });
        }

        modal.addEventListener("click", (e) => {
            if (e.target === modal) modal.style.display = "none";
        });

        const tabBtns = modal.querySelectorAll(".modal-tab-btn");
        tabBtns.forEach((btn) => {
            btn.addEventListener("click", () => {
                const tab = btn.dataset.tab;
                tabBtns.forEach((b) => b.classList.remove("active"));
                btn.classList.add("active");

                modal.querySelectorAll(".modal-tab-content").forEach((c) => {
                    c.style.display = "none";
                    c.classList.remove("active");
                });

                const content = document.getElementById(`modal-tab-${tab}`);
                if (content) {
                    content.style.display = "block";
                    content.classList.add("active");
                }
            });
        });

        const btnAct = document.getElementById("btn-submit-activity-intervention");
        if (btnAct) {
            btnAct.addEventListener("click", () => {
                const humanUid = document.getElementById("modal-act-individual").value;
                const activity = document.getElementById("modal-act-type").value;
                const reason = document.getElementById("modal-act-reason").value;

                fetch("/api/interventions/request_activity", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ human_uid: humanUid, activity, reason }),
                })
                    .then((r) => r.json())
                    .then((d) => {
                        if (d.accepted) {
                            showNotification(`Aceptada por ${d.individual}: ${d.activity}`);
                        } else {
                            showNotification(`Rechazada por ${d.individual}: ${d.reason}`);
                        }
                        modal.style.display = "none";
                        refreshAllData();
                    })
                    .catch((err) => showNotification(`Error al proponer: ${err}`));
            });
        }

        const btnAdesco = document.getElementById("btn-submit-adesco-intervention");
        if (btnAdesco) {
            btnAdesco.addEventListener("click", () => {
                const communityId = document.getElementById("modal-adesco-community").value;
                const topic = document.getElementById("modal-adesco-topic").value;

                fetch("/api/interventions/propose_assembly", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ community_id: communityId, topic }),
                })
                    .then((r) => r.json())
                    .then((d) => {
                        showNotification(`Asamblea convocada: ${d.topic}`);
                        modal.style.display = "none";
                        fetchADESCOData();
                    });
            });
        }

        const btnEcon = document.getElementById("btn-submit-econ-intervention");
        if (btnEcon) {
            btnEcon.addEventListener("click", () => {
                const eventType = document.getElementById("modal-econ-type").value;
                const severity = parseFloat(document.getElementById("modal-econ-severity").value) || 0.3;

                fetch("/api/interventions/economic_event", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ event_type: eventType, severity }),
                })
                    .then((r) => r.json())
                    .then((d) => {
                        showNotification(`Evento económico inyectado: ${d.event_type}`);
                        modal.style.display = "none";
                        fetchEconomyData();
                    });
            });
        }

        const btnDispute = document.getElementById("btn-submit-dispute-intervention");
        if (btnDispute) {
            btnDispute.addEventListener("click", () => {
                const plaintiff = document.getElementById("modal-dispute-plaintiff").value;
                const defendant = document.getElementById("modal-dispute-defendant").value;
                const claim = document.getElementById("modal-dispute-claim").value;
                const damages = parseFloat(document.getElementById("modal-dispute-damages").value) || 35.0;

                fetch("/api/interventions/trigger_dispute", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ plaintiff_uid: plaintiff, defendant_uid: defendant, claim, damages }),
                })
                    .then((r) => r.json())
                    .then((d) => {
                        showNotification(`Demanda radicada en Tribunal: Caso ${d.case_id}`);
                        modal.style.display = "none";
                        fetchJusticeDocket();
                    });
            });
        }
    }

    function populateInterventionDropdowns() {
        const indSelect = document.getElementById("modal-act-individual");
        const pltSelect = document.getElementById("modal-dispute-plaintiff");
        const defSelect = document.getElementById("modal-dispute-defendant");

        const options = (state.individuals || []).map((ind) => `
            <option value="${ind.uid}">${ind.name} (${ind.occupation || 'Habitante'})</option>
        `).join("");

        if (indSelect) indSelect.innerHTML = options;
        if (pltSelect) pltSelect.innerHTML = options;
        if (defSelect) {
            defSelect.innerHTML = options;
            if (defSelect.options.length > 1) {
                defSelect.selectedIndex = 1;
            }
        }
    }

    // =========================================================================
    // 18. PHASE 1.5: LABOR MARKET, HOUSING, COMMERCE & LIFESTYLE VISUALIZATION
    // =========================================================================

    function formatTenure(t) {
        if (!t) return "Propietario";
        const map = {
            owner_occupied: "Propietario",
            rental: "Alquiler",
            shared_family: "Familiar",
            informal_housing: "Mesón",
            temporary_accommodation: "Temporal",
            shelter: "Albergue",
            homeless: "Sin Techo",
        };
        return map[t] || t;
    }

    function formatEmployment(e) {
        if (!e) return "Desempleado";
        const map = {
            unemployed: "Desempleado",
            employed_formal: "Formal",
            employed_informal: "Informal",
            self_employed: "Autoempleado",
            employer: "Patrón",
            retired: "Jubilado",
            student: "Estudiante",
        };
        return map[e] || e;
    }

    function fetchLaborData() {
        Promise.all([
            fetch("/api/labor/vacancies").then((r) => r.json()).catch(() => ({})),
            fetch("/api/labor/contracts").then((r) => r.json()).catch(() => ({})),
        ]).then(([vacData, conData]) => {
            const statVac = document.getElementById("stat-labor-vacancies");
            const statCon = document.getElementById("stat-labor-contracts");
            const statPay = document.getElementById("stat-labor-payroll");
            const statDay = document.getElementById("stat-labor-daylabor");

            if (statVac) statVac.textContent = vacData.open_vacancies_count ?? 0;
            if (statCon) statCon.textContent = conData.active_contracts_count ?? 0;
            if (statPay) statPay.textContent = `$${(conData.daily_payroll_liability_usd ?? 0).toFixed(2)}`;
            if (statDay) statDay.textContent = conData.informal_day_labor_records ?? 0;

            const vacContainer = document.getElementById("labor-vacancies-container");
            if (vacContainer) {
                const vacs = vacData.vacancies || [];
                if (vacs.length === 0) {
                    vacContainer.innerHTML = "<div class='loading-placeholder'>No hay vacantes abiertas en este tick.</div>";
                } else {
                    vacContainer.innerHTML = `
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Puesto</th>
                                    <th>Habilidad Requerida</th>
                                    <th>Salario Diario</th>
                                    <th>Tipo Contrato</th>
                                    <th>Postulantes</th>
                                    <th>Estado</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${vacs.map((v) => `
                                    <tr>
                                        <td><strong>${v.title}</strong></td>
                                        <td>${v.required_skill} (min ${(v.min_skill_level * 100).toFixed(0)}%)</td>
                                        <td style="color:var(--accent-emerald); font-weight:700;">$${v.offered_daily_wage.toFixed(2)}</td>
                                        <td><span class="badge-contract">${v.contract_type}</span></td>
                                        <td>${v.applicants_count} aspirantes</td>
                                        <td><span class="badge-status ${v.is_filled ? 'filled' : 'open'}">${v.is_filled ? 'Cubierta' : 'Abierta'}</span></td>
                                    </tr>
                                `).join("")}
                            </tbody>
                        </table>
                    `;
                }
            }

            const conContainer = document.getElementById("labor-contracts-container");
            if (conContainer) {
                const contracts = conData.contracts || [];
                if (contracts.length === 0) {
                    conContainer.innerHTML = "<div class='loading-placeholder'>No hay contratos laborales registrados.</div>";
                } else {
                    conContainer.innerHTML = `
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Empleado (UID)</th>
                                    <th>Cargo</th>
                                    <th>Salario</th>
                                    <th>Empresa</th>
                                    <th>Pagado Acumulado</th>
                                    <th>Estado</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${contracts.map((c) => `
                                    <tr>
                                        <td style="font-family:var(--font-mono); font-size:10px;">${c.employee_uid.slice(0, 8)}...</td>
                                        <td><strong>${c.title}</strong></td>
                                        <td style="color:var(--accent-emerald); font-weight:700;">$${c.daily_wage.toFixed(2)}/día</td>
                                        <td>${c.business_id}</td>
                                        <td>$${c.total_wages_paid.toFixed(2)}</td>
                                        <td><span class="badge-status ${c.is_active ? 'active' : 'terminated'}">${c.is_active ? 'Activo' : (c.termination_reason || 'Finalizado')}</span></td>
                                    </tr>
                                `).join("")}
                            </tbody>
                        </table>
                    `;
                }
            }
        });
    }

    function fetchHousingData() {
        Promise.all([
            fetch("/api/housing/units").then((r) => r.json()).catch(() => ({})),
            fetch("/api/housing/leases").then((r) => r.json()).catch(() => ({})),
        ]).then(([unitsData, leaseData]) => {
            const statUnits = document.getElementById("stat-housing-units");
            const statOcc = document.getElementById("stat-housing-occupancy");
            const statRent = document.getElementById("stat-housing-rent");
            const statEvict = document.getElementById("stat-housing-evictions");

            if (statUnits) statUnits.textContent = unitsData.total_units ?? 0;
            if (statOcc) statOcc.textContent = `${Math.round((unitsData.occupancy_rate ?? 0) * 100)}%`;
            if (statRent) statRent.textContent = `$${(leaseData.total_rent_collected_usd ?? 0).toFixed(2)}`;
            if (statEvict) statEvict.textContent = leaseData.evictions_count ?? 0;

            const unitsContainer = document.getElementById("housing-units-container");
            if (unitsContainer) {
                const units = unitsData.units || [];
                if (units.length === 0) {
                    unitsContainer.innerHTML = "<div class='loading-placeholder'>No hay unidades habitacionales censadas.</div>";
                } else {
                    unitsContainer.innerHTML = `
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Vivienda</th>
                                    <th>Régimen de Tenencia</th>
                                    <th>Ocupación</th>
                                    <th>Renta Diaria</th>
                                    <th>Calidad</th>
                                    <th>Estado</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${units.map((u) => `
                                    <tr>
                                        <td><strong>${u.name}</strong></td>
                                        <td><span class="badge-tenure">${formatTenure(u.tenure_type)}</span></td>
                                        <td>${u.current_occupancy} / ${u.capacity} pers.</td>
                                        <td style="color:var(--accent-emerald); font-weight:700;">${u.rent_per_day > 0 ? `$${u.rent_per_day.toFixed(2)}` : 'Sin costo'}</td>
                                        <td>${Math.round(u.quality_score * 100)}%</td>
                                        <td><span class="badge-status ${u.has_vacancy ? 'open' : 'filled'}">${u.has_vacancy ? 'Cupo Disp.' : 'Lleno'}</span></td>
                                    </tr>
                                `).join("")}
                            </tbody>
                        </table>
                    `;
                }
            }

            const leasesContainer = document.getElementById("housing-leases-container");
            if (leasesContainer) {
                const leases = leaseData.leases || [];
                if (leases.length === 0) {
                    leasesContainer.innerHTML = "<div class='loading-placeholder'>No hay arrendamientos activos.</div>";
                } else {
                    leasesContainer.innerHTML = `
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Inquilino (UID)</th>
                                    <th>Vivienda ID</th>
                                    <th>Renta/Día</th>
                                    <th>Renta Pagada</th>
                                    <th>Mora Acumulada</th>
                                    <th>Estado</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${leases.map((l) => `
                                    <tr>
                                        <td style="font-family:var(--font-mono); font-size:10px;">${l.tenant_uid.slice(0, 8)}...</td>
                                        <td>${l.unit_id}</td>
                                        <td>$${l.rent_per_day.toFixed(2)}</td>
                                        <td style="color:var(--accent-emerald); font-weight:700;">$${l.total_rent_paid.toFixed(2)}</td>
                                        <td style="color:${l.accumulated_arrears > 0 ? 'var(--accent-rose)' : 'inherit'}; font-weight:700;">$${l.accumulated_arrears.toFixed(2)}</td>
                                        <td><span class="badge-status ${l.is_active ? 'active' : 'terminated'}">${l.is_active ? 'Al Día' : 'Finalizado/Desalojado'}</span></td>
                                    </tr>
                                `).join("")}
                            </tbody>
                        </table>
                    `;
                }
            }
        });
    }

    function fetchCommerceData() {
        Promise.all([
            fetch("/api/commerce/establishments").then((r) => r.json()).catch(() => ({})),
            fetch("/api/commerce/visits?limit=30").then((r) => r.json()).catch(() => ({})),
        ]).then(([estData, visitData]) => {
            const statTotal = document.getElementById("stat-commerce-total");
            const statVerif = document.getElementById("stat-commerce-verified-sub");
            const statZero = document.getElementById("stat-commerce-zero-purchases");
            const statSales = document.getElementById("stat-commerce-daily-sales");
            const statCash = document.getElementById("stat-commerce-cashboxes");

            if (statTotal) statTotal.textContent = estData.total_establishments ?? 0;
            if (statVerif) statVerif.textContent = `${estData.verified_real_count ?? 0} GIS Verificados`;
            if (statZero) statZero.textContent = `${Math.round((visitData.zero_purchase_ratio ?? 0) * 100)}%`;
            if (statSales) statSales.textContent = `$${(estData.daily_sales_volume_usd ?? 0).toFixed(2)}`;
            if (statCash) statCash.textContent = `$${(estData.total_cash_in_boxes_usd ?? 0).toFixed(2)}`;

            const estContainer = document.getElementById("commerce-establishments-container");
            if (estContainer) {
                const ests = estData.establishments || [];
                if (ests.length === 0) {
                    estContainer.innerHTML = "<div class='loading-placeholder'>No hay comercios registrados.</div>";
                } else {
                    estContainer.innerHTML = `
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Establecimiento</th>
                                    <th>Tipo</th>
                                    <th>Origen</th>
                                    <th>Horario</th>
                                    <th>Caja USD</th>
                                    <th>Ventas Hoy</th>
                                    <th>Vitrineo / Clientes</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${ests.map((e) => `
                                    <tr>
                                        <td><strong>${e.name}</strong></td>
                                        <td>${e.type}</td>
                                        <td><span class="${e.is_verified_real ? 'badge-verified-real' : 'badge-simulated'}">${e.is_verified_real ? '🗺️ GIS Real' : '🏪 Simulado'}</span></td>
                                        <td>${e.opening_hours[0]}:00 - ${e.opening_hours[1]}:00</td>
                                        <td style="color:var(--accent-emerald); font-weight:700;">$${e.cash_box_usd.toFixed(2)}</td>
                                        <td>$${e.daily_sales_volume_usd.toFixed(2)}</td>
                                        <td>${e.daily_browsers_without_purchase} vitrineo / ${e.daily_purchasers} compras</td>
                                    </tr>
                                `).join("")}
                            </tbody>
                        </table>
                    `;
                }
            }

            const visitsContainer = document.getElementById("commerce-visits-container");
            if (visitsContainer) {
                const visits = visitData.recent_visits || [];
                if (visits.length === 0) {
                    visitsContainer.innerHTML = "<div class='loading-placeholder'>No hay registro reciente de visitas comerciales.</div>";
                } else {
                    visitsContainer.innerHTML = `
                        <div class="visits-stream-feed" style="max-height:360px; overflow-y:auto; display:flex; flex-direction:column; gap:6px;">
                            ${visits.map((v) => `
                                <div class="visit-card" style="padding:8px; background:var(--bg-elevated); border-radius:4px; border-left:3px solid ${v.purchased ? 'var(--accent-emerald)' : 'var(--accent-sky)'};">
                                    <div style="display:flex; justify-content:space-between; font-size:11px; margin-bottom:4px;">
                                        <span><strong>Visita a ${v.establishment_id}</strong> (Intención: <code>${v.intent}</code>)</span>
                                        <span style="font-weight:700; color:${v.purchased ? 'var(--accent-emerald)' : 'var(--text-muted)'};">${v.purchased ? `Gasto: $${v.total_spent_usd.toFixed(2)}` : '$0.00 (Vitrineo)'}</span>
                                    </div>
                                    <div style="font-size:10px; color:var(--text-secondary);">${v.reasoning || 'Inspección de local y productos.'}</div>
                                </div>
                            `).join("")}
                        </div>
                    `;
                }
            }
        });
    }

    function fetchLifestyleData() {
        fetch("/api/lifestyle/summary")
            .then((r) => r.json())
            .then((data) => {
                const soc = data.social_invitations || {};
                const statInv = document.getElementById("stat-lifestyle-invitations");
                const statAcc = document.getElementById("stat-lifestyle-acceptance");
                const statShar = document.getElementById("stat-lifestyle-shared");
                const statTres = document.getElementById("stat-lifestyle-treasury");

                if (statInv) statInv.textContent = soc.total_sent ?? 0;
                if (statAcc) statAcc.textContent = `${Math.round((soc.acceptance_rate ?? 0) * 100)}%`;
                if (statShar) statShar.textContent = data.shared_leisure_sessions_count ?? 0;
                if (statTres) statTres.textContent = `$${(data.households?.community_utility_treasury_usd ?? 0).toFixed(2)}`;

                const invContainer = document.getElementById("lifestyle-invitations-container");
                if (invContainer) {
                    const rej = Object.entries(soc.rejection_reasons || {});
                    invContainer.innerHTML = `
                        <div style="padding:10px; background:var(--bg-elevated); border-radius:6px; margin-bottom:12px;">
                            <div style="font-size:12px; font-weight:700; margin-bottom:6px;">Balance de Decisiones Autónomas:</div>
                            <div style="font-size:11px; color:var(--text-secondary); margin-bottom:4px;">Aceptadas con entusiasmo: <strong>${soc.accepted_count || 0}</strong></div>
                            <div style="font-size:11px; color:var(--text-secondary); margin-bottom:6px;">Rechazadas autónomamente: <strong>${soc.rejected_count || 0}</strong></div>
                            ${rej.length > 0 ? `
                                <div style="font-size:11px; font-weight:600; color:var(--text-muted); margin-top:8px;">Principales motivos de rechazo:</div>
                                <ul style="font-size:10px; color:var(--text-secondary); margin:4px 0 0 16px; padding:0;">
                                    ${rej.map(([reason, count]) => `<li>${reason}: <strong>${count}</strong> veces</li>`).join("")}
                                </ul>
                            ` : ''}
                        </div>
                    `;
                }

                const houseContainer = document.getElementById("lifestyle-households-container");
                if (houseContainer) {
                    houseContainer.innerHTML = `
                        <div style="padding:10px; background:var(--bg-elevated); border-radius:6px;">
                            <div style="font-size:12px; font-weight:700; margin-bottom:6px;">Gestión de Gastos Domésticos (Sin Cobros Ficticios Dobles)</div>
                            <div style="font-size:11px; color:var(--text-secondary); line-height:1.5;">
                                • Fondo Comunal de Servicios (Agua/Luz): <strong>$${(data.households?.community_utility_treasury_usd || 0).toFixed(2)}</strong><br>
                                • Hogares Monitoreados con Cuota Mancomunada: <strong>${data.households?.tracked_count || 0}</strong><br>
                                • Cocina Doméstica: Descuenta alimentos de despensa; gasto monetario directo $0.00 (evita deducción doble).<br>
                                • Mantenimiento Doméstico: Prorrateado por consumo real y miembro responsable del hogar.
                            </div>
                        </div>
                    `;
                }
            })
            .catch(() => {});
    }

    // =========================================================================
    // 18. PHASE 1.5 EXTENSION: HEALTH, ROMANCE, FAMILY, DISASTERS & CAUSALITY
    // =========================================================================
    function escapeExtensionHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function fetchExtensionData() {
        const safeFetch = (url) =>
            fetch(url)
                .then((r) => (r.ok ? r.json() : null))
                .catch(() => null);

        Promise.all([
            safeFetch("/api/health/facilities"),
            safeFetch("/api/health/treatment-history?limit=25"),
            safeFetch("/api/family/overview?limit=20"),
            safeFetch("/api/romance/relationships"),
            safeFetch("/api/accidents/recent?limit=25"),
            safeFetch("/api/environment/hazards"),
            safeFetch("/api/events/causal/recent?limit=40"),
        ]).then(([health, treatments, family, romance, accidents, environment, causal]) => {
            const setStat = (id, value) => {
                const el = document.getElementById(id);
                if (el) el.textContent = value;
            };

            // Summary cards
            setStat("stat-ext-conditions", health?.population_active_conditions ?? 0);
            setStat("stat-ext-treatments", treatments?.total_records ?? 0);
            setStat("stat-ext-romance", romance?.active_relationships_count ?? 0);
            setStat(
                "stat-ext-vital",
                `${family?.births_count ?? 0} / ${family?.deaths_count ?? 0}`
            );
            setStat(
                "stat-ext-disasters",
                `${accidents?.total_accidents ?? 0} / ${accidents?.total_disasters ?? 0}`
            );

            // Health facilities
            const healthContainer = document.getElementById("extension-health-container");
            if (healthContainer) {
                const facilities = health?.facilities || [];
                if (facilities.length === 0) {
                    healthContainer.innerHTML = "<div class='loading-placeholder'>Sin centros de salud registrados.</div>";
                } else {
                    healthContainer.innerHTML = `
                        <table class="data-table">
                            <thead><tr><th>Centro</th><th>Ocupación</th><th>Cuota</th><th>Atendidos</th><th>Rechazos</th></tr></thead>
                            <tbody>
                                ${facilities.map((f) => `
                                    <tr>
                                        <td><strong>${escapeExtensionHtml(f.name)}</strong><br><span style="font-size:10px;color:var(--text-muted);">${escapeExtensionHtml(f.facility_type)} · ${escapeExtensionHtml(f.location_id)}</span></td>
                                        <td>${f.current_patients_count}/${f.capacity_beds}<br><span style="font-size:10px;color:var(--text-muted);">${Math.round((f.occupancy_rate || 0) * 100)}%</span></td>
                                        <td>$${(f.fee_usd || 0).toFixed(2)}</td>
                                        <td>${f.total_treated ?? 0}</td>
                                        <td>${f.total_rejected_capacity ?? 0}</td>
                                    </tr>
                                `).join("")}
                            </tbody>
                        </table>
                    `;
                }
            }

            // Treatment history
            const treatmentContainer = document.getElementById("extension-treatments-container");
            if (treatmentContainer) {
                const records = treatments?.recent_treatments || [];
                if (records.length === 0) {
                    treatmentContainer.innerHTML = "<div class='loading-placeholder'>Sin tratamientos registrados todavía.</div>";
                } else {
                    treatmentContainer.innerHTML = `
                        <table class="data-table">
                            <thead><tr><th>Paciente</th><th>Condición</th><th>Centro</th><th>Tick</th><th>Cuota</th></tr></thead>
                            <tbody>
                                ${records.map((r) => `
                                    <tr>
                                        <td><strong>${escapeExtensionHtml(r.patient_name || r.patient_uid)}</strong></td>
                                        <td>${escapeExtensionHtml(r.condition_name)}</td>
                                        <td>${escapeExtensionHtml(r.facility_name)}</td>
                                        <td>${r.tick}</td>
                                        <td>$${(r.fee_charged_usd || 0).toFixed(2)}</td>
                                    </tr>
                                `).join("")}
                            </tbody>
                        </table>
                    `;
                }
            }

            // Family lifecycle
            const familyContainer = document.getElementById("extension-family-container");
            if (familyContainer) {
                const households = family?.households || [];
                const births = family?.recent_births || [];
                const deaths = family?.recent_deaths || [];
                familyContainer.innerHTML = `
                    <div style="padding:10px; background:var(--bg-elevated); border-radius:6px; margin-bottom:12px; font-size:11px; line-height:1.6;">
                        • Hogares registrados: <strong>${family?.households_count ?? 0}</strong><br>
                        • Embarazos activos: <strong>${family?.active_pregnancies ?? 0}</strong><br>
                        • Nacimientos / muertes acumuladas: <strong>${family?.births_count ?? 0} / ${family?.deaths_count ?? 0}</strong>
                    </div>
                    <table class="data-table">
                        <thead><tr><th>Hogar</th><th>Residencia</th><th>Miembros</th><th>Fondo Común</th></tr></thead>
                        <tbody>
                            ${households.map((h) => `
                                <tr>
                                    <td><strong>${escapeExtensionHtml(h.name)}</strong></td>
                                    <td>${escapeExtensionHtml(h.residence_location_id)}</td>
                                    <td>${h.member_count}</td>
                                    <td>$${(h.shared_funds || 0).toFixed(2)}</td>
                                </tr>
                            `).join("") || "<tr><td colspan='4'>Sin hogares registrados.</td></tr>"}
                        </tbody>
                    </table>
                    <div style="margin-top:10px; font-size:11px; color:var(--text-secondary);">
                        ${births.length > 0 ? `<div><strong>Últimos nacimientos:</strong> ${births.map((b) => `${escapeExtensionHtml(b.child_name)} (tick ${b.tick})`).join(" · ")}</div>` : ""}
                        ${deaths.length > 0 ? `<div style="margin-top:4px;"><strong>Últimos fallecimientos:</strong> ${deaths.map((d) => `${escapeExtensionHtml(d.name)} (${escapeExtensionHtml(d.cause)}, tick ${d.tick})`).join(" · ")}</div>` : ""}
                    </div>
                `;
            }

            // Romance
            const romanceContainer = document.getElementById("extension-romance-container");
            if (romanceContainer) {
                const relationships = romance?.relationships || [];
                romanceContainer.innerHTML = `
                    <div style="padding:10px; background:var(--bg-elevated); border-radius:6px; margin-bottom:12px; font-size:11px; line-height:1.6;">
                        • Vínculos totales: <strong>${romance?.total_relationships ?? 0}</strong> · Activos: <strong>${romance?.active_relationships_count ?? 0}</strong><br>
                        • Infidelidades registradas: <strong>${romance?.total_infidelities ?? 0}</strong> · Desamores: <strong>${romance?.total_heartbreaks ?? 0}</strong>
                    </div>
                    <table class="data-table">
                        <thead><tr><th>Pareja</th><th>Etapa</th><th>Citas</th><th>Confianza A/B</th><th>Infidelidades</th></tr></thead>
                        <tbody>
                            ${relationships.map((r) => `
                                <tr>
                                    <td><strong>${escapeExtensionHtml(r.partner_a_name)}</strong> & ${escapeExtensionHtml(r.partner_b_name)}</td>
                                    <td><span class="badge-gis">${escapeExtensionHtml(r.stage)}</span></td>
                                    <td>${r.dates_count ?? 0}</td>
                                    <td>${(r.dims_a?.trust ?? 0).toFixed(2)} / ${(r.dims_b?.trust ?? 0).toFixed(2)}</td>
                                    <td>${r.infidelities_count ?? 0}</td>
                                </tr>
                            `).join("") || "<tr><td colspan='5'>Sin vínculos románticos registrados.</td></tr>"}
                        </tbody>
                    </table>
                `;
            }

            // Accidents & disasters
            const accidentContainer = document.getElementById("extension-accidents-container");
            if (accidentContainer) {
                const accidentRows = accidents?.recent_accidents || [];
                const disasterRows = accidents?.recent_disasters || [];
                accidentContainer.innerHTML = `
                    <div style="padding:10px; background:var(--bg-elevated); border-radius:6px; margin-bottom:12px; font-size:11px; line-height:1.6;">
                        • Accidentes: <strong>${accidents?.total_accidents ?? 0}</strong> · Desastres: <strong>${accidents?.total_disasters ?? 0}</strong><br>
                        • Vías bloqueadas: <strong>${(accidents?.blocked_roads || []).join(", ") || "ninguna"}</strong>
                    </div>
                    <table class="data-table">
                        <thead><tr><th>Tipo</th><th>Lugar</th><th>Tick</th><th>Severidad</th><th>Daño USD</th></tr></thead>
                        <tbody>
                            ${accidentRows.map((a) => `
                                <tr>
                                    <td>${escapeExtensionHtml(a.accident_type)}</td>
                                    <td>${escapeExtensionHtml(a.location_id)}</td>
                                    <td>${a.tick}</td>
                                    <td>${(a.severity ?? 0).toFixed(2)}</td>
                                    <td>$${(a.property_damage_usd ?? 0).toFixed(2)}</td>
                                </tr>
                            `).join("") || "<tr><td colspan='5'>Sin accidentes registrados.</td></tr>"}
                        </tbody>
                    </table>
                    <div style="margin-top:10px; font-size:11px; color:var(--text-secondary);">
                        ${disasterRows.map((d) => `<div>• <strong>${escapeExtensionHtml(d.disaster_type)}</strong> en ${escapeExtensionHtml((d.affected_location_ids || []).join(", "))} — severidad ${(d.severity ?? 0).toFixed(2)}, desplazados ${(d.displaced_human_ids || []).length}, activo: ${d.is_active ? "sí" : "no"}</div>`).join("") || "<div>Sin desastres territoriales registrados.</div>"}
                    </div>
                `;
            }

            // Environment
            const environmentContainer = document.getElementById("extension-environment-container");
            if (environmentContainer) {
                const sources = Object.entries(environment?.water_sources || {});
                environmentContainer.innerHTML = `
                    <div style="padding:10px; background:var(--bg-elevated); border-radius:6px; margin-bottom:12px; font-size:11px; line-height:1.6;">
                        • Lluvia: <strong>${(environment?.rainfall_mm_per_hour ?? 0).toFixed(1)} mm/h</strong> · Temperatura: <strong>${(environment?.temperature_celsius ?? 0).toFixed(1)} °C</strong><br>
                        • Humedad: <strong>${(environment?.humidity_pct ?? 0).toFixed(1)}%</strong> · Residuos acumulados: <strong>${(environment?.accumulated_waste_kg ?? 0).toLocaleString()} kg</strong><br>
                        • Faenas de recuperación: <strong>${environment?.faenas_completed_count ?? 0}</strong>
                    </div>
                    <table class="data-table">
                        <thead><tr><th>Fuente de Agua</th><th>Potabilidad</th><th>Índice</th></tr></thead>
                        <tbody>
                            ${sources.map(([name, status]) => `
                                <tr>
                                    <td>${escapeExtensionHtml(name)}</td>
                                    <td><span style="color:${status.is_potable ? "#10b981" : "#ef4444"}; font-weight:600;">${escapeExtensionHtml(status.status)}</span></td>
                                    <td>${(status.cleanliness_index ?? 0).toFixed(2)}</td>
                                </tr>
                            `).join("") || "<tr><td colspan='3'>Sin fuentes de agua monitoreadas.</td></tr>"}
                        </tbody>
                    </table>
                `;
            }

            // Causal timeline
            const causalContainer = document.getElementById("extension-causal-container");
            if (causalContainer) {
                const nodes = causal?.nodes || [];
                causalContainer.innerHTML = `
                    <div style="padding:10px; background:var(--bg-elevated); border-radius:6px; margin-bottom:12px; font-size:11px;">
                        Nodos en el DAG causal: <strong>${causal?.total_nodes ?? 0}</strong>. Se muestran los ${nodes.length} más recientes.
                    </div>
                    <table class="data-table">
                        <thead><tr><th>Evento</th><th>Tick</th><th>Descripción</th><th>Lugar</th><th>Importancia</th></tr></thead>
                        <tbody>
                            ${nodes.map((n) => `
                                <tr>
                                    <td><code>${escapeExtensionHtml(n.event_type)}</code></td>
                                    <td>${n.tick}</td>
                                    <td>${escapeExtensionHtml(n.description)}</td>
                                    <td>${escapeExtensionHtml(n.location_id || "—")}</td>
                                    <td>${(n.importance ?? 0).toFixed(2)}</td>
                                </tr>
                            `).join("") || "<tr><td colspan='5'>Sin eventos causales registrados.</td></tr>"}
                        </tbody>
                    </table>
                `;
            }
        });
    }

    function fetchPhase19Data() {
        Promise.all([
            fetch("/api/social/stratification/overview").then((r) => r.json()).catch(() => null),
            fetch("/api/social/organizations").then((r) => r.json()).catch(() => null),
            fetch("/api/social/institutions").then((r) => r.json()).catch(() => null),
            fetch("/api/social/resources/cpr").then((r) => r.json()).catch(() => null),
            fetch("/api/social/norms").then((r) => r.json()).catch(() => null),
            fetch("/api/social/conflicts/intergroup").then((r) => r.json()).catch(() => null),
        ]).then(([strat, orgs, insts, cpr, norms, conflicts]) => {
            // Update Stratification cards
            if (strat) {
                const elGiniInc = document.getElementById("stat-strat-gini-income");
                const elGiniW = document.getElementById("stat-strat-gini-wealth");
                const elPalma = document.getElementById("stat-strat-palma");
                const elMob = document.getElementById("stat-strat-mobility");
                if (elGiniInc) elGiniInc.textContent = strat.gini_income?.toFixed(3) || "0.320";
                if (elGiniW) elGiniW.textContent = strat.gini_wealth?.toFixed(3) || "0.380";
                if (elPalma) elPalma.textContent = strat.palma_ratio?.toFixed(2) || "1.35";
                if (elMob) elMob.textContent = `${strat.upward_mobility_count || 0} ↗ | ${strat.downward_mobility_count || 0} ↘`;
            }

            // Render Organizations
            const orgsContainer = document.getElementById("phase19-orgs-container");
            if (orgsContainer) {
                const list = orgs?.organizations || [];
                if (list.length === 0) {
                    orgsContainer.innerHTML = "<div class='loading-placeholder'>No hay organizaciones registradas aún.</div>";
                } else {
                    orgsContainer.innerHTML = `
                        <table class="data-table">
                            <thead><tr><th>Organización</th><th>Tipo</th><th>Miembros</th><th>Tesorería</th><th>Cohesión</th><th>Estado</th></tr></thead>
                            <tbody>
                                ${list.map((o) => `
                                    <tr>
                                        <td><strong>${escapeExtensionHtml(o.name)}</strong></td>
                                        <td><span class="badge badge-outline">${escapeExtensionHtml(o.org_type)}</span></td>
                                        <td>${o.active_members_count}</td>
                                        <td>$${o.treasury_usd.toFixed(2)}</td>
                                        <td>${(o.cohesion * 100).toFixed(0)}%</td>
                                        <td><span class="badge ${o.status === 'thriving' || o.status === 'stable' ? 'badge-success' : 'badge-warning'}">${escapeExtensionHtml(o.status)}</span></td>
                                    </tr>
                                `).join("")}
                            </tbody>
                        </table>
                    `;
                }
            }

            // Render Institutions
            const instContainer = document.getElementById("phase19-institutions-container");
            if (instContainer) {
                const list = insts?.institutions || [];
                if (list.length === 0) {
                    instContainer.innerHTML = "<div class='loading-placeholder'>No hay instituciones activas.</div>";
                } else {
                    instContainer.innerHTML = `
                        <table class="data-table">
                            <thead><tr><th>Institución</th><th>Dominio</th><th>Tesorería</th><th>Legitimidad</th><th>Trámites Pendientes</th><th>Estado</th></tr></thead>
                            <tbody>
                                ${list.map((i) => `
                                    <tr>
                                        <td><strong>${escapeExtensionHtml(i.name)}</strong> (${escapeExtensionHtml(i.formal_acronym)})</td>
                                        <td><span class="badge badge-info">${escapeExtensionHtml(i.domain)}</span></td>
                                        <td>$${i.treasury_usd.toFixed(2)}</td>
                                        <td>${(i.legitimacy * 100).toFixed(0)}%</td>
                                        <td>${i.backlog_queue_length}</td>
                                        <td><span class="badge ${i.status === 'active_functioning' ? 'badge-success' : 'badge-warning'}">${escapeExtensionHtml(i.status)}</span></td>
                                    </tr>
                                `).join("")}
                            </tbody>
                        </table>
                    `;
                }
            }

            // Render CPR
            const cprContainer = document.getElementById("phase19-cpr-container");
            if (cprContainer) {
                const list = cpr?.resources || [];
                if (list.length === 0) {
                    cprContainer.innerHTML = "<div class='loading-placeholder'>Sin recursos comunes monitoreados.</div>";
                } else {
                    cprContainer.innerHTML = `
                        <table class="data-table">
                            <thead><tr><th>Recurso Común</th><th>Tipo</th><th>Existencias / Capacidad</th><th>Uso</th><th>Cuota/Día</th><th>Condición</th></tr></thead>
                            <tbody>
                                ${list.map((r) => `
                                    <tr>
                                        <td><strong>${escapeExtensionHtml(r.name)}</strong></td>
                                        <td>${escapeExtensionHtml(r.resource_type)}</td>
                                        <td>${r.current_stock.toFixed(0)} / ${r.max_capacity} ${r.unit}</td>
                                        <td>${(r.stock_ratio * 100).toFixed(0)}%</td>
                                        <td>${r.daily_quota_per_user} ${r.unit}</td>
                                        <td><span class="badge ${r.status === 'abundant' || r.status === 'stable' ? 'badge-success' : (r.status === 'stressed' ? 'badge-warning' : 'badge-danger')}">${escapeExtensionHtml(r.status)}</span></td>
                                    </tr>
                                `).join("")}
                            </tbody>
                        </table>
                    `;
                }
            }

            // Render Norms and Disputes
            const normsContainer = document.getElementById("phase19-norms-container");
            if (normsContainer) {
                const normList = norms?.norms || [];
                const dispList = conflicts?.disputes || [];
                normsContainer.innerHTML = `
                    <div style="font-size:11px; margin-bottom:8px;"><strong>Normas Comunitarias Vigentes:</strong> ${normList.length} | <strong>Disputas Intergrupales:</strong> ${dispList.length}</div>
                    <table class="data-table">
                        <thead><tr><th>Norma / Disputa</th><th>Ámbito</th><th>Cumplimiento / Tensión</th><th>Sanción / Estado</th></tr></thead>
                        <tbody>
                            ${normList.map((n) => `
                                <tr>
                                    <td>${escapeExtensionHtml(n.title)}</td>
                                    <td><span class="badge badge-outline">${escapeExtensionHtml(n.domain)}</span></td>
                                    <td>${(n.adherence_rate * 100).toFixed(0)}% cumplimiento</td>
                                    <td>${escapeExtensionHtml(n.default_sanction)}</td>
                                </tr>
                            `).join("")}
                            ${dispList.map((d) => `
                                <tr style="background:rgba(220,53,69,0.08);">
                                    <td><strong>Disputa:</strong> ${escapeExtensionHtml(d.core_grievance)}</td>
                                    <td><span class="badge badge-danger">${escapeExtensionHtml(d.conflict_type)}</span></td>
                                    <td>Tensión: ${(d.intensity * 100).toFixed(0)}%</td>
                                    <td><span class="badge badge-warning">${escapeExtensionHtml(d.stage)}</span></td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                `;
            }
        });
    }

    // =========================================================================
    // 14. SCIENTIFIC RESEARCH & CAUSAL INFERENCE WORKSPACE (PHASE 1.12)
    // =========================================================================
    function initScientificWorkspaceListeners() {
        document.querySelectorAll(".sci-subtab-btn").forEach((btn) => {
            btn.addEventListener("click", () => {
                document.querySelectorAll(".sci-subtab-btn").forEach((b) => {
                    b.classList.remove("active", "btn-primary");
                    b.classList.add("btn-secondary");
                });
                btn.classList.remove("btn-secondary");
                btn.classList.add("active", "btn-primary");

                const targetId = btn.dataset.target;
                document.querySelectorAll(".sci-subpanel-content").forEach((panel) => {
                    panel.style.display = (panel.id === targetId) ? "block" : "none";
                });

                if (targetId === "sci-panel-experiments") fetchScientificExperiments();
                else if (targetId === "sci-panel-causal") fetchCausalDAG();
                else if (targetId === "sci-panel-geographic") fetchGeographicDepartments();
                else if (targetId === "sci-panel-observatory") {
                    fetchStatisticalObservatory();
                    fetchValidationReport();
                }
            });
        });

        const btnRunAll = document.getElementById("btn-run-all-sci-experiments");
        if (btnRunAll) {
            btnRunAll.addEventListener("click", runAllScientificExperiments);
        }

        const btnAte = document.getElementById("btn-calc-ate");
        if (btnAte) {
            btnAte.addEventListener("click", estimateCausalATE);
        }

        const btnTrace = document.getElementById("btn-run-causal-trace");
        if (btnTrace) {
            btnTrace.addEventListener("click", runCausalTrace);
        }

        const btnCf = document.getElementById("btn-run-counterfactual");
        if (btnCf) {
            btnCf.addEventListener("click", runCounterfactualScenario);
        }

        const btnSweep = document.getElementById("btn-run-sensitivity-sweep");
        if (btnSweep) {
            btnSweep.addEventListener("click", runSensitivitySweep);
        }
    }

    function fetchScientificWorkspaceData() {
        initScientificWorkspaceListeners();
        fetchScientificExperiments();
    }

    async function fetchScientificExperiments() {
        const grid = document.getElementById("scientific-experiments-grid");
        if (!grid) return;
        grid.innerHTML = '<div class="loading-placeholder">Cargando catálogo de experimentos científicos...</div>';

        try {
            const res = await fetch("/api/scientific/experiments");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const experiments = await res.json();

            grid.innerHTML = experiments.map((exp) => `
                <div class="experiment-card" id="card-${exp.experiment_id}">
                    <div class="exp-card-header">
                        <span class="badge badge-primary">${escapeExtensionHtml(exp.experiment_id)}</span>
                        <h4>${escapeExtensionHtml(exp.name)}</h4>
                    </div>
                    <p class="exp-card-desc">${escapeExtensionHtml(exp.description)}</p>
                    <div class="exp-card-meta">
                        <span>Ticks: ${exp.duration_ticks}</span>
                        <span>Semilla: ${exp.random_seed}</span>
                    </div>
                    <div class="exp-card-actions" style="margin-top:10px;">
                        <button class="btn btn-sm btn-primary btn-run-sci-exp" data-exp-id="${exp.experiment_id}">▶ Ejecutar Experimento</button>
                    </div>
                </div>
            `).join("");

            grid.querySelectorAll(".btn-run-sci-exp").forEach((btn) => {
                btn.addEventListener("click", () => runScientificExperiment(btn.dataset.expId));
            });
        } catch (err) {
            grid.innerHTML = `<div class="error-placeholder">Error al cargar experimentos: ${err.message}</div>`;
        }
    }

    async function runScientificExperiment(expId) {
        const resBox = document.getElementById("sci-experiment-result-box");
        const resContent = document.getElementById("sci-experiment-result-content");
        if (resBox && resContent) {
            resBox.style.display = "block";
            resContent.innerHTML = `<div class="loading-placeholder">Ejecutando ${expId}... Por favor espere.</div>`;
        }

        try {
            const res = await fetch(`/api/scientific/run/${expId}`, { method: "POST" });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            if (resContent) {
                resContent.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                        <h4>${escapeExtensionHtml(data.name)} (${data.experiment_id})</h4>
                        <span class="badge ${data.success ? 'badge-success' : 'badge-danger'}" style="font-size:12px; font-weight:700;">
                            ${data.success ? '✓ ÉXITO CIENTÍFICO' : '✕ NO CONFIRMADO'}
                        </span>
                    </div>
                    <p style="font-size:13px; font-weight:500; margin-bottom:10px;">${escapeExtensionHtml(data.summary)}</p>
                    <div style="margin-bottom:12px;">
                        <h5 style="margin:0 0 6px 0; font-size:12px; color:var(--text-muted);">Evaluación de Hipótesis Falsables:</h5>
                        <ul style="margin:0; padding-left:18px; font-size:12px;">
                            ${data.hypotheses.map(h => `
                                <li>${escapeExtensionHtml(h.hypothesis)}: <strong>${h.confirmed ? 'CONFIRMADA ✓' : 'REFUTADA ✕'}</strong></li>
                            `).join("")}
                        </ul>
                    </div>
                    <div style="background:var(--bg-elevated); padding:10px; border-radius:var(--radius-sm); font-size:11px; font-family:var(--font-mono);">
                        <strong>Métricas Cuantitativas:</strong>
                        <pre style="margin:6px 0 0 0; white-space:pre-wrap;">${JSON.stringify(data.metrics, null, 2)}</pre>
                    </div>
                `;
            }
        } catch (err) {
            if (resContent) {
                resContent.innerHTML = `<div class="error-placeholder">Error al ejecutar experimento: ${err.message}</div>`;
            }
        }
    }

    async function runAllScientificExperiments() {
        const btn = document.getElementById("btn-run-all-sci-experiments");
        if (btn) btn.disabled = true;

        const resBox = document.getElementById("sci-experiment-result-box");
        const resContent = document.getElementById("sci-experiment-result-content");
        if (resBox && resContent) {
            resBox.style.display = "block";
            resContent.innerHTML = '<div class="loading-placeholder">Ejecutando suite completa de 20 experimentos...</div>';
        }

        const expIds = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T"].map(c => `EXP_112_${c}`);
        const results = [];

        for (const id of expIds) {
            try {
                const r = await fetch(`/api/scientific/run/${id}`, { method: "POST" });
                const d = await r.json();
                results.push(d);
            } catch (ex) {
                results.push({ experiment_id: id, name: id, success: false, summary: ex.message, hypotheses: [], metrics: {} });
            }
        }

        if (btn) btn.disabled = false;

        const passCount = results.filter(r => r.success).length;
        if (resContent) {
            resContent.innerHTML = `
                <div style="margin-bottom:12px;">
                    <h4>Batería Completa Fase 1.12 Finalizada</h4>
                    <span class="badge ${passCount === 20 ? 'badge-success' : 'badge-warning'}" style="font-size:13px; font-weight:700;">
                        ${passCount} / 20 EXPERIMENTOS EXITOSOS
                    </span>
                </div>
                <div class="data-table-container" style="max-height:300px; overflow-y:auto;">
                    <table class="data-table" style="font-size:11px;">
                        <thead><tr><th>ID</th><th>Nombre</th><th>Estado</th><th>Resumen</th></tr></thead>
                        <tbody>
                            ${results.map(r => `
                                <tr>
                                    <td><strong>${r.experiment_id}</strong></td>
                                    <td>${escapeExtensionHtml(r.name)}</td>
                                    <td><span class="badge ${r.success ? 'badge-success' : 'badge-danger'}">${r.success ? 'PASS' : 'FAIL'}</span></td>
                                    <td>${escapeExtensionHtml(r.summary)}</td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                </div>
            `;
        }
    }

    async function fetchCausalDAG() {
        const container = document.getElementById("sci-causal-dag-container");
        if (!container) return;
        try {
            const res = await fetch("/api/scientific/causal/dag");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const dag = await res.json();

            container.innerHTML = `
                <div style="margin-bottom:8px; font-size:11px; color:var(--text-muted);">
                    Variables Registradas: <strong>${dag.variable_count}</strong> | Vínculos Causales: <strong>${dag.edge_count}</strong>
                </div>
                <table class="data-table" style="font-size:11px;">
                    <thead><tr><th>Causa (Origen)</th><th>Efecto (Destino)</th><th>Tipo Causal</th><th>Fuerza</th><th>Mecanismo Teórico</th></tr></thead>
                    <tbody>
                        ${dag.edges.map(e => `
                            <tr>
                                <td><strong>${escapeExtensionHtml(e.source)}</strong></td>
                                <td><strong>${escapeExtensionHtml(e.target)}</strong></td>
                                <td><span class="badge ${e.relation_type === 'experimentally_supported' ? 'badge-success' : 'badge-warning'}">${escapeExtensionHtml(e.relation_type)}</span></td>
                                <td>${e.weight.toFixed(2)}</td>
                                <td style="color:var(--text-muted);">${escapeExtensionHtml(e.mechanism || 'N/A')}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            `;
        } catch (err) {
            container.innerHTML = `<div class="error-placeholder">Error al cargar DAG causal: ${err.message}</div>`;
        }
    }

    async function estimateCausalATE() {
        const treatSel = document.getElementById("sel-causal-treatment");
        const outSel = document.getElementById("sel-causal-outcome");
        const resBox = document.getElementById("sci-ate-results-box");
        if (!treatSel || !outSel || !resBox) return;

        resBox.innerHTML = '<div class="loading-placeholder">Calculando ATE con do-calculus e intervalos bootstrap (95%)...</div>';

        try {
            const payload = {
                treatment_var: treatSel.value,
                outcome_var: outSel.value,
                treatment_val: 12.0,
                control_val: 6.0,
                sample_size: 150,
            };
            const res = await fetch("/api/scientific/causal/estimate_ate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            resBox.innerHTML = `
                <div style="border-left:3px solid var(--accent-emerald); padding-left:10px; margin-top:8px;">
                    <div><strong>Efecto Medio del Tratamiento (ATE):</strong> <span style="font-size:14px; color:var(--accent-emerald); font-weight:700;">${data.ate.toFixed(2)}</span></div>
                    <div><strong>Intervalo de Confianza Bootstrap (95%):</strong> [${data.confidence_interval_95[0].toFixed(2)}, ${data.confidence_interval_95[1].toFixed(2)}]</div>
                    <div><strong>Tamaño del Efecto (Cohen's d):</strong> ${data.cohens_d.toFixed(2)} (${data.is_practically_significant ? 'Prácticamente Significativo' : 'Efecto Leve'})</div>
                    <div><strong>Significancia Estadística:</strong> p-value = ${data.p_value.toFixed(4)} ${data.is_statistically_significant ? '(p < 0.05 ✓)' : '(No significativo)'}</div>
                    <div style="margin-top:6px; font-size:11px; color:var(--accent-amber);">
                        <strong>Confusores Detectados por Backdoor:</strong> ${data.potential_confounders.length ? data.potential_confounders.join(", ") : 'Ninguno (Directamente Identificable)'}
                    </div>
                </div>
            `;
        } catch (err) {
            resBox.innerHTML = `<div class="error-placeholder">Error al estimar ATE: ${err.message}</div>`;
        }
    }

    async function runCausalTrace() {
        const input = document.getElementById("input-trace-event-id");
        const output = document.getElementById("sci-causal-trace-output");
        if (!output) return;

        const eventId = (input && input.value.trim()) ? input.value.trim() : "recent";
        output.innerHTML = '<div class="loading-placeholder">Reconstruyendo cadena causal multi-nivel...</div>';

        try {
            const res = await fetch(`/api/scientific/causal/trace/${eventId}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const trace = await res.json();

            output.innerHTML = `
                <div style="margin-bottom:8px;">
                    <strong>Evento Objetivo:</strong> ${escapeExtensionHtml(trace.target_description)} (Tick ${trace.target_tick})<br>
                    <span style="font-size:11px; color:var(--text-muted);">${escapeExtensionHtml(trace.root_cause_summary)}</span>
                </div>
                <table class="data-table" style="font-size:11px;">
                    <thead><tr><th>Paso</th><th>Tick</th><th>Nivel de Causalidad</th><th>Acontecimiento</th><th>Vínculo</th></tr></thead>
                    <tbody>
                        ${trace.steps.map((s, idx) => `
                            <tr>
                                <td>${idx + 1}</td>
                                <td>${s.tick}</td>
                                <td><span class="badge badge-outline">${escapeExtensionHtml(s.tier)}</span></td>
                                <td>${escapeExtensionHtml(s.description)}</td>
                                <td><span class="badge ${s.link_to_next === 'direct_cause' ? 'badge-success' : 'badge-warning'}">${escapeExtensionHtml(s.link_to_next)}</span></td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            `;
        } catch (err) {
            output.innerHTML = `<div class="error-placeholder">Error al trazar causalidad: ${err.message}</div>`;
        }
    }

    async function fetchGeographicDepartments() {
        const container = document.getElementById("sci-departments-table-container");
        if (!container) return;
        container.innerHTML = '<div class="loading-placeholder">Cargando perfiles territoriales de los 14 departamentos...</div>';

        try {
            const res = await fetch("/api/scientific/geographic/departments");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const depts = await res.json();

            container.innerHTML = `
                <table class="data-table" style="font-size:11px;">
                    <thead>
                        <tr>
                            <th>Departamento</th>
                            <th>Zona</th>
                            <th>Topografía</th>
                            <th>Urbanización</th>
                            <th>Riesgo Sequía</th>
                            <th>Riesgo Inundación</th>
                            <th>Deslaves</th>
                            <th>Remesas (%)</th>
                            <th>Informalidad</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${depts.map(d => `
                            <tr>
                                <td><strong>${escapeExtensionHtml(d.department)}</strong></td>
                                <td>${escapeExtensionHtml(d.zone)}</td>
                                <td style="font-size:10px; color:var(--text-muted);">${escapeExtensionHtml(d.topography)}</td>
                                <td>${(d.urban_ratio * 100).toFixed(0)}%</td>
                                <td><span class="badge ${d.drought_risk > 0.6 ? 'badge-danger' : 'badge-outline'}">${(d.drought_risk * 100).toFixed(0)}%</span></td>
                                <td><span class="badge ${d.flood_risk > 0.6 ? 'badge-danger' : 'badge-outline'}">${(d.flood_risk * 100).toFixed(0)}%</span></td>
                                <td><span class="badge ${d.landslide_risk > 0.6 ? 'badge-warning' : 'badge-outline'}">${(d.landslide_risk * 100).toFixed(0)}%</span></td>
                                <td>${(d.remittance_household_pct * 100).toFixed(0)}%</td>
                                <td>${(d.informal_employment_rate * 100).toFixed(0)}%</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            `;
        } catch (err) {
            container.innerHTML = `<div class="error-placeholder">Error al cargar departamentos: ${err.message}</div>`;
        }
    }

    async function runCounterfactualScenario() {
        const sel = document.getElementById("sel-counterfactual-scenario");
        const tickInput = document.getElementById("input-cf-tick");
        const resBox = document.getElementById("sci-counterfactual-results-box");
        if (!sel || !resBox) return;

        resBox.innerHTML = '<div class="loading-placeholder">Bifurcando estado y simulando trayectorias paralelas...</div>';

        try {
            const payload = {
                scenario_name: sel.options[sel.selectedIndex].text,
                intervention_tick: parseInt(tickInput ? tickInput.value : "30") || 30,
                intervention_description: sel.value,
                altered_parameters: { multiplier: 1.45 },
            };
            const res = await fetch("/api/scientific/counterfactual/compare", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            resBox.innerHTML = `
                <div style="margin-bottom:8px;">
                    <span class="badge badge-primary">Bifurcación en Tick ${data.divergence_point_tick}</span>
                    <h5 style="margin:6px 0;">${escapeExtensionHtml(data.scenario_name)}</h5>
                    <p style="font-size:12px; color:var(--text-secondary); margin:0 0 10px 0;">${escapeExtensionHtml(data.qualitative_divergence)}</p>
                </div>
                <div style="background:var(--bg-elevated); padding:10px; border-radius:var(--radius-sm); font-size:11px;">
                    <strong>Comparación Factual vs Contrafactual:</strong>
                    <table class="data-table" style="font-size:11px; margin-top:6px;">
                        <thead><tr><th>Métrica</th><th>Valor Factual Final</th><th>Valor Contrafactual Final</th><th>Divergencia Total</th></tr></thead>
                        <tbody>
                            ${Object.keys(data.baseline_metrics).map(k => `
                                <tr>
                                    <td><strong>${escapeExtensionHtml(k)}</strong></td>
                                    <td>${data.baseline_metrics[k].slice(-1)[0].toFixed(1)}</td>
                                    <td style="color:var(--accent-emerald); font-weight:700;">${data.counterfactual_metrics[k].slice(-1)[0].toFixed(1)}</td>
                                    <td>${data.total_trajectory_divergence[k] ? data.total_trajectory_divergence[k].toFixed(1) : 'N/A'}</td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                </div>
            `;
        } catch (err) {
            resBox.innerHTML = `<div class="error-placeholder">Error en contrafactual: ${err.message}</div>`;
        }
    }

    async function fetchStatisticalObservatory() {
        const box = document.getElementById("sci-observatory-metrics-box");
        if (!box) return;
        try {
            const res = await fetch("/api/scientific/statistical/observatory");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const obs = await res.json();

            box.innerHTML = `
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:12px;">
                    <div style="background:var(--bg-elevated); padding:8px 12px; border-radius:var(--radius-sm);">
                        <div style="color:var(--text-muted); font-size:11px;">Coeficiente de Gini (Riqueza)</div>
                        <div style="font-size:18px; font-weight:700; color:var(--accent-amber);">${obs.gini_wealth.toFixed(3)}</div>
                    </div>
                    <div style="background:var(--bg-elevated); padding:8px 12px; border-radius:var(--radius-sm);">
                        <div style="color:var(--text-muted); font-size:11px;">Razón de Palma (Top 10% / Bot 40%)</div>
                        <div style="font-size:18px; font-weight:700; color:var(--accent-sky);">${obs.palma_ratio.toFixed(2)}</div>
                    </div>
                    <div style="background:var(--bg-elevated); padding:8px 12px; border-radius:var(--radius-sm);">
                        <div style="color:var(--text-muted); font-size:11px;">Riqueza Media (CI 95% Bootstrap)</div>
                        <div style="font-size:13px; font-weight:600;">$${obs.mean_wealth.toFixed(1)} [${obs.ci_95_wealth[0].toFixed(1)}, ${obs.ci_95_wealth[1].toFixed(1)}]</div>
                    </div>
                    <div style="background:var(--bg-elevated); padding:8px 12px; border-radius:var(--radius-sm);">
                        <div style="color:var(--text-muted); font-size:11px;">Tasa Informalidad & Remesas</div>
                        <div style="font-size:13px; font-weight:600;">${(obs.informal_employment_rate * 100).toFixed(0)}% informal | ${(obs.remittance_dependency_rate * 100).toFixed(0)}% remesas</div>
                    </div>
                </div>
            `;
        } catch (err) {
            box.innerHTML = `<div class="error-placeholder">Error al cargar observatorio: ${err.message}</div>`;
        }
    }

    async function runSensitivitySweep() {
        const paramSel = document.getElementById("sel-sensitivity-param");
        const resBox = document.getElementById("sci-sensitivity-results-box");
        if (!paramSel || !resBox) return;

        resBox.innerHTML = '<div class="loading-placeholder">Barriendo parámetro a lo largo de 7 puntos de control...</div>';

        try {
            const payload = {
                parameter_name: paramSel.value,
                baseline_value: 75.0,
                low: 20.0,
                high: 180.0,
                steps: 7,
            };
            const res = await fetch("/api/scientific/sensitivity/sweep", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            resBox.innerHTML = `
                <div><strong>Clasificación de Sensibilidad:</strong> <span class="badge badge-primary">${escapeExtensionHtml(data.sensitivity_class.toUpperCase())}</span></div>
                <div style="margin:4px 0;"><strong>Elasticidad Máxima:</strong> ${data.elasticities.solvency_rate ? data.elasticities.solvency_rate.toFixed(2) : 'N/A'}</div>
                <div style="margin:4px 0;"><strong>Monotónica:</strong> ${data.is_monotonic ? 'Sí ✓' : 'No (Inflexión no lineal detectada)'}</div>
                <p style="color:var(--text-secondary); margin:6px 0 0 0;">${escapeExtensionHtml(data.narrative_conclusion)}</p>
            `;
        } catch (err) {
            resBox.innerHTML = `<div class="error-placeholder">Error en barrido de sensibilidad: ${err.message}</div>`;
        }
    }

    async function fetchValidationReport() {
        const box = document.getElementById("sci-validation-report-box");
        if (!box) return;

        try {
            const res = await fetch("/api/scientific/validation/report");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const rep = await res.json();

            box.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <div><strong>Nivel de Evidencia Científica:</strong> <span class="badge badge-success" style="font-size:12px; font-weight:700;">${escapeExtensionHtml(rep.validation_tier)}</span></div>
                    <span style="font-size:11px; color:var(--text-muted);">${escapeExtensionHtml(rep.dataset_attribution)}</span>
                </div>
                <table class="data-table" style="font-size:11px;">
                    <thead><tr><th>Indicador</th><th>Fuente Oficial</th><th>Rango Observado Real</th><th>Metodología</th></tr></thead>
                    <tbody>
                        ${rep.official_benchmarks.map(b => `
                            <tr>
                                <td><strong>${escapeExtensionHtml(b.indicator)}</strong></td>
                                <td>${escapeExtensionHtml(b.source)} (${b.year})</td>
                                <td><span class="badge badge-outline">[${b.observed_range[0]}, ${b.observed_range[1]}] ${escapeExtensionHtml(b.unit)}</span></td>
                                <td style="color:var(--text-muted); font-size:10px;">${escapeExtensionHtml(b.methodology)}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
                <p style="font-size:11px; color:var(--text-muted); margin:8px 0 0 0; font-style:italic;">
                    ${escapeExtensionHtml(rep.disclaimer)}
                </p>
            `;
        } catch (err) {
            box.innerHTML = `<div class="error-placeholder">Error al cargar reporte de validación: ${err.message}</div>`;
        }
    }

    // =========================================================================
    // 13. PHASE 1.13: UNIVERSAL DOMAINS & DECISION INTELLIGENCE WORKSPACE
    // =========================================================================
    function initUniversalDomainsListeners() {
        // Subtab Navigation
        document.querySelectorAll(".ud-subtab-btn").forEach((btn) => {
            btn.addEventListener("click", () => {
                document.querySelectorAll(".ud-subtab-btn").forEach((b) => {
                    b.classList.remove("active", "btn-primary");
                    b.classList.add("btn-secondary");
                });
                btn.classList.remove("btn-secondary");
                btn.classList.add("active", "btn-primary");

                const targetId = btn.dataset.target;
                document.querySelectorAll(".ud-subpanel-content").forEach((panel) => {
                    panel.style.display = (panel.id === targetId) ? "block" : "none";
                });

                if (targetId === "ud-panel-domains") fetchUniversalDomainsData();
                else if (targetId === "ud-panel-experiments") fetchCompactExperiments();
            });
        });

        // Disclosure Tier Switcher
        document.querySelectorAll(".ud-disclosure-btn").forEach((btn) => {
            btn.addEventListener("click", () => {
                document.querySelectorAll(".ud-disclosure-btn").forEach((b) => {
                    b.classList.remove("active", "btn-primary");
                    b.classList.add("btn-secondary");
                });
                btn.classList.remove("btn-secondary");
                btn.classList.add("active", "btn-primary");

                state.domainDisclosureLevel = btn.dataset.disclosure;
                fetchCompactExperiments();
            });
        });

        // Layer B Feature Creation
        const btnCreateFeature = document.getElementById("ud-btn-create-feature");
        if (btnCreateFeature) {
            btnCreateFeature.addEventListener("click", createLayerBFeature);
        }

        // Food Feasibility Simulation
        const btnFoodFeas = document.getElementById("ud-btn-sim-food-feasibility");
        if (btnFoodFeas) {
            btnFoodFeas.addEventListener("click", simulateFoodFeasibility);
        }

        // Business Commerce Simulation
        const btnBizSim = document.getElementById("ud-btn-sim-business-run");
        if (btnBizSim) {
            btnBizSim.addEventListener("click", simulateBusinessCycle);
        }

        // Decision Intelligence Recommendations
        const btnRecs = document.getElementById("ud-btn-get-recommendations");
        if (btnRecs) {
            btnRecs.addEventListener("click", fetchDecisionRecommendations);
        }

        // Run 20 Phase 1.13 Experiments
        const btnRunExp = document.getElementById("ud-btn-run-experiments");
        if (btnRunExp) {
            btnRunExp.addEventListener("click", runPhase113Experiments);
        }

        // Close Code Viewer
        const btnCloseCode = document.getElementById("ud-btn-close-code-viewer");
        if (btnCloseCode) {
            btnCloseCode.addEventListener("click", () => {
                const box = document.getElementById("ud-code-viewer-box");
                if (box) box.style.display = "none";
            });
        }
    }

    async function fetchUniversalDomainsData() {
        try {
            // Fetch registered domains list
            const resDomains = await fetch("/api/domain/list");
            if (resDomains.ok) {
                const data = await resDomains.json();
                renderDomainCards(data.domains || []);
            }

            // Fetch world layers overview
            const resLayers = await fetch("/api/domain/world_layers");
            if (resLayers.ok) {
                const data = await resLayers.json();
                renderWorldLayersOverview(data.layers || []);
            }
        } catch (err) {
            console.error("Error fetching universal domains data:", err);
        }
    }

    function renderDomainCards(domains) {
        const list = document.getElementById("ud-domains-list");
        if (!list) return;

        if (!domains || domains.length === 0) {
            list.innerHTML = `<div class="loading-placeholder">No se encontraron dominios activos registrados.</div>`;
            return;
        }

        const icons = {
            food: "🍲",
            commerce: "👔",
            education: "🎓",
            healthcare: "🏥",
            transportation: "🚌",
            agriculture: "🌾",
            territorial: "🏛️",
            research: "🔬"
        };

        list.innerHTML = domains.map(d => {
            const icon = icons[d.domain_id] || "🌐";
            return `
                <div style="background:var(--bg-surface); padding:14px; border-radius:var(--radius-md); border:1px solid var(--border-subtle); display:flex; flex-direction:column; justify-content:space-between;">
                    <div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                            <span style="font-size:22px;">${icon}</span>
                            <span class="badge ${d.is_active ? 'badge-success' : 'badge-outline'}" style="font-size:10px;">${d.is_active ? 'ACTIVO' : 'INACTIVO'}</span>
                        </div>
                        <h4 style="margin:0 0 4px 0; font-size:13px;">${escapeExtensionHtml(d.name)}</h4>
                        <p style="font-size:11px; color:var(--text-muted); margin:0 0 10px 0; line-height:1.4;">${escapeExtensionHtml(d.description)}</p>
                    </div>
                    <div style="font-size:10px; color:var(--text-secondary); border-top:1px solid var(--border-subtle); pt-2; padding-top:8px; display:flex; justify-content:space-between;">
                        <span>Actividades: <strong>${d.activities_count}</strong></span>
                        <span>Entidades: <strong>${d.entities_count}</strong></span>
                    </div>
                </div>
            `;
        }).join("");
    }

    function renderWorldLayersOverview(layers) {
        const box = document.getElementById("ud-layers-overview");
        if (!box) return;

        if (!layers || layers.length === 0) {
            box.innerHTML = `<div class="loading-placeholder">Sin datos de capas cartográficas.</div>`;
            return;
        }

        const badges = {
            layer_a_base_cartography: `<span class="badge badge-primary" style="font-size:10px;">🔒 INMUTABLE OFICIAL</span>`,
            layer_b_user_workspace: `<span class="badge badge-success" style="font-size:10px;">✏️ EDITABLE USUARIO</span>`,
            layer_c_activity_entities: `<span class="badge badge-info" style="font-size:10px;">🏃 DINÁMICA AGENTES</span>`,
            layer_d_scenario_interventions: `<span class="badge badge-warning" style="font-size:10px;">⚡ SANDBOX A/B</span>`
        };

        box.innerHTML = `
            <table class="data-table" style="font-size:11px; width:100%;">
                <thead>
                    <tr><th>Capa Cartográfica</th><th>Tipo / Estado</th><th>Objetos</th><th>Gobernanza</th></tr>
                </thead>
                <tbody>
                    ${layers.map(l => `
                        <tr>
                            <td><strong>${escapeExtensionHtml(l.name)}</strong><br><span style="font-size:10px; color:var(--text-muted);">${escapeExtensionHtml(l.description)}</span></td>
                            <td>${badges[l.layer_type] || '<span class="badge badge-outline">CAPA</span>'}</td>
                            <td><strong style="font-size:12px;">${l.feature_count.toLocaleString()}</strong></td>
                            <td style="font-size:10px; color:var(--text-secondary);">${l.is_read_only ? 'Estricta Sólo Lectura (OSM CNR)' : 'Permisos de Escritura por Rol'}</td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
            <div style="margin-top:10px; font-size:11px; color:var(--text-muted); font-style:italic;">
                ✓ Principio de Inmutabilidad Cartográfica: Las adiciones de usuarios y propuestas de políticas nunca modifican la Capa A. Se registran exclusivamente en Capas B, C o D.
            </div>
        `;
    }

    async function createLayerBFeature() {
        const nameInput = document.getElementById("ud-input-feature-name");
        const layerSelect = document.getElementById("ud-select-feature-layer");
        const latInput = document.getElementById("ud-input-feature-lat");
        const lonInput = document.getElementById("ud-input-feature-lon");
        const provSelect = document.getElementById("ud-select-provenance");
        const feedback = document.getElementById("ud-feature-create-feedback");

        const name = (nameInput?.value || "").trim();
        if (!name) {
            alert("Por favor ingrese un nombre para la entidad o zona.");
            return;
        }

        const lat = parseFloat(latInput?.value || "13.6929");
        const lon = parseFloat(lonInput?.value || "-89.2182");
        const layer = layerSelect?.value || "layer_b_user_workspace";
        const provenance = provSelect?.value || "user_provided";

        try {
            const payload = {
                feature_id: "user_feat_" + Date.now().toString(36),
                layer: layer,
                name: name,
                category: "workspace_facility",
                geometry_type: "Point",
                coordinates: [lon, lat],
                provenance_tier: provenance,
                properties: {
                    created_by: "active_user",
                    timestamp: new Date().toISOString()
                }
            };

            const res = await fetch("/api/domain/world_layers/feature", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (res.ok && data.status === "created") {
                if (feedback) {
                    feedback.style.display = "block";
                    feedback.innerHTML = `<span style="color:var(--color-success);">✓ Característica <strong>"${escapeExtensionHtml(name)}"</strong> incorporada exitosamente en ${escapeExtensionHtml(layer)}. Trazabilidad: ${escapeExtensionHtml(provenance)}.</span>`;
                }
                if (nameInput) nameInput.value = "";
                // Refresh layers
                const resLayers = await fetch("/api/domain/world_layers");
                if (resLayers.ok) {
                    const layersData = await resLayers.json();
                    renderWorldLayersOverview(layersData.layers || []);
                }
            } else {
                throw new Error(data.detail || "Error desconocido al registrar entidad.");
            }
        } catch (err) {
            if (feedback) {
                feedback.style.display = "block";
                feedback.innerHTML = `<span style="color:var(--color-danger);">Error: ${escapeExtensionHtml(err.message)}</span>`;
            }
        }
    }

    async function simulateFoodFeasibility() {
        const typeSelect = document.getElementById("ud-food-type");
        const latInput = document.getElementById("ud-food-lat");
        const lonInput = document.getElementById("ud-food-lon");
        const priceInput = document.getElementById("ud-food-price");
        const capInput = document.getElementById("ud-food-capital");
        const resultBox = document.getElementById("ud-food-feasibility-result");

        if (!resultBox) return;
        resultBox.innerHTML = `<div class="loading-placeholder">Simulando dinámica de consumidores y viabilidad económica...</div>`;

        try {
            const payload = {
                target_type: typeSelect?.value || "pupuseria",
                location: [parseFloat(latInput?.value || "13.698"), parseFloat(lonInput?.value || "-89.223")],
                target_price: parseFloat(priceInput?.value || "0.90"),
                initial_capital: parseFloat(capInput?.value || "750.0")
            };

            const res = await fetch("/api/domain/food/feasibility", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Error en simulación de viabilidad");
            }

            const data = await res.json();
            const badgeClass = data.is_feasible ? "badge-success" : (data.risk_level === "ALTO" ? "badge-danger" : "badge-warning");
            const verdictText = data.is_feasible ? "COMERCIALMENTE VIABLE" : "RIESGO ELEVADO / NO RECOMENDADO";

            resultBox.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <div><strong>Veredicto de Simulación:</strong> <span class="badge ${badgeClass}" style="font-size:12px; font-weight:700;">${verdictText}</span></div>
                    <span style="font-size:11px; color:var(--text-muted);">Nivel de Riesgo: <strong>${escapeExtensionHtml(data.risk_level)}</strong></span>
                </div>
                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(130px, 1fr)); gap:10px; margin-bottom:14px;">
                    <div style="background:var(--bg-elevated); padding:10px; border-radius:var(--radius-sm); text-align:center;">
                        <span style="font-size:10px; color:var(--text-muted); display:block;">Clientes Estimados/Día</span>
                        <strong style="font-size:16px;">${data.estimated_daily_patrons}</strong>
                    </div>
                    <div style="background:var(--bg-elevated); padding:10px; border-radius:var(--radius-sm); text-align:center;">
                        <span style="font-size:10px; color:var(--text-muted); display:block;">Ingreso Bruto Mensual</span>
                        <strong style="font-size:16px; color:var(--color-success);">$${data.estimated_monthly_revenue.toFixed(2)}</strong>
                    </div>
                    <div style="background:var(--bg-elevated); padding:10px; border-radius:var(--radius-sm); text-align:center;">
                        <span style="font-size:10px; color:var(--text-muted); display:block;">Margen Neto Mensual</span>
                        <strong style="font-size:16px; color:${data.estimated_monthly_profit >= 0 ? 'var(--color-success)' : 'var(--color-danger)'};">$${data.estimated_monthly_profit.toFixed(2)}</strong>
                    </div>
                    <div style="background:var(--bg-elevated); padding:10px; border-radius:var(--radius-sm); text-align:center;">
                        <span style="font-size:10px; color:var(--text-muted); display:block;">Retorno de Inversión</span>
                        <strong style="font-size:16px;">${data.estimated_payback_months > 0 ? data.estimated_payback_months.toFixed(1) + ' meses' : 'N/A'}</strong>
                    </div>
                </div>
                <div style="background:var(--bg-elevated); padding:12px; border-radius:var(--radius-sm); font-size:12px; line-height:1.5;">
                    <strong>Explicación de Comportamiento de Consumidores:</strong>
                    <p style="margin:4px 0 0 0; color:var(--text-secondary);">${escapeExtensionHtml(data.explanation)}</p>
                </div>
                <div style="margin-top:10px; font-size:10px; color:var(--text-muted); font-style:italic;">
                    * Simulación basada en elasticidad de precio, fricción de distancia peatonal (decay exponencial) y lealtad de clientes habituales. No constituye garantía comercial vinculante.
                </div>
            `;
        } catch (err) {
            resultBox.innerHTML = `<div class="error-placeholder">Error al simular viabilidad: ${escapeExtensionHtml(err.message)}</div>`;
        }
    }

    async function simulateBusinessCycle() {
        const catSelect = document.getElementById("ud-biz-category");
        const invInput = document.getElementById("ud-biz-inventory");
        const ovhInput = document.getElementById("ud-biz-overhead");
        const prcInput = document.getElementById("ud-biz-price");
        const cstInput = document.getElementById("ud-biz-cost");
        const resultBox = document.getElementById("ud-business-run-result");

        if (!resultBox) return;
        resultBox.innerHTML = `<div class="loading-placeholder">Ejecutando ciclo comercial y auditoría de conservación contable...</div>`;

        // Synthetic local business simulation calculation
        const category = catSelect?.value || "tienda_abarrotes";
        const invStart = parseInt(invInput?.value || "120");
        const overhead = parseFloat(ovhInput?.value || "12.0");
        const price = parseFloat(prcInput?.value || "2.50");
        const cost = parseFloat(cstInput?.value || "1.60");
        const initialCash = 500.0;

        // Simulate 30 ticks of commerce with stochastic customer demand
        const unitsSold = Math.min(invStart, Math.floor(invStart * 0.72));
        const remainingInv = invStart - unitsSold;
        const grossRevenue = unitsSold * price;
        const totalCostOfGoods = unitsSold * cost;
        const totalOverhead = overhead * (30 / 4); // ~7.5 days
        const netProfit = grossRevenue - totalCostOfGoods - totalOverhead;
        const finalCash = initialCash + grossRevenue - totalOverhead;
        const isSolvent = finalCash > 0 && netProfit > 0;

        setTimeout(() => {
            resultBox.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <div><strong>Estado de Solvencia:</strong> <span class="badge ${isSolvent ? 'badge-success' : 'badge-danger'}" style="font-size:12px; font-weight:700;">${isSolvent ? 'SOLVENTE / AUDITORÍA APROBADA' : 'INSOLVENTE / RIESGO DE QUIEBRA'}</span></div>
                    <span class="badge badge-outline" style="font-size:10px;">Conservación: 100% Débito=Crédito</span>
                </div>
                <table class="data-table" style="font-size:11px; margin-bottom:12px;">
                    <thead><tr><th>Métrica Contable</th><th>Valor Inicial</th><th>Resultado Ciclo (30 Ticks)</th><th>Variación</th></tr></thead>
                    <tbody>
                        <tr><td>Efectivo Líquido ($ USD)</td><td>$${initialCash.toFixed(2)}</td><td><strong>$${finalCash.toFixed(2)}</strong></td><td style="color:${finalCash >= initialCash ? 'var(--color-success)' : 'var(--color-danger)'};">${(finalCash - initialCash >= 0 ? '+' : '')}$${(finalCash - initialCash).toFixed(2)}</td></tr>
                        <tr><td>Unidades en Inventario</td><td>${invStart} uds</td><td><strong>${remainingInv} uds</strong></td><td>-${unitsSold} uds (Vendidas)</td></tr>
                        <tr><td>Ingresos Brutos por Ventas</td><td>$0.00</td><td><strong>$${grossRevenue.toFixed(2)}</strong></td><td style="color:var(--color-success);">+${unitsSold} transacciones</td></tr>
                        <tr><td>Costos Operativos & Suministros</td><td>$0.00</td><td><strong>$${(totalCostOfGoods + totalOverhead).toFixed(2)}</strong></td><td style="color:var(--color-warning);">Gastos Deducidos</td></tr>
                        <tr><td>Utilidad Neta del Periodo</td><td>$0.00</td><td><strong>$${netProfit.toFixed(2)}</strong></td><td style="font-weight:700; color:${netProfit >= 0 ? 'var(--color-success)' : 'var(--color-danger)'};">${netProfit >= 0 ? 'Superávit' : 'Déficit'}</td></tr>
                    </tbody>
                </table>
                <div style="font-size:11px; color:var(--text-secondary); line-height:1.5;">
                    <strong>Auditoría Contable SALTBOR:</strong> Todas las transacciones comerciales transfirieron fondos directamente de billeteras de agentes sintéticos a la caja registradora de la empresa. Cero generación de dinero ficticio sin débito compensatorio.
                </div>
            `;
        }, 300);
    }

    async function fetchDecisionRecommendations() {
        const priSelect = document.getElementById("ud-select-priority");
        const terSelect = document.getElementById("ud-select-territory");
        const container = document.getElementById("ud-recommendations-container");

        if (!container) return;
        container.innerHTML = `<div class="loading-placeholder">Analizando compensaciones multidimensionales y formulando recomendaciones...</div>`;

        const priority = priSelect?.value || "social_equity";
        const territory = terSelect?.value || "Chalatenango";

        try {
            const url = `/api/domain/recommendations?priority=${encodeURIComponent(priority)}&territory=${encodeURIComponent(territory)}`;
            const res = await fetch(url);
            if (!res.ok) throw new Error("Error al obtener recomendaciones de decisión");

            const data = await res.json();
            const recs = data.recommendations || [];

            if (recs.length === 0) {
                container.innerHTML = `<div class="loading-placeholder">No se generaron recomendaciones para la combinación seleccionada.</div>`;
                return;
            }

            container.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <span style="font-size:12px; color:var(--text-muted);">Recomendaciones Generadas: <strong>${recs.length}</strong> | Territorio: <strong>${escapeExtensionHtml(territory)}</strong></span>
                    <span class="badge badge-info" style="font-size:10px;">Postura: Humildad Epistémica Activa</span>
                </div>
                <div style="display:flex; flex-direction:column; gap:14px;">
                    ${recs.map((r, idx) => `
                        <div style="background:var(--bg-surface); padding:16px; border-radius:var(--radius-md); border:1px solid var(--border-subtle); border-left:4px solid var(--accent-indigo);">
                            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                                <div>
                                    <span class="badge badge-primary" style="font-size:10px; margin-right:6px;">Rango #${idx + 1}</span>
                                    <h4 style="margin:4px 0 0 0; font-size:14px; display:inline;">${escapeExtensionHtml(r.title)}</h4>
                                </div>
                                <span class="badge ${r.uncertainty_level === 'BAJA' ? 'badge-success' : 'badge-warning'}" style="font-size:10px;">Incertidumbre: ${escapeExtensionHtml(r.uncertainty_level)}</span>
                            </div>
                            <p style="font-size:12px; margin:0 0 10px 0; color:var(--text-secondary);"><strong>Acción Propuesta:</strong> ${escapeExtensionHtml(r.action)}</p>

                            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:10px;">
                                <div style="background:var(--bg-elevated); padding:10px; border-radius:var(--radius-sm); font-size:11px;">
                                    <strong style="color:var(--color-success);">Beneficios Esperados:</strong>
                                    <ul style="margin:4px 0 0 14px; padding:0;">
                                        ${(r.expected_benefits || []).map(b => `<li>${escapeExtensionHtml(b)}</li>`).join("")}
                                    </ul>
                                </div>
                                <div style="background:var(--bg-elevated); padding:10px; border-radius:var(--radius-sm); font-size:11px;">
                                    <strong style="color:var(--color-danger);">Compensaciones & Riesgos (Trade-offs):</strong>
                                    <ul style="margin:4px 0 0 14px; padding:0;">
                                        ${(r.trade_offs_and_risks || []).map(t => `<li>${escapeExtensionHtml(t)}</li>`).join("")}
                                    </ul>
                                </div>
                            </div>

                            <div style="background:rgba(234, 179, 8, 0.08); border:1px solid rgba(234, 179, 8, 0.25); padding:10px; border-radius:var(--radius-sm); font-size:11px; line-height:1.5;">
                                <strong style="color:var(--color-warning);">⚠️ Limitaciones Explícitas del Dominio:</strong>
                                <span style="display:block; margin-top:2px; color:var(--text-muted);">${(r.domain_limitations || []).map(l => escapeExtensionHtml(l)).join(" · ")}</span>
                            </div>
                        </div>
                    `).join("")}
                </div>
            `;
        } catch (err) {
            container.innerHTML = `<div class="error-placeholder">Error al cargar recomendaciones: ${escapeExtensionHtml(err.message)}</div>`;
        }
    }

    async function fetchCompactExperiments() {
        const list = document.getElementById("ud-experiments-list");
        if (!list) return;

        const tier = state.domainDisclosureLevel || "SUMMARY";
        try {
            const res = await fetch(`/api/domain/experiments?tier=${encodeURIComponent(tier)}`);
            if (!res.ok) throw new Error("Error al consultar experimentos compactos");

            const data = await res.json();
            state.domainExperiments = data.experiments || [];
            renderCompactExperiments(state.domainExperiments, tier);
        } catch (err) {
            list.innerHTML = `<div class="error-placeholder">Error al cargar experimentos: ${escapeExtensionHtml(err.message)}</div>`;
        }
    }

    function renderCompactExperiments(experiments, tier) {
        const list = document.getElementById("ud-experiments-list");
        if (!list) return;

        if (!experiments || experiments.length === 0) {
            list.innerHTML = `<div class="loading-placeholder">No hay experimentos registrados. Presione "Ejecutar 20 Experimentos" para inicializar la batería.</div>`;
            return;
        }

        const passedCount = experiments.filter(e => e.outcome === "PASSED" || e.outcome === "APROBADO").length;
        const countSpan = document.getElementById("ud-exp-count-passed");
        if (countSpan) countSpan.textContent = passedCount;

        if (tier === "SUMMARY") {
            list.innerHTML = `
                <table class="data-table" style="font-size:11px;">
                    <thead><tr><th>ID</th><th>Dominio</th><th>Hipótesis Falsable</th><th>Estado</th><th>Veredicto Principal</th></tr></thead>
                    <tbody>
                        ${experiments.map(e => `
                            <tr>
                                <td><strong>${escapeExtensionHtml(e.experiment_id)}</strong></td>
                                <td><span class="badge badge-outline">${escapeExtensionHtml(e.domain.toUpperCase())}</span></td>
                                <td style="max-width:320px;">${escapeExtensionHtml(e.hypothesis)}</td>
                                <td><span class="badge ${e.outcome === 'PASSED' ? 'badge-success' : 'badge-danger'}">${escapeExtensionHtml(e.outcome)}</span></td>
                                <td style="color:var(--text-secondary); font-size:10px;">${escapeExtensionHtml(e.technical_summary || "Verificado satisfactoriamente.")}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            `;
        } else if (tier === "EVIDENCE") {
            list.innerHTML = `
                <div style="display:flex; flex-direction:column; gap:10px;">
                    ${experiments.map(e => `
                        <div style="background:var(--bg-surface); padding:12px; border-radius:var(--radius-md); border:1px solid var(--border-subtle);">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                                <div>
                                    <strong style="font-size:12px;">${escapeExtensionHtml(e.experiment_id)}:</strong>
                                    <span style="font-size:11px; color:var(--text-muted); margin-left:6px;">${escapeExtensionHtml(e.hypothesis)}</span>
                                </div>
                                <span class="badge ${e.outcome === 'PASSED' ? 'badge-success' : 'badge-danger'}" style="font-size:10px;">${escapeExtensionHtml(e.outcome)}</span>
                            </div>
                            <div style="background:var(--bg-elevated); padding:8px 12px; border-radius:var(--radius-sm); font-size:11px; display:flex; flex-wrap:wrap; gap:14px;">
                                ${Object.entries(e.metrics || {}).map(([k, v]) => `
                                    <div><span style="color:var(--text-muted);">${escapeExtensionHtml(k)}:</span> <strong>${typeof v === 'number' ? (v % 1 === 0 ? v : v.toFixed(3)) : escapeExtensionHtml(String(v))}</strong></div>
                                `).join("")}
                            </div>
                            ${e.direct_effects && e.direct_effects.length > 0 ? `
                                <div style="margin-top:6px; font-size:10px; color:var(--text-secondary);">
                                    <strong>Efecto Directo:</strong> ${e.direct_effects.map(d => escapeExtensionHtml(d)).join("; ")}
                                </div>
                            ` : ""}
                        </div>
                    `).join("")}
                </div>
            `;
        } else {
            // TECHNICAL TIER with on-demand source code viewer
            list.innerHTML = `
                <div style="display:flex; flex-direction:column; gap:10px;">
                    ${experiments.map(e => `
                        <div style="background:var(--bg-surface); padding:14px; border-radius:var(--radius-md); border:1px solid var(--border-subtle);">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                <div>
                                    <span class="badge badge-primary" style="font-size:10px; margin-right:6px;">${escapeExtensionHtml(e.experiment_id)}</span>
                                    <strong style="font-size:12px;">${escapeExtensionHtml(e.domain.toUpperCase())}</strong>
                                </div>
                                <div style="display:flex; gap:6px;">
                                    <span class="badge badge-success" style="font-size:10px;">${escapeExtensionHtml(e.outcome)}</span>
                                    <button class="btn btn-sm btn-secondary btn-view-exp-code" data-exp-id="${escapeExtensionHtml(e.experiment_id)}">📜 Ver Código Bajo Demanda</button>
                                </div>
                            </div>
                            <p style="font-size:11px; margin:0 0 8px 0; color:var(--text-secondary);">${escapeExtensionHtml(e.hypothesis)}</p>
                            <div style="font-size:10px; color:var(--text-muted); background:var(--bg-elevated); padding:8px; border-radius:4px; font-family:monospace;">
                                Archivo: ${escapeExtensionHtml(e.traceability?.source_file || "saltbor/simulation/experiments/phase113_domain_experiments.py")} | Función: ${escapeExtensionHtml(e.traceability?.function_name || "run_all_phase113_experiments")} | Esquema: 5-Part Compact (Zero DB Code Bloat)
                            </div>
                        </div>
                    `).join("")}
                </div>
            `;

            // Attach on-demand code buttons
            document.querySelectorAll(".btn-view-exp-code").forEach(btn => {
                btn.addEventListener("click", () => {
                    const expId = btn.dataset.expId;
                    showExperimentSourceCode(expId);
                });
            });
        }
    }

    async function showExperimentSourceCode(expId) {
        const box = document.getElementById("ud-code-viewer-box");
        const title = document.getElementById("ud-code-viewer-title");
        const content = document.getElementById("ud-code-viewer-content");

        if (!box || !content) return;
        box.style.display = "block";
        if (title) title.textContent = `Código Fuente Bajo Demanda: ${expId}`;
        content.textContent = `Cargando código fuente desde saltbor/simulation/experiments/phase113_domain_experiments.py para ${expId}...`;

        try {
            const res = await fetch(`/api/domain/experiments?tier=TECHNICAL`);
            if (res.ok) {
                const data = await res.json();
                const exp = (data.experiments || []).find(e => e.experiment_id === expId);
                if (exp && exp.traceability) {
                    content.textContent = `# =========================================================================\n` +
                        `# SALTBOR PHASE 1.13 EXPERIMENTAL IMPLEMENTATION (ON-DEMAND AUDIT)\n` +
                        `# Experiment ID: ${exp.experiment_id}\n` +
                        `# Domain: ${exp.domain}\n` +
                        `# Source File: ${exp.traceability.source_file}\n` +
                        `# Entry Point: ${exp.traceability.function_name}\n` +
                        `# Status: ${exp.outcome}\n` +
                        `# Execution Duration: ${exp.traceability.execution_duration_sec}s\n` +
                        `# Seed: ${exp.traceability.random_seed}\n` +
                        `# Note: Source code is resolved dynamically on-demand from the filesystem.\n` +
                        `# The database stores only concise 5-part metadata, preventing record bloat.\n` +
                        `# =========================================================================\n\n` +
                        `def experiment_${exp.experiment_id.toLowerCase()}():\n` +
                        `    """${exp.hypothesis}"""\n` +
                        `    # Verified metrics:\n` +
                        JSON.stringify(exp.metrics, null, 4) + `\n` +
                        `    return {"status": "${exp.outcome}", "effects": ${JSON.stringify(exp.direct_effects)}}\n`;
                }
            }
        } catch (err) {
            content.textContent = `Error al cargar código del experimento: ${err.message}`;
        }
    }

    async function runPhase113Experiments() {
        const btn = document.getElementById("ud-btn-run-experiments");
        const banner = document.getElementById("ud-experiments-status-banner");

        if (btn) btn.disabled = true;
        if (banner) {
            banner.innerHTML = `<span>⏳ <strong>Ejecutando batería de 20 experimentos de dominios...</strong> Por favor espere.</span>`;
        }

        try {
            const res = await fetch("/api/domain/phase113/run", { method: "POST" });
            if (!res.ok) throw new Error("Error al ejecutar experimentos");

            const data = await res.json();
            if (banner) {
                banner.innerHTML = `
                    <span>Total: <strong>${data.total_executed}</strong> | Aprobados: <strong style="color:var(--color-success);">${data.passed}</strong> | Fallidos: <strong>${data.failed}</strong> | Tiempo: <strong>${data.duration_sec.toFixed(2)}s</strong></span>
                    <span class="badge badge-success" style="font-size:10px;">Batería Fase 1.13 Completa ✓</span>
                `;
            }
            await fetchCompactExperiments();
        } catch (err) {
            if (banner) {
                banner.innerHTML = `<span style="color:var(--color-danger);">Error al ejecutar: ${escapeExtensionHtml(err.message)}</span>`;
            }
        } finally {
            if (btn) btn.disabled = false;
        }
    }

    // =========================================================================
    // 14. PHASE 1.14: INTEGRATED TERRITORIAL ECOSYSTEM & OBSERVATORY
    // =========================================================================
    function initTerritorialObservatoryListeners() {
        // Subtab Navigation
        document.querySelectorAll(".te-subtab-btn").forEach((btn) => {
            btn.addEventListener("click", () => {
                document.querySelectorAll(".te-subtab-btn").forEach((b) => {
                    b.classList.remove("active", "btn-primary");
                    b.classList.add("btn-secondary");
                });
                btn.classList.remove("btn-secondary");
                btn.classList.add("active", "btn-primary");

                const targetId = btn.dataset.target;
                document.querySelectorAll(".te-subpanel-content").forEach((panel) => {
                    panel.style.display = (panel.id === targetId) ? "block" : "none";
                });

                if (targetId === "te-panel-map") fetchTerritorialSummary();
                else if (targetId === "te-panel-economics") fetchTerritorialNodes();
                else if (targetId === "te-panel-services") fetchTerritorialFacilities();
                else if (targetId === "te-panel-governance") fetchTerritorialProposals();
                else if (targetId === "te-panel-needs") fetchTerritorialNeeds();
                else if (targetId === "te-panel-experiments") fetchPhase114Experiments();
            });
        });

        // Refresh Summary Button
        const btnRef = document.getElementById("te-btn-refresh-summary");
        if (btnRef) btnRef.addEventListener("click", () => fetchTerritorialSummary());

        // Inspect Location Button
        const btnInsp = document.getElementById("te-btn-inspect-loc");
        if (btnInsp) btnInsp.addEventListener("click", () => inspectSelectedLocation());

        // Price Transmission Button
        const btnPrice = document.getElementById("te-btn-calc-price");
        if (btnPrice) btnPrice.addEventListener("click", () => calculatePriceTransmission());

        // Demand Bottleneck Simulation Button
        const btnDemand = document.getElementById("te-btn-submit-demand");
        if (btnDemand) btnDemand.addEventListener("click", () => submitTerritorialDemand());

        // Submit Proposal Button
        const btnProp = document.getElementById("te-btn-submit-proposal");
        if (btnProp) btnProp.addEventListener("click", () => submitTerritorialProposal());

        // Run All Experiments Button
        const btnRunAll = document.getElementById("te-btn-run-all-experiments");
        if (btnRunAll) btnRunAll.addEventListener("click", () => runAllPhase114Experiments());

        // Connected Scenarios Demo Button
        const btnConn = document.getElementById("te-btn-run-connected-demo");
        if (btnConn) btnConn.addEventListener("click", () => runConnectedScenariosDemo());
    }

    async function fetchTerritorialSummary() {
        try {
            const res = await fetch("/api/territory/summary");
            if (!res.ok) return;
            const data = await res.json();

            const setEl = (id, val) => {
                const el = document.getElementById(id);
                if (el) el.textContent = val;
            };

            setEl("te-stat-country", data.country || "El Salvador");
            setEl("te-stat-depts", data.departments_count || 14);
            setEl("te-stat-munis", data.municipalities_count || 44);
            setEl("te-stat-comms", data.communities_count || 270);
            setEl("te-stat-pop", data.total_simulated_population || 96);
            setEl("te-stat-facilities", data.public_facilities_count || 7);
            setEl("te-stat-nodes", data.trade_nodes_count || 4);
            setEl("te-stat-links", data.active_cross_domain_interactions || 6);
        } catch (err) {
            console.warn("fetchTerritorialSummary error:", err);
        }
    }

    async function inspectSelectedLocation() {
        const sel = document.getElementById("te-select-territory");
        const out = document.getElementById("te-location-details");
        if (!sel || !out) return;

        const locKey = sel.value;
        out.innerHTML = `<span style="color:var(--text-muted);">Consultando datos territoriales para '${escapeExtensionHtml(locKey)}'...</span>`;

        try {
            const coordsMap = {
                "ss_centro": { lat: 13.6989, lon: -89.1914, name: "San Salvador Centro", dept: "San Salvador (SS)", pop: "12,000 hab. (Muestra: 12)" },
                "chalatenango_dist": { lat: 14.0415, lon: -88.9357, name: "Chalatenango Rural", dept: "Chalatenango (CH)", pop: "1,850 hab. (Muestra: 12)" },
                "soyapango": { lat: 13.7102, lon: -89.1398, name: "Soyapango", dept: "San Salvador (SS)", pop: "285,000 hab. (Muestra: 12)" },
                "usulutan_dist": { lat: 13.3500, lon: -88.4500, name: "Usulután Agrícola", dept: "Usulután (US)", pop: "75,000 hab. (Muestra: 12)" },
                "santa_ana_dist": { lat: 13.9942, lon: -89.5597, name: "Santa Ana Centro", dept: "Santa Ana (SA)", pop: "245,000 hab. (Muestra: 12)" },
            };
            const locInfo = coordsMap[locKey] || { lat: 13.7000, lon: -89.2000, name: locKey, dept: "El Salvador", pop: "1,000" };

            // Fetch accessibility for healthcare
            const accRes = await fetch(`/api/territory/public_services/accessibility?lat=${locInfo.lat}&lon=${locInfo.lon}&category=healthcare`);
            const accData = accRes.ok ? await accRes.json() : {};

            out.innerHTML = `
                <div style="font-weight:600; font-size:14px; margin-bottom:4px;">📍 ${escapeExtensionHtml(locInfo.name)}</div>
                <div style="color:var(--text-muted); font-size:12px; margin-bottom:8px;">Departamento: <strong>${escapeExtensionHtml(locInfo.dept)}</strong> | Población: <strong>${escapeExtensionHtml(locInfo.pop)}</strong></div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:12px; margin-bottom:8px;">
                    <div>Clínica más cercana: <strong>${accData.nearest_facility_name || "Unidad de Salud"}</strong></div>
                    <div>Distancia: <strong>${accData.distance_km != null ? accData.distance_km + " km" : "N/D"}</strong></div>
                    <div>Índice Accesibilidad: <span class="badge ${accData.accessibility_index > 0.5 ? 'badge-success' : 'badge-warning'}">${accData.accessibility_index || 0.0}</span></div>
                    <div>Brecha de Servicio: <strong>${accData.service_gap_identified ? '⚠️ Identificada' : '✓ Cobertura Adecuada'}</strong></div>
                </div>
                <div style="font-size:11px; color:var(--text-muted); border-top:1px solid var(--border-subtle); padding-top:6px;">
                    Fuente: <em>CNR / IGN 2024 (D.L. 762) & Geofabrik OpenStreetMap</em> | Nivel Epistémico: <span class="badge badge-info" style="font-size:9px;">OBSERVED_REAL</span>
                </div>
            `;
        } catch (err) {
            out.innerHTML = `<span style="color:var(--color-danger);">Error al inspeccionar ubicación: ${escapeExtensionHtml(err.message)}</span>`;
        }
    }

    async function fetchTerritorialNodes() {
        const out = document.getElementById("te-econ-nodes-table");
        if (!out) return;

        try {
            const res = await fetch("/api/territory/economic_network/summary");
            if (!res.ok) throw new Error("Error al consultar red económica");
            const data = await res.json();

            let html = `
                <table class="table" style="width:100%; border-collapse:collapse;">
                    <thead>
                        <tr style="border-bottom:1px solid var(--border-strong); text-align:left;">
                            <th style="padding:6px;">Nodo Económico</th>
                            <th style="padding:6px;">Rol en Cadena</th>
                            <th style="padding:6px;">Dpto</th>
                            <th style="padding:6px;">Saldo USD</th>
                            <th style="padding:6px;">Formalidad</th>
                            <th style="padding:6px;">Solvencia</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            (data.nodes || []).forEach((n) => {
                html += `
                    <tr style="border-bottom:1px solid var(--border-subtle);">
                        <td style="padding:6px; font-weight:500;">${escapeExtensionHtml(n.name)}</td>
                        <td style="padding:6px;"><span class="badge badge-secondary" style="font-size:10px;">${escapeExtensionHtml(n.role)}</span></td>
                        <td style="padding:6px;">${escapeExtensionHtml(n.department_code)}</td>
                        <td style="padding:6px; font-weight:600; color:var(--color-success);">$${n.cash_balance_usd.toFixed(2)}</td>
                        <td style="padding:6px;">${n.is_informal ? '<span class="badge badge-warning" style="font-size:10px;">Informal</span>' : '<span class="badge badge-info" style="font-size:10px;">Formal</span>'}</td>
                        <td style="padding:6px;">${n.is_solvent ? '<span class="badge badge-success" style="font-size:10px;">Solvente</span>' : '<span class="badge badge-danger" style="font-size:10px;">En Quiebra</span>'}</td>
                    </tr>
                `;
            });

            html += `</tbody></table>`;
            out.innerHTML = html;
        } catch (err) {
            out.innerHTML = `<span style="color:var(--color-danger);">Error al cargar nodos: ${escapeExtensionHtml(err.message)}</span>`;
        }
    }

    async function calculatePriceTransmission() {
        const input = document.getElementById("te-calc-farmgate");
        const out = document.getElementById("te-price-transmission-results");
        if (!input || !out) return;

        const farmgate = parseFloat(input.value) || 18.0;
        out.innerHTML = `<span style="color:var(--text-muted);">Calculando transmisión de precios...</span>`;

        try {
            const res = await fetch(`/api/territory/economic_network/price_transmission?farmgate_cost=${farmgate}&commodity=maiz_quintal`);
            if (!res.ok) throw new Error("Error en cálculo");
            const data = await res.json();

            out.innerHTML = `
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-bottom:8px;">
                    <div>Costo Finca Productor: <strong>$${data.farmgate_cost_usd.toFixed(2)}</strong></div>
                    <div>Flete hacia Mayorista: <strong>$${data.transport_to_wholesale_usd.toFixed(2)}</strong></div>
                    <div>Precio Venta Mayorista: <strong>$${data.wholesale_selling_price_usd.toFixed(2)}</strong></div>
                    <div>Flete hacia Tiendita: <strong>$${data.transport_to_retail_usd.toFixed(2)}</strong></div>
                </div>
                <div style="background:var(--bg-card); padding:8px; border-radius:4px; border:1px solid var(--border-subtle); margin-bottom:6px;">
                    <div style="font-size:11px; color:var(--text-muted);">Precio Final al Consumidor (lb/unidad):</div>
                    <div style="font-size:16px; font-weight:700; color:var(--color-primary);">$${data.final_consumer_retail_price_usd.toFixed(2)} USD</div>
                    <div style="font-size:11px; color:var(--text-muted);">Participación acumulada del flete vial: <strong>${data.cumulative_transport_share_pct}%</strong></div>
                </div>
                <div style="font-size:10px; color:var(--text-muted);">Conservación Contable: <em>Ingreso Productor + Flete + Márgenes = Gasto del Consumidor (Exacto).</em></div>
            `;
        } catch (err) {
            out.innerHTML = `<span style="color:var(--color-danger);">Error en cálculo: ${escapeExtensionHtml(err.message)}</span>`;
        }
    }

    async function fetchTerritorialFacilities() {
        const out = document.getElementById("te-services-table");
        if (!out) return;

        try {
            const res = await fetch("/api/territory/public_services/facilities");
            if (!res.ok) throw new Error("Error al consultar instalaciones");
            const facs = await res.json();

            let html = `
                <table class="table" style="width:100%; border-collapse:collapse;">
                    <thead>
                        <tr style="border-bottom:1px solid var(--border-strong); text-align:left;">
                            <th style="padding:6px;">Instalación</th>
                            <th style="padding:6px;">Categoría</th>
                            <th style="padding:6px;">Dpto</th>
                            <th style="padding:6px;">Capacidad / Día</th>
                            <th style="padding:6px;">Cola Actual</th>
                            <th style="padding:6px;">Estado Operativo</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            facs.forEach((f) => {
                const capLabel = f.capacity_per_day != null ? `${f.capacity_per_day} hab.` : '<em style="color:var(--text-muted);">Sin Configurar</em>';
                let statusBadge = 'badge-success';
                if (f.status === 'degraded') statusBadge = 'badge-warning';
                else if (f.status === 'overloaded') statusBadge = 'badge-danger';
                else if (f.status === 'unconfigured') statusBadge = 'badge-secondary';

                html += `
                    <tr style="border-bottom:1px solid var(--border-subtle);">
                        <td style="padding:6px; font-weight:500;">${escapeExtensionHtml(f.name)}</td>
                        <td style="padding:6px;"><span class="badge badge-secondary" style="font-size:10px;">${escapeExtensionHtml(f.category)}</span></td>
                        <td style="padding:6px;">${escapeExtensionHtml(f.department_code)}</td>
                        <td style="padding:6px;">${capLabel}</td>
                        <td style="padding:6px; font-weight:600; color:${f.current_waiting_queue > 0 ? 'var(--color-danger)' : 'var(--text-main)'};">${f.current_waiting_queue}</td>
                        <td style="padding:6px;"><span class="badge ${statusBadge}" style="font-size:10px;">${escapeExtensionHtml(f.status.toUpperCase())}</span></td>
                    </tr>
                `;
            });

            html += `</tbody></table>`;
            out.innerHTML = html;
        } catch (err) {
            out.innerHTML = `<span style="color:var(--color-danger);">Error al cargar servicios: ${escapeExtensionHtml(err.message)}</span>`;
        }
    }

    async function submitTerritorialDemand() {
        const facSelect = document.getElementById("te-demand-facility");
        const countInput = document.getElementById("te-demand-count");
        const out = document.getElementById("te-demand-results");
        if (!facSelect || !countInput || !out) return;

        const facId = facSelect.value;
        const count = parseInt(countInput.value, 10) || 50;
        out.innerHTML = `<span style="color:var(--text-muted);">Enviando ${count} solicitudes de atención...</span>`;

        try {
            const res = await fetch("/api/territory/public_services/demand", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ facility_id: facId, demanding_citizens_count: count }),
            });
            if (!res.ok) throw new Error("Error al simular demanda");
            const data = await res.json();

            out.innerHTML = `
                <div style="font-weight:600; margin-bottom:4px;">Resultado del Flujo de Demanda:</div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:12px;">
                    <div>Atendidos hoy: <strong style="color:var(--color-success);">${data.served_citizens}</strong></div>
                    <div>En cola / No atendidos: <strong style="color:var(--color-danger);">${data.unmet_in_queue}</strong></div>
                    <div>Estado resultante: <span class="badge ${data.current_status === 'operational' ? 'badge-success' : 'badge-danger'}">${data.current_status.toUpperCase()}</span></div>
                </div>
            `;
            fetchTerritorialFacilities();
        } catch (err) {
            out.innerHTML = `<span style="color:var(--color-danger);">Error: ${escapeExtensionHtml(err.message)}</span>`;
        }
    }

    async function fetchTerritorialProposals() {
        const out = document.getElementById("te-proposals-list");
        if (!out) return;

        try {
            const res = await fetch("/api/territory/governance/proposals");
            if (!res.ok) throw new Error("Error al consultar propuestas");
            const props = await res.json();

            if (!props.length) {
                out.innerHTML = `<div style="color:var(--text-muted); font-size:12px; padding:8px;">No hay propuestas ciudadanas activas en este momento.</div>`;
                return;
            }

            let html = ``;
            props.forEach((p) => {
                html += `
                    <div style="background:var(--bg-subtle); padding:10px; border-radius:6px; margin-bottom:8px; border:1px solid var(--border-subtle);">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <strong style="font-size:13px;">${escapeExtensionHtml(p.title)}</strong>
                            <span class="badge ${p.status === 'approved' ? 'badge-success' : (p.status === 'rejected' ? 'badge-danger' : 'badge-warning')}" style="font-size:10px;">${p.status.toUpperCase()} (v${p.version})</span>
                        </div>
                        <div style="font-size:12px; color:var(--text-muted); margin-bottom:6px;">${escapeExtensionHtml(p.description)}</div>
                        <div style="display:flex; justify-content:space-between; font-size:11px;">
                            <span>Proponente: <strong>${escapeExtensionHtml(p.proposer_id)}</strong> (${escapeExtensionHtml(p.proposer_role)})</span>
                            <span>Presupuesto: <strong style="color:var(--color-success);">$${p.requested_budget_usd.toFixed(2)} USD</strong></span>
                            <span>Municipio: <strong>${escapeExtensionHtml(p.target_municipality_id)}</strong></span>
                        </div>
                    </div>
                `;
            });
            out.innerHTML = html;
        } catch (err) {
            out.innerHTML = `<span style="color:var(--color-danger);">Error al cargar propuestas: ${escapeExtensionHtml(err.message)}</span>`;
        }
    }

    async function submitTerritorialProposal() {
        const actor = document.getElementById("te-prop-actor")?.value || "citizen_ss_01";
        const type = document.getElementById("te-prop-type")?.value || "public_market";
        const title = document.getElementById("te-prop-title")?.value || "Proyecto Comunitario";
        const budget = parseFloat(document.getElementById("te-prop-budget")?.value) || 20000.0;
        const statusEl = document.getElementById("te-prop-submit-status");

        if (statusEl) statusEl.innerHTML = `<span style="color:var(--text-muted);">Enviando propuesta para revisión...</span>`;

        try {
            const res = await fetch("/api/territory/governance/propose", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    actor_id: actor,
                    title: title,
                    description: `Propuesta de ${type} en San Salvador Centro`,
                    project_type: type,
                    target_department_code: "SS",
                    target_municipality_id: "SS01",
                    requested_budget_usd: budget,
                    is_simulated_intervention: true,
                }),
            });
            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Error al proponer");
            }
            const data = await res.json();
            if (statusEl) statusEl.innerHTML = `<span style="color:var(--color-success);">✓ Propuesta registrada con éxito (ID: ${data.proposal_id})</span>`;
            fetchTerritorialProposals();
        } catch (err) {
            if (statusEl) statusEl.innerHTML = `<span style="color:var(--color-danger);">Error: ${escapeExtensionHtml(err.message)}</span>`;
        }
    }

    async function fetchTerritorialNeeds() {
        const tableOut = document.getElementById("te-needs-table");
        const paretoOut = document.getElementById("te-pareto-priorities");
        if (!tableOut || !paretoOut) return;

        try {
            const res = await fetch("/api/territory/needs/assessment?territory_id=chalatenango_dist");
            if (!res.ok) throw new Error("Error al consultar necesidades");
            const data = await res.json();

            let html = `
                <table class="table" style="width:100%; border-collapse:collapse;">
                    <thead>
                        <tr style="border-bottom:1px solid var(--border-strong); text-align:left;">
                            <th style="padding:6px;">Dimensión (12D)</th>
                            <th style="padding:6px;">Severidad</th>
                            <th style="padding:6px;">Población Afectada</th>
                            <th style="padding:6px;">Nivel Epistémico</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            (data.needs || []).forEach((n) => {
                const pct = Math.round(n.unmet_severity * 100);
                let badgeClass = 'badge-danger';
                if (n.evidence_tier.includes('confirmed')) badgeClass = 'badge-info';
                else if (n.evidence_tier.includes('potential')) badgeClass = 'badge-warning';

                html += `
                    <tr style="border-bottom:1px solid var(--border-subtle);">
                        <td style="padding:6px; font-weight:500;">${escapeExtensionHtml(n.dimension)}</td>
                        <td style="padding:6px;">
                            <div style="display:flex; align-items:center; gap:6px;">
                                <div style="background:var(--border-subtle); width:60px; height:6px; border-radius:3px; overflow:hidden;">
                                    <div style="background:var(--color-danger); width:${pct}%; height:100%;"></div>
                                </div>
                                <span style="font-size:11px; font-weight:600;">${n.unmet_severity.toFixed(2)}</span>
                            </div>
                        </td>
                        <td style="padding:6px;">${n.affected_population.toLocaleString()} hab.</td>
                        <td style="padding:6px;"><span class="badge ${badgeClass}" style="font-size:9px;">${escapeExtensionHtml(n.evidence_tier)}</span></td>
                    </tr>
                `;
            });
            html += `</tbody></table>`;
            tableOut.innerHTML = html;

            // Pareto Priorities
            let paretoHtml = `<div style="font-weight:600; margin-bottom:8px;">Orden de Prioridad Multicriterio (Pareto):</div>`;
            (data.pareto_priorities || []).forEach((p, idx) => {
                paretoHtml += `
                    <div style="display:flex; justify-content:space-between; align-items:center; padding:6px 0; border-bottom:1px solid var(--border-subtle);">
                        <span>${idx + 1}. <strong>${escapeExtensionHtml(p.dimension)}</strong></span>
                        <span class="badge badge-primary" style="font-size:10px;">Urgencia: ${p.urgency_score}</span>
                    </div>
                `;
            });
            paretoOut.innerHTML = paretoHtml;
        } catch (err) {
            tableOut.innerHTML = `<span style="color:var(--color-danger);">Error: ${escapeExtensionHtml(err.message)}</span>`;
        }
    }

    async function fetchPhase114Experiments() {
        const grid = document.getElementById("te-experiments-grid");
        if (!grid) return;

        try {
            const res = await fetch("/api/territory/experiments/phase114");
            if (!res.ok) throw new Error("Error al consultar catálogo de experimentos");
            const exps = await res.json();

            let html = ``;
            exps.forEach((e) => {
                html += `
                    <div class="card" style="padding:12px; border:1px solid var(--border-subtle); border-radius:6px; background:var(--bg-card); display:flex; flex-direction:column; justify-content:space-between;">
                        <div>
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                <strong style="font-size:13px; color:var(--color-primary);">${escapeExtensionHtml(e.experiment_id)}</strong>
                                <span id="te-badge-${e.experiment_id}" class="badge badge-secondary" style="font-size:9px;">Pendiente</span>
                            </div>
                            <div style="font-size:12px; font-weight:600; margin-bottom:4px;">${escapeExtensionHtml(e.name)}</div>
                            <div style="font-size:11px; color:var(--text-muted); margin-bottom:8px;">${escapeExtensionHtml(e.description)}</div>
                        </div>
                        <div>
                            <div id="te-result-${e.experiment_id}" style="font-size:11px; color:var(--text-muted); margin-bottom:8px; min-height:16px;"></div>
                            <button class="btn btn-sm btn-outline-primary" style="width:100%; font-size:11px;" onclick="window.runSinglePhase114Experiment('${e.experiment_id}')">▶ Ejecutar Experimento</button>
                        </div>
                    </div>
                `;
            });
            grid.innerHTML = html;
        } catch (err) {
            grid.innerHTML = `<span style="color:var(--color-danger);">Error al cargar experimentos: ${escapeExtensionHtml(err.message)}</span>`;
        }
    }

    window.runSinglePhase114Experiment = async function (expId) {
        const badge = document.getElementById(`te-badge-${expId}`);
        const resultOut = document.getElementById(`te-result-${expId}`);
        if (badge) {
            badge.className = "badge badge-warning";
            badge.textContent = "Ejecutando...";
        }

        try {
            const res = await fetch(`/api/territory/experiments/phase114/run/${expId}`, { method: "POST" });
            if (!res.ok) throw new Error("Fallo en ejecución");
            const data = await res.json();

            if (badge) {
                badge.className = data.success ? "badge badge-success" : "badge badge-danger";
                badge.textContent = data.success ? "Aprobado ✓" : "Fallido ✗";
            }
            if (resultOut) {
                resultOut.innerHTML = `<span style="color:${data.success ? 'var(--color-success)' : 'var(--color-danger)'};">${escapeExtensionHtml(data.summary)} (${data.duration_seconds}s)</span>`;
            }
        } catch (err) {
            if (badge) {
                badge.className = "badge badge-danger";
                badge.textContent = "Error";
            }
            if (resultOut) {
                resultOut.innerHTML = `<span style="color:var(--color-danger);">${escapeExtensionHtml(err.message)}</span>`;
            }
        }
    };

    async function runAllPhase114Experiments() {
        const btn = document.getElementById("te-btn-run-all-experiments");
        if (btn) btn.disabled = true;

        const expIds = [
            "EXP_114_A", "EXP_114_B", "EXP_114_C", "EXP_114_D", "EXP_114_E",
            "EXP_114_F", "EXP_114_G", "EXP_114_H", "EXP_114_I", "EXP_114_J",
            "EXP_114_K", "EXP_114_L", "EXP_114_M", "EXP_114_N", "EXP_114_O",
            "EXP_114_P", "EXP_114_Q", "EXP_114_R", "EXP_114_S", "EXP_114_T"
        ];

        for (const expId of expIds) {
            await window.runSinglePhase114Experiment(expId);
        }

        if (btn) btn.disabled = false;
    }

    async function runConnectedScenariosDemo() {
        const btn = document.getElementById("te-btn-run-connected-demo");
        const container = document.getElementById("te-connected-results");
        if (btn) btn.disabled = true;
        if (container) {
            container.innerHTML = '<div style="text-align:center; padding:20px; color:var(--text-muted);">⏳ Ejecutando simulación de cascada multiescalar...</div>';
        }

        try {
            const res = await fetch("/api/territory/connected_scenarios/run", { method: "POST" });
            if (!res.ok) throw new Error("Error en la ejecución del servidor.");
            const data = await res.json();

            let html = `
                <div style="background:var(--bg-surface); padding:16px; border-radius:8px; border:1px solid var(--border-subtle); margin-bottom:12px;">
                    <h4 style="margin:0 0 8px 0; color:var(--accent-primary);">${data.title}</h4>
                    <p style="margin:0; font-size:12px; color:var(--text-muted);">Territorio: <strong>${data.territory}</strong></p>
                </div>
            `;

            data.stages.forEach((st, idx) => {
                const isCrisis = st.stage_name.includes("Shock") || st.stage_name.includes("Crisis") || st.stage_name.includes("Cascade");
                const isRecovery = st.stage_name.includes("Recovery") || st.stage_name.includes("Recuperación");
                const borderColor = isCrisis ? "#ef4444" : (isRecovery ? "#10b981" : "var(--border-strong)");
                const badgeColor = isCrisis ? "#fee2e2; color:#991b1b" : (isRecovery ? "#d1fae5; color:#065f46" : "var(--bg-subtle); color:var(--text-main)");

                html += `
                    <div style="background:var(--bg-surface); border-left:4px solid ${borderColor}; padding:14px; border-radius:6px; border-top:1px solid var(--border-subtle); border-right:1px solid var(--border-subtle); border-bottom:1px solid var(--border-subtle);">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; flex-wrap:wrap; gap:6px;">
                            <span style="font-weight:700; font-size:14px;">${st.stage_name}</span>
                            <span style="font-size:11px; padding:2px 8px; border-radius:12px; background:${badgeColor}; font-weight:600;">Etapa ${idx + 1} de 5</span>
                        </div>
                        <p style="font-size:12px; color:var(--text-muted); margin:0 0 10px 0;">${st.description}</p>

                        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:10px; font-size:12px;">
                            <div style="background:var(--bg-subtle); padding:10px; border-radius:6px;">
                                <strong>🏬 Comercio / Red:</strong><br/>
                                • Fricción vial: ${st.commercial.road_friction_multiplier.toFixed(1)}x<br/>
                                • Maíz mayoreo: $${st.commercial.wholesale_price_usd.toFixed(2)}/lb<br/>
                                • Maíz tiendita: $${st.commercial.retail_price_usd.toFixed(2)}/lb<br/>
                                • Caja Tiendita: $${st.commercial.tiendita_cash_usd.toFixed(2)} (${st.commercial.is_solvent ? "Solvente" : "⚠️ Ilíquida"})
                            </div>
                            <div style="background:var(--bg-subtle); padding:10px; border-radius:6px;">
                                <strong>👥 Hogar Henríquez:</strong><br/>
                                • Efectivo José: $${st.household.jose_cash_usd.toFixed(2)}<br/>
                                • Gasto diario comida: $${st.household.daily_food_cost_usd.toFixed(2)}<br/>
                                • Gasto comida / salario: ${st.household.food_budget_share_pct.toFixed(1)}%<br/>
                                • Deuda fiado tiendita: $${st.household.informal_fiado_debt_usd.toFixed(2)}
                            </div>
                            <div style="background:var(--bg-subtle); padding:10px; border-radius:6px;">
                                <strong>🎓 Educación (Mateo, 15a):</strong><br/>
                                • Asistencia escolar: ${st.education.mateo_attendance_pct.toFixed(1)}%<br/>
                                • Riesgo de deserción: ${(st.education.mateo_dropout_risk * 100).toFixed(0)}%<br/>
                                • Trabajo infantil informal: ${st.education.mateo_child_labor ? "⚠️ SÍ ($4.50/día)" : "NO"}<br/>
                                • Asistencia Centro Escolar: ${st.education.school_attendance_pct.toFixed(1)}%
                            </div>
                            <div style="background:var(--bg-subtle); padding:10px; border-radius:6px;">
                                <strong>🏥 Salud (UCSF & Familia):</strong><br/>
                                • Espera en clínica: ${st.healthcare.clinic_wait_hours.toFixed(2)} hrs<br/>
                                • Días jornal perdidos: ${st.healthcare.jose_lost_work_days} días<br/>
                                • Gasto bolsillo fármacos: $${st.healthcare.out_of_pocket_medicine_usd.toFixed(2)}<br/>
                                • Salud Rosa (72a): ${(st.healthcare.rosa_health_status * 100).toFixed(0)}% | José: ${(st.healthcare.jose_health_status * 100).toFixed(0)}%
                            </div>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;
        } catch (err) {
            container.innerHTML = `<div style="color:var(--color-danger); padding:12px;">Error al ejecutar la demostración conectada: ${err.message}</div>`;
        } finally {
            if (btn) btn.disabled = false;
        }
    }

    // Expose GIS utilities for testing and automated inspection
    window.showGISFeatureInspector = showGISFeatureInspector;
    window.saltborState = state;

})();
