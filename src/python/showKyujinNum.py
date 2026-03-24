from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# サービスアカウント キーを直接指定
SERVICE_ACCOUNT_KEY_PATH = '/home/poly/src/wanted/poly9wanted-firebase-adminsdk.json'
COLLECTION_NAME = 'jobPostings'

def count_documents_aggregation():
    db = firestore.Client.from_service_account_json(SERVICE_ACCOUNT_KEY_PATH)
    query = db.collection(COLLECTION_NAME)

    query2026 = query.where(filter=FieldFilter("recruitmentYear", "==", 2026))
    query2027 = query.where(filter=FieldFilter("recruitmentYear", "==", 2027))
    #query2028 = query.where(filter=FieldFilter("recruitmentYear", "==", 2028))

    aggregation_query2026_obj = query2026.count()
    aggregation_query2027_obj = query2027.count()
    result_list2026 = list(aggregation_query2026_obj.get())
    result_list2027 = list(aggregation_query2027_obj.get())
    
    # 単一の集計結果 (count) から件数を読み取ります。
    # list(get()) の最初の要素が AggregationResult オブジェクトであり、
    # その .value プロパティにカウント値が含まれます。
    #print(result_list)
    count_value2026 = result_list2026[0][0].value 
    count_value2027 = result_list2027[0][0].value 
    print(f"2026年度のドキュメント数: {count_value2026}")
    print(f"2027年度のドキュメント数: {count_value2027}")

if __name__ == "__main__":
    count_documents_aggregation()
