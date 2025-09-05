from flask.cli import with_appcontext
import click
import pytest
import os
import json
from app import create_app, db
from app.models import Event

config_name = os.getenv('FLASK_CONFIG', 'default')
app = create_app(config_name)

@app.cli.command("run")
def run():
    """Run the Flask application."""
    app.run()

@app.cli.command("test")
@click.argument('path', default='tests')
def test(path):
    """Run the tests."""
    result = pytest.main(['-v', path])
    exit(result)

@app.cli.command("seed")
@with_appcontext
def seed():
    """Seed the database with data from a JSON file."""
    with open('data/seed_data.json') as f:
        data = json.load(f)
        for event_data in data['events']:
            event = Event(
                name=event_data['name'],
                date=datetime.strptime(event_data['date'], '%d-%m-%Y'),
                venue=event_data['venue'],
                available_tickets=event_data['available_tickets'],
                price=event_data['price']
            )
            db.session.add(event)
        db.session.commit()
    click.echo("Database seeded with JSON data!")

if __name__ == "__main__":
    app.run()
