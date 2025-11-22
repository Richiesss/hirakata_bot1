"""データベース管理モジュール

SQLAlchemyを使用したデータベース接続・操作管理
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import hashlib
from contextlib import contextmanager

from config import DATABASE_URL, LINE_ID_SALT

# SQLAlchemy設定
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# モデル定義
class User(Base):
    """ユーザーモデル"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    line_user_id_hash = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(255))
    age_range = Column(String(20))
    district = Column(String(100))
    total_points = Column(Integer, default=0)
    notification_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーション
    opinions = relationship("Opinion", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
    poll_responses = relationship("PollResponse", back_populates="user")
    points_history = relationship("PointsHistory", back_populates="user")


class Opinion(Base):
    """意見モデル"""
    __tablename__ = "opinions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    source_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50))
    emotion_score = Column(Integer)
    priority_score = Column(Float)
    cluster_id = Column(Integer)
    session_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーション
    user = relationship("User", back_populates="opinions")


class ChatSession(Base):
    """対話セッションモデル"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="active")
    turn_count = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    summary_text = Column(Text)
    summary_category = Column(String(50))
    summary_emotion_score = Column(Integer)
    
    # リレーション
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """対話メッセージモデル"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # リレーション
    session = relationship("ChatSession", back_populates="messages")


class Poll(Base):
    """アンケートモデル"""
    __tablename__ = "polls"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="draft")
    created_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)
    closed_at = Column(DateTime)
    
    # リレーション
    options = relationship("PollOption", back_populates="poll", cascade="all, delete-orphan")
    responses = relationship("PollResponse", back_populates="poll", cascade="all, delete-orphan")


class PollOption(Base):
    """アンケート選択肢モデル"""
    __tablename__ = "poll_options"
    
    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id", ondelete="CASCADE"), nullable=False)
    option_text = Column(Text, nullable=False)
    option_order = Column(Integer, default=0)
    is_other = Column(Boolean, default=False)
    based_on_opinion_id = Column(Integer, ForeignKey("opinions.id", ondelete="SET NULL"))
    
    # リレーション
    poll = relationship("Poll", back_populates="options")


class PollResponse(Base):
    """アンケート回答モデル"""
    __tablename__ = "poll_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    option_id = Column(Integer, ForeignKey("poll_options.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # リレーション
    poll = relationship("Poll", back_populates="responses")
    user = relationship("User", back_populates="poll_responses")


class PointsHistory(Base):
    """ポイント履歴モデル"""
    __tablename__ = "points_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    points = Column(Integer, nullable=False)
    reason = Column(String(100), nullable=False)
    reference_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # リレーション
    user = relationship("User", back_populates="points_history")


class AdminUser(Base):
    """管理者ユーザーモデル"""
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime)


# ユーティリティ関数
def hash_line_user_id(line_user_id: str) -> str:
    """LINE User IDをハッシュ化"""
    salted = f"{line_user_id}{LINE_ID_SALT}"
    return hashlib.sha256(salted.encode()).hexdigest()


@contextmanager
def get_db():
    """データベースセッションのコンテキストマネージャー"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """データベーステーブルを初期化"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")


def get_or_create_user(db, line_user_id: str, display_name: str = None):
    """ユーザーを取得または新規作成"""
    user_hash = hash_line_user_id(line_user_id)
    user = db.query(User).filter(User.line_user_id_hash == user_hash).first()
    
    if not user:
        user = User(
            line_user_id_hash=user_hash,
            display_name=display_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user


def add_points(db, user_id: int, points: int, reason: str, reference_id: int = None):
    """ユーザーにポイントを付与"""
    # ユーザーの累積ポイント更新
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.total_points += points
        
        # 履歴登録
        history = PointsHistory(
            user_id=user_id,
            points=points,
            reason=reason,
            reference_id=reference_id
        )
        db.add(history)
        db.commit()
        return user.total_points
    return None


if __name__ == "__main__":
    # テスト実行
    init_db()
