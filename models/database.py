"""
Database connection and setup utilities.
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()


def _build_database_url() -> str:
    """Build database URL from DATABASE_URL or DB_* environment variables."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    required_vars = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_NAME"]
    missing_vars = [name for name in required_vars if not os.getenv(name)]
    if missing_vars:
        missing_str = ", ".join(missing_vars)
        raise ValueError(
            "Database configuration is incomplete. Set DATABASE_URL or define "
            f"the following environment variables: {missing_str}."
        )

    db_port = os.getenv("DB_PORT", "5432")
    return (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{db_port}/{os.getenv('DB_NAME')}"
    )


def get_engine():
    """Create and return a SQLAlchemy engine."""
    url = _build_database_url()
    return create_engine(url, connect_args={"sslmode": "require"})


def init_db():
    """Initialize the database by running the schema SQL file."""
    engine = get_engine()
    schema_path = os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql")

    with open(schema_path, "r") as f:
        schema_sql = f.read()

    with engine.connect() as conn:
        conn.execute(text(schema_sql))
        conn.commit()

    print("✅ Database initialized successfully.")


if __name__ == "__main__":
    init_db()
