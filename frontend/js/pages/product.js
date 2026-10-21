import { api } from '../api.js';
import { $, initPage, qs, esc, won, pct, dt, labelBadge, scoreBar, categoryIcon, spinner, showError, toast, LABELS } from '../common.js';

await initPage({ active: 'search' });

const id = Number(qs('id'));
const COLORS = ['#6f42c1', '#0d6efd', '#fd7e14'];

async function loadHead() {
  const p = await api.get(`/products/${id}`);
  document.title = `${p.name} · 바이타이밍`;
  $('#product-head').innerHTML = `<div class="d-flex flex-wrap align-items-center gap-3 mb-4">
    <div class="product-thumb lg"><i class="bi ${categoryIcon(p.category)}"></i></div>
    <div class="flex-grow-1"><div class="text-secondary small">${esc(p.category)} · ${esc(p.brand)} · ${esc(p.model_no)}</div>
      <h1 class="h3 fw-bold mb-0">${esc(p.name)}</h1></div>
    <div class="d-flex gap-2">
      <button class="btn btn-outline-primary" data-bs-toggle="modal" data-bs-target="#watch-modal"><i class="bi bi-star me-1"></i>관심 상품</button>
      <a class="btn btn-brand" href="chat.html?id=${p.id}"><i class="bi bi-stars me-1"></i>AI 상담</a>
    </div></div>`;
}

async function loadCompare() {
  const el = $('#compare');
  el.innerHTML = spinner();
  const c = await api.get(`/products/${id}/compare`);
  $('#collected-at').textContent = c.collected_at ? `수집 ${dt(c.collected_at)}` : '';
  if (!c.items.length) {
    el.innerHTML = '<p class="text-secondary mb-0">아직 수집된 가격이 없습니다. 다음 수집 주기(매시 정각)에 반영됩니다.</p>';
    return;
  }
  el.innerHTML = `<div class="table-responsive"><table class="table compare-table mb-0">
    <thead><tr><th>쇼핑몰</th><th class="text-end">판매가</th><th class="text-end">배송비</th><th class="text-end">실구매가</th><th></th></tr></thead><tbody>
    ${c.items.map((i) => `<tr class="${i.is_lowest ? 'lowest' : ''}${i.in_stock ? '' : ' soldout'}">
      <td>${esc(i.mall)} ${i.is_lowest ? '<span class="badge text-bg-success ms-1">최저가</span>' : ''}${i.in_stock ? '' : '<span class="badge text-bg-secondary ms-1">품절</span>'}</td>
      <td class="text-end text-nowrap">${won(i.price)}</td><td class="text-end text-nowrap">${i.shipping_fee ? won(i.shipping_fee) : '무료'}</td>
      <td class="text-end text-nowrap fw-bold">${won(i.total_price)}</td>
      <td class="text-end"><a class="btn btn-sm btn-outline-secondary${i.in_stock ? '' : ' disabled'}" href="${esc(i.url)}" target="_blank" rel="noopener">구매하기</a></td></tr>`).join('')}
    </tbody></table></div>`;
}

async function loadChart(days) {
  const el = $('#chart');
  const d = await api.get(`/products/${id}/prices?days=${days}`);
  if (!d.dates.length) {
    el.innerHTML = '<p class="text-secondary">가격 이력이 없습니다.</p>';
    return;
  }
  const traces = d.malls.map((m, i) => ({ x: d.dates, y: m.values, name: m.mall, mode: 'lines', line: { width: 1.5, color: COLORS[i % 3] }, opacity: 0.55 }));
  traces.push({ x: d.dates, y: d.lowest, name: '최저 실구매가', mode: 'lines+markers', line: { width: 3, color: '#198754' }, marker: { size: days <= 30 ? 5 : 3 } });
  const shapes = d.all_time_min.price ? [{ type: 'line', xref: 'paper', x0: 0, x1: 1, y0: d.all_time_min.price, y1: d.all_time_min.price, line: { dash: 'dot', color: '#dc3545', width: 1.5 } }] : [];
  const annotations = d.all_time_min.price ? [{ xref: 'paper', x: 0, y: d.all_time_min.price, text: `역대 최저 ${won(d.all_time_min.price)}`, showarrow: false, yanchor: 'bottom', xanchor: 'left', font: { size: 11, color: '#dc3545' } }] : [];
  Plotly.react(el, traces, {
    margin: { l: 70, r: 10, t: 10, b: 40 }, height: 340, hovermode: 'x unified', shapes, annotations,
    legend: { orientation: 'h', y: -0.18 }, yaxis: { tickformat: ',d', ticksuffix: '원' }, xaxis: { type: 'date', tickformat: '%m-%d' },
    font: { family: 'Pretendard, Malgun Gothic, sans-serif' },
  }, { displayModeBar: false, responsive: true });
}

async function loadTiming() {
  const el = $('#timing');
  el.innerHTML = spinner('구매 적기 분석 중…');
  const t = await api.get(`/products/${id}/timing`);
  const l = LABELS[t.label] || LABELS.HOLD;
  el.innerHTML = `<h2 class="h6 fw-bold">구매 적기 판정</h2>
    <div class="d-flex align-items-end gap-3 mb-2"><div class="score-big text-${l.cls}">${t.score ?? '–'}</div>
      <div class="pb-1">${labelBadge(t.label, 'fs-6')}<div class="small text-secondary mt-1">적기 점수 (0~100, 높을수록 지금이 저렴)</div></div></div>
    ${scoreBar(t.score, t.label)}
    <dl class="row small mt-3 mb-0">
      <dt class="col-6 text-secondary fw-normal">현재 최저 실구매가</dt><dd class="col-6 text-end fw-semibold">${won(t.current_price)}</dd>
      <dt class="col-6 text-secondary fw-normal">90일 최저가</dt><dd class="col-6 text-end">${won(t.min_90d)}</dd>
      <dt class="col-6 text-secondary fw-normal">90일 가격 위치</dt><dd class="col-6 text-end">${t.percentile_90d == null ? '-' : `하위 ${pct(t.percentile_90d)}`}</dd>
      <dt class="col-6 text-secondary fw-normal">7일 내 5% 하락 확률</dt><dd class="col-6 text-end">${pct(t.prob_drop_7d)}</dd>
      <dt class="col-6 text-secondary fw-normal">가격 이력</dt><dd class="col-6 text-end">${t.history_days}일</dd>
    </dl>
    <div class="small text-secondary mt-2"><i class="bi bi-cpu me-1"></i>모델 ${esc(t.model_version || '-')}</div>`;
}

async function loadAdvice() {
  const el = $('#advice');
  el.innerHTML = `<h2 class="h6 fw-bold"><i class="bi bi-stars text-brand me-1"></i>AI 구매 조언</h2>
    <div class="skeleton w-75"></div><div class="skeleton"></div><div class="skeleton w-50"></div>`;
  try {
    const a = await api.post(`/products/${id}/advice`);
    el.innerHTML = `<div class="d-flex justify-content-between align-items-center mb-2"><h2 class="h6 fw-bold mb-0"><i class="bi bi-stars text-brand me-1"></i>AI 구매 조언</h2>
      <span class="badge text-bg-light">${a.source === 'gemini' ? 'Gemini' : '규칙 기반'}${a.cached ? ' · 캐시' : ''}</span></div>
      <p class="fw-bold mb-1">${esc(a.verdict)}</p><p>${esc(a.summary)}</p>
      ${a.reasons.map((r) => `<div class="reason small mb-1"><i class="bi bi-check2-circle"></i><span>${esc(r)}</span></div>`).join('')}
      <p class="small text-secondary border-top pt-2 mt-3 mb-0"><i class="bi bi-info-circle me-1"></i>${esc(a.caution)}${a.remaining != null ? ` · 오늘 남은 AI 사용 ${a.remaining}회` : ''}</p>`;
  } catch (err) {
    el.innerHTML = '<h2 class="h6 fw-bold">AI 구매 조언</h2>';
    el.insertAdjacentHTML('beforeend', `<div class="alert alert-warning small mb-0">${esc(err.message)}</div>`);
  }
}

$('#range-group').addEventListener('click', (e) => {
  const btn = e.target.closest('button[data-days]');
  if (!btn) return;
  document.querySelectorAll('#range-group button').forEach((b) => b.classList.toggle('active', b === btn));
  loadChart(Number(btn.dataset.days)).catch((err) => showError(err));
});

$('#watch-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  try {
    const target = $('#target').value;
    await api.post('/watchlist', { product_id: id, target_price: target ? Number(target) : null });
    bootstrap.Modal.getInstance($('#watch-modal')).hide();
    toast('관심 상품으로 등록했습니다.', 'success');
  } catch (err) {
    showError(err);
  }
});

try {
  await loadHead();
  await Promise.all([loadCompare(), loadChart(90), loadTiming()]);
  loadAdvice();
} catch (err) {
  showError(err, $('#product-head'));
}
