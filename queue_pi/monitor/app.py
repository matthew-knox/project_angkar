import logging
import os
from urllib.parse import quote

import requests
from fastapi import FastAPI, HTTPException
from prometheus_client import CONTENT_TYPE_LATEST, Gauge, generate_latest
from starlette.responses import Response

RABBITMQ_API_URL = os.getenv("RABBITMQ_API_URL", "http://localhost:15672/api")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "adminpass")
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "sensors_vhost")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "5"))

app = FastAPI(title="Queue Pi Monitor")
logging.basicConfig(level=logging.INFO)

RABBITMQ_UP = Gauge("rabbitmq_up", "RabbitMQ API reachable (1) or not (0)")
QUEUE_MESSAGES = Gauge(
    "rabbitmq_queue_messages",
    "Total messages in queue",
    ["vhost", "queue"],
)
QUEUE_MESSAGES_READY = Gauge(
    "rabbitmq_queue_messages_ready",
    "Ready messages in queue",
    ["vhost", "queue"],
)
QUEUE_MESSAGES_UNACKED = Gauge(
    "rabbitmq_queue_messages_unacked",
    "Unacked messages in queue",
    ["vhost", "queue"],
)
QUEUE_CONSUMERS = Gauge(
    "rabbitmq_queue_consumers",
    "Number of consumers",
    ["vhost", "queue"],
)


def api_get(path: str):
    base = RABBITMQ_API_URL.rstrip("/")
    url = f"{base}/{path.lstrip('/')}"
    try:
        response = requests.get(
            url,
            auth=(RABBITMQ_USER, RABBITMQ_PASS),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not response.ok:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


def update_queue_metrics(vhost: str):
    QUEUE_MESSAGES.clear()
    QUEUE_MESSAGES_READY.clear()
    QUEUE_MESSAGES_UNACKED.clear()
    QUEUE_CONSUMERS.clear()

    queues = api_get(f"queues/{quote(vhost, safe='')}")
    for queue in queues:
        name = queue.get("name", "unknown")
        QUEUE_MESSAGES.labels(vhost=vhost, queue=name).set(queue.get("messages", 0))
        QUEUE_MESSAGES_READY.labels(vhost=vhost, queue=name).set(
            queue.get("messages_ready", 0)
        )
        QUEUE_MESSAGES_UNACKED.labels(vhost=vhost, queue=name).set(
            queue.get("messages_unacknowledged", 0)
        )
        QUEUE_CONSUMERS.labels(vhost=vhost, queue=name).set(
            queue.get("consumers", 0)
        )


@app.get("/health")
def health():
    try:
        api_get("overview")
        RABBITMQ_UP.set(1)
    except HTTPException:
        RABBITMQ_UP.set(0)
        raise
    return {"status": "ok"}


@app.get("/rabbitmq/overview")
def rabbitmq_overview():
    return api_get("overview")


@app.get("/rabbitmq/queues")
def rabbitmq_queues(vhost: str = RABBITMQ_VHOST):
    return api_get(f"queues/{quote(vhost, safe='')}")


@app.get("/metrics")
def metrics():
    try:
        update_queue_metrics(RABBITMQ_VHOST)
        RABBITMQ_UP.set(1)
    except HTTPException:
        RABBITMQ_UP.set(0)
        raise
    payload = generate_latest()
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)
