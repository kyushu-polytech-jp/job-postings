import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

def parse_recruiting_major(recruiting_major: str) -> list[int]:
    """recruitingMajor文字列を解析して、recruitingDepartmentsのリストを生成します。"""
    if not recruiting_major or not recruiting_major.startswith('K'):
        return []
    
    digits = recruiting_major[1:] # 'K' を除く
    recruiting_departments = []
    for i, digit in enumerate(digits):
        if digit == '1':
            recruiting_departments.append(i + 1) # 1-indexedの科ID
    return recruiting_departments

def update_job_postings():
    # Firebaseプロジェクトの初期化
    # サービスアカウントキーファイルへのパスを指定してください。
    # Firebase Consoleの「プロジェクト設定」->「サービスアカウント」から生成できます。
    # このファイルは公開リポジトリに含めないでください。
    cred = credentials.Certificate("/home/poly/src/wanted/poly9wanted-firebase-adminsdk.json")
    firebase_admin.initialize_app(cred)

    db = firestore.client()

    print("jobPostingsコレクションの更新を開始します...")

    job_postings_ref = db.collection('jobPostings2')
    docs = job_postings_ref.stream()

    updates = []
    for doc in docs:
        doc_data = doc.to_dict()
        if doc_data and 'recruitingMajor' in doc_data and isinstance(doc_data['recruitingMajor'], str):
            recruiting_major = doc_data['recruitingMajor']
            recruiting_departments = parse_recruiting_major(recruiting_major)

            print(f"ドキュメントID: {doc.id}, recruitingMajor: {recruiting_major} -> recruitingDepartments: {recruiting_departments}")

            # バッチ書き込みを使用して効率的に更新
            updates.append((doc.reference, {'recruitingDepartments': recruiting_departments}))
        else:
            print(f"ドキュメントID: {doc.id} には recruitingMajor フィールドがないか、形式が不正です。スキップします。")

    # バッチ書き込みの実行
    if updates:
        batch = db.batch()
        for doc_ref, data in updates:
            batch.update(doc_ref, data)
        batch.commit()
        print(f"{len(updates)} 件のドキュメントが更新されました。")
    else:
        print("更新対象のドキュメントは見つかりませんでした。")

    print("すべてのドキュメントの更新が完了しました。")

if __name__ == '__main__':
    update_job_postings()


