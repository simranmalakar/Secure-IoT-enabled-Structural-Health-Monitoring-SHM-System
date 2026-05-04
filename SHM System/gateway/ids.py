"""
Intrusion Detection System (IDS) — Secure IoT SHM Gateway
============================================================
Monitors for security threats:
  - Hash integrity failures (spoofed packets)
  - DoS flooding (rate limiting per sensor)
  - Unauthorized access attempts
"""

import time
import json
import hashlib
import hmac
from collections import defaultdict, deque

from gateway.db import insert_security_log
from sensor_simulator.config import HMAC_SECRET


# --- IDS Configuration ---
DOS_WINDOW = 5          # seconds
DOS_THRESHOLD = 20      # max messages per window per sensor
HASH_FAIL_ALERT = 3     # alert after N consecutive hash failures


class IntrusionDetector:
    """Monitors for security threats in MQTT traffic."""

    def __init__(self):
        self.message_timestamps = defaultdict(list)

        # Hash failure tracking: {sensor_id: consecutive_failures}
        self.hash_failures = defaultdict(int)

        # Replay attack tracking: store last 1000 packet IDs
        self.seen_packets = deque(maxlen=1000)

        # Stats
        self.total_spoofed = 0
        self.total_dos_events = 0
        self.total_replay = 0

    def verify_hash(self, payload: dict) -> bool:
        """Verify the SHA-256 HMAC of a sensor packet.

        Returns True if hash is valid, False if spoofed.
        """
        received_hash = payload.get("hash", "")

        # Recompute HMAC from payload data (excluding hash field)
        data_str = json.dumps(
            {k: v for k, v in payload.items() if k != "hash"},
            sort_keys=True,
        )
        expected_hash = hmac.new(
            HMAC_SECRET.encode(),
            data_str.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(received_hash, expected_hash)

    def check_spoofing(self, sensor_id: str, payload: dict) -> bool:
        """Check if a packet has been tampered with.

        Returns True if packet is spoofed (hash mismatch).
        """
        if self.verify_hash(payload):
            # Reset consecutive failure count on valid hash
            self.hash_failures[sensor_id] = 0
            return False

        # Hash mismatch — potential spoofing
        self.hash_failures[sensor_id] += 1
        self.total_spoofed += 1

        severity = "CRITICAL" if self.hash_failures[sensor_id] >= HASH_FAIL_ALERT else "HIGH"

        insert_security_log(
            event_type="SPOOFED_PACKET",
            source=sensor_id,
            details=(
                f"SHA-256 HMAC verification failed. "
                f"Consecutive failures: {self.hash_failures[sensor_id]}. "
                f"Received hash: {payload.get('hash', 'MISSING')[:16]}..."
            ),
            severity=severity,
        )

        print(f"  [!] IDS: Spoofed packet from {sensor_id} "
              f"(failure #{self.hash_failures[sensor_id]})")

        return True

    def check_dos(self, sensor_id: str) -> bool:
        """Check for DoS flooding from a sensor.

        Returns True if rate limit exceeded.
        """
        now = time.time()
        timestamps = self.message_timestamps[sensor_id]

        # Prune timestamps outside the window
        self.message_timestamps[sensor_id] = [
            ts for ts in timestamps if now - ts < DOS_WINDOW
        ]
        self.message_timestamps[sensor_id].append(now)

        msg_count = len(self.message_timestamps[sensor_id])

        if msg_count > DOS_THRESHOLD:
            self.total_dos_events += 1

            insert_security_log(
                event_type="DOS_ATTACK",
                source=sensor_id,
                details=(
                    f"Rate limit exceeded: {msg_count} messages in "
                    f"{DOS_WINDOW}s window (threshold: {DOS_THRESHOLD})"
                ),
                severity="CRITICAL",
            )

            print(f"  [!] IDS: DoS detected from {sensor_id} "
                  f"({msg_count} msgs/{DOS_WINDOW}s)")

            return True

        return False

    def check_replay(self, sensor_id: str, payload: dict) -> bool:
        """Check for replay attacks using packet_id."""
        packet_id = payload.get("packet_id")
        if not packet_id:
            return False  # Ignore if no packet_id

        if packet_id in self.seen_packets:
            self.total_replay += 1
            insert_security_log(
                event_type="REPLAY_ATTACK",
                source=sensor_id,
                details=f"Duplicate packet ID detected: {packet_id}",
                severity="HIGH",
            )
            print(f"  [!] IDS: Replay attack detected from {sensor_id}")
            return True

        self.seen_packets.append(packet_id)
        return False

    def log_unauthorized_access(self, source: str, details: str):
        """Log an unauthorized API access attempt."""
        insert_security_log(
            event_type="UNAUTHORIZED_ACCESS",
            source=source,
            details=details,
            severity="MEDIUM",
        )
        print(f"  [!] IDS: Unauthorized access from {source}")

    def process(self, sensor_id: str, payload: dict) -> dict:
        """Run all IDS checks on an incoming packet.

        Returns a dict with check results:
            {"spoofed": bool, "dos": bool, "passed": bool}
        """
        is_spoofed = self.check_spoofing(sensor_id, payload)
        is_dos = self.check_dos(sensor_id)
        is_replay = self.check_replay(sensor_id, payload)

        return {
            "spoofed": is_spoofed,
            "dos": is_dos,
            "replay": is_replay,
            "passed": not is_spoofed and not is_dos and not is_replay,
        }

    def get_stats(self) -> dict:
        """Return IDS statistics."""
        return {
            "total_spoofed_packets": self.total_spoofed,
            "total_dos_events": self.total_dos_events,
            "total_replay_events": self.total_replay,
            "tracked_sensors": len(self.message_timestamps),
        }

