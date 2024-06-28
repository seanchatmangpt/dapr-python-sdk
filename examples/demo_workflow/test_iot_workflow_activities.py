import pytest
import requests
import requests_mock
from unittest.mock import create_autospec, MagicMock
from dapr.ext.workflow import WorkflowActivityContext

from mocks.mock_dapr_workflow_context import MockDaprWorkflowContextManager
from workflow.iot_gas_workflow import GasIotWorkflow

# Configuration constants for the tests
BASE_URL = "https://api.jsonbin.io/v3/b"
MASTER_KEY = "$2a$10$c4.2QWMBzpHa/sxV0PzDU.xvZxLdYJHhghCYcXDWTV6HJOva5e7ZO"
ACCESS_KEY_HASH = "$2a$10$CXJvF.mMBzOeKe0.A05KkuM3nYGrFATtRc7YaN6z0jkm5B6fO6Ohq"


@pytest.fixture
def workflow():
    with MockDaprWorkflowContextManager() as (mock_dapr_client, mock_workflow_runtime):
        return GasIotWorkflow(instance_id="test_instance", workflow_name="test_workflow", input_data={}, workflow_options={})


@pytest.fixture
def mock_context():
    return create_autospec(WorkflowActivityContext, instance=True)


def test_create_gas_record(workflow, mock_context):
    data = {
        "sensor_id": "sensor_1",
        "temperature": 22.5,
        "humidity": 45.0,
        "pressure": 101.3
    }
    with requests_mock.Mocker() as m:
        m.post(BASE_URL, json={"metadata": {"id": "test_bin_id"}})

        bin_id = workflow.create_gas_record(mock_context, data)

        assert bin_id == "test_bin_id"
        assert m.called
        assert m.call_count == 1
        request = m.request_history[0]
        assert request.json() == data
        assert request.headers["X-MASTER-KEY"] == MASTER_KEY
        assert request.headers["X-ACCESS-KEY"] == ACCESS_KEY_HASH


def test_read_gas_record(workflow, mock_context):
    bin_id = "test_bin_id"
    expected_data = {
        "sensor_id": "sensor_1",
        "temperature": 22.5,
        "humidity": 45.0,
        "pressure": 101.3
    }
    with requests_mock.Mocker() as m:
        m.get(f"{BASE_URL}/{bin_id}", json={"record": expected_data})

        gas_data = workflow.read_gas_record(mock_context, bin_id)

        assert gas_data == expected_data
        assert m.called
        assert m.call_count == 1
        request = m.request_history[0]
        assert request.headers["X-MASTER-KEY"] == MASTER_KEY
        assert request.headers["X-ACCESS-KEY"] == ACCESS_KEY_HASH


def test_update_gas_record(workflow, mock_context):
    bin_id = "test_bin_id"
    data = {
        "sensor_id": "sensor_1",
        "temperature": 22.5,
        "humidity": 45.0,
        "pressure": 101.5
    }
    with requests_mock.Mocker() as m:
        m.put(f"{BASE_URL}/{bin_id}")

        workflow.update_gas_record(mock_context, {"bin_id": bin_id, "data": data})

        assert m.called
        assert m.call_count == 1
        request = m.request_history[0]
        assert request.json() == data
        assert request.headers["X-MASTER-KEY"] == MASTER_KEY
        assert request.headers["X-ACCESS-KEY"] == ACCESS_KEY_HASH


def test_delete_gas_record(workflow, mock_context):
    bin_id = "test_bin_id"
    with requests_mock.Mocker() as m:
        m.delete(f"{BASE_URL}/{bin_id}")

        workflow.delete_gas_record(mock_context, bin_id)

        assert m.called
        assert m.call_count == 1
        request = m.request_history[0]
        assert request.headers["X-MASTER-KEY"] == MASTER_KEY
        assert request.headers["X-ACCESS-KEY"] == ACCESS_KEY_HASH


def test_assert_gas_data(workflow, mock_context):
    expected_data = {
        "bin_id": "test_bin_id",
        "sensor_id": "sensor_1",
        "temperature": 22.5,
        "humidity": 45.0,
        "pressure": 101.5
    }
    actual_data = expected_data.copy()

    # This should pass without exceptions
    workflow.assert_gas_data(mock_context, {
        "bin_id": "test_bin_id",
        "expected": expected_data,
        "actual": actual_data
    })

    # Modify actual_data to cause an assertion error
    actual_data["pressure"] = 100.0
    with pytest.raises(AssertionError, match="Data mismatch: expected .* got .*"):
        workflow.assert_gas_data(mock_context, {"expected": expected_data, "actual": actual_data})
