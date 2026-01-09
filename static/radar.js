const canvas = document.getElementById('radarCanvas');
const ctx = canvas.getContext('2d');
const container = document.querySelector('.radar-section');


let ships = [];
let alerts = [];
let selectedId = null;
let socket = null;


let view = { x: 0, y: 0, scale: 1.0 };
let cameraOffset = { x: 0, y: 0 };
let lastShipPos = { x: 0, y: 0 };
let scannerAngle = 0;


let isDragging = false;
let dragStart = { x: 0, y: 0 };
let lastMouse = { x: 0, y: 0 };
let hasMoved = false;


function init() {
    resize();
    window.addEventListener('resize', resize);


    connectWebSocket();


    requestAnimationFrame(renderLoop);
}

function resize() {
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${protocol}://${window.location.host}/ws`;

    console.log("Connecting to Radar Stream:", wsUrl);
    socket = new WebSocket(wsUrl);

    socket.onopen = () => console.log("Radar System: Online");

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        ships = data.ships;
        alerts = data.alerts;

        const btn = document.getElementById('btnPause');
        if (btn) btn.innerText = data.is_paused ? "RESUME" : "PAUSE";

        updateUI();
    };

    socket.onclose = () => {
        console.warn("Connection lost. Reconnecting in 1s...");
        setTimeout(connectWebSocket, 1000);
    };

    socket.onerror = (err) => console.error("WebSocket Error:", err);
}

function renderLoop() {
    render();
    requestAnimationFrame(renderLoop);
}


function render() {

    const ownShip = ships.find(s => s.id === 'OWN');


    if (ownShip) {
        lastShipPos = { x: ownShip.position.x, y: ownShip.position.y };
    }



    view.x = lastShipPos.x + cameraOffset.x;
    view.y = lastShipPos.y + cameraOffset.y;


    ctx.fillStyle = '#0f1215';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const cx = canvas.width / 2;
    const cy = canvas.height / 2;

    ctx.save();


    ctx.translate(cx, cy);
    ctx.scale(view.scale, view.scale);
    ctx.translate(-view.x, -view.y);



    drawGrid(lastShipPos);
    drawScanner(lastShipPos);


    alerts.forEach(drawCPAMarker);

    ships.forEach(ship => {
        const alert = alerts.find(a => a.target_id === ship.id);
        const risk = alert ? alert.level : 'SAFE';
        drawShip(ship, risk);
    });

    ctx.restore();


    scannerAngle += 0.03;
}



function drawGrid(center) {
    ctx.strokeStyle = '#003300';
    ctx.lineWidth = 1 / view.scale;

    const cx = center.x;
    const cy = center.y;


    [100, 200, 300, 400, 500].forEach(r => {
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.stroke();
    });


    const big = 50000;

    ctx.beginPath();
    ctx.moveTo(cx - big, cy); ctx.lineTo(cx + big, cy);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(cx, cy - big); ctx.lineTo(cx, cy + big);
    ctx.stroke();
}

function drawScanner(center) {
    const length = 1000;

    ctx.save();
    ctx.translate(center.x, center.y);
    ctx.rotate(scannerAngle);


    const grad = ctx.createLinearGradient(0, 0, length, 0);
    grad.addColorStop(0, 'rgba(0, 255, 65, 0)');
    grad.addColorStop(1, 'rgba(0, 255, 65, 0.15)');

    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.arc(0, 0, length, -0.3, 0);
    ctx.fill();


    ctx.strokeStyle = '#00ff41';
    ctx.lineWidth = 2 / view.scale;
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(length, 0);
    ctx.stroke();

    ctx.restore();
}

function drawShip(s, risk) {
    let color = '#00ff41';
    if (risk === 'WARNING') color = '#ffcc00';
    if (risk === 'DANGER') color = '#ff3333';
    if (s.id === 'OWN') color = '#00ff41';
    if (s.id === selectedId) color = '#ffffff';

    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(s.position.x, s.position.y, 6 / view.scale, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = color;
    ctx.lineWidth = 2 / view.scale;
    ctx.beginPath();
    ctx.moveTo(s.position.x, s.position.y);
    ctx.lineTo(s.position.x + s.velocity.x * 4, s.position.y + s.velocity.y * 4);
    ctx.stroke();

    if (risk !== 'SAFE' || s.id === 'OWN' || s.id === selectedId) {
        ctx.fillStyle = color;
        ctx.font = `bold ${14 / view.scale}px "Courier New"`;
        ctx.fillText(s.id, s.position.x + 12 / view.scale, s.position.y + 4 / view.scale);
    }
}

function drawCPAMarker(alert) {
    const s = ships.find(x => x.id === alert.target_id);
    if (!s) return;

    const x = alert.cpa_point.x;
    const y = alert.cpa_point.y;

    ctx.strokeStyle = '#ff3333';
    ctx.setLineDash([6 / view.scale, 4 / view.scale]);
    ctx.lineWidth = 2 / view.scale;
    ctx.beginPath();
    ctx.moveTo(s.position.x, s.position.y);
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.setLineDash([]);

    const size = 8 / view.scale;
    ctx.beginPath();
    ctx.moveTo(x - size, y - size); ctx.lineTo(x + size, y + size);
    ctx.moveTo(x + size, y - size); ctx.lineTo(x - size, y + size);
    ctx.stroke();

    ctx.fillStyle = '#ff3333';
    ctx.font = `bold ${12 / view.scale}px "Courier New"`;
    ctx.fillText("CPA", x + 10 / view.scale, y);
}




canvas.addEventListener('mousedown', e => {
    isDragging = true;
    hasMoved = false;
    dragStart = { x: e.clientX, y: e.clientY };
    lastMouse = { x: e.clientX, y: e.clientY };
});


canvas.addEventListener('mousemove', e => {
    if (isDragging) {
        const dx = e.clientX - lastMouse.x;
        const dy = e.clientY - lastMouse.y;



        cameraOffset.x -= dx / view.scale;
        cameraOffset.y -= dy / view.scale;

        if (Math.abs(e.clientX - dragStart.x) > 5 || Math.abs(e.clientY - dragStart.y) > 5) {
            hasMoved = true;
        }

        lastMouse = { x: e.clientX, y: e.clientY };
    }
});


canvas.addEventListener('mouseup', e => {
    isDragging = false;
    if (!hasMoved) handleCanvasClick(e);
});


canvas.addEventListener('wheel', e => {
    e.preventDefault();
    const factor = e.deltaY > 0 ? 0.9 : 1.1;
    const newScale = view.scale * factor;
    if (newScale > 0.05 && newScale < 10) view.scale = newScale;
});


function screenToWorld(sx, sy) {
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    return {
        x: (sx - cx) / view.scale + view.x,
        y: (sy - cy) / view.scale + view.y
    };
}

function handleCanvasClick(e) {
    const rect = canvas.getBoundingClientRect();
    const world = screenToWorld(e.clientX - rect.left, e.clientY - rect.top);
    const hitRadius = 20 / view.scale;

    const hit = ships.find(s => Math.hypot(s.position.x - world.x, s.position.y - world.y) < hitRadius);

    if (hit) selectTarget(hit);
    else closeEdit();
}



function selectTarget(s) {
    selectedId = s.id;
    document.getElementById('target-editor').classList.remove('hidden');
    document.getElementById('edit-id').innerText = s.id;
    document.getElementById('edit-spd').value = Math.round(s.speed || 0);
    document.getElementById('edit-hdg').value = Math.round(s.heading || 0);
    document.getElementById('no-selection').classList.add('hidden');
}

function updateUI() {

    const box = document.getElementById('alert-box');
    if (alerts.length === 0) box.innerHTML = '<div class="no-alerts" style="color:#666">SECTOR CLEAR</div>';
    else {
        box.innerHTML = alerts.map(a => `
            <div class="alert ${a.level.toLowerCase()}">
                <strong>${a.target_id}</strong>: ${a.level}<br>
                TCPA: ${a.tcpa}s | CPA: ${a.cpa}px
            </div>
        `).join('');
    }


    const list = document.getElementById('ship-list');
    const targets = ships.filter(s => !s.is_own_ship);

    list.innerHTML = targets.map(s => {
        const isSel = s.id === selectedId ? 'background:#222; border-left: 2px solid #fff;' : '';
        return `
        <div class="list-item" style="${isSel}" onclick="selectTarget({id:'${s.id}'})">
            <span class="ship-id">${s.id}</span>
            <span class="ship-data">${Math.round(s.speed)}kts / ${Math.round(s.heading)}°</span>
        </div>`;
    }).join('');
}




function resetView() {
    cameraOffset = { x: 0, y: 0 };
    view.scale = 1.0;

}


function pan(d) {
    const s = 50 / view.scale;
    if (d == 'N') cameraOffset.y -= s;
    if (d == 'S') cameraOffset.y += s;
    if (d == 'W') cameraOffset.x -= s;
    if (d == 'E') cameraOffset.x += s;
}

function zoom(f) { view.scale *= f; }


async function togglePause() { await fetch('/api/control/pause', { method: 'POST' }); }
async function addTarget() { await fetch('/api/control/add', { method: 'POST' }); }
async function deleteTarget() {
    if (selectedId) await fetch(`/api/control/remove/${selectedId}`, { method: 'POST' });
    closeEdit();
}
async function applyEdit() {
    if (!selectedId) return;
    const s = document.getElementById('edit-spd').value;
    const h = document.getElementById('edit-hdg').value;
    await fetch(`/api/control/update/${selectedId}?speed=${s}&heading=${h}`, { method: 'POST' });
}
function closeEdit() {
    selectedId = null;
    document.getElementById('target-editor').classList.add('hidden');
    document.getElementById('no-selection').classList.remove('hidden');
}


init();