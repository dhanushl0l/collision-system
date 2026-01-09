from fastapi.testclient import TestClient
from app.main import app
from app.state import sim 
import pytest
import time

@pytest.fixture(name="client")
def client_fixture():
    with TestClient(app) as client:
        yield client

@pytest.fixture(autouse=True)
def reset_state():
    """Ensure every test starts with a freh, unpaused simulation."""
    sim.reset_scenario()
    sim.paused = False

def test_websocket_initial_state(client):
    """Scenario 1: Verify the connection is established and sends valid initial data."""
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()
        
        assert "ships" in data
        assert "alerts" in data
        assert "is_paused" in data
        
        assert data["is_paused"] is False
        assert len(data["ships"]) > 0
        
        own_ship = next((s for s in data["ships"] if s["id"] == "OWN"), None)
        assert own_ship is not None

def test_pause_action_reflects_in_websocket(client):
    """Scenario 2: Verify that clicking 'Pause' updates the live stream."""
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()
        
        response = client.post("/api/control/pause")
        assert response.status_code == 200
        
        is_paused = False
        for _ in range(3):
            data = websocket.receive_json()
            if data["is_paused"] is True:
                is_paused = True
                break
        
        assert is_paused is True, "WebSocket stream never reported the Pause state"

def test_add_target_reflects_in_websocket(client):
    """Scenario 3: Verify that adding a ship updates the live stream."""
    with client.websocket_connect("/ws") as websocket:
        initial_data = websocket.receive_json()
        initial_count = len(initial_data["ships"])
        
        client.post("/api/control/add")
        
        found_new_ship = False
        for _ in range(5):
            data = websocket.receive_json()
            if len(data["ships"]) > initial_count:
                found_new_ship = True
                break
                
        assert found_new_ship is True, "New ship never appeared in the WebSocket stream"

def test_physics_engine_moves_ships(client):
    """Scenario 4: Verify that ships actually change position over time."""
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()
        target = next(s for s in data["ships"] if not s["is_own_ship"])
        start_x = target["position"]["x"]
        
        moved = False
        for _ in range(10): 
            new_data = websocket.receive_json()
            new_target = next(s for s in new_data["ships"] if s["id"] == target["id"])
            
            if new_target["position"]["x"] != start_x:
                moved = True
                break
        
        assert moved is True, f"Ship {target['id']} did not move after 10 simulation ticks"