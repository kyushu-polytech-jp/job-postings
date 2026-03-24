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

def kyujinKensu():
    mariadb_conn = None
    try:
        # 2. MariaDBに接続
        mariadb_conn = mysql.connector.connect(**DB_CONFIG)
        cursor = mariadb_conn.cursor(dictionary=True) # カラム名辞書
        print("MariaDBに正常に接続しました。")

        # 3. MariaDBから求人票データを取得
        print("MariaDBから求人票データを取得中...")
        query = """
            SELECT 採用年,COUNT(*) 件数
            FROM `求人票tbl`
	    GROUP BY 採用年
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
    kyujinKensu()

