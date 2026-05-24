import redis.asyncio as redis

from hang.schemas.config import conf


redis_client = redis.Redis(
    host=conf.REDIS_HOST,
    port=conf.REDIS_PORT,
    decode_responses=True,
)
