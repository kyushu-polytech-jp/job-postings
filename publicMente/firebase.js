// publicMente/firebase.ts
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore'; // Firestoreも利用する場合
// Firebaseプロジェクトの設定情報をここに記述してください。
// これらの情報はFirebaseコンソールの「プロジェクトの設定」->「全般」タブから確認できます。
// Firebase Configuration (from user input)
const firebaseConfig = {
    apiKey: "AIzaSyD0eZXGBFrmYKUdK1-h6tTRJrEh3v-CSz0",
    authDomain: "poly9wanted.firebaseapp.com",
    projectId: "poly9wanted",
    storageBucket: "poly9wanted.firebasestorage.app",
    messagingSenderId: "425756247340",
    appId: "1:425756247340:web:120fbc4093f9cbf26bd889"
};
// Firebaseアプリを初期化
const app = initializeApp(firebaseConfig);
// AuthサービスとFirestoreサービスを取得し、エクスポート
export const auth = getAuth(app);
export const db = getFirestore(app); // Firestoreを利用する場合
