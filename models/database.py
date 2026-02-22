"""
Database connection and setup utilities.
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    """Create and return a SQLAlchemy engine."""
   
    url = (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )

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
