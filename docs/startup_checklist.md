# システム起動前チェックリスト

## 必須サービス

システムを起動する前に、以下のサービスが起動していることを確認してください。

### 1. Ollama（必須）

**確認方法:**
```bash
curl http://localhost:11434/api/tags
```

**起動されていない場合:**

別のターミナルで以下を実行:
```bash
ollama serve
```

**モデルの確認:**
```bash
ollama list
```

llama3.2が表示されない場合:
```bash
ollama pull llama3.2
```

---

### 2. ngrok（LINE連携時のみ必須）

ローカルでのテストのみであれば不要です。LINE公式アカウントと連携する場合のみ必要です。

**起動方法:**

別のターミナルで以下を実行:
```bash
ngrok http 5000
```

**表示されるURL（例）:**
```
Forwarding    https://xxxx-xxxx.ngrok-free.app -> http://localhost:5000
```

このURLをLINE Developers ConsoleのWebhook URLに設定:
```
https://xxxx-xxxx.ngrok-free.app/callback
```

---

## 起動手順

### ステップ1: 事前確認

```bash
# Ollamaの起動確認
curl http://localhost:11434/api/tags

# ngrokの起動確認（LINE連携時のみ）
pgrep -f ngrok
```

### ステップ2: システム起動

```bash
cd /root/workspace/hirakata_bot1
./start_all.sh
```

**start_all.shが自動で行うこと:**
1. Ollamaの起動確認
2. ngrokの起動確認（情報表示のみ）
3. 既存プロセスの停止
4. LINE Botの起動
5. 管理画面の起動
6. 起動確認

### ステップ3: 動作確認

```bash
# LINE Bot
curl http://localhost:5000/health

# 管理画面
curl -I http://localhost:8080/admin/login
```

---

## 典型的な起動シーケンス

### ローカルテスト（ngrok不要）

```bash
# ターミナル1: Ollama
ollama serve

# ターミナル2: システム起動
cd /root/workspace/hirakata_bot1
./start_all.sh
```

### LINE連携テスト（ngrok必要）

```bash
# ターミナル1: Ollama
ollama serve

# ターミナル2: ngrok
ngrok http 5000

# ターミナル3: システム起動
cd /root/workspace/hirakata_bot1
./start_all.sh
```

---

## トラブルシューティング

### Ollamaが起動しない

```bash
# Ollamaのインストール確認
which ollama

# Ollamaのバージョン確認
ollama --version

# Ollamaの再起動
pkill ollama
ollama serve
```

### ngrokが認証エラー

```bash
# authtokenの設定
ngrok config add-authtoken YOUR_TOKEN

# ngrokの再起動
pkill ngrok
ngrok http 5000
```

### start_all.shでOllama接続エラー

別ターミナルで`ollama serve`を実行してから、再度`./start_all.sh`を実行してください。

---

## サービス依存関係

```
┌─────────────┐
│   Ollama    │ ← 必須（LLM応答に使用）
│ (port 11434)│
└─────────────┘
       ↑
       │
┌─────────────┐     ┌─────────────┐
│  LINE Bot   │ ←─→ │   ngrok     │ ← オプション（LINE連携時のみ）
│ (port 5000) │     │ (port 5000) │
└─────────────┘     └─────────────┘

┌─────────────┐
│  管理画面    │ ← 独立（Ollama不要）
│ (port 8080) │
└─────────────┘
```

---

## まとめ

**必須起動順序:**
1. Ollama（別ターミナル）
2. ngrok（LINE連携時のみ、別ターミナル）
3. システム本体（./start_all.sh）

**確認ポイント:**
- Ollama: http://localhost:11434/api/tags にアクセス可能
- ngrok: Forwarding URLが表示されている（LINE連携時）
- LINE Bot: http://localhost:5000/health が正常応答
- 管理画面: http://localhost:8080/admin/login が表示される
