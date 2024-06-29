from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from models import Base  # Import your models module
import os

# Define your database URL
DATABASE_URL = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/"
    f"{os.getenv('DB_NAME')}"
)


print(os.getenv("DB_HOST"))
# Create an engine and metadata object
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Drop all tables


def drop_all_tables():
    print("Dropping all tables...")
    Base.metadata.drop_all(engine)
    print("All tables dropped.")

# Create all tables


def create_all_tables():
    print("Creating all tables...")
    Base.metadata.create_all(engine)
    print("All tables created.")

# Main function to drop and recreate tables


def reset_database():
    drop_all_tables()
    create_all_tables()


# Prompt the user
if __name__ == "__main__":
    user_input = input(
        "This will drop all tables and recreate them. Are you sure? (yes/no): ")
    if user_input.lower() == 'yes':
        reset_database()
    else:
        print("Operation cancelled.")
