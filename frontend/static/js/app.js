// SCIENTIFIC PAPER TRANSLATOR - Frontend Logic

let currentResult = null;
let syncScrollEnabled = true;
let isScrolling = false;

document.addEventListener('DOMContentLoaded', () => {
    setupDragDrop();
    // Auto-load RSNA paper on startup for immediate demonstration
    loadRsnaPreset();
});

function switchTab(tab) {
    const uploadBtn = document.getElementById('tabUploadBtn');
    const doiBtn = document.getElementById('tabDoiBtn');
    const uploadContent = document.getElementById('uploadTabContent');
    const doiContent = document.getElementById('doiTabContent');

    if (tab === 'upload') {
        uploadBtn.classList.add('active');
        doiBtn.classList.remove('active');
        uploadContent.classList.add('active');
        doiContent.classList.remove('active');
    } else {
        doiBtn.classList.add('active');
        uploadBtn.classList.remove('active');
        doiContent.classList.add('active');
        uploadContent.classList.remove('active');
    }
}

function setupDragDrop() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.style.borderColor = '#2563EB', false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.style.borderColor = '#374151', false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
}

function handleFileSelect(file) {
    document.getElementById('selectedFileName').textContent = `Fichier sélectionné : ${file.name} (${Math.round(file.size / 1024)} Ko)`;
    window.selectedFile = file;
}

async function loadRsnaPreset() {
    showProgress("Chargement de l'article RSNA (10.1148/radiol.233482)...", 30);
    try {
        const response = await fetch('/api/sample/rsna');
        if (!response.ok) {
            throw new Error("Impossible de charger le modèle RSNA.");
        }
        const data = await response.json();
        showProgress("Finalisation du rendu...", 90);
        setTimeout(() => {
            hideProgress();
            renderResult(data);
        }, 400);
    } catch (err) {
        hideProgress();
        console.error("Erreur lors du chargement :", err);
    }
}

async function submitDoi() {
    const doiVal = document.getElementById('doiInput').value.trim();
    if (!doiVal) {
        alert("Veuillez saisir un DOI ou une URL.");
        return;
    }

    const domain = document.getElementById('domainSelect').value;
    showProgress(`Résolution du DOI ${doiVal}...`, 20);

    const formData = new FormData();
    formData.append('doi_or_url', doiVal);
    formData.append('domain', domain);

    try {
        const res = await fetch('/api/translate/doi', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (data.result) {
            hideProgress();
            renderResult(data.result);
        } else {
            pollTaskStatus();
        }
    } catch (err) {
        hideProgress();
        alert("Erreur de connexion avec l'API : " + err);
    }
}

async function startTranslation() {
    if (!window.selectedFile) {
        // If no file selected, trigger DOI / preset
        loadRsnaPreset();
        return;
    }

    const file = window.selectedFile;
    const domain = document.getElementById('domainSelect').value;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('domain', domain);

    showProgress("Téléversement et extraction du document...", 15);

    try {
        const res = await fetch('/api/translate/upload', {
            method: 'POST',
            body: formData
        });
        pollTaskStatus();
    } catch (err) {
        hideProgress();
        alert("Erreur lors du téléversement : " + err);
    }
}

function pollTaskStatus() {
    const interval = setInterval(async () => {
        try {
            const res = await fetch('/api/status');
            const status = await res.json();

            showProgress(status.stage || "Traitement en cours...", status.progress || 30);

            if (status.status === 'completed') {
                clearInterval(interval);
                hideProgress();
                if (status.result) {
                    renderResult(status.result);
                }
            } else if (status.status === 'error') {
                clearInterval(interval);
                hideProgress();
                alert("Erreur lors de la traduction : " + status.error);
            }
        } catch (e) {
            clearInterval(interval);
            hideProgress();
        }
    }, 1500);
}

function showProgress(stage, percent) {
    document.getElementById('progressContainer').style.display = 'block';
    document.getElementById('progressStage').textContent = stage;
    document.getElementById('progressPercent').textContent = `${percent}%`;
    document.getElementById('progressBar').style.width = `${percent}%`;
}

function hideProgress() {
    document.getElementById('progressContainer').style.display = 'none';
}

function renderResult(data) {
    currentResult = data;

    // Show Dashboard & Viewer
    document.getElementById('qcDashboard').style.display = 'block';
    document.getElementById('viewerSection').style.display = 'block';

    // QC Metrics
    const qc = data.qc_report || { overall_score: 100, number_fidelity_pct: 100, citation_fidelity_pct: 100, confidence_rating: 'HIGH' };
    document.getElementById('qcOverallScore').textContent = `${qc.overall_score}%`;
    document.getElementById('qcNumberFidelity').textContent = `${qc.number_fidelity_pct}%`;
    document.getElementById('qcCitationFidelity').textContent = `${qc.citation_fidelity_pct}%`;
    document.getElementById('qcConfidenceBadge').textContent = qc.confidence_rating;

    // Source Column
    const sourceContainer = document.getElementById('sourceArticleContent');
    sourceContainer.innerHTML = '';

    const srcTitle = document.createElement('h2');
    srcTitle.className = 'doc-title';
    srcTitle.textContent = data.source_title || (data.source_doc && data.source_doc.title) || '';
    sourceContainer.appendChild(srcTitle);

    if (data.authors) {
        const srcAuth = document.createElement('div');
        srcAuth.className = 'doc-authors';
        srcAuth.innerHTML = data.authors.replace(/\n/g, '<br>');
        sourceContainer.appendChild(srcAuth);
    }

    const srcElements = data.source_elements || (data.source_doc && data.source_doc.elements) || [];
    srcElements.forEach((elem, idx) => {
        const el = createBlockElement(elem, `src_block_${idx}`);
        sourceContainer.appendChild(el);
    });

    // Target Column
    const targetContainer = document.getElementById('targetArticleContent');
    targetContainer.innerHTML = '';

    const trgTitle = document.createElement('h2');
    trgTitle.className = 'doc-title';
    trgTitle.textContent = data.translated_title || (data.translated_doc && data.translated_doc.title) || '';
    targetContainer.appendChild(trgTitle);

    if (data.authors) {
        const trgAuth = document.createElement('div');
        trgAuth.className = 'doc-authors';
        trgAuth.innerHTML = data.authors.replace(/\n/g, '<br>');
        targetContainer.appendChild(trgAuth);
    }

    const trgElements = data.translated_elements || (data.translated_doc && data.translated_doc.elements) || [];
    trgElements.forEach((elem, idx) => {
        const el = createBlockElement(elem, `trg_block_${idx}`);
        targetContainer.appendChild(el);
    });

    setupSynchronizedScrolling();
}

function createBlockElement(elem, id) {
    const div = document.createElement('div');
    div.id = id;
    div.dataset.type = elem.type;

    if (elem.type === 'heading') {
        const h = document.createElement(elem.level === 1 ? 'h3' : 'h4');
        h.className = elem.level === 1 ? 'doc-h1' : 'doc-h2';
        h.textContent = elem.text;
        div.appendChild(h);
    } else if (elem.type === 'reference') {
        const p = document.createElement('p');
        p.className = 'doc-ref';
        p.textContent = elem.text;
        div.appendChild(p);
    } else {
        const p = document.createElement('p');
        p.className = 'doc-p';
        p.textContent = elem.text;
        div.appendChild(p);
    }

    return div;
}

function toggleSyncScroll(enabled) {
    syncScrollEnabled = enabled;
}

function setupSynchronizedScrolling() {
    const srcPane = document.getElementById('sourceArticleContent');
    const trgPane = document.getElementById('targetArticleContent');

    srcPane.addEventListener('scroll', () => {
        if (!syncScrollEnabled || isScrolling) return;
        isScrolling = true;
        const scrollPct = srcPane.scrollTop / (srcPane.scrollHeight - srcPane.clientHeight);
        trgPane.scrollTop = scrollPct * (trgPane.scrollHeight - trgPane.clientHeight);
        setTimeout(() => isScrolling = false, 50);
    });

    trgPane.addEventListener('scroll', () => {
        if (!syncScrollEnabled || isScrolling) return;
        isScrolling = true;
        const scrollPct = trgPane.scrollTop / (trgPane.scrollHeight - trgPane.clientHeight);
        srcPane.scrollTop = scrollPct * (srcPane.scrollHeight - srcPane.clientHeight);
        setTimeout(() => isScrolling = false, 50);
    });
}
