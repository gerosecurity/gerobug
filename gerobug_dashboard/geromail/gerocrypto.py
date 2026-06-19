import os
import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken


_fernet_instance = None


def _derive_key_from_secret(secret_key):
    key_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        secret_key.encode('utf-8'),
        b'gerobug-field-encryption-salt',
        iterations=480000,
        dklen=32
    )
    return base64.urlsafe_b64encode(key_bytes)


def get_fernet():
    global _fernet_instance
    if _fernet_instance is not None:
        return _fernet_instance

    env_key = os.environ.get('FIELD_ENCRYPTION_KEY', '').strip()

    if env_key:
        try:
            _fernet_instance = Fernet(env_key.encode('utf-8') if isinstance(env_key, str) else env_key)
            return _fernet_instance
        except Exception as e:
            logging.getLogger("Gerologger").error(
                f"Invalid FIELD_ENCRYPTION_KEY, falling back to SECRET_KEY derivation: {e}"
            )

    from django.conf import settings
    derived_key = _derive_key_from_secret(settings.SECRET_KEY)
    _fernet_instance = Fernet(derived_key)
    return _fernet_instance


def encrypt_value(plaintext):
    if not plaintext:
        return ''

    plaintext_str = str(plaintext)
    if not plaintext_str:
        return ''

    fernet = get_fernet()
    encrypted = fernet.encrypt(plaintext_str.encode('utf-8'))
    return encrypted.decode('utf-8')


def decrypt_value(ciphertext):
    if not ciphertext:
        return ''

    ciphertext_str = str(ciphertext)
    if not ciphertext_str:
        return ''

    fernet = get_fernet()
    try:
        decrypted = fernet.decrypt(ciphertext_str.encode('utf-8'))
        return decrypted.decode('utf-8')
    except (InvalidToken, Exception):
        return ciphertext_str


def generate_key():
    return Fernet.generate_key().decode('utf-8')
