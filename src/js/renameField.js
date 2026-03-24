// scripts/renameField.js
// departmentsのisvalidがisValidでは参照できないためフィールド名を修正する
const admin = require('firebase-admin');
const serviceAccount = require('../poly9wanted-firebase-adminsdk-20260121.json'); // サービスアカウントキーのパスを修正してください

// Firebase Admin SDK を初期化
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

async function renameIsValidToIsValid() {
  const collectionRef = db.collection('departments');
  const snapshot = await collectionRef.get();

  if (snapshot.empty) {
    console.log('No documents found in "departments" collection.');
    return;
  }

  const batch = db.batch();
  let updateCount = 0;

  console.log(`Found ${snapshot.size} documents in "departments" collection. Checking for 'isvalid' field...`);

  snapshot.docs.forEach(doc => {
    const data = doc.data();
    
    // フィールド 'isvalid' が存在するかどうかを確認
    if (Object.prototype.hasOwnProperty.call(data, 'isvalid')) {
      const docRef = collectionRef.doc(doc.id);
      const isvalidValue = data.isvalid;

      console.log(`Updating document ID: ${doc.id} - 'isvalid' value: ${isvalidValue}`);

      // バッチに更新操作を追加: 新しいフィールド 'isValid' を設定し、古いフィールド 'isvalid' を削除
      batch.update(docRef, {
        isValid: isvalidValue,
        isvalid: admin.firestore.FieldValue.delete() // 古いフィールドを削除
      });
      updateCount++;
    }
  });

  if (updateCount > 0) {
    console.log(`Committing batch with ${updateCount} updates...`);
    await batch.commit();
    console.log('Field renaming complete!');
  } else {
    console.log('No documents found with "isvalid" field. No updates made.');
  }
}

// 関数を実行
renameIsValidToIsValid().catch(error => {
  console.error('Error renaming field:', error);
  process.exit(1); // エラーが発生した場合は終了コード1で終了
});
