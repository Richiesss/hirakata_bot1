"""管理者ダッシュボード - メインアプリケーション

Flaskベースの管理画面アプリケーション
"""

from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from datetime import datetime, timedelta
import pandas as pd
import io

from database.db_manager import get_db, Opinion, User, ChatSession, PointsHistory, AdminUser
from admin.auth import verify_password, create_admin_user
from config import SECRET_KEY

# ディレクトリパス
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Flask初期化
app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
app.config['SECRET_KEY'] = SECRET_KEY

# Flask-Login設定
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    """ユーザーローダー"""
    with get_db() as db:
        return db.query(AdminUser).filter(AdminUser.id == int(user_id)).first()


@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    """ログイン画面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        with get_db() as db:
            admin = db.query(AdminUser).filter(AdminUser.username == username).first()
            
            if admin and admin.is_active and verify_password(password, admin.password_hash):
                login_user(admin)
                admin.last_login_at = datetime.utcnow()
                db.commit()
                return redirect(url_for('dashboard'))
            else:
                flash('ユーザー名またはパスワードが正しくありません', 'error')
    
    return render_template('login.html')


@app.route('/admin/logout')
@login_required
def logout():
    """ログアウト"""
    logout_user()
    return redirect(url_for('login'))


@app.route('/admin')
@app.route('/admin/dashboard')
@login_required
def dashboard():
    """ダッシュボード画面"""
    with get_db() as db:
        # 基本統計
        total_opinions = db.query(Opinion).count()
        total_users = db.query(User).count()
        total_sessions = db.query(ChatSession).filter(ChatSession.status == 'completed').count()
        
        # 今日の統計
        today = datetime.utcnow().date()
        today_opinions = db.query(Opinion).filter(
            Opinion.created_at >= datetime.combine(today, datetime.min.time())
        ).count()
        
        # カテゴリ別集計
        category_stats = db.query(
            Opinion.category,
            db.func.count(Opinion.id).label('count')
        ).group_by(Opinion.category).all()
        
        # ソース別集計
        source_stats = db.query(
            Opinion.source_type,
            db.func.count(Opinion.id).label('count')
        ).group_by(Opinion.source_type).all()
        
        # 最近の意見
        recent_opinions = db.query(Opinion).order_by(
            Opinion.created_at.desc()
        ).limit(10).all()
        
        # 日別推移（過去7日間）
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        daily_stats = db.query(
            db.func.date(Opinion.created_at).label('date'),
            db.func.count(Opinion.id).label('count')
        ).filter(
            Opinion.created_at >= seven_days_ago
        ).group_by(db.func.date(Opinion.created_at)).all()
        
        return render_template('dashboard.html',
            total_opinions=total_opinions,
            total_users=total_users,
            total_sessions=total_sessions,
            today_opinions=today_opinions,
            category_stats=category_stats,
            source_stats=source_stats,
            recent_opinions=recent_opinions,
            daily_stats=daily_stats
        )


@app.route('/admin/opinions')
@login_required
def opinions():
    """意見一覧画面"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    category_filter = request.args.get('category')
    source_filter = request.args.get('source')
    
    with get_db() as db:
        query = db.query(Opinion)
        
        if category_filter:
            query = query.filter(Opinion.category == category_filter)
        if source_filter:
            query = query.filter(Opinion.source_type == source_filter)
        
        # ページネーション
        total = query.count()
        opinions_list = query.order_by(
            Opinion.created_at.desc()
        ).offset((page - 1) * per_page).limit(per_page).all()
        
        # カテゴリ一覧（フィルタ用）
        categories = db.query(Opinion.category).distinct().all()
        categories = [c[0] for c in categories if c[0]]
        
        return render_template('opinions.html',
            opinions=opinions_list,
            page=page,
            per_page=per_page,
            total=total,
            categories=categories,
            current_category=category_filter,
            current_source=source_filter
        )


@app.route('/admin/export/csv')
@login_required
def export_csv():
    """CSV出力"""
    with get_db() as db:
        opinions = db.query(Opinion).order_by(Opinion.created_at.desc()).all()
        
        # DataFrameに変換
        data = []
        for op in opinions:
            data.append({
                'ID': op.id,
                '作成日時': op.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'カテゴリ': op.category,
                'ソース': op.source_type,
                '内容': op.content,
                '感情スコア': op.emotion_score,
                '優先度スコア': op.priority_score
            })
        
        df = pd.DataFrame(data)
        
        # CSVとして出力
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'opinions_{datetime.now().strftime("%Y%m%d")}.csv'
        )


@app.route('/admin/stats')
@login_required
def stats():
    """統計・分析画面"""
    with get_db() as db:
        # カテゴリ別集計
        category_data = db.query(
            Opinion.category,
            db.func.count(Opinion.id).label('count'),
            db.func.avg(Opinion.emotion_score).label('avg_emotion')
        ).group_by(Opinion.category).all()
        
        # 月別推移
        monthly_data = db.query(
            db.func.strftime('%Y-%m', Opinion.created_at).label('month'),
            db.func.count(Opinion.id).label('count')
        ).group_by(db.func.strftime('%Y-%m', Opinion.created_at)).all()
        
        return render_template('stats.html',
            category_data=category_data,
            monthly_data=monthly_data
        )


if __name__ == '__main__':
    # 初回起動時に管理者ユーザーを作成
    with get_db() as db:
        admin_exists = db.query(AdminUser).filter(AdminUser.username == 'admin').first()
        if not admin_exists:
            create_admin_user(db, 'admin', 'admin123')  # デフォルトパスワード
            print("Default admin user created: admin / admin123")
    
    app.run(host='0.0.0.0', port=8080, debug=True)
