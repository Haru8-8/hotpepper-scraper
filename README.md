![Python](https://img.shields.io/badge/Python-3.10+-blue)
![macOS](https://img.shields.io/badge/macOS-Compatible-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

# 飲食店リスト自動収集ツール

HotPepperから店舗情報を自動収集し、リスト化できるスクレイピングツールです。

👉 **飲食店リスト作成・営業リスト収集・市場調査を効率化できます。**

---

## スクリーンショット

<img width="854" height="578" alt="スクリーンショット 2026-03-10 20 02 59" src="https://github.com/user-attachments/assets/ea917281-dd8f-4ba9-839d-418e8ee2a445" />

---

## 解決できる課題

- 飲食店リスト作成に時間がかかる
- 手動での情報収集が非効率
- 営業リストを作るのが大変

---

## 想定ユースケース

- 営業リスト作成
- 出店エリア調査
- 競合店舗分析
- マーケティングリサーチ

---

## 主な機能

- **店舗情報の自動収集**: HotPepperから条件に応じて店舗情報を取得
- **再帰的なエリア探索**: 複雑なエリア階層を動的に解析し、末端エリアまで自動巡回
- **GUIによる操作**: 直感的な操作画面で簡単に実行可能
- **マルチスレッド処理**: GUIのフリーズを防ぎリアルタイムにログを表示
- **CSV出力**: 収集データをそのまま営業リスト・分析に活用できる形式で保存
- **macOS .app対応**: ダブルクリックで即起動できる形式で配布可能

---

## 出力データの形式

収集した店舗情報は `shop_list.csv` として出力されます。

| カラム名 | 説明 |
|----------|------|
| name | 店舗名 |
| detail_url | 店舗の詳細ページURL |
| area | エリア名（小エリア単位） |
| genre | ジャンル |
| source_url | 情報取得元のエリアURL |
| tel | 電話番号 |

### 出力例

```csv
name,detail_url,area,genre,source_url,tel
サンプル店舗A,/strJ123456789/,新宿エリア,居酒屋,https://example.com/...,03-0000-0000
サンプル店舗B,/strJ987654321/,新宿エリア,カフェ,https://example.com/...,090-0000-0000
```

---

## 技術スタック

| 分類 | 技術 |
|------|------|
| 言語 | Python 3.10以上 |
| スクレイピング | BeautifulSoup |
| GUI | CustomTkinter |
| データ処理 | Pandas |
| アプリ化 | PyInstaller |

---

## 技術的なこだわり

- **再帰的探索による網羅的データ取得**: 複雑なエリア構造を動的に解析し、末端エリアまで自動巡回
- **メモリ効率の最適化**: ジェネレータ（`yield`/`yield from`）を活用し、大量データでも安定処理
- **安定したGUI設計**: マルチスレッドにより処理中でもUIがフリーズしない設計
- **堅牢なエラーハンドリング**: 中断時も途中までのデータを確実に保持
- **macOSアプリ対応**: `.app`化時のパス問題を独自ロジックで解決し、配布後もそのまま実行可能

---

## 設計思想

このツールは単なるスクレイピングツールを超え、拡張可能な設計を目指しています。特に、再帰的な探索ロジックとジェネレータを組み合わせることで、**「失敗してもそこまでの成果を確実に残せる」** 設計思想を重視しました。

---

## 使い方

### 一般ユーザーの方（アプリ使用）

1. [Releases](https://github.com/Haru8-8/hotpepper-scraper/releases) から最新の `HotPepperScraper.zip` をダウンロードし、解凍します。
2. `HotPepperScraper.app` と同じ階層に `config.json` を配置します。

```
dist/
├── HotPepperScraper.app  # アプリ本体
├── config.json           # 設定ファイル（config.json.exampleを自分用に設定したもの）
├── scraper.log           # 実行時に自動生成
└── shop_list.csv         # 実行時に自動生成
```

3. アプリを起動し、設定を入力して「実行開始」をクリックしてください。

### 開発者の方（ビルド方法）

```bash
# 依存ライブラリのインストール
pip install pandas beautifulsoup4 customtkinter pyinstaller

# macOSでのビルド
pyinstaller --noconfirm --onedir --windowed --name "HotPepperScraper" app.py
```

※ビルド後、配布する際は `dist/HotPepperScraper.app` と `config.json` をセットにして配布してください。

### CUIの場合

```bash
pip install pandas beautifulsoup4 customtkinter pyinstaller
python main.py
```

取得データは `shop_list.csv` に追記保存されます。

---

## 設定ファイル仕様

`config.json` にて以下のパラメータを指定可能です。

- GUI使用時: `target_area_key` / `target_genre_key` はアプリ画面から入力。`headers` のみ `config.json` を参照。
- CUI使用時: 全項目が `config.json` 必須。

| キー | 説明 | 例 |
|------|------|-----|
| `target_area_key` | 探索対象となるエリア名 | `"Dougenzaka"` |
| `target_genre_key` | 検索するジャンル名 | `"Izakaya"` |
| `headers` | スクレイピング時のHTTPヘッダー | `{"User-Agent": "..."}` |

> **注意**: `headers` の `User-Agent` は、ご自身のブラウザの情報を設定することを推奨します。

---

## 今後の改善予定

- [ ] **リトライ機能の実装**: 指数関数的な待機時間（Exponential Backoff）を設けた再試行処理
- [ ] **DB保存機能**: CSV保存に加え、SQLiteなどデータベースへの直接保存オプション
- [ ] **非同期処理の導入**: `asyncio` を活用した、より高速な並列スクレイピング

---

## 備考

👉 業務内容に応じてカスタマイズ（通知機能追加・Web化など）も可能です。

本ツールは学習・研究目的で作成されたものです。利用にあたっては各サイトの利用規約および robots.txt を遵守してください。

---

## ライセンス

MIT License
