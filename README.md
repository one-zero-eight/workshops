# Workshops API | InNoHassle ecosystem

> https://api.innohassle.ru/workshops/v0

[![GitHub Actions pre-commit](https://img.shields.io/github/actions/workflow/status/one-zero-eight/workshops/pre-commit.yaml?label=pre-commit)](https://github.com/one-zero-eight/workshops/actions)

[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=one-zero-eight_workshops&metric=ncloc)](https://sonarcloud.io/summary/new_code?id=one-zero-eight_workshops)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=one-zero-eight_workshops&metric=bugs)](https://sonarcloud.io/summary/new_code?id=one-zero-eight_workshops)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=one-zero-eight_workshops&metric=vulnerabilities)](https://sonarcloud.io/summary/new_code?id=one-zero-eight_workshops)

## Table of contents

Did you know that GitHub supports table of
contents [by default](https://github.blog/changelog/2021-04-13-table-of-contents-support-in-markdown-files/) 🤔

## About

This is the API for workshops service in InNoHassle ecosystem. It provides backend functionality for managing workshops, user check-ins, and capacity management.

### Features

- ✅ Check-in/check-out workshops for bootcamp participants
- 👨‍💼 Manage workshops for admins
- 📊 Capacity management and tracking

### Technologies

- [Python 3.13+](https://www.python.org/downloads/) & [uv](https://astral.sh/uv/)
- [FastAPI](https://fastapi.tiangolo.com/)
- Database and ORM: [PostgreSQL](https://www.postgresql.org/), [SQLModel](https://sqlmodel.tiangolo.com/), [SQLAlchemy](https://www.sqlalchemy.org/), [Alembic](https://alembic.sqlalchemy.org/)

## Development

### Set up for development

1. Install [uv](https://astral.sh/uv/) and [Docker](https://docs.docker.com/engine/install/)
2. Install dependencies:
   ```bash
   uv sync
   ```
3. Start development server (read logs in the terminal):
   ```bash
   uv run -m src.api --reload
   ```
4. Open in the browser: http://localhost:8005
   > The api will be reloaded when you edit the code

> [!IMPORTANT]
> For endpoints requiring authorization click "Authorize" button in Swagger UI

> [!TIP]
> Edit `settings.yaml` according to your needs, you can view schema in
> [config_schema.py](src/config_schema.py) and in [settings.schema.yaml](settings.schema.yaml)

**Set up PyCharm integrations**

1. Run configurations ([docs](https://www.jetbrains.com/help/pycharm/run-debug-configuration.html#createExplicitly)).
   Right-click the `__main__.py` file in the project explorer, select `Run '__main__'` from the context menu.
2. Ruff ([plugin](https://plugins.jetbrains.com/plugin/20574-ruff)).
   It will lint and format your code. Make sure to enable `Use ruff format` option in plugin settings.
3. Pydantic ([plugin](https://plugins.jetbrains.com/plugin/12861-pydantic)). It will fix PyCharm issues with
   type-hinting.
4. Conventional commits ([plugin](https://plugins.jetbrains.com/plugin/13389-conventional-commit)). It will help you
   to write [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/).

## FAQ

### How to run tests?

1. Create `test-db` database in your local PostgreSQL:
   ```bash
   docker exec -it workshops-db-1 psql -U postgres -c 'CREATE DATABASE "test-db";'
   ```
2. Run tests with `SETTINGS_PATH=settings.test.yaml uv run pytest`

### How to setup database?

1. Run `docker compose up -d db` to start the PostgreSQL container (create `.env` file with options if needed)
2. Run `uv run alembic upgrade head` to apply all pending migrations
3. Run `uv run alembic revision --autogenerate -m "description"` to create new migration
4. Run `uv run alembic current` to check current migration status
5. Revert all migrations: `uv run alembic downgrade base`
6. Just set to `base` to revert to the initial state: `uv run alembic stamp base`

## Contributing

We are open to contributions of any kind.
You can help us with code, bugs, design, documentation, media, new ideas, etc.
If you are interested in contributing, please read
our [contribution guide](https://github.com/one-zero-eight/.github/blob/main/CONTRIBUTING.md).
