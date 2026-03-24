// scripts/addPrefectureToJobPostings.js
// 都道府県の情報がjobPostingsに含まれてなかったのでそれを登録する
//
const admin = require('firebase-admin');
//const serviceAccount = require('../poly9wanted-firebase-adminsdk-20260121.json'); // パスを修正
const serviceAccount = require('/home/poly/src/wanted/poly9wanted-firebase-adminsdk.json'); // パスを修正

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

async function addPrefectureFieldToJobPostings() {
  const jobPostingsRef = db.collection('jobPostings');
  const businessesRef = db.collection('businesses');

  const jobPostingsSnapshot = await jobPostingsRef.get();

  if (jobPostingsSnapshot.empty) {
    console.log('No documents found in "jobPostings" collection.');
    return;
  }

  const batch = db.batch();
  let updateCount = 0;

  console.log(`Processing ${jobPostingsSnapshot.size} job postings...`);

  for (const doc of jobPostingsSnapshot.docs) {
    const jobPostingData = doc.data();
    const jobPostingRef = jobPostingsRef.doc(doc.id);

    // jobPostingsにbusinessIdが存在するか確認
    if (jobPostingData.businessId) {
      const businessId = String(jobPostingData.businessId).trim();
      try {
        const businessDoc = await businessesRef.doc(businessId).get(); // businessesコレクションから対応するドキュメントを取得
        if (businessDoc.exists && businessDoc.data().prefecture) {
          const prefectureValue = businessDoc.data().prefecture;
          console.log(`  Updating jobPosting ID: ${doc.id} with prefecture: ${prefectureValue}`);
          batch.update(jobPostingRef, { prefecture: prefectureValue }); // prefectureフィールドを追加
          updateCount++;
        } else {
          console.warn(`  Warning: Business ID ${businessId} not found or no prefecture field for jobPosting ID: ${doc.id}`);
        }
      } catch (error) {
        console.error(`  Error fetching business ${businessId} for jobPosting ID ${doc.id}:`, error);
      }
    } else {
      console.warn(`  Warning: jobPosting ID: ${doc.id} has no businessId.`);
    }

    // バッチ書き込みの制限を考慮 (最大500件)
    if (updateCount % 499 === 0 && updateCount > 0) { // 499件ごとにコミット
      console.log(`  Committing batch with ${updateCount} updates...`);
      await batch.commit();
      batch = db.batch(); // 新しいバッチを開始
      updateCount = 0;
    }
  }

  // 残りのバッチをコミット
  if (updateCount > 0) {
    console.log(`Committing final batch with ${updateCount} updates...`);
    await batch.commit();
  }

  console.log('Successfully added prefecture field to job postings!');
}

addPrefectureFieldToJobPostings().catch(error => {
  console.error('Error adding prefecture field:', error);
  process.exit(1);
});

