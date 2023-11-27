import redis
import os
import json

from enum import Enum
from dotenv import load_dotenv
from typing import Dict

load_dotenv()


class Queue(Enum):
    order_queue = f'queue:{os.getenv("ORDER_QUEUE_NAME")}'
    payment_queue = f'queue:{os.getenv("PAYMENT_QUEUE_NAME")}'
    inventory_queue = f'queue:{os.getenv("INVENTORY_QUEUE_NAME")}'


class RedisResource:
    REDIS_QUEUE_LOCATION = os.getenv("REDIS_QUEUE", "localhost")

    host, *port_info = REDIS_QUEUE_LOCATION.split(":")
    port = tuple()

    if port_info:
        port, *_ = port_info
        port = (int(port),)

    conn = redis.Redis(host=host, *port)

    def push_to_queue(queue: Queue, data: Dict):
        RedisResource.conn.rpush(queue.value, json.dumps(data))

    def get_connection() -> redis.Redis:
        return RedisResource.conn
