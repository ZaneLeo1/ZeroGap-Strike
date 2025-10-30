const tbody = document.querySelector('#data tbody');
const title = document.querySelector('#title');
const info = document.getElementById('info');
const upd = document.getElementById('update');
const pairCount = document.getElementById('pairCount');

function fmt(num, p=4) {
  if (num === null || num === undefined || isNaN(num)) return '';
  return parseFloat(num).toFixed(p);
}

function render(items) {
  tbody.innerHTML = '';
  pairCount.textContent = `Pairs : ${items.length}`;
  for (const it of items) {
    const tr = document.createElement('tr');
    const nAB = it.net_ab_pct, nBA = it.net_ba_pct;
    const sAB = it.spread_ab_pct, sBA = it.spread_ba_pct;

    const dirAB = nAB > 0 ? '↑' : (nAB < 0 ? '↓' : '');
    const dirBA = nBA > 0 ? '↑' : (nBA < 0 ? '↓' : '');

    tr.innerHTML = `
      <td>${it.symbol}</td>
      <td>${it.exA}</td>
      <td>${it.exB}</td>
      <td class="${sAB>=0?'positive':'negative'}">${fmt(sAB)}%</td>
      <td class="${sBA>=0?'positive':'negative'}">${fmt(sBA)}%</td>
      <td class="${nAB>=0?'positive':'negative'}">${fmt(nAB)}% ${dirAB}</td>
      <td class="${nBA>=0?'positive':'negative'}">${fmt(nBA)}% ${dirBA}</td>
      <td>${fmt(it.zscore,2)}</td>
      <td>${fmt(it.fundingA,6)}</td>
      <td>${fmt(it.fundingB,6)}</td>
    `;
    tbody.appendChild(tr);
  }
}

async function tick() {
  try {
    const r = await fetch('/api/data', { cache:'no-store' });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const j = await r.json();
    if (!j.ok) throw new Error(j.error || 'API error');
    const ts = new Date(j.updated).toLocaleTimeString();
    upd.textContent = `Updated @ ${ts}`;
    title.textContent = 'ZeroGap-Strike v4.2 Realtime Monitor';
    render(j.items || []);
  } catch (e) {
    title.textContent = `❌ Error: ${e.message}`;
  }
}

tick();
setInterval(tick, 1000);