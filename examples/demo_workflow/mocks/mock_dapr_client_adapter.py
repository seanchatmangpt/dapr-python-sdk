from typing import Union, Optional, Callable

from dapr.clients.grpc._response import StateResponse

from interface.dapr_client_interface import DaprClientInterface


class MockDaprClient(DaprClientInterface):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.state_store = {}
        self.subscriptions = {}
        self.published_messages = []

    def save_state(self, store_name: str, key: str, value: Union[str, bytes, dict]):
        """Simulate saving state to a state store."""
        if store_name not in self.state_store:
            self.state_store[store_name] = {}
        self.state_store[store_name][key] = value

    def get_state(self, store_name: str, key: str) -> Optional[StateResponse]:
        """Simulate retrieving state from a state store."""
        data = self.state_store.get(store_name, {}).get(key, None)
        if data is not None:
            return StateResponse(data=data, etag='mock-etag', headers=())
        return None

    def delete_state(self, store_name: str, key: str):
        """Simulate deleting state from a state store."""
        if store_name in self.state_store and key in self.state_store[store_name]:
            del self.state_store[store_name][key]

    def publish_event(self, pubsub_name: str, topic_name: str, data: Union[str, bytes, dict]):
        """Simulate publishing an event to a pub/sub component."""
        if pubsub_name not in self.subscriptions:
            self.subscriptions[pubsub_name] = {}
        if topic_name not in self.subscriptions[pubsub_name]:
            self.subscriptions[pubsub_name][topic_name] = []
        self.subscriptions[pubsub_name][topic_name].append(data)
        self.published_messages.append((pubsub_name, topic_name, data))

    def get_published_messages(self):
        """Retrieve all published messages."""
        return self.published_messages

    def subscribe(self, pubsub_name: str, topic_name: str, callback: Callable):
        """Simulate subscribing to a topic."""
        if pubsub_name not in self.subscriptions:
            self.subscriptions[pubsub_name] = {}
        if topic_name not in self.subscriptions[pubsub_name]:
            self.subscriptions[pubsub_name][topic_name] = []
        self.subscriptions[pubsub_name][topic_name].append(callback)

    def trigger_subscription(self, pubsub_name: str, topic_name: str, data: Union[str, bytes, dict]):
        """Simulate triggering a subscription callback."""
        if pubsub_name in self.subscriptions and topic_name in self.subscriptions[pubsub_name]:
            for callback in self.subscriptions[pubsub_name][topic_name]:
                callback(data)