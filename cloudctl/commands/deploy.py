import typer
import subprocess
import time
from pathlib import Path
from ssh.client import SSHClient, get_terraform_outputs, load_settings

app = typer.Typer()

TERRAFORM_DIR = Path(__file__).resolve().parents[2] / "terraform"
BOOTSTRAP = Path(__file__).resolve().parents[1] / "scripts/bootstrap.sh"

def run(cmd):
    subprocess.run(cmd, cwd=TERRAFORM_DIR, check=True)


def wait_for_ssh_ready(host: str, key_path: str, user: str, retries: int = 20, delay: int = 10) -> None:
    """Wait for the instance SSH service to become reachable."""
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            with SSHClient(host=host, key_path=key_path, user=user):
                return
        except Exception as error:  # pragma: no cover - network conditions are environment-specific.
            last_error = error
            if attempt == retries:
                break
            print(f"[INFO] SSH not ready yet ({attempt}/{retries}). Retrying in {delay}s...")
            time.sleep(delay)

    raise RuntimeError(f"SSH did not become ready for {host}: {last_error}")

@app.callback(invoke_without_command=True)
def deploy():
    """Provision infrastructure and deploy service"""

    print("[INFO] Initializing Terraform...")
    run(["terraform", "init"])

    print("[INFO] Applying Infrastructure...")
    run(["terraform", "apply", "-auto-approve"])

    if not BOOTSTRAP.exists():
        raise FileNotFoundError(f"Bootstrap script was not found at {BOOTSTRAP}")

    outputs = get_terraform_outputs()
    settings = load_settings()

    host = outputs["public_ip"]
    key_path = settings["ssh"]["key_path"]
    user = settings["ssh"]["user"]

    print("[INFO] Waiting for SSH readiness...")
    wait_for_ssh_ready(host=host, key_path=key_path, user=user)

    remote_script = "/home/ec2-user/bootstrap.sh"

    with SSHClient(host=host, key_path=key_path, user=user) as ssh:
        print("[INFO] Uploading bootstrap script...")
        ssh.upload(str(BOOTSTRAP), remote_script)

        print("[INFO] Executing bootstrap...")
        out, err = ssh.run(f"chmod +x {remote_script} && sudo {remote_script}", check=True)

    if out.strip():
        print(out.strip())
    if err.strip():
        print(err.strip())

    print(f"[SUCCESS] Deployment complete. Instance public IP: {host}")