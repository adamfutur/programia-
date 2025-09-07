import click
import pytest
import os
from app import create_app

config_name = os.getenv("FLASK_CONFIG", "default")
app = create_app(config_name)


@app.cli.command("run")
def run():
    """Run the Flask application."""
    app.run()


@app.cli.command("test")
@click.argument("path", default="tests")
def test(path):
    """Run the tests."""
    result = pytest.main(["-v", path])
    exit(result)


if __name__ == "__main__":
    app.run()
