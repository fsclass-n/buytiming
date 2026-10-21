import { api } from '../api.js';
import { $, initPage, productCard, labelBadge, won, pct, esc, spinner, showError } from '../common.js';

await initPage({ active: 'home' });

const timingEl = $('#timing-list');
const dropEl = $('#drop-list');
timingEl.innerHTML = spinner();

try {
  const [{ timing, drops }, alerts] = await Promise.all([api.get('/deals/today'), api.get('/alerts')]);
  timingEl.innerHTML = timing.length
    ? timing.map((p) => productCard(p, `${labelBadge(p.label)}<span class="small text-secondary">점수 ${p.score}</span><span class="fw-semibold ms-auto">${won(p.current_price)}</span>`)).join('')
    : '<p class="text-secondary">판정 가능한 상품이 아직 없습니다.</p>';
  dropEl.innerHTML = drops.map((p) => productCard(p,
    `<span class="badge ${p.change_7d < 0 ? 'text-bg-primary' : 'text-bg-light'}"><i class="bi bi-arrow-${p.change_7d < 0 ? 'down' : 'up'}"></i> ${pct(Math.abs(p.change_7d), 1)}</span><span class="fw-semibold ms-auto">${won(p.current_price)}</span>`)).join('');
  const unread = alerts.items.filter((a) => !a.is_read).slice(0, 3);
  if (unread.length) {
    $('#alert-summary').innerHTML = `<div class="card p-3 mb-2"><div class="d-flex justify-content-between mb-2"><strong><i class="bi bi-bell-fill text-warning me-1"></i>새 알림 ${alerts.unread}건</strong><a href="alerts.html" class="small">전체 보기</a></div>
      ${unread.map((a) => `<a class="d-block small text-body text-decoration-none py-1" href="product.html?id=${a.product_id}">• ${esc(a.message)}</a>`).join('')}</div>`;
  }
} catch (err) {
  showError(err, timingEl);
}
