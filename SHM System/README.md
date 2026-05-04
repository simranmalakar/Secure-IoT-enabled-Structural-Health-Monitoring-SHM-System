# Secure IoT-enabled Structural Health Monitoring (SHM) System

A production-quality prototype of a **Secure IoT Structural Health Monitoring system** for bridges and buildings. The system simulates sensor data, secures communication via MQTT with TLS and SHA-256 HMAC, detects anomalies using rule-based thresholds and Isolation Forest ML, exposes a FastAPI REST API with JWT authentication, and renders a real-time web dashboard.

---

## Architecture

```
┌─────────────────┐     MQTT (TLS)     ┌──────────────────┐
│  Sensor Nodes   │ ──────────────────▶ │    Gateway        │
│  (Simulator)    │                     │  ┌──────────────┐ │
│                 │                     │  │ IDS Engine    │ │
│  • Vibration    │                     │  │ Anomaly Det.  │ │
│  • Tilt         │                     │  │ SQLite Store  │ │
│  • Strain       │                     │  └──────────────┘ │
└─────────────────┘                     └────────┬─────────┘
                                                 │
                                        ┌────────▼─────────┐
                                        │   FastAPI Backend │
                                        │  • JWT Auth       │
                                        │  • REST Endpoints │
                                        └────────┬─────────┘
                                                 │
                                        ┌────────▼─────────┐
                                        │   Web Dashboard   │
                                        │  • Live Charts    │
                                        │  • Alerts Panel   │
                                        │  • Security Logs  │
                                        └──────────────────┘
```

## Features

| Feature | Implementation |
|---------|---------------|
| Sensor Simulation | 3 virtual sensors (vibration, tilt, strain) with configurable modes |
| MQTT Communication | Paho-MQTT with optional TLS on port 8883 |
| Data Integrity | SHA-256 HMAC on every packet |
| Anomaly Detection | Rule-based thresholds + Isolation Forest ML |
| Intrusion Detection | Spoofed packet detection, DoS rate limiting |
| Authentication | JWT tokens (HS256, 60-min expiry) |
| REST API | FastAPI with Swagger docs at `/docs` |
| Dashboard | Real-time Chart.js graphs, alerts, security logs |
| Storage | SQLite with WAL mode |

## Quick Start

### Prerequisites

- **Python 3.9+**
- **Mosquitto MQTT Broker** — [Download](https://mosquitto.org/download/)

### Setup

1. **Install Python dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

2. **Generate TLS certificates**:
   ```powershell
   python generate_certs.py
   ```

3. **Add Mosquitto to PATH**:
   Ensure `C:\Program Files\Mosquitto` is in your System Environment Variables (Path). Restart your terminal after adding it.

4. **Launch the System**:
   The easiest way on Windows is to use the provided batch script:
   ```powershell
   .\run_all.bat
   ```

### Manual Service Start (Optional)
If you prefer running services in separate terminals:
1. **Broker**: `mosquitto -c broker/mosquitto.conf`
2. **Gateway**: `python -m gateway.gateway`
3. **API**: `uvicorn backend.main:app --reload --port 8000`
4. **Simulator**: `python -m sensor_simulator.simulator`

### Windows "One-Click" Setup
If this is your first time running the project:
```powershell
.\setup.bat
.\run_all.bat
```

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/login` | — | Get JWT token |
| GET | `/sensor-data` | JWT | Sensor readings |
| GET | `/alerts` | JWT | Anomaly alerts |
| GET | `/logs` | JWT | Security logs |
| GET | `/health` | — | System health |
| GET | `/docs` | — | Swagger UI |

## Testing

```bash
# Normal readings (expect no alerts)
python tests/test_normal.py

# High vibration (expect CRITICAL alerts)
python tests/test_high_vibration.py

# Spoofed packets (expect IDS security logs)
python tests/test_spoofed_packet.py

# DoS flood (expect rate-limit security logs)
python tests/test_dos_attack.py
```

## Project Structure

```
secure-monitoring/
├── broker/               # Mosquitto config
├── sensor_simulator/     # Sensor data generation
├── gateway/              # Edge computing + IDS + anomaly detection
├── backend/              # FastAPI REST API
├── dashboard/            # Web UI (HTML + CSS + JS)
├── tests/                # Security & anomaly test scripts
├── certs/                # TLS certificates (generated)
├── generate_certs.py     # Certificate generator
├── requirements.txt      # Python dependencies
├── setup.bat             # Windows setup script
└── README.md
```

## Security Layers

1. **TLS Encryption** — MQTT secured with self-signed certificates
2. **SHA-256 HMAC** — Every sensor packet includes integrity hash
3. **JWT Authentication** — API protected with time-limited tokens
4. **IDS Engine** — Detects spoofing, DoS attacks, unauthorized access
5. **Anomaly Detection** — Thresholds + ML catch structural anomalies

## Demo Credentials

- **Username:** `admin`
- **Password:** `shm@secure2024`

---

*Based on the research paper: "Secure IoT-enabled Structural Health Monitoring (SHM) System for Bridges and Buildings"*
