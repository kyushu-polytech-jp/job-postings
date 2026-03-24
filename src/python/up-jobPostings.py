# up-jobPosting.py
# jobPosting2の作り直し

import mysql.connector
import firebase_admin
from firebase_admin import credentials, firestore

# --- 設定情報 ---
load_dotenv()

# MariaDBの接続情報
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_DATABASE')
}

# 検索SQL
SQL_QUERY = """
select 採用年,受付番号 ,募集学科,備考,事業主名,事業主名カナ,郵便番号,都道府県,市区町村,ビル名,電話番号,従業員数,資本金,産業分類,職種,会社区分,url
from 求人票tbl k join 事業所tbl j on  k.事業所番号=j.事業所番号 
where 採用年 in(2026,2027);
"""

# Firebaseサービスアカウントキーのパス
SERVICE_ACCOUNT_KEY_PATH = '/home/poly/src/wanted/poly9wanted-firebase-adminsdk.json'

# Firebase Firestoreのコレクション名
FIRESTORE_COLLECTION_NAME = 'jobPosting2'

# 日本語カラム名と英語属性名のマッピング
COLUMN_MAPPING = {
    '採用年': 'recruitmentYear',
    '受付番号': 'receptionNumber',
    '募集学科': 'recruitingDepartments',
    '備考': 'notes',
    '事業主名': 'ownerName',
    '事業主名カナ': 'ownerNameKana',
    '郵便番号': 'postalCode',
    '都道府県': 'prefecture',
    '市区町村': 'cityTownVillage',
    'ビル名': 'buildingName',
    '電話番号': 'phoneNumber',
    '従業員数': 'numberOfEmployees',
    '資本金': 'capital',
    '産業分類': 'industryClassification',
    '職種': 'jobType',
    '会社区分': 'companyCategory',
    'url': 'url'
}

def migrate_data():
    """
    MariaDBからデータを取得し、Firestoreに移行するスクリプト。
    """
    print("--- データ移行処理を開始します ---")

    # 1. Firebaseの初期化
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Firebase Admin SDK の初期化に成功しました。")
    except Exception as e:
        print(f"Firebase Admin SDK の初期化中にエラーが発生しました: {e}")
        return

    # 2. MariaDBへの接続
    mariadb_connection = None
    try:
        mariadb_connection = mysql.connector.connect(**DB_CONFIG)
        cursor = mariadb_connection.cursor(dictionary=True) # カラム名をキーとする辞書として結果を取得
        print("MariaDBへの接続に成功しました。")
    except mysql.connector.Error as err:
        print(f"MariaDBへの接続中にエラーが発生しました: {err}")
        return

    # 3. SQLクエリの実行とデータ取得
    try:
        print("MariaDBからデータを取得しています...")
        cursor.execute(SQL_QUERY)
        records = cursor.fetchall()
        print(f"MariaDBから {len(records)} 件のレコードを取得しました。")
    except mysql.connector.Error as err:
        print(f"SQLクエリの実行中にエラーが発生しました: {err}")
        return
    finally:
        if mariadb_connection.is_connected():
            cursor.close()
            mariadb_connection.close()
            print("MariaDB接続を閉じました。")

    # 4. Firestoreへのデータ登録
    if not records:
        print("移行するデータがありません。")
        return

    print(f"Firestoreの '{FIRESTORE_COLLECTION_NAME}' コレクションにデータを登録します...")
    for i, row in enumerate(records):
        try:
            # ドキュメントIDの生成 (年度:受付番号4桁)
            recruitment_year = row['採用年']
            reception_number = str(row['受付番号']).zfill(4) # 4桁にゼロ埋め
            document_id = f"{recruitment_year}:{reception_number}"

            # Firestoreに登録するデータ辞書の作成
            firestore_data = {}
            for jp_col, en_attr in COLUMN_MAPPING.items():
                firestore_data[en_attr] = row[jp_col]
            
            # Firestoreにドキュメントを追加 (既存IDの場合は更新)
            doc_ref = db.collection(FIRESTORE_COLLECTION_NAME).document(document_id)
            doc_ref.set(firestore_data)

            if (i + 1) % 100 == 0:
                print(f"{i + 1} 件のデータを登録しました。")

        except Exception as e:
            print(f"ドキュメントID '{document_id}' の登録中にエラーが発生しました: {e}")
            continue # エラーが発生しても次のレコードの処理を続行

    print(f"--- データ移行処理が完了しました。合計 {len(records)} 件の処理を試行しました。---")

if __name__ == "__main__":
    migrate_data()

