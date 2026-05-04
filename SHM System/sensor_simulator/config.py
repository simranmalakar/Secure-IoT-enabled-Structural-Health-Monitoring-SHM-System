"""
Sensor Simulator Configuration
================================
Central configuration for sensor simulation parameters,
MQTT broker connection, and data ranges.
"""

# --- MQTT Broker ---
MQTT_BROKER = "localhost"
MQTT_PORT = 1883              # Use 8883 for TLS
MQTT_TLS_PORT = 8883
MQTT_TOPIC_PREFIX = "shm/sensors"
USE_TLS = False               # Set True when certs are configured

# --- TLS Paths (relative to project root) ---
CA_CERT = "../certs/ca.crt"

# --- Sensor Configuration ---
SENSOR_IDS = ["SENSOR_01", "SENSOR_02", "SENSOR_03"]
PUBLISH_INTERVAL = 2          # seconds between readings

# --- Data Ranges (Normal) ---
VIBRATION_MIN = 0.01          # m/s²
VIBRATION_MAX = 2.0           # m/s² (normal upper bound)
VIBRATION_SPIKE_MIN = 3.0     # m/s² (anomaly range)
VIBRATION_SPIKE_MAX = 5.0     # m/s²

TILT_MIN = 0.0                # degrees
TILT_MAX = 3.0                # degrees (normal)
TILT_SPIKE_MIN = 4.5          # degrees (anomaly)
TILT_SPIKE_MAX = 5.0          # degrees

STRAIN_MIN = 0.0              # µε
STRAIN_MAX = 180.0            # µε (normal upper bound)
STRAIN_SPIKE_MIN = 220.0      # µε (anomaly range)
STRAIN_SPIKE_MAX = 300.0      # µε

# --- SHA-256 HMAC Secret ---
HMAC_SECRET = "shm-iot-secure-key-2024"

