import typer
from commands import deploy, destroy, status, validate

app = typer.Typer(help="Cloud infrastructure command line toolkit.")

app.add_typer(deploy.app, name="deploy")
app.add_typer(destroy.app, name="destroy")
app.add_typer(status.app, name="status")
app.add_typer(validate.app, name="validate")

if __name__ == "__main__":
    app()