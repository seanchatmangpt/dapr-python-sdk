import os
import typer
import subprocess

app = typer.Typer()

@app.command()
def run(
    app_id: str = typer.Option("orderapp", help="The app ID for the Dapr application."),
    resources_path: str = typer.Option("components", help="The path to the Dapr components."),
    placement_host: str = typer.Option("localhost:50005", help="The address of the Dapr placement service."),
    app_port: int = typer.Option(8000, help="The port the application will run on."),
    script: str = typer.Option("fast_app.py", help="The script to run.")
):
    os.chdir("/Users/sac/dev/dapr-python-sdk/examples/demo_workflow")
    subprocess.run([
        "dapr", "run",
        "--app-id", app_id,
        "--resources-path", resources_path,
        "--placement-host-address", placement_host,
        "--app-port", str(app_port),
        "--", "python3", script
    ])

@app.command()
def publish(
    id: str = typer.Option("7", help="ID of the user."),
    name: str = typer.Option("Bob Jones", help="Name of the user."),
    app_id: str = typer.Option("orderapp", help="The app ID for the Dapr application."),
    topic: str = typer.Option("cloud_topic", help="The topic to publish to."),
    pubsub: str = typer.Option("pubsub", help="The name of the pub/sub component.")
):
    subprocess.run([
        "dapr", "publish",
        "--publish-app-id", app_id,
        "--topic", topic,
        "--pubsub", pubsub,
        "--data", f'{{"id":"{id}", "name":"{name}", "message_type":"BaseMessage"}}'
    ])

if __name__ == "__main__":
    app()
