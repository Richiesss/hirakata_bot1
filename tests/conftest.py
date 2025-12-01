import pytest
import os
import sys

# プロジェクトルートをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app
from database.db_manager import Base, User, Opinion, Poll
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

@pytest.fixture
def app():
    """テスト用Flaskアプリ"""
    flask_app.config.update({
        "TESTING": True,
        "DATABASE_URL": "sqlite:///:memory:"  # インメモリDB
    })
    return flask_app

@pytest.fixture
def client(app):
    """テスト用クライアント"""
    return app.test_client()

@pytest.fixture
def db_session(app):
    """テスト用DBセッション"""
    engine = create_engine(app.config["DATABASE_URL"])
    Base.metadata.create_all(engine)
    
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    
    # db_managerのget_dbをオーバーライドするための準備
    # (実際にはdb_manager.get_dbがDATABASE_URL環境変数を読むようにするか、
    #  ここでパッチを当てる必要があるが、簡易的に環境変数をセット)
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    
    yield Session
    
    Session.remove()
    Base.metadata.drop_all(engine)
