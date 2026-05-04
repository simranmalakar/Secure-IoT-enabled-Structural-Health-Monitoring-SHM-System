"""
MQTT Gateway — Secure IoT SHM Edge Computing Layer
=====================================================
Subscribes to sensor MQTT topics, validates integrity,
runs anomaly detection + IDS, and persists data to SQLite.

Usage:
    python -m gateway.gateway
    python -m gateway.gateway --tls       (with TLS enabled)
"""

import json
import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paho.mqtt.client as mqtt

from gateway.db import insert_reading, init_database
from gateway.anomaly_detector import AnomalyDetector
from gateway.ids import IntrusionDetector
from sensor_simulator.config import (
    MQTT_BROKER, MQTT_PORT, MQTT_TLS_PORT,
    MQTT_TOPIC_PREFIX, CA_CERT,
)


class SHMGateway:
    """Main gateway service that orchestrates security + anomaly detection."""

    def __init__(self, use_tls: bool = False, enable_ml: bool = True):
        self.use_tls = use_tls
        self.anomaly_detector = AnomalyDetector(enable_ml=enable_ml)
        self.ids = IntrusionDetector()
        self.total_processed = 0
        self.total_rejected = 0

        # Initialize DB
        init_database()

    def on_connect(self, client, userdata, flags, rc):
        """Callback: successful MQTT connection."""
        if rc == 0:
            topic = f"{MQTT_TOPIC_PREFIX}/+"
            client.subscribe(topic, qos=1)
            print(f"[OK] Gateway connected — subscribed to: {topic}")
        else:
            print(f"[ERROR] Connection failed (rc={rc})")

    def on_message(self, client, userdata, msg):
        """Callback: incoming MQTT message processing pipeline."""
        try:
            payload = json.loads(msg.payload.decode())
            sensor_id = payload.get("sensor_id", "UNKNOWN")

            self.total_processed += 1

            # === Step 1: IDS Checks ===
            ids_result = self.ids.process(sensor_id, payload)

            if ids_result["spoofed"]:
                self.total_rejected += 1
                return  # Drop spoofed packets

            if ids_result["dos"]:
                # Log but still process (could be legitimate burst)
                pass

            # === Step 3: Anomaly Detection ===
            anomaly_result = self.anomaly_detector.process(
                sensor_id=sensor_id,
                vibration=payload.get("vibration", 0),
                tilt=payload.get("tilt", 0),
                strain=payload.get("strain", 0),
            )
            alerts = anomaly_result.get("alerts", [])

            # === Step 2: Store reading (Updated to include anomaly score) ===
            insert_reading(
                sensor_id=sensor_id,
                timestamp=payload.get("timestamp", ""),
                vibration=payload.get("vibration", 0),
                tilt=payload.get("tilt", 0),
                strain=payload.get("strain", 0),
                hash_value=payload.get("hash", ""),
                anomaly_score=anomaly_result.get("score", 0.0),
                anomaly_class=anomaly_result.get("classification", "NORMAL"),
                prediction=anomaly_result.get("prediction", 0.0),
                explanation=anomaly_result.get("explanation", ""),
            )

            # === Step 4: Console output ===
            status = "[OK]"
            if alerts or anomaly_result["score"] >= 70:
                status = "[!] CRIT"
            elif anomaly_result["score"] >= 20:
                status = "[~] WARN"
            elif ids_result["dos"]:
                status = "[~] RATE"

            print(
                f"  {status} [{sensor_id}] "
                f"v={payload.get('vibration', 0):.2f} "
                f"t={payload.get('tilt', 0):.2f} "
                f"s={payload.get('strain', 0):.1f} "
                f"| Processed: {self.total_processed} "
                f"| Rejected: {self.total_rejected}"
            )

            if alerts:
                for alert in alerts:
                    print(f"    [WARN]  {alert['severity']}: {alert['message']}")

        except json.JSONDecodeError:
            print(f"  [WARN]  Invalid JSON from topic: {msg.topic}")
        except Exception as e:
            print(f"  [ERROR] Error processing message: {e}")

    def on_disconnect(self, client, userdata, rc):
        """Callback: MQTT disconnection."""
        print(f"[WARN]  Gateway disconnected (rc={rc})")

    def run(self):
        """Start the gateway service."""
        client = mqtt.Client(client_id="shm-gateway-001")

        if self.use_tls:
            import ssl
            client.tls_set(
                ca_certs=CA_CERT,
                tls_version=ssl.PROTOCOL_TLSv1_2,
            )

        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.on_disconnect = self.on_disconnect

        port = MQTT_TLS_PORT if self.use_tls else MQTT_PORT

        print(f"\n[NET] SHM Gateway — Edge Computing Layer")
        print(f"   Broker: {MQTT_BROKER}:{port}")
        print(f"   TLS: {'Enabled' if self.use_tls else 'Disabled'}")
        print(f"   ML Detection: {'Enabled' if self.anomaly_detector.enable_ml else 'Disabled'}")
        print(f"   Subscribing to: {MQTT_TOPIC_PREFIX}/+")
        print()

        try:
            client.connect(MQTT_BROKER, port, keepalive=60)
            client.loop_forever()
        except ConnectionRefusedError:
            print("[ERROR] Could not connect to MQTT broker. Is Mosquitto running?")
            print("   Start it with: mosquitto -c broker/mosquitto.conf")
            sys.exit(1)
        except KeyboardInterrupt:
            print(f"\n\n[STOP] Gateway stopped.")
            print(f"   Total processed: {self.total_processed}")
            print(f"   Total rejected: {self.total_rejected}")
            ids_stats = self.ids.get_stats()
            print(f"   Spoofed packets: {ids_stats['total_spoofed_packets']}")
            print(f"   DoS events: {ids_stats['total_dos_events']}")
        finally:
            client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SHM Gateway Service")
    parser.add_argument("--tls", action="store_true", help="Enable TLS encryption")
    parser.add_argument("--no-ml", action="store_true", help="Disable ML anomaly detection")
    args = parser.parse_args()

    gateway = SHMGateway(use_tls=args.tls, enable_ml=not args.no_ml)
    gateway.run()

