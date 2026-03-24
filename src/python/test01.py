import mysql.connector
import datetime
from dotenv import load_dotenv
import os
# --- 設定情報 ---
load_dotenv()

# MariaDBの接続情報
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_DATABASE')
}

def upload_data_read():
    mariadb_conn = None
    try:
        # 2. MariaDBに接続
        mariadb_conn = mysql.connector.connect(**DB_CONFIG)
        cursor = mariadb_conn.cursor(dictionary=True) # カラム名をキーとする辞書で結果を取得
        print("MariaDBに正常に接続しました。")

        # 3. MariaDBから求人票データを取得
        print("MariaDBから求人票データを取得中...")
        query = """
            SELECT
                `求人票id` AS jobPostingId,
                `採用年` AS recruitmentYear,
                `事業所番号` AS businessId,
                `受付番号` AS receptionNumber,
                `求人数` AS numPositions,
                `受付日時` AS receptionDate,
                `募集学科` AS recruitingMajor,
                `備考` AS remarks
            FROM `求人票tbl`
	    WHERE 採用年 in (2026,2027)
        """
        cursor.execute(query)

        for row in cursor:
            print(row)

    except mysql.connector.Error as err:
        print(f"MariaDBエラー: {err}")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
    finally:
        if mariadb_conn:
            mariadb_conn.close()
            print("MariaDB接続を閉じました。")

# スクリプト実行
if __name__ == '__main__':
    upload_data_read()

