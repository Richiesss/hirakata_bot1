import hashlib
import os
from database.db_manager import User, Opinion, Poll, PollResponse, PollOption

def generate_hash(user_id):
    salt = os.environ.get('LINE_ID_SALT', 'test_salt')
    return hashlib.sha256((user_id + salt).encode()).hexdigest()

def test_user_creation(db_session):
    """ユーザー作成テスト"""
    user_id = "test_user_1"
    user = User(
        line_user_id=user_id, 
        line_user_id_hash=generate_hash(user_id),
        display_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    
    saved_user = db_session.query(User).filter_by(line_user_id="test_user_1").first()
    assert saved_user is not None
    assert saved_user.display_name == "Test User"
    assert saved_user.total_points == 0
    assert saved_user.notification_enabled is True

def test_opinion_creation(db_session):
    """意見作成テスト"""
    user_id = "test_user_2"
    user = User(
        line_user_id=user_id,
        line_user_id_hash=generate_hash(user_id)
    )
    db_session.add(user)
    db_session.commit()
    
    opinion = Opinion(
        user_id=user.id,
        content="もっと公園を増やしてほしい",
        source_type="text_message",
        priority_score=0.5
    )
    db_session.add(opinion)
    db_session.commit()
    
    saved_opinion = db_session.query(Opinion).first()
    assert saved_opinion.content == "もっと公園を増やしてほしい"
    assert saved_opinion.user_id == user.id

def test_poll_response(db_session):
    """投票機能テスト"""
    user_id = "test_user_3"
    user = User(
        line_user_id=user_id,
        line_user_id_hash=generate_hash(user_id)
    )
    db_session.add(user)
    db_session.commit()
    
    poll = Poll(title="新しい公園について", description="どこがいい？")
    db_session.add(poll)
    db_session.commit()
    
    option1 = PollOption(poll_id=poll.id, option_text="駅前", option_order=1)
    option2 = PollOption(poll_id=poll.id, option_text="郊外", option_order=2)
    db_session.add(option1)
    db_session.add(option2)
    db_session.commit()
    
    response = PollResponse(
        poll_id=poll.id,
        user_id=user.id,
        option_id=option1.id
    )
    db_session.add(response)
    db_session.commit()
    
    saved_response = db_session.query(PollResponse).first()
    assert saved_response.option_id == option1.id
    assert saved_response.poll_id == poll.id
