from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# サービスアカウント キーを直接指定
SERVICE_ACCOUNT_KEY_PATH = '/home/poly/src/wanted/poly9wanted-firebase-adminsdk.json'
COLLECTION_NAME = 'jobPostings3'

def count_documents_aggregation():
    db = firestore.Client.from_service_account_json(SERVICE_ACCOUNT_KEY_PATH)
    query = db.collection(COLLECTION_NAME)

    query = query.where(filter=FieldFilter("recruitmentYear", "==", 2027))
    query = query.where(filter=FieldFilter("prefecture", "==", "福岡県"))

    results = query.stream()
    num=0
    for doc in results:
        print(f"{doc.id} => {doc.to_dict()}")
        num=num+1
    print(f"ドキュメント数: {num}")

    aggregation_query_obj = query.count()
    result_list = list(aggregation_query_obj.get())
    
    # 単一の集計結果 (count) から件数を読み取ります。
    # list(get()) の最初の要素が AggregationResult オブジェクトであり、
    # その .value プロパティにカウント値が含まれます。
    #print(result_list)
    count_value = result_list[0][0].value 
    
    return count_value

if __name__ == "__main__":
    total = count_documents_aggregation()
    print(f"{COLLECTION_NAME} のドキュメント数: {total}")
