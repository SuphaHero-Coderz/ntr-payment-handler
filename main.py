import os
import logging as LOG
import json
import uuid
import requests

from dotenv import load_dotenv
from src.models import Payment
from src.redis import RedisResource, Queue
from src.exceptions import InsufficientFundsError
import src.db_services as _services

load_dotenv()

REDIS_QUEUE_LOCATION = os.getenv("REDIS_QUEUE", "localhost")
PAYMENT_QUEUE_NAME = os.getenv("PAYMENT_QUEUE_NAME")

QUEUE_NAME = f"queue:{PAYMENT_QUEUE_NAME}"
INSTANCE_NAME = uuid.uuid4().hex

LOG.basicConfig(
    level=LOG.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def watch_queue(redis_conn, queue_name, callback_func, timeout=30):
    """
    Listens to queue `queue_name` and passes messages to `callback_func`
    """
    active = True

    while active:
        # Fetch a json-encoded task using a blocking (left) pop
        packed = redis_conn.blpop([queue_name], timeout=timeout)

        if not packed:
            # if nothing is returned, poll a again
            continue

        _, packed_task = packed

        # If it's treated to a poison pill, quit the loop
        if packed_task == b"DIE":
            active = False
        else:
            task = None
            try:
                task = json.loads(packed_task)
            except Exception:
                LOG.exception("json.loads failed")
                data = {"status": -1, "message": "An error occurred"}
                redis_conn.publish(PAYMENT_QUEUE_NAME, json.dumps(data))
            if task:
                callback_func(task)
                data = {"status": 1, "message": "Successfully chunked video"}
                redis_conn.publish(PAYMENT_QUEUE_NAME, json.dumps(task))


def create_payment(
    order_id: int, user_id: int, num_tokens: int, user_credits: int
) -> None:
    """
    Creates a payment object in the database

    Args:
        order_id (int): order id
        user_id (int): user id
        num_tokens (int): number of tokens ordered
        user_credits (int): money of user

    Raises:
        InsufficientFundsError: user brok
    """
    if user_credits < num_tokens:
        raise InsufficientFundsError

    payment: Payment = Payment(
        user_id=user_id, order_id=order_id, payment_amount=num_tokens
    )

    LOG.info("Creating payment")
    _services.create_payment(payment)


def update_order_status(order_id: int, status: str, status_message: str):
    """
    Sends a request to update order status in order service

    Args:
        order_id (int): order id to update
        status (str): status message
    """
    LOG.info(f"Updating status for order with id {order_id}: {status}")
    requests.put(
        "http://order-handler/update-order-status",
        params={
            "order_id": order_id,
            "status": status,
            "status_message": status_message,
        },
    )


def add_user_funds(user_id: int, num_credits: int):
    """
    Sends a request to increment user funds in backend

    Args:
        user_id (int): user id to add credits from
        num_credits (int): amount to add
    """
    LOG.info(f"Adding {num_credits} credits to user {user_id}")
    requests.put(
        "http://backend/add-credits",
        params={"user_id": user_id, "num_credits": num_credits},
    )


def deduct_user_funds(user_id: int, num_credits: int):
    """
    Sends a request to deduct user funds in backend

    Args:
        user_id (int): user id to deduct credits from
        num_credits (int): amount to deduct
    """
    LOG.info(f"Deducting {num_credits} credits from user {user_id}")
    requests.put(
        "http://backend/deduct-credits",
        params={"user_id": user_id, "num_credits": num_credits},
    )


def rollback(order_id: int, user_id: int, num_tokens: int):
    """
    Rolls back changes made

    Args:
        order_id (int): order id
        user_id (int): user id
        num_tokens (int): number of tokens
    """
    LOG.warning(f"Rolling back for order id {order_id}")
    create_payment(
        order_id=order_id, user_id=user_id, num_tokens=-num_tokens, user_credits=777
    )
    add_user_funds(user_id, num_tokens)


def process_message(data):
    """
    Processes an incoming message from the work queue
    """
    try:
        if data["task"] == "rollback":
            rollback(data["order_id"], data["user_id"], data["num_tokens"])
        else:
            order_id: int = data["order_id"]
            user_id: int = data["user_id"]
            num_tokens: int = data["num_tokens"]
            user_credits: int = data["user_credits"]

            create_payment(
                order_id=order_id,
                user_id=user_id,
                num_tokens=num_tokens,
                user_credits=user_credits,
            )

            # TODO ! Add error checking
            deduct_user_funds(user_id=user_id, num_credits=num_tokens)

            update_order_status(
                order_id=order_id, status="payment", status_message="Payment successful"
            )

            LOG.info("Pushing to inventory queue")
            RedisResource.push_to_queue(Queue.inventory_queue, data)
    except Exception as e:
        LOG.error("ERROR OCCURED! ", e.message)
        update_order_status(
            order_id=order_id, status="failed", status_message=e.message
        )


def main():
    LOG.info("Starting a worker...")
    LOG.info("Unique name: %s", INSTANCE_NAME)
    named_logging = LOG.getLogger(name=INSTANCE_NAME)
    named_logging.info("Trying to connect to %s", REDIS_QUEUE_LOCATION)
    named_logging.info("Listening to queue: %s", QUEUE_NAME)

    redis_conn = RedisResource.get_connection()

    watch_queue(redis_conn, QUEUE_NAME, process_message)


if __name__ == "__main__":
    _services.create_database()
    main()
