import firebase_admin
from firebase_admin import credentials, storage
import requests
import os

# --- 設定項目 ---
# サービスアカウントキーのパス
# ダウンロードしたJSONファイルのパスに置き換えてください
SERVICE_ACCOUNT_KEY_PATH = '/home/poly/src/wanted/poly9wanted-firebase-adminsdk.json'

# FirebaseプロジェクトID (例: poly9wanted)
FIREBASE_PROJECT_ID = 'poly9wanted'
# LAN内WebサービスのホストIPアドレス
LAN_WEB_SERVICE_HOST = '10.200.1.1'

# --- Firebase Admin SDKの初期化 ---
try:
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
    firebase_admin.initialize_app(cred, {
        'storageBucket': f"{FIREBASE_PROJECT_ID}.appspot.com"
    })
    print("Firebase Admin SDKが正常に初期化されました。")
except Exception as e:
    print(f"Firebase Admin SDKの初期化に失敗しました: {e}")
    exit()

def upload_pdf_from_lan(year: int, number: int):
    """
    LAN内のWebサービスからPDFを取得し、Firebase Storageにアップロードします。

    Args:
        year (int): PDFファイルの年 (例: '2023')
        number (int): PDFファイルの番号 (例: '001')
    """
    lan_pdf_url = f"http://{LAN_WEB_SERVICE_HOST}/wanted/pdf/{year}/{number}.pdf"
    firebase_storage_path = f"contents/pdf/{year}/{number}.pdf"
    # /home/poly/job-postings/public/contents/pdf/{year}/{number}.pdf
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

        # 3. Firebase Storageにアップロード
        bucket = storage.bucket() # デフォルトのStorageバケットを取得
        blob = bucket.blob(firebase_storage_path)

        # ファイルの内容を直接アップロード
        # content_typeを'application/pdf'に設定することが重要
        blob.upload_from_string(response.content, content_type='application/pdf')

        # 公開URLを取得 (必要であれば)
        # 注意: 適切にセキュリティルールを設定しないと、誰でもアクセスできるようになります
        # blob.make_public()
        # public_url = blob.public_url

        print(f"PDFがFirebase Storageに正常にアップロードされました: gs://{bucket.name}/{firebase_storage_path}")
        # if 'public_url' in locals():
        #     print(f"公開URL: {public_url}")

    except requests.exceptions.RequestException as e:
        print(f"LAN内のWebサービスからのPDFダウンロード中にエラーが発生しました: {e}")
    except IOError as e:
        print(f"ローカルファイルへの保存中にエラーが発生しました: {e}")
    except Exception as e:
        print(f"Firebase Storageへのアップロード中にエラーが発生しました: {e}")

if __name__ == "__main__":
    # 例: 2024年の001番のPDFをアップロード
    upload_pdf_from_lan(year='2027', number=236)

    # 必要に応じて他のPDFもアップロード
    # upload_pdf_from_lan(year='2024', number='002')

