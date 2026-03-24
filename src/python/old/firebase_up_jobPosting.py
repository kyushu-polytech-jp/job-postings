import mysql.connector
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import time # for potential rate limiting or delays

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
# ダウンロードしたJSONファイルのパスを指定してください
SERVICE_ACCOUNT_KEY_PATH = '/home/poly/src/wanted/poly9wanted-firebase-adminsdk.json'

# Firestoreのコレクション名
COLLECTION_NAME = 'jobPostings'

# Firestoreのバッチ書き込みサイズ (最大500ですが、安全のため少し小さめに設定)
BATCH_SIZE = 400

def upload_job_postings_to_firestore():
    # 1. Firebase Admin SDKの初期化
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Firebase Admin SDKが正常に初期化されました。")
    except Exception as e:
        print(f"Firebase Admin SDKの初期化中にエラーが発生しました: {e}")
        return

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
        """
        cursor.execute(query)

        job_postings_data = []
        for row in cursor:
            job_postings_data.append(row)
        print(f"{len(job_postings_data)}件の求人票データを取得しました。")

        if not job_postings_data:
            print("アップロードする求人票が見つかりませんでした。")
            return

        # 4. Firestoreへのバッチ書き込み準備
        batch = db.batch()
        batch_count = 0
        total_uploaded = 0

        print(f"Firestoreコレクション '{COLLECTION_NAME}' へのアップロードを開始します。")

        for i, data_row in enumerate(job_postings_data):
            # データ変換とFirestoreドキュメントの準備
            firestore_doc_data = {
                'jobPostingId': data_row['jobPostingId'], # MariaDBのIDをFirestoreのフィールドとして保持
                'recruitmentYear': data_row['recruitmentYear'],
                'businessId': data_row['businessId'],
                'receptionNumber': data_row['receptionNumber'],
                'numPositions': data_row['numPositions'],
                'recruitingMajor': data_row['recruitingMajor'],
                'remarks': data_row['remarks'],
                'createdAt': firestore.SERVER_TIMESTAMP # アップロード日時をFirestore側で自動生成
            }

            # MariaDBのDATE型をFirestoreのTimestampに変換
            if data_row['receptionDate'] and isinstance(data_row['receptionDate'], datetime.date):
                # datetime.dateオブジェクトをdatetime.datetimeに変換
                firestore_doc_data['receptionDate'] = datetime.datetime.combine(
                    data_row['receptionDate'], datetime.time.min
                )
            elif data_row['receptionDate']:
                # 既にdatetimeオブジェクトやNoneでない場合はそのまま使用（エラー回避のため）
                firestore_doc_data['receptionDate'] = data_row['receptionDate']


            # Firestoreのドキュメントリファレンスを生成
            # ドキュメントIDはFirestoreに自動生成させるのが一般的です。
            doc_ref = db.collection(COLLECTION_NAME).document()

            # もしMariaDBの `求人票id` をFirestoreのドキュメントIDとして使いたい場合 (一意性が保証されている場合):
            # doc_ref = db.collection(COLLECTION_NAME).document(str(data_row['jobPostingId']))
            # ただし、`求人票id`が文字列として長すぎたり、特殊文字を含む場合は避けるべきです。

            batch.set(doc_ref, firestore_doc_data)
            batch_count += 1

            # バッチサイズに達したらコミット
            if batch_count >= BATCH_SIZE:
                print(f"バッチ({batch_count}件)をコミット中...")
                batch.commit()
                total_uploaded += batch_count
                print(f"これまでにアップロードされた合計件数: {total_uploaded}")
                batch = db.batch() # 新しいバッチを開始
                batch_count = 0
                # 短い休憩を入れることで、Firestoreの書き込み制限に抵触する可能性を減らせます
                # time.sleep(0.1)

        # 残りのドキュメントをコミット
        if batch_count > 0:
            print(f"最後のバッチ({batch_count}件)をコミット中...")
            batch.commit()
            total_uploaded += batch_count
            print(f"最終的にアップロードされた合計件数: {total_uploaded}")

        print("求人票のアップロードが完了しました！")

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
    upload_job_postings_to_firestore()

