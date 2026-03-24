# rename_field.py

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# --- 設定 ---
# サービスアカウントキーのパスを修正してください
# ダウンロードしたJSONファイルをプロジェクトのどこかに配置し、そのパスを指定します。
SERVICE_ACCOUNT_KEY_PATH = '../poly9wanted-firebase-adminsdk-20260121.json'

COLLECTION_NAME = 'departments'  # 対象のコレクション名
OLD_FIELD_NAME = 'isvalid'       # 変更前のフィールド名
NEW_FIELD_NAME = 'isValid'       # 変更後のフィールド名
# --- 設定ここまで ---

# Firebase Admin SDK を初期化
try:
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase Admin SDK initialized successfully.")
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")
    print("Please ensure the service account key path is correct and the JSON file is valid.")
    exit(1) # 初期化失敗時は終了

async def rename_firestore_field():
    print(f"Starting field rename from '{OLD_FIELD_NAME}' to '{NEW_FIELD_NAME}' in '{COLLECTION_NAME}' collection...")

    collection_ref = db.collection(COLLECTION_NAME)
    
    try:
        docs = collection_ref.stream() # 全ドキュメントをストリームで取得
    except Exception as e:
        print(f"Error streaming documents from '{COLLECTION_NAME}': {e}")
        print("Please check your Firestore security rules and network connectivity.")
        exit(1)

    batch = db.batch()
    update_count = 0
    
    # バッチ書き込みの最大サイズ (500)
    MAX_BATCH_SIZE = 499 

    for doc in docs:
        data = doc.to_dict()
        
        # 古いフィールド名が存在するかどうかを確認
        if OLD_FIELD_NAME in data:
            doc_ref = collection_ref.document(doc.id)
            old_field_value = data[OLD_FIELD_NAME]

            print(f"  Updating document ID: {doc.id} - '{OLD_FIELD_NAME}' value: {old_field_value}")

            # バッチに更新操作を追加: 新しいフィールドを設定し、古いフィールドを削除
            batch.update(doc_ref, {
                NEW_FIELD_NAME: old_field_value,
                OLD_FIELD_NAME: firestore.DELETE_FIELD # 古いフィールドを削除
            })
            update_count += 1

            # バッチが最大サイズに達したらコミットし、新しいバッチを開始
            if update_count % MAX_BATCH_SIZE == 0:
                print(f"  Committing batch with {MAX_BATCH_SIZE} updates...")
                await batch.commit()
                batch = db.batch() # 新しいバッチを作成
                update_count = 0 # カウンターをリセット

    # 残りのバッチをコミット
    if update_count > 0:
        print(f"  Committing final batch with {update_count} updates...")
        await batch.commit()
        print("Field renaming complete!")
    else:
        print(f"No documents found with '{OLD_FIELD_NAME}' field. No updates made.")

# 非同期関数として実行
# Python 3.7+ では、トップレベルで await を使うために
# asyncio.run() を使うか、Jupyter Notebook のような環境で実行する必要があります。
# 通常のスクリプトとして実行する場合は、以下のようにします。
import asyncio
asyncio.run(rename_firestore_field())
