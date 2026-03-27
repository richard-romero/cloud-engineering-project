import typer
import subprocess
from pathlib import Path

app = typer.Typer()

TERRAFORM_DIR = Path(__file__).resolve().parents[2] / "terraform"

def run(cmd):
    subprocess.run(cmd, cwd=TERRAFORM_DIR, check=True)

@app.callback(invoke_without_command=True)
def deploy():
    """Provision infrastructure and deploy service"""

    print("[INFO] Initializing Terraform...")
    run(["terraform", "init"])

    print("[INFO] Applying Infrastructure...")
    run(["terraform", "apply", "-auto-approve"])