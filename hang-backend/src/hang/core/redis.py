import redis.asyncio as redis
from redis.asyncio import Redis
from typing import cast, Awaitable

from hang.schemas.config import conf


redis_client: Redis = redis.Redis(
    host=conf.REDIS_HOST,
    port=conf.REDIS_PORT,
    decode_responses=True,
)


async def ping() -> bool:
    return await cast(Awaitable[bool], redis_client.ping())
