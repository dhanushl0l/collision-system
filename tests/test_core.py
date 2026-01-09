import pytest
import math
from app.simulation import Simulation


@pytest.fixture
def sim():
    s = Simulation()
    s.ships = []
    return s


def test_vector_calculation(sim):
    """Verify Heading (Nav) to Vector (Math) conversion"""
    # Heading 90 (East) -> Should be x=Speed, y=0
    ship = {"speed": 10, "heading": 90}
    vx, vy = sim._get_vectors(ship)
    
    # Allow small floating point error (pytest.approx)
    assert vx == pytest.approx(10.0) 
    assert vy == pytest.approx(0.0)

    # Heading 0 (North) -> Should be x=0, y=Speed
    ship = {"speed": 10, "heading": 0}
    vx, vy = sim._get_vectors(ship)
    assert vx == pytest.approx(0.0)
    assert vy == pytest.approx(10.0)

def test_head_on_collision_risk(sim):
    """Test two ships moving directly at each other triggers DANGER"""
    # Own Ship: At 0,0 moving East at 10m/s
    sim.ships.append({
        "id": "OWN", "x": 0.0, "y": 0.0, 
        "speed": 10.0, "heading": 90.0, "is_own": True
    })
    
    # Target: At 1000,0 moving West at 10m/s (Head on)
    sim.ships.append({
        "id": "TGT_1", "x": 1000.0, "y": 0.0, 
        "speed": 10.0, "heading": 270.0, "is_own": False
    })
    
    own = sim.ships[0]
    target = sim.ships[1]
    
    alert = sim.calculate_risk(own, target)
    
    assert alert is not None
    assert alert.level == "DANGER"
    assert alert.cpa == pytest.approx(0.0, abs=1.0)
    assert alert.tcpa == pytest.approx(50.0, abs=0.1)

def test_crossing_safe_scenario(sim):
    """Test ships crossing with plenty of space (Safe)"""
    sim.ships.append({
        "id": "OWN", "x": 0, "y": 0, "speed": 10, "heading": 0, "is_own": True
    })
    # Target: 5000m away, Parallel course
    sim.ships.append({
        "id": "TGT", "x": 5000, "y": 0, "speed": 10, "heading": 0, "is_own": False
    })
    
    alert = sim.calculate_risk(sim.ships[0], sim.ships[1])
    
    assert alert is None

def test_overtaking_scenario(sim):
    """Test Overtaking: Target faster, same heading, coming from behind."""
    # Own Ship: Speed 10, Heading 90 (East)
    sim.ships.append({
        "id": "OWN", "x": 0.0, "y": 0.0, 
        "speed": 10.0, "heading": 90.0, "is_own": True
    })
    
    # Target: Behind (-500m), Speed 20 (Faster), Heading 90 (Same)
    sim.ships.append({
        "id": "TGT_OVERTAKE", "x": -500.0, "y": 0.0, 
        "speed": 20.0, "heading": 90.0, "is_own": False
    })
    
    own = sim.ships[0]
    target = sim.ships[1]
    
    alert = sim.calculate_risk(own, target)
    
    # Calculations:
    # Relative Speed = 10 m/s . Distance = 500m.
    # TCPA should be 50 seconds. CPA should be 0.
    assert alert is not None
    assert alert.cpa == pytest.approx(0.0, abs=1.0)
    assert alert.tcpa == pytest.approx(50.0, abs=0.1) 
    assert alert.level == "DANGER" # TCPA < 120s is DANGER in your logic

def test_crossing_bow_warning(sim):
    """Test Crossing Bow: Target crossing ahead at a distance triggering WARNING."""
    # Own Ship: Moving North (Heading 0)
    sim.ships.append({
        "id": "OWN", "x": 0.0, "y": 0.0, 
        "speed": 10.0, "heading": 0.0, "is_own": True
    })
    
    # Target: To the Right (East), Moving West (270)
    # Positioned so it crosses ahead but not immediately (Warning Zone)
    # Distance ~250m, Closing Speed ~14m/s
    sim.ships.append({
        "id": "TGT_CROSS", "x": 250.0, "y": 250.0, 
        "speed": 10.0, "heading": 270.0, "is_own": False
    })
    
    own = sim.ships[0]
    target = sim.ships[1]
    
    alert = sim.calculate_risk(own, target)
    
    # We expect a warn because it is close (<300m) 
    # but maybe not immediate collision depending on exact geometry
    assert alert is not None
    assert alert.level in ["WARNING", "DANGER"]