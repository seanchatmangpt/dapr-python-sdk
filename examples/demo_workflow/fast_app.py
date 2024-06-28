import asyncio
import os
import asyncio
import json
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Body
from pydantic import BaseModel
from faker import Faker
from dapr.aio.clients import DaprClient


import uvicorn
from dapr.clients import DaprClient
from dspygen.rdddy.base_actor import BaseActor
from dspygen.rdddy.base_message import BaseMessage, TerminationMessage, ExceptionMessage
from fastapi import FastAPI, Body
from pydantic import BaseModel

from actors.dapr_actor_system import ActorSystem

"""
This module provides the subscribe decorator to be used in combination with a route generator
to create subscriptions to Dapr pubsub topics with FastAPI.
"""
import logging
from typing import Optional, Dict, Any, List, Union

from fastapi import FastAPI, APIRouter


def subscribe(
    app: Union[FastAPI, APIRouter],
    path: str,
    pubsub: str,
    topic: str,
    *args,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, str]] = None,
    dead_letter_topic: Optional[str] = None,
    openapi_extra: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> callable:
    """
    A decorator used in combination with a route generator to create subscriptions to Dapr pubsub topics with FastAPI.

    Args:
        app (Union[FastAPI, APIRouter]): The FastAPI or APIRouter application.
        path (str): The endpoint path.
        pubsub (str): The pubsub name.
        topic (str): The topic name.
        tags (Optional[List[str]]): Optional tags for the endpoint.
        metadata (Optional[Dict[str, str]]): Optional metadata.
        dead_letter_topic (Optional[str]): Optional dead letter topic.
        openapi_extra (Optional[Dict[str, Any]]): Optional extra OpenAPI info.

    Returns:
        callable: The decorator.
    """
    if metadata is None:
        metadata = {}

    if openapi_extra is None:
        openapi_extra = {}

    if not isinstance(app, (FastAPI, APIRouter)):
        raise TypeError('Expected FastAPI or APIRouter instance for "app"')
    if not isinstance(path, str):
        raise TypeError('Expected string for "path"')
    if not isinstance(pubsub, str):
        raise TypeError('Expected string for "pubsub"')
    if not isinstance(topic, str):
        raise TypeError('Expected string for "topic"')
    if tags is not None and not isinstance(tags, list):
        raise TypeError('Expected list for "tags"')
    if dead_letter_topic is not None and not isinstance(dead_letter_topic, str):
        raise TypeError('Expected string for "dead_letter_topic"')

    def decorator(func):
        openapi_extra["dapr"] = {
            "pubsubname": pubsub,
            "topic": topic,
            "metadata": metadata,
            **(
                {"deadLetterTopic": dead_letter_topic}
                if dead_letter_topic is not None
                else {}
            ),
        }

        app.add_api_route(
            path=path,
            endpoint=func,
            methods=["POST"],
            tags=tags,
            openapi_extra=openapi_extra,
            *args,
            **kwargs,
        )

        return func

    return decorator


# pylint: disable=R0903
class DaprFastAPI:
    """
    Class to handle Dapr subscriptions and the FastAPI application.
    """

    def __init__(self, remove_dapr_data: bool = False):
        self.remove_dapr_data = remove_dapr_data
        self._subscriptions = []

    def _get_subscriptions(self):
        return self._subscriptions

    def _extract_subscriptions(self, app: FastAPI) -> List[Dict[str, Any]]:
        route_info = []

        for route in app.routes:
            if hasattr(route, "openapi_extra") is False:
                logging.info(f"Skipping route {route.path} as it has no openapi_extra")
                continue

            if route.openapi_extra is None:
                logging.info(f"Skipping route {route.path} as it has no openapi_extra")
                continue

            if "dapr" not in route.openapi_extra:
                logging.info(f"Skipping route {route.path} as it has no dapr info")
                continue

            logging.info(f"Extracting route {route.path} as it has dapr info")

            dapr_info = route.openapi_extra["dapr"]
            info = {
                "pubsubname": dapr_info["pubsubname"],
                "topic": dapr_info["topic"],
                "route": route.path,
                "metadata": dapr_info["metadata"],
            }

            route_info.append(info)

            if self.remove_dapr_data:
                del route.openapi_extra["dapr"]

        self._subscriptions.extend(route_info)

        return self._subscriptions

    def generate_subscribe_route(self, app: FastAPI):
        """
        Generates the /dapr/subscribe route in the FastAPI app.
        """
        self._extract_subscriptions(app)

        app.add_api_route(
            path="/dapr/subscribe",
            endpoint=self._get_subscriptions,
            methods=["GET"],
        )

app = FastAPI()
dapr = DaprFastAPI()


# Define models
class RawEventModel(BaseModel):
    body: str


class User(BaseModel):
    id: int
    name: str = 'Jane Doe'


@subscribe(app=app, path="/test", pubsub="pubsub", topic="test_topic")
def test_endpoint():
    print("Test endpoint")


# Define event handlers
@subscribe(app, "/any", "pubsub", "any_topic")
async def any_event_handler(event_data: dict = Body(...)):
    print(f"Received any_topic event: {event_data}")


class CloudActor(BaseActor):
    def __init__(self, asys, **kwargs):
        super().__init__(asys, **kwargs)
        print(f"CloudActor {self.actor_id} initialized.")

    async def handle_terminate(self, message: TerminationMessage):
        print(f"Actor {self.actor_id} received termination message.")
        await self.publish(ExceptionMessage())
        print(f"Actor {self.actor_id} published exception message.")


@subscribe(app, "/cloud", "pubsub", "cloud_topic")
async def cloud_event_handler(message: BaseMessage):
    # print(f"Received cloud_topic event: {event_data}")
    # print(f"Received cloud_topic event: {message}")
    actor_system = ActorSystem()

    # print(f"Received cloud_topic event: {message}")

    print("Creating cloud actor...")

    actor = await actor_system.actor_of(CloudActor)

    print("Cloud actor created.")

    await actor_system.on_message(TerminationMessage())

    print("Termination message sent.")

    await actor_system.wait_for_message(ExceptionMessage)

    print("Exception message received.")

    print("Actor system shutdown in progress...")

    # await asyncio.sleep(10)

    # await actor_system.shutdown()


@subscribe(app, "/raw", "pubsub", "raw_topic")
async def raw_event_handler(event_data: RawEventModel):
    print(f"Received raw_topic event: {event_data}")




# Set up required inputs for http client to perform service invocation
base_url = os.getenv('DAPR_HTTP_ENDPOINT', 'http://localhost')
dapr_api_token = os.getenv('DAPR_API_TOKEN', '')
pubsub_name = os.getenv('PUBSUB_NAME', 'pubsub')
kvstore_name = os.getenv('KVSTORE_NAME', 'kvstore')
invoke_target_appid = os.getenv('INVOKE_APPID', 'target')


@app.get('/')
async def helloworld():
    return {"Hello World"}


class Order(BaseModel):
    orderId: int
    product: str
    quantity: int
    price: float


@app.post('/pubsub/orders')
async def publish_orders(order: Order):
    with DaprClient() as d:
        try:
            result = d.publish_event(
                pubsub_name=pubsub_name,
                topic_name='orders',
                data=order.model_dump_json(),
                data_content_type='application/json',
            )
            logging.info('Publish Successful. Order published: %s' %
                         order.orderId)
            return {'success': True}
        except grpc.RpcError as err:
            logging.error(
                f"Error occurred while publishing order: {err.code()}")


@app.post('/pubsub/neworders')
def consume_orders(event: CloudEvent):
    logging.info('Order received : %s' % event.data['orderId'])
    return {'success': True}


@app.post('/invoke/orders')
async def send_order(order: Order):
    headers = {'dapr-app-id': invoke_target_appid, 'dapr-api-token': dapr_api_token,
               'content-type': 'application/json'}
    try:
        result = requests.post(
            url='%s/invoke/neworders' % (base_url),
            data=order.model_dump_json(),
            headers=headers
        )

        if result.ok:
            logging.info('Invocation successful with status code: %s' %
                         result.status_code)
            return str(order)
        else:
            logging.error(
                'Error occurred while invoking App ID: %s' % result.reason)
            raise HTTPException(status_code=500, detail=result.reason)

    except grpc.RpcError as err:
        logging.error(f"ErrorCode={err.code()}")
        raise HTTPException(status_code=500, detail=err.details())


@app.post('/invoke/neworders')
def receive_order(order: Order):
    logging.info('Request received : ' + str(order))
    return str(order)


@app.post('/kv/orders')
def create_kv(order: Order):
    with DaprClient() as d:
        try:
            d.save_state(store_name=kvstore_name,
                         key=str(order.orderId), value=str(order))
            return {"success": True}
        except grpc.RpcError as err:
            print(f"Error={err.details()}")
            raise HTTPException(status_code=500, detail=err.details())


@app.get('/kv/orders/{orderId}')
def get_kv(orderId: int):
    with DaprClient() as d:
        try:
            kv = d.get_state(kvstore_name, str(orderId))
            return {"data": kv.data}
        except grpc.RpcError as err:
            print(f"Error={err.details()}")
            raise HTTPException(status_code=500, detail=err.details())

@app.delete('/kv/orders/{orderId}')
def delete_kv(orderId: int):
    with DaprClient() as d:
        try:
            d.delete_state(kvstore_name, str(orderId))
            return {'success': True}
        except grpc.RpcError as err:
            print(f"Error={err.details()}")
            raise HTTPException(status_code=500, detail=err.details())


dapr.generate_subscribe_route(app)

uvicorn.run(app, host="0.0.0.0", port=8000)
