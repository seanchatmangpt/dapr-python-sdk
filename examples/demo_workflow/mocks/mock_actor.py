from dspygen.rdddy.base_actor import BaseActor


class MockActor(BaseActor):
    def __init__(self, actor_system, **kwargs):
        super().__init__(actor_system, **kwargs)
        self.state = 0

    async def on_message(self, message):
        self.state += 1
        print(f"Actor {self.actor_id} received message {message} and state is {self.state}")
