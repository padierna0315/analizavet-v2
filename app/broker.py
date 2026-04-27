"""
Broker Configuration — Phase 15

Dramatiq + Redis broker setup. Loaded once at application startup.
"""

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from app.config import settings

# Get Redis URL from Dynaconf config (falls back to localhost)
redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")

# Setup broker
redis_broker = RedisBroker(url=redis_url)
dramatiq.set_broker(redis_broker)
