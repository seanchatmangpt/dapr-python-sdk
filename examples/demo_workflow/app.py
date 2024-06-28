import logging
import time
from enum import Enum, auto
from dspygen.mixin.fsm.fsm_mixin import FSMMixin, trigger
from dapr.ext.workflow import DaprWorkflowContext

from agents.challenger_agent import ChallengerSalesAgent  # Import the agent directly
from workflow.dapr_workflow_context import DaprWorkflowContextManager
from workflow.dapr_workflow_mixin import *


class SalesWorkflow(DaprWorkflowMixin):
    def __init__(self, instance_id, workflow_name, input_data, workflow_options, auto_start=True):
        super().__init__(instance_id=instance_id,
                         workflow_name=workflow_name,
                         input_data=input_data,
                         workflow_options=workflow_options,
                         auto_start=auto_start)

    @register_workflow
    def sales_process(self, ctx: DaprWorkflowContext, input_data: dict):
        agent = ChallengerSalesAgent()
        print(f"Initial state: {agent.state}")

        # Simulate the registration and setup of sales processes
        agent.prompt("begin researching the market")
        print(f"State after market research: {agent.state}")

        agent.prompt("start reaching out to leads")
        print(f"State after outreach: {agent.state}")

        agent.prompt("get to know the client needs")
        print(f"State after discovery: {agent.state}")

        agent.prompt("customize the solutions for client")
        print(f"State after tailoring solutions: {agent.state}")

        agent.prompt("deal with client concerns")
        print(f"State after handling objections: {agent.state}")

        agent.prompt("update the proposal based on feedback")
        print(f"State after revising proposal: {agent.state}")

        agent.prompt("gather more details about the client")
        print(f"State after deepening discovery: {agent.state}")

        agent.prompt("reach out to more potential clients")
        print(f"State after restarting outreach: {agent.state}")

        agent.prompt("finalize the deal")
        print(f"State after closing the deal: {agent.state}")

        agent.prompt("wrap up the sale")
        print(f"State after completing the sale: {agent.state}")

        agent.prompt("get ready for the next client")
        print(f"Final state: {agent.state}")

        return {"final_state": agent.state.name}


if __name__ == "__main__":
    from dapr.clients import DaprClient

    instance_id = "salesWorkflowExample"
    workflow_name = "sales_process"
    input_data = {}

    with DaprWorkflowContextManager() as (dapr_client, workflow_runtime):
        sales_workflow = SalesWorkflow(
            instance_id=instance_id,
            workflow_name=workflow_name,
            input_data=input_data,
            workflow_options={}
        )
        time.sleep(20)
        sales_workflow.terminate_workflow()
