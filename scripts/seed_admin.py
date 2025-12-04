import sys
import os

# アプリケーションディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import get_db, AdminUser
from admin.auth import create_admin_user

def seed_admin():
    print("Seeding admin user...")
    with get_db() as db:
        # 既存チェック
        existing = db.query(AdminUser).filter(AdminUser.username == 'admin').first()
        if existing:
            print("Admin user already exists.")
            return

        create_admin_user(db, 'admin', 'admin123', 'admin@example.com')
        print("Admin user created successfully.")
        print("Username: admin")
        print("Password: admin123")

if __name__ == "__main__":
    seed_admin()
