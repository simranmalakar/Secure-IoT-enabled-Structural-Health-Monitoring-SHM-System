"""
Sensor Simulator — Secure IoT SHM System
==========================================
Simulates IoT sensors (vibration, tilt, strain) and publishes
JSON packets via MQTT with SHA-256 HMAC integrity hashes.

Usage:
    python simulator.py                  # Normal mode (3 sensors)
    python simulator.py --mode normal
    python simulator.py --mode high_vibration
    python simulator.py --mode spoofed
    python simulator.py --count 50       # Send 50 packets then stop
"""

import json
import time
import random
import hashlib
import hmac
import argparse
import sys
import os
import uuid
import math
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paho.mqtt.client as mqtt

from sensor_simulator.config import (
    MQTT_BROKER, MQTT_PORT, MQTT_TLS_PORT, MQTT_TOPIC_PREFIX, USE_TLS, CA_CERT,
    SENSOR_IDS, PUBLISH_INTERVAL, HMAC_SECRET,
    VIBRATION_MIN, VIBRATION_MAX, VIBRATION_SPIKE_MIN, VIBRATION_SPIKE_MAX,
    TILT_MIN, TILT_MAX, TILT_SPIKE_MIN, TILT_SPIKE_MAX,
    STRAIN_MIN, STRAIN_MAX, STRAIN_SPIKE_MIN, STRAIN_SPIKE_MAX,
)


def generate_reading(sensor_id: str, mode: str = "normal") -> dict:
    """Generate a single sensor reading based on the simulation mode."""

    if mode == "high_vibration":
        vibration = round(random.uniform(VIBRATION_SPIKE_MIN, VIBRATION_SPIKE_MAX), 4)
        tilt = round(random.uniform(TILT_MIN, TILT_MAX), 4)
        strain = round(random.uniform(STRAIN_MIN, STRAIN_MAX), 4)
    elif mode == "high_strain":
        vibration = round(random.uniform(VIBRATION_MIN, VIBRATION_MAX), 4)
        tilt = round(random.uniform(TILT_MIN, TILT_MAX), 4)
        strain = round(random.uniform(STRAIN_SPIKE_MIN, STRAIN_SPIKE_MAX), 4)
    elif mode == "high_tilt":
        vibration = round(random.uniform(VIBRATION_MIN, VIBRATION_MAX), 4)
        tilt = round(random.uniform(TILT_SPIKE_MIN, TILT_SPIKE_MAX), 4)
        strain = round(random.uniform(STRAIN_MIN, STRAIN_MAX), 4)
    else:
        # Normal mode with very slight, realistic jitter (structural baseline)
        vibration = round(random.uniform(0.05, 0.15), 4)
        tilt = round(random.uniform(0.1, 0.2), 4)
        strain = round(random.uniform(10.0, 15.0), 4)

    payload = {
        "sensor_id": sensor_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vibration": vibration,
        "tilt": tilt,
        "strain": strain,
        "packet_id": str(uuid.uuid4())
    }

    return payload


def compute_hash(payload: dict) -> str:
    """Compute SHA-256 HMAC of the payload for integrity verification."""
    # Create a deterministic string from the payload (sorted keys, no hash field)
    data_str = json.dumps(
        {k: v for k, v in payload.items() if k != "hash"},
        sort_keys=True,
    )
    return hmac.new(
        HMAC_SECRET.encode(),
        data_str.encode(),
        hashlib.sha256,
    ).hexdigest()


def create_mqtt_client() -> mqtt.Client:
    """Create and configure an MQTT client."""
    client = mqtt.Client(client_id=f"shm-sensor-sim-{random.randint(1000,9999)}")

    if USE_TLS:
        import ssl
        client.tls_set(
            ca_certs=CA_CERT,
            tls_version=ssl.PROTOCOL_TLSv1_2,
        )

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("[OK] Connected to MQTT broker")
        else:
            print(f"[ERROR] Connection failed with code {rc}")

    def on_disconnect(client, userdata, rc):
        print(f"[WARN]  Disconnected from broker (rc={rc})")

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    return client


def run_simulator(mode: str = "normal", count: int = 0):
    """Main simulation loop.

    Args:
        mode: Simulation mode (normal, high_vibration, high_strain, high_tilt, spoofed)
        count: Number of packets to send (0 = infinite)
    """
    client = create_mqtt_client()
    port = MQTT_TLS_PORT if USE_TLS else MQTT_PORT

    print(f"\n[START] SHM Sensor Simulator")
    print(f"   Mode: {mode}")
    print(f"   Broker: {MQTT_BROKER}:{port}")
    print(f"   Sensors: {', '.join(SENSOR_IDS)}")
    print(f"   Interval: {PUBLISH_INTERVAL}s")
    print(f"   Count: {'infinite' if count == 0 else count}")
    print(f"   TLS: {'Enabled' if USE_TLS else 'Disabled'}")
    print()

    try:
        client.connect(MQTT_BROKER, port, keepalive=60)
        client.loop_start()
    except ConnectionRefusedError:
        print("[ERROR] Could not connect to MQTT broker. Is Mosquitto running?")
        print("   Start it with: mosquitto -c broker/mosquitto.conf")
        sys.exit(1)

    sent = 0
    try:
        while True:
            for sensor_id in SENSOR_IDS:
                if mode == "structural_anomaly":
                    # Create a phased event over time (simulating a heavy vehicle or structural stress)
                    t = time.time()
                    # Use spike ranges for dramatic, realistic interaction
                    vibration = round(VIBRATION_SPIKE_MIN + (VIBRATION_SPIKE_MAX - VIBRATION_SPIKE_MIN) * (0.5 + 0.5 * math.sin(t * 1.5)), 4)
                    tilt = round(TILT_SPIKE_MIN + (TILT_SPIKE_MAX - TILT_SPIKE_MIN) * (0.5 + 0.5 * math.cos(t * 0.8)), 4)
                    strain = round(STRAIN_SPIKE_MIN + (STRAIN_SPIKE_MAX - STRAIN_SPIKE_MIN) * (0.5 + 0.5 * math.sin(t * 0.5)), 4)
                    
                    # Occasionally add a random spike to make it look "real"
                    if random.random() > 0.8: vibration *= 1.2
                    if random.random() > 0.9: strain *= 1.1
                    
                    payload = {
                        "sensor_id": sensor_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "vibration": vibration,
                        "tilt": tilt,
                        "strain": strain,
                        "packet_id": str(uuid.uuid4())
                    }
                else:
                    payload = generate_reading(sensor_id, mode)

                # Compute integrity hash
                if mode == "spoofed":
                    # Deliberately corrupt the hash
                    payload["hash"] = "FAKE_HASH_" + hashlib.sha256(
                        str(random.random()).encode()
                    ).hexdigest()[:32]
                else:
                    payload["hash"] = compute_hash(payload)

                topic = f"{MQTT_TOPIC_PREFIX}/{sensor_id}"
                message = json.dumps(payload)
                client.publish(topic, message, qos=1)

                print(
                    f"  [>>] [{sensor_id}] "
                    f"v={payload['vibration']:.2f} "
                    f"t={payload['tilt']:.2f} "
                    f"s={payload['strain']:.1f} "
                    f"{'[!] SPOOFED' if mode == 'spoofed' else '[OK]'}"
                )

                sent += 1
                if count > 0 and sent >= count:
                    raise KeyboardInterrupt  # Clean exit

            time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:
        print(f"\n\n[STOP] Simulator stopped. Total packets sent: {sent}")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SHM Sensor Simulator")
    parser.add_argument(
        "--mode",
        choices=["normal", "high_vibration", "high_strain", "high_tilt", "spoofed"],
        default="normal",
        help="Simulation mode (default: normal)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help="Number of packets to send (0 = infinite)",
    )
    args = parser.parse_args()
    run_simulator(mode=args.mode, count=args.count)

