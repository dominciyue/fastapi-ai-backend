from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.database import SessionLocal


def check_database_connection() -> bool:
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


def check_redis_connection() -> bool:
    settings = get_settings()

    try:
        client = Redis.from_url(settings.redis_url, socket_connect_timeout=3, socket_timeout=3)
        try:
            return bool(client.ping())
        finally:
            client.close()
    except RedisError:
        return False
