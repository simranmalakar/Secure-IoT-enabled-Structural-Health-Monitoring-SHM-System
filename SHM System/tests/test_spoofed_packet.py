"""
Test: Spoofed Packet Detection
=================================
Publishes packets with corrupted SHA-256 hashes to trigger IDS alerts.
"""
import sys, os, time, json, hashlib, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensor_simulator.simulator import create_mqtt_client, generate_reading
from sensor_simulator.config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_PREFIX, SENSOR_IDS

def run():
    client = create_mqtt_client()
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()

    print("\n[TEST] TEST: Spoofed Packet Detection (10 packets)")
    print("=" * 50)

    for i in range(10):
        sid = SENSOR_IDS[i % len(SENSOR_IDS)]
        payload = generate_reading(sid, mode="normal")
        # Corrupt the hash
        payload["hash"] = "FAKE_" + hashlib.sha256(str(random.random()).encode()).hexdigest()[:32]
        topic = f"{MQTT_TOPIC_PREFIX}/{sid}"
        client.publish(topic, json.dumps(payload), qos=1)
        print(f"  [{i+1:02d}] {sid} hash=FAKE... [!] SPOOFED")
        time.sleep(0.5)

    print(f"\n[OK] Sent 10 spoofed packets. Check /logs — should show SPOOFED_PACKET entries.")
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    run()

