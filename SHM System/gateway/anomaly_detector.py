"""
Anomaly Detection Engine — Secure IoT SHM Gateway
====================================================
Implements rule-based anomaly detection with thresholds
and an optional Isolation Forest ML model for advanced detection.
"""

import json
import numpy as np
from collections import defaultdict, deque
from gateway.db import insert_alert


# --- Threshold Rules ---
THRESHOLDS = {
    "vibration": {"warn": 2.0, "critical": 2.5, "unit": "m/s²"},
    "tilt":      {"warn": 3.5, "critical": 4.0, "unit": "°"},
    "strain":    {"warn": 180,  "critical": 200,  "unit": "µε"},
}


class AnomalyDetector:
    """Combined rule-based, ML, and time-series anomaly detector."""

    def __init__(self, enable_ml: bool = True):
        self.enable_ml = enable_ml
        self.ml_model = None
        self.training_data = []
        self.ml_trained = False
        self.training_threshold = 50
        
        # History per sensor for trend analysis
        self.history = defaultdict(lambda: deque(maxlen=100))

    def _detect_spike(self, sensor_id: str, vibration: float) -> bool:
        """Detect sudden spikes using moving average and std deviation."""
        hist = [r['vibration'] for r in self.history[sensor_id]]
        if len(hist) < 10:
            return False
        
        recent = hist[-10:]
        mean = np.mean(recent)
        std = np.std(recent)
        
        if std == 0:
            return False
        
        # If current value is > 3 std devs from recent mean
        return abs(vibration - mean) > (3 * std)

    def _detect_drift(self, sensor_id: str) -> bool:
        """Detect gradual structural degradation/drift."""
        hist = [r['strain'] for r in self.history[sensor_id]]
        if len(hist) < 50:
            return False
        
        old_mean = np.mean(hist[:25])
        recent_mean = np.mean(hist[-25:])
        
        # 10% drift in strain over 50 readings indicates potential degradation
        if old_mean > 0 and abs(recent_mean - old_mean) / old_mean > 0.10:
            return True
        return False

    def _predict_trend(self, sensor_id: str) -> float:
        """Simple linear extrapolation for next 10 seconds."""
        hist = [r['vibration'] for r in self.history[sensor_id]]
        if len(hist) < 10:
            return 0.0
        
        y = hist[-10:]
        x = np.arange(len(y))
        
        if len(x) > 1:
            slope, intercept = np.polyfit(x, y, 1)
            # Predict 10 steps ahead (approx 10 seconds if 1 Hz)
            return float(slope * (len(x) + 10) + intercept)
        return float(y[-1])

    def check_ml(self, vibration: float, tilt: float, strain: float) -> bool:
        if not self.enable_ml or not self.ml_trained:
            return False
        try:
            sample = np.array([[vibration, tilt, strain]])
            prediction = self.ml_model.predict(sample)
            return prediction[0] == -1
        except Exception:
            return False

    def train_ml_model(self):
        if not self.enable_ml or len(self.training_data) < self.training_threshold:
            return
        try:
            from sklearn.ensemble import IsolationForest
            X = np.array(self.training_data)
            self.ml_model = IsolationForest(
                n_estimators=100, contamination=0.05, random_state=42
            )
            self.ml_model.fit(X)
            self.ml_trained = True
            print(f"  [ML] ML model trained on {len(self.training_data)} samples")
        except ImportError:
            self.enable_ml = False

    def process(self, sensor_id: str, vibration: float, tilt: float, strain: float) -> dict:
        """Run full anomaly detection pipeline and return a comprehensive result."""
        
        score = 0
        explanations = []
        alerts = []
        
        # 1. Rule-based detection
        if vibration >= THRESHOLDS["vibration"]["critical"]:
            score += 50
            explanations.append(f"Vibration critical ({vibration:.2f})")
            alerts.append({
                "alert_type": "HIGH_VIBRATION", 
                "severity": "CRITICAL", 
                "message": f"CRITICAL: Vibration exceeded safe limit ({vibration:.2f} m/s² > {THRESHOLDS['vibration']['critical']} m/s²)",
                "features": {"vibration": 100, "tilt": 0, "strain": 0}
            })
        elif vibration >= THRESHOLDS["vibration"]["warn"]:
            score += 30
            explanations.append(f"Vibration warning ({vibration:.2f})")
            alerts.append({
                "alert_type": "HIGH_VIBRATION", 
                "severity": "HIGH", 
                "message": f"WARNING: Vibration elevated ({vibration:.2f} m/s² > {THRESHOLDS['vibration']['warn']} m/s²)",
                "features": {"vibration": 100, "tilt": 0, "strain": 0}
            })

        if strain >= THRESHOLDS["strain"]["critical"]:
            score += 50
            explanations.append(f"Strain critical ({strain:.1f})")
            alerts.append({
                "alert_type": "HIGH_STRAIN", 
                "severity": "CRITICAL", 
                "message": f"CRITICAL: Strain exceeded safe limit ({strain:.1f} µε > {THRESHOLDS['strain']['critical']} µε)",
                "features": {"vibration": 0, "tilt": 0, "strain": 100}
            })
        elif strain >= THRESHOLDS["strain"]["warn"]:
            score += 30
            explanations.append(f"Strain warning ({strain:.1f})")
            alerts.append({
                "alert_type": "HIGH_STRAIN", 
                "severity": "HIGH", 
                "message": f"WARNING: Strain elevated ({strain:.1f} µε > {THRESHOLDS['strain']['warn']} µε)",
                "features": {"vibration": 0, "tilt": 0, "strain": 100}
            })

        if tilt >= THRESHOLDS["tilt"]["critical"]:
            score += 50
            explanations.append(f"Tilt critical ({tilt:.2f})")
            alerts.append({
                "alert_type": "HIGH_TILT", 
                "severity": "CRITICAL", 
                "message": f"CRITICAL: Tilt exceeded safe limit ({tilt:.2f}° > {THRESHOLDS['tilt']['critical']}°)",
                "features": {"vibration": 0, "tilt": 100, "strain": 0}
            })
        elif tilt >= THRESHOLDS["tilt"]["warn"]:
            score += 30
            explanations.append(f"Tilt warning ({tilt:.2f})")
            alerts.append({
                "alert_type": "HIGH_TILT", 
                "severity": "HIGH", 
                "message": f"WARNING: Tilt elevated ({tilt:.2f}° > {THRESHOLDS['tilt']['warn']}°)",
                "features": {"vibration": 0, "tilt": 100, "strain": 0}
            })

        # 2. Time-series Analysis
        if self._detect_spike(sensor_id, vibration):
            score += 30
            explanations.append("Sudden vibration spike detected")
            alerts.append({
                "alert_type": "SUDDEN_SPIKE", 
                "severity": "HIGH", 
                "message": "HIGH: Sudden vibration spike detected (Rapid acceleration deviation)",
                "features": {"vibration": 90, "tilt": 5, "strain": 5}
            })
            
        if self._detect_drift(sensor_id):
            score += 20
            explanations.append("Gradual structural degradation (drift) detected")
            alerts.append({
                "alert_type": "SENSOR_DRIFT", 
                "severity": "MEDIUM", 
                "message": "MEDIUM: Gradual structural degradation detected (Strain drift over time)",
                "features": {"vibration": 0, "tilt": 10, "strain": 90}
            })

        # 3. ML Detection
        if self.ml_trained and self.check_ml(vibration, tilt, strain):
            score += 40
            explanations.append("Isolation Forest detected multi-variate anomaly")
            # Calculate simple heuristic feature deviation for ML explainability
            hist_v = [r['vibration'] for r in self.history[sensor_id]]
            hist_t = [r['tilt'] for r in self.history[sensor_id]]
            hist_s = [r['strain'] for r in self.history[sensor_id]]
            
            dev_v = abs(vibration - np.mean(hist_v)) / (np.std(hist_v) + 0.001) if hist_v else 1.0
            dev_t = abs(tilt - np.mean(hist_t)) / (np.std(hist_t) + 0.001) if hist_t else 1.0
            dev_s = abs(strain - np.mean(hist_s)) / (np.std(hist_s) + 0.001) if hist_s else 1.0
            
            total_dev = dev_v + dev_t + dev_s
            pct_v = int((dev_v / total_dev) * 100) if total_dev > 0 else 33
            pct_t = int((dev_t / total_dev) * 100) if total_dev > 0 else 33
            pct_s = 100 - pct_v - pct_t
            
            alerts.append({
                "alert_type": "ML_ANOMALY", 
                "severity": "HIGH", 
                "message": "HIGH: ML detected structural anomaly (Multi-variate interaction)",
                "features": {"vibration": pct_v, "tilt": pct_t, "strain": pct_s}
            })

        # Collect data for ML training if normal
        if score == 0 and self.enable_ml:
            self.training_data.append([vibration, tilt, strain])
            if len(self.training_data) == self.training_threshold and not self.ml_trained:
                self.train_ml_model()

        # 4. Scoring and Classification
        score = min(score, 100)
        
        if score >= 70:
            classification = "CRITICAL"
        elif score >= 20:
            classification = "WARNING"
        else:
            classification = "NORMAL"
            
        explanation = " | ".join(explanations) if explanations else "Normal behavior"
        
        # 5. Prediction
        prediction = self._predict_trend(sensor_id)
        
        # 6. Update History
        self.history[sensor_id].append({"vibration": vibration, "tilt": tilt, "strain": strain})

        # 7. Persist Alerts
        for alert in alerts:
            insert_alert(
                sensor_id=sensor_id, 
                alert_type=alert["alert_type"], 
                severity=alert["severity"], 
                message=alert["message"],
                features=json.dumps(alert.get("features", {}))
            )

        return {
            "score": score,
            "classification": classification,
            "explanation": explanation,
            "prediction": prediction,
            "alerts": alerts
        }

