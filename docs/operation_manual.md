# 枚方市民ニーズ抽出ハイブリッドシステム 運用マニュアル

## 1. システム概要
本システムは、LINE BotとWeb管理画面から構成されるハイブリッドシステムです。
- **LINE Bot**: 市民との対話、アンケート収集 (Port: 5000)
- **管理画面**: データ分析、設定管理 (Port: 8080)
- **データベース**: SQLite (instance/hirakata_bot.sqlite)

## 2. 起動・停止手順

### Dockerを使用する場合（推奨）
**準備:**
1. `.env.production` ファイルを開き、必要な環境変数（LINEチャネル設定など）を編集してください。
   ```bash
   vi .env.production
   ```

**起動:**
```bash
docker-compose up -d
```

**停止:**
```bash
docker-compose down
```

**ログ確認:**
```bash
docker-compose logs -f
```

### スクリプトを使用する場合（直接実行）
**起動:**
```bash
./start_prod.sh
```

**停止:**
```bash
./stop.sh
```

## 3. バックアップ手順
データベースファイルは `instance/` ディレクトリに保存されています。

**手動バックアップ:**
```bash
./scripts/backup_db.sh
```
バックアップファイルは `backups/` ディレクトリに保存されます。

**リストア:**
1. システムを停止します。
2. `instance/hirakata_bot.sqlite` をバックアップファイルで上書きします。
3. システムを起動します。

## 4. トラブルシューティング

### Q. 管理画面にアクセスできない
- ポート8080が使用されていないか確認してください。
- `docker-compose logs` でエラーログを確認してください。

### Q. LINE Botが応答しない
- ngrokが起動しているか、Webhook URLが正しいか確認してください。
- `logs/linebot.log` を確認してください。

### Q. 分析グラフの文字化け
- 日本語フォント（Noto Sans CJK）が正しく読み込まれているか確認してください。
- Docker環境ではイメージにフォントが含まれています。
