import math
import time
import random
import traceback
from typing import List, Optional, Dict
from .models import RiskAlert, Vector

class Simulation:
    def __init__(self):
        self.ships: List[Dict] = []
        self.paused = False
        self.last_update = time.time()
        self.ship_count = 0
        self.world_limit = 1500  
        self.reset_scenario()

    def reset_scenario(self):
        self.ships = [{
            "id": "OWN", "x": 0.0, "y": 0.0, 
            "speed": 15.0, "heading": 45.0, "is_own": True
        }]
        for _ in range(8): 
            self.add_target()

    def _get_own_ship(self) -> Optional[Dict]:
        return next((s for s in self.ships if s.get('is_own')), None)

    def add_target(self):
        own = self._get_own_ship()
        base_x, base_y = (own['x'], own['y']) if own else (0, 0)
        
        new_id = f"TGT_{self.ship_count:03d}"
        self.ship_count += 1
        
        offset_x = random.randint(-self.world_limit + 100, self.world_limit - 100)
        offset_y = random.randint(-self.world_limit + 100, self.world_limit - 100)

        self.ships.append({
            "id": new_id,
            "x": base_x + offset_x,
            "y": base_y + offset_y,
            "speed": random.randint(5, 20),
            "heading": random.randint(0, 360),
            "is_own": False
        })

    def remove_target(self, target_id: str):
        if target_id == "OWN": 
            return
        self.ships = [s for s in self.ships if s['id'] != target_id]

    def update_target(self, target_id: str, speed: float, heading: float):
        for s in self.ships:
            if s['id'] == target_id:
                s['speed'], s['heading'] = float(speed), float(heading)

    def _get_vectors(self, s):
        rad = math.radians(90 - s['heading'])
        return s['speed'] * math.cos(rad), s['speed'] * math.sin(rad)

    def calculate_risk(self, own, target) -> Optional[RiskAlert]:
        dx, dy = target['x'] - own['x'], target['y'] - own['y']
        
        vox, voy = self._get_vectors(own)
        vtx, vty = self._get_vectors(target)
        
        dvx, dvy = vtx - vox, vty - voy
        dv2 = dvx**2 + dvy**2
        
        if dv2 < 0.0001: 
            return None 

        tcpa = -(dx * dvx + dy * dvy) / dv2
        
        if tcpa < 0: 
            return None

        future_x = dx + dvx * tcpa
        future_y = dy + dvy * tcpa
        cpa_dist = math.sqrt(future_x**2 + future_y**2)

        level = "SAFE"
        if cpa_dist < 100 and tcpa < 120: 
            level = "DANGER"
        elif cpa_dist < 300 and tcpa < 300: 
            level = "WARNING"

        if level != "SAFE":
            pred_tgt_x = target['x'] + vtx * tcpa
            pred_tgt_y = target['y'] + vty * tcpa
            
            return RiskAlert(
                target_id=target['id'], 
                cpa=round(cpa_dist, 1), 
                tcpa=round(tcpa, 1), 
                level=level, 
                cpa_point=Vector(x=pred_tgt_x, y=pred_tgt_y)
            )
        return None

    def step(self):
        try:
            now = time.time()
            dt = now - self.last_update
            self.last_update = now

            if self.paused: 
                return []

            own = self._get_own_ship()
            if not own: 
                return []

            alerts = []
            
            for s in self.ships:
                vx, vy = self._get_vectors(s)
                s['x'] += vx * dt
                s['y'] += vy * dt

            world_width = self.world_limit * 2
            
            for s in self.ships:
                if s.get('is_own'): 
                    continue

                rel_x = s['x'] - own['x']
                rel_y = s['y'] - own['y']

                if rel_x > self.world_limit: 
                    s['x'] -= world_width
                elif rel_x < -self.world_limit:
                    s['x'] += world_width
                
                if rel_y > self.world_limit: 
                    s['y'] -= world_width
                elif rel_y < -self.world_limit: 
                    s['y'] += world_width

                dist_sq = rel_x**2 + rel_y**2
                if dist_sq < (self.world_limit * 1.5)**2:
                    alert = self.calculate_risk(own, s)
                    if alert: alerts.append(alert)

            return alerts
        except Exception:
            traceback.print_exc()
            return []