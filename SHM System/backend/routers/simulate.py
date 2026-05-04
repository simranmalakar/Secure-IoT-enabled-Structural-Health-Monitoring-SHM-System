"""
Simulate Router — /simulate
====================================
Endpoint to trigger attack simulations and control live data.
"""

import json
import time
import hashlib
import threading
from fastapi import APIRouter, Depends, BackgroundTasks
import paho.mqtt.client as mqtt

from backend.auth import get_current_user
from backend.database import clear_all_data
from sensor_simulator.simulator import generate_reading, compute_hash
from sensor_simulator.config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_PREFIX, SENSOR_IDS

router = APIRouter(tags=["Simulation"])

# Global state for continuous simulation
simulation_active = False
simulation_thread = None

def _continuous_simulation():
    """Background thread to generate continuous 'Normal' data."""
    global simulation_active
    client = mqtt.Client(client_id="shm-live-simulator")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT)
        client.loop_start()
        
        while simulation_active:
            for sensor_id in SENSOR_IDS:
                payload = generate_reading(sensor_id)
                payload["hash"] = compute_hash(payload)
                client.publish(f"{MQTT_TOPIC_PREFIX}/{sensor_id}", json.dumps(payload), qos=1)
            
            # Wait for next interval
            time.sleep(2)
            
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print(f"[SIMULATOR ERROR] {e}")
        simulation_active = False

def _publish_attack(attack_type: str):
    """Publish malicious MQTT messages."""
    client = mqtt.Client(client_id="shm-attack-simulator")
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start()

    sensor_id = SENSOR_IDS[0]

    if attack_type == "spoof":
        # Corrupted packets with rapid, aggressive up-down patterns (Jitter)
        for i in range(12):
            payload = generate_reading(sensor_id)
            # Create "V" and "M" shapes on the graph
            payload["vibration"] = 8.0 if i % 2 == 0 else 0.5
            payload["tilt"] = 5.0 if i % 3 == 0 else 1.0
            payload["hash"] = "FAKE_SIG_" + hashlib.md5(str(time.time()).encode()).hexdigest()
            client.publish(f"{MQTT_TOPIC_PREFIX}/{sensor_id}", json.dumps(payload), qos=1)
            time.sleep(0.3)
    
    elif attack_type == "dos":
        # High-frequency burst of erratic data
        for i in range(60):
            payload = generate_reading(sensor_id)
            # Random high spikes
            payload["vibration"] = 3.0 + (i % 7) * 1.2
            payload["strain"] = 400 + (i % 4) * 150
            payload["hash"] = compute_hash(payload)
            client.publish(f"{MQTT_TOPIC_PREFIX}/{sensor_id}", json.dumps(payload), qos=1)
            time.sleep(0.08)


    client.loop_stop()
    client.disconnect()

@router.get("/simulation/status")
async def get_sim_status(user: dict = Depends(get_current_user)):
    """Check if the live simulation is currently active."""
    return {"active": simulation_active}

@router.post("/simulation/start")
async def start_simulation(user: dict = Depends(get_current_user)):
    """Start the continuous live sensor simulation."""
    global simulation_active, simulation_thread
    if simulation_active:
        return {"status": "error", "message": "Simulation is already running"}
    
    # Clear previous data to show "0" activity initially
    clear_all_data()
    
    simulation_active = True
    simulation_thread = threading.Thread(target=_continuous_simulation, daemon=True)
    simulation_thread.start()
    return {"status": "success", "message": "System monitoring started"}

@router.post("/simulation/stop")
async def stop_simulation(user: dict = Depends(get_current_user)):
    """Stop the continuous live sensor simulation."""
    global simulation_active
    simulation_active = False
    return {"status": "success", "message": "System monitoring stopped"}

@router.post("/simulate/{attack_type}")
async def simulate_attack(
    attack_type: str,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """Trigger a simulated attack. Requires JWT authentication."""
    if not simulation_active:
        return {"status": "error", "message": "System must be STARTED before simulating attacks"}

    if attack_type not in ["spoof", "dos"]:
        return {"status": "error", "message": "Invalid simulation type"}
    
    background_tasks.add_task(_publish_attack, attack_type)
    return {"status": "success", "message": f"Simulating {attack_type} attack"}
