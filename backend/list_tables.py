import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def list_all_tables():
    """Connects to the database and lists all tables in the public schema."""
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not found in .env file.")
        return

    engine = create_engine(db_url)
    
    with engine.connect() as connection:
        query = text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
        result = connection.execute(query)
        tables = [row[0] for row in result]

        print("Tables in the database:")
        for table in tables:
            print(f"- {table}")

if __name__ == "__main__":
    list_all_tables()