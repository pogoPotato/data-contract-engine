import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Base, engine
from app.models.database import Contract, ContractVersion, ValidationResult, QualityMetric


def reset_database():
    print("⚠️  WARNING: This will delete ALL data!")
    response = input("Are you sure? Type 'yes' to continue: ")
    
    if response.lower() != 'yes':
        print("Operation cancelled.")
        return
    
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ Tables dropped")
    
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created")
    
    print("Database reset complete!")


if __name__ == "__main__":
    reset_database()