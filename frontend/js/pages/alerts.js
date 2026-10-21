import { api } from '../api.js';
import { $, initPage, esc, dt, spinner, showError } from '../common.js';

await initPage({ active: 'alerts' });

const el = $('#alert-list');
const ICON = { TARGET_PRICE: 'bi-bullseye text-success', TIMING_CHANGE: 'bi-arrow-repeat text-primary' };

async function render() {
  el.innerHTML = spinner();
  try {
    const { items } = await api.get('/alerts');
    el.innerHTML = items.length
      ? items.map((a) => `<a class="list-group-item list-group-item-action d-flex gap-3 py-3${a.is_read ? ' text-secondary' : ''}" href="product.html?id=${a.product_id}">
          <i class="bi ${ICON[a.type] || 'bi-bell'} fs-4"></i>
          <div class="flex-grow-1"><div class="${a.is_read ? '' : 'fw-semibold'}">${esc(a.message)}</div><div class="small text-secondary">${dt(a.created_at)}</div></div>
          ${a.is_read ? '' : '<span class="badge text-bg-danger align-self-center">새 알림</span>'}</a>`).join('')
      : '<div class="list-group-item text-secondary py-4">알림이 없습니다.</div>';
  } catch (err) {
    showError(err, el);
  }
}

$('#read-all').addEventListener('click', async () => {
  try {
    await api.post('/alerts/read-all');
    document.querySelector('#nav-alert-count')?.classList.add('d-none');
    render();
  } catch (err) {
    showError(err);
  }
});

render();
