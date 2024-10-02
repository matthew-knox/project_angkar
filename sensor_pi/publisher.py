import asyncio
import aio_pika
import json
import random
from datetime import datetime

# RabbitMQ settings
# TODO: replace <queue-pi-ip> with actual ip
RABBITMQ_URL = "amqp://guest:guest@<queue-pi-ip>:5672/"
QUEUE_NAME = "sensor_data_queue"


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
            print(f"Published: {sensor_data_temp}")

            # Publish humidity data
            await channel.default_exchange.publish(
                aio_pika.Message(body=json.dumps(sensor_data_humidity).encode()),
                routing_key=queue.name,
            )
            print(f"Published: {sensor_data_humidity}")

            await asyncio.sleep(5)  # Send data every 5 seconds


if __name__ == "__main__":
    pi_id = "sensor-pi-01"  # Unique identifier for the Sensor Pi
    asyncio.run(publish_sensor_data(pi_id))
