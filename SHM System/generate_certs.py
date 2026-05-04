"""
TLS Certificate Generator for Secure IoT SHM System
=====================================================
Generates a self-signed CA certificate and server certificate
for securing MQTT communication with TLS encryption.

Usage:
    python generate_certs.py
"""

import os
import datetime
import ipaddress
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa


CERTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs")


def generate_key():
    """Generate a 2048-bit RSA private key."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def generate_ca(ca_key):
    """Generate a self-signed Certificate Authority certificate."""
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Delhi"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SHM IoT Security Lab"),
        x509.NameAttribute(NameOID.COMMON_NAME, "SHM Root CA"),
    ])

    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(ca_key, hashes.SHA256())
    )
    return ca_cert


def generate_server_cert(ca_key, ca_cert, server_key):
    """Generate a server certificate signed by the CA."""
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Delhi"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SHM IoT Security Lab"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])

    server_cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )
    return server_cert


def save_key(key, filepath):
    """Save a private key to PEM file."""
    with open(filepath, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    print(f"  ✔ Saved: {filepath}")


def save_cert(cert, filepath):
    """Save a certificate to PEM file."""
    with open(filepath, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    print(f"  ✔ Saved: {filepath}")


def main():
    os.makedirs(CERTS_DIR, exist_ok=True)
    print("\n[LOCK] Generating TLS certificates for Secure SHM system...\n")

    # --- CA ---
    print("[1/3] Generating Certificate Authority...")
    ca_key = generate_key()
    ca_cert = generate_ca(ca_key)
    save_key(ca_key, os.path.join(CERTS_DIR, "ca.key"))
    save_cert(ca_cert, os.path.join(CERTS_DIR, "ca.crt"))

    # --- Server ---
    print("\n[2/3] Generating Server certificate...")
    server_key = generate_key()
    server_cert = generate_server_cert(ca_key, ca_cert, server_key)
    save_key(server_key, os.path.join(CERTS_DIR, "server.key"))
    save_cert(server_cert, os.path.join(CERTS_DIR, "server.crt"))

    # --- Summary ---
    print("\n[3/3] Certificate generation complete!")
    print(f"\n[DIR] Certificates saved to: {CERTS_DIR}")
    print("   • ca.crt      — Root CA certificate")
    print("   • ca.key      — Root CA private key")
    print("   • server.crt  — Server certificate (signed by CA)")
    print("   • server.key  — Server private key")
    print("\n[OK] Ready for Mosquitto TLS configuration.\n")


if __name__ == "__main__":
    main()

