import os


class DefaultConfig:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 1800}
    MAX_CONTENT_LENGTH = 1024 * 1024


def environment_config():
    # Read on every factory call so each app can have its own configuration.
    return {
        "SQLALCHEMY_DATABASE_URI": os.getenv(
            "DB_URL", os.getenv("DATABASE_URL", "sqlite:///lec07.db")
        ),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
    }
