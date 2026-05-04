"""
Test: Normal Sensor Data
==========================
Publishes 30 normal readings and verifies no alerts are generated.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensor_simulator.simulator import create_mqtt_client, generate_reading, compute_hash
from sensor_simulator.config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_PREFIX, SENSOR_IDS
import json

def run():
    client = create_mqtt_client()
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()

    print("\n[TEST] TEST: Normal Sensor Data (30 packets)")
    print("=" * 50)

    for i in range(30):
        sid = SENSOR_IDS[i % len(SENSOR_IDS)]
        payload = generate_reading(sid, mode="normal")
        payload["hash"] = compute_hash(payload)
        topic = f"{MQTT_TOPIC_PREFIX}/{sid}"
        client.publish(topic, json.dumps(payload), qos=1)
        print(f"  [{i+1:02d}] {sid} v={payload['vibration']:.2f} t={payload['tilt']:.2f} s={payload['strain']:.1f}")
        time.sleep(0.3)

    print(f"\n[OK] Sent 30 normal packets. Check /alerts — should be empty.")
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    run()

