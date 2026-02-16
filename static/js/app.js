// API Configuration
const API_BASE = 'http://localhost:5002/api';

// DOM Elements
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const uploadProgress = document.getElementById('uploadProgress');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const filePreview = document.getElementById('filePreview');
const resultsGrid = document.getElementById('resultsGrid');
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const exportJsonBtn = document.getElementById('exportJsonBtn');
const exportCsvBtn = document.getElementById('exportCsvBtn');
const refreshBtn = document.getElementById('refreshBtn');
const recordModal = document.getElementById('recordModal');
const modalClose = document.getElementById('modalClose');
const modalBody = document.getElementById('modalBody');
const modalTitle = document.getElementById('modalTitle');
const filterPills = document.querySelectorAll('.pill');
const toastContainer = document.getElementById('toastContainer');

// State
let allRecords = [];
let currentFilter = 'all';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    loadRecords();
    loadStats();
});

function initEventListeners() {
    // Drag and Drop
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('dragleave', handleDragLeave);
    dropZone.addEventListener('drop', handleDrop);

    // File Input
    browseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });
    fileInput.addEventListener('change', handleFileSelect);

    // Search
    searchBtn.addEventListener('click', handleSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });

    // Export
    exportJsonBtn.addEventListener('click', () => exportRecords('json'));
    exportCsvBtn.addEventListener('click', () => exportRecords('csv'));

    // Refresh
    refreshBtn.addEventListener('click', () => {
        loadRecords();
        loadStats();
        showToast('Records refreshed', 'success');
    });

    // Filter Pills
    filterPills.forEach(pill => {
        pill.addEventListener('click', () => {
            filterPills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            currentFilter = pill.dataset.type;
            filterRecords();
        });
    });

    // Modal
    modalClose.addEventListener('click', closeModal);
    recordModal.addEventListener('click', (e) => {
        if (e.target === recordModal) closeModal();
    });
}

// Drag and Drop Handlers
function handleDragOver(e) {
    e.preventDefault();
    dropZone.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    dropZone.classList.remove('drag-over');

    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
}

function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    handleFiles(files);
}

// File Handling
function handleFiles(files) {
    if (files.length === 0) return;

    // Show preview
    showFilePreview(files);

    // Upload files
    if (files.length === 1) {
        uploadSingle(files[0]);
    } else {
        uploadBatch(files);
    }
}

function showFilePreview(files) {
    filePreview.innerHTML = '';
    files.forEach(file => {
        const item = document.createElement('div');
        item.className = 'file-preview-item';

        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);

        const name = document.createElement('p');
        name.textContent = file.name;

        item.appendChild(img);
        item.appendChild(name);
        filePreview.appendChild(item);
    });
}

// Upload Functions
async function uploadSingle(file) {
    const formData = new FormData();
    formData.append('file', file);

    showProgress('Uploading and processing...');

    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            showToast(`Successfully processed: ${file.name}`, 'success');
            loadRecords();
            loadStats();
            filePreview.innerHTML = '';
            fileInput.value = '';
        } else {
            showToast(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showToast(`Upload failed: ${error.message}`, 'error');
    } finally {
        hideProgress();
    }
}

async function uploadBatch(files) {
    const formData = new FormData();
    files.forEach(file => {
        formData.append('files[]', file);
    });

    showProgress(`Processing ${files.length} files...`);

    try {
        const response = await fetch(`${API_BASE}/batch-upload`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            const successCount = result.results.filter(r => r.success).length;
            showToast(`Processed ${successCount} of ${result.total} files`, 'success');
            loadRecords();
            loadStats();
            filePreview.innerHTML = '';
            fileInput.value = '';
        } else {
            showToast(`Batch upload failed: ${result.error}`, 'error');
        }
    } catch (error) {
        showToast(`Upload failed: ${error.message}`, 'error');
    } finally {
        hideProgress();
    }
}

// Progress
function showProgress(message) {
    uploadProgress.style.display = 'block';
    progressText.textContent = message;
    progressFill.style.width = '100%';
}

function hideProgress() {
    setTimeout(() => {
        uploadProgress.style.display = 'none';
        progressFill.style.width = '0%';
    }, 500);
}

// Load Records
async function loadRecords() {
    try {
        const response = await fetch(`${API_BASE}/records`);
        const result = await response.json();

        if (result.success) {
            allRecords = result.records;
            filterRecords();
        }
    } catch (error) {
        console.error('Error loading records:', error);
        showToast('Failed to load records', 'error');
    }
}

// Filter Records
function filterRecords() {
    let filtered = allRecords;

    if (currentFilter !== 'all') {
        filtered = allRecords.filter(r => r.document_type === currentFilter);
    }

    displayRecords(filtered);
}

// Display Records
function displayRecords(records) {
    if (records.length === 0) {
        resultsGrid.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <h3>No Records Found</h3>
                <p>Upload documents to get started</p>
            </div>
        `;
        return;
    }

    resultsGrid.innerHTML = records.map(record => `
        <div class="record-card" onclick="showRecordDetails(${record.id})">
            <div class="record-header">
                <div>
                    <div class="record-title">${record.filename}</div>
                    <div class="record-date">${formatDate(record.upload_date)}</div>
                </div>
                <span class="record-type">${record.document_type || 'unknown'}</span>
            </div>
            <div class="record-text">${record.raw_text || 'No text extracted'}</div>
            <div class="record-footer">
                <span class="confidence-badge">
                    ${Math.round((record.confidence_score || 0) * 100)}% confidence
                </span>
            </div>
        </div>
    `).join('');
}

// Show Record Details
async function showRecordDetails(recordId) {
    try {
        const response = await fetch(`${API_BASE}/records/${recordId}`);
        const result = await response.json();

        if (result.success) {
            const record = result.record;

            modalTitle.textContent = record.filename;
            modalBody.innerHTML = `
                <div class="detail-section">
                    <h3>📄 Basic Information</h3>
                    <div class="detail-row">
                        <span class="detail-label">Filename:</span>
                        <span class="detail-value">${record.filename}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Upload Date:</span>
                        <span class="detail-value">${formatDate(record.upload_date)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Document Type:</span>
                        <span class="detail-value">${record.document_type || 'Unknown'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Confidence:</span>
                        <span class="detail-value">${Math.round((record.confidence_score || 0) * 100)}%</span>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h3>📝 Extracted Text</h3>
                    <div style="background: var(--bg-tertiary); padding: 1rem; border-radius: 0.75rem; white-space: pre-wrap; line-height: 1.8;">
                        ${record.raw_text || 'No text extracted'}
                    </div>
                </div>
                
                ${record.structured_data ? `
                    <div class="detail-section">
                        <h3>🏷️ Extracted Entities</h3>
                        ${renderEntities(record.structured_data)}
                    </div>
                ` : ''}
                
                ${record.ai_analysis ? `
                    <div class="detail-section">
                        <h3>🤖 AI Analysis</h3>
                        <div style="background: var(--bg-tertiary); padding: 1rem; border-radius: 0.75rem;">
                            <pre style="white-space: pre-wrap; font-family: inherit;">${JSON.stringify(record.ai_analysis, null, 2)}</pre>
                        </div>
                    </div>
                ` : ''}
            `;

            recordModal.style.display = 'flex';
        }
    } catch (error) {
        showToast('Failed to load record details', 'error');
    }
}

function renderEntities(entities) {
    if (!entities || typeof entities !== 'object') return '<p>No entities extracted</p>';

    let html = '';
    for (const [key, values] of Object.entries(entities)) {
        if (Array.isArray(values) && values.length > 0) {
            html += `
                <div style="margin-bottom: 1rem;">
                    <strong style="text-transform: capitalize; color: var(--text-secondary);">${key.replace(/_/g, ' ')}:</strong>
                    <div class="entity-list" style="margin-top: 0.5rem;">
                        ${values.map(v => `<span class="entity-tag">${v}</span>`).join('')}
                    </div>
                </div>
            `;
        }
    }

    return html || '<p>No entities extracted</p>';
}

function closeModal() {
    recordModal.style.display = 'none';
}

// Search
async function handleSearch() {
    const query = searchInput.value.trim();

    if (!query) {
        loadRecords();
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/records?search=${encodeURIComponent(query)}`);
        const result = await response.json();

        if (result.success) {
            allRecords = result.records;
            filterRecords();
        }
    } catch (error) {
        showToast('Search failed', 'error');
    }
}

// Export
function exportRecords(format) {
    window.open(`${API_BASE}/export?format=${format}`, '_blank');
    showToast(`Exporting as ${format.toUpperCase()}...`, 'success');
}

// Load Stats
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const result = await response.json();

        if (result.success) {
            const stats = result.stats;
            document.getElementById('totalRecords').textContent = stats.total_records || 0;
            document.getElementById('avgConfidence').textContent =
                `${Math.round((stats.average_confidence || 0) * 100)}%`;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Toast Notifications
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Utility Functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Make function available globally
window.showRecordDetails = showRecordDetails;
