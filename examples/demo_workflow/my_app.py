import asyncio
import json
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Body
from pydantic import BaseModel
from faker import Faker
from dapr.aio.clients import DaprClient

# Define models
class RawEventModel(BaseModel):
    body: str

class User(BaseModel):
    id: int
    name: str = 'Jane Doe'

class CloudEventModel(BaseModel):
    data: User
    datacontenttype: str
    id: str
    pubsubname: str
    source: str
    specversion: str
    topic: str
    traceid: str
    traceparent: str
    tracestate: str
    type: str

# Initialize app and Dapr client
app = FastAPI()
fake = Faker()
pubsub_events = []

# Define event handlers
@app.post("/events/pubsub/any_topic")
async def any_event_handler(event_data: dict = Body(...)):
    pubsub_events.append(event_data)
    print(f"Received any_topic event: {event_data}")
    return {"status": "ok"}

@app.post("/events/pubsub/cloud_topic")
async def cloud_event_handler(event_data: CloudEventModel):
    pubsub_events.append(event_data.dict())
    print(f"Received cloud_topic event: {event_data}")
    return {"status": "ok"}

@app.post("/events/pubsub/raw_topic")
async def raw_event_handler(event_data: RawEventModel):
    pubsub_events.append(event_data.dict())
    print(f"Received raw_topic event: {event_data}")
    return {"status": "ok"}

@app.get("/")
def read_root():
    return pubsub_events

@app.post("/send_event/{topic}")
async def send_event(topic: str):
    message = {
        'name': fake.name(),
        'address': fake.address(),
        'text': fake.text()
    }
    async with DaprClient() as client:
        await client.publish_event(
            pubsub_name='pubsub',
            topic_name=topic,
            data=json.dumps(message),
        )
    return {"message": f"Event sent to topic {topic}", "data": message}

@app.get("/dapr/subscribe")
async def subscribe():
    subscriptions = [
        {
            "pubsubname": "pubsub",
            "topic": "any_topic",
            "route": "/events/pubsub/any_topic"
        },
        {
            "pubsubname": "pubsub",
            "topic": "cloud_topic",
            "route": "/events/pubsub/cloud_topic"
        },
        {
            "pubsubname": "pubsub",
            "topic": "raw_topic",
            "route": "/events/pubsub/raw_topic"
        }
    ]
    return subscriptions

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Dapr client")
    yield
    print("Dapr client closed")

app.router.lifespan_context = lifespan

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=30212)
