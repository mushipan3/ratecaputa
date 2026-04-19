#!/usr/bin/env python3
"""
ラテカピュータ 汎用エージェントオーケストレーター

対応タスク種別:
  - 3d    : CadQuery による3D CAD設計
  - pcb   : KiCad による基板設計
  - code  : 一般コーディング（ESP32ファームウェア等）
  - auto  : design_state.md から自動判断（デフォルト）

フロー:
  1. design_state.md を読み込み、次のタスクを提案
  2. ユーザー確認後に作業開始
  3. Ollama（ローカルLLM）でコード/設計を生成
  4. タスク種別に応じて実行・検証
  5. Claude Code（オンライン）でレビュー → フィードバックをOllamaへ返す
  6. 完了まで 3〜5 を繰り返す（最大MAX_ITERATIONS回）
  7. sudo等の人間操作が必要な時だけユーザーを呼び出す
  8. オフライン/トークン上限時はOllamaのみで継続
"""

import os
import sys
import re
import json
import time
import socket
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# ===== 設定 =====
PROJECT_ROOT    = Path(__file__).parent
CAD_DIR         = PROJECT_ROOT / "cad"
PCB_DIR         = PROJECT_ROOT / "pcb"
DESIGN_STATE    = PROJECT_ROOT / "design_state.md"
LOG_FILE        = PROJECT_ROOT / "orchestrator.log"

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.environ.get("OLLAMA_MODEL", "gemma3:4b")
PYTHON_BIN      = os.environ.get("MCP_PYTHON", str(Path.home() / "mcp-env/bin/python3"))
MAX_ITERATIONS  = int(os.environ.get("MAX_ITERATIONS", "5"))

HUMAN_TRIGGERS = [
    "sudo", "password", "permission denied",
    "実測値", "手書きスケッチ", "人間が確認",
    "判断できません", "情報が不足", "cannot determine",
]


# ===== ユーティリティ =====

def now() -> str:
    return datetime.now().strftime("%H:%M:%S")

def log(msg: str, level: str = "INFO"):
    line = f"[{now()}] [{level}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def section(title: str):
    bar = "─" * 50
    print(f"\n{bar}")
    print(f"  {title}")
    print(f"{bar}")

def is_online() -> bool:
    try:
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except Exception:
        return False

def needs_human(text: str) -> tuple[bool, str]:
    tl = text.lower()
    for t in HUMAN_TRIGGERS:
        if t in tl:
            return True, t
    return False, ""

def notify_user(message: str):
    log(f"★ ユーザー呼び出し: {message}", "HUMAN")
    try:
        subprocess.run(
            ["powershell.exe", "-c",
             f'[System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms");'
             f'[System.Windows.Forms.MessageBox]::Show("{message}","ラテカピュータ エージェント")'],
            timeout=5, capture_output=True)
    except Exception:
        pass
    try:
        subprocess.run(["powershell.exe", "-c", "[console]::beep(1000,800)"],
                       timeout=3, capture_output=True)
    except Exception:
        pass

def extract_code(text: str, lang: str = "python") -> str:
    m = re.search(rf"```{lang}\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r"```\w*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()

def read_design_state() -> str:
    if DESIGN_STATE.exists():
        return DESIGN_STATE.read_text(encoding="utf-8")
    return "（design_state.md が見つかりません）"

def update_design_state(current: str, next_tasks: str):
    if not DESIGN_STATE.exists():
        return
    content = DESIGN_STATE.read_text(encoding="utf-8")
    today = datetime.now().strftime("%Y-%m-%d")
    content = re.sub(r"> 更新日: .*", f"> 更新日: {today}", content)
    new_section = f"### 進行中\n{current}\n\n### 次にやること\n{next_tasks}\n"
    content = re.sub(
        r"### 進行中.*?(?=---|$)", new_section + "\n",
        content, flags=re.DOTALL)
    DESIGN_STATE.write_text(content, encoding="utf-8")


# ===== Ollama =====

def ollama_chat(messages: list[dict], image_path: str = None) -> str:
    import urllib.request, urllib.error
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.3, "num_ctx": 16384},
    }
    if image_path and Path(image_path).exists():
        import base64
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        payload["messages"][-1]["images"] = [b64]

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            result = json.loads(r.read().decode("utf-8"))
            return result["message"]["content"]
    except urllib.error.URLError as e:
        return f"[Ollama接続エラー: {e}]"


# ===== Claude Code =====

def claude_review(context: str, code: str, error: str = "") -> tuple[bool, str]:
    prompt = f"""以下の作業内容とコードをレビューしてください。

## コンテキスト
{context}

## コード / 成果物
```
{code}
```
"""
    if error:
        prompt += f"\n## エラー出力\n```\n{error}\n```"
    prompt += "\n\n問題があれば修正済みコード全体を出力してください。問題なければ「OK」とだけ答えてください。"

    try:
        result = subprocess.run(
            ["claude", "--print", prompt],
            capture_output=True, text=True, timeout=120,
        )
        output = result.stdout.strip()
        is_ok = output.strip().upper() in ("OK", "OK.", "問題ありません", "問題なし", "LGTM")
        return is_ok, output
    except FileNotFoundError:
        return True, "[claudeコマンド未検出 - スキップ]"
    except subprocess.TimeoutExpired:
        return True, "[Claudeタイムアウト - スキップ]"


# ===== タスク実行（種別別） =====

class TaskRunner:
    def __init__(self, task_type: str, work_dir: Path, output_name: str):
        self.task_type = task_type
        self.work_dir = work_dir
        self.output_name = output_name
        self.output_file = self._output_file()

    def _output_file(self) -> Path:
        if self.task_type == "3d":
            return self.work_dir / f"{self.output_name}.py"
        elif self.task_type == "pcb":
            return self.work_dir / f"{self.output_name}.py"
        else:
            return self.work_dir / f"{self.output_name}.py"

    def write_code(self, code: str):
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.output_file.write_text(code, encoding="utf-8")
        log(f"書き込み: {self.output_file}")

    def read_code(self) -> str:
        if self.output_file.exists():
            return self.output_file.read_text(encoding="utf-8")
        return ""

    def execute(self) -> tuple[bool, str]:
        if self.task_type in ("3d", "pcb", "code"):
            return self._run_python()
        return True, "（実行なし）"

    def _run_python(self) -> tuple[bool, str]:
        try:
            r = subprocess.run(
                [PYTHON_BIN, str(self.output_file)],
                capture_output=True, text=True, timeout=120,
                cwd=str(self.work_dir),
            )
            out = r.stdout + ("\n[STDERR]\n" + r.stderr if r.stderr else "")
            return r.returncode == 0, out
        except subprocess.TimeoutExpired:
            return False, "タイムアウト（120秒）"
        except Exception as e:
            return False, str(e)

    def system_prompt(self) -> str:
        state = read_design_state()
        if self.task_type == "3d":
            return f"""あなたはCadQuery（Python 3D CADライブラリ）の専門家です。
プロジェクトの設計状態を踏まえて、指示されたパーツをCadQueryで実装してください。

## プロジェクト状態
{state[:2000]}

## 出力規則
- `import cadquery as cq` を使う
- 最後に `cq.exporters.export(result, "{self.work_dir}/{self.output_name}.step")` でSTEP保存
- Pythonコードのみ出力（説明不要）"""
        elif self.task_type == "pcb":
            return f"""あなたはKiCad PCB設計の専門家です。
kicad-cli または pcbnew Python APIを使って指示された基板を実装してください。

## プロジェクト状態
{state[:2000]}

- Pythonコードのみ出力（説明不要）"""
        else:
            return f"""あなたは組み込みシステム開発の専門家です（ESP32, C, Python）。
以下のプロジェクト状態を踏まえてコードを実装してください。

## プロジェクト状態
{state[:2000]}

- コードのみ出力（説明不要）"""


# ===== タスク種別の自動判断 =====

def detect_task_type(task_desc: str) -> str:
    desc = task_desc.lower()
    if any(w in desc for w in ["3d", "stl", "step", "cadquery", "パーツ", "筐体", "アダプタ", "パネル"]):
        return "3d"
    if any(w in desc for w in ["pcb", "基板", "回路", "kicad", "ネットリスト", "フットプリント"]):
        return "pcb"
    return "code"

TYPE_LABELS = {"3d": "3D CAD設計", "pcb": "PCB設計", "code": "コーディング"}
TYPE_DIRS   = {"3d": CAD_DIR, "pcb": PCB_DIR, "code": PROJECT_ROOT}


# ===== インタラクティブモード（引数なし） =====

def interactive_mode(image_path: str = None):
    section("ラテカピュータ エージェントオーケストレーター")
    state = read_design_state()

    # Ollamaにプロジェクト状態を読ませて次のタスクを提案
    print("\n[Ollama] プロジェクト状態を分析中...")
    suggestion = ollama_chat([
        {"role": "system", "content": "あなたはプロジェクトマネージャーです。簡潔に日本語で答えてください。"},
        {"role": "user", "content": f"""以下のプロジェクト状態を読んで、次に取り組むべきタスクを1〜3個、箇条書きで提案してください。

{state[:3000]}

形式:
1. （タスク名）: （一行説明）
2. ...
"""}
    ])

    section("次のタスク候補")
    print(suggestion)
    print()

    task = input(">>> 実行するタスクを入力してください（または候補番号）: ").strip()
    if not task:
        print("キャンセルしました。")
        return

    # 番号が入力されたら候補から抽出
    if task.isdigit():
        lines = [l for l in suggestion.split("\n") if re.match(rf"^{task}\.", l)]
        if lines:
            task = re.sub(r"^\d+\.\s*", "", lines[0]).strip()

    task_type = detect_task_type(task)
    print(f"\nタスク種別: {TYPE_LABELS.get(task_type, task_type)}")

    name_suggestion = ollama_chat([
        {"role": "user", "content": f"次のタスクに対応するPythonファイル名（拡張子なし、英数字とアンダースコアのみ）を1語で答えてください: {task}"}
    ]).strip().split()[0]
    name_suggestion = re.sub(r"[^\w]", "_", name_suggestion)[:30] or "output"

    output_name = input(f">>> 出力ファイル名 [{name_suggestion}]: ").strip() or name_suggestion

    run_orchestrate(task, task_type, output_name, image_path)


# ===== メインオーケストレーション =====

def run_orchestrate(task: str, task_type: str, output_name: str, image_path: str = None):
    work_dir = TYPE_DIRS.get(task_type, PROJECT_ROOT)
    runner = TaskRunner(task_type, work_dir, output_name)

    section(f"作業開始: {task}")
    log(f"種別: {TYPE_LABELS.get(task_type)}  モデル: {OLLAMA_MODEL}  最大: {MAX_ITERATIONS}回")

    online = is_online()
    log(f"ネットワーク: {'オンライン' if online else 'オフライン（Ollamaのみで継続）'}")

    # 会話履歴（OllamaとClaudeのフィードバックを蓄積）
    messages = [
        {"role": "system", "content": runner.system_prompt()},
        {"role": "user", "content": task},
    ]

    for i in range(1, MAX_ITERATIONS + 1):
        section(f"イテレーション {i} / {MAX_ITERATIONS}")

        # --- Ollamaでコード生成 ---
        log(f"[Ollama:{OLLAMA_MODEL}] 生成中...")
        response = ollama_chat(messages, image_path if i == 1 else None)
        code = extract_code(response)
        print(f"\n--- 生成コード ({len(code)}文字) ---\n{code[:400]}{'...' if len(code)>400 else ''}\n")

        runner.write_code(code)
        messages.append({"role": "assistant", "content": response})

        # --- 実行・検証 ---
        log("実行中...")
        success, output = runner.execute()
        status = "✓ 成功" if success else "✗ 失敗"
        log(f"実行結果: {status}")
        if output:
            print(f"--- 実行出力 ---\n{output[:600]}\n")

        # 人間介入チェック
        human_needed, trigger = needs_human(output)
        if human_needed:
            msg = f"人間の操作が必要です（{trigger}）\nファイル: {runner.output_file}"
            notify_user(msg)
            input("\n>>> 操作完了後にEnterを押してください...")
            messages.append({"role": "user", "content": f"ユーザーが操作を完了しました。継続してください。"})
            continue

        # --- Claude レビュー（オンライン時のみ） ---
        claude_feedback = ""
        if online:
            log("[Claude] レビュー中...")
            context = f"タスク: {task}\n種別: {TYPE_LABELS.get(task_type)}"
            is_ok, review = claude_review(context, code, "" if success else output)
            print(f"--- Claudeレビュー ---\n{review[:400]}\n")

            if is_ok and success:
                section("✓ 完了")
                log(f"成果物: {runner.output_file}")
                update_design_state(
                    f"{task} → 完了（{runner.output_file.name}）",
                    "次のタスクを orchestrator.py で確認"
                )
                return True

            # Claudeのフィードバックを次のOllamaへの入力に追加
            claude_feedback = review
            new_code = extract_code(review)
            if new_code and new_code != code:
                runner.write_code(new_code)
                log("Claudeが修正を提案 → 適用済み")
                messages.append({
                    "role": "user",
                    "content": f"レビュー結果:\n{review}\n\n修正を反映してさらに改善してください。"
                })
            else:
                messages.append({
                    "role": "user",
                    "content": f"実行結果:\n{output}\n\nエラーを修正してください。"
                })
        else:
            # オフライン：成功なら終了、失敗ならOllamaにフィードバック
            if success:
                section("✓ 完了（オフライン）")
                log(f"成果物: {runner.output_file}")
                return True
            messages.append({
                "role": "user",
                "content": f"実行エラー:\n{output}\n\n修正してください。"
            })

    # 上限到達
    log(f"最大イテレーション({MAX_ITERATIONS})到達", "WARN")
    notify_user(f"{MAX_ITERATIONS}回試みましたが未完了です。\n{runner.output_file} を確認してください。")
    return False


# ===== CLI =====

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ラテカピュータ 汎用エージェントオーケストレーター",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使い方:
  python3 orchestrator.py                          # インタラクティブモード（推奨）
  python3 orchestrator.py 'U字パーツを設計して'    # タスク直接指定
  python3 orchestrator.py 'U字パーツ' -t 3d -s u_bracket -i cad/section.png
  python3 orchestrator.py 'BLE通信を実装して' -t code -s ble_module

環境変数:
  OLLAMA_MODEL=qwen2.5-coder:7b  モデル切り替え
  MAX_ITERATIONS=10              試行回数変更
        """
    )
    parser.add_argument("task", nargs="?", default="",
                        help="タスクの説明（省略でインタラクティブモード）")
    parser.add_argument("-t", "--type", choices=["3d", "pcb", "code", "auto"],
                        default="auto", help="タスク種別（デフォルト: auto）")
    parser.add_argument("-s", "--script", default="",
                        help="出力ファイル名（拡張子なし）")
    parser.add_argument("-i", "--image", default="",
                        help="参照画像パス（断面スケッチ等）")
    parser.add_argument("-m", "--model", default="",
                        help=f"Ollamaモデル名（デフォルト: {OLLAMA_MODEL}）")
    parser.add_argument("--max-iter", type=int, default=MAX_ITERATIONS,
                        help=f"最大イテレーション数（デフォルト: {MAX_ITERATIONS}）")
    args = parser.parse_args()

    if args.model:
        OLLAMA_MODEL = args.model
    MAX_ITERATIONS = args.max_iter
    image = args.image or None

    if not args.task:
        # 引数なし → インタラクティブモード
        interactive_mode(image)
    else:
        task_type = args.type if args.type != "auto" else detect_task_type(args.task)
        output_name = args.script or re.sub(r"[^\w]", "_", args.task[:20])
        run_orchestrate(args.task, task_type, output_name, image)
