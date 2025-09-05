from flask import Flask
from config import config


def create_app(config_name="default"):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_name])

    from app.views import logs_blueprint
    app.register_blueprint(logs_blueprint)

    return app
