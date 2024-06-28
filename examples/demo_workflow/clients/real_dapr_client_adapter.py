from typing import Union, Optional, Callable

from dapr.clients import DaprClient
from dapr.clients.grpc._response import StateResponse

from interface.dapr_client_interface import DaprClientInterface


class RealDaprClientAdapter(DaprClientInterface):
    def __init__(self, dapr_client: DaprClient):
        self.dapr_client = dapr_client

    def save_state(self, store_name: str, key: str, value: Union[str, bytes, dict]):
        self.dapr_client.save_state(store_name, key, value)

    def get_state(self, store_name: str, key: str) -> StateResponse:
        return self.dapr_client.get_state(store_name, key)

    def delete_state(self, store_name: str, key: str):
        self.dapr_client.delete_state(store_name, key)

    def publish_event(self, pubsub_name: str, topic_name: str, data: Union[str, bytes, dict]):
        self.dapr_client.publish_event(pubsub_name, topic_name, data)

    def subscribe(self, pubsub_name: str, topic_name: str, callback: Callable):
        # This will depend on how you handle subscriptions in your real client
        raise NotImplementedError("Real client subscription handling is not implemented")

    def trigger_subscription(self, pubsub_name: str, topic_name: str, data: Union[str, bytes, dict]):
        raise NotImplementedError("Real client subscription triggering is not implemented")
