"""
Simple in-memory cache for frequently accessed data.
Caches data by health unit and filters to reduce database load.
"""
import time
from functools import wraps
import hashlib
import json

_cache = {}
_cache_ttl = 300  # 5 minutes

def _make_key(*args, **kwargs):
    """Create a cache key from function arguments."""
    key_data = json.dumps({'args': [str(a) for a in args], 'kwargs': {k: str(v) for k, v in sorted(kwargs.items())}}, sort_keys=True)
    return hashlib.md5(key_data.encode()).hexdigest()

def cached(ttl=_cache_ttl):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{_make_key(*args, **kwargs)}"
            now = time.time()
            
            if cache_key in _cache:
                value, timestamp = _cache[cache_key]
                if now - timestamp < ttl:
                    return value
            
            result = func(*args, **kwargs)
            _cache[cache_key] = (result, now)
            return result
        return wrapper
    return decorator

def clear_cache():
    """Clear all cached data."""
    global _cache
    _cache = {}

def clear_expired():
    """Remove expired entries from cache."""
    global _cache
    now = time.time()
    _cache = {k: v for k, v in _cache.items() if now - v[1] < _cache_ttl}

def get_cache_stats():
    """Get cache statistics."""
    return {
        'entries': len(_cache),
        'keys': list(_cache.keys())[:10]
    }
