# ラテカピュータ 開発環境ガイド

作成日: 2026-04-17  
最終更新: 2026-04-17

---

## 1. 全体構成

```
┌──────────────────────────────────────────────────────────────┐
│                     作業者（あなた）                          │
│  VS Code または WSLターミナル                                 │
└───────────┬──────────────┬──────────────┬───────────────────┘
            │              │              │
            ▼              ▼              ▼
        claude          codex     python3 orchestrator.py
    （Claudeだけ）  （Codexだけ）  （Ollama + Claude 協調）
            │              │              │
            └──────────────┴──────────────┘
                           │
                  MCP（共通ツール層）
              ※ どのエージェントも同じMCPを使う
                           │
          ┌────────────────┴────────────────┐
          ▼                                 ▼
  latecaputa-cadquery MCP          latecaputa-kicad MCP
  （3D CAD / CadQuery）            （PCB設計 / KiCad）
          │                                 │
          ▼                                 ▼
    CadQuery 2.7.0                    KiCad 7.0.11
```

**ポイント:** MCPサーバーはWSL内で常時稼働。どのエージェントを使っても同じツールが使える。

---

## 2. 起動方法

### 基本：プロジェクトフォルダへ移動してコマンドを打つだけ

```bash
cd ~/esp_projects/ratecaputa
```

これまで通り、VS CodeのターミナルやWSLターミナルでプロジェクトフォルダに移動してコマンドを入力します。MCPサーバーとOllamaはWSL起動時に自動的に動いています。

---

## 3. コマンドの使い分け

### 3-1. Claude だけで作業する（従来通り）

```bash
claude
```

- オンライン必須
- トークンを消費するが品質は最高
- `.mcp.json` が自動読み込みされ、CadQuery・KiCadツールが使える

### 3-2. Codex CLI だけで作業する

```bash
codex
```

- オンライン必須
- Claudeのトークンが尽きた時の引き継ぎ先
- 同じ `.mcp.json` を参照するため、作業を継続できる

### 3-3. ローカルLLM だけで作業する（完全オフライン）

```bash
ollama run gemma3:4b
```

- オフライン動作
- インターネット不要
- 品質はClaudeより低いが、ネット不通時・トークン節約時に使用

### 3-4. ローカルLLM + オンラインレビュー（推奨・トークン節約）

```bash
python3 orchestrator.py
```

- **通常作業の推奨コマンド**
- `design_state.md` を読み込んで次のタスクを提案
- Ollamaがコードを生成 → Claudeがレビュー・修正 → ループ
- オフライン時は自動的にOllamaのみで継続
- 人間の操作が必要な時だけ通知して待機

---

## 4. orchestrator.py の使い方

### 引数なし（インタラクティブモード・推奨）

```bash
python3 orchestrator.py
```

1. `design_state.md` を読んでプロジェクト状態を把握
2. 次にやるべきタスクを1〜3個提案
3. タスクを選ぶ（番号入力 or 自由入力）
4. Ollama → 実行 → Claude → ループが自動で動く

### タスクを直接指定する

```bash
# 自動でタスク種別を判断
python3 orchestrator.py 'U字パーツを設計して'

# タスク種別・ファイル名・参照画像を明示
python3 orchestrator.py 'ジョイントアダプタv3を設計して' \
  -t 3d \
  -s joint_adapter_v3 \
  -i cad/section_front.png

# コーディングタスク
python3 orchestrator.py 'BLE通信モジュールを実装して' \
  -t code \
  -s ble_module
```

### オプション一覧

| オプション | 説明 | 例 |
|-----------|------|-----|
| `-t` | タスク種別（3d / pcb / code / auto） | `-t 3d` |
| `-s` | 出力ファイル名（拡張子なし） | `-s u_bracket` |
| `-i` | 参照画像（断面スケッチ等） | `-i cad/section.png` |
| `-m` | Ollamaモデル指定 | `-m gemma3:4b` |
| `--max-iter` | 最大試行回数（デフォルト5） | `--max-iter 10` |

### 環境変数でデフォルトを変える

```bash
# モデルを切り替えて実行
OLLAMA_MODEL=qwen2.5-coder:7b python3 orchestrator.py

# 試行回数を増やして実行
MAX_ITERATIONS=10 python3 orchestrator.py 'タスク内容'
```

---

## 5. orchestrator.py の動作フロー

```
python3 orchestrator.py
        │
        ├─ design_state.md を読み込む
        ├─ Ollama が次のタスクを提案
        ├─ あなたがタスクを選択・承認
        │
        ▼
  ┌─────────────────────────────────────┐
  │  イテレーションループ（最大5回）      │
  │                                     │
  │  1. Ollama がコードを生成            │
  │  2. コードを実行・検証               │
  │  3. Claude がレビュー・修正          │
  │  4. フィードバックをOllamaへ返す     │
  │  5. 完了なら終了、問題あれば繰り返し  │
  └─────────────────────────────────────┘
        │
        ├─ 完了 → design_state.md を更新
        └─ 人間操作が必要 → 通知して待機
```

**オフライン時:** ステップ3（Claudeレビュー）をスキップし、Ollamaのみで継続。

---

## 6. エージェント引き継ぎ手順

Claudeのトークンが尽きた、またはオフラインになった場合：

```bash
# Claudeのトークン上限 → Codexへ切り替え
cd ~/esp_projects/ratecaputa
codex
# → 「design_state.md を読んで作業を続けてください」と伝える

# Codex → Claudeへ戻す
claude

# どちらもトークン上限 → ローカルのみで継続
python3 orchestrator.py   # 自動でオフラインモードになる
# または
ollama run gemma3:4b
```

---

## 7. MCPサーバー ツール一覧

すべてのエージェント（Claude / Codex / orchestrator）から共通して利用できる。

### 3D CAD（latecaputa-cadquery）

| ツール | 機能 |
|--------|------|
| `cadquery_run` | CadQueryスクリプトを実行してSTEP出力 |
| `cadquery_run_inline` | インラインコードを直接実行 |
| `list_cad_files` | CADディレクトリのファイル一覧 |
| `design_state_read` | 引き継ぎファイルを読み込む |
| `design_state_update` | 引き継ぎファイルの作業状態を更新 |

### PCB設計（latecaputa-kicad）

| ツール | 機能 |
|--------|------|
| `kicad_version` | KiCad CLIバージョン確認 |
| `list_pcb_projects` | PCBプロジェクト一覧 |
| `pcb_drc` | デザインルールチェック |
| `pcb_export_gerber` | ガーバーファイル出力 |
| `schematic_erc` | 電気ルールチェック |
| `schematic_export_netlist` | ネットリスト出力 |

---

## 8. インストール済みコンポーネント一覧

| コンポーネント | バージョン | 場所 |
|--------------|-----------|------|
| Python仮想環境 | 3.12.3 | `~/mcp-env/` |
| CadQuery | 2.7.0 | `~/mcp-env/` |
| MCP SDK | 1.27.0 | `~/mcp-env/` |
| KiCad CLI | 7.0.11 | `/usr/bin/kicad-cli` |
| Ollama | 0.21.0 | `/usr/local/bin/ollama` |
| gemma3:4b | 3.3GB | Ollamaモデル（Vision対応） |

---

## 9. 重要ファイル

| ファイル | 場所 | 役割 |
|---------|------|------|
| `design_state.md` | プロジェクトルート | **最重要。常に最新に保つ。エージェント引き継ぎの核心** |
| `.mcp.json` | プロジェクトルート | MCPサーバー設定（全エージェント共用） |
| `.claudeignore` | プロジェクルート | AIコンテキスト除外（トークン削減） |
| `orchestrator.py` | プロジェクトルート | 汎用マルチエージェントオーケストレーター |
| `check_env.sh` | `~/mcp-servers/` | 環境確認スクリプト |

---

## 10. 環境確認コマンド

```bash
# 環境全体の確認
~/mcp-servers/check_env.sh

# MCPサーバー接続確認
claude mcp list

# Ollamaの状態確認
ollama list

# Ollamaサービス状態
systemctl is-active ollama
```

---

## 11. ディレクトリ構成

```
~/ （ホームディレクトリ）
├── mcp-env/                      # Python仮想環境（CadQuery + MCP SDK）
└── mcp-servers/
    ├── cadquery-mcp/server.py    # CadQuery MCPサーバー（5 tools）
    ├── kicad-mcp/server.py       # KiCad MCPサーバー（6 tools）
    └── check_env.sh              # 環境チェックスクリプト

~/esp_projects/ratecaputa/        # プロジェクトリポジトリ
├── .claudeignore                 # AIコンテキスト除外設定
├── .mcp.json                     # MCPサーバー設定（全エージェント共用）
├── design_state.md               # 引き継ぎファイル（★常に最新に保つ）
├── orchestrator.py               # 汎用マルチエージェントオーケストレーター
├── docs/
│   └── dev_environment.md        # このファイル
├── cad/                          # 3D CADスクリプト・出力
├── pcb/                          # PCB設計ファイル（KiCad）
├── waveshare-c6/                 # ESP32-C6ファームウェア
├── xiao-c6/                      # XIAO C6関連
└── i2c_scan/                     # I2Cスキャンツール
```
