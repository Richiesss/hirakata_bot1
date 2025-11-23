"""管理者ダッシュボード - メインアプリケーション

Flaskベースの管理画面アプリケーション
"""

from flask import Flask, render_template, redirect, url_for, request, flash, send_file, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import func
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

# セッションをアプリケーションレベルで管理
from database.db_manager import SessionLocal

@login_manager.user_loader
def load_user(user_id):
    """ユーザーローダー"""
    db = SessionLocal()
    try:
        user = db.query(AdminUser).filter(AdminUser.id == int(user_id)).first()
        if user:
            # セッションから切り離して返す（expunge）
            db.expunge(user)
        return user
    finally:
        db.close()


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
            func.count(Opinion.id).label('count')
        ).group_by(Opinion.category).all()
        
        # ソース別集計
        source_stats = db.query(
            Opinion.source_type,
            func.count(Opinion.id).label('count')
        ).group_by(Opinion.source_type).all()
        
        # 最近の意見
        recent_opinions = db.query(Opinion).order_by(
            Opinion.created_at.desc()
        ).limit(10).all()
        
        # 日別推移（過去7日間）
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        daily_stats = db.query(
            func.date(Opinion.created_at).label('date'),
            func.count(Opinion.id).label('count')
        ).filter(
            Opinion.created_at >= seven_days_ago
        ).group_by(func.date(Opinion.created_at)).all()
        
        # daily_statsの最大値を計算
        daily_stats_max = max([d.count for d in daily_stats]) if daily_stats else 1
        
        return render_template('dashboard.html',
            total_opinions=total_opinions,
            total_users=total_users,
            total_sessions=total_sessions,
            today_opinions=today_opinions,
            category_stats=category_stats,
            source_stats=source_stats,
            recent_opinions=recent_opinions,
            daily_stats=daily_stats,
            daily_stats_max=daily_stats_max
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
            func.count(Opinion.id).label('count'),
            func.avg(Opinion.emotion_score).label('avg_emotion')
        ).group_by(Opinion.category).all()
        
        # 月別推移
        monthly_data = db.query(
            func.strftime('%Y-%m', Opinion.created_at).label('month'),
            func.count(Opinion.id).label('count')
        ).group_by(func.strftime('%Y-%m', Opinion.created_at)).all()
        
        return render_template('stats.html',
            category_data=category_data,
            monthly_data=monthly_data
        )


@app.route('/admin/polls')
@login_required
def polls():
    """投票一覧画面"""
    from database.db_manager import Poll, PollResponse
    
    with get_db() as db:
        polls_list = db.query(Poll).order_by(Poll.created_at.desc()).all()
        
        # 各投票の回答数を集計
        for poll in polls_list:
            poll.response_count = db.query(PollResponse).filter(
                PollResponse.poll_id == poll.id
            ).count()
        
        return render_template('polls.html', polls=polls_list)


@app.route('/admin/polls/create', methods=['POST'])
@login_required
def create_poll():
    """投票作成"""
    from features.poll_manager import create_poll as create_poll_func
    
    question = request.form.get('question')
    choices = [
        request.form.get('choice_1'),
        request.form.get('choice_2'),
        request.form.get('choice_3'),
        request.form.get('choice_4')
    ]
    description = request.form.get('description')
    
    try:
        poll_id = create_poll_func(question, choices, description)
        flash(f'投票を作成しました（ID: {poll_id}）', 'success')
    except Exception as e:
        flash(f'エラーが発生しました: {str(e)}', 'error')
    
    return redirect(url_for('polls'))


@app.route('/admin/polls/<int:poll_id>/send')
@login_required
def send_poll(poll_id):
    """投票配信（公開）"""
    from features.poll_manager import send_poll_to_users
    from database.db_manager import Poll
    from datetime import datetime
    
    try:
        # 投票を配信
        result = send_poll_to_users(poll_id)
        
        msg = f'投票を配信・公開しました。（成功: {result["success"]}件, 失敗: {result["failed"]}件）'
        if result["success"] == 0:
            msg += ' ※プッシュ通知を送るには、ユーザーが一度ボットにメッセージを送る必要があります。'
            
        flash(msg, 'success')
                
    except Exception as e:
        flash(f'エラーが発生しました: {str(e)}', 'error')
    
    return redirect(url_for('polls'))


@app.route('/admin/polls/<int:poll_id>/results')
@login_required
def poll_results(poll_id):
    """投票結果表示"""
    from features.poll_manager import get_poll_results
    
    try:
        results = get_poll_results(poll_id)
        return render_template('poll_results.html', results=results)
    except Exception as e:
        flash(f'エラーが発生しました: {str(e)}', 'error')
        return redirect(url_for('polls'))


@app.route('/admin/analysis')
@login_required
def analysis():
    """AI分析ダッシュボード"""
    # セッションに保存された結果があれば表示
    results = session.get('analysis_results')
    return render_template('analysis.html', results=results)

@app.route('/admin/analysis/run', methods=['POST'])
@login_required
def run_analysis():
    """分析を実行"""
    from features.ai_analysis import get_analyzer
    
    try:
        # 意見データを取得
        with get_db() as db:
            opinions = db.query(Opinion).order_by(Opinion.created_at.desc()).limit(200).all() # 件数制限
            
            if not opinions:
                flash('分析する意見データがありません。', 'warning')
                return redirect(url_for('analysis'))
                
            opinion_data = [
                {"id": op.id, "text": op.content}
                for op in opinions
                if len(op.content) > 5 # 短すぎる意見は除外
            ]
        
        if not opinion_data:
            flash('有効な意見データがありません。', 'warning')
            return redirect(url_for('analysis'))

        # 分析実行
        analyzer = get_analyzer()
        results = analyzer.analyze_opinions(opinion_data)
        
        if "error" in results:
            flash(f'分析エラー: {results["error"]}', 'error')
        else:
            # 結果をセッションに保存（サイズに注意。大きすぎる場合はDBかファイルへ）
            # プロット画像がBase64で大きい可能性があるため、本来はファイル保存推奨
            # ここでは簡易的にセッションを使うが、容量オーバーのリスクあり
            # -> 安全のため、プロット画像以外をセッションに入れ、画像は一時ファイルにするか...
            # 今回はデモなのでそのままいくが、エラーが出たら修正する
            session['analysis_results'] = results
            flash('分析が完了しました。', 'success')
            
    except Exception as e:
        flash(f'システムエラー: {str(e)}', 'error')
        
    return redirect(url_for('analysis'))


@app.route('/admin/polls/<int:poll_id>/close')
@login_required  
def close_poll(poll_id):
    """投票締切"""
    from features.poll_manager import close_poll as close_poll_func
    
    try:
        close_poll_func(poll_id)
        flash('投票を締め切りました', 'success')
    except Exception as e:
        flash(f'エラーが発生しました: {str(e)}', 'error')
    
    return redirect(url_for('polls'))


if __name__ == '__main__':
    # 初回起動時に管理者ユーザーを作成
    with get_db() as db:
        admin_exists = db.query(AdminUser).filter(AdminUser.username == 'admin').first()
        if not admin_exists:
            create_admin_user(db, 'admin', 'admin123')  # デフォルトパスワード
            print("Default admin user created: admin / admin123")
    
    app.run(host='0.0.0.0', port=8080, debug=True)
