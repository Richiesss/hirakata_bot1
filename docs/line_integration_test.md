# LINE実機テスト ガイド

## 前提条件

✅ **システム稼働中**: LINE Bot + 管理画面  
✅ **ngrok起動中**: `https://longevous-cubbishly-helena.ngrok-free.dev`  
✅ **Webフォーム動作確認済み**: 全機能正常動作

---

## ステップ1: LINE Developers Console設定

### 1-1. Webhook URLの設定

1. [LINE Developers Console](https://developers.line.biz/console/) にアクセス
2. 対象のプロバイダーとチャネルを選択
3. **Messaging API設定** タブを開く
4. **Webhook URL** を設定:
   ```
   https://longevous-cubbishly-helena.ngrok-free.dev/callback
   ```
5. **検証** ボタンをクリック → 「成功」と表示されることを確認
6. **Webhookの利用** を有効化（ONにする）

### 1-2. 応答設定

1. **応答メッセージ** を無効化（OFFにする）
2. **Webhookを使用** を有効化（ONにする）

---

## ステップ2: リッチメニュー設定

### 2-1. リッチメニュー作成

ターミナルで以下を実行:

```bash
cd /root/workspace/hirakata_bot1
source venv/bin/activate
PYTHONPATH=/root/workspace/hirakata_bot1:$PYTHONPATH python features/rich_menu.py https://longevous-cubbishly-helena.ngrok-free.dev
```

**実行結果例**:
```
✓ Rich menu created: richmenu-xxxxx
リッチメニュー画像のパスを入力してください（Enter=スキップ）: 
（Enterを押してスキップ）
✓ Set as default menu

リッチメニューID: richmenu-xxxxx
設定が完了しました！
```

### 2-2. リッチメニュー画像（オプション）

リッチメニューに画像を設定する場合:

1. 2500×1686pxの画像を作成
2. レイアウト:
   ```
   ┌─────────┬─────────┐
   │ 対話で  │ アンケート│
   │ 意見    │         │
   ├─────────┼─────────┤
   │ポイント  │ ヘルプ   │
   │確認     │         │
   └─────────┴─────────┘
   ```
3. rich_menu.py実行時に画像パスを指定

---

## ステップ3: 実機テスト

### 3-1. LINE Botを友だち追加

1. LINE Developers Consoleの**Messaging API設定**タブ
2. QRコードをスキャンして友だち追加

### 3-2. テスト項目

#### ✅ テスト1: 友だち追加メッセージ

**期待結果**:
```
ようこそ、枚方市民ニーズ抽出システムへ！

このBotでは、市民の皆様のご意見を簡単に送信できます。

【使い方】
💬 対話で意見: 「意見を送りたい」と入力
📝 アンケート: リッチメニューの「アンケート」をタップ
💎 ポイント確認: /point コマンド
❓ ヘルプ: /help コマンド

ご意見をお待ちしています！
```

---

#### ✅ テスト2: リッチメニュー「アンケート」ボタン

**操作手順**:
1. 画面下部のリッチメニューを開く
2. 「アンケート」ボタンをタップ

**期待結果**:
- Webブラウザが開く
- URL: `https://longevous-cubbishly-helena.ngrok-free.dev/web/survey?user_id=<YOUR_LINE_USER_ID>`
- アンケートフォームが表示される

**フォーム内容確認**:
- ✅ タイトル: 「枚方市民ニーズアンケート」
- ✅ カテゴリ選択（8カテゴリ）
- ✅ テキストエリア
- ✅ 文字数カウント
- ✅ 送信ボタン

---

#### ✅ テスト3: アンケート送信

**操作手順**:
1. カテゴリを選択（例: 交通）
2. 意見を入力（例: 実機テスト：駅前の駐輪場が少ない）
3. 「送信する」ボタンをタップ
4. 確認ダイアログで「OK」

**期待結果**:
- 送信完了ページが表示
- メッセージ: 「ご意見ありがとうございます」
- ポイント表示: 「💎 5 ポイント」
- 送信内容の確認表示

---

#### ✅ テスト4: データベース確認

ターミナルで確認:

```bash
cd /root/workspace/hirakata_bot1
source venv/bin/activate
PYTHONPATH=/root/workspace/hirakata_bot1:$PYTHONPATH python << 'EOF'
from database.db_manager import get_db, Opinion

with get_db() as db:
    # 最新の意見を表示
    opinions = db.query(Opinion).filter(
        Opinion.source_type == 'free_form'
    ).order_by(Opinion.created_at.desc()).limit(5).all()
    
    print("=== 最新の自由記述アンケート（5件）===")
    for op in opinions:
        print(f"ID: {op.id}, カテゴリ: {op.category}, 内容: {op.content[:30]}...")
EOF
```

---

#### ✅ テスト5: 対話機能（既存機能）

**操作手順**:
1. 「意見を送りたい」と入力

**期待結果**:
- 対話型意見収集が開始
- Ollamaが質問を生成（例: 「どのようなご意見でしょうか？」）

---

#### ✅ テスト6: コマンド機能

**コマンドテスト**:

| コマンド | 期待結果 |
|---------|---------|
| `/point` | 総ポイント表示 |
| `/help` | ヘルプメッセージ |
| `/reset` | 対話履歴リセット |

---

## トラブルシューティング

### 問題1: Webhook検証が失敗

**確認事項**:
- ngrokが起動しているか
- LINE Botアプリ（app.py）が起動しているか
- Webhook URL が正しいか（`/callback`）

**解決方法**:
```bash
# システム再起動
cd /root/workspace/hirakata_bot1
./stop.sh
./start_all.sh

# ngrok URL確認
curl http://localhost:4040/api/tunnels | python -m json.tool
```

---

### 問題2: リッチメニューが表示されない

**確認事項**:
- リッチメニューIDが正しく登録されているか
- デフォルトメニューに設定されているか

**解決方法**:
```bash
# リッチメニューを再作成
cd /root/workspace/hirakata_bot1
source venv/bin/activate
PYTHONPATH=/root/workspace/hirakata_bot1:$PYTHONPATH python features/rich_menu.py https://longevous-cubbishly-helena.ngrok-free.dev
```

---

### 問題3: アンケートフォームが開かない

**確認事項**:
- ngrok URLが有効か
- Webフォーム（/web/survey）が動作しているか

**テスト**:
```bash
curl -I https://longevous-cubbishly-helena.ngrok-free.dev/web/survey?user_id=test
```

---

### 問題4: Ollamaエラー（対話機能）

**現象**: 対話型意見収集で500エラー

**原因**: Ollamaのメモリ不足（llama3.2モデル）

**対応**:
- 軽量モデル（gemma:2b）を使用
- または、このエラーは既知の問題として無視

---

## チェックリスト

実機テスト前の確認:

- [ ] LINE Developers ConsoleでWebhook URL設定
- [ ] Webhook検証成功
- [ ] 応答設定（応答メッセージOFF、WebhookON）
- [ ] リッチメニュー作成完了
- [ ] LINE Botを友だち追加
- [ ] システム稼働中（LINE Bot、管理画面、ngrok）

---

## 次のステップ

実機テスト完了後:

1. **本番運用準備**
   - ngrokの有料プランまたは固定ドメイン取得
   - サーバーデプロイ（Heroku、AWS、GCPなど）

2. **次フェーズ実装**
   - フェーズ7: 選択式アンケート
   - フェーズ9: AI分析強化

3. **運用開始**
   - 市民への案内
   - データ収集開始
   - 管理画面で集計・分析

---

## まとめ

このガイドに従って実機テストを実施してください。

**重要**: ngrok URLは無料版の場合、再起動すると変わります。本番運用では固定URLが必要です。

問題が発生した場合は、トラブルシューティングセクションを参照してください。
