import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from .models import ShipData, SimState, Vector
from .state import sim, manager 
from .routers import control 

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(run_simulation())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="collision system",
    description="Real-time maritime radar with collision detection.",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.include_router(control.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse('static/index.html')

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def run_simulation():
    while True:
        await asyncio.sleep(0.1)
        alerts = sim.step()
        
        ship_models = []
        for s in sim.ships:
            vx, vy = sim._get_vectors(s)
            ship_models.append(ShipData(
                id=s['id'], 
                position=Vector(x=s['x'], y=s['y']),
                velocity=Vector(x=vx, y=vy), 
                speed=s['speed'],
                heading=s['heading'], 
                is_own_ship=s['is_own']
            ))
        
        state = SimState(ships=ship_models, alerts=alerts, is_paused=sim.paused)
        
        if manager.active_connections:
            await manager.broadcast(state.model_dump())