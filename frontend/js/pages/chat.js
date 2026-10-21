import { api } from '../api.js';
import { $, initPage, qs, esc, won, pct, labelBadge, showError } from '../common.js';

await initPage({ active: 'search' });

const id = Number(qs('id')) || 1;
const box = $('#chat-box');
const SUGGESTS = ['다음 주까지 기다리면 더 싸질까?', '역대 최저가는 언제였어?', '할인은 보통 언제 해?', '어느 쇼핑몰이 제일 싸?'];

function addMsg(role, text) {
  const div = document.createElement('div');
  div.className = `chat-msg ${role}`;
  div.textContent = text;
  box.append(div);
  box.scrollTop = box.scrollHeight;
  return div;
}

async function ask(question) {
  addMsg('user', question);
  const pending = addMsg('ai', '답변을 준비하고 있어요…');
  $('#send-btn').disabled = true;
  try {
    const res = await api.post('/ai/chat', { product_id: id, question });
    pending.textContent = res.answer;
    $('#remaining').textContent = `오늘 남은 질문 ${res.remaining}회`;
  } catch (err) {
    pending.textContent = err.message;
    pending.classList.add('text-danger');
  } finally {
    $('#send-btn').disabled = false;
  }
}

try {
  const [p, t] = await Promise.all([api.get(`/products/${id}`), api.get(`/products/${id}/timing`)]);
  $('#chat-summary').innerHTML = `<div class="small text-secondary">${esc(p.category)} · ${esc(p.brand)}</div>
    <h2 class="h5 fw-bold">${esc(p.name)}</h2>
    <div class="mb-2">${labelBadge(t.label)} <span class="small text-secondary ms-1">적기 점수 ${t.score ?? '-'}</span></div>
    <dl class="row small mb-2"><dt class="col-6 fw-normal text-secondary">현재 최저가</dt><dd class="col-6 text-end">${won(t.current_price)}</dd>
      <dt class="col-6 fw-normal text-secondary">90일 최저가</dt><dd class="col-6 text-end">${won(t.min_90d)}</dd>
      <dt class="col-6 fw-normal text-secondary">7일 하락 확률</dt><dd class="col-6 text-end">${pct(t.prob_drop_7d)}</dd></dl>
    <a class="btn btn-outline-secondary btn-sm w-100" href="product.html?id=${id}">상품 상세로</a>`;
  addMsg('ai', `안녕하세요! ${p.name}의 가격과 구매 시점에 대해 물어보세요.`);
} catch (err) {
  showError(err, $('#chat-summary'));
}

$('#suggests').innerHTML = SUGGESTS.map((s) => `<button class="btn btn-outline-secondary btn-sm suggest-btn" type="button">${esc(s)}</button>`).join('');
$('#suggests').addEventListener('click', (e) => { if (e.target.matches('button')) ask(e.target.textContent); });
$('#chat-form').addEventListener('submit', (e) => {
  e.preventDefault();
  const q = $('#question').value.trim();
  if (!q) return;
  $('#question').value = '';
  ask(q);
});
