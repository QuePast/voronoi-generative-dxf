(function () {
  'use strict';

  const canvas = document.getElementById('voronoiCanvas');
  const ctx = canvas.getContext('2d');
  const spinner = document.getElementById('spinner');
  const status = document.getElementById('status');
  const downloadBtn = document.getElementById('downloadBtn');

  // Slider IDs and their display element IDs
  const SLIDERS = [
    'num_seeds',
    'space_between_cells',
    'outline_margin',
    'triangle_size',
    'corner_radius',
    'simplification_tolerance',
  ];

  // Colors for shape types
  const COLORS = {
    outline: { stroke: '#94a3b8', lineWidth: 1.5 },
    logo:    { stroke: '#34d399', lineWidth: 1.5 },
    cell:    { stroke: '#60a5fa', fill: 'rgba(96,165,250,0.06)', lineWidth: 1 },
  };

  let currentShapes = [];
  let debounceTimer = null;

  // ── Init sliders ──────────────────────────────────────────────
  SLIDERS.forEach(id => {
    const slider = document.getElementById(id);
    const badge = document.getElementById(id + '_val');

    const fmt = id === 'simplification_tolerance'
      ? v => parseFloat(v).toFixed(2)
      : v => parseFloat(v).toFixed(id === 'num_seeds' ? 0 : (v % 1 === 0 ? 0 : 1));

    badge.textContent = fmt(slider.value);

    slider.addEventListener('input', () => {
      badge.textContent = fmt(slider.value);
      schedulePreview();
    });
  });

  // ── Collect params ────────────────────────────────────────────
  function getParams() {
    const p = {};
    SLIDERS.forEach(id => {
      p[id] = parseFloat(document.getElementById(id).value);
    });
    return p;
  }

  // ── Debounce preview ──────────────────────────────────────────
  function schedulePreview() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(fetchPreview, 300);
  }

  // ── Fetch preview ─────────────────────────────────────────────
  async function fetchPreview() {
    showSpinner(true);
    hideStatus();

    try {
      const res = await fetch('/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(getParams()),
      });
      const data = await res.json();
      if (!res.ok || data.error) throw new Error(data.error || 'Server error');

      currentShapes = data.shapes;
      drawShapes(currentShapes);
    } catch (err) {
      showStatus('Error: ' + err.message, 'error');
    } finally {
      showSpinner(false);
    }
  }

  // ── Draw on canvas ────────────────────────────────────────────
  function drawShapes(shapes) {
    if (!shapes || shapes.length === 0) return;

    // Fit canvas to container
    const container = canvas.parentElement;
    const cw = container.clientWidth;
    const ch = container.clientHeight;

    // Find bounding box
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    shapes.forEach(s => {
      s.coords.forEach(([x, y]) => {
        if (x < minX) minX = x; if (x > maxX) maxX = x;
        if (y < minY) minY = y; if (y > maxY) maxY = y;
      });
    });

    const pad = 20;
    const geomW = maxX - minX;
    const geomH = maxY - minY;
    const scale = Math.min((cw - pad * 2) / geomW, (ch - pad * 2) / geomH);
    const offX = (cw - geomW * scale) / 2 - minX * scale;
    const offY = (ch - geomH * scale) / 2 - minY * scale;

    canvas.width = cw;
    canvas.height = ch;

    ctx.clearRect(0, 0, cw, ch);

    const toCanvasX = x => x * scale + offX;
    // Flip Y: SVG-style coords have Y increasing downward, but Shapely has Y up.
    // Reflect around canvas center vertically.
    const toCanvasY = y => ch - (y * scale + offY);

    shapes.forEach(shape => {
      const style = COLORS[shape.type] || COLORS.cell;
      const coords = shape.coords;
      if (!coords || coords.length < 2) return;

      ctx.beginPath();
      ctx.moveTo(toCanvasX(coords[0][0]), toCanvasY(coords[0][1]));
      for (let i = 1; i < coords.length; i++) {
        ctx.lineTo(toCanvasX(coords[i][0]), toCanvasY(coords[i][1]));
      }
      ctx.closePath();

      if (style.fill) {
        ctx.fillStyle = style.fill;
        ctx.fill();
      }
      ctx.strokeStyle = style.stroke;
      ctx.lineWidth = style.lineWidth;
      ctx.stroke();
    });
  }

  // ── Download DXF ──────────────────────────────────────────────
  downloadBtn.addEventListener('click', async () => {
    showSpinner(true);
    hideStatus();
    try {
      const res = await fetch('/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(getParams()),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || 'Download failed');
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'voronoi.dxf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      showStatus('DXF downloaded successfully.', 'info');
    } catch (err) {
      showStatus('Error: ' + err.message, 'error');
    } finally {
      showSpinner(false);
    }
  });

  // ── Helpers ───────────────────────────────────────────────────
  function showSpinner(v) {
    spinner.classList.toggle('hidden', !v);
  }

  function showStatus(msg, type) {
    status.textContent = msg;
    status.className = 'status ' + type;
  }

  function hideStatus() {
    status.className = 'status hidden';
  }

  // Redraw on window resize
  window.addEventListener('resize', () => {
    if (currentShapes.length) drawShapes(currentShapes);
  });

  // Initial load
  fetchPreview();
})();
