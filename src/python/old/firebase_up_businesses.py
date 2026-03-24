import mysql.connector
import firebase_admin
from firebase_admin import credentials, firestore
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
COLLECTION_NAME = 'businesses' # 例: 'businesses' コレクション

# Firestoreのバッチ書き込みサイズ (最大500ですが、安全のため少し小さめに設定)
BATCH_SIZE = 400

def upload_businesses_to_firestore():
    # 1. Firebase Admin SDKの初期化
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
        # 既に初期化されている場合はスキップ
        if not firebase_admin._apps:
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

        # 3. MariaDBから事業所データを取得
        print("MariaDBから事業所データを取得中...")
        query = """
            SELECT
                `事業所番号` AS businessId,
                `事業主名` AS ownerName,
                `事業主名カナ` AS ownerNameKana,
                `事業所名` AS businessName,
                `事業所名カナ` AS businessNameKana,
                `郵便番号` AS postalCode,
                `都道府県` AS prefecture,
                `市区町村` AS cityTownVillage,
                `ビル名` AS buildingName,
                `電話番号` AS phoneNumber,
                `従業員数` AS numEmployees,
                `資本金` AS capital,
                `産業分類` AS industryClassification,
                `職種` AS jobCategory,
                `会社区分` AS companyType,
                `url` AS url
            FROM `事業所tbl`
        """
        cursor.execute(query)

        businesses_data = []
        for row in cursor:
            businesses_data.append(row)
        print(f"{len(businesses_data)}件の事業所データを取得しました。")

        if not businesses_data:
            print("アップロードする事業所が見つかりませんでした。")
            return

        # 4. Firestoreへのバッチ書き込み準備
        batch = db.batch()
        batch_count = 0
        total_uploaded = 0

        print(f"Firestoreコレクション '{COLLECTION_NAME}' へのアップロードを開始します。")

        for i, data_row in enumerate(businesses_data):
            # データ変換とFirestoreドキュメントの準備
            firestore_doc_data = {
                'ownerName': data_row['ownerName'],
                'ownerNameKana': data_row['ownerNameKana'],
                'businessName': data_row['businessName'],
                'businessNameKana': data_row['businessNameKana'],
                'postalCode': data_row['postalCode'],
                'prefecture': data_row['prefecture'],
                'cityTownVillage': data_row['cityTownVillage'],
                'buildingName': data_row['buildingName'],
                'phoneNumber': data_row['phoneNumber'],
                'numEmployees': data_row['numEmployees'],
                'capital': data_row['capital'],
                'industryClassification': data_row['industryClassification'],
                'jobCategory': data_row['jobCategory'],
                'companyType': data_row['companyType'],
                'url': data_row['url'],
                'createdAt': firestore.SERVER_TIMESTAMP # アップロード日時をFirestore側で自動生成
            }

            # MariaDBの `事業所番号` をFirestoreのドキュメントIDとして使用
            # FirestoreのドキュメントIDは文字列である必要があるため、str()で変換
            doc_id = str(data_row['businessId'])
            doc_ref = db.collection(COLLECTION_NAME).document(doc_id)

            batch.set(doc_ref, firestore_doc_data) # set() はドキュメントが存在すれば上書き、なければ作成
            batch_count += 1

            # バッチサイズに達したらコミット
            if batch_count >= BATCH_SIZE:
                print(f"バッチ({batch_count}件)をコミット中...")
                batch.commit()
                total_uploaded += batch_count
                print(f"これまでにアップロードされた合計件数: {total_uploaded}")
                batch = db.batch() # 新しいバッチを開始
                batch_count = 0
                # 必要であれば短い休憩を入れ、Firestoreの書き込み制限に抵触する可能性を減らす
                # time.sleep(0.1)

        # 残りのドキュメントをコミット
        if batch_count > 0:
            print(f"最後のバッチ({batch_count}件)をコミット中...")
            batch.commit()
            total_uploaded += batch_count
            print(f"最終的にアップロードされた合計件数: {total_uploaded}")

        print("事業所のアップロードが完了しました！")

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
    upload_businesses_to_firestore()

