import os
import click
from flask import Flask
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from config import config

db = SQLAlchemy()

def create_app(config_name='default'):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_name])
    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)
    app.config['JWT_SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    jwt = JWTManager(app)

    from app.views import user_blueprint
    app.register_blueprint(user_blueprint)

    app.cli.add_command(init_db_command)

    return app

def init_db():
    """Drop and create all tables in the database."""
    db.drop_all()
    db.create_all()

@click.command("init-db")
@with_appcontext
def init_db_command():
    """CLI command to initialize the database."""
    init_db()
    click.echo("Initialized the database.")
