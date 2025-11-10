"""
Rate limiting implementation using slowapi
Protege contra brute force e DDoS
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from functools import wraps

limiter = Limiter(key_func=get_remote_address)

def rate_limit(limit_string: str):
    """
    Decorator para aplicar rate limit a um endpoint
    Uso: @rate_limit("5/minute")
    
    Formatos suportados:
    - "5/minute" - 5 requisições por minuto
    - "10/hour" - 10 requisições por hora
    - "100/day" - 100 requisições por dia
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return limiter.limit(limit_string)(wrapper)
    return decorator
