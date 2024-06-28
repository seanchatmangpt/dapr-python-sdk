import asyncio
import json
from asyncio import Future
from typing import TYPE_CHECKING, Optional, TypeVar, cast
import reactivex as rx
from dspygen.rdddy.base_event import BaseEvent
from loguru import logger
from reactivex import operators as ops
from reactivex.scheduler.eventloop import AsyncIOScheduler
from dapr.clients import DaprClient

from dspygen.rdddy.base_message import BaseMessage, MessageFactory

from interface.dapr_client_interface import DaprClientInterface
from mocks.mock_dapr_client_adapter import MockDaprClient

if TYPE_CHECKING:
    from dspygen.rdddy.base_actor import BaseActor

T = TypeVar("T", bound="BaseActor")


class ActorSystem:
    def __init__(self,
                 loop: Optional[asyncio.AbstractEventLoop] = None,
                 dapr_client: Optional[DaprClientInterface] = None):
        self.dapr_client = dapr_client or DaprClient()
        self.actors: dict[int, BaseActor] = {}
        self.loop = loop if loop is not None else asyncio.get_event_loop()
        self.scheduler = AsyncIOScheduler(loop=self.loop)
        self.event_stream = rx.subject.Subject()
        self.subscriptions = {}  # Store subscriptions for cleanup

    async def actor_of(self, actor_class, **kwargs) -> T:
        actor = actor_class(self, **kwargs)
        self.actors[actor.actor_id] = actor
        await actor.start(self.scheduler)
        return actor

    async def actors_of(self, actor_classes, **kwargs) -> list[T]:
        actors = []
        for actor_class in actor_classes:
            actor = await self.actor_of(actor_class, **kwargs)
            actors.append(actor)
        return actors

    async def publish(self, message: "BaseMessage"):
        logger.debug(f"Publishing message: {message}")
        if type(message) is BaseMessage:
            raise ValueError("The base Message class should not be used directly. Please use a subclass of Message.")
        self.event_stream.on_next(message)
        actors = list(self.actors.values())
        for actor in actors:
            await self.send(actor.actor_id, message)
        self.dapr_client.publish_event(
            pubsub_name="pubsub",
            topic_name="actor_system/publish",
            data=message.model_dump_json()
        )

    async def remove_actor(self, actor_id):
        actor = self.actors.pop(actor_id, None)
        if actor:
            logger.debug(f"Removing actor {actor_id}")
        else:
            logger.debug(f"Actor {actor_id} not found for removal")
        logger.debug(f"Current actors count: {len(self.actors)}")

    async def send(self, actor_id: int, message: "BaseMessage"):
        actor = self.actors.get(actor_id)
        if actor:
            actor.mailbox.on_next(message)
            await asyncio.sleep(0)
        else:
            logger.debug(f"Actor {actor_id} not found.")

    async def wait_for_message(self, message_type: type) -> Future["BaseMessage"]:
        loop = asyncio.get_event_loop()
        future = loop.create_future()

        def on_next(msg):
            if isinstance(msg, message_type):
                future.set_result(msg)
                subscription.dispose()

        subscription = self.event_stream.pipe(
            ops.filter(lambda msg: isinstance(msg, message_type))
        ).subscribe(on_next)

        return await future

    def __getitem__(self, actor_id) -> T:
        return cast(T, self.actors.get(actor_id))

    async def subscribe(self, topic_name: str):
        self.dapr_client.subscribe(
            pubsub_name="pubsub",
            topic_name=topic_name,
            callback=self.on_message
        )

    async def on_message(self, message: BaseMessage):
        logger.debug(f"Received message: {message}")
        # payload_dict = json.loads(message["data"])
        # msg = MessageFactory.create_message(payload_dict)
        self.event_stream.on_next(BaseMessage)
        actors = list(self.actors.values())
        for actor in actors:
            await self.send(actor.actor_id, message)

    async def shutdown(self):
        logger.debug("Actor system shutdown complete.")


import asyncio


async def main():
    from clients.real_dapr_client_adapter import RealDaprClientAdapter
    actor_system = ActorSystem(dapr_client=RealDaprClientAdapter(dapr_client=DaprClient()))
    await actor_system.subscribe("actor_system/publish")
    print("Subscribed to actor_system/publish")

    from mocks.mock_actor import MockActor
    await actor_system.actor_of(MockActor)

    await asyncio.sleep(1)

    await actor_system.publish(BaseEvent(content="Hello"))


if __name__ == "__main__":
    asyncio.run(main())
