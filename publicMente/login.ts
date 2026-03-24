// login.ts (または login.js)
import { signInWithEmailAndPassword } from 'firebase/auth';
import { auth } from './firebase'; // ステップ1で作成したFirebase初期化ファイルからauthをインポート

const loginForm = document.getElementById('loginForm') as HTMLFormElement;
const emailInput = document.getElementById('email') as HTMLInputElement;
const passwordInput = document.getElementById('password') as HTMLInputElement;
const errorMessageDisplay = document.getElementById('errorMessage') as HTMLParagraphElement;

loginForm.addEventListener('submit', async (event) => {
    event.preventDefault(); // フォームのデフォルト送信を防止

    const email = emailInput.value;
    const password = passwordInput.value;
    errorMessageDisplay.textContent = ''; // エラーメッセージをクリア

    try {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;

        console.log('ログイン成功！', user);
        // ここでログイン後のページにリダイレクトします
        // 例: window.location.href = '/admin-dashboard.html';
        alert('ログイン成功！'); // テスト用アラート。実際にはリダイレクトに置き換えてください
        window.location.href = '/index.html'; // ログイン後の管理画面へのパス
    } catch (error: any) {
        console.error('ログイン失敗:', error);
        let message = 'ログインに失敗しました。メールアドレスまたはパスワードが間違っています。';
        // Firebaseからのエラーコードに基づいてメッセージを調整することも可能です
        // if (error.code === 'auth/user-not-found' || error.code === 'auth/wrong-password') {
        //     message = 'メールアドレスまたはパスワードが間違っています。';
        // } else if (error.code === 'auth/invalid-email') {
        //     message = '無効なメールアドレス形式です。';
        // }
        errorMessageDisplay.textContent = message;
    }
});

