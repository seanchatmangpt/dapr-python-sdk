import pytest
import logging

from mocks.mock_dapr_workflow_context import DaprClientFactory, WorkflowRuntimeFactory, MockDaprWorkflowContextManager

logging.basicConfig(level=logging.INFO)

# @pytest.fixture
# def mock_dapr_workflow_context(monkeypatch):
#     def _mock_dapr_workflow_context(dapr_responses=None, workflow_responses=None):
#         logging.info("Initializing mock Dapr workflow context with responses.")
#         print("Initializing mock Dapr workflow context with responses.")  # Debug print
#
#         def mock_dapr_client_factory(*args, **kwargs):
#             return DaprClientFactory(responses=dapr_responses)
#
#         def mock_workflow_runtime_factory(*args, **kwargs):
#             return WorkflowRuntimeFactory(responses=workflow_responses)
#
#         monkeypatch.setattr('workflow.dapr_workflow_context.DaprClient', mock_dapr_client_factory)
#         monkeypatch.setattr('workflow.dapr_workflow_context.WorkflowRuntime', mock_workflow_runtime_factory)
#         return MockDaprWorkflowContextManager(dapr_responses, workflow_responses)
#
#     return _mock_dapr_workflow_context
