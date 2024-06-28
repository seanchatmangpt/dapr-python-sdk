from typing import Union, Optional, Callable


from dapr.clients.grpc._response import StateResponse


class DaprClientInterface:
    def save_state(self, store_name: str, key: str, value: Union[str, bytes, dict]):
        raise NotImplementedError

    def get_state(self, store_name: str, key: str) -> StateResponse:
        raise NotImplementedError

    def delete_state(self, store_name: str, key: str):
        raise NotImplementedError

    def publish_event(self, pubsub_name: str, topic_name: str, data: Union[str, bytes, dict]):
        raise NotImplementedError

    def subscribe(self, pubsub_name: str, topic_name: str, callback: Callable):
        raise NotImplementedError

    def trigger_subscription(self, pubsub_name: str, topic_name: str, data: Union[str, bytes, dict]):
        raise NotImplementedError
