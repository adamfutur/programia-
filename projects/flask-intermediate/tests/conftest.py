import pytest
from app import create_app, db
from app.models import CustomUser
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def user(app):
    """Fixture to create a test user"""
    with app.app_context():
        user = CustomUser(username="testuser", password=generate_password_hash("password123"))
        db.session.add(user)
        db.session.commit()
    return user