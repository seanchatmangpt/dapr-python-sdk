# dapr_workflow_context.py
from dapr.clients import DaprClient
from dapr.ext.workflow import WorkflowRuntime
import inject

class DaprWorkflowContextManager:
    def __enter__(self):
        self.dapr_client = DaprClient()
        self.workflow_runtime = WorkflowRuntime()

        def configure(binder):
            """Configure dependency injection bindings."""
            # binder.bind(DaprClient, self.dapr_client)
            # binder.bind(WorkflowRuntime, self.workflow_runtime)

        inject.configure(configure)
        return self.dapr_client, self.workflow_runtime

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.workflow_runtime.shutdown()
        self.dapr_client.close()


