"""
Test: DoS Attack Simulation
==============================
Floods MQTT with 100+ messages per second from a single sensor
to trigger the rate-limiting IDS detection.
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensor_simulator.simulator import create_mqtt_client, generate_reading, compute_hash
from sensor_simulator.config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_PREFIX

def run():
    client = create_mqtt_client()
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()

    target_sensor = "SENSOR_01"
    flood_count = 100

    print(f"\n[TEST] TEST: DoS Attack Simulation ({flood_count} packets in burst)")
    print("=" * 50)
    print(f"   Target: {target_sensor}")
    print(f"   Threshold: >20 msgs / 5 seconds\n")

    start = time.time()
    for i in range(flood_count):
        payload = generate_reading(target_sensor, mode="normal")
        payload["hash"] = compute_hash(payload)
        topic = f"{MQTT_TOPIC_PREFIX}/{target_sensor}"
        client.publish(topic, json.dumps(payload), qos=0)  # QoS 0 for speed
        if (i + 1) % 25 == 0:
            print(f"  Sent {i+1}/{flood_count}...")

    elapsed = time.time() - start
    rate = flood_count / elapsed if elapsed > 0 else flood_count

    print(f"\n[OK] Sent {flood_count} packets in {elapsed:.2f}s ({rate:.0f} msgs/s)")
    print(f"   Check /logs — should show DOS_ATTACK entries.")
    time.sleep(1)
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    run()

