# 管理者ダッシュボード利用ガイド

## 概要

枚方市民ニーズ抽出システムの管理者向けダッシュボードです。
収集した市民の意見を可視化・分析できます。

## 機能

- ✅ **ダッシュボード**: 意見数、カテゴリ別・ソース別分布、日別推移をグラフ表示
- ✅ **意見一覧**: フィルタリング・ページネーション機能付き一覧表示
- ✅ **統計・分析**: カテゴリ別・月別の統計データ
- ✅ **CSV出력**: 全意見データをCSV形式でエクスポート
- ✅ **認証**: ログイン・ログアウト機能

## セットアップ

### 1. 依存パッケージのインストール

```bash
cd /root/workspace/hirakata_bot1
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 管理者ユーザーの作成（初回のみ）

管理画面を初回起動すると、デフォルトの管理者アカウントが自動作成されます:
- ユーザー名: `admin`
- パスワード: `admin123`

### 3. テストデータの作成（オプション）

```bash
PYTHONPATH=/root/workspace/hirakata_bot1:$PYTHONPATH python scripts/create_test_data.py
```

これにより、テスト用のユーザーと意見データが作成されます。

## 起動方法

### 通常起動

```bash
cd /root/workspace/hirakata_bot1
source venv/bin/activate
PYTHONPATH=/root/workspace/hirakata_bot1:$PYTHONPATH python admin/admin_app.py
```

管理画面にアクセス: `http://localhost:8080/admin/login`

### バックグラウンド起動

```bash
cd /root/workspace/hirakata_bot1
source venv/bin/activate
nohup env PYTHONPATH=/root/workspace/hirakata_bot1:$PYTHONPATH python admin/admin_app.py > admin.log 2>&1 &
```

## 使い方

### ログイン

1. ブラウザで `http://localhost:8080/admin/login` にアクセス
2. ユーザー名: `admin`、パスワード: `admin123` でログイン

### ダッシュボード

- **サマリーカード**: 総意見数、本日の意見数、登録ユーザー数、完了セッション数
- **カテゴリ別分布**: 意見のカテゴリ別集計（交通、環境、教育など）
- **ソース別分布**: 意見収集方法別（対話型、自由記述、選択式）
- **日別推移**: 過去7日間の意見数推移
- **最近の意見**: 最新10件の意見リスト

### 意見一覧

- **フィルタリング**: カテゴリ・ソース別にフィルタ可能
- **ページネーション**: 1ページ20件表示
- **詳細表示**: ID、日時、カテゴリ、内容、感情スコア、優先度を表示

### CSV出力

- ダッシュボードのサイドバーから「CSV出力」をクリック
- 全意見データがCSVファイルとしてダウンロードされます
- ファイル名: `opinions_YYYYMMDD.csv`

## 画面構成

```
admin/
├── admin_app.py          # メインアプリケーション
├── auth.py               # 認証機能
├── templates/
│   ├── base.html         # ベーステンプレート
│   ├── login.html        # ログイン画面
│   ├── dashboard.html    # ダッシュボード
│   ├── opinions.html     # 意見一覧
│   └── stats.html        # 統計・分析
└── static/
    └── css/
        └── admin.css     # スタイルシート
```

## トラブルシューティング

### ポート8080が使用中

別のポートで起動:
```bash
# admin_app.pyの最終行を編集
app.run(host='0.0.0.0', port=8081, debug=True)
```

### ログインできない

デフォルトの管理者アカウントを再作成:
```python
from database.db_manager import get_db, AdminUser
from admin.auth import create_admin_user

with get_db() as db:
    # 既存アカウント削除
    admin = db.query(AdminUser).filter(AdminUser.username == 'admin').first()
    if admin:
        db.delete(admin)
        db.commit()
    
    # 再作成
    create_admin_user(db, 'admin', 'admin123')
```

### パッケージエラー

依存パッケージを再インストール:
```bash
pip install --force-reinstall Flask-Login pandas plotly
```

## セキュリティ注意事項

⚠️ **本番環境での使用前に必ず実施してください**:

1. **デフォルトパスワードの変更**: `admin123`から強力なパスワードに変更
2. **SECRET_KEYの変更**: `.env`のSECRET_KEYをランダムな値に変更
3. **HTTPS化**: 本番環境ではHTTPSを使用
4. **ファイアウォール設定**: 管理画面へのアクセスを制限

## 今後の拡張機能（未実装）

- PDF/Excelレポート生成
- アンケート配信管理
- ポイント管理画面
- ユーザー分析
- AIによる傾向分析グラフ
