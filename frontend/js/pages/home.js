import { api } from '../api.js';
import { $, initPage, productCard, labelBadge, won, pct, esc, spinner, showError } from '../common.js';

// 홈은 로그인 없이 볼 수 있다. 알림 요약만 로그인 사용자에게 표시
const user = await initPage({ active: 'home', requireAuth: false });

const timingEl = $('#timing-list');
const dropEl = $('#drop-list');
timingEl.innerHTML = spinner();
if (!user) {
  $('#alert-summary').innerHTML = `<div class="card p-3 mb-2 small"><span><i class="bi bi-person-circle me-1"></i>
    <a href="login.html">로그인</a>하면 관심 상품의 목표가 알림과 AI 구매 조언을 받을 수 있습니다.</span></div>`;
}

try {
  const [{ timing, drops }, alerts] = await Promise.all([api.get('/deals/today'), user ? api.get('/alerts') : { items: [] }]);
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
