from alembic import command
from alembic.config import Config
import os


def run_migrations():
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "../alembic.ini"))
    alembic_cfg.set_main_option("script_location", "alembic/")
    command.upgrade(alembic_cfg, "head")


if __name__ == "__main__":
    run_migrations()
