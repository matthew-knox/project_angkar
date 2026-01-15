import asyncio
import aio_pika
import json
import logging
import os
import random
from datetime import datetime

# RabbitMQ settings
RABBITMQ_URL = os.getenv("SENSOR_PI_RABBITMQ_URL")
if not RABBITMQ_URL:
    raise RuntimeError("SENSOR_PI_RABBITMQ_URL must be set")
QUEUE_NAME = os.getenv("SENSOR_PI_QUEUE_NAME", "sensor_data_queue")
PUBLISH_INTERVAL_SECONDS = float(os.getenv("SENSOR_PI_INTERVAL_SECONDS", "5"))


async def publish_sensor_data(pi_id: str):
    # Establish connection
    connection = await aio_pika.connect_robust(RABBITMQ_URL)

    async with connection:
        # Creating a channel
        channel = await connection.channel()

        # Declaring queue
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)

        while True:
            # Simulate sensor data
            temperature = round(random.uniform(20.0, 30.0), 2)
            humidity = round(random.uniform(30.0, 60.0), 2)
            timestamp = datetime.utcnow().isoformat()

            # Create sensor data messages
            sensor_data_temp = {
                "pi_id": pi_id,
                "sensor_type": "temperature",
                "value": temperature,
                "timestamp": timestamp
            }

            sensor_data_humidity = {
                "pi_id": pi_id,
                "sensor_type": "humidity",
                "value": humidity,
                "timestamp": timestamp
            }

            # Publish temperature data
            await channel.default_exchange.publish(
                aio_pika.Message(body=json.dumps(sensor_data_temp).encode()),
                routing_key=queue.name,
            )
            logging.info("Published: %s", sensor_data_temp)

            # Publish humidity data
            await channel.default_exchange.publish(
                aio_pika.Message(body=json.dumps(sensor_data_humidity).encode()),
                routing_key=queue.name,
            )
            logging.info("Published: %s", sensor_data_humidity)

            await asyncio.sleep(PUBLISH_INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pi_id = os.getenv("SENSOR_PI_ID", "sensor-pi-01")
    asyncio.run(publish_sensor_data(pi_id))
