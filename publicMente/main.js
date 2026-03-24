import { collection, query, where, orderBy, limit, getDocs, doc, getDoc, setDoc, deleteDoc } from 'firebase/firestore';
import { auth, db } from './firebase';
import { onAuthStateChanged } from 'firebase/auth';
// 認証状態の監視を開始 ブラウザのコンソールに表示してくれる
onAuthStateChanged(auth, (user) => {
    if (user) {
        // ユーザーがログインしている場合
        console.log('User is signed in:', user.email);
        // ログイン済みユーザー向けのUI表示や、Firebaseのセキュリティルールが適用されるFirestoreへの書き込み処理など
        // ログイン済みユーザーにしかできない操作（例: jobPostingsへの書き込みなど）
    }
    else {
        // ユーザーがログアウトしている場合
        console.log('No user is signed in.');
        // 例: ログインページへの自動リダイレクト
        // if (window.location.pathname !== '/login.html') {
        //   window.location.href = '/login.html';
        // }
    }
});
// --- DOM Elements ---
const inputReceptionYear = document.getElementById('inputReceptionYear');
const inputReceptionNumber = document.getElementById('inputReceptionNumber');
const newRegistrationBtn = document.getElementById('newRegistrationBtn');
const confirmModifyBtn = document.getElementById('confirmModifyBtn');
const deleteBtn = document.getElementById('deleteBtn');
const recruitmentYearField = document.getElementById('recruitmentYear');
const receptionNumberField = document.getElementById('receptionNumber');
const recruitingDepartmentsDiv = document.getElementById('recruitingDepartments');
const ownerNameField = document.getElementById('ownerName');
const ownerNameKanaField = document.getElementById('ownerNameKana');
const postalCodeField = document.getElementById('postalCode');
const prefectureField = document.getElementById('prefecture');
const addressField = document.getElementById('address');
const buildingNameField = document.getElementById('buildingName');
const phoneNumberField = document.getElementById('phoneNumber');
const capitalField = document.getElementById('capital');
const numberOfEmployeesField = document.getElementById('numberOfEmployees');
const companyTypeField = document.getElementById('companyType');
const industryClassificationField = document.getElementById('industryClassification');
const jobTypeField = document.getElementById('jobType');
const notesField = document.getElementById('notes');
const urlField = document.getElementById('url');
const submitBtn = document.getElementById('submitBtn');
const cancelBtn = document.getElementById('cancelBtn');
const pdfViewer = document.getElementById('pdfViewer');
// --- Global Variables ---
let allDepartments = [];
// --- Helper Functions ---
/**
 * Firestoreから有効な部署リストを取得し、チェックボックスとして表示する
 */
async function loadDepartments() {
    recruitingDepartmentsDiv.innerHTML = ''; // Clear existing checkboxes
    try {
        const departmentsCol = collection(db, 'departments');
        const q = query(departmentsCol, where('isValid', '==', true), orderBy('order'));
        const querySnapshot = await getDocs(q);
        allDepartments = querySnapshot.docs.map((doc) => ({
            id: doc.id,
            name: doc.data().name
        }));
        allDepartments.forEach(dept => {
            const div = document.createElement('div');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `dept-${dept.id}`;
            checkbox.value = dept.id;
            const label = document.createElement('label');
            label.htmlFor = `dept-${dept.id}`;
            label.textContent = dept.name;
            div.appendChild(checkbox);
            div.appendChild(label);
            recruitingDepartmentsDiv.appendChild(div);
        });
    }
    catch (error) {
        console.error("Error loading departments:", error);
        alert("部署情報の読み込み中にエラーが発生しました。");
    }
}
/**
 * フォームの入力値をクリアする
 */
function clearForm() {
    recruitmentYearField.value = '';
    receptionNumberField.value = '';
    ownerNameField.value = '';
    ownerNameKanaField.value = '';
    postalCodeField.value = '';
    prefectureField.value = '';
    addressField.value = '';
    buildingNameField.value = '';
    phoneNumberField.value = '';
    capitalField.value = '';
    numberOfEmployeesField.value = '';
    companyTypeField.value = '';
    industryClassificationField.value = '';
    jobTypeField.value = '';
    notesField.value = '';
    urlField.value = '';
    // Clear checkboxes
    const checkboxes = recruitingDepartmentsDiv.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = false);
}
/**
 * 指定された年度と受付番号に基づいてFirestoreからデータを読み込み、フォームに表示する
 */
async function loadJobPosting(year, number) {
    if (!year || !number) {
        // alert("年度と受付番号を入力してください。"); // このアラートは confirmModifyBtn 側で制御する
        return false;
    }
    const nstr = String(number).padStart(4, '0');
    const docId = `${year}:${nstr}`;
    try {
        const jobPostingDocRef = doc(db, 'jobPostings', docId);
        const docSnap = await getDoc(jobPostingDocRef);
        if (docSnap.exists()) {
            const data = docSnap.data();
            recruitmentYearField.value = String(data.recruitmentYear || '');
            receptionNumberField.value = String(data.receptionNumber || '');
            ownerNameField.value = data.ownerName || '';
            ownerNameKanaField.value = data.ownerNameKana || '';
            postalCodeField.value = data.postalCode || '';
            prefectureField.value = data.prefecture || '';
            addressField.value = data.city || '';
            buildingNameField.value = data.buildingName || '';
            phoneNumberField.value = data.phoneNumber || '';
            capitalField.value = data.capital || '';
            numberOfEmployeesField.value = data.numberOfEmployees || '';
            companyTypeField.value = data.companyType || '';
            industryClassificationField.value = data.industryClassification || '';
            jobTypeField.value = data.jobType || '';
            notesField.value = data.notes || '';
            urlField.value = data.url || '';
            // Set recruitingDepartments checkboxes
            const checkedDepartments = data.recruitingDepartments || [];
            const checkboxes = recruitingDepartmentsDiv.querySelectorAll('input[type="checkbox"]');
            checkboxes.forEach(cb => {
                // ドキュメントIDが文字列で、recruitingDepartmentsが数値の配列の場合を考慮し、型を合わせる
                cb.checked = checkedDepartments.includes(Number(cb.value));
            });
            updatePdfViewer(year, number);
            return true;
        }
        else {
            // alert("指定された求人票は見つかりませんでした。"); // このアラートは confirmModifyBtn 側で制御する
            clearForm();
            updatePdfViewer(0, 0); // Clear PDF viewer
            return false;
        }
    }
    catch (error) {
        console.error("Error loading job posting:", error);
        alert("求人票の読み込み中にエラーが発生しました。");
        clearForm();
        updatePdfViewer(0, 0); // Clear PDF viewer
        return false;
    }
}
/**
 * フォームの入力値から求人票データオブジェクトを生成する
 */
function getFormData() {
    const formData = {};
    // Only include fields that have values (空文字列も除外)
    if (ownerNameField.value !== '')
        formData.ownerName = ownerNameField.value;
    if (ownerNameKanaField.value !== '')
        formData.ownerNameKana = ownerNameKanaField.value;
    if (postalCodeField.value !== '')
        formData.postalCode = postalCodeField.value;
    if (prefectureField.value !== '')
        formData.prefecture = prefectureField.value;
    if (addressField.value !== '')
        formData.city = addressField.value;
    if (buildingNameField.value !== '')
        formData.buildingName = buildingNameField.value;
    if (phoneNumberField.value !== '')
        formData.phoneNumber = phoneNumberField.value;
    if (capitalField.value !== '')
        formData.capital = capitalField.value;
    if (numberOfEmployeesField.value !== '')
        formData.numberOfEmployees = numberOfEmployeesField.value;
    if (companyTypeField.value !== '')
        formData.companyType = companyTypeField.value;
    if (industryClassificationField.value !== '')
        formData.industryClassification = industryClassificationField.value;
    if (jobTypeField.value !== '')
        formData.jobType = jobTypeField.value;
    if (notesField.value !== '')
        formData.notes = notesField.value;
    if (urlField.value !== '')
        formData.url = urlField.value;
    const selectedDepartments = [];
    recruitingDepartmentsDiv.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
        selectedDepartments.push(Number(cb.value));
    });
    // チェックが一つもなければ含めない、または空の配列として含めるかはお好みで
    if (selectedDepartments.length > 0) {
        formData.recruitingDepartments = selectedDepartments;
    }
    else {
        // 全て選択解除された場合は空の配列として保存
        formData.recruitingDepartments = [];
    }
    return formData;
}
/**
 * PDFビューアを更新する
 */
function updatePdfViewer(year, number) {
    if (year && number) {
        pdfViewer.src = `https://poly9wanted.web.app/contents/pdf/${year}/${number}.pdf`;
    }
    else {
        pdfViewer.src = ''; // Clear PDF viewer
    }
}
/**
 * 次の年度の初期値を計算して返します。
 * @returns 次の年度の文字列
 */
function getInitialReceptionYear() {
    const currentYear = new Date().getFullYear();
    return String(currentYear + 1); // 次の年度
}
/**
 * 指定された年度の最新の受付番号を取得し、次の受付番号を返します。
 * データがなければ '1' を返します。
 * @param yearNumber 取得したい年度の数値
 * @returns 次の受付番号の文字列
 */
async function getMaxReceptionNumber(yearNumber) {
    try {
        const jobPostingsCol = collection(db, 'jobPostings'); // Firestoreのdbインスタンスを使用
        const q = query(jobPostingsCol, where('recruitmentYear', '==', yearNumber), orderBy('receptionNumber', 'desc'), limit(1));
        const latestJobPostingQuery = await getDocs(q);
        if (!latestJobPostingQuery.empty) {
            // 最新の受付番号を取得し、1を加算
            const latestNumber = parseInt(latestJobPostingQuery.docs[0].data().receptionNumber, 10);
            return String(latestNumber); // 最新の番号に1を加算
        }
        else {
            return '1'; // 該当年度のデータがなければ1から
        }
    }
    catch (error) {
        console.error("Error getting next reception number:", error);
        return '1'; // エラー発生時もデフォルトで1を返す
    }
}
/**
 * 年と受付番号の初期値をHTML要素に設定します。
 * 既存のinputReceptionYearとinputReceptionNumber要素に値を代入します。
 */
async function setDefaultValues() {
    // 年の初期値を設定 (inputReceptionYearが既に値を持っていれば上書きしない)
    if (!inputReceptionYear.value) {
        inputReceptionYear.value = getInitialReceptionYear();
    }
    // 受付番号の初期値を設定
    // inputReceptionYear.value が設定されていることが前提
    const yearForReceptionNumber = Number(inputReceptionYear.value);
    inputReceptionNumber.value = await getMaxReceptionNumber(yearForReceptionNumber);
}
// --- Event Handlers ---
newRegistrationBtn.addEventListener('click', async () => {
    const year = Number(inputReceptionYear.value);
    const number = Number(inputReceptionNumber.value);
    if (!year || !number) { // 受付番号の自動生成はしない
        alert("登録する求人票の年度と受付番号を指定してください。");
        return;
    }
    clearForm();
    // 受付番号が重なっていると更新として取り扱う。
    const exists = await loadJobPosting(year, number);
    if (exists) { // あれば表示
        alert("既に求人情報が登録されています。登録求人票情報を表示します。");
        updatePdfViewer(year, number);
    }
    else {
        // 上段の値を中段の編集不可フィールドに反映
        recruitmentYearField.value = String(year);
        receptionNumberField.value = String(number);
        updatePdfViewer(year, number); // pdfがあれば表示
        alert("新規登録モードです。必要事項を入力してください。");
    }
});
confirmModifyBtn.addEventListener('click', async () => {
    const year = Number(inputReceptionYear.value);
    const number = Number(inputReceptionNumber.value);
    if (!year || !number) {
        alert("確認・修正する求人票の年度と受付番号を入力してください。");
        return;
    }
    const exists = await loadJobPosting(year, number);
    if (exists) {
        recruitmentYearField.value = String(year); // 上段の値を中段に反映
        receptionNumberField.value = String(number); // 上段の値を中段に反映
        alert("確認・修正モードです。中段のデータを修正し、「編集完了」を押してください。");
    }
    else {
        // 上段の値を中段の編集不可フィールドに反映
        recruitmentYearField.value = String(year);
        receptionNumberField.value = String(number);
        alert("指定された求人票は見つかりませんでした。");
    }
    updatePdfViewer(year, number); // pdfがあれば表示
});
deleteBtn.addEventListener('click', async () => {
    const year = Number(recruitmentYearField.value);
    const number = Number(receptionNumberField.value);
    if (!year || !number) {
        alert("削除する求人票の年度と受付番号を確認してください。削除できません。");
        return;
    }
    const docId = `${year}:${number.toString().padStart(4, '0')}`;
    if (confirm(`求人票 (年度: ${year}, 受付番号: ${number.toString().padStart(4, '0')}) 登録情報を本当に削除しますか？`)) {
        try {
            const jobPostingDocRef = doc(db, 'jobPostings', docId);
            await deleteDoc(jobPostingDocRef);
            alert("求人票登録情報を削除しました。");
            clearForm();
            setDefaultValues();
            //updatePdfViewer(Number(recruitmentYearField.value), Number(receptionNumberField.value));
        }
        catch (error) {
            console.error("Error deleting job posting:", error);
            alert("求人票登録情報の削除中にエラーが発生しました。");
        }
    }
});
submitBtn.addEventListener('click', async () => {
    const year = Number(recruitmentYearField.value);
    const number = Number(receptionNumberField.value);
    if (!year || !number) {
        alert("年度と受付番号が設定されていません。新規登録または確認・修正で設定してください。");
        return;
    }
    const docId = `${year}:${number.toString().padStart(4, '0')}`;
    const formData = getFormData();
    alert("更新します。" + docId);
    // recruitmentYearとreceptionNumberはdocIdから取得できるが、念のためデータにも含める
    formData.recruitmentYear = year;
    formData.receptionNumber = String(number).padStart(4, '0');
    try {
        const jobPostingDocRef = doc(db, 'jobPostings', docId);
        await setDoc(jobPostingDocRef, formData, { merge: true });
        alert("求人票情報を登録・更新しました。" + docId);
        // 最新のデータを再読み込みしてフォームを更新
        await loadJobPosting(year, number);
        updatePdfViewer(year, number);
    }
    catch (error) {
        console.error("Error saving job posting:", error);
        alert("求人票情報の保存中にエラーが発生しました。");
    }
});
cancelBtn.addEventListener('click', () => {
    clearForm();
    setDefaultValues();
    updatePdfViewer(0, 0); // Clear PDF viewer
    alert("入力をキャンセルしました。");
});
// 上段の年度・受付番号が変更されたら
inputReceptionYear.addEventListener('change', () => {
    //    recruitmentYearField.value = inputReceptionYear.value;
});
inputReceptionNumber.addEventListener('change', () => {
    //    receptionNumberField.value = inputReceptionNumber.value;
});
// --- Initialization ---
document.addEventListener('DOMContentLoaded', async () => {
    await loadDepartments(); // 部署情報を最初に読み込む
    await setDefaultValues(); // 初期値を設定
    recruitmentYearField.value = inputReceptionYear.value;
    receptionNumberField.value = inputReceptionNumber.value;
    // 初期表示時もPDFビューアを更新
    //updatePdfViewer(Number(inputReceptionYear.value), Number(inputReceptionNumber.value));
});
