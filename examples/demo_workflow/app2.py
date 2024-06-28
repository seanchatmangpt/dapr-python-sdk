import logging
import json  # Import JSON module for serialization
import os

# from dapr.clients import DaprClient
from enum import Enum, auto
from typing import Union, Optional, Callable

from dapr.clients import DaprClient
from dspygen.mixin.fsm.fsm_mixin import FSMMixin, trigger
from transitions import MachineError



class ConversationState(Enum):
    STARTING = auto()
    GREETING = auto()
    SMALL_TALK = auto()
    ENDING = auto()


class ConversationAgent(FSMMixin):
    def __init__(self, agent_id, topic, client=None):
        super().__init__()
        self.agent_id = agent_id
        self.topic = topic
        self.state_store = "statestore-actors"
        self.dapr_client = client or DaprClient()
        self.setup_fsm(ConversationState, initial=ConversationState.STARTING)

    def save_state(self):
        self.dapr_client.save_state(store_name=self.state_store, key=self.agent_id, value=self.state)

    def publish_event(self, message):
        self.dapr_client.publish_event(
            pubsub_name="pubsub",
            topic_name=self.topic,
            data=json.dumps(message)
        )

    @trigger(source=ConversationState.STARTING, dest=ConversationState.GREETING)
    def start_conversation(self):
        print(f"{self.agent_id}: Starting conversation")
        self.save_state()
        self.publish_event({"agent": self.agent_id, "message": "Hello!"})

    @trigger(source=ConversationState.GREETING, dest=ConversationState.SMALL_TALK)
    def greet(self):
        print(f"{self.agent_id}: Greeting")
        self.save_state()
        self.publish_event({"agent": self.agent_id, "message": "How are you?"})

    @trigger(source=ConversationState.SMALL_TALK, dest=ConversationState.SMALL_TALK)
    def small_talk(self):
        print(f"{self.agent_id}: Small talk")
        self.save_state()
        self.publish_event({"agent": self.agent_id, "message": "Nice talking to you."})

    @trigger(source='*', dest=ConversationState.ENDING)
    def end_conversation(self):
        print(f"{self.agent_id}: Ending conversation")
        self.save_state()
        self.publish_event({"agent": self.agent_id, "message": "Goodbye!"})


class ConversationAgentA(ConversationAgent):
    def __init__(self, client=None):
        super().__init__(agent_id="agent-a", topic="conversation-topic", client=client)

    def handle_message(self, message):
        print(f"{self.agent_id}: Received message: {message}")
        self.prompt(message)


class ConversationAgentB(ConversationAgent):
    def __init__(self, client=None):
        super().__init__(agent_id="agent-b", topic="conversation-topic", client=client)

    def handle_message(self, message):
        print(f"{self.agent_id}: Received message: {message}")
        self.prompt(message)


def main():
    from dspygen.utils.dspy_tools import init_ol
    init_ol()

    # dapr_client = MockDaprClient(address=f'127.0.0.1:{os.getenv("DAPR_GRPC_PORT", 50001)}')
    dapr_client = DaprClient(address=f'127.0.0.1:{os.getenv("DAPR_GRPC_PORT", 50001)}')

    agent_a = ConversationAgentA(dapr_client)
    agent_b = ConversationAgentB(dapr_client)

    print("Initial states: Agent A:", agent_a.state, ", Agent B:", agent_b.state)

    agent_a.start_conversation()
    agent_b.handle_message({"message": "Hello!"})
    print("States after greetings: Agent A:", agent_a.state, ", Agent B:", agent_b.state)

    agent_a.handle_message({"message": "How are you?"})
    agent_b.handle_message({"message": "Nice talking to you."})
    print("States after small talk: Agent A:", agent_a.state, ", Agent B:", agent_b.state)

    agent_a.handle_message({"message": "Goodbye!"})
    agent_b.handle_message({"message": "Goodbye!"})
    print("Final states: Agent A:", agent_a.state, ", Agent B:", agent_b.state)


if __name__ == '__main__':
    main()
