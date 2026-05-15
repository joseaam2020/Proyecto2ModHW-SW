// reports.js
// Lógica de la página /reportes:
//   - Tabs (Visualizar PDF / Reportes individuales)
//   - Generación y descarga del PDF
//   - Listado de reportes individuales
//   - Modal con el detalle de un reporte

(function () {
  'use strict';

  // ----- Refs -----------------------------------------------------------
  const downloadBtn   = document.getElementById('download-pdf-btn');
  const downloadHint  = document.getElementById('download-hint');
  const tabPdf        = document.getElementById('tab-pdf');
  const tabList       = document.getElementById('tab-list');
  const panelPdf      = document.getElementById('panel-pdf');
  const panelList     = document.getElementById('panel-list');
  const pdfIframe     = document.getElementById('pdf-iframe');
  const pdfEmpty      = document.getElementById('pdf-empty-state');
  const banner        = document.getElementById('reports-banner');

  const listScroll    = document.getElementById('reports-list-scroll');
  const listEmpty     = document.getElementById('reports-list-empty');
  const listCount     = document.getElementById('reports-list-count');

  const modalBackdrop = document.getElementById('report-modal-backdrop');
  const modalTitle    = document.getElementById('report-modal-title');
  const modalBody     = document.getElementById('report-modal-body');
  const modalClose    = document.getElementById('report-modal-close');

  // ----- Estado ---------------------------------------------------------
  let pdfBlobUrl = null;   // URL.createObjectURL del último PDF generado
  let pdfReady   = false;
  let reportsLoaded = false;

  // ----- Banner ---------------------------------------------------------
  function showBanner(message, kind) {
    banner.textContent = message;
    banner.className = 'reports-banner ' + (kind || 'info');
    banner.style.display = 'block';
  }
  function hideBanner() {
    banner.style.display = 'none';
    banner.textContent = '';
  }

  // ----- Tabs -----------------------------------------------------------
  function switchTab(name) {
    if (name === 'pdf') {
      tabPdf.classList.add('active');
      tabList.classList.remove('active');
      panelPdf.style.display  = 'flex';
      panelList.style.display = 'none';
    } else {
      tabList.classList.add('active');
      tabPdf.classList.remove('active');
      panelList.style.display = 'flex';
      panelPdf.style.display  = 'none';
      if (!reportsLoaded) {
        loadReportsList();
      }
    }
  }
  tabPdf.addEventListener('click',  () => switchTab('pdf'));
  tabList.addEventListener('click', () => switchTab('list'));

  // ----- Generar / descargar PDF ---------------------------------------
  // Estrategia: POST a /informe?inline=1 con fetch, recibir el blob,
  // crearle una URL local y:
  //   - cargarla en el iframe (visualización)
  //   - disparar la descarga (clic adicional desde la misma URL)
  async function generatePdf({ download = true } = {}) {
    hideBanner();
    if (downloadBtn.classList.contains('is-loading')) return;
    downloadBtn.classList.add('is-loading');
    downloadBtn.disabled = true;

    try {
      const response = await fetch('/informe?inline=1', { method: 'POST' });

      if (!response.ok) {
        // El backend redirige a /reportes?error=... cuando hay problema
        const url = new URL(response.url);
        const errorKey = url.searchParams.get('error');
        if (errorKey === 'no_reports') {
          showBanner(
            'No hay reportes disponibles. Ejecuta una simulación primero.',
            'error'
          );
        } else if (errorKey === 'pdf_error') {
          showBanner(
            'Ocurrió un error al generar el PDF. Revisa los logs del servidor.',
            'error'
          );
        } else {
          showBanner('No se pudo generar el informe (HTTP ' + response.status + ').', 'error');
        }
        return;
      }

      const blob = await response.blob();
      if (pdfBlobUrl) URL.revokeObjectURL(pdfBlobUrl);
      pdfBlobUrl = URL.createObjectURL(blob);
      pdfReady = true;

      // Mostrar en el iframe
      pdfIframe.src = pdfBlobUrl;
      pdfIframe.style.display = 'block';
      pdfEmpty.style.display = 'none';

      // Descargar automáticamente
      if (download) {
        triggerDownload(pdfBlobUrl, 'informe_general.pdf');
      }

      showBanner('Informe generado correctamente.', 'success');
      // Auto-ocultar el banner de éxito tras 3s
      setTimeout(() => {
        if (banner.classList.contains('success')) hideBanner();
      }, 3000);

      // Cambiar al tab del PDF si el usuario está en otro
      switchTab('pdf');

    } catch (err) {
      console.error(err);
      showBanner('Error de red al generar el informe: ' + err.message, 'error');
    } finally {
      downloadBtn.classList.remove('is-loading');
      downloadBtn.disabled = false;
    }
  }

  function triggerDownload(url, filename) {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  downloadBtn.addEventListener('click', () => generatePdf({ download: true }));

  // ----- Listado de reportes individuales -------------------------------
  async function loadReportsList() {
    try {
      const res = await fetch('/api/reports');
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      renderReportsList(data.reports || []);
      reportsLoaded = true;
    } catch (err) {
      console.error(err);
      listScroll.innerHTML =
        '<div class="reports-list-empty">No se pudo cargar la lista de reportes.</div>';
    }
  }

  function renderReportsList(reports) {
    listCount.textContent = reports.length + (reports.length === 1 ? ' reporte' : ' reportes');

    if (!reports.length) {
      listScroll.innerHTML =
        '<div class="reports-list-empty">No hay reportes disponibles. Ejecuta una simulación primero.</div>';
      return;
    }

    listScroll.innerHTML = '';
    reports.forEach(r => listScroll.appendChild(createReportCard(r)));
  }

  function createReportCard(report) {
    const card = document.createElement('div');
    card.className = 'report-card';
    card.setAttribute('role', 'button');
    card.setAttribute('tabindex', '0');

    const tick = document.createElement('div');
    tick.className = 'report-card-tick';
    tick.textContent = 'Tick ' + (report.tick !== null ? report.tick : '—');

    const meta = document.createElement('div');
    meta.className = 'report-card-meta';
    meta.textContent = report.filename;

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'report-card-action';
    btn.textContent = 'Ver detalle';

    card.appendChild(tick);
    card.appendChild(meta);
    card.appendChild(btn);

    const open = () => openReportModal(report);
    btn.addEventListener('click', e => { e.stopPropagation(); open(); });
    card.addEventListener('click', open);
    card.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); }
    });

    return card;
  }

  // ----- Modal de detalle -----------------------------------------------
  async function openReportModal(report) {
    modalTitle.textContent = 'Tick ' + (report.tick !== null ? report.tick : '—') +
                             ' · ' + report.filename;
    modalBody.innerHTML = '<p style="color:#6b7280;">Cargando…</p>';
    modalBackdrop.style.display = 'flex';

    try {
      const res = await fetch(report.url);
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      // Los reportes son una lista de snapshots por proceso (o un único dict)
      const snapshots = Array.isArray(data) ? data : [data];
      modalBody.innerHTML = renderSnapshotsHTML(snapshots);
    } catch (err) {
      modalBody.innerHTML =
        '<p style="color:#c0392b;">No se pudo cargar el reporte: ' + err.message + '</p>';
    }
  }

  function renderSnapshotsHTML(snapshots) {
    return snapshots.map(snap => {
      const products = (snap.products || []).map(p => `
        <tr>
          <td class="center">${escapeHtml(p.product_id)}</td>
          <td class="center"><span class="modal-state-badge modal-state-${escapeAttr(p.state)}">${escapeHtml(p.state)}</span></td>
          <td class="center">${escapeHtml(p.pid)}</td>
          <td class="center">${escapeHtml(p.tid)}</td>
        </tr>
      `).join('') || '<tr><td colspan="4" style="text-align:center;color:#888;">Sin productos</td></tr>';

      const tasks = (snap.tasks || []).map(t => `
        <tr>
          <td class="center">${escapeHtml(t.task_id)}</td>
          <td class="center">${escapeHtml(t.task_time)}</td>
          <td>${(t.queue_product_ids || []).join(', ') || '<span style="color:#888;">vacío</span>'}</td>
          <td class="center"><span class="modal-state-badge modal-state-${escapeAttr(t.state)}">${escapeHtml(t.state)}</span></td>
          <td class="center">${t.product_in_process_id !== null && t.product_in_process_id !== undefined ? escapeHtml(t.product_in_process_id) : '—'}</td>
          <td class="center">${escapeHtml(t.current_time)}/${escapeHtml(t.task_time)}</td>
        </tr>
      `).join('') || '<tr><td colspan="6" style="text-align:center;color:#888;">Sin tareas</td></tr>';

      return `
        <div class="modal-process-block">
          <h3 class="modal-process-title">Proceso ${escapeHtml(snap.process_id)}</h3>

          <table class="modal-table">
            <thead>
              <tr>
                <th class="center">Producto</th>
                <th class="center">Estado</th>
                <th class="center">PID</th>
                <th class="center">TID</th>
              </tr>
            </thead>
            <tbody>${products}</tbody>
          </table>

          <table class="modal-table" style="margin-top:14px;">
            <thead>
              <tr>
                <th class="center">Tarea</th>
                <th class="center">T. tarea</th>
                <th>Cola</th>
                <th class="center">Estado</th>
                <th class="center">En proceso</th>
                <th class="center">Progreso</th>
              </tr>
            </thead>
            <tbody>${tasks}</tbody>
          </table>
        </div>
      `;
    }).join('');
  }

  function escapeHtml(v) {
    if (v === null || v === undefined) return '';
    return String(v)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  function escapeAttr(v) {
    if (v === null || v === undefined) return '';
    return String(v).replace(/[^A-Za-z0-9_-]/g, '');
  }

  function closeModal() {
    modalBackdrop.style.display = 'none';
    modalBody.innerHTML = '';
  }
  modalClose.addEventListener('click', closeModal);
  modalBackdrop.addEventListener('click', e => {
    if (e.target === modalBackdrop) closeModal();
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && modalBackdrop.style.display !== 'none') closeModal();
  });

  // ----- Init -----------------------------------------------------------
  // Si la URL trae ?error=, mostrar el banner
  const params = new URLSearchParams(window.location.search);
  const initialError = params.get('error');
  if (initialError === 'no_reports') {
    showBanner('No hay reportes disponibles. Ejecuta una simulación primero.', 'error');
  } else if (initialError === 'pdf_error') {
    showBanner('Ocurrió un error al generar el PDF. Revisa los logs del servidor.', 'error');
  }

  // Pre-cargar la lista en segundo plano para que el contador esté listo
  loadReportsList();

  // Liberar la URL del blob al salir
  window.addEventListener('beforeunload', () => {
    if (pdfBlobUrl) URL.revokeObjectURL(pdfBlobUrl);
  });

})();
