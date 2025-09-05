import json
import pytest
from app import create_app


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(scope="module")
def test_data():
    """Load the test data from an external file for use in tests."""
    with open('data/seed.json', 'r') as file:
        return json.load(file)
