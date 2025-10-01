# 設計ガイド: CIPetteLens 🏗️

この文書は、CI/CDダッシュボードのMVP「CIPetteLens」の設計ガイドです。

## 1. 設計原則

-   **ラバレッジ**: 強力な外部ツール`CIAnalyzer`をエンジンとして最大限に活用する。
-   **シンプル**: 最小限の技術スタック（Python/Flask, SQLite）で完結させる。
-   **集中**: 私たちの役割はデータ分析ではなく、**分析結果の整形と表示**に集中する。

---

## 2. システム構成

| 領域 | 技術 | 理由 |
| :--- | :--- | :--- |
| **言語** | Python 3 | `CIAnalyzer`を呼び出し、JSONを処理するのに最適。 |
| **Web** | Flask | 軽量で迅速なWeb UI構築が可能。 |
| **データベース** | SQLite | 設定不要のファイルベースDB。MVPに最適。 |
| **UI** | HTML/CSS | フレームワーク不要。シンプルなテーブル表示に徹する。 |
| **コアエンジン**| `CIAnalyzer` | Go製の高速な分析エンジン。データ取得と分析を担当。 |

**実行フロー**:
`Scheduler` ⟶ `Engine (CIAnalyzer)` ⟶ `Lens (Wrapper)` ⟶ `Database (SQLite)` ⟶ `View (Flask)`

---

## 3. データ構造

`CIAnalyzer`の分析結果を保存するための、シンプルなテーブル設計です。

```sql
-- リポジトリごとの集計済みメトリクスを保存するテーブル
CREATE TABLE metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  repository TEXT NOT NULL,
  collected_at DATETIME NOT NULL,
  -- CIAnalyzerのレポートから抽出した主要メトリクス
  throughput INTEGER,
  success_rate REAL,
  avg_duration_seconds REAL,
  mttr_seconds REAL
);
```
**設計方針**: `CIAnalyzer`が計算した集計済みの値をそのまま保存します。個別の`Run`データを保存する必要はなく、テーブル構造を極限までシンプルに保ちます。

---

## 4. データ収集と計算ロジック

-   **データ収集**:
    -   Pythonの`subprocess`モジュールを使い、`cianalyzer analyze --format json`コマンドを実行。
-   **計算ロジック**:
    -   **メトリクス計算は`CIAnalyzer`に完全に委任**します。
    -   `CIPetteLens`の役割は、`CIAnalyzer`が出力したJSONレポートから、`throughput`, `success_rate`, `avg_duration_seconds`, `mttr_seconds`といったキーの値を**抽出してDBに保存するだけ**です。
    -   これにより、`CIPetteLens`側で複雑なSQLや計算ロジックを持つ必要がなくなります。

---

## 5. 実装アプローチ

### ファイル構成
```
cipette_lens/
├── app.py              # Flask アプリケーション
├── lens.py             # CIAnalyzerを実行し、結果をDBに保存するラッパー
├── database.py         # SQLiteの初期化と基本的な操作
├── config.py           # 設定（分析対象リポジトリ、APIトークン等）
├── templates/
│   └── dashboard.html  # メインダッシュボード
└── static/
    └── style.css       # ごく最小限のCSS
```

### 段階的開発
1.  **Engine実行**: `lens.py`から`CIAnalyzer`を実行し、JSONレポートを取得できることを確認する。
2.  **データ保存**: 取得したJSONからメトリクスを抽出し、SQLiteの`metrics`テーブルに保存する。
3.  **データ表示**: `app.py`でSQLiteから最新のメトリクスを読み出し、`dashboard.html`にテーブルとして表示する。
4.  **定期実行**: `cron`などを使って、`lens.py`を定期的に実行し、データを自動更新する。

---

## 6. シンプルUI

-   **フレームワーク不要**: プレーンなHTML/CSSで実装。
-   **テーブル中心**: `metrics`テーブルの内容をそのままHTMLの`<table>`で表示。
-   **最小限のCSS**: 50行以内で、ステータスに応じた色分け（成功率など）と基本的な可読性を担保。

この構成により、**複雑なパフォーマンスチューニング（キャッシュなど）を考慮する必要がなく**、迅速に動作するプロトタイプを構築できます。