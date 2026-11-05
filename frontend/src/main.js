import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import './style.css';

const API_URL = 'http://127.0.0.1:8000';
const WS_URL = 'ws://127.0.0.1:8000/ws/telemetry';

const DEVICE_CONFIG = {
    'TOWER-SENSOR-001': {
        name: 'Telecom Tower',
        type: 'Environmental Sensor',
        position: [-8, 9, 0],
        color: 0x38bdf8,
        icon: 'TWR'
    },
    'BACKHAUL-MONITOR-001': {
        name: 'Backhaul Link',
        type: 'Backhaul Monitor',
        position: [0, 3, -8],
        color: 0xa78bfa,
        icon: 'BHL'
    },
    'RAN-MONITOR-001': {
        name: 'Radio Access Network',
        type: 'RAN Performance Monitor',
        position: [8, 3, 0],
        color: 0x22d3ee,
        icon: 'RAN'
    },
    'POWER-MONITOR-001': {
        name: 'Power System',
        type: 'Power Monitor',
        position: [0, 3, 8],
        color: 0xfbbf24,
        icon: 'PWR'
    }
};

const state = {
    devices: {},
    websocket: null,
    connected: false,
    reconnectTimer: null
};

// --------------------------------------------------
// 1. DASHBOARD INTERFACE
// --------------------------------------------------

const app = document.querySelector('#app');

app.innerHTML = `
    <div class="dashboard">

        <header class="topbar">
            <div class="brand">
                <div class="brand-mark">TD</div>

                <div>
                    <h1>TELECOM DIGITAL TWIN</h1>
                    <p>VIRTUAL TELECOMMUNICATIONS ENGINEERING LABORATORY</p>
                </div>
            </div>

            <div class="header-right">
                <div class="site-indicator">
                    <span class="indicator-dot"></span>
                    SITE: TELECOM-SITE-001
                </div>

                <div id="connection-status" class="connection-status disconnected">
                    <span class="status-dot"></span>
                    CONNECTING
                </div>
            </div>
        </header>

        <main class="main-layout">

            <section class="topology-section">

                <div class="section-heading">
                    <div>
                        <span class="eyebrow">NETWORK VISUALIZATION</span>
                        <h2>3D Network Topology</h2>
                        <p>Live logical representation of the monitored telecom site</p>
                    </div>

                    <div class="topology-controls">
                        <span class="control-hint">DRAG TO ROTATE · SCROLL TO ZOOM</span>
                        <button id="reset-camera" class="reset-button">
                            RESET VIEW
                        </button>
                    </div>
                </div>

                <div id="topology-container">

                    <div class="topology-overlay">
                        <div class="overlay-label">SITE OVERVIEW</div>
                        <div class="overlay-value">TELECOM-SITE-001</div>
                        <div class="overlay-subtitle">SIMULATED INFRASTRUCTURE</div>
                    </div>

                    <div class="topology-legend">
                        <div><span class="legend-dot healthy"></span> HEALTHY</div>
                        <div><span class="legend-dot warning"></span> WARNING</div>
                        <div><span class="legend-dot critical"></span> CRITICAL</div>
                        <div><span class="legend-dot unknown"></span> UNKNOWN</div>
                    </div>

                </div>

                <div class="summary-strip">

                    <div class="summary-item">
                        <span class="summary-label">MONITORED DEVICES</span>
                        <strong id="device-count">0 / 4</strong>
                    </div>

                    <div class="summary-item">
                        <span class="summary-label">HEALTHY</span>
                        <strong id="healthy-count" class="healthy-text">0</strong>
                    </div>

                    <div class="summary-item">
                        <span class="summary-label">WARNING</span>
                        <strong id="warning-count" class="warning-text">0</strong>
                    </div>

                    <div class="summary-item">
                        <span class="summary-label">CRITICAL</span>
                        <strong id="critical-count" class="critical-text">0</strong>
                    </div>

                </div>

            </section>

            <aside class="telemetry-section">

                <div class="panel-heading">
                    <div>
                        <span class="eyebrow">REAL-TIME MONITORING</span>
                        <h2>Device Telemetry</h2>
                    </div>

                    <span class="live-tag">
                        <span class="live-dot"></span>
                        LIVE
                    </span>
                </div>

                <div id="device-list" class="device-list">

                    <div class="empty-state">
                        Waiting for telemetry from the backend...
                    </div>

                </div>

            </aside>

        </main>

        <footer class="footer">
            <div>
                TELECOM DIGITAL TWIN
                <span class="footer-separator">|</span>
                PHASE 4: LIVE VISUALIZATION
            </div>

            <div id="last-update">WAITING FOR FIRST TELEMETRY EVENT</div>
        </footer>

    </div>
`;

// --------------------------------------------------
// 2. THREE.JS SCENE
// --------------------------------------------------

const topologyContainer = document.querySelector('#topology-container');

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x07111f);
scene.fog = new THREE.Fog(0x07111f, 25, 65);

const camera = new THREE.PerspectiveCamera(
    48,
    topologyContainer.clientWidth / topologyContainer.clientHeight,
    0.1,
    200
);

camera.position.set(19, 16, 23);

const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: false
});

renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(
    topologyContainer.clientWidth,
    topologyContainer.clientHeight
);

renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;

topologyContainer.appendChild(renderer.domElement);

// CSS labels for topology nodes
const labelRenderer = new CSS2DRenderer();

labelRenderer.setSize(
    topologyContainer.clientWidth,
    topologyContainer.clientHeight
);

labelRenderer.domElement.className = 'label-renderer';

topologyContainer.appendChild(labelRenderer.domElement);

// --------------------------------------------------
// 3. CAMERA CONTROLS
// --------------------------------------------------

const controls = new OrbitControls(camera, renderer.domElement);

controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.minDistance = 10;
controls.maxDistance = 45;
controls.maxPolarAngle = Math.PI / 2.05;
controls.target.set(0, 3, 0);

// --------------------------------------------------
// 4. LIGHTING
// --------------------------------------------------

scene.add(new THREE.AmbientLight(0xffffff, 1.5));

const mainLight = new THREE.DirectionalLight(0xffffff, 2);
mainLight.position.set(10, 20, 10);
mainLight.castShadow = true;
scene.add(mainLight);

const blueLight = new THREE.PointLight(0x2563eb, 35, 35);
blueLight.position.set(-10, 8, -8);
scene.add(blueLight);

const cyanLight = new THREE.PointLight(0x0891b2, 30, 35);
cyanLight.position.set(10, 6, 10);
scene.add(cyanLight);

// --------------------------------------------------
// 5. GROUND AND GRID
// --------------------------------------------------

const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(100, 100),
    new THREE.MeshStandardMaterial({
        color: 0x0b1726,
        roughness: 0.9,
        metalness: 0.1
    })
);

ground.rotation.x = -Math.PI / 2;
ground.position.y = -0.1;
ground.receiveShadow = true;
scene.add(ground);

const grid = new THREE.GridHelper(50, 50, 0x1e4b70, 0x153047);
grid.position.y = 0.01;
scene.add(grid);

// --------------------------------------------------
// 6. CENTRAL TELECOM SITE NODE
// --------------------------------------------------

const coreGroup = new THREE.Group();
coreGroup.position.set(0, 3, 0);
scene.add(coreGroup);

const coreSphere = new THREE.Mesh(
    new THREE.IcosahedronGeometry(1.15, 2),
    new THREE.MeshStandardMaterial({
        color: 0x2563eb,
        emissive: 0x123b9a,
        emissiveIntensity: 1.5,
        metalness: 0.65,
        roughness: 0.25
    })
);

coreSphere.castShadow = true;
coreGroup.add(coreSphere);

const coreRing = new THREE.Mesh(
    new THREE.TorusGeometry(1.65, 0.045, 8, 80),
    new THREE.MeshBasicMaterial({
        color: 0x38bdf8
    })
);

coreRing.rotation.x = Math.PI / 2;
coreGroup.add(coreRing);

const coreLabel = document.createElement('div');
coreLabel.className = 'node-label core-label';
coreLabel.textContent = 'TELECOM SITE CORE';

const coreLabelObject = new CSS2DObject(coreLabel);
coreLabelObject.position.set(0, 2.1, 0);
coreGroup.add(coreLabelObject);

// --------------------------------------------------
// 7. TELECOM TOWER MODEL
// --------------------------------------------------

const towerGroup = new THREE.Group();
towerGroup.position.set(-8, 0, 0);
scene.add(towerGroup);

const metalMaterial = new THREE.MeshStandardMaterial({
    color: 0x94a3b8,
    metalness: 0.8,
    roughness: 0.3
});

const mast = new THREE.Mesh(
    new THREE.CylinderGeometry(0.12, 0.35, 8, 8),
    metalMaterial
);

mast.position.y = 4;
mast.castShadow = true;
towerGroup.add(mast);

for (let i = 0; i < 3; i++) {
    const antenna = new THREE.Mesh(
        new THREE.BoxGeometry(0.35, 1.7, 0.16),
        new THREE.MeshStandardMaterial({
            color: 0xe2e8f0,
            metalness: 0.5,
            roughness: 0.4
        })
    );

    const angle = (i * Math.PI * 2) / 3;

    antenna.position.set(
        Math.sin(angle) * 0.7,
        7.2,
        Math.cos(angle) * 0.7
    );

    antenna.rotation.y = angle;
    towerGroup.add(antenna);
}

const towerBase = new THREE.Mesh(
    new THREE.CylinderGeometry(0.6, 0.8, 0.5, 8),
    new THREE.MeshStandardMaterial({
        color: 0x334155,
        metalness: 0.5
    })
);

towerBase.position.y = 0.25;
towerGroup.add(towerBase);

// --------------------------------------------------
// 8. DEVICE NODES AND NETWORK LINKS
// --------------------------------------------------

const deviceNodes = {};
const linkObjects = {};

const deviceIds = Object.keys(DEVICE_CONFIG);

function createNodeLabel(id) {

    const config = DEVICE_CONFIG[id];

    const element = document.createElement('div');

    element.className = 'node-label';
    element.textContent = config.icon;

    return new CSS2DObject(element);
}

function createDeviceNode(id) {

    const config = DEVICE_CONFIG[id];

    const group = new THREE.Group();

    group.position.set(...config.position);

    const material = new THREE.MeshStandardMaterial({
        color: 0x64748b,
        emissive: 0x334155,
        emissiveIntensity: 1,
        metalness: 0.4,
        roughness: 0.3
    });

    const sphere = new THREE.Mesh(
        new THREE.SphereGeometry(0.65, 24, 24),
        material
    );

    sphere.castShadow = true;
    group.add(sphere);

    const ring = new THREE.Mesh(
        new THREE.TorusGeometry(1, 0.035, 8, 64),
        new THREE.MeshBasicMaterial({
            color: 0x64748b
        })
    );

    ring.rotation.x = Math.PI / 2;
    group.add(ring);

    const label = createNodeLabel(id);
    label.position.y = 1.3;
    group.add(label);

    scene.add(group);

    deviceNodes[id] = {
        group,
        sphere,
        ring,
        material
    };
}

function createNetworkLink(id) {

    const config = DEVICE_CONFIG[id];

    const start = new THREE.Vector3(0, 3, 0);
    const end = new THREE.Vector3(...config.position);

    const geometry = new THREE.BufferGeometry().setFromPoints([
        start,
        end
    ]);

    const material = new THREE.LineBasicMaterial({
        color: 0x2563eb,
        transparent: true,
        opacity: 0.75
    });

    const line = new THREE.Line(geometry, material);

    scene.add(line);

    linkObjects[id] = {
        line,
        material
    };
}

for (const id of deviceIds) {
    createDeviceNode(id);
    createNetworkLink(id);
}

// --------------------------------------------------
// 9. STATUS MANAGEMENT
// --------------------------------------------------

function getStatusColor(status) {

    switch ((status || 'UNKNOWN').toUpperCase()) {

        case 'HEALTHY':
            return 0x22c55e;

        case 'WARNING':
            return 0xf59e0b;

        case 'CRITICAL':
            return 0xef4444;

        default:
            return 0x64748b;
    }
}

function updateNodeStatus(id, status) {

    const node = deviceNodes[id];
    const link = linkObjects[id];

    if (!node || !link) return;

    const color = getStatusColor(status);

    node.material.color.setHex(color);
    node.material.emissive.setHex(color);

    node.ring.material.color.setHex(color);
    link.material.color.setHex(color);

    const intensity = status === 'HEALTHY' ? 1.3 : 1.8;

    node.material.emissiveIntensity = intensity;
}

// --------------------------------------------------
// 10. TELEMETRY DISPLAY
// --------------------------------------------------

function escapeHtml(value) {

    return String(value).replace(/[&<>"']/g, character => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    })[character]);
}

function formatMetric(value) {

    if (value && typeof value === 'object' && 'value' in value) {

        const number = value.value;
        const unit = value.unit || '';

        return `${number}${unit ? ` ${unit}` : ''}`;
    }

    if (typeof value === 'boolean') {
        return value ? 'YES' : 'NO';
    }

    return String(value);
}

function friendlyMetricName(key) {

    const names = {
        temperature: 'Temperature',
        latency: 'Latency',
        packet_loss: 'Packet Loss',
        throughput: 'Throughput',
        link_available: 'Link Available',
        signal_strength: 'Signal Strength',
        bandwidth_utilization: 'Bandwidth Utilization',
        congestion: 'Congestion',
        voltage: 'Voltage',
        battery_level: 'Battery Level',
        power_available: 'Power Available'
    };

    return names[key] || key.replaceAll('_', ' ');
}

function renderDeviceCards() {

    const deviceList = document.querySelector('#device-list');

    deviceList.innerHTML = '';

    for (const id of deviceIds) {

        const config = DEVICE_CONFIG[id];
        const event = state.devices[id];

        const status = event?.status || 'UNKNOWN';
        const telemetry = event?.telemetry || {};

        const metrics = Object.entries(telemetry);

        const metricMarkup = metrics.length
            ? metrics.map(([key, value]) => `
                <div class="metric">
                    <span>${escapeHtml(friendlyMetricName(key))}</span>
                    <strong>${escapeHtml(formatMetric(value))}</strong>
                </div>
            `).join('')
            : '<div class="no-metrics">Waiting for device readings...</div>';

        const card = document.createElement('article');

        card.className = 'device-card';

        card.innerHTML = `
            <div class="device-card-header">

                <div class="device-identity">
                    <div class="device-icon">${escapeHtml(config.icon)}</div>

                    <div>
                        <h3>${escapeHtml(config.name)}</h3>
                        <p>${escapeHtml(config.type)}</p>
                    </div>
                </div>

                <span class="device-status ${status.toLowerCase()}">
                    ${escapeHtml(status)}
                </span>

            </div>

            <div class="device-id">${escapeHtml(id)}</div>

            <div class="metrics-grid">
                ${metricMarkup}
            </div>
        `;

        deviceList.appendChild(card);

        updateNodeStatus(id, status);
    }

    updateSummary();
}

function updateSummary() {

    const events = Object.values(state.devices);

    const healthy = events.filter(
        event => event.status === 'HEALTHY'
    ).length;

    const warning = events.filter(
        event => event.status === 'WARNING'
    ).length;

    const critical = events.filter(
        event => event.status === 'CRITICAL'
    ).length;

    document.querySelector('#device-count').textContent =
        `${events.length} / 4`;

    document.querySelector('#healthy-count').textContent = healthy;
    document.querySelector('#warning-count').textContent = warning;
    document.querySelector('#critical-count').textContent = critical;
}

function updateTelemetry(event) {

    if (!event || !event.device_id) return;

    if (!DEVICE_CONFIG[event.device_id]) {
        console.warn('Unknown device received:', event.device_id);
        return;
    }

    state.devices[event.device_id] = event;

    renderDeviceCards();

    if (event.timestamp) {

        const date = new Date(event.timestamp);

        document.querySelector('#last-update').textContent =
            `LAST UPDATE: ${date.toLocaleTimeString()}`;
    }
}

// --------------------------------------------------
// 11. INITIAL TELEMETRY FROM REST API
// --------------------------------------------------

async function loadInitialTelemetry() {

    try {

        const response = await fetch(`${API_URL}/api/telemetry`);

        if (!response.ok) {
            throw new Error(`API returned HTTP ${response.status}`);
        }

        const result = await response.json();

        for (const event of Object.values(result.devices || {})) {
            updateTelemetry(event);
        }

        console.log('[API] Initial telemetry loaded.');

    } catch (error) {

        console.error('[API] Could not load initial telemetry:', error);
    }
}

// --------------------------------------------------
// 12. WEBSOCKET CONNECTION
// --------------------------------------------------

function setConnectionStatus(connected) {

    const element = document.querySelector('#connection-status');

    element.className = connected
        ? 'connection-status connected'
        : 'connection-status disconnected';

    element.innerHTML = `
        <span class="status-dot"></span>
        ${connected ? 'LIVE CONNECTION' : 'DISCONNECTED'}
    `;
}

function connectWebSocket() {

    console.log('[WEBSOCKET] Connecting to backend...');

    const ws = new WebSocket(WS_URL);

    state.websocket = ws;

    ws.onopen = () => {

        state.connected = true;

        setConnectionStatus(true);

        console.log('[WEBSOCKET] Live connection established.');
    };

    ws.onmessage = message => {

        try {

            const event = JSON.parse(message.data);

            updateTelemetry(event);

        } catch (error) {

            console.error('[WEBSOCKET] Invalid telemetry message:', error);
        }
    };

    ws.onerror = error => {

        console.error('[WEBSOCKET] Connection error:', error);
    };

    ws.onclose = () => {

        state.connected = false;

        setConnectionStatus(false);

        console.warn('[WEBSOCKET] Connection closed. Retrying in 3 seconds...');

        clearTimeout(state.reconnectTimer);

        state.reconnectTimer = setTimeout(() => {
            connectWebSocket();
        }, 3000);
    };
}

// --------------------------------------------------
// 13. CAMERA RESET
// --------------------------------------------------

document.querySelector('#reset-camera').addEventListener('click', () => {

    camera.position.set(19, 16, 23);

    controls.target.set(0, 3, 0);

    controls.update();
});

// --------------------------------------------------
// 14. ANIMATION LOOP
// --------------------------------------------------

const clock = new THREE.Clock();

function animate() {

    requestAnimationFrame(animate);

    const elapsed = clock.getElapsedTime();

    coreSphere.rotation.y += 0.003;
    coreRing.rotation.z += 0.004;

    for (const id of deviceIds) {

        const node = deviceNodes[id];

        if (!node) continue;

        node.sphere.rotation.y += 0.005;

        const pulse = 1 + Math.sin(elapsed * 2.5) * 0.035;

        node.ring.scale.set(pulse, pulse, pulse);
    }

    controls.update();

    renderer.render(scene, camera);
    labelRenderer.render(scene, camera);
}

animate();

// --------------------------------------------------
// 15. RESPONSIVE RESIZING
// --------------------------------------------------

window.addEventListener('resize', () => {

    const width = topologyContainer.clientWidth;
    const height = topologyContainer.clientHeight;

    camera.aspect = width / height;
    camera.updateProjectionMatrix();

    renderer.setSize(width, height);
    labelRenderer.setSize(width, height);
});

// --------------------------------------------------
// 16. START APPLICATION
// --------------------------------------------------

renderDeviceCards();
loadInitialTelemetry();
connectWebSocket();

console.log('[DIGITAL TWIN] Dashboard initialized.');