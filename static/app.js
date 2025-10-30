
async function loadData() {
  const res = await fetch('/api/data');
  const j = await res.json();
  const tbody = document.querySelector('#data tbody');
  tbody.innerHTML = '';
  if (!j.ok) return;
  j.items.forEach(it=>{
    const tr=document.createElement('tr');
    tr.innerHTML=`<td>${it.symbol}</td><td>${it.exA}</td><td>${it.exB}</td>
    <td>${it.spread_pct.toFixed(4)}</td>
    <td>${it.zscore===null?'':it.zscore.toFixed(2)}</td>
    <td>${it.fundingA??''}</td><td>${it.fundingB??''}</td>`;
    tbody.appendChild(tr);
  });
}
setInterval(loadData,1000);
loadData();
setInterval(fetchData, 1000); // 每1秒刷新一次
