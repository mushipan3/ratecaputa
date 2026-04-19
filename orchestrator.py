#!/usr/bin/env python3
"""
ラテカピュータ エージェントオーケストレーター

フロー:
  1. ローカルモデル（Ollama）でコード生成
  2. CadQueryで実行・動作確認
  3. Claude Codeでレビュー・修正
  4. エラーがあればループ（最大MAX_ITERATIONS回）
  5. sudo等の人間操作が必要なら通知して待機
"""

import os
import sys
import json
import time
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# ===== 設定 =====
PROJECT_ROOT = Path(__file__).parent
CAD_DIR = PROJECT_ROOT / "cad"
DESIGN_STATE = PROJECT_ROOT / "design_state.md"

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.environ.get("OLLAMA_MODEL", "gemma3:4b")
PYTHON_BIN      = os.environ.get("MCP_PYTHON", str(Path.home() / "mcp-env/bin/python3"))

MAX_ITERATIONS  = int(os.environ.get("MAX_ITERATIONS", "5"))
LOG_FILE        = PROJECT_ROOT / "orchestrator.log"


# ===== ログ =====
def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ===== 人間の介入が必要か判定 =====
HUMAN_TRIGGERS = [
    "sudo", "password", "permission denied",
    "実測値", "手書きスケッチ", "確認してください",
    "判断できません", "情報が不足", "cannot", "human",
]

def needs_human(text: str) -> tuple[bool, str]:
    text_lower = text.lower()
    for trigger in HUMAN_TRIGGERS:
        if trigger in text_lower:
            return True, trigger
    return False, ""


# ===== ユーザー通知 =====
def notify_user(message: str):
    log(f"★ ユーザー呼び出し: {message}", "HUMAN")
    # Windowsデスクトップ通知（WSL経由）
    try:
        subprocess.run(
            ["powershell.exe", "-c",
             f'[System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms");'
             f'[System.Windows.Forms.MessageBox]::Show("{message}", "ラテカピュータ エージェント")'],
            timeout=5, capture_output=True
        )
    except Exception:
        pass
    # ビープ音
    try:
        subprocess.run(["powershell.exe", "-c", "[console]::beep(1000,800)"],
                       timeout=5, capture_output=True)
    except Exception:
        pass


# ===== Ollama でコード生成 =====
def ollama_generate(prompt: str, image_path: str = None) -> str:
    import urllib.request
    import urllib.error

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_ctx": 8192},
    }
    if image_path and Path(image_path).exists():
        import base64
        with open(image_path, "rb") as f:
            payload["images"] = [base64.b64encode(f.read()).decode()]

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("response", "")
    except urllib.error.URLError as e:
        return f"Ollamaに接続できません: {e}\nOllamaが起動しているか確認: ollama serve"


# ===== CadQueryスクリプト実行 =====
def run_cadquery(script_path: Path, timeout: int = 120) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [PYTHON_BIN, str(script_path)],
            capture_output=True, text=True,
            timeout=timeout, cwd=str(CAD_DIR),
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]\n{result.stderr}"
        success = result.returncode == 0
        return success, output
    except subprocess.TimeoutExpired:
        return False, f"タイムアウト（{timeout}秒）"
    except Exception as e:
        return False, f"実行エラー: {e}"


# ===== Claude Code でレビュー・修正 =====
def claude_review_and_fix(script_path: Path, error_output: str = "") -> tuple[bool, str]:
    script_content = script_path.read_text(encoding="utf-8")
    state_content = DESIGN_STATE.read_text(encoding="utf-8") if DESIGN_STATE.exists() else ""

    prompt = f"""以下のCadQueryスクリプトをレビューして、問題があれば修正してください。

## design_state.md（プロジェクト状態）
{state_content[:2000]}

## スクリプト: {script_path.name}
```python
{script_content}
```
"""
    if error_output:
        prompt += f"\n## 実行エラー\n```\n{error_output}\n```\n"

    prompt += "\n修正が必要な場合は修正済みのコード全体を出力してください。問題なければ「OK」とだけ答えてください。"

    try:
        result = subprocess.run(
            ["claude", "--print", prompt],
            capture_output=True, text=True, timeout=120,
        )
        output = result.stdout.strip()

        # 「OK」なら修正不要
        if output.strip().upper() in ("OK", "OK.", "問題ありません", "問題なし"):
            return True, output

        # コードブロックを抽出して上書き
        import re
        match = re.search(r"```python\n(.*?)```", output, re.DOTALL)
        if match:
            new_code = match.group(1)
            script_path.write_text(new_code, encoding="utf-8")
            log(f"Claude がスクリプトを修正しました: {script_path.name}")
            return False, output  # 修正したので再実行が必要

        return True, output  # コードブロックなし＝修正不要と判断
    except FileNotFoundError:
        return True, "claude コマンドが見つかりません（スキップ）"
    except subprocess.TimeoutExpired:
        return True, "Claude レビュータイムアウト（スキップ）"


# ===== メインループ =====
def orchestrate(task: str, script_name: str, image_path: str = None):
    log(f"=== オーケストレーター開始 ===")
    log(f"タスク: {task}")
    log(f"スクリプト: {script_name}")
    log(f"ローカルモデル: {OLLAMA_MODEL}")

    script_path = CAD_DIR / script_name
    if not script_path.suffix:
        script_path = script_path.with_suffix(".py")

    # --- Step 1: Ollamaでコード生成（新規の場合のみ）---
    if not script_path.exists():
        log("Ollamaでコード生成中...")
        state_content = DESIGN_STATE.read_text(encoding="utf-8") if DESIGN_STATE.exists() else ""
        prompt = f"""あなたはCadQuery（Python 3Dモデリングライブラリ）の専門家です。
以下のタスクを実現するCadQueryスクリプトを生成してください。

## プロジェクト状態
{state_content[:1500]}

## タスク
{task}

## 要件
- import cadquery as cq を使うこと
- STEPファイルを cq.exporters.export(result, "出力ファイル名.step") で保存すること
- 出力先は /home/mushipan3/esp_projects/ratecaputa/cad/ とすること
- コードのみ出力し、説明は不要

```python
"""
        code = ollama_generate(prompt, image_path)

        # コードブロック抽出
        import re
        match = re.search(r"```python\n(.*?)```", code, re.DOTALL)
        if match:
            code = match.group(1)
        elif "```" in code:
            code = re.sub(r"```\w*\n?", "", code).strip()

        script_path.write_text(code, encoding="utf-8")
        log(f"スクリプト生成完了: {script_path}")
    else:
        log(f"既存スクリプトを使用: {script_path}")

    # --- Step 2〜4: 実行→レビュー→修正ループ ---
    for i in range(1, MAX_ITERATIONS + 1):
        log(f"--- イテレーション {i}/{MAX_ITERATIONS} ---")

        # CadQuery実行
        log("CadQuery実行中...")
        success, output = run_cadquery(script_path)
        log(f"実行結果: {'成功' if success else '失敗'}")
        if output:
            log(f"出力:\n{output[:500]}")

        # 人間介入チェック
        human_needed, trigger = needs_human(output)
        if human_needed:
            msg = f"人間の操作が必要です（トリガー: {trigger}）\nスクリプト: {script_path}"
            notify_user(msg)
            log(msg, "HUMAN")
            input(">>> 操作完了後にEnterを押してください...")
            continue

        if success:
            log("実行成功。Claudeでレビュー中...")
            ok, review = claude_review_and_fix(script_path)
            if ok:
                log("=== 完了 ===")
                log(f"成果物: {script_path.with_suffix('.step')}")
                return True
            else:
                log("Claudeが修正しました。再実行します...")
                continue
        else:
            log("実行失敗。Claudeで修正中...")
            ok, review = claude_review_and_fix(script_path, output)
            if not ok:
                log("Claudeが修正しました。再実行します...")
            else:
                log("Claude修正なし。次のイテレーションへ...")

    log(f"最大イテレーション数({MAX_ITERATIONS})に達しました。", "WARN")
    notify_user(f"エージェントが{MAX_ITERATIONS}回試みましたが完了できませんでした。\n確認: {script_path}")
    return False


# ===== CLI =====
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ラテカピュータ エージェントオーケストレーター")
    parser.add_argument("task", nargs="?", default="",
                        help="実行するタスクの説明（例: 'U字パーツを設計して'）")
    parser.add_argument("--script", "-s", default="",
                        help="対象スクリプト名（例: u_bracket.py）。省略時はtaskから自動命名")
    parser.add_argument("--image", "-i", default="",
                        help="参照画像パス（断面スケッチ等）")
    parser.add_argument("--model", "-m", default="",
                        help=f"Ollamaモデル名（デフォルト: {OLLAMA_MODEL}）")
    parser.add_argument("--max-iter", type=int, default=MAX_ITERATIONS,
                        help=f"最大イテレーション数（デフォルト: {MAX_ITERATIONS}）")

    args = parser.parse_args()

    if args.model:
        OLLAMA_MODEL = args.model
    MAX_ITERATIONS = args.max_iter

    if not args.task:
        print("使い方:")
        print("  python3 orchestrator.py 'U字パーツを設計して' --script u_bracket")
        print("  python3 orchestrator.py 'ジョイントアダプタv3' --script joint_adapter_v3 --image cad/section.png")
        print("  OLLAMA_MODEL=qwen2.5-coder:7b python3 orchestrator.py 'タスク' --script out")
        sys.exit(0)

    script_name = args.script or args.task[:20].replace(" ", "_").replace("'", "")
    orchestrate(args.task, script_name, args.image or None)
