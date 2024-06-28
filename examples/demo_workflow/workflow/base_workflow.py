"""
This module defines a BaseWorkflow class that serves as a reference implementation of the DaprWorkflowMixin.
The BaseWorkflow class encapsulates common functionality and provides a foundation for more specific workflows.
"""

from datetime import timedelta
import inject
from dapr.ext.workflow import DaprWorkflowContext, WorkflowActivityContext

from utils.log_doc_time import log_timing_and_docstring
from workflow.dapr_workflow_mixin import *


class BaseWorkflow(DaprWorkflowMixin):
    def __init__(self, instance_id, workflow_name, input_data, workflow_options, auto_start=True):
        super().__init__(instance_id=instance_id, 
                         workflow_name=workflow_name, 
                         input_data=input_data, 
                         workflow_options=workflow_options, 
                         auto_start=auto_start)
        self.counter = 0
        self.retry_count = 0
        self.child_orchestrator_count = 0
        self.child_orchestrator_string = ''
        self.child_act_retry_count = 0
        self.child_instance_id = 'childInstanceID'
        self.event_name = 'event1'
        self.event_data = 'eventData'
        self.non_existent_id_error = 'no such instance exists'

    @log_timing_and_docstring
    @register_workflow
    def hello_world_wf(self, ctx: DaprWorkflowContext, wf_input):
        """
        This is a workflow that calls activities and child workflows.
        """
        print(f'{wf_input}')
        yield ctx.call_activity(self.hello_act, input=1_337)
        yield ctx.call_activity(self.hello_act, input=1_338)
        yield ctx.call_activity(self.hello_retryable_act)
        yield ctx.call_child_workflow(self.child_retryable_wf, instance_id=self.child_instance_id, input=wf_input)
        yield ctx.call_child_workflow(self.child_wf, instance_id=self.child_instance_id, input=wf_input)
        yield ctx.call_activity(self.hello_act, input=100)
        yield ctx.call_activity(self.hello_act, input=1000)

    @log_timing_and_docstring
    @register_workflow
    def child_wf(self, ctx: DaprWorkflowContext):
        """
        This is a child workflow that waits for an external event and then calls an activity.
        """
        yield ctx.wait_for_external_event(self.event_name)

    @log_timing_and_docstring
    @register_activity
    def hello_act(self, ctx: WorkflowActivityContext, wf_input):
        """
        This is an activity that increments a counter and logs the new value.
        """
        print("hello_act")
        self.counter += wf_input
        print(f'New counter value is: {self.counter}!', flush=True)

    @log_timing_and_docstring
    @register_activity
    def hello_retryable_act(self, ctx: WorkflowActivityContext):
        """
        This is an activity that increments a counter and logs the new value.
        """
        print("hello_retryable_act")
        if (self.retry_count % 2) == 0:
            print(f'Retry count value is: {self.retry_count}!', flush=True)
            self.retry_count += 1
            raise ValueError('Retryable Error')
        print(f'Retry count value is: {self.retry_count}! This print statement verifies retry', flush=True)
        self.retry_count += 1

    @log_timing_and_docstring
    @register_workflow
    def child_retryable_wf(self, ctx: DaprWorkflowContext):
        """
        This is a child workflow that waits for an external event and then calls an activity.
        """
        print("child_retryable_wf")
        if not ctx.is_replaying:
            self.child_orchestrator_count += 1
            print(f'Appending {self.child_orchestrator_count} to child_orchestrator_string!', flush=True)
            self.child_orchestrator_string += str(self.child_orchestrator_count)
        yield ctx.call_activity(
            self.act_for_child_wf, input=self.child_orchestrator_count
        )
        if self.child_orchestrator_count < 3:
            raise ValueError('Retryable Error')

    @log_timing_and_docstring
    @register_activity
    def act_for_child_wf(self, ctx: WorkflowActivityContext, inp):
        """
        This is an activity that increments a counter and logs the new value.
        """
        print(f"act_for_child_wf {inp}")
        inp_char = chr(96 + inp)
        print(f'Appending {inp_char} to child_orchestrator_string!', flush=True)
        self.child_orchestrator_string += inp_char
        if self.child_act_retry_count % 2 == 0:
            self.child_act_retry_count += 1
            raise ValueError('Retryable Error')
        self.child_act_retry_count += 1
