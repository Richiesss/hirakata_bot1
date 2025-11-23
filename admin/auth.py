"""認証・パスワード管理モジュール"""

import bcrypt
from database.db_manager import AdminUser


def hash_password(password: str) -> str:
    """パスワードをハッシュ化"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """パスワードを検証"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def create_admin_user(db, username: str, password: str, email: str = None):
    """管理者ユーザーを作成"""
    password_hash = hash_password(password)
    
    admin = AdminUser(
        username=username,
        password_hash=password_hash,
        email=email,
        is_active=True
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    return admin
