"""Webアンケートフォーム用Flaskブループリント"""

from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime
import logging

from database.db_manager import get_db, get_or_create_user, add_points, Opinion
from config import OPINION_CATEGORIES, POINT_FREE_FORM

logger = logging.getLogger(__name__)

# Blueprint作成
survey_bp = Blueprint(
    'survey_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)


@survey_bp.route('/survey')
def survey_form():
    """アンケートフォームページ表示"""
    user_id = request.args.get('user_id', '')
    
    if not user_id:
        return render_template('survey_error.html', 
            error='ユーザー認証エラー',
            message='LINEアプリからアクセスしてください'
        ), 400
    
    # CSRFトークン生成（簡易版）
    import secrets
    csrf_token = secrets.token_hex(16)
    
    return render_template('survey_form.html',
        user_id=user_id,
        categories=OPINION_CATEGORIES,
        csrf_token=csrf_token
    )


@survey_bp.route('/survey/submit', methods=['POST'])
def submit_survey():
    """アンケート送信処理"""
    try:
        # フォームデータ取得
        line_user_id = request.form.get('user_id', '').strip()
        category = request.form.get('category', '').strip()
        opinion_text = request.form.get('opinion', '').strip()
        
        # バリデーション
        if not line_user_id:
            return render_template('survey_error.html',
                error='認証エラー',
                message='ユーザー情報が取得できませんでした'
            ), 400
        
        if not category or category not in OPINION_CATEGORIES:
            return render_template('survey_error.html',
                error='入力エラー',
                message='カテゴリを正しく選択してください'
            ), 400
        
        if not opinion_text:
            return render_template('survey_error.html',
                error='入力エラー',
                message='ご意見を入力してください'
            ), 400
        
        if len(opinion_text) > 1000:
            return render_template('survey_error.html',
                error='入力エラー',
                message='ご意見は1000文字以内で入力してください'
            ), 400
        
        # データベース処理
        with get_db() as db:
            # ユーザー取得または作成
            user = get_or_create_user(db, line_user_id)
            
            # 意見を保存
            opinion = Opinion(
                user_id=user.id,
                source_type='free_form',
                content=opinion_text,
                category=category,
                emotion_score=None,  # ユーザー選択のため
                priority_score=None,
                created_at=datetime.utcnow()
            )
            db.add(opinion)
            db.commit()
            
            # ポイント付与
            add_points(db, user.id, POINT_FREE_FORM, 'アンケート送信')
            
            logger.info(f"Free-form opinion submitted: user={user.id}, category={category}")
        
        # 成功ページ表示
        return render_template('survey_success.html',
            user_id=line_user_id,
            category=category,
            opinion=opinion_text,
            points=POINT_FREE_FORM
        )
        
    except Exception as e:
        logger.error(f"Error submitting survey: {e}", exc_info=True)
        return render_template('survey_error.html',
            error='システムエラー',
            message='送信に失敗しました。しばらくしてから再度お試しください'
        ), 500
