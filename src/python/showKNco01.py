from google.cloud import firestore

# サービスアカウント キーを直接指定
SERVICE_ACCOUNT_KEY_PATH = '/home/poly/src/wanted/poly9wanted-firebase-adminsdk.json'
COLLECTION_NAME = 'jobPostings3'

def count_documents_aggregation():
    db = firestore.Client.from_service_account_json(SERVICE_ACCOUNT_KEY_PATH)
    query = db.collection(COLLECTION_NAME)
    # 集約クエリで count を取得
    aggregation_query = query.count()
    result = list(aggregation_query.get())
    # 単一の集約結果から件数を読む
    count_value = result[0][0].value  # (AggregationField, AggregationResult) のタプル
    return count_value

if __name__ == "__main__":
    total = count_documents_aggregation()
    print(f"{COLLECTION_NAME} のドキュメント数: {total}")

