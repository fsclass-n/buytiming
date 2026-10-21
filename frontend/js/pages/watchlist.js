import { api } from '../api.js';
import { $, initPage, esc, won, labelBadge, spinner, showError, toast } from '../common.js';

await initPage({ active: 'watchlist' });

const el = $('#watch-table');

async function render() {
  el.innerHTML = spinner();
  try {
    const { items } = await api.get('/watchlist');
    if (!items.length) {
      el.innerHTML = '<p class="text-secondary p-4 mb-0">관심 상품이 없습니다. 상품 상세 화면에서 등록해 보세요.</p>';
      return;
    }
    el.innerHTML = `<div class="table-responsive"><table class="table align-middle mb-0">
      <thead><tr><th>상품</th><th class="text-end">현재 최저가</th><th class="text-end">목표가</th><th>판정</th><th class="text-end">관리</th></tr></thead><tbody>
      ${items.map((w) => `<tr>
        <td><a href="product.html?id=${w.product.id}" class="fw-semibold">${esc(w.product.name)}</a><div class="small text-secondary">${esc(w.product.category)}</div></td>
        <td class="text-end">${won(w.current_price)}</td>
        <td class="text-end">${w.target_price ? won(w.target_price) : '-'} ${w.reached ? '<span class="badge text-bg-success ms-1">도달</span>' : ''}</td>
        <td>${labelBadge(w.label)} <span class="small text-secondary">${w.score ?? ''}</span></td>
        <td class="text-end text-nowrap"><button class="btn btn-sm btn-outline-secondary" data-edit="${w.id}" data-target="${w.target_price ?? ''}">목표가</button>
          <button class="btn btn-sm btn-outline-danger" data-del="${w.id}" aria-label="삭제"><i class="bi bi-trash"></i></button></td></tr>`).join('')}
      </tbody></table></div>`;
  } catch (err) {
    showError(err, el);
  }
}

el.addEventListener('click', async (e) => {
  const edit = e.target.closest('[data-edit]');
  const del = e.target.closest('[data-del]');
  try {
    if (edit) {
      const value = prompt('목표가(원)를 입력하세요. 비우면 해제됩니다.', edit.dataset.target);
      if (value === null) return;
      await api.patch(`/watchlist/${edit.dataset.edit}`, { target_price: value ? Number(value) : null });
      toast('목표가를 저장했습니다.', 'success');
    } else if (del && confirm('관심 상품에서 삭제할까요?')) {
      await api.del(`/watchlist/${del.dataset.del}`);
      toast('삭제했습니다.');
    } else return;
    render();
  } catch (err) {
    showError(err);
  }
});

render();
