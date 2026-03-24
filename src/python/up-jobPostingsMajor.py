import mysql.connector
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

# --- 設定情報 ---
load_dotenv()

# MariaDBの接続情報
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_DATABASE')
}

# Firebaseサービスアカウントキーのパス
SERVICE_ACCOUNT_KEY_PATH = '/home/poly/src/wanted/poly9wanted-firebase-adminsdk.json'

# Firebase Admin SDKの初期化
try:
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase Admin SDK initialized successfully.")
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")
    exit()

def process_recruiting_major(recruiting_major_str):
    """
    募集学科文字列からrecruitingDepartmentsリストを生成します。
    例: "K10101000010" -> [1, 3, 5, 10]
    """
    recruiting_departments = []
    if recruiting_major_str and len(recruiting_major_str) == 12 and recruiting_major_str.startswith('K'):
        # 'K'の次の文字から11桁までを処理
        digits_part = recruiting_major_str[1:]
        for i, char in enumerate(digits_part):
            if char == '1':
                # 1-based index (Kの次が1桁目)
                recruiting_departments.append(i + 1)
    return recruiting_departments

def main():
    mariadb_conn = None
    try:
        # MariaDBに接続
        mariadb_conn = mysql.connector.connect(**DB_CONFIG)
        cursor = mariadb_conn.cursor(dictionary=True)
        print("Connected to MariaDB successfully.")

        # SQLクエリの定義
        sql_query = """
        select 採用年,受付番号 ,募集学科,備考,事業主名,事業主名カナ,郵便番号,都道府県,市区町村,ビル名,電話番号,従業員数,資本金,産業分類,職種,会社区分,url
        from 求人票tbl k join 事業所tbl j on k.事業所番号=j.事業所番号 
        where 採用年 in(2026,2027);
        """

        # SQLクエリの実行
        cursor.execute(sql_query)
        results = cursor.fetchall()
        print(f"Fetched {len(results)} records from MariaDB.")

        # Firestoreにデータをアップロード
        batch = db.batch()
        job_postings_ref = db.collection('jobPostings')
        processed_count = 0

        for row in results:
            recruitment_year = row.get('採用年')
            reception_number = row.get('受付番号')
            recruiting_major = row.get('募集学科')

            if recruitment_year is None or reception_number is None:
                print(f"Skipping row due to missing '採用年' or '受付番号': {row}")
                continue

            # ドキュメントIDの生成 (年度:受付番号の4桁)
            doc_id = f"{recruitment_year}:{str(reception_number).zfill(4)}"

            # recruitingDepartmentsの生成
            recruiting_departments = process_recruiting_major(recruiting_major)

            # Firestoreドキュメントデータの準備
            doc_data = {
                'recruitmentYear': recruitment_year,
                'receptionNumber': str(reception_number).zfill(4), # Ensure it's a 4-digit string
                'recruitingMajor': recruiting_major,
                'notes': row.get('備考'),
                'ownerName': row.get('事業主名'),
                'ownerNameKana': row.get('事業主名カナ'),
                'postalCode': row.get('郵便番号'),
                'prefecture': row.get('都道府県'),
                'city': row.get('市区町村'),
                'buildingName': row.get('ビル名'),
                'phoneNumber': row.get('電話番号'),
                'numberOfEmployees': row.get('従業員数'),
                'capital': row.get('資本金'),
                'industryClassification': row.get('産業分類'),
                'jobType': row.get('職種'),
                'companyType': row.get('会社区分'),
                'url': row.get('url'),
            }

            # recruitingDepartmentsが空でなければ追加
            if recruiting_departments:
                doc_data['recruitingDepartments'] = recruiting_departments
            else:
                # 明示的に存在しない場合はフィールドを追加しないか、null/空リストを設定
                # 今回は存在しない場合は追加しない方針で進めます。
                pass

            # バッチにドキュメントを追加
            doc_ref = job_postings_ref.document(doc_id)
            batch.set(doc_ref, doc_data)
            processed_count += 1

            if processed_count % 500 == 0: # 500件ごとにバッチをコミット
                batch.commit()
                batch = db.batch() # 新しいバッチを開始
                print(f"Committed {processed_count} documents so far.")

        # 残りのバッチをコミット
        if processed_count % 500 != 0 or processed_count == 0:
            batch.commit()
        print(f"Successfully uploaded {processed_count} documents to Firestore.")

    except mysql.connector.Error as err:
        print(f"MariaDB Error: {err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if mariadb_conn and mariadb_conn.is_connected():
            mariadb_conn.close()
            print("MariaDB connection closed.")

if __name__ == "__main__":
    main()

