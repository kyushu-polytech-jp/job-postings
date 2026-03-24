// Firebase SDKのインポート
import { initializeApp } from 'firebase/app';
import {
  getFirestore,
  collection,
  query,
  where,
  getDocs,
  DocumentData,
  Query,
  limit,
  orderBy,
  startAfter,
  QueryConstraint
} from 'firebase/firestore';

// Firebaseプロジェクトの設定
const firebaseConfig = {
  apiKey: "AIzaSyD0eZXGBFrmYKUdK1-h6tTRJrEh3v-CSz0",
  authDomain: "poly9wanted.firebaseapp.com",
  projectId: "poly9wanted",
  storageBucket: "poly9wanted.firebasestorage.app",
  messagingSenderId: "425756247340",
  appId: "1:425756247340:web:120fbc4093f9cbf26bd889"
};

// Firebaseを初期化
const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

// --- DOM要素 ---
const yearSelect = document.getElementById('yearSelect') as HTMLSelectElement;
const departmentSelect = document.getElementById('departmentSelect') as HTMLSelectElement;
const ownerNameKanaInput = document.getElementById('ownerNameKanaInput') as HTMLInputElement;
const prefectureInput = document.getElementById('prefectureInput') as HTMLInputElement;
const searchForm = document.getElementById('searchForm') as HTMLFormElement;
const resultsTableBody = document.getElementById('resultsTableBody') as HTMLTableSectionElement;
const moreInfoDiv = document.getElementById('moreInfo') as HTMLDivElement;
const pdfDisplayArea = document.getElementById('pdfDisplayArea') as HTMLDivElement;

const prevPageButton = document.getElementById('prevPageButton') as HTMLButtonElement;
const nextPageButton = document.getElementById('nextPageButton') as HTMLButtonElement;
const pageInfoSpan = document.getElementById('pageInfo') as HTMLSpanElement;

// --- 定数・状態 ---
const PAGE_SIZE = 10;
const SERVER_BATCH_SIZE = 50;

let currentBaseQuery: Query<DocumentData> | null = null;
let scanStartMarkers: (DocumentData | null)[] = [];
let currentPageIndex = 0;
let reachedEnd = false;
let totalCount = 0;
let totalCountKnown = false;

// --- カナ正規化 ---
function toKatakana(src: string): string {
  return src.replace(/[\u3041-\u3096]/g, c =>
    String.fromCharCode(c.charCodeAt(0) + 0x60)
  );
}

function normalizeKana(input: string): string {
  if (!input) return '';
  let s = input.normalize('NFKC');
  s = toKatakana(s);
  s = s.replace(/\s+/g, '');
  return s;
}

// --- 科名ロード（クライアント側でソートに変更して安全化） ---
async function loadDepartments() {
  try {
    const deptSnap = await getDocs(
      query(collection(db, 'departments'), where('isValid', '==', true))
    );

    const items: { id: string; name: string; order: number }[] = [];
    deptSnap.forEach(doc => {
      const d = doc.data() as any;
      items.push({
        id: doc.id,
        name: d.name ?? '',
        order: typeof d.order === 'number' ? d.order : Number.MAX_SAFE_INTEGER
      });
    });

    items.sort((a, b) => a.order - b.order);

    departmentSelect.innerHTML = '<option value="">科を選択</option>';
    for (const it of items) {
      const opt = document.createElement('option');
      opt.value = it.id;
      opt.textContent = it.name;
      departmentSelect.appendChild(opt);
    }
  } catch (e) {
    console.error('科リスト取得エラー:', e);
    departmentSelect.innerHTML = '<option value="">科を選択（取得失敗）</option>';
  }
}

// --- 検索 ---
async function searchJobPostings(direction: 'initial' | 'next' | 'prev' = 'initial') {
  // 画面初期化（毎回）
  resultsTableBody.innerHTML = '';
  pdfDisplayArea.innerHTML = '';
  pageInfoSpan.textContent = '';

  const kanaNeedle = normalizeKana(ownerNameKanaInput.value.trim());

  // --- 初回検索 ---
  if (direction === 'initial') {
    const constraints: QueryConstraint[] = [];

    if (yearSelect.value) {
      constraints.push(where('recruitmentYear', '==', Number(yearSelect.value)));
    }

    if (departmentSelect.value) {
      constraints.push(
        where(
          'recruitingDepartments',
          'array-contains',
          isNaN(Number(departmentSelect.value))
            ? departmentSelect.value
            : Number(departmentSelect.value)
        )
      );
    }

    let hasPrefRange = false;
    if (prefectureInput.value.trim()) {
      const p = prefectureInput.value.trim().toLowerCase();
      constraints.push(where('prefecture', '>=', p));
      constraints.push(where('prefecture', '<=', p + '\uf8ff'));
      hasPrefRange = true;
    }

    let base: Query<DocumentData> = collection(db, 'jobPostings');
    if (constraints.length) base = query(base, ...constraints);

    // ★ prefecture の範囲条件がある場合は orderBy('prefecture') のみ
    currentBaseQuery = hasPrefRange
      ? query(base, orderBy('prefecture', 'asc'))
      : query(base, orderBy('__name__', 'asc'));

    // 状態初期化
    scanStartMarkers = [null];        // ページ1の開始は null
    currentPageIndex = 0;             // これから 1 にする
    reachedEnd = false;
    totalCountKnown = false;
    totalCount = 0;
    moreInfoDiv.textContent = '件数集計中…';

    // バックグラウンドで件数集計（同じ currentBaseQuery で全走査）
    (async () => {
      try {
        let count = 0;
        let last: DocumentData | null = null;
        while (true) {
          const batchQuery: Query<DocumentData> = last
            ? query(currentBaseQuery as Query<DocumentData>, startAfter(last), limit(SERVER_BATCH_SIZE))
            : query(currentBaseQuery as Query<DocumentData>, limit(SERVER_BATCH_SIZE));

          const snapshot = await getDocs(batchQuery);
          if (snapshot.empty) break;

          for (const d of snapshot.docs) {
            const kana = normalizeKana((d.data() as any).ownerNameKana || '');
            if (kana.includes(kanaNeedle)) count++;
          }
          last = snapshot.docs[snapshot.docs.length - 1];
        }
        totalCount = count;
        totalCountKnown = true;
        moreInfoDiv.textContent = `合計 ${totalCount} 件`;
      } catch (err) {
        console.error('合計件数集計でエラー:', err);
        moreInfoDiv.textContent = '合計: 取得に失敗';
      }
    })();
  }

  if (!currentBaseQuery) return;

  // --- ページ開始位置 ---
  let start: DocumentData | null = null;
  if (direction === 'next') start = scanStartMarkers[currentPageIndex] ?? null;
  if (direction === 'prev') start = scanStartMarkers[Math.max(0, currentPageIndex - 2)] ?? null;

  // ★毎回リセット（末尾残留フラグを防止）
  reachedEnd = false;

  const results: any[] = [];
  let lastScanned: DocumentData | null = start;

  while (results.length < PAGE_SIZE) {
    const pageBatchQuery: Query<DocumentData> = lastScanned
      ? query(currentBaseQuery as Query<DocumentData>, startAfter(lastScanned), limit(SERVER_BATCH_SIZE))
      : query(currentBaseQuery as Query<DocumentData>, limit(SERVER_BATCH_SIZE));

    const pageSnapshot = await getDocs(pageBatchQuery);
    if (pageSnapshot.empty) {
      reachedEnd = true;
      break;
    }

    // ★  このバッチで「最後に検査した」スナップショットを保持
    let lastInspected: DocumentData | null = null;

    for (const d of pageSnapshot.docs) {
      lastInspected = d; // ← ここを常に更新（検査が進んだ位置）
      const data = d.data() as any;
      const kana = normalizeKana(data.ownerNameKana || '');
      if (kana.includes(kanaNeedle)) {
        results.push(data);
        if (results.length >= PAGE_SIZE) break; // ページ分たまったらバッチ途中で抜ける
      }
    }

    // ★  次ページの開始点は「最後に検査した位置」から
    lastScanned = lastInspected ?? pageSnapshot.docs[pageSnapshot.docs.length - 1];

    // ページ分たまっていたら while を抜ける
    if (results.length >= PAGE_SIZE) break;
  }

  // --- 表示 ---
  if (results.length === 0) {
    const tr = resultsTableBody.insertRow();
    const td = tr.insertCell();
    td.colSpan = 5;
    td.textContent = '該当する求人情報はありません。';
  } else {
    results.forEach(job => {
      const row = resultsTableBody.insertRow();
      row.innerHTML = `
        <td>${job.ownerName || ''}</td>
        <td>${job.jobType || ''}</td>
        <td>${job.numberOfEmployees || ''}</td>
        <td>${job.capital || ''}</td>
        <td>${job.city || ''}</td>
      `;
      row.style.cursor = 'pointer';
      row.onclick = () => displayPdf(job.recruitmentYear, job.receptionNumber);
    });
  }

  // --- ページ状態更新 ---
  if (direction === 'initial') currentPageIndex = 1;
  if (direction === 'next')    currentPageIndex++;
  if (direction === 'prev')    currentPageIndex--;

  // 次ページの開始点として必ず記録（null で塗りつぶさない）
  if (lastScanned) {
    scanStartMarkers[currentPageIndex] = lastScanned;
  } else if (scanStartMarkers[currentPageIndex] === undefined) {
    scanStartMarkers[currentPageIndex] = start ?? null;
  }

  // --- ページングボタン ---
  prevPageButton.disabled = currentPageIndex <= 1;

  const hasNextStart =
    scanStartMarkers[currentPageIndex] !== undefined &&
    scanStartMarkers[currentPageIndex] !== null;

  // 末尾かつ今回 PAGE_SIZE 未満、または次ページ開始点が不明なら無効
  nextPageButton.disabled = (reachedEnd && results.length < PAGE_SIZE) || !hasNextStart;

  // --- ページ情報 ---
  pageInfoSpan.textContent = totalCountKnown
    ? `ページ ${currentPageIndex} / ${Math.max(1, Math.ceil(totalCount / PAGE_SIZE))}`
    : `ページ ${currentPageIndex}`;
}

// --- PDF表示（DOM APIで安全に描画） ---

async function displayPdf(year: number, reception: string | number) {
  // 1) ファイル名（ゼロ埋めなし）の生成
  //    - number ならそのまま
  //    - string なら parseInt で数値化（頭の0を落とす）
  //    - もし NaN なら、先頭の 0 を取り除く（全部0なら "0" にする）フォールバック
  let numericReception: number | null = null;
  if (typeof reception === 'number') {
    numericReception = reception;
  } else {
    const n = parseInt(reception, 10);
    if (!Number.isNaN(n)) {
      numericReception = n;
    } else {
      numericReception = 0;// 存在しないファイル番号
    }
  }
  const fileName = String(numericReception).trim();
  const pdfPath = `/contents/pdf/${year}/${fileName}.pdf`;

  // 見出し要素を生成
  pdfDisplayArea.innerHTML = '';
  const h3 = document.createElement('h3');
  h3.textContent = `PDFプレビュー: ${fileName}.pdf (${year}年度)`;
  pdfDisplayArea.appendChild(h3);

  // コンテナ
  const pdfContentDiv = document.createElement('div');
  pdfContentDiv.id = 'pdfContent';
  pdfContentDiv.textContent = '読み込み中...';
  pdfDisplayArea.appendChild(pdfContentDiv);

  try {
    const res = await fetch(pdfPath, { method: 'HEAD' });
    // iframe
    const iframe = document.createElement('iframe');
    iframe.src = pdfPath;
    iframe.width = '100%';
    iframe.height = '600';
    iframe.style.border = 'none';

    pdfContentDiv.textContent = '';
    pdfContentDiv.appendChild(iframe);

    if (!res.ok) {
      const p = document.createElement('p');
      p.style.color = 'red';
      p.textContent = `PDFファイルが見つかりません: ${fileName}.pdf`;
      pdfContentDiv.appendChild(p);
    }
  } catch (e) {
    console.warn('PDF HEAD エラー（iframe は試行）:', e);
    const iframe = document.createElement('iframe');
    iframe.src = pdfPath;
    iframe.width = '100%';
    iframe.height = '600';
    iframe.style.border = 'none';

    pdfContentDiv.textContent = '';
    pdfContentDiv.appendChild(iframe);
  }
}

// --- イベント（※これが無いと何も動きません） ---
searchForm.addEventListener('submit', e => {
  e.preventDefault();
  searchJobPostings('initial');
});

prevPageButton.addEventListener('click', () => {
  if (currentPageIndex > 1) searchJobPostings('prev');
});

nextPageButton.addEventListener('click', () => {
  searchJobPostings('next');
});

// 初期ロード：科リスト読込
document.addEventListener('DOMContentLoaded', () => {
  loadDepartments().catch(err => console.error('初期ロードで科読込エラー:', err));
});
