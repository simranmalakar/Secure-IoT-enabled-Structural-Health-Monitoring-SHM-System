# 🔐 Secure IoT-enabled Structural Health Monitoring (SHM) System

A **production-grade cybersecurity + IoT prototype** for monitoring the structural integrity of bridges and buildings in real time.

This system integrates **sensor simulation, secure communication, edge computing, anomaly detection, and intrusion detection** into a unified architecture designed for **cyber-physical infrastructure protection**.

---

## 🚀 Overview

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

## 📄 Research Basis

This project is based on:

**“Secure IoT-enabled Structural Health Monitoring (SHM) System for Bridges and Buildings”** 

---

## 👩‍💻 Author

**Simran Malakar**
Cybersecurity | IoT Security | VAPT

---

## ⭐ Why This Project Stands Out

This is not just an IoT project — it is a **cybersecurity-focused cyber-physical system**, combining:

* Offensive thinking (attack simulation)
* Defensive engineering (IDS, encryption)
* Real-world infrastructure relevance

---

If you want, I can next:

* 🔥 Add **GitHub badges + screenshots section**
* 🔥 Create **LinkedIn project post**
* 🔥 Turn this into a **portfolio case study (interview ready)**
