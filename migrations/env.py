import logging
import os

from alembic import context
from flask import current_app

# Grab Alembic Config
config = context.config

# Optional logging setup — only if alembic.ini exists
if config.config_file_name is not None and os.path.exists(config.config_file_name):
    from logging.config import fileConfig
    fileConfig(config.config_file_name)

# Use SQLAlchemy metadata from your Flask app (so autogenerate works)
target_metadata = current_app.extensions['migrate'].db.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no DB connection)."""
    url = current_app.config.get("SQLALCHEMY_DATABASE_URI")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (with DB connection)."""
    connectable = current_app.extensions['migrate'].db.engine

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
