from pydantic import BaseModel
from typing import List, Optional

class Vector(BaseModel):
    x: float
    y: float

class ShipData(BaseModel):
    id: str
    position: Vector
    velocity: Vector
    speed: float
    heading: float
    is_own_ship: bool

class RiskAlert(BaseModel):
    target_id: str
    cpa: float
    tcpa: float
    level: str
    cpa_point: Vector

class SimState(BaseModel):
    ships: List[ShipData]
    alerts: List[RiskAlert]
    is_paused: bool