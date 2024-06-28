import pytest
from unittest.mock import create_autospec, patch
from dapr.ext.workflow import DaprWorkflowContext

from mocks.mock_dapr_workflow_context import MockDaprWorkflowContextManager
from workflow.iot_gas_workflow import GasIotWorkflow


def test_gas_workflow():
    with MockDaprWorkflowContextManager() as (mock_dapr_client, mock_workflow_runtime):
        gas_workflow = GasIotWorkflow(instance_id="gas-workflow", workflow_name="gas-workflow", input_data={}, workflow_options={})
        assert gas_workflow is not None

        mock_context = create_autospec(DaprWorkflowContext, instance=True)
        workflow_input = {
            "sensor_id": "sensor_1",
            "temperature": 22.5,
            "humidity": 45.0,
            "pressure": 101.3
        }

        # Mocking return values for call_activity
        mock_context.call_activity.side_effect = [
            'bin_id_123',  # create_gas_record
            {"sensor_id": "sensor_1", "temperature": 22.5, "humidity": 45.0, "pressure": 101.3},  # read_gas_record
            None,  # update_gas_record
            {"sensor_id": "sensor_1", "temperature": 22.5, "humidity": 45.0, "pressure": 101.5},  # read_gas_record (updated)
            None,  # assert_gas_data
            None  # delete_gas_record
        ]

        # Run the workflow generator and send mock return values into the generator
        gen = gas_workflow.gas_iot_crud_workflow(mock_context, workflow_input)

        try:
            # Start the generator
            next_value = None
            while True:
                next_value = gen.send(next_value)
        except StopIteration:
            pass

        # Assertions to verify the calls were made correctly
        mock_context.call_activity.assert_any_call(gas_workflow.create_gas_record, input=workflow_input)
        mock_context.call_activity.assert_any_call(gas_workflow.read_gas_record, input='bin_id_123')
        mock_context.call_activity.assert_any_call(gas_workflow.update_gas_record, input={"bin_id": 'bin_id_123', "data": {"sensor_id": "sensor_1", "temperature": 22.5, "humidity": 45.0, "pressure": 101.5}})
        mock_context.call_activity.assert_any_call(gas_workflow.read_gas_record, input='bin_id_123')
        mock_context.call_activity.assert_any_call(gas_workflow.assert_gas_data, input={"expected": {"sensor_id": "sensor_1", "temperature": 22.5, "humidity": 45.0, "pressure": 101.5}, "actual": {"sensor_id": "sensor_1", "temperature": 22.5, "humidity": 45.0, "pressure": 101.5}})
        mock_context.call_activity.assert_any_call(gas_workflow.delete_gas_record, input='bin_id_123')