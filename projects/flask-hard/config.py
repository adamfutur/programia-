import os

FLASK_CONFIG = os.environ.get("FLASK_CONFIG", "default")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"


class DevelopmentConfig(Config):
    DEBUG = True
    CRITICAL = 10
    WARNING = 30
    INFO = 60


class TestingConfig(Config):
    TESTING = True
    CRITICAL = 5
    WARNING = 10
    INFO = 15


class ProductionConfig(Config):
    CRITICAL = 60
    WARNING = 180
    INFO = 300


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
