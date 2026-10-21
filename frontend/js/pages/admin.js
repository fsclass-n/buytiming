import { api } from '../api.js';
import { $, initPage, esc, dt, pct, spinner, showError } from '../common.js';

await initPage({ active: 'admin', admin: true });

const STATUS = { SUCCESS: 'success', PARTIAL: 'warning', FAIL: 'danger', RUNNING: 'info' };
const stat = (label, value) => `<div class="col-6 col-lg-3"><div class="card stat-card p-3 h-100"><div class="label">${label}</div><div class="value">${value}</div></div></div>`;

$('#logs').innerHTML = spinner();
try {
  const d = await api.get('/admin/rpa-logs');
  const active = d.models.find((m) => m.active);
  $('#stats').innerHTML = stat('오늘 수집 실행', `${d.summary.runs_today}회`) + stat('7일 수집 성공률', pct(d.summary.success_rate, 1))
    + stat('오늘 수집 건수', d.summary.collected_today.toLocaleString('ko-KR')) + stat('운영 모델 F1', active ? active.f1.toFixed(2) : '-');
  Plotly.react($('#chart'), [
    { x: d.daily.map((r) => r.date), y: d.daily.map((r) => r.collected), type: 'bar', name: '수집 성공', marker: { color: '#6f42c1' } },
    { x: d.daily.map((r) => r.date), y: d.daily.map((r) => r.failed), type: 'scatter', mode: 'lines+markers', name: '실패 건수', line: { color: '#dc3545' }, yaxis: 'y2' },
  ], { height: 320, margin: { l: 60, r: 50, t: 10, b: 40 }, legend: { orientation: 'h', y: -0.2 },
    yaxis: { title: { text: '수집 성공' }, rangemode: 'tozero' }, yaxis2: { title: { text: '실패' }, overlaying: 'y', side: 'right', showgrid: false, rangemode: 'tozero' },
    xaxis: { type: 'category' }, font: { family: 'Pretendard, Malgun Gothic' } },
  { displayModeBar: false, responsive: true });
  $('#models').innerHTML = `<table class="table table-sm align-middle mb-0"><thead><tr><th>버전</th><th class="text-end">F1</th><th class="text-end">정밀도</th><th class="text-end">학습 행</th></tr></thead><tbody>
    ${d.models.map((m) => `<tr><td>${esc(m.version)} ${m.active ? '<span class="badge text-bg-success">운영</span>' : ''}<div class="small text-secondary">${esc(m.algorithm)}</div></td>
      <td class="text-end">${m.f1?.toFixed(2) ?? '-'}</td><td class="text-end">${m.precision?.toFixed(2) ?? '-'}</td><td class="text-end">${(m.trained_rows || 0).toLocaleString('ko-KR')}</td></tr>`).join('')}</tbody></table>`;
  $('#logs').innerHTML = `<div class="table-responsive"><table class="table table-sm align-middle mb-0"><thead><tr><th>시작</th><th>작업</th><th>상태</th><th class="text-end">처리</th><th class="text-end">실패</th><th>메시지</th></tr></thead><tbody>
    ${d.logs.map((l) => `<tr><td class="text-nowrap">${dt(l.started_at)}</td><td><code>${esc(l.job_name)}</code></td>
      <td><span class="badge text-bg-${STATUS[l.status] || 'secondary'}">${esc(l.status)}</span></td>
      <td class="text-end">${(l.collected || 0).toLocaleString('ko-KR')}</td><td class="text-end">${l.failed}</td><td class="small">${esc(l.message || '')}</td></tr>`).join('')}</tbody></table></div>`;
} catch (err) {
  showError(err, $('#logs'));
}
