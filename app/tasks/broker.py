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

# Import actors after broker is set to ensure they are registered
# This prevents "actor not registered" errors when consuming messages
import app.tasks.hl7_processor  # noqa: F401

# Prometheus middleware is enabled by default in Dramatiq 1.15.0, it binds to ports 9191/9200
# To disable in production: set DRAMATIQ_PROMETHEUS_PORT env var to a different value or -1
