# -*- coding: utf-8 -*-
"""
募集学科 (例: K00110001100) を展開し、(求人票id, 科id) を 募集科 テーブルに格納するスクリプト

- 接続先: MariaDB (user=poly, password=password)
- 動作:
    1) 募集科テーブルを作成 (存在しなければ)
    2) 求人票tbl から (求人票id, 募集学科) を全件読み出し
    3) 募集学科が K + 11桁の0/1 の場合だけ展開して (求人票id, 科id) を一括INSERT
    4) 冪等性担保: 主キー(求人票id, 科id)により重複は自動で排除
- 実行:
    python build_boshuka.py --host localhost --port 3306 --db YOUR_DB_NAME [--rebuild]
    ※ --rebuild 指定時は一度 TRUNCATE して全再構築
"""

import sys
import re
import unicodedata
import argparse
from typing import List, Tuple

import mariadb

PATTERN = re.compile(r'^[KＫ][01]{11}$')  # 全角Kにも一応対応

def create_table_if_not_exists(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS 募集科 (
          求人票id INT NOT NULL,
          科id TINYINT NOT NULL,
          PRIMARY KEY (求人票id, 科id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

def truncate_boshuka(cur):
    cur.execute("TRUNCATE TABLE 募集科;")

def normalize_boshuu(s: str) -> str:
    """
    正規化: 全角を半角へ (例: 'Ｋ001...' → 'K001...')、前後空白除去
    """
    if s is None:
        return ''
    s = s.strip()
    s = unicodedata.normalize('NFKC', s)
    return s

def parse_bits(b: str) -> List[int]:
    """
    'K' + 11桁の 0/1 文字列を受け取り、'1' の位置を返す（1始まり）.
    例: K00110001100 -> [3, 4, 8, 9]
    """
    bits = b[1:]  # 先頭Kを除去
    result = []
    for i, ch in enumerate(bits, start=1):
        if ch == '1':
            result.append(i)
    return result

def batch_insert(cur, rows: List[Tuple[int, int]]):
    """
    rows: [(求人票id, 科id), ...]
    主キー重複を無視するため INSERT IGNORE を使用
    """
    if not rows:
        return
    cur.executemany(
        "INSERT IGNORE INTO 募集科 (求人票id, 科id) VALUES (?, ?)",
        rows
    )

def main():
    parser = argparse.ArgumentParser(description="求人票tbl.募集学科のビット展開 → 募集科テーブル作成/投入")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=3306)
    parser.add_argument("--db", required=True, help="接続先データベース名")
    parser.add_argument("--user", default="poly")
    parser.add_argument("--password", default="password")
    parser.add_argument("--rebuild", action="store_true", help="募集科をTRUNCATEして全再構築")
    parser.add_argument("--batch-size", type=int, default=5000, help="INSERTのバッチ件数（(求人票id, 科id) の組数）")
    args = parser.parse_args()

    conn = None
    try:
        conn = mariadb.connect(
            user=args.user,
            password=args.password,
            host=args.host,
            port=args.port,
            database=args.db,
            autocommit=False
        )
        cur = conn.cursor()

        # 1) テーブル作成
        create_table_if_not_exists(cur)
        if args.rebuild:
            truncate_boshuka(cur)
        conn.commit()

        # 2) データ読み出し
        cur.execute("SELECT 求人票id, 募集学科 FROM 求人票tbl")
        rows = cur.fetchall()

        to_insert: List[Tuple[int, int]] = []
        total_pairs = 0
        invalid_count = 0

        for idx, (kyujin_id, raw) in enumerate(rows, start=1):
            b = normalize_boshuu(raw)
            if not PATTERN.match(b):
                invalid_count += 1
                # 必要ならログ: print(f"[WARN] ID={kyujin_id} 無効な募集学科: {raw}", file=sys.stderr)
                continue

            ones = parse_bits(b)
            # (求人票id, 科id) を追加
            for dep_id in ones:
                to_insert.append((int(kyujin_id), int(dep_id)))
                total_pairs += 1

            # バッチ挿入
            if len(to_insert) >= args.batch_size:
                batch_insert(cur, to_insert)
                conn.commit()
                to_insert.clear()

        # 余りを投入
        if to_insert:
            batch_insert(cur, to_insert)
            conn.commit()
            to_insert.clear()

        print(f"処理完了: 求人票 {len(rows)} 件, 生成ペア {total_pairs} 件, 無効レコード {invalid_count} 件")

        # --- 動作確認の一例（ID=1 がサンプルとして存在するなら）---
        try:
            cur.execute("SELECT 科id FROM 募集科 WHERE 求人票id = 1 ORDER BY 科id")
            sample = [r[0] for r in cur.fetchall()]
            print(f"[Check] 求人票id=1 の 科id: {sample}  (期待例: [3, 4, 8, 9])")
        except Exception:
            pass

        conn.commit()

    except mariadb.Error as e:
        print(f"[ERROR] MariaDB error: {e}", file=sys.stderr)
        if conn:
            conn.rollback()
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()

