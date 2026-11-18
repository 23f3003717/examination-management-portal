from functools import wraps
from flask import request, jsonify
def require_json(*fields):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            data=request.get_json(silent=True) or {}
            missing=[field for field in fields if data.get(field) in (None,"")]
            if missing:return jsonify(error="Missing required fields: "+", ".join(missing)),400
            return fn(*args, **kwargs)
        return wrapped
    return decorator
