from google.cloud import firestore

# サービスアカウント キーを直接指定
SERVICE_ACCOUNT_KEY_PATH = '/home/poly/src/wanted/poly9wanted-firebase-adminsdk.json'
COLLECTION_NAME = 'jobPostings'

def count_documents_aggregation():
    # 直接 Firestore クライアントを初期化します。
    db = firestore.Client.from_service_account_json(SERVICE_ACCOUNT_KEY_PATH)
    
    # コレクション参照を取得 (これは Query オブジェクトでもあります)
    query = db.collection(COLLECTION_NAME)
    
    # 最新のライブラリでは、コレクションとQuery オブジェクトは同じ扱いができる
    # counti()が利用できて、これが AggregationQuery オブジェクトを返す。
    aggregation_query_obj = query.count()
    
    # AggregationQuery オブジェクトの get() メソッドを実行して結果を取得します。
    # result は AggregationResult オブジェクトのリストになります。
    result_list = list(aggregation_query_obj.get())
    
    # 単一の集計結果 (count) から件数を読み取ります。
    # list(get()) の最初の要素が AggregationResult オブジェクトであり、
    # その .value プロパティにカウント値が含まれます。
    count_value = result_list[0][0].value 
    
    return count_value

if __name__ == "__main__":
    total = count_documents_aggregation()
    print(f"{COLLECTION_NAME} のドキュメント数: {total}")
