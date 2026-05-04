# 🔐 Secure IoT-enabled Structural Health Monitoring (SHM) System

A **production-grade cybersecurity + IoT prototype** for monitoring the structural integrity of bridges and buildings in real time.

This system integrates **sensor simulation, secure communication, edge computing, anomaly detection, and intrusion detection** into a unified architecture designed for **cyber-physical infrastructure protection**.
Traditional structural monitoring relies on manual inspections, which are slow and reactive. This project implements a **real-time, secure, and automated SHM system** using:

* IoT sensor simulation
* Secure MQTT communication (TLS)
* Edge-based anomaly detection
* Cybersecurity protections (HMAC, JWT, IDS)
* Real-time dashboard visualization

---

## 🏗️ System Architecture

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
                                        │  • REST APIs      │
                                        └────────┬─────────┘
                                                 │
                                        ┌────────▼─────────┐
                                        │   Web Dashboard   │
                                        │  • Live Charts    │
                                        │  • Alerts Panel   │
                                        │  • Security Logs  │
                                        └──────────────────┘
```

---

## ✨ Key Features

### 🔹 IoT & Data Pipeline

* Simulated sensors: **vibration, tilt, strain**
* Real-time data transmission using **MQTT**
* Edge preprocessing via gateway (Raspberry Pi simulation)

### 🔹 Security (Core Highlight 🚨)

* **TLS encryption** for MQTT communication
* **SHA-256 HMAC** for packet integrity
* **JWT authentication** for API access
* **Intrusion Detection System (IDS)**:

  * Spoofed packet detection
  * DoS / flooding detection
  * Unauthorized access logging

### 🔹 Anomaly Detection

* Rule-based thresholds:

  * High vibration
  * Structural strain anomalies
* Machine Learning:

  * **Isolation Forest** for anomaly detection

### 🔹 Backend & API

* Built with **FastAPI**
* Interactive API docs via Swagger (`/docs`)
* Secure endpoints with JWT

### 🔹 Dashboard

* Real-time visualization using **Chart.js**
* Displays:

  * Sensor data streams
  * Alerts
  * Security logs

### 🔹 Storage

* Lightweight **SQLite database**
* WAL mode enabled for performance

---

## ⚙️ Tech Stack

| Layer             | Technology                       |
| ----------------- | -------------------------------- |
| IoT Communication | MQTT (Mosquitto)                 |
| Backend           | FastAPI                          |
| Security          | TLS, SHA-256, JWT                |
| ML                | Scikit-learn (Isolation Forest)  |
| Database          | SQLite                           |
| Dashboard         | HTML, CSS, JavaScript (Chart.js) |
| Language          | Python                           |

---

## ⚡ Quick Start

### 📌 Prerequisites

* Python 3.9+
* Mosquitto MQTT Broker

---

### 🔧 Installation

```bash
pip install -r requirements.txt
```

---

### 🔐 Generate Certificates

```bash
python generate_certs.py
```

---

### ▶️ Run the System (Windows)

```bash
.\setup.bat
.\run_all.bat
```

---

### 🧪 Manual Run (Optional)

Run each component separately:

```bash
# MQTT Broker
mosquitto -c broker/mosquitto.conf

# Gateway
python -m gateway.gateway

# Backend API
uvicorn backend.main:app --reload --port 8000

# Sensor Simulator
python -m sensor_simulator.simulator
```

---

## 🌐 API Endpoints

| Method | Endpoint       | Auth | Description        |
| ------ | -------------- | ---- | ------------------ |
| POST   | `/login`       | ❌    | Generate JWT token |
| GET    | `/sensor-data` | ✅    | Fetch sensor data  |
| GET    | `/alerts`      | ✅    | Get anomaly alerts |
| GET    | `/logs`        | ✅    | Security logs      |
| GET    | `/health`      | ❌    | System status      |
| GET    | `/docs`        | ❌    | Swagger UI         |

---

## 🧪 Testing Scenarios

```bash
# Normal operation
python tests/test_normal.py

# Structural anomaly (high vibration)
python tests/test_high_vibration.py

# Spoofed data attack
python tests/test_spoofed_packet.py

# DoS simulation
python tests/test_dos_attack.py
```

---

## 📁 Project Structure

```
secure-monitoring/
├── broker/               # MQTT broker configuration
├── sensor_simulator/     # Sensor data generator
├── gateway/              # Edge processing + IDS + anomaly detection
├── backend/              # FastAPI application
├── dashboard/            # Frontend dashboard
├── tests/                # Attack & anomaly simulations
├── certs/                # TLS certificates
├── generate_certs.py     # Certificate generator
├── requirements.txt
├── setup.bat
└── README.md
```

---

## 🛡️ Security Architecture

This system implements a **multi-layered defense model**:

1. **Transport Security** → TLS-encrypted MQTT
2. **Data Integrity** → SHA-256 HMAC verification
3. **Access Control** → JWT authentication
4. **Threat Detection** → IDS (spoofing, DoS)
5. **Behavior Analysis** → anomaly detection

---

## 🔑 Demo Credentials

```
Username: admin
Password: shm@secure2024
```
## 📸 System Screenshots
<img width="836" height="789" alt="Screenshot 2026-05-03 232758" src="https://github.com/user-attachments/assets/93668ea2-bc42-4470-afdd-ced42e41ab65" />
<img width="1897" height="943" alt="Screenshot 2026-05-03 232702" src="https://github.com/user-attachments/assets/af487356-1525-4a8c-b86d-0c3204ec6e5a" />
<img width="1894" height="941" alt="Screenshot 2026-05-03 232718" src="https://github.com/user-attachments/assets/c037624c-f08a-409d-b137-78ba5a34ce36" />
<img width="1894" height="944" alt="Screenshot 2026-05-03 232731" src="https://github.com/user-attachments/assets/44aabe9e-7909-4f31-8564-a5c5332495f5" />
<img width="1907" height="754" alt="Screenshot 2026-05-03 232741" src="https://github.com/user-attachments/assets/cc3f2c39-0f91-4b65-9dff-fd2a44090ac5" />



---

## 📊 Use Cases

* Smart city infrastructure monitoring
* Bridge and building safety systems
* Industrial structural monitoring
* Cyber-physical system security research

---

## 🔮 Future Enhancements

* Deep learning models (CNN-LSTM)
* Digital twin integration
* Blockchain-based data integrity
* Cloud deployment (AWS / Azure)
* Real hardware sensor integration (ESP32, Raspberry Pi)

---

---

## 👩‍💻 Author

**Simran Malakar**
Cybersecurity | VAPT

---


