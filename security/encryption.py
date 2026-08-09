"""
Triple AES-256-GCM encryption module.
"""
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes


def _derive_three_keys(master_key: bytes) -> tuple:
    info_strings = [b"aes256_layer_1_key", b"aes256_layer_2_key", b"aes256_layer_3_key"]
    keys = []
    for info in info_strings:
        hkdf = HKDF(algorithm=hashes.SHA512(), length=32, salt=None, info=info)
        keys.append(hkdf.derive(master_key))
    return tuple(keys)


def encrypt_data(plaintext: str, master_key: bytes) -> str:
    if not plaintext:
        return ""
    k1, k2, k3 = _derive_three_keys(master_key)
    data = plaintext.encode("utf-8")
    nonce1 = os.urandom(12)
    enc1 = AESGCM(k1).encrypt(nonce1, data, None)
    blob1 = nonce1 + enc1
    nonce2 = os.urandom(12)
    enc2 = AESGCM(k2).encrypt(nonce2, blob1, None)
    blob2 = nonce2 + enc2
    nonce3 = os.urandom(12)
    enc3 = AESGCM(k3).encrypt(nonce3, blob2, None)
    blob3 = nonce3 + enc3
    return base64.b64encode(blob3).decode("utf-8")


def decrypt_data(ciphertext: str, master_key: bytes) -> str:
    if not ciphertext:
        return ""
    k1, k2, k3 = _derive_three_keys(master_key)
    data = base64.b64decode(ciphertext.encode("utf-8"))
    nonce3 = data[:12]
    blob2 = AESGCM(k3).decrypt(nonce3, data[12:], None)
    nonce2 = blob2[:12]
    blob1 = AESGCM(k2).decrypt(nonce2, blob2[12:], None)
    nonce1 = blob1[:12]
    plaintext_bytes = AESGCM(k1).decrypt(nonce1, blob1[12:], None)
    return plaintext_bytes.decode("utf-8")
