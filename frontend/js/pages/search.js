import { api } from '../api.js';
import { $, initPage, productCard, labelBadge, won, qs, spinner, showError, toast } from '../common.js';

await initPage({ active: 'search' });

const results = $('#results');

async function search(q) {
  results.innerHTML = spinner('검색 중…');
  try {
    const { items } = await api.get(`/products/search?q=${encodeURIComponent(q)}`);
    results.innerHTML = items.length
      ? items.map((p) => productCard(p, `${labelBadge(p.label)}<span class="fw-semibold ms-auto">${won(p.lowest_price)}</span>`)).join('')
      : '<p class="text-secondary">검색 결과가 없습니다. 아래에서 상품 URL로 등록할 수 있습니다.</p>';
  } catch (err) {
    showError(err, results);
  }
}

$('#q').value = qs('q') || '';
search($('#q').value);

$('#search-form').addEventListener('submit', (e) => {
  e.preventDefault();
  const q = $('#q').value.trim();
  history.replaceState(null, '', q ? `?q=${encodeURIComponent(q)}` : location.pathname);
  search(q);
});

$('#url-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  try {
    const res = await api.post('/products', { url: $('#url').value.trim(), name: $('#pname').value.trim() || null });
    toast(res.message, 'success');
    e.target.reset();
    search($('#q').value.trim());
  } catch (err) {
    showError(err);
  }
});
