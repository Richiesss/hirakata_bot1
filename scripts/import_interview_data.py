#!/usr/bin/env python3
"""
interview.xlsxからテストデータをデータベースにインポートするスクリプト
"""

import sys
import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import hashlib
from datetime import datetime

# プロジェクトルートを追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATABASE_URL, LINE_ID_SALT, OPINION_CATEGORIES

def parse_gender(gender_str):
    """性別文字列を正規化"""
    if pd.isna(gender_str) or gender_str == 'ー' or gender_str == '-':
        return None
    if '女性' in str(gender_str) or '女' in str(gender_str):
        return '女性'
    if '男性' in str(gender_str) or '男' in str(gender_str):
        return '男性'
    return None

def parse_age(age_str):
    """年代文字列を正規化してage_range形式に変換"""
    if pd.isna(age_str) or age_str == 'ー' or age_str == '-':
        return None

    age_str = str(age_str).strip()

    # 年代を抽出
    if '20' in age_str or '２０' in age_str:
        return '20-29'
    elif '30' in age_str or '３０' in age_str:
        return '30-39'
    elif '40' in age_str or '４０' in age_str:
        return '40-49'
    elif '50' in age_str or '５０' in age_str:
        return '50-59'
    elif '60' in age_str or '６０' in age_str:
        return '60+'
    elif '70' in age_str or '７０' in age_str or '以上' in age_str:
        return '60+'

    return None

def categorize_opinion(content):
    """意見内容から簡易的にカテゴリを推測（キーワードベース）"""
    if pd.isna(content):
        return 'その他'

    content = str(content)

    # キーワードマッチング
    if any(keyword in content for keyword in ['道', '交通', 'バス', '駅', '電車', '車', '駐車', '信号']):
        return '交通'
    if any(keyword in content for keyword in ['福祉', '介護', '高齢', '年金']):
        return '福祉'
    if any(keyword in content for keyword in ['学校', '教育', '勉強', '先生', '塾']):
        return '教育'
    if any(keyword in content for keyword in ['環境', 'ゴミ', '公園', '緑', '自然', '川', '山']):
        return '環境'
    if any(keyword in content for keyword in ['子育て', '保育', '幼稚園', '子ども', '子供']):
        return '子育て'
    if any(keyword in content for keyword in ['医療', '病院', '診療', '健康', 'クリニック']):
        return '医療'
    if any(keyword in content for keyword in ['防災', '災害', '避難', '地震', '台風']):
        return '防災'

    return 'その他'

def create_test_user(conn, gender, age_range, user_index):
    """テスト用ユーザーを作成"""
    cursor = conn.cursor()

    # テスト用のLINE IDハッシュを生成
    test_line_id = f"test_user_{user_index}_{gender}_{age_range}"
    line_user_id_hash = hashlib.sha256(
        (test_line_id + LINE_ID_SALT).encode()
    ).hexdigest()

    # 表示名を生成
    gender_display = gender if gender else '不明'
    age_display = age_range if age_range else '不明'
    display_name = f"テストユーザー{user_index}({gender_display}/{age_display})"

    try:
        cursor.execute("""
            INSERT INTO users (line_user_id_hash, display_name, age_range, district, total_points, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (line_user_id_hash, display_name, age_range, '枚方市', 0, datetime.now()))

        user_id = cursor.fetchone()[0]
        conn.commit()
        return user_id
    except psycopg2.IntegrityError:
        # すでに存在する場合は既存のIDを取得
        conn.rollback()
        cursor.execute("""
            SELECT id FROM users WHERE line_user_id_hash = %s
        """, (line_user_id_hash,))
        return cursor.fetchone()[0]
    finally:
        cursor.close()

def import_interview_data(excel_path, clear_existing=False):
    """interview.xlsxデータをインポート"""

    print(f"Reading {excel_path}...")
    df = pd.read_excel(excel_path, header=1)

    # ヘッダー行を除去してクリーニングvscode-webview://1s9h9aggu7st6s8ms5luv0i33ft0rg6ogrl3t2q5e33cutvraqlp/index.html?id=aa17f500-946f-4cff-bbf9-bfb2ed96003b&parentId=1&origin=81d8344a-cc47-43e5-96ad-624e9342ad61&swVersion=4&extensionId=Anthropic.claude-code&platform=electron&vscode-resource-base-authority=vscode-resource.vscode-cdn.net&parentOrigin=vscode-file%3A%2F%2Fvscode-app&remoteAuthority=attached-container%2B7b22636f6e7461696e65724e616d65223a222f6d6c5f656e76222c2273657474696e6773223a7b22636f6e74657874223a226465736b746f702d6c696e7578227d7d%40tunnel%2Bsuyama-lab&session=09f16b14-40a9-4a51-91d4-3e4db5e4eca1#
    df = df[df['市民意見'] != 'アンケート内容(テキスト)'].copy()
    df = df[df['市民意見'] != 'アンケート内容（テキスト）'].copy()
    df = df.dropna(subset=['市民意見'])

    # 性別が「性別」というヘッダー行も除外
    df = df[df['回答者属性'] != '性別'].copy()

    print(f"Total rows to import: {len(df)}")

    # データベース接続
    print(f"Connecting to database: {DATABASE_URL}")
    conn = psycopg2.connect(DATABASE_URL)

    try:
        cursor = conn.cursor()

        # 既存データのクリア（オプション）
        if clear_existing:
            print("Clearing existing test data...")
            cursor.execute("DELETE FROM opinions WHERE source_type = 'imported_test_data'")
            cursor.execute("DELETE FROM users WHERE line_user_id_hash LIKE 'test_user_%'")
            conn.commit()
            print("Existing test data cleared.")

        # データインポート
        imported_count = 0
        user_cache = {}  # ユーザーキャッシュ

        for idx, row in df.iterrows():
            content = row['市民意見']
            gender = parse_gender(row['回答者属性'])
            age_range = parse_age(row['Unnamed: 4'])

            # カテゴリ分類
            category = categorize_opinion(content)

            # ユーザーを作成またはキャッシュから取得
            user_key = f"{gender}_{age_range}_{imported_count % 100}"  # 100人ずつユーザーを再利用
            if user_key not in user_cache:
                user_id = create_test_user(conn, gender, age_range, len(user_cache))
                user_cache[user_key] = user_id
            else:
                user_id = user_cache[user_key]

            # 意見を挿入
            cursor.execute("""
                INSERT INTO opinions
                (user_id, source_type, content, category, emotion_score, priority_score, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                'imported_test_data',
                content,
                category,
                5,  # デフォルト感情スコア
                1.0,  # デフォルト優先度スコア
                datetime.now()
            ))

            imported_count += 1

            if imported_count % 100 == 0:
                conn.commit()
                print(f"Imported {imported_count}/{len(df)} opinions...")

        conn.commit()
        print(f"\n✓ Successfully imported {imported_count} opinions")
        print(f"✓ Created {len(user_cache)} test users")

        # 統計情報を表示
        cursor.execute("""
            SELECT category, COUNT(*)
            FROM opinions
            WHERE source_type = 'imported_test_data'
            GROUP BY category
            ORDER BY COUNT(*) DESC
        """)
        print("\nCategory distribution:")
        for category, count in cursor.fetchall():
            print(f"  {category}: {count}")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        conn.close()

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Import interview.xlsx data into database')
    parser.add_argument('--clear', action='store_true',
                       help='Clear existing test data before import')
    parser.add_argument('--file', default='/home/hirakata_bot1/interview.xlsx',
                       help='Path to interview.xlsx file')

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        sys.exit(1)

    import_interview_data(args.file, clear_existing=args.clear)

if __name__ == '__main__':
    main()
