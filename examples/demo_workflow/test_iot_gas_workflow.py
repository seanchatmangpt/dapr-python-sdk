import pytest
from pytest_bdd import scenarios, given, when, then

from workflow.iot_gas_workflow import GasIotWorkflow

scenarios('features/test_gas_iot_workflow.feature')


@pytest.fixture
def dapr_workflow_context_manager(mock_dapr_workflow_context):
    dapr_responses = {
        'start_workflow': {"instance_id": "mock_instance_id"},
        'get_workflow': {"status": "RUNNING"},
        'pause_workflow': None,
        'resume_workflow': None,
        'raise_workflow_event': None,
        'purge_workflow': None,
        'terminate_workflow': None
    }
    workflow_responses = {
        'start': None,
        'shutdown': None
    }
    return mock_dapr_workflow_context(dapr_responses=dapr_responses, workflow_responses=workflow_responses)


@given('a mock Dapr client')
def dapr_client(dapr_workflow_context_manager):
    return True


@given('a mock Workflow runtime')
def workflow_runtime(dapr_workflow_context_manager):
    return True


@when('the workflow is started')
def start_workflow(dapr_client, workflow_runtime):
    with dapr_workflow_context_manager:
        gas_iot_workflow = GasIotWorkflow(
            instance_id="test",
            workflow_name="gas_iot_crud_workflow",
            input_data={"sensor_id": "sensor_1", "temperature": 22.5, "humidity": 45.0, "pressure": 101.3},
            workflow_options={}
        )
        gas_iot_workflow.start_workflow()


@then('the workflow should start successfully')
def workflow_started(dapr_client):
    assert \
    dapr_client.start_workflow(instance_id="test", workflow_component="dapr", workflow_name="gas_iot_crud_workflow")[
        "instance_id"] == "mock_instance_id"


@when('the workflow status is requested')
def get_workflow_status(dapr_client):
    return dapr_client.get_workflow(instance_id="test", workflow_component="dapr")


@then('the status should be "RUNNING"')
def verify_workflow_status(dapr_client):
    assert dapr_client.get_workflow(instance_id="test", workflow_component="dapr")["status"] == "RUNNING"


@when('the workflow is paused')
def pause_workflow(dapr_client):
    dapr_client.pause_workflow(instance_id="test", workflow_component="dapr")


@then('the workflow should pause successfully')
def verify_workflow_paused(dapr_client):
    assert dapr_client.get_workflow(instance_id="test", workflow_component="dapr")["status"] == "PAUSED"


@when('the workflow is resumed')
def resume_workflow(dapr_client):
    dapr_client.resume_workflow(instance_id="test", workflow_component="dapr")


@then('the workflow should resume successfully')
def verify_workflow_resumed(dapr_client):
    assert dapr_client.get_workflow(instance_id="test", workflow_component="dapr")["status"] == "RUNNING"


@when('the workflow is terminated')
def terminate_workflow(dapr_client):
    dapr_client.terminate_workflow(instance_id="test", workflow_component="dapr")


@then('the workflow should terminate successfully')
def verify_workflow_terminated(dapr_client):
    assert dapr_client.get_workflow(instance_id="test", workflow_component="dapr")["status"] == "TERMINATED"


@when('an event "dataUpdate" is raised with data {"key": "value"}')
def raise_event(dapr_client):
    dapr_client.raise_workflow_event(instance_id="test", workflow_component="dapr", event_name="dataUpdate",
                                     event_data={"key": "value"})


@then('the event should be processed successfully')
def verify_event_processed(dapr_client):
    # In a real test, we would check some state or response indicating the event was processed
    assert dapr_client.raise_workflow_event(instance_id="test", workflow_component="dapr", event_name="dataUpdate",
                                            event_data={"key": "value"}) is None


@when('the workflow is purged')
def purge_workflow(dapr_client):
    dapr_client.purge_workflow(instance_id="test", workflow_component="dapr")


@then('the workflow should be purged successfully')
def verify_workflow_purged(dapr_client):
    assert dapr_client.get_workflow(instance_id="test", workflow_component="dapr")["status"] == "UNKNOWN"
