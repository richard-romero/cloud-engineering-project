import subprocess
import json
import yaml
import paramiko
from pathlib import Path
from typing import Tuple

BASE_DIR = Path(__file__).resolve().parents[2]
TERRAFORM_DIR = BASE_DIR / "terraform"
CONFIG_PATH = BASE_DIR / "cloudctl/config/settings.yaml"

def load_settings() -> dict:
    """Load application settings from the YAML config file."""
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def get_terraform_outputs() -> dict:
    """Retrieve Terraform outputs as a dictionary."""
    try:
        result = subprocess.run(
            ["terraform", "output", "-json"],
            cwd=TERRAFORM_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
        outputs = json.loads(result.stdout)

        return {
            "public_ip": outputs["instance_public_ip"]["value"],
            "instance_id": outputs["instance_id"]["value"],
            "region": outputs["configured_region"]["value"],
            "ssh_command": outputs["ssh_command"]["value"],
        }
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to fetch Terraform outputs: {e}") from e
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise RuntimeError(f"Terraform outputs are invalid or incomplete: {e}") from e

class SSHClient:
    """A context-managed SSH client wrapper using Paramiko."""
    
    def __init__(self, host: str, key_path: str, user: str = "ec2-user") -> None:
        self.host = host
        self.user = user
        self.key_path = str(Path(key_path).expanduser())
        self.client = None

    def connect(self) -> None:
        """Establish the SSH connection to the remote host."""
        key = self._load_private_key()

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.client.connect(
            hostname=self.host,
            username=self.user,
            pkey=key,
        )

    def _load_private_key(self):
        """Load the SSH private key using a supported Paramiko key class."""
        key_loaders = (
            paramiko.Ed25519Key,
            paramiko.RSAKey,
            paramiko.ECDSAKey,
        )

        last_error = None
        for key_loader in key_loaders:
            try:
                return key_loader.from_private_key_file(self.key_path)
            except (paramiko.SSHException, ValueError, TypeError) as error:
                last_error = error

        raise paramiko.SSHException(
            f"Unable to load SSH private key from {self.key_path}: {last_error}"
        )

    def run(self, command: str, check: bool = False) -> Tuple[str, str]:
        """Execute a command on the remote host and return (stdout, stderr)."""
        if not self.client:
            raise RuntimeError("SSH Client is not connected. Call .connect() first.")

        _, stdout, stderr = self.client.exec_command(command)

        out = stdout.read().decode()
        err = stderr.read().decode()
        exit_code = stdout.channel.recv_exit_status()

        if check and exit_code != 0:
            raise RuntimeError(
                f"Remote command failed with exit code {exit_code}: {command}\n{err.strip()}"
            )

        return out, err

    def upload(self, local_path: str, remote_path: str) -> None:
        """Upload a local file to the remote host over SFTP."""
        if not self.client:
            raise RuntimeError("SSH Client is not connected. Call .connect() first.")

        source_path = Path(local_path).expanduser().resolve()
        if not source_path.exists() or not source_path.is_file():
            raise FileNotFoundError(f"Local file not found: {source_path}")

        with self.client.open_sftp() as sftp:
            sftp.put(str(source_path), remote_path)
    
    def close(self) -> None:
        """Close the SSH connection safely."""
        if self.client:
            self.client.close()
            self.client = None

    def __enter__(self):
        """Allow the client to be used as a context manager."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure connection is closed when the context manager exits."""
        self.close()