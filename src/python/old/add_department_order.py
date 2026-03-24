import firebase_admin
from firebase_admin import credentials, firestore

# Firebaseサービスアカウントキーのパス (必要であれば調整)
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

def add_order_field_to_departments():
    """
    'departments' コレクションの各ドキュメントに 'order' フィールドを追加します。
    ここでは、取得した順序に基づいて連番を割り当てます。
    """
    departments_ref = db.collection('departments')
    docs = departments_ref.stream() # 全てのドキュメントを取得

    batch = db.batch()
    order_number = 1
    processed_count = 0

    print("Starting to add 'order' field to 'departments' collection...")

    for doc in docs:
        doc_ref = departments_ref.document(doc.id)
        # ドキュメントに 'order' フィールドを追加または更新
        batch.update(doc_ref, {'order': order_number})
        order_number += 1
        processed_count += 1

        if processed_count % 500 == 0: # 500件ごとにバッチをコミット
            batch.commit()
            batch = db.batch() # 新しいバッチを開始
            print(f"Committed {processed_count} documents so far with 'order' field.")

    # 残りのバッチをコミット
    if processed_count % 500 != 0 or processed_count == 0:
        batch.commit()

    print(f"Finished. Added 'order' field to {processed_count} documents in 'departments' collection.")
    print("Please verify the assigned order values in your Firestore console.")

if __name__ == "__main__":
    add_order_field_to_departments()

