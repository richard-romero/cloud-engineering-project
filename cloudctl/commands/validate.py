import requests
import typer

from ssh.client import SSHClient, get_terraform_outputs, load_settings

app = typer.Typer()
CONTAINER = "webapp"


@app.callback(invoke_without_command=True)
def validate() -> None:
    """Run post-deployment validation checks against the target host."""
    typer.echo("[INFO] Starting validation...")

    try:
        outputs = get_terraform_outputs()
        settings = load_settings()

        host = outputs["public_ip"]
        key_path = settings["ssh"]["key_path"]
        user = settings["ssh"]["user"]
    except Exception as error:
        typer.echo(f"[ERROR] Failed to load Terraform outputs or settings: {error}")
        raise typer.Exit(code=1)

    typer.echo("[INFO] Checking SSH connectivity...")

    try:
        with SSHClient(host, key_path, user) as ssh:
            typer.echo("[SUCCESS] SSH reachable")

            typer.echo("[INFO] Checking Docker service...")

            service_state, service_error = ssh.run("sudo systemctl is-active docker")
            service_state = service_state.strip()

            if service_state != "active":
                details = service_error.strip() or service_state or "unknown"
                typer.echo(f"[ERROR] Docker not running (state/details: {details})")
                raise typer.Exit(code=1)

            typer.echo("[SUCCESS] Docker running")

            typer.echo("[INFO] Checking container status...")

            container_list, container_error = ssh.run("sudo docker ps --format '{{.Names}}'")

            if CONTAINER not in container_list.splitlines():
                details = container_error.strip() or container_list.strip() or "none"
                typer.echo(f"[ERROR] {CONTAINER} container not running (details: {details})")
                raise typer.Exit(code=1)

            typer.echo("[SUCCESS] Container running")
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"[ERROR] SSH failed: {e}")
        raise typer.Exit(code=1)

    typer.echo("[INFO] Checking HTTP response...")

    try:
        response = requests.get(f"http://{host}", timeout=5)

        if response.status_code == 200:
            typer.echo("[SUCCESS] Service reachable")
        else:
            typer.echo(f"[ERROR] HTTP unhealthy (status: {response.status_code})")
            raise typer.Exit(code=1)
    except Exception as error:
        typer.echo(f"[ERROR] Cannot reach HTTP service: {error}")
        raise typer.Exit(code=1)

    typer.echo("[SUCCESS] Validation complete.")
