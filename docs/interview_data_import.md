# interview.xlsx データインポート

## 概要

`interview.xlsx` ファイルには枚方市の市民ニーズ分析用データ（約5,200件）が含まれています。
このデータをテストデータとしてデータベースに組み込むためのインポートスクリプトを提供しています。

## データ構造

### interview.xlsx の内容

- **総行数**: 約5,200行
- **列構成**:
  - 市民意見: 市民からの意見・要望のテキスト
  - アンケート出典: データ収集元のアンケート名
  - アンケート取得時期: データ取得時期
  - 回答者属性: 回答者の性別（男性/女性）
  - 年代: 回答者の年代（20代〜70代以上）

## インポートスクリプト

### 使い方

```bash
# 既存のテストデータをクリアして新規インポート
python3 scripts/import_interview_data.py --clear

# 既存データを残したまま追加インポート
python3 scripts/import_interview_data.py

# カスタムファイルパスを指定
python3 scripts/import_interview_data.py --file /path/to/file.xlsx
```

### インポート処理の内容

1. **データクリーニング**
   - ヘッダー行の除去
   - 空白行の除去
   - 性別・年代データの正規化

2. **ユーザー生成**
   - 性別と年代の組み合わせごとにテストユーザーを生成
   - 100意見ごとにユーザーを循環させて再利用
   - LINE IDハッシュは `test_user_{index}_{gender}_{age}` から生成

3. **意見データ挿入**
   - `source_type`: 'imported_test_data' として保存
   - `category`: キーワードベースで自動分類
   - `emotion_score`: デフォルト5
   - `priority_score`: デフォルト1.0

## インポート結果

### 統計情報

- **インポート済み意見数**: 3,762件
- **テストユーザー数**: 1,042人

### カテゴリ別分布

| カテゴリ | 件数 | 割合 |
|---------|------|------|
| その他 | 1,733 | 46.1% |
| 交通 | 672 | 17.9% |
| 子育て | 495 | 13.2% |
| 教育 | 315 | 8.4% |
| 環境 | 305 | 8.1% |
| 福祉 | 144 | 3.8% |
| 防災 | 59 | 1.6% |
| 医療 | 39 | 1.0% |

### 年代別ユーザー分布

| 年代 | ユーザー数 |
|------|-----------|
| 20-29 | 109 |
| 30-39 | 170 |
| 40-49 | 142 |
| 50-59 | 152 |
| 60+ | 226 |
| 不明 | 243 |

## カテゴリ分類ロジック

キーワードベースで以下のように自動分類されます:

- **交通**: 道、交通、バス、駅、電車、車、駐車、信号
- **福祉**: 福祉、介護、高齢、年金
- **教育**: 学校、教育、勉強、先生、塾
- **環境**: 環境、ゴミ、公園、緑、自然、川、山
- **子育て**: 子育て、保育、幼稚園、子ども、子供
- **医療**: 医療、病院、診療、健康、クリニック
- **防災**: 防災、災害、避難、地震、台風
- **その他**: 上記に該当しないもの

## データ確認

インポート後のデータ確認用SQLクエリ:

```sql
-- 総数確認
SELECT COUNT(*) FROM opinions WHERE source_type = 'imported_test_data';

-- カテゴリ別集計
SELECT category, COUNT(*) as count
FROM opinions
WHERE source_type = 'imported_test_data'
GROUP BY category
ORDER BY count DESC;

-- サンプルデータ表示
SELECT o.id, u.display_name, o.category, o.content
FROM opinions o
JOIN users u ON o.user_id = u.id
WHERE o.source_type = 'imported_test_data'
LIMIT 10;
```

## 注意事項

- `--clear` オプションを使用すると、既存の `source_type = 'imported_test_data'` のデータがすべて削除されます
- テストユーザーは `display_name` が「テストユーザー」で始まるユーザーとして識別されます
- インポートには約1〜2分程度かかります（データ量による）

## ファイル

- **データファイル**: [/home/hirakata_bot1/interview.xlsx](../interview.xlsx)
- **インポートスクリプト**: [scripts/import_interview_data.py](../scripts/import_interview_data.py)