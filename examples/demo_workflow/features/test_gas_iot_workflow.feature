Feature: Gas IoT Workflow
  Scenario: Start a workflow
    Given a mock Dapr client
    And a mock Workflow runtime
    When the workflow is started
    Then the workflow should start successfully

  Scenario: Get workflow status
    Given a mock Dapr client
    And a mock Workflow runtime
    When the workflow status is requested
    Then the status should be "RUNNING"

  Scenario: Pause and resume workflow
    Given a mock Dapr client
    And a mock Workflow runtime
    When the workflow is paused
    Then the workflow should pause successfully
    When the workflow is resumed
    Then the workflow should resume successfully

  Scenario: Terminate a workflow
    Given a mock Dapr client
    And a mock Workflow runtime
    When the workflow is terminated
    Then the workflow should terminate successfully

  Scenario: Raise an event in a workflow
    Given a mock Dapr client
    And a mock Workflow runtime
    When an event "dataUpdate" is raised with data {"key": "value"}
    Then the event should be processed successfully

  Scenario: Purge a workflow
    Given a mock Dapr client
    And a mock Workflow runtime
    When the workflow is purged
    Then the workflow should be purged successfully
