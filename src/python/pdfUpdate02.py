# file: main.py
import argparse
import re
from typing import Iterable, List, Set
from firebase_admin import credentials, storage
import requests
import os

SERVICE_ACCOUNT_KEY_PATH = '/home/poly/src/wanted/poly9wanted-firebase-adminsdk.json'
FIREBASE_PROJECT_ID = 'poly9wanted' # FirebaseプロジェクトID
LAN_WEB_SERVICE_HOST = '10.200.1.1' # LAN内WebサービスのホストIPアドレス

def upload_pdf_from_lan(year: int, number: int):
    """
    LAN内のWebサービスからPDFを取得し、Firebase Storageにアップロードします。

    Args:
        year (int): PDFファイルの年 (例: '2023')
        number (int): PDFファイルの番号 (例: '001')
    """
    lan_pdf_url = f"http://{LAN_WEB_SERVICE_HOST}/wanted/pdf/{year}/{number}.pdf"
    firebase_storage_path = f"contents/pdf/{year}/{number}.pdf"
    local_pdf_dir = f"/home/poly/job-postings/public/contents/pdf/{year}"
    local_pdf_path = os.path.join(local_pdf_dir, f"{number}.pdf")

    print(f"\n--- PDFアップロード処理を開始します ---")
    print(f"LAN内のPDF URL: {lan_pdf_url}")
    print(f"Firebase Storageパス: {firebase_storage_path}")

    try:
        # 1. LAN内のWebサービスからPDFを取得
        print(f"LANからPDF ({lan_pdf_url}) をダウンロード中...")
        response = requests.get(lan_pdf_url, stream=True, timeout=10) # タイムアウトを設定
        response.raise_for_status()  # HTTPエラーがあれば例外を発生させる
        print("PDFのダウンロードに成功しました。")

        # 2. ローカルにPDFを保存 (既存ファイルは上書き)
        print(f"ローカルパス ({local_pdf_path}) にPDFを保存中...")
        os.makedirs(local_pdf_dir, exist_ok=True) # ディレクトリが存在しない場合は作成
        with open(local_pdf_path, 'wb') as f:
            f.write(response.content)
        print("PDFのローカル保存に成功しました。")

    except requests.exceptions.RequestException as e:
        print(f"LAN内のWebサービスからのPDFダウンロード中にエラーが発生しました: {e}")
    except IOError as e:
        print(f"ローカルファイルへの保存中にエラーが発生しました: {e}")
    except Exception as e:
        print(f"Firebase Storageへのアップロード中にエラーが発生しました: {e}")

def parse_numbers(tokens: Iterable[str]) -> List[int]:
    """
    文字列トークン群（例: ["1", "3-6", "10"]）を整数リストに展開する。
    - 単体数値: "7" -> [7]
    - 範囲: "3-6" -> [3,4,5,6]
    - 空白区切りで複数可: ["1", "3-6", "10"]
    エラー時は ValueError を投げる。
    """
    nums: Set[int] = set()
    hyphen_pattern = re.compile(r"^\s*(-?\d+)\s*[-?ー~]\s*(-?\d+)\s*$")  # "3-6", "3~6", "3～6", "3ー6" も許容

    for token in tokens:
        token = token.strip()
        if not token:
            continue

        # 範囲（3-6 等）
        m = hyphen_pattern.match(token)
        if m:
            start, end = int(m.group(1)), int(m.group(2))
            if start > end:
                raise ValueError(f"範囲の始点が終点より大きいです: '{token}'")
            nums.update(range(start, end + 1))
            continue

        # 単体（整数）
        try:
            n = int(token)
            nums.add(n)
        except ValueError:
            raise ValueError(f"番号の形式が不正です: '{token}'")

    return sorted(nums)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="年度と番号（複数・範囲対応）を引数で受け取る"
    )
    p.add_argument(
        "-y", "--year",
        type=int,
        required=True,
        help="年度（例: 2027）"
    )
    p.add_argument(
        "-n", "--nums",
        nargs="+",              # 空白区切りで複数受け取る
        required=True,
        help="番号（複数/範囲指定可。例: 1 3-6 10）"
    )
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        expanded = parse_numbers(args.nums)
    except ValueError as e:
        parser.error(str(e))

    year = args.year
    print(f"年度: {year}")
    print(f"番号（展開後）: {expanded}")

    print(f"{year}年度のpdfをコピーします。")
    for no in expanded:
        upload_pdf_from_lan(year=year, number=no)

if __name__ == "__main__":
    main()
