![Python](https://img.shields.io/badge/Python-3.10+-blue)
![macOS](https://img.shields.io/badge/macOS-Compatible-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

# HotPepper-Scraper

このプロジェクトは、HotPepperの店舗情報を効率的に収集するための、クラスベースで設計されたWebスクレイピングツールです。

従来のCUIベースの安定したロジックにモダンなGUIを統合し、macOSのアプリケーション形式（.app）での配布・実行にも対応しました。

## 特徴 (Features)
- **再帰的な探索**: 複雑なエリア階層を動的に解析し、末端エリアまで自動巡回します。
- **メモリ効率の最適化**: Pythonのジェネレータ（`yield`/`yield from`）を活用し、メモリ消費を抑えた効率的なデータ処理を実現。
- **堅牢な設計**: クラスによる一元管理と適切なエラーハンドリングにより、プロセス中断時も成果を確実に保護。
- **モダンなGUI**: `customtkinter` を採用し、直感的な操作画面を実現。
- **マルチスレッド処理**: GUIのフリーズを防ぎつつ、リアルタイムにログを表示。
- **macOS (.app) 完全対応**: パッケージ内部と外部のパスを分離する独自ロジックを実装。配布時にアプリの隣に設定ファイルを置くだけで即座に実行可能です。

## スクリーンショット
<img width="854" height="578" alt="スクリーンショット 2026-03-10 20 02 59" src="https://github.com/user-attachments/assets/ea917281-dd8f-4ba9-839d-418e8ee2a445" />

## 必要環境 (Requirements)
- Python 3.10以上推奨
- macOS環境（`.app`ビルド済み）または Python環境

**ライブラリ等**
- `pandas`, `beautifulsoup4`
- 実行には `scraper.py` および `parser.py` （別途定義）が必要です。

## 使い方 (Usage)
**一般ユーザーの方**
1. Releases から最新の `HotPepperScraper.zip` をダウンロードし、解凍します。
2. `HotPepperScraper.app` と同じ階層に `config.json` を配置します。

   ```text
   # ディレクトリ構成
   dist/
   ├── HotPepperScraper.app  # アプリ本体
   ├── config.json           # 設定ファイル（config.json.exampleを自分用に設定したもの）
   ├── scraper.log           # 実行時に自動生成
   └── shop_list.csv         # 実行時に自動生成
   ```
3. アプリを起動し、設定を入力して「実行開始」をクリックしてください。

**開発者の方（ビルド方法）**
```Bash
# 依存ライブラリのインストール
pip install pandas beautifulsoup4 customtkinter pyinstaller

# macOSでのビルド
pyinstaller --noconfirm --onedir --windowed --name "HotPepperScraper" app.py
```
※ビルド後、配布する際は dist/HotPepperScraper.app と config.json をセットにして配布してください。

**CUIの場合**
1. `config.json` を適切に設定してください。
2. 依存ライブラリのインストール
   ```Bash
   pip install pandas beautifulsoup4 customtkinter pyinstaller
   ```
3. `main.py` を実行します。
   ```bash
   python main.py
   ```
4. 取得データは `shop_list.csv` に追記保存されます。

## 📊 出力データの形式 (Output Format)
収集した店舗情報は、`shop_list.csv` として出力されます。各カラムの構成は以下の通りです。

| カラム名 | 説明 |
| :--- | :--- |
| **name** | 店舗名 |
| **detail_url** | 店舗の詳細ページURL |
| **area** | エリア名（小エリア単位） |
| **genre** | ジャンル |
| **source_url** | 情報取得元のエリアURL |
| **tel** | 電話番号 |

### 出力例 (CSV)
```csv
name,detail_url,area,genre,source_url,tel
サンプル店舗A,/strJ123456789/,新宿エリア,居酒屋,https://example.com/...,03-0000-0000
サンプル店舗B,/strJ987654321/,新宿エリア,カフェ,https://example.com/...,090-0000-0000
```

## ⚙️ 設定ファイル仕様 (Configuration)
`config.json` にて以下のパラメータを指定可能です。
- GUI使用時: `target_area_key` / `target_genre_key` はアプリ画面から入力。`headers` のみ `config.json` を参照。
- CUI使用時: 全項目が `config.json` 必須。

| キー | 説明 | 例 |
| :--- | :--- | :--- |
| `target_area_key` | 探索対象となるエリア名 | `"Dougenzaka"` |
| `target_genre_key` | 検索するジャンル名 | `"Izakaya"` |
| `headers` | スクレイピング時のHTTPヘッダー | `{"User-Agent": "..."}` |

> **注意**: `headers` の `User-Agent` は、ご自身のブラウザの情報を設定することを推奨します。

## 設計思想 (Design Philosophy)
このツールは、単なるスクレイピングツールを超え、拡張可能な設計を目指しています。特に、再帰的な探索ロジックとジェネレータを組み合わせることで、**「失敗してもそこまでの成果を確実に残せる」** 設計思想を重視しました。

## 今後の改善予定 (Roadmap)
- [ ] **リトライ機能の実装**: 指数関数的な待機時間（Exponential Backoff）を設けた再試行処理を追加予定。

- [ ] **DB保存機能**: CSV保存に加え、SQLiteなどデータベースへの直接保存オプションを追加予定。

- [ ] **非同期処理の導入**: `asyncio` を活用した、より高速な並列スクレイピングへの対応。

---
本ツールは学習・研究目的で作成されたものです。利用にあたっては各サイトの利用規約および robots.txt を遵守してください。
