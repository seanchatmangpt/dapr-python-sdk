import time

import requests
from dapr.ext.workflow import DaprWorkflowContext, WorkflowActivityContext

from workflow.dapr_workflow_mixin import DaprWorkflowMixin, register_workflow, register_activity
from workflow.dapr_workflow_context import DaprWorkflowContextManager

# Configuration
MASTER_KEY = "$2a$10$c4.2QWMBzpHa/sxV0PzDU.xvZxLdYJHhghCYcXDWTV6HJOva5e7ZO"
ACCESS_KEY = "TEST"
ACCESS_KEY_HASH = "$2a$10$CXJvF.mMBzOeKe0.A05KkuM3nYGrFATtRc7YaN6z0jkm5B6fO6Ohq"
BASE_URL = "https://api.jsonbin.io/v3/b"


class GasIotWorkflow(DaprWorkflowMixin):
    def __init__(self, instance_id, workflow_name, input_data, workflow_options, auto_start=True):
        super().__init__(instance_id=instance_id,
                         workflow_name=workflow_name,
                         input_data=input_data,
                         workflow_options=workflow_options,
                         auto_start=auto_start)

    @register_workflow
    def gas_iot_crud_workflow(self, ctx: DaprWorkflowContext, wf_input: dict):
        # import pdb;
        # pdb.set_trace()  # Python's built-in debugger

        # Create
        bin_id = yield ctx.call_activity(self.create_gas_record, input=wf_input)

        # Read
        gas_data = yield ctx.call_activity(self.read_gas_record, input=bin_id)

        # Store in Dapr KV store
        # yield ctx.call_activity(self.store_gas_data, input={"bin_id": bin_id, "data": gas_data})

        # Update
        updated_data = gas_data.copy()
        updated_data["pressure"] = 101.5
        yield ctx.call_activity(self.update_gas_record, input={"bin_id": bin_id, "data": updated_data})

        # Verify update
        final_data = yield ctx.call_activity(self.read_gas_record, input=bin_id)

        # Final assert
        yield ctx.call_activity(self.assert_gas_data, input={"expected": updated_data, "actual": final_data})

        # Delete
        yield ctx.call_activity(self.delete_gas_record, input=bin_id)

        return bin_id

    @register_activity
    def create_gas_record(self, ctx: WorkflowActivityContext, data: dict) -> str:
        url = BASE_URL
        headers = {
            "Content-Type": "application/json",
            "X-MASTER-KEY": MASTER_KEY,
            "X-ACCESS-KEY": ACCESS_KEY_HASH
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        bin_id = response.json()["metadata"]["id"]
        print(f"Created gas record with bin ID: {bin_id}")
        return bin_id

    @register_activity
    def read_gas_record(self, ctx: WorkflowActivityContext, bin_id: str) -> dict:
        url = f"{BASE_URL}/{bin_id}"
        headers = {
            "X-MASTER-KEY": MASTER_KEY,
            "X-ACCESS-KEY": ACCESS_KEY_HASH
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        gas_data = response.json()["record"]
        print(f"Read gas record: {gas_data}")
        return gas_data

    @register_activity
    def update_gas_record(self, ctx: WorkflowActivityContext, input: dict):
        bin_id = input["bin_id"]
        data = input["data"]
        url = f"{BASE_URL}/{bin_id}"
        headers = {
            "Content-Type": "application/json",
            "X-MASTER-KEY": MASTER_KEY,
            "X-ACCESS-KEY": ACCESS_KEY_HASH
        }
        response = requests.put(url, json=data, headers=headers)
        response.raise_for_status()
        print(f"Updated gas record with bin ID: {bin_id}")

    @register_activity
    def delete_gas_record(self, ctx: WorkflowActivityContext, bin_id: str):
        url = f"{BASE_URL}/{bin_id}"
        headers = {
            "X-MASTER-KEY": MASTER_KEY,
            "X-ACCESS-KEY": ACCESS_KEY_HASH
        }
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        print(f"Deleted gas record with bin ID: {bin_id}")

    @register_activity
    def store_gas_data(self, ctx: WorkflowActivityContext, input: dict):
        bin_id = input["bin_id"]
        data = input["data"]
        store_key = f"gasdata-{bin_id}"
        dapr_client = ctx.get_dapr_client()
        dapr_client.save_state(store_name="statestore", key=store_key, value=data)
        print(f"Stored gas data with bin ID: {bin_id} in Dapr KV store")

    @register_activity
    def assert_gas_data(self, ctx: WorkflowActivityContext, input: dict):
        expected_data = input["expected"]
        actual_data = input["actual"]
        assert expected_data == actual_data, f"Data mismatch: expected {expected_data}, got {actual_data}"
        print(f"Assertion passed: data matches for bin ID {input['bin_id']}")


if __name__ == "__main__":
    instance_id = "gasIotExample"
    workflow_name = "gas_iot_crud_workflow"
    input_data = {
        "sensor_id": "sensor_1",
        "temperature": 22.5,
        "humidity": 45.0,
        "pressure": 101.3
    }
    workflow_options = {}

    with DaprWorkflowContextManager() as (d_client, wf_runtime):
        gas_iot_workflow = GasIotWorkflow(
            instance_id=instance_id,
            workflow_name=workflow_name,
            input_data=input_data,
            workflow_options=workflow_options
        )
        time.sleep(20)
        gas_iot_workflow.terminate_workflow()
