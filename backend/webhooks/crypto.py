import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

PREFIX = 'enc:'


def _fernet() -> Fernet:
    key_material = getattr(settings, 'WEBHOOK_SECRET_KEY', '') or settings.SECRET_KEY
    key = base64.urlsafe_b64encode(hashlib.sha256(key_material.encode('utf-8')).digest())
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    if not value or value.startswith(PREFIX):
        return value
    token = _fernet().encrypt(value.encode('utf-8'))
    return PREFIX + token.decode('utf-8')


def decrypt_secret(value: str) -> str:
    if not value:
        return ''
    if value.startswith(PREFIX):
        try:
            token = _fernet().decrypt(value[len(PREFIX):].encode('utf-8'))
        except InvalidToken:
            return ''
        return token.decode('utf-8')
    return value
