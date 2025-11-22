-- 枚方市民ニーズ抽出システム データベーススキーマ
-- PostgreSQL 12+

-- ユーザーテーブル
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    line_user_id_hash VARCHAR(255) UNIQUE NOT NULL,  -- LINE User IDのハッシュ値
    display_name VARCHAR(255),
    age_range VARCHAR(20),  -- '20-29', '30-39', '40-49', '50-59', '60+'
    district VARCHAR(100),  -- 居住地区
    total_points INTEGER DEFAULT 0,
    notification_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 意見テーブル
CREATE TABLE IF NOT EXISTS opinions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    source_type VARCHAR(20) NOT NULL,  -- 'chat', 'free_form', 'poll'
    content TEXT NOT NULL,  -- 意見内容（要約文または自由記述）
    category VARCHAR(50),  -- AI分類カテゴリ
    emotion_score INTEGER,  -- 感情スコア (0-10)
    priority_score FLOAT,  -- 優先度スコア（AI算出）
    cluster_id INTEGER,  -- クラスタリングID
    session_id INTEGER,  -- 対話セッションID（chat型の場合）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 対話セッションテーブル
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'completed', 'abandoned'
    turn_count INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    summary_text TEXT,  -- 最終要約
    summary_category VARCHAR(50),
    summary_emotion_score INTEGER
);

-- 対話メッセージテーブル
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- アンケート定義テーブル
CREATE TABLE IF NOT EXISTS polls (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'draft',  -- 'draft', 'active', 'closed'
    created_by INTEGER,  -- 管理者ID（将来拡張）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP,
    closed_at TIMESTAMP
);

-- アンケート選択肢テーブル
CREATE TABLE IF NOT EXISTS poll_options (
    id SERIAL PRIMARY KEY,
    poll_id INTEGER REFERENCES polls(id) ON DELETE CASCADE,
    option_text TEXT NOT NULL,
    option_order INTEGER DEFAULT 0,
    is_other BOOLEAN DEFAULT FALSE,  -- 「該当なし」フラグ
    based_on_opinion_id INTEGER REFERENCES opinions(id) ON DELETE SET NULL  -- 元となった意見ID
);

-- アンケート回答テーブル
CREATE TABLE IF NOT EXISTS poll_responses (
    id SERIAL PRIMARY KEY,
    poll_id INTEGER REFERENCES polls(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    option_id INTEGER REFERENCES poll_options(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(poll_id, user_id)  -- 1ユーザー1回答のみ
);

-- ポイント履歴テーブル
CREATE TABLE IF NOT EXISTS points_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    points INTEGER NOT NULL,
    reason VARCHAR(100) NOT NULL,  -- 'chat_opinion', 'free_form', 'poll_response'
    reference_id INTEGER,  -- 関連するopinion_idやpoll_response_id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 管理者ユーザーテーブル
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_opinions_user_id ON opinions(user_id);
CREATE INDEX IF NOT EXISTS idx_opinions_category ON opinions(category);
CREATE INDEX IF NOT EXISTS idx_opinions_created_at ON opinions(created_at);
CREATE INDEX IF NOT EXISTS idx_opinions_cluster_id ON opinions(cluster_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_status ON chat_sessions(status);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_poll_responses_poll_id ON poll_responses(poll_id);
CREATE INDEX IF NOT EXISTS idx_points_history_user_id ON points_history(user_id);

-- トリガー関数: updated_atの自動更新
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- トリガー設定
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_opinions_updated_at ON opinions;
CREATE TRIGGER update_opinions_updated_at BEFORE UPDATE ON opinions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
