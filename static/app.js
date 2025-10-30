// static/app.js
const TBody = document.querySelector('#data tbody');
const title = document.querySelector('h2');

function render(items) {
  TBody.innerHTML = '';
  for (const it of items) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${it.symbol}</td>
      <td>${it.exA}</td>
      <td>${it.exB}</td>
      <td>${it.spread_pct?.toFixed(4) ?? ''}</td>
      <td>${it.zscore == null ? '' : it.zscore.toFixed(2)}</td>
      <td>${it.fundingA ?? ''}</td>
      <td>${it.fundingB ?? ''}</td>
    `;
    TBody.appendChild(tr);
  }
}

async function tick() {
  try {
    const r = await fetch('/api/data');
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const j = await r.json();
    if (!j.ok) throw new Error(j.error || 'api error');
    title.textContent = `ZeroGap-Strike v4.2 Realtime Monitor — ${j.updated}`;
    render(j.items || []);
  } catch (e) {
    title.textContent = `ZeroGap-Strike v4.2 Realtime Monitor — ERROR: ${e.message}`;
  }
}

tick();
setInterval(tick, 1000);
