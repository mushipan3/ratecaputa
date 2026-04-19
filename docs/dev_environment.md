# ラテカピュータ 開発環境概要

作成日: 2026-04-17  
対象プロジェクト: ラテカピュータ（ラテカセ筐体組み込みコンピュータ）

---

## 1. 全体構成

```
┌─────────────────────────────────────────────────────┐
│  AIエージェント（Claude Code / OpenAI Codex CLI）    │
│  ※トークン上限に達したら相互に引き継ぎ可能          │
└──────────────────────┬──────────────────────────────┘
                       │ MCP (Model Context Protocol)
         ┌─────────────┴──────────────┐
         ▼                            ▼
┌─────────────────┐        ┌─────────────────┐
│ latecaputa-     │        │ latecaputa-     │
│ cadquery MCP    │        │ kicad MCP       │
│ (5 tools)       │        │ (6 tools)       │
└────────┬────────┘        └────────┬────────┘
         │                          │
         ▼                          ▼
┌─────────────────┐        ┌─────────────────┐
│ CadQuery 2.7.0  │        │ KiCad CLI       │
│ (3D CAD エンジン)│        │ (PCB設計エンジン) │
└─────────────────┘        └─────────────────┘
         │                          │
         └──────────┬───────────────┘
                    ▼
         ~/esp_projects/ratecaputa/
         （プロジェクトリポジトリ）
```

---

## 2. MCPサーバー一覧

### 2-1. latecaputa-cadquery（3D CAD）

**場所:** `~/mcp-servers/cadquery-mcp/server.py`  
**実行環境:** `~/mcp-env/bin/python3`（専用仮想環境）  
**状態:** ✓ 稼働中

| ツール名 | 機能 |
|----------|------|
| `cadquery_run` | スクリプトファイルを実行してSTEP出力 |
| `cadquery_run_inline` | インラインCadQueryコードを直接実行 |
| `list_cad_files` | CADディレクトリのファイル一覧 |
| `design_state_read` | 引き継ぎファイル（design_state.md）を読み込む |
| `design_state_update` | 引き継ぎファイルの作業状態を更新する |

### 2-2. latecaputa-kicad（PCB設計）

**場所:** `~/mcp-servers/kicad-mcp/server.py`  
**実行環境:** `~/mcp-env/bin/python3`（同上）  
**状態:** ✓ 構築済み（KiCadインストール後に完全稼働）

| ツール名 | 機能 |
|----------|------|
| `kicad_version` | KiCad CLIのバージョン確認 |
| `list_pcb_projects` | PCBプロジェクト一覧 |
| `pcb_drc` | DRC（デザインルールチェック）実行 |
| `pcb_export_gerber` | ガーバーファイル出力 |
| `schematic_erc` | ERC（電気ルールチェック）実行 |
| `schematic_export_netlist` | ネットリスト出力 |

---

## 3. 設定ファイル

### 3-1. .mcp.json（プロジェクトルート）

`~/esp_projects/ratecaputa/.mcp.json`

Claude Code・Codex CLI 双方が参照するMCPサーバー設定ファイル。  
プロジェクトルートに置くことで `cd` するだけで自動読み込みされる。

```json
{
  "mcpServers": {
    "latecaputa-cadquery": { ... },
    "latecaputa-kicad": { ... }
  }
}
```

### 3-2. .claudeignore

`~/esp_projects/ratecaputa/.claudeignore`

AIのコンテキストから除外するファイルを定義。トークン消費を削減する。

| 除外対象 | 理由 |
|----------|------|
| `**/build/` | ESP-IDFビルド中間ファイル（大量・不要） |
| `**/*.step`, `**/*.stl` | 3D出力バイナリ（テキストとして無意味） |
| `**/*.jpg`, `**/*.jpeg`, `**/*.png` | 画像ファイル |
| `**/managed_components/` | ESP-IDF自動管理ライブラリ |
| `**/__pycache__/` | Pythonキャッシュ |
| `**/node_modules/` | Node.jsパッケージ（将来のMCP用） |

### 3-3. design_state.md（引き継ぎファイル）

`~/esp_projects/ratecaputa/design_state.md`

**最重要ファイル。** AIエージェントを切り替える際の引き継ぎ書。  
以下を記録・更新し続ける：

- プロジェクト概要・ハードウェア構成
- 各パーツの設計進捗状態
- 現在の作業内容と次にやること
- 設計上の重要な制約・寸法
- ファイル構成・ツールチェーン情報

**運用ルール:** 作業終了時に `design_state_update` ツールで更新すること。

---

## 4. Python仮想環境

**場所:** `~/mcp-env/`  
**Pythonバージョン:** 3.12.3

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| cadquery | 2.7.0 | 3D CADエンジン |
| mcp | 1.27.0 | MCPサーバーSDK |
| vtk | 9.3.1 | 3Dレンダリング（CadQuery依存） |

---

## 5. AIエージェント引き継ぎ手順

トークン上限に達した場合、以下の手順で別エージェントへ引き継ぐ：

### Claude Code → Codex CLI の場合

```bash
# 1. 現在のエージェントが design_state.md を更新
#    （design_state_update ツールを使用）

# 2. Codex CLIを起動（.mcp.jsonが自動読み込みされる）
cd ~/esp_projects/ratecaputa
codex

# 3. Codex CLIに指示
# 「design_state.md を読み込んで、作業を続けてください」
```

### Codex CLI → Claude Code の場合

```bash
cd ~/esp_projects/ratecaputa
claude  # .mcp.jsonが自動読み込みされる
```

---

## 6. 環境チェックコマンド

```bash
# 環境全体の確認
~/mcp-servers/check_env.sh

# MCPサーバー接続確認（Claude Code内）
claude mcp list

# CadQueryスクリプト手動実行
~/mcp-env/bin/python3 cad/joint_adapter_v2.py
```

---

## 7. 残作業（環境構築）

| 項目 | コマンド | 状態 |
|------|---------|------|
| KiCadインストール | `sudo apt-get install -y kicad` | **要実行** |
| PCBディレクトリ作成 | `mkdir -p ~/esp_projects/ratecaputa/pcb` | KiCad導入時 |

---

## 8. ディレクトリ構成

```
~/ (ホームディレクトリ)
├── mcp-env/                    # Python仮想環境（CadQuery + MCP SDK）
└── mcp-servers/
    ├── cadquery-mcp/
    │   └── server.py           # CadQuery MCPサーバー
    ├── kicad-mcp/
    │   └── server.py           # KiCad MCPサーバー
    └── check_env.sh            # 環境チェックスクリプト

~/esp_projects/ratecaputa/      # プロジェクトリポジトリ
├── .claudeignore               # AIコンテキスト除外設定
├── .mcp.json                   # MCPサーバー設定（Claude Code / Codex CLI共用）
├── design_state.md             # 引き継ぎファイル（★常に最新に保つ）
├── docs/
│   └── dev_environment.md      # このファイル
├── cad/                        # 3D CADスクリプト・出力
│   ├── joint_adapter_v1.py
│   ├── joint_adapter_v2.py
│   └── ラテカピュータのコンピュータ部筐構成について.txt
├── waveshare-c6/               # ESP32-C6ファームウェア
├── xiao-c6/                    # XIAO C6関連
└── i2c_scan/                   # I2Cスキャンツール
```
