import asyncio
import json
from .database import SessionLocal, engine
from .models import SensorData, Base
import aio_pika
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Ensure tables are created
Base.metadata.create_all(bind=engine)

# RabbitMQ settings
RABBITMQ_URL = "amqp://guest:guest@<queue-pi-ip>:5672/"
QUEUE_NAME = "sensor_data_queue"


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
                async with message.process():
                    try:
                        data = json.loads(message.body.decode())
                        logging.info(f"Received data: {data}")

                        # Save to database
                        db = SessionLocal()
                        sensor_entry = SensorData(
                            pi_id=data["pi_id"],
                            sensor_type=data["sensor_type"],
                            value=data["value"],
                            timestamp=data["timestamp"]
                        )
                        db.add(sensor_entry)
                        db.commit()
                        db.refresh(sensor_entry)
                        db.close()
                        logging.info(f"Saved data to DB: {sensor_entry}")
                    except Exception as e:
                        logging.error(f"Failed to process message: {e}")


if __name__ == "__main__":
    asyncio.run(consume())
