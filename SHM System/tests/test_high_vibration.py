"""
Test: High Vibration Anomaly
===============================
Publishes packets with vibration spikes > 2.5 m/s² to trigger alerts.
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

    print("\n[TEST] TEST: High Vibration Anomaly (20 packets)")
    print("=" * 50)

    for i in range(20):
        sid = SENSOR_IDS[i % len(SENSOR_IDS)]
        payload = generate_reading(sid, mode="high_vibration")
        payload["hash"] = compute_hash(payload)
        topic = f"{MQTT_TOPIC_PREFIX}/{sid}"
        client.publish(topic, json.dumps(payload), qos=1)
        print(f"  [{i+1:02d}] {sid} v={payload['vibration']:.2f} [!] SPIKE")
        time.sleep(0.3)

    print(f"\n[OK] Sent 20 high-vibration packets. Check /alerts — should show CRITICAL alerts.")
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    run()

