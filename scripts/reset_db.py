import sys
import os

# アプリケーションディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import Base, engine, init_db

def reset_db():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Tables dropped.")
    
    print("Recreating tables...")
    init_db()
    print("Database reset successfully.")

if __name__ == "__main__":
    reset_db()
