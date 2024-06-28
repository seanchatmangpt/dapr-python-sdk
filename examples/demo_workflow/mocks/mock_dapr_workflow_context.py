import random

import inject
import requests
from dapr.clients import DaprClient
from dapr.ext.workflow import WorkflowRuntime
from factory import Factory
import icontract
from munch import Munch


class MockDaprClient:
    def __init__(self, *args, **kwargs):
        # super().__init__()
        self.responses = Munch.fromDict({
            'start_workflow': {"instance_id": "1234567890"},
            'get_workflow': {"status": "RUNNING"},
            'pause_workflow': None,
            'resume_workflow': None,
            'raise_workflow_event': None,
            'purge_workflow': None,
            'terminate_workflow': None,
        })
        self.workflow_states = {}

    @icontract.require(lambda instance_id, workflow_component, workflow_name, input,
                              workflow_options: instance_id is not None and workflow_component is not None)
    @icontract.ensure(lambda result: result is not None and "instance_id" in result)
    def start_workflow(self, instance_id, workflow_component, workflow_name, input, workflow_options):
        self.workflow_states[instance_id] = "RUNNING"
        return self.responses.get('start_workflow', {"instance_id": instance_id})

    @icontract.require(
        lambda instance_id, workflow_component: instance_id is not None and workflow_component is not None)
    @icontract.ensure(lambda result: result is not None and "status" in result)
    def get_workflow(self, instance_id, workflow_component):
        return {"status": self.workflow_states.get(instance_id, "UNKNOWN")}

    @icontract.require(
        lambda instance_id, workflow_component: instance_id is not None and workflow_component is not None)
    def pause_workflow(self, instance_id, workflow_component):
        if instance_id in self.workflow_states:
            self.workflow_states[instance_id] = "PAUSED"
        return self.responses.get('pause_workflow', None)

    @icontract.require(
        lambda instance_id, workflow_component: instance_id is not None and workflow_component is not None)
    def resume_workflow(self, instance_id, workflow_component):
        if instance_id in self.workflow_states:
            self.workflow_states[instance_id] = "RUNNING"
        return self.responses.get('resume_workflow', None)

    @icontract.require(lambda instance_id, workflow_component, event_name,
                              event_data: instance_id is not None and workflow_component is not None and event_name is not None)
    def raise_workflow_event(self, instance_id, workflow_component, event_name, event_data):
        # Simulate event processing
        return self.responses.get('raise_workflow_event', None)

    @icontract.require(
        lambda instance_id, workflow_component: instance_id is not None and workflow_component is not None)
    def purge_workflow(self, instance_id, workflow_component):
        if instance_id in self.workflow_states:
            del self.workflow_states[instance_id]
        return self.responses.get('purge_workflow', None)

    @icontract.require(
        lambda instance_id, workflow_component: instance_id is not None and workflow_component is not None)
    def terminate_workflow(self, instance_id, workflow_component):
        if instance_id in self.workflow_states:
            self.workflow_states[instance_id] = "TERMINATED"
        return self.responses.get('terminate_workflow', None)

    def close(self):
        ...


class MockWorkflowRuntime:
    def __init__(self, *args, **kwargs):
        self.responses = Munch.fromDict({
            'start': None,
            'shutdown': None,
        })
        self.workflows = {}
        self.activities = {}
        self.is_running = False

    @icontract.ensure(lambda result: result is None)
    def start(self, *args, **kwargs):
        self.is_running = True
        return self.responses.get('start', None)

    @icontract.ensure(lambda result: result is None)
    def shutdown(self, *args, **kwargs):
        self.is_running = False
        return self.responses.get('shutdown', None)

    def register_workflow(self, workflow_func):
        self.workflows[workflow_func.__name__] = workflow_func

    def register_activity(self, activity_func):
        self.activities[activity_func.__name__] = activity_func

    def call_activity(self, activity_name, *args, **kwargs):
        if activity_name in self.activities:
            return self.activities[activity_name](*args, **kwargs)
        raise ValueError(f"Activity {activity_name} not registered")

    def call_workflow(self, workflow_name, *args, **kwargs):
        if workflow_name in self.workflows:
            return self.workflows[workflow_name](*args, **kwargs)
        raise ValueError(f"Workflow {workflow_name} not registered")


class DaprClientFactory(Factory):
    class Meta:
        model = MockDaprClient

    responses = {}


class WorkflowRuntimeFactory(Factory):
    class Meta:
        model = MockWorkflowRuntime

    responses = {}


class MockDaprWorkflowContextManager:
    def __init__(self, dapr_responses=None, workflow_responses=None):
        self.dapr_responses = dapr_responses or {}
        self.workflow_responses = workflow_responses or {}

    def __enter__(self):
        self.dapr_client = MockDaprClient(responses=self.dapr_responses)
        self.workflow_runtime = MockWorkflowRuntime(responses=self.workflow_responses)

        def configure(binder):
            """Configure dependency injection bindings."""
            binder.bind(DaprClient, self.dapr_client)
            binder.bind(WorkflowRuntime, self.workflow_runtime)

        inject.configure(configure, clear=True)
        return self.dapr_client, self.workflow_runtime

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.workflow_runtime.shutdown()
        self.dapr_client.close()

