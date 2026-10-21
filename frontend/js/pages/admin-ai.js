import { api } from '../api.js';
import { $, initPage, esc, dt, pct, spinner, showError } from '../common.js';

await initPage({ active: 'admin-ai', admin: true });

const stat = (label, value) => `<div class="col-6 col-lg"><div class="card stat-card p-3 h-100"><div class="label">${label}</div><div class="value">${value}</div></div></div>`;
const layout = { height: 300, margin: { l: 55, r: 10, t: 10, b: 40 }, legend: { orientation: 'h', y: -0.2 }, xaxis: { type: 'category' }, font: { family: 'Pretendard, Malgun Gothic' } };

$('#recent').innerHTML = spinner();
try {
  const d = await api.get('/admin/ai-metrics');
  const s = d.summary;
  $('#stats').innerHTML = stat('7일 호출 수', s.calls_7d.toLocaleString('ko-KR')) + stat('평균 응답', `${(s.avg_latency_ms / 1000).toFixed(1)}초`)
    + stat('7일 토큰', s.tokens_7d.toLocaleString('ko-KR')) + stat('캐시 적중률', pct(s.cache_hit_rate)) + stat('검증 실패율', pct(s.validation_fail_rate, 2));
  const x = d.daily.map((r) => r.date);
  Plotly.react($('#chart-calls'), [
    { x, y: d.daily.map((r) => r.calls), type: 'bar', name: '호출', marker: { color: '#6f42c1' } },
    { x, y: d.daily.map((r) => r.cache_hits), type: 'scatter', mode: 'lines+markers', name: '캐시 적중', line: { color: '#198754' } },
  ], layout, { displayModeBar: false, responsive: true });
  Plotly.react($('#chart-latency'), [
    { x, y: d.daily.map((r) => r.avg_latency_ms), type: 'scatter', mode: 'lines+markers', name: '평균 응답(ms)', line: { color: '#fd7e14' } },
  ], { ...layout, shapes: [{ type: 'line', xref: 'paper', x0: 0, x1: 1, y0: 3000, y1: 3000, line: { dash: 'dot', color: '#dc3545' } }] }, { displayModeBar: false, responsive: true });
  $('#recent').innerHTML = `<div class="table-responsive"><table class="table table-sm align-middle mb-0"><thead><tr><th>시각</th><th>유형</th><th>상품</th><th class="text-end">응답(ms)</th><th>캐시</th><th>검증</th></tr></thead><tbody>
    ${d.recent.map((r) => `<tr><td class="text-nowrap">${dt(r.created_at)}</td><td>${esc(r.type)}</td><td>${esc(r.product)}</td><td class="text-end">${r.latency_ms.toLocaleString('ko-KR')}</td>
      <td>${r.cache_hit ? '<span class="badge text-bg-success">적중</span>' : '-'}</td><td><span class="badge text-bg-${r.validation === 'OK' ? 'light' : 'warning'}">${esc(r.validation)}</span></td></tr>`).join('')}</tbody></table></div>
    <p class="small text-secondary p-3 mb-0">모델: ${esc(s.model)}</p>`;
} catch (err) {
  showError(err, $('#recent'));
}
