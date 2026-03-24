#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apache CGI で動作する簡易メンテナンス UI + 実行ハンドラ
- GET /poly9-bin/mente.py                : UI を返す
- GET /poly9-bin/mente.py?action=run&... : 指定タスクを実行し、ログを逐次表示
"""

import cgi
import cgitb
import html
import io
import os
import re
import sys
import time
import shlex
import subprocess
from datetime import datetime

#cgitb.enable()  # デバッグ時のみ。運用で外すならコメントアウト

# ======== ローカル環境に合わせて調整 ========
VENV_PY = "/home/poly/env/firebase/bin/python"
SCRIPTS_DIR = "/home/poly/job-postings/src/python"
FIREBASE_CLI = "/usr/local/bin/firebase"    # 例: which firebase で確認
SERVICE_ACCOUNT_JSON = "/home/poly/job-postings/src/poly9wanted-firebase-adminsdk.json"
APP_LOG_DIR = "/var/log/maint-web"          # 任意（www-data 書込権限）

# タイムアウト（秒）：長めに（pdfやdeployが長くなる想定）
EXEC_TIMEOUT = 60 * 30  # 30分

# ======== ユーティリティ ========


def ensure_dirs():
    if APP_LOG_DIR and not os.path.isdir(APP_LOG_DIR):
        try:
            os.makedirs(APP_LOG_DIR, exist_ok=True)
        except Exception:
            pass

def now_stamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def print_headers(content_type="text/html; charset=utf-8", extra=None):
    print(f"Content-Type: {content_type}")
    if extra:
        for k, v in extra.items():
            print(f"{k}: {v}")
    print()  # 空行

def escape(s: str) -> str:
    return html.escape(s, quote=True)

def valid_year(s: str) -> int:
    if not re.fullmatch(r"\d{4}", s or ""):
        raise ValueError("年度は4桁の数字で指定してください。例: 2027")
    return int(s)

# 「3-5」や単数「320」を許容、空白区切りで複数
RANGE_TOKEN = re.compile(r"^(?:\d+|\d+-\d+)$")

def parse_nums_text(nums_text: str) -> list[str]:
    """
    入力例: "320 333-336 111"
    仕様: 空白区切り／範囲は "3-5" のみ（全角や ~ は不可）
    """
    tokens = [t for t in (nums_text or "").split() if t]
    if not tokens:
        raise ValueError("番号(-n)を指定してください。例: 320 333-336 111")
    for t in tokens:
        if not RANGE_TOKEN.fullmatch(t):
            raise ValueError(f"番号の形式が不正です: '{t}'（例: 320 333-336）")
    return tokens

def build_command(task: str, params: dict) -> tuple[list[str], dict]:
    """
    実行コマンド配列と環境変数の追加を返す。
    shell=False で実行するため、1要素1引数に分割すること。
    """
    cwd = SCRIPTS_DIR
    env = os.environ.copy()

    if task == "showKyujinNuminLAN":
        cmd = [VENV_PY, os.path.join(cwd, "showKyujinNuminLAN.py")]

    elif task == "showKyujinNum":
        cmd = [VENV_PY, os.path.join(cwd, "showKyujinNum.py")]

    elif task == "upJobPostingsMajor":
        cmd = [VENV_PY, os.path.join(cwd, "up-jobPostingsMajor.py")]

    elif task == "pdfUpdate":
        year = valid_year(params.get("year"))
        nums_text = params.get("nums", "")
        tokens = parse_nums_text(nums_text)
        # -n は空白区切りで複数を渡す（例: ["-n", "320", "333-336", "111"]）
        cmd = [
            VENV_PY,
            os.path.join(cwd, "pdfUpdate.py"),
            "-y", str(year),
            "-n", *tokens
        ]

    elif task == "listLanPdfFiles":
        cmd = ["ls", "-lR", "/home/poly/job-postings/public/contents/pdf"]

    elif task == "firebaseDeploy":

        # サービスアカウントJSONで認証
        if not os.path.isfile(SERVICE_ACCOUNT_JSON):
            raise RuntimeError(f"Service Account JSON が見つかりません: {SERVICE_ACCOUNT_JSON}")
        env["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_JSON
        cmd = [FIREBASE_CLI, "deploy", "--only", "hosting"]

    else:
        raise ValueError("不明なタスクです。")

    return cmd, env

def stream_run(cmd: list[str], env: dict, cwd: str | None) -> int:
    """
    コマンドを起動し、標準出力/エラーを逐次出力してフラッシュ。
    返り値はプロセスのリターンコード。
    """
    # ログファイル（任意）
    ensure_dirs()
    log_fp = None
    try:
        if APP_LOG_DIR:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_cmd = "_".join(os.path.basename(x) for x in cmd[:2])  # 簡易名
            log_path = os.path.join(APP_LOG_DIR, f"{ts}_{safe_cmd}.log")
            log_fp = open(log_path, "a", encoding="utf-8", buffering=1)
            #print(f"[{now_stamp()}] [INFO] ログ: {log_path}")
            sys.stdout.flush()

        # 実行開始
        #print(f"[{now_stamp()}] [INFO] 実行コマンド: {shlex.join(cmd)}")
        sys.stdout.flush()
        p = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            text=True
        )

        start = time.time()
        for line in iter(p.stdout.readline, ''):
            # 逐次出力
            sys.stdout.write(line)
            sys.stdout.flush()
            if log_fp:
                log_fp.write(line)

            # タイムアウト監視（任意）
            if (time.time() - start) > EXEC_TIMEOUT:
                p.kill()
                print(f"\n[{now_stamp()}] [ERROR] タイムアウトによりプロセスを停止しました。")
                sys.stdout.flush()
                if log_fp:
                    log_fp.write("\n[ERROR] timeout\n")
                return 124  # timeout

        p.wait()
        code = p.returncode
        #print(f"\n[{now_stamp()}] [INFO] 終了コード: {code}")
        sys.stdout.flush()
        return code

    finally:
        if log_fp:
            log_fp.close()

def render_ui():
    print_headers("text/html; charset=utf-8")
    # シンプルな1ページUI。下部は <iframe> に実行結果をストリーミング表示。
    print(f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>九州職業能力開発大学校 求人情報提示メンテナンスツール</title>
<style>
body {{ font-family: system-ui, -apple-system, "Segoe UI", sans-serif; margin: 16px; }}
h1 {{ font-size: 1.2rem; }}
.container {{ max-width: 1200px; margin: 0 auto; }}
.topbar button {{ margin: 4px 8px 8px 0; padding: 8px 12px; }}
.formrow {{ margin: 6px 0; }}
.label {{ display:inline-block; width: 60px; }}
#outwrap {{ margin-top: 12px; border: 1px solid #ccc; border-radius: 6px; }}
#outtitle {{ padding: 8px; background: #f7f7f7; border-bottom: 1px solid #ddd; font-weight: bold; }}
#outpane {{ width: 100%; height: 420px; border: 0; display:block; }}
.note {{ color:#666; font-size:0.9em; }}
</style>
<script>
function runTask(task) {{
  const frame = document.getElementById('outpane');
  frame.src = '/poly9-bin/mente.py?action=run&task=' + encodeURIComponent(task) + '&ts=' + Date.now();
}}
function runPdf() {{
  const year = document.getElementById('year').value.trim();
  const nums = document.getElementById('nums').value.trim();
  const frame = document.getElementById('outpane');
  const qs = new URLSearchParams({{ action:'run', task:'pdfUpdate', year:year, nums:nums, ts:Date.now() }});
  frame.src = '/poly9-bin/mente.py?' + qs.toString();
}}
function runDeploy() {{
  if (!confirm('hosting へデプロイします。よろしいですか？')) return;
  runTask('firebaseDeploy');
}}
function runListPdf() {{
  runTask('listLanPdfFiles');
}}
</script>
</head>
<body>
<div class="container">
  <h1>求人票公開サービス(poly9wanted.web.app) メンテナンスツール</h1>
  <h2>学内の求人情報閲覧システムに登録済みの情報を外部で利用できるように転送します</h2>
  <div class="topbar">
    <button onclick="runTask('showKyujinNuminLAN')">学内LAN登録数(年度毎)を表示</button>
    <button onclick="runTask('showKyujinNum')">外部Web公開中(2026/2027)件数表示</button>
    <button onclick="runTask('upJobPostingsMajor')">検索情報を外部Webにupload</button>
  </div>
  <h2>学内の求人情報閲覧システムに登録済みのPDFファイルを外部で利用できるように転送します</h2>
  <div class="formrow">
    <span class="label">年度</span>
    <input id="year" type="text" value="2027" size="6" placeholder="2027">
    <span class="label" style="margin-left:16px;">番号(-n)</span>
    <input id="nums" type="text" size="40" placeholder="例: 320 333-336 111">
    <button onclick="runPdf()">PDF転送</button>
  </div>
  <div class="formrow note">番号の範囲指定は <code>3-5</code> のようにハイフン結合、空白区切りで複数指定可。</div>
  <div class="formrow">
    <button onclick="runListPdf()"> 学内LAN転送完了pdfファイル一覧 </button>
    <button style="background:#0067b8;color:#fff;" onclick="runDeploy()">PDFファイル登録公開(deploy)</button>
  </div>

  <div id="outwrap">
    <div id="outtitle">出力（リアルタイム）</div>
    <iframe id="outpane">about:blank</iframe>
  </div>
</div>
</body>
</html>
""")

def run_action():
    form = cgi.FieldStorage()
    task = form.getfirst("task", "")
    params = {
        "year": form.getfirst("year", ""),
        "nums": form.getfirst("nums", ""),
    }

    # レスポンスはプレーンテキストでストリーミング
    # ※ IE 非対応。現行ブラウザはOK
    print_headers("text/plain; charset=utf-8", extra={"X-Content-Type-Options": "nosniff"})
    #print(f"[{now_stamp()}] [INFO] タスク: {task}")
    sys.stdout.flush()

    try:
        cmd, env = build_command(task, params)
    except Exception as e:
        print(f"[{now_stamp()}] [ERROR] {e}")
        sys.stdout.flush()
        return

    # 実行
    code = stream_run(cmd, env, cwd=SCRIPTS_DIR)
    #print(f"[{now_stamp()}] [INFO] 完了（コード={code}）")
    sys.stdout.flush()

def main():
    qs = os.environ.get("QUERY_STRING", "")
    if "action=run" in qs:
        run_action()
    else:
        render_ui()

if __name__ == "__main__":
    main()
