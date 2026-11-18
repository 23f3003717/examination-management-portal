import json
from functools import wraps
from flask import current_app
try:
    import redis
except ImportError:
    redis = None

def get_client():
    if redis is None:
        return None
    try:
        client = redis.Redis.from_url(current_app.config["REDIS_URL"], decode_responses=True, socket_connect_timeout=1)
        client.ping()
        return client
    except Exception:
        return None

def cached(key, ttl=None):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            client = get_client()
            if client:
                try:
                    value = client.get(key)
                    if value:
                        return json.loads(value)
                except Exception:
                    pass
            result = fn(*args, **kwargs)
            if client:
                try:
                    client.setex(key, ttl or current_app.config["CACHE_TTL"], json.dumps(result))
                except Exception:
                    pass
            return result
        return wrapper
    return deco

def invalidate(prefixes=("exams:", "schedules:", "rubrics:")):
    client = get_client()
    if not client:
        return
    try:
        for prefix in prefixes:
            for key in client.scan_iter(match=prefix + "*"):
                client.delete(key)
    except Exception:
        pass
