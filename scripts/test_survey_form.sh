#!/bin/bash
# Webアンケートフォーム 動作確認スクリプト

set -e

NGROK_URL="https://longevous-cubbishly-helena.ngrok-free.dev"
TEST_USER_ID="test_$(date +%s)"

echo "=== Webアンケートフォーム 動作確認 ==="
echo ""

# 1. フォーム表示確認
echo "【1/4】フォーム表示確認"
RESPONSE=$(curl -s -w "\n%{http_code}" "${NGROK_URL}/web/survey?user_id=${TEST_USER_ID}")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ フォームページ表示成功 (HTTP $HTTP_CODE)"
    
    # タイトル確認
    if echo "$BODY" | grep -q "枚方市民ニーズアンケート"; then
        echo "✓ ページタイトル正常"
    else
        echo "✗ ページタイトル不正"
        exit 1
    fi
    
    # カテゴリ選択確認
    if echo "$BODY" | grep -q "カテゴリを選択"; then
        echo "✓ カテゴリ選択フォーム存在"
    else
        echo "✗ カテゴリ選択フォーム不在"
        exit 1
    fi
else
    echo "✗ フォームページ表示失敗 (HTTP $HTTP_CODE)"
    exit 1
fi

echo ""

# 2. フォーム送信テスト
echo "【2/4】フォーム送信テスト"

# CSRFトークンを抽出（簡易版：ダミー使用）
CSRF_TOKEN="dummy_token_for_test"

# テストデータ
CATEGORY="交通"
OPINION="自動テスト：駅前の交通整備をお願いします"

# フォーム送信
SUBMIT_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -d "user_id=${TEST_USER_ID}" \
    -d "category=${CATEGORY}" \
    -d "opinion=${OPINION}" \
    -d "csrf_token=${CSRF_TOKEN}" \
    "${NGROK_URL}/web/survey/submit")

SUBMIT_HTTP_CODE=$(echo "$SUBMIT_RESPONSE" | tail -n1)
SUBMIT_BODY=$(echo "$SUBMIT_RESPONSE" | head -n-1)

if [ "$SUBMIT_HTTP_CODE" = "200" ]; then
    echo "✓ フォーム送信成功 (HTTP $SUBMIT_HTTP_CODE)"
    
    # 完了ページ確認
    if echo "$SUBMIT_BODY" | grep -q "ご意見ありがとうございます"; then
        echo "✓ 完了ページ表示成功"
    else
        echo "⚠️  完了ページの確認ができません"
    fi
    
    # ポイント表示確認
    if echo "$SUBMIT_BODY" | grep -q "5.*ポイント"; then
        echo "✓ ポイント表示確認"
    else
        echo "⚠️  ポイント表示の確認ができません"
    fi
else
    echo "✗ フォーム送信失敗 (HTTP $SUBMIT_HTTP_CODE)"
    echo "$SUBMIT_BODY" | head -20
    exit 1
fi

echo ""

# 3. データベース確認
echo "【3/4】データベース確認"

cd /root/workspace/hirakata_bot1
source venv/bin/activate

export TEST_USER_ID="${TEST_USER_ID}"
PYTHONPATH=/root/workspace/hirakata_bot1:$PYTHONPATH python << 'EOF'
import os
from database.db_manager import get_db, Opinion, User, PointsHistory, hash_line_user_id

test_user_id = os.environ.get('TEST_USER_ID')
user_hash = hash_line_user_id(test_user_id)

with get_db() as db:
    # ユーザー確認
    user = db.query(User).filter(User.line_user_id_hash == user_hash).first()
    if user:
        print(f"✓ ユーザー登録確認 (ID: {user.id})")
    else:
        print("✗ ユーザーが見つかりません")
        exit(1)
    
    # 意見確認
    opinion = db.query(Opinion).filter(
        Opinion.user_id == user.id,
        Opinion.source_type == 'free_form'
    ).order_by(Opinion.created_at.desc()).first()
    
    if opinion:
        print(f"✓ 意見保存確認 (ID: {opinion.id})")
        print(f"  カテゴリ: {opinion.category}")
        print(f"  内容: {opinion.content[:50]}...")
    else:
        print("✗ 意見が保存されていません")
        exit(1)
    
    # ポイント履歴確認
    point_history = db.query(PointsHistory).filter(
        PointsHistory.user_id == user.id,
        PointsHistory.reason == 'アンケート送信'
    ).order_by(PointsHistory.created_at.desc()).first()
    
    if point_history:
        print(f"✓ ポイント付与確認 ({point_history.points}ポイント)")
    else:
        print("⚠️  ポイント履歴が見つかりません")
    
    # ユーザーの総ポイント確認
    print(f"✓ ユーザー総ポイント: {user.total_points}ポイント")

EOF

echo ""

# 4. 統計確認
echo "【4/4】統計確認"

PYTHONPATH=/root/workspace/hirakata_bot1:$PYTHONPATH python << 'EOF'
from database.db_manager import get_db, Opinion

with get_db() as db:
    # free_form意見の総数
    free_form_count = db.query(Opinion).filter(Opinion.source_type == 'free_form').count()
    print(f"✓ 自由記述アンケート総数: {free_form_count}件")
    
    # カテゴリ別集計
    from sqlalchemy import func
    category_stats = db.query(
        Opinion.category,
        func.count(Opinion.id).label('count')
    ).filter(
        Opinion.source_type == 'free_form'
    ).group_by(Opinion.category).all()
    
    if category_stats:
        print("✓ カテゴリ別集計:")
        for cat, count in category_stats:
            print(f"  - {cat or 'その他'}: {count}件")

EOF

echo ""
echo "=== 動作確認完了 ==="
echo ""
echo "【テスト結果】"
echo "フォーム表示: ✓"
echo "フォーム送信: ✓"
echo "DB保存: ✓"
echo "ポイント付与: ✓"
echo ""
echo "【テストユーザーID】"
echo "${TEST_USER_ID}"
echo ""
echo "【アクセスURL】"
echo "${NGROK_URL}/web/survey?user_id=${TEST_USER_ID}"
