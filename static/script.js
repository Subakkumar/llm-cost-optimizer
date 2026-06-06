const dropZone   = document.getElementById('drop-zone');
const fileInput  = document.getElementById('file-input');
const selectBtn  = document.getElementById('select-btn');
const loadingDiv = document.getElementById('loading');
const resultsDiv = document.getElementById('results');

// ── File select ────────────────────────────────────────
selectBtn.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', e => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
});

fileInput.addEventListener('change', e => {
  if (e.target.files[0]) handleFile(e.target.files[0]);
});

// ── Upload + Analyze ───────────────────────────────────
function handleFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  loadingDiv.classList.remove('hidden');
  resultsDiv.classList.add('hidden');

  fetch('/api/upload', { method: 'POST', body: formData })
    .then(r => r.json())
    .then(data => {
      loadingDiv.classList.add('hidden');
      if (data.error) {
        alert('Error: ' + data.error);
        return;
      }
      renderResults(data);
    })
    .catch(err => {
      loadingDiv.classList.add('hidden');
      alert('Error: ' + err.message);
    });
}

// ── Render Results ─────────────────────────────────────
function renderResults(data) {
  const breakdown = data.breakdown || {};
  const models    = Object.keys(breakdown);
  const maxCost   = Math.max(...Object.values(breakdown), 0.0001);
  const topModel  = models.length
    ? models.reduce((a, b) => breakdown[a] > breakdown[b] ? a : b)
    : 'N/A';

  // KPIs
  document.getElementById('res-total').textContent =
    '$' + data.total_spent.toFixed(2);
  document.getElementById('res-provider').textContent =
    data.provider.toUpperCase();
  document.getElementById('res-models').textContent =
    models.length || '—';
  document.getElementById('res-top').textContent =
    topModel.length > 14 ? topModel.slice(0, 12) + '…' : topModel;

  // Provider badge
  document.getElementById('results-provider').textContent =
    data.provider.toUpperCase();

  // Breakdown bars
  const list = document.getElementById('breakdown-list');
  if (models.length === 0) {
    list.innerHTML = '<p style="color:#6b7280;font-size:.85rem">No model breakdown available.</p>';
  } else {
    list.innerHTML = Object.entries(breakdown)
      .sort((a, b) => b[1] - a[1])
      .map(([model, cost]) => {
        const pct = (cost / maxCost * 100).toFixed(1);
        return `
          <div class="breakdown-row">
            <span class="breakdown-model">${model}</span>
            <div class="breakdown-bar-wrap">
              <div class="breakdown-bar" style="width:${pct}%"></div>
            </div>
            <span class="breakdown-cost">$${cost.toFixed(2)}</span>
          </div>`;
      }).join('');
  }

  // Recommendations
  document.getElementById('recommendations-text').textContent =
    data.recommendations;

  resultsDiv.classList.remove('hidden');
  resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });

  // Refresh previous list
  refreshPrevious();
}

// ── Load Previous Analysis ─────────────────────────────
function loadAnalysis(id) {
  fetch('/api/analysis/' + id)
    .then(r => r.json())
    .then(data => {
      renderResults({
        total_spent:     data.total_spent,
        provider:        data.provider,
        breakdown:       data.breakdown || {},
        recommendations: data.analysis
      });
    })
    .catch(err => alert('Error: ' + err.message));
}

// ── Refresh Previous List ──────────────────────────────
function refreshPrevious() {
  fetch('/api/analyses')
    .then(r => r.json())
    .then(analyses => {
      const list = document.getElementById('previous-list');
      if (!analyses.length) {
        list.innerHTML = '<p class="empty-msg">No previous analyses yet.</p>';
        return;
      }
      list.innerHTML = analyses.map(a => `
        <div class="prev-item" onclick="loadAnalysis(${a.id})">
          <div class="prev-left">
            <span class="prev-file">${a.filename}</span>
            <span class="prev-provider">${a.provider}</span>
          </div>
          <div class="prev-right">
            <span class="prev-cost">$${parseFloat(a.total_spent).toFixed(2)}</span>
            <span class="prev-date">${new Date(a.created_at).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'})}</span>
          </div>
        </div>`).join('');
    });
}