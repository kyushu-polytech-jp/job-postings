// Firebase SDKのインポート
import { initializeApp } from "firebase/app";
import {
  getFirestore,
  doc,
  getDoc,
  setDoc,
  updateDoc,
  deleteDoc,
  collection
} from "firebase/firestore";

// Firebase Configuration (from user input)
const firebaseConfig = {
    apiKey: "AIzaSyD0eZXGBFrmYKUdK1-h6tTRJrEh3v-CSz0",
    authDomain: "poly9wanted.firebaseapp.com",
    projectId: "poly9wanted",
    storageBucket: "poly9wanted.firebasestorage.app",
    messagingSenderId: "425756247340",
    appId: "1:425756247340:web:120fbc4093f9cbf26bd889"
};

// Firebaseサービスの初期化
const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

// --- DOM Elements ---
const inputReceptionYear = document.getElementById('inputReceptionYear') as HTMLInputElement;
const inputReceptionNumber = document.getElementById('inputReceptionNumber') as HTMLInputElement;

const newRegistrationBtn = document.getElementById('newRegistrationBtn') as HTMLButtonElement;
const confirmModifyBtn = document.getElementById('confirmModifyBtn') as HTMLButtonElement;
const deleteBtn = document.getElementById('deleteBtn') as HTMLButtonElement;

const recruitmentYearField = document.getElementById('recruitmentYear') as HTMLInputElement;
const receptionNumberField = document.getElementById('receptionNumber') as HTMLInputElement;
const recruitingDepartmentsDiv = document.getElementById('recruitingDepartments') as HTMLDivElement;
const ownerNameField = document.getElementById('ownerName') as HTMLInputElement;
const ownerNameKanaField = document.getElementById('ownerNameKana') as HTMLInputElement;
const postalCodeField = document.getElementById('postalCode') as HTMLInputElement;
const prefectureField = document.getElementById('prefecture') as HTMLInputElement;
const addressField = document.getElementById('address') as HTMLInputElement;
const buildingNameField = document.getElementById('buildingName') as HTMLInputElement;
const phoneNumberField = document.getElementById('phoneNumber') as HTMLInputElement;
const capitalField = document.getElementById('capital') as HTMLInputElement;
const numberOfEmployeesField = document.getElementById('numberOfEmployees') as HTMLInputElement;
const companyTypeField = document.getElementById('companyType') as HTMLInputElement;
const industryClassificationField = document.getElementById('industryClassification') as HTMLInputElement;
const jobTypeField = document.getElementById('jobType') as HTMLInputElement;
const notesField = document.getElementById('notes') as HTMLTextAreaElement;
const urlField = document.getElementById('url') as HTMLInputElement;

const submitBtn = document.getElementById('submitBtn') as HTMLButtonElement;
const cancelBtn = document.getElementById('cancelBtn') as HTMLButtonElement;

const pdfViewer = document.getElementById('pdfViewer') as HTMLIFrameElement;

// --- Global Variables ---
let allDepartments: { id: string; name: string }[] = [];

// --- Type Definitions ---
interface JobPostingData {
    recruitmentYear: number;
    receptionNumber: number;
    recruitingDepartments?: number[];
    ownerName?: string;
    ownerNameKana?: string;
    postalCode?: string;
    prefecture?: string;
    address?: string;
    buildingName?: string;
    phoneNumber?: string;
    capital?: string;
    numberOfEmployees?: string;
    companyType?: string;
    industryClassification?: string;
    jobType?: string;
    notes?: string;
    url?: string;
}

// --- Helper Functions ---

/**
 * Firestoreから有効な部署リストを取得し、チェックボックスとして表示する
 */
async function loadDepartments() {
    recruitingDepartmentsDiv.innerHTML = ''; // Clear existing checkboxes
    try {
        const querySnapshot = await db.collection('departments')
            .where('isValid', '==', true)
            .orderBy('order')
            .get();

        allDepartments = querySnapshot.docs.map(doc => ({
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
    } catch (error) {
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
    const checkboxes = recruitingDepartmentsDiv.querySelectorAll('input[type="checkbox"]') as NodeListOf<HTMLInputElement>;
    checkboxes.forEach(cb => cb.checked = false);
}

/**
 * 指定された年度と受付番号に基づいてFirestoreからデータを読み込み、フォームに表示する
 */
async function loadJobPosting(year: number, number: number) {
    if (!year || !number) {
        alert("年度と受付番号を入力してください。");
        return;
    }

    const docId = `${year}-${number}`;
    try {
        const docRef = db.collection('jobPostings3').doc(docId);
        const doc = await docRef.get();

        if (doc.exists) {
            const data = doc.data() as JobPostingData;
            recruitmentYearField.value = String(data.recruitmentYear || '');
            receptionNumberField.value = String(data.receptionNumber || '');
            ownerNameField.value = data.ownerName || '';
            ownerNameKanaField.value = data.ownerNameKana || '';
            postalCodeField.value = data.postalCode || '';
            prefectureField.value = data.prefecture || '';
            addressField.value = data.address || '';
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
            const checkboxes = recruitingDepartmentsDiv.querySelectorAll('input[type="checkbox"]') as NodeListOf<HTMLInputElement>;
            checkboxes.forEach(cb => {
                cb.checked = checkedDepartments.includes(Number(cb.value)); // Assuming department IDs are numbers
            });

            updatePdfViewer(year, number);
        } else {
            alert("指定された求人票は見つかりませんでした。");
            clearForm();
            updatePdfViewer(0, 0); // Clear PDF viewer
        }
    } catch (error) {
        console.error("Error loading job posting:", error);
        alert("求人票の読み込み中にエラーが発生しました。");
        clearForm();
        updatePdfViewer(0, 0); // Clear PDF viewer
    }
}

/**
 * フォームの入力値から求人票データオブジェクトを生成する
 */
function getFormData(): Partial<JobPostingData> {
    const formData: Partial<JobPostingData> = {};

    // Only include fields that have values
    if (ownerNameField.value) formData.ownerName = ownerNameField.value;
    if (ownerNameKanaField.value) formData.ownerNameKana = ownerNameKanaField.value;
    if (postalCodeField.value) formData.postalCode = postalCodeField.value;
    if (prefectureField.value) formData.prefecture = prefectureField.value;
    if (addressField.value) formData.address = addressField.value;
    if (buildingNameField.value) formData.buildingName = buildingNameField.value;
    if (phoneNumberField.value) formData.phoneNumber = phoneNumberField.value;
    if (capitalField.value) formData.capital = capitalField.value;
    if (numberOfEmployeesField.value) formData.numberOfEmployees = numberOfEmployeesField.value;
    if (companyTypeField.value) formData.companyType = companyTypeField.value;
    if (industryClassificationField.value) formData.industryClassification = industryClassificationField.value;
    if (jobTypeField.value) formData.jobType = jobTypeField.value;
    if (notesField.value) formData.notes = notesField.value;
    if (urlField.value) formData.url = urlField.value;

    const selectedDepartments: number[] = [];
    recruitingDepartmentsDiv.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
        selectedDepartments.push(Number((cb as HTMLInputElement).value));
    });
    if (selectedDepartments.length > 0) formData.recruitingDepartments = selectedDepartments;

    return formData;
}

/**
 * PDFビューアを更新する
 */
function updatePdfViewer(year: number, number: number) {
    if (year && number) {
        pdfViewer.src = `https://poly9wanted.web.app/contents/pdf/${year}/${number}.pdf`;
    } else {
        pdfViewer.src = ''; // Clear PDF viewer
    }
}

/**
 * 初期値を設定する (次年度と最新の受付番号)
 */
async function setDefaultValues() {
    const currentYear = new Date().getFullYear();
    inputReceptionYear.value = String(currentYear + 1); // 次の年度

    try {
        // 最新の受付番号を取得
        const latestJobPostingQuery = await db.collection('jobPostings3')
            .where('recruitmentYear', '==', currentYear + 1)
            .orderBy('receptionNumber', 'desc')
            .limit(1)
            .get();

        if (!latestJobPostingQuery.empty) {
            const latestNumber = latestJobPostingQuery.docs[0].data().receptionNumber;
            inputReceptionNumber.value = String(latestNumber + 1);
        } else {
            inputReceptionNumber.value = '1'; // 該当年度のデータがなければ1から
        }
    } catch (error) {
        console.error("Error setting default reception number:", error);
        inputReceptionNumber.value = '1';
    }
}

// --- Event Handlers ---
// --- Event Handlers ---

newRegistrationBtn.addEventListener('click', () => {
    clearForm();
    setDefaultValues(); // 新規登録時は次年度と最新の受付番号をセット
    // 上段の値を中段の編集不可フィールドに反映
    recruitmentYearField.value = inputReceptionYear.value;
    receptionNumberField.value = inputReceptionNumber.value;
    updatePdfViewer(Number(inputReceptionYear.value), Number(inputReceptionNumber.value));
    alert("新規登録モードです。年度と受付番号を確認し、必要事項を入力してください。");
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
        alert("確認・修正モードです。データを修正し、「登録編集完了」を押してください。");
    } else {
        alert("指定された求人票は見つかりませんでした。");
    }
});

deleteBtn.addEventListener('click', async () => {
    const year = Number(inputReceptionYear.value);
    const number = Number(inputReceptionNumber.value);
    if (!year || !number) {
        alert("削除する求人票の年度と受付番号を入力してください。");
        return;
    }

    const docId = `${year}-${number}`;
    if (confirm(`求人票 (年度: ${year}, 受付番号: ${number}) を本当に削除しますか？`)) {
        try {
            await db.collection('jobPostings3').doc(docId).delete();
            alert("求人票を削除しました。");
            clearForm();
            setDefaultValues();
            updatePdfViewer(0, 0); // Clear PDF viewer
        } catch (error) {
            console.error("Error deleting job posting:", error);
            alert("求人票の削除中にエラーが発生しました。");
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

    const docId = `${year}-${number}`;
    const formData = getFormData();

    // recruitmentYearとreceptionNumberはdocIdから取得できるが、念のためデータにも含める
    formData.recruitmentYear = year;
    formData.receptionNumber = number;

    try {
        await db.collection('jobPostings3').doc(docId).set(formData, { merge: true });
        alert("求人票情報を登録・更新しました。");
        // 最新のデータを再読み込みしてフォームを更新
        await loadJobPosting(year, number);
        updatePdfViewer(year, number);
    } catch (error) {
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

// 上段の年度・受付番号が変更されたら、中段のフィールドとPDFビューアを更新
inputReceptionYear.addEventListener('change', () => {
    recruitmentYearField.value = inputReceptionYear.value;
    updatePdfViewer(Number(inputReceptionYear.value), Number(inputReceptionNumber.value));
});
inputReceptionNumber.addEventListener('change', () => {
    receptionNumberField.value = inputReceptionNumber.value;
    updatePdfViewer(Number(inputReceptionYear.value), Number(inputReceptionNumber.value));
});


// --- Initialization ---
document.addEventListener('DOMContentLoaded', async () => {
    await loadDepartments(); // 部署情報を最初に読み込む
    await setDefaultValues(); // 初期値を設定
    // 初期表示時も中段フィールドとPDFビューアを更新
    recruitmentYearField.value = inputReceptionYear.value;
    receptionNumberField.value = inputReceptionNumber.value;
    updatePdfViewer(Number(inputReceptionYear.value), Number(inputReceptionNumber.value));
});

