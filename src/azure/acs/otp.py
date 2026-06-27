import secrets
import redis as redis_lib

from src.azure.kv.get_secrets_from_kv import get_redis_url

_OTP_TTL = 600
_OTP_LENGTH = 6

def generate_otp() -> str:
    return str(secrets.randbelow(1_000_000)).zfill(_OTP_LENGTH)

def _key(username: str) -> str:
    return f"fp_otp:{username}"


def store_otp(username: str, otp: str) -> None:
    r = redis_lib.Redis.from_url(get_redis_url())
    try:
        r.setex(_key(username), _OTP_TTL, otp)
    finally:
        r.close()


def verify_otp(username: str, otp: str) -> bool:
    r = redis_lib.Redis.from_url(get_redis_url())
    try:
        stored = r.get(_key(username))
        if stored and stored.decode() == otp:
            r.delete(_key(username))
            return True
        return False
    finally:
        r.close()
