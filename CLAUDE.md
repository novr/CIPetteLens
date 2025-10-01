# Copilot Instructions for CIPetteLens

この文書は、AIアシスタント（GitHub Copilot, Geminiなど）が`CIPetteLens`プロジェクトの開発を支援する際のガイドです。

## About this repository (このリポジトリについて)

`CIPetteLens`は、CI/CDプロセスの主要メトリクスを可視化するための、**最小限で実用的な（MVP）**Webダッシュボードです。

このプロジェクトの最大の特徴は、データ収集と分析をオープンソースのCLIツールである**`CIAnalyzer`**に完全に依存している点です。私たちの役割は、`CIAnalyzer`の分析結果（JSON）をラップし、整形し、シンプルなWebインターフェースで表示する**「レンズ（Lens）」**に集中します。

## Tech stack (技術スタック)

| 領域 | 技術 |
| :--- | :--- |
| **言語** | Python 3 |
| **Webフレームワーク**| Flask |
| **データベース** | SQLite |
| **開発ツール** | `uv` (pyproject.toml) |
| **UI** | プレーンなHTML/CSS (フレームワークなし) |
| **コアエンジン** | `CIAnalyzer` |

## How to run (実行方法)

```bash
# 1. 依存関係のインストール
uv sync

# 2. CIAnalyzerバイナリのダウンロード (初回のみ)
# (Makefileやスクリプトで自動化することを推奨)
# 例: curl -L "[https://github.com/Kesin11/CIAnalyzer/releases/download/v0.12.0/](https://github.com/Kesin11/CIAnalyzer/releases/download/v0.12.0/)..." | tar xz -C ./bin

# 3. 設定ファイルの作成
# env.exampleをコピーして、GitHubのトークンなどを設定
cp env.example .env
vi .env

# 4. データ収集の実行
uv run collect

# 5. Webアプリケーションの起動
uv run web
```

## Directory structure (ディレクトリ構成)

```
cipette_lens/
├── app.py              # Flaskのメインアプリケーション (View)
├── lens.py             # CIAnalyzerを実行し、結果をDBに保存するラッパー (Lens)
├── database.py         # SQLiteの初期化と基本的な操作
├── config.py           # 設定（分析対象リポジトリ、APIトークン等）
├── bin/
│   └── cianalyzer      # CIAnalyzerの実行バイナリを配置
├── db/
│   └── database.sqlite # SQLiteのデータベースファイル
├── templates/
│   └── dashboard.html  # メインダッシュボードのHTML
└── static/
    └── style.css       # ごく最小限のCSS
```

## About Pull Requests (Pull Requestについて)

- 1つのPull Requestは、1つの関心事に集中させてください。
- どのような変更を行ったのか、そして「なぜ」その変更が必要だったのかを明確に記述してください。
- `WIP` (Work In Progress) の状態でのPull Requestも歓迎します。