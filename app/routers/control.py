import time
from fastapi import APIRouter
from app.state import sim  

router = APIRouter(prefix="/api/control", tags=["control"])

@router.post("/pause")
def toggle_pause():
    sim.paused = not sim.paused
    sim.last_update = time.time()
    return {"paused": sim.paused}

@router.post("/add")
def add_target():
    sim.add_target()
    return {"status": "added"}

@router.post("/remove/{id}")
def remove_target(id: str):
    sim.remove_target(id)
    return {"status": "removed"}

@router.post("/update/{id}")
def update_ship(id: str, speed: float, heading: float):
    sim.update_target(id, speed, heading)
    return {"status": "updated"}