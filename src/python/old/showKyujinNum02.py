from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# サービスアカウント キーを直接指定
SERVICE_ACCOUNT_KEY_PATH = '/home/poly/src/wanted/poly9wanted-firebase-adminsdk.json'
COLLECTION_NAME = 'jobPostings3'

def count_documents_aggregation():
    db = firestore.Client.from_service_account_json(SERVICE_ACCOUNT_KEY_PATH)
    query = db.collection(COLLECTION_NAME)

    #query = query.where("recruitmentYear", "==", 2027)
    query = query.where(filter=FieldFilter("recruitmentYear", "==", 2027))
    #query = query.where("prefecture", "==", "愛知県")

    aggregation_query_obj = query.count()
    
    # AggregationQuery オブジェクトの get() メソッドを実行して結果を取得します。
    # result は AggregationResult オブジェクトのリストになります。
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
