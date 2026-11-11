from alembic import context

from app.database.database import Base, importar_modelos

importar_modelos()
target_metadata = Base.metadata


def run_migrations_online() -> None:
    engine = context.config.attributes["engine"]
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
