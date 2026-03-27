import typer
from ssh.client import SSHClient, get_terraform_outputs, load_settings

app = typer.Typer()

@app.callback(invoke_without_command=True)
def status():
    print("[INFO] Retrieving infrastructure info...")

    outputs = get_terraform_outputs()
    settings = load_settings()

    print("[INFO] Connecting via SSH...")
    with SSHClient(
        host=outputs["public_ip"],
        key_path=settings["ssh"]["key_path"],
        user=settings["ssh"]["user"]
    ) as ssh:
        print("[SUCCESS] Connected successfully!")
        
        stdout, stderr = ssh.run("uptime")
        print(f"[STATUS] Server Uptime: {stdout.strip()}")