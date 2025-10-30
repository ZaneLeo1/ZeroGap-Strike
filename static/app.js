async function fetchData() {
  try {
    const res = await fetch('/api/data');
    const data = await res.json();
    renderTable(data);
  } catch (err) {
    console.error('数据加载失败:', err);
  }
}

function renderTable(data) {
  const table = document.getElementById('data-table');
  if (!table) return;

  table.innerHTML = `
    <tr>
      <th>Symbol</th>
      <th>ExA</th>
      <th>ExB</th>
      <th>Spread %</th>
      <th>Z-Score</th>
      <th>Funding A</th>
      <th>Funding B</th>
    </tr>
  `;

  data.forEach(row => {
    const spreadColor = row.spread > 0 ? '#00ff00' : '#ff4444';
    const zValue = row.zscore !== undefined ? row.zscore.toFixed(3) : '-';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${row.symbol}</td>
      <td>${row.exA}</td>
      <td>${row.exB}</td>
      <td style="color:${spreadColor};">${row.spread.toFixed(3)}</td>
      <td>${zValue}</td>
      <td>${row.fundingA ?? '-'}</td>
      <td>${row.fundingB ?? '-'}</td>
    `;
    table.appendChild(tr);
  });
}

// 初始化时加载一次
fetchData();

// ✅ 每1秒刷新一次
setInterval(fetchData, 1000);
