import asyncio
import json
import os
from .db import Base, SessionLocal
from .models import SensorData
import aio_pika
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Ensure tables are created
Base.metadata.create_all(bind=engine)

# RabbitMQ settings
RABBITMQ_URL = os.getenv("CENTRAL_PI_RABBITMQ_URL")
if not RABBITMQ_URL:
    raise RuntimeError("CENTRAL_PI_RABBITMQ_URL must be set")
QUEUE_NAME = os.getenv("CENTRAL_PI_QUEUE_NAME", "sensor_data_queue")


async def consume():
    logging.info(f"Connecting to RabbitMQ at {RABBITMQ_URL}...")
    connection = await aio_pika.connect_robust(RABBITMQ_URL)

    async with connection:
        # Creating a channel
        channel = await connection.channel()

        # Declaring queue
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        logging.info(f"Listening for messages on queue: {QUEUE_NAME}...")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process(requeue=True):
                    try:
                        data = json.loads(message.body.decode())
                        logging.info(f"Received data: {data}")

                        # Save to database
                        db = SessionLocal()
                        try:
                            sensor_entry = SensorData(
                                pi_id=data["pi_id"],
                                sensor_type=data["sensor_type"],
                                value=data["value"],
                                timestamp=data["timestamp"]
                            )
                            db.add(sensor_entry)
                            db.commit()
                            db.refresh(sensor_entry)
                        except Exception:
                            db.rollback()
                            raise
                        finally:
                            db.close()

                        logging.info(f"Saved data to DB: {sensor_entry}")
                    except Exception as e:
                        logging.error(f"Failed to process message: {e}")
                        raise


if __name__ == "__main__":
    asyncio.run(consume())
