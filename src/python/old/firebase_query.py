from firebase_admin import firestore
import firebase_admin
from firebase_admin import credentials

# Firebase Admin SDKが初期化されていない場合は初期化
if not firebase_admin._apps:
    cred = credentials.Certificate('/home/poly/src/wanted/poly9wanted-firebase-adminsdk.json')
    firebase_admin.initialize_app(cred)
db = firestore.client()

def search_job_postings_by_partial_business_name(partial_name: str):
    """
    事業所名の一部（前方一致）で求人票の年度とIDを検索します。
    部分文字列検索の制限とwhereInの制限があります。
    """
    matching_business_ids = []

    # 1. 事業所コレクションを検索し、前方一致する事業所のIDを取得
    # Firestoreで前方一致検索を行うテクニック
    end_char = chr(ord(partial_name[-1]) + 1)
    end_prefix = partial_name[:-1] + end_char

    print(f"事業所名 '{partial_name}' で始まる事業所を検索中...")
    businesses_ref = db.collection('businesses')
    query_businesses = businesses_ref.where('ownerName', '>=', partial_name).where('ownerName', '<', end_prefix)

    for doc in query_businesses.stream():
        # ドキュメントIDがbusinessIdとして使用されているため、doc.id を取得
        matching_business_ids.append(doc.id)
    
    print(f"一致する事業所ID: {matching_business_ids}")

    if not matching_business_ids:
        print("一致する事業所は見つかりませんでした。")
        return []

    # 2. 取得した事業所IDを使って求人票コレクションを検索
    job_postings_results = []
    job_postings_ref = db.collection('jobPostings')

    # whereInの制限 (最大10個) を考慮
    # 実際には、matching_business_ids が10を超える場合、
    # リストを分割して複数回クエリを実行する必要があります。
    if len(matching_business_ids) > 10:
        print("警告: 検索結果の事業所IDが10件を超えています。最初の10件のみで求人票を検索します。")
        # ここでリストを分割してループ処理を行う必要がありますが、簡略化のため最初の10件のみ
        ids_to_query = matching_business_ids[:10]
    else:
        ids_to_query = matching_business_ids

    # ids_to_query (文字列のリスト) を数値のリストに変換
    ids_to_query_int = [int(bid) for bid in ids_to_query]

    print(f"求人票を検索中 (事業所ID - 数値: {ids_to_query_int})...")
    # 変換した数値のリストを使ってクエリを実行
    query_job_postings = job_postings_ref.where('businessId', 'in', ids_to_query_int)

    print(f"求人票を検索中 (事業所ID: {ids_to_query})...")
    query_job_postings = job_postings_ref.where('businessId', 'in', ids_to_query)

    for doc in query_job_postings.stream():
        data = doc.to_dict()
        job_postings_results.append({
            '求人票id': data.get('jobPostingId'), # MariaDBの元ID
            '事業所ID': data.get('businessId'),
            '採用年': data.get('recruitmentYear')
        })
    
    return job_postings_results

# 実行例
search_term = "上野" # 例: 事業所名の前方一致で検索したい文字列
results = search_job_postings_by_partial_business_name(search_term)

if results:
    print("\n検索結果:")
    for job in results:
        print(f"求人票ID: {job['求人票id']}, 採用年: {job['採用年']}, 関連事業所ID: {job['事業所ID']}")
else:
    print("条件に合う求人票は見つかりませんでした。")


