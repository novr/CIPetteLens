# AI Assistant Instructions for CIPetteLens

この文書は、AIアシスタント（GitHub Copilot, Claude, Geminiなど）が`CIPetteLens`プロジェクトの開発を支援する際のガイドです。

## About this repository (このリポジトリについて)

`CIPetteLens`は、CI/CDプロセスの主要メトリクスを可視化するための、**最小限で実用的な（MVP）**Webダッシュボードです。

このプロジェクトの最大の特徴は、データ収集と分析をオープンソースのCLIツールである**`CIAnalyzer`**に完全に依存している点です。私たちの役割は、`CIAnalyzer`の分析結果（JSON）をラップし、整形し、シンプルなWebインターフェースで表示する**「レンズ（Lens）」**に集中します。

### アーキテクチャの特徴

- **Clean Architecture**: レイヤー分離による保守性の高い設計
- **Dependency Injection**: サービス層での依存関係管理
- **Repository Pattern**: データアクセス層の抽象化
- **Domain Models**: ビジネスロジックの明確な分離

## Tech stack (技術スタック)

| 領域 | 技術 | バージョン |
| :--- | :--- | :--- |
| **言語** | Python | 3.11+ |
| **Webフレームワーク** | Flask | 3.0.3+ |
| **データベース** | SQLite | 3.x |
| **パッケージ管理** | uv | latest |
| **開発ツール** | ruff, black, mypy, pytest | latest |
| **UI** | プレーンなHTML/CSS | フレームワークなし |
| **コアエンジン** | CIAnalyzer | Docker |
| **コンテナ** | Docker | latest |

## How to run (実行方法)

### セットアップ

```bash
# 1. 依存関係のインストール
uv sync

# 2. 環境変数の設定
cp env.example .env
# .envファイルを編集してGITHUB_TOKENとTARGET_REPOSITORIESを設定

# 3. データベースの初期化（自動で作成されます）
# 特に手動操作は不要
```

### 開発・実行

```bash
# データ収集の実行
uv run cipettelens
# または
uv run collect

# Webアプリケーションの起動
uv run web

# 開発サーバーの起動（mise使用時）
mise run dev
```

### 利用可能なコマンド

```bash
# テスト実行
uv run pytest

# コード品質チェック
uv run ruff check
uv run ruff check --fix

# 型チェック
uv run mypy

# フォーマット
uv run black .
uv run isort .

# コミット前チェック（推奨）
mise run pre-commit

# 個別チェック
mise run lint        # リントチェック
mise run format      # フォーマット
mise run type-check  # 型チェック
mise run test        # テスト実行
```

## Directory structure (ディレクトリ構成)

```
CIPetteLens/
├── cipettelens/                    # メインパッケージ
│   ├── __init__.py
│   ├── main.py                     # アプリケーションエントリーポイント
│   ├── config.py                   # 設定管理
│   ├── database.py                 # レガシーデータベース操作（互換性用）
│   ├── logger.py                   # ログ設定
│   ├── security.py                 # セキュリティユーティリティ
│   ├── cli/                        # CLIコマンド
│   │   └── collect.py              # データ収集コマンド
│   ├── external/                   # 外部サービス連携
│   │   ├── ci_analyzer.py          # CIAnalyzerクライアント
│   │   └── mock_data.py            # モックデータ生成
│   ├── models/                     # ドメインモデル
│   │   ├── ci_metrics.py           # CIメトリクスモデル
│   │   └── repository.py           # リポジトリモデル
│   ├── repositories/               # データアクセス層
│   │   ├── base.py                 # リポジトリインターフェース
│   │   └── sqlite_metrics.py       # SQLite実装
│   ├── services/                   # ビジネスロジック層
│   │   └── metrics_service.py      # メトリクスサービス
│   ├── use_cases/                  # ユースケース層
│   │   └── collect_metrics.py      # メトリクス収集ユースケース
│   ├── web/                        # Webアプリケーション層
│   │   └── app.py                  # Flaskアプリケーション
│   └── exceptions/                 # カスタム例外
│       ├── base.py
│       ├── ci_analyzer.py
│       ├── database.py
│       └── validation.py
├── tests/                          # テストスイート
│   ├── test_cli.py
│   ├── test_models.py
│   ├── test_security.py
│   ├── test_sqlite_repository.py
│   └── test_lastrun_functionality.py
├── templates/                      # HTMLテンプレート
│   └── dashboard.html
├── static/                         # 静的ファイル
│   └── style.css
├── db/                             # データベースファイル
│   └── data.sqlite
├── .ci_analyzer/                   # CIAnalyzer設定・出力
│   └── last_run/
│       └── github.json
├── ci_analyzer.yaml                # CIAnalyzer設定ファイル
├── pyproject.toml                  # プロジェクト設定
├── .mise.toml                      # タスクランナー設定
└── README.md
```

## Development Guidelines (開発ガイドライン)

### コード品質

- **型ヒント**: すべての関数・メソッドに型ヒントを記述
- **docstring**: クラス・メソッドには適切なdocstringを記述
- **テスト**: 新機能には必ずテストを追加
- **リント**: `ruff check --fix`でコード品質を維持
- **コミット前チェック**: `mise run pre-commit`で包括的な品質チェックを実行

### アーキテクチャ原則

- **単一責任**: 各クラス・関数は単一の責任を持つ
- **依存性逆転**: 抽象に依存し、具象に依存しない
- **インターフェース分離**: 必要最小限のインターフェースを提供
- **開放閉鎖**: 拡張に開放、修正に閉鎖

### テスト戦略

- **単体テスト**: 各コンポーネントの個別テスト
- **統合テスト**: コンポーネント間の連携テスト
- **モック**: 外部依存（Docker、GitHub API）はモック化
- **カバレッジ**: 可能な限り高いテストカバレッジを維持

### Pull Request

- 1つのPull Requestは、1つの関心事に集中
- 変更内容と理由を明確に記述
- `WIP` (Work In Progress) の状態でのPRも歓迎
- レビュー前に`ruff check`と`pytest`を実行

### Git Workflow

- **コミット前**: 必ず`mise run pre-commit`を実行
- **pre-commitフック**: 自動的にコード品質チェックを実行
- **コミットメッセージ**: 変更内容を明確に記述
- **ブランチ**: 機能ごとにブランチを作成

## Key Features (主要機能)

### データ収集
- CIAnalyzerによる自動メトリクス収集
- GitHub Actions APIからのデータ取得
- 増分更新（last_runファイルによる）

### メトリクス表示
- Duration（実行時間）
- Success Rate（成功率）
- Throughput（スループット）
- MTTR（平均復旧時間）

### API エンドポイント
- `GET /api/metrics` - 全メトリクス取得
- `GET /api/metrics/<repository>` - リポジトリ別メトリクス
- `GET /api/metrics/<repository>/latest` - 最新メトリクス
- `GET /api/metrics/<repository>/<metric>/history` - メトリクス履歴
- `GET /api/repositories` - リポジトリ一覧
- `GET /api/health` - ヘルスチェック

## Current Status (現在の状況)

### 完了済み機能
- ✅ Clean Architecture実装
- ✅ SQLiteMetricsRepository完全実装
- ✅ レガシーコード削除
- ✅ last_runファイル保存機能
- ✅ 包括的なテストスイート（52テスト）
- ✅ コード品質ツール設定（ruff, black, mypy）
- ✅ Web API実装
- ✅ セキュリティ機能

### 今後の改善予定
- 🔄 認証・認可機能の追加
- 🔄 リアルタイム更新機能
- 🔄 より詳細なメトリクス可視化
- 🔄 アラート機能
- 🔄 設定UI

### 既知の制限事項
- CIAnalyzerのDocker実行に依存
- 現在はGitHub Actionsのみ対応
- 認証機能なし（本番環境では要追加）