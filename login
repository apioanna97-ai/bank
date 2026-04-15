<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Queue Token — First Community Bank</title>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500&family=DM+Mono:wght@500&display=swap" rel="stylesheet" />
  <style>
    *, *::before, *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    :root {
      --teal-50:  #E1F5EE;
      --teal-100: #9FE1CB;
      --teal-400: #1D9E75;
      --teal-600: #0F6E56;
      --teal-800: #085041;
      --teal-900: #04342C;
      --radius-md: 8px;
      --radius-lg: 14px;
      --radius-pill: 50px;
    }

    body {
      font-family: 'DM Sans', sans-serif;
      background: #f4f6f4;
      min-height: 100vh;
      display: flex;
      align-items: flex-start;
      justify-content: center;
      padding: 2rem 1rem 3rem;
    }

    /* ── Page wrapper ── */
    .page {
      width: 100%;
      max-width: 460px;
    }

    /* ── Bank header ── */
    .bank-header {
      text-align: center;
      margin-bottom: 1.75rem;
    }

    .bank-icon {
      width: 54px;
      height: 54px;
      border-radius: 50%;
      background: var(--teal-400);
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 12px;
    }

    .bank-icon svg {
      width: 24px;
      height: 24px;
      fill: none;
      stroke: #fff;
      stroke-width: 2;
      stroke-linecap: round;
      stroke-linejoin: round;
    }

    .bank-name {
      font-size: 17px;
      font-weight: 500;
      color: #1a1a1a;
      letter-spacing: 1.5px;
    }

    .bank-sub {
      font-size: 12px;
      color: #888;
      margin-top: 3px;
      letter-spacing: 0.4px;
    }

    /* ── Card ── */
    .card {
      background: #fff;
      border: 0.5px solid #d8d8d8;
      border-radius: var(--radius-lg);
      padding: 1.5rem;
    }

    /* ── Section label ── */
    .section-label {
      font-size: 11px;
      font-weight: 500;
      color: #999;
      text-transform: uppercase;
      letter-spacing: 0.9px;
      margin-bottom: 12px;
    }

    /* ── Service grid ── */
    .service-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 1.5rem;
    }

    .svc {
      background: #f7f8f7;
      border: 0.5px solid #e0e0e0;
      border-radius: var(--radius-md);
      padding: 14px 8px;
      text-align: center;
      cursor: pointer;
      transition: border-color 0.15s, background 0.15s;
      user-select: none;
    }

    .svc:hover {
      border-color: #b0b0b0;
    }

    .svc.active {
      border: 2px solid var(--teal-400);
      background: var(--teal-50);
    }

    .svc-code {
      font-size: 20px;
      font-weight: 500;
      color: #222;
    }

    .svc.active .svc-code {
      color: var(--teal-800);
    }

    .svc-name {
      font-size: 11px;
      color: #888;
      margin-top: 4px;
    }

    .svc.active .svc-name {
      color: var(--teal-600);
    }

    /* ── Get token button ── */
    .get-btn {
      width: 100%;
      padding: 13px;
      font-size: 15px;
      font-weight: 500;
      font-family: 'DM Sans', sans-serif;
      border-radius: var(--radius-pill);
      border: none;
      background: var(--teal-400);
      color: #fff;
      cursor: pointer;
      transition: opacity 0.2s, transform 0.1s;
    }

    .get-btn:disabled {
      opacity: 0.3;
      cursor: not-allowed;
    }

    .get-btn:not(:disabled):hover {
      opacity: 0.88;
    }

    .get-btn:not(:disabled):active {
      transform: scale(0.98);
    }

    /* ── Spinner ── */
    .spinner-wrap {
      display: none;
      text-align: center;
      padding: 1.5rem 0;
    }

    .spinner {
      width: 30px;
      height: 30px;
      border: 2.5px solid #e0e0e0;
      border-top-color: var(--teal-400);
      border-radius: 50%;
      animation: spin 0.75s linear infinite;
      margin: 0 auto 10px;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .spinner-text {
      font-size: 13px;
      color: #888;
    }

    /* ── Success section ── */
    .success-wrap {
      display: none;
    }

    .success-badge {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 7px;
      background: var(--teal-50);
      border: 0.5px solid var(--teal-100);
      border-radius: var(--radius-md);
      padding: 9px 16px;
      margin-bottom: 1rem;
    }

    .badge-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--teal-400);
      flex-shrink: 0;
    }

    .badge-text {
      font-size: 13px;
      font-weight: 500;
      color: var(--teal-600);
    }

    /* ── Token card ── */
    .token-card {
      background: var(--teal-50);
      border: 0.5px solid var(--teal-100);
      border-radius: var(--radius-lg);
      padding: 1.75rem 1.5rem 1.5rem;
      text-align: center;
      position: relative;
      overflow: hidden;
    }

    .token-label {
      font-size: 11px;
      font-weight: 500;
      color: var(--teal-600);
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    .token-number {
      font-family: 'DM Mono', monospace;
      font-size: 58px;
      font-weight: 500;
      color: var(--teal-800);
      letter-spacing: 10px;
      line-height: 1.1;
      margin: 10px 0 6px;
    }

    .token-service {
      font-size: 14px;
      color: var(--teal-600);
      margin-bottom: 1rem;
    }

    /* ── Meta tiles ── */
    .token-meta {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 1rem;
    }

    .meta-item {
      background: #fff;
      border: 0.5px solid var(--teal-100);
      border-radius: var(--radius-md);
      padding: 10px 12px;
    }

    .meta-label {
      font-size: 11px;
      color: var(--teal-400);
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.6px;
    }

    .meta-value {
      font-size: 22px;
      font-weight: 500;
      color: var(--teal-800);
      margin-top: 2px;
    }

    .token-hint {
      font-size: 12px;
      color: var(--teal-600);
      margin-top: 1rem;
    }

    /* ── Particle canvas ── */
    .particle-canvas {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
    }

    /* ── Reset button ── */
    .reset-btn {
      width: 100%;
      margin-top: 1rem;
      padding: 11px;
      font-size: 14px;
      font-weight: 500;
      font-family: 'DM Sans', sans-serif;
      border-radius: var(--radius-pill);
      border: 0.5px solid var(--teal-100);
      background: transparent;
      color: var(--teal-600);
      cursor: pointer;
      transition: background 0.15s;
    }

    .reset-btn:hover {
      background: var(--teal-50);
    }
  </style>
</head>
<body>

  <div class="page">

    <!-- Bank header -->
    <div class="bank-header">
      <div class="bank-icon">
        <svg viewBox="0 0 24 24">
          <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
      </div>
      <div class="bank-name">First Community Bank</div>
      <div class="bank-sub">Queue Management System</div>
    </div>

    <!-- Main card -->
    <div class="card">

      <!-- Form state -->
      <div id="formSection">
        <div class="section-label">Select service</div>
        <div class="service-grid" id="serviceGrid">
          <div class="svc" data-code="W" data-name="Withdrawal">
            <div class="svc-code">W</div>
            <div class="svc-name">Withdrawal</div>
          </div>
          <div class="svc" data-code="L" data-name="Loan Application">
            <div class="svc-code">L</div>
            <div class="svc-name">Loan</div>
          </div>
          <div class="svc" data-code="D" data-name="Deposit">
            <div class="svc-code">D</div>
            <div class="svc-name">Deposit</div>
          </div>
          <div class="svc" data-code="C" data-name="Account Opening">
            <div class="svc-code">C</div>
            <div class="svc-name">Account Opening</div>
          </div>
          <div class="svc" data-code="T" data-name="Cheque Processing">
            <div class="svc-code">T</div>
            <div class="svc-name">Cheque</div>
          </div>
          <div class="svc" data-code="E" data-name="Enquiry">
            <div class="svc-code">E</div>
            <div class="svc-name">Enquiries</div>
          </div>
        </div>
        <button class="get-btn" id="getBtn" disabled>Get queue token</button>
      </div>

      <!-- Loading state -->
      <div class="spinner-wrap" id="spinnerWrap">
        <div class="spinner"></div>
        <div class="spinner-text">Generating your token…</div>
      </div>

      <!-- Success state -->
      <div class="success-wrap" id="successWrap">
        <div class="success-badge">
          <div class="badge-dot"></div>
          <div class="badge-text">Token issued successfully</div>
        </div>
        <div class="token-card" id="tokenCard">
          <canvas class="particle-canvas" id="particleCanvas"></canvas>
          <div class="token-label">Your queue token</div>
          <div class="token-number" id="tokenNumber">—</div>
          <div class="token-service" id="tokenService">—</div>
          <div class="token-meta">
            <div class="meta-item">
              <div class="meta-label">Position</div>
              <div class="meta-value" id="metaPosition">—</div>
            </div>
            <div class="meta-item">
              <div class="meta-label">Wait time</div>
              <div class="meta-value" id="metaWait">—</div>
            </div>
          </div>
          <div class="token-hint">Please wait for your number to be called</div>
        </div>
        <button class="reset-btn" id="resetBtn">Get another token</button>
      </div>

    </div>
  </div>

  <script>
    const API_BASE = 'http://127.0.0.1:5000';
    let selected = null;

    // ── Service selection ──
    document.querySelectorAll('.svc').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.svc').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        selected = { code: btn.dataset.code, name: btn.dataset.name };
        document.getElementById('getBtn').disabled = false;
      });
    });

    document.getElementById('getBtn').addEventListener('click', handleGenerate);
    document.getElementById('resetBtn').addEventListener('click', handleReset);

    // ── State machine ──
    function showState(state) {
      document.getElementById('formSection').style.display  = state === 'form'    ? 'block' : 'none';
      document.getElementById('spinnerWrap').style.display  = state === 'loading' ? 'block' : 'none';
      document.getElementById('successWrap').style.display  = state === 'success' ? 'block' : 'none';
    }

    // ── Generate token ──
    async function handleGenerate() {
      if (!selected) return;
      showState('loading');

      try {
        const res = await fetch(`${API_BASE}/api/tokens`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            service_category: selected.code,
            customer_name: null,
            customer_phone: null,
            source: 'form'
          })
        });
        const data = await res.json();
        data.success ? renderToken(data) : handleApiError(data.message);
      } catch {
        renderToken(mockToken());
      }
    }

    function handleApiError(msg) {
      showState('form');
      alert('Error: ' + msg);
    }

    // ── Mock token (fallback when API is offline) ──
    function mockToken() {
      const pos = Math.floor(Math.random() * 10) + 1;
      return {
        token_number: selected.code + (Math.floor(Math.random() * 900) + 100),
        service_name: selected.name,
        queue_position: pos,
        estimated_wait: Math.round(pos * 4 + Math.random() * 4)
      };
    }

    // ── Render token ──
    function renderToken(data) {
      document.getElementById('tokenNumber').textContent  = data.token_number;
      document.getElementById('tokenService').textContent = data.service_name;
      document.getElementById('metaPosition').textContent = '#' + data.queue_position;
      document.getElementById('metaWait').textContent     = Math.round(data.estimated_wait) + ' min';
      showState('success');
      scrambleNumber(data.token_number);
      launchParticles();
    }

    // ── Reset ──
    function handleReset() {
      document.querySelectorAll('.svc').forEach(b => b.classList.remove('active'));
      selected = null;
      document.getElementById('getBtn').disabled = true;
      showState('form');
    }

    // ── Scramble animation ──
    function scrambleNumber(final) {
      const el     = document.getElementById('tokenNumber');
      const chars  = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
      let frame    = 0;
      const total  = 22;
      const iv = setInterval(() => {
        frame++;
        if (frame >= total) { el.textContent = final; clearInterval(iv); return; }
        const ratio = frame / total;
        el.textContent = final.split('').map((c, i) =>
          i < Math.floor(ratio * final.length)
            ? c
            : chars[Math.floor(Math.random() * chars.length)]
        ).join('');
      }, 46);
    }

    // ── Particle burst ──
    function launchParticles() {
      const canvas = document.getElementById('particleCanvas');
      const ctx    = canvas.getContext('2d');
      canvas.width  = canvas.offsetWidth  || 400;
      canvas.height = canvas.offsetHeight || 260;

      const palette = ['#1D9E75','#5DCAA5','#9FE1CB','#0F6E56','#085041','#c8ede0'];
      const particles = Array.from({ length: 56 }, () => ({
        x:     canvas.width / 2,
        y:     canvas.height / 2,
        vx:    (Math.random() - 0.5) * 9,
        vy:    (Math.random() - 0.75) * 11,
        r:     Math.random() * 5 + 2,
        color: palette[Math.floor(Math.random() * palette.length)],
        life:  1,
        decay: Math.random() * 0.022 + 0.015,
        rect:  Math.random() > 0.5
      }));

      function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        let alive = false;
        particles.forEach(p => {
          if (p.life <= 0) return;
          alive    = true;
          p.x     += p.vx;
          p.y     += p.vy;
          p.vy    += 0.26;
          p.life  -= p.decay;
          ctx.globalAlpha = Math.max(0, p.life);
          ctx.fillStyle   = p.color;
          if (p.rect) {
            ctx.fillRect(p.x - p.r / 2, p.y - p.r / 2, p.r, p.r);
          } else {
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fill();
          }
        });
        ctx.globalAlpha = 1;
        if (alive) requestAnimationFrame(draw);
      }

      draw();
    }

    // Init
    showState('form');
  </script>
</body>
</html>