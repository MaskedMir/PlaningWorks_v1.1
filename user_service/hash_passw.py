import hashlib
import os

salt = b'\xb7t\xc4\xdb\xf5\x92\xb5\x0b\x95\x81\xea.0\x94\x19\xf1#\xe5\xc2\xcc\xa3\x1eV\xa9\x03y?|\xfd\xa1\xc7\x93'

def hpassw(password):
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return key

def check_hash_key(password):
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return key