import { DEMO, api, auth } from './api.js';

export const LABELS = {
  BUY_NOW: { text: '지금 구매', cls: 'success', icon: 'bi-bag-check' },
  WAIT_A_BIT: { text: '조금 대기', cls: 'warning', icon: 'bi-hourglass-split' },
  WAIT: { text: '대기 권장', cls: 'danger', icon: 'bi-pause-circle' },
  HOLD: { text: '판단 보류', cls: 'secondary', icon: 'bi-question-circle' },
};

const CATEGORY_ICONS = { 디지털: 'bi-headphones', 가전: 'bi-plug', 생필품: 'bi-basket', 유아: 'bi-balloon-heart' };

const NAV = [
  { key: 'home', href: 'index.html', text: '홈', icon: 'bi-house' },
  { key: 'search', href: 'search.html', text: '상품 검색', icon: 'bi-search' },
  { key: 'watchlist', href: 'watchlist.html', text: '관심 상품', icon: 'bi-star' },
  { key: 'alerts', href: 'alerts.html', text: '알림', icon: 'bi-bell' },
];
const ADMIN_NAV = [
  { key: 'admin', href: 'admin.html', text: '수집·모델', icon: 'bi-cpu' },
  { key: 'admin-ai', href: 'admin-ai.html', text: 'AI 사용량', icon: 'bi-stars' },
];

export const $ = (sel, root = document) => root.querySelector(sel);
export const qs = (name) => new URLSearchParams(location.search).get(name);

export function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

export const won = (n) => (n == null ? '-' : `${Number(n).toLocaleString('ko-KR')}원`);
export const pct = (v, digits = 0) => (v == null ? '-' : `${(v * 100).toFixed(digits)}%`);
export const dt = (iso) => (iso ? new Date(iso).toLocaleString('ko-KR', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '-');
export const categoryIcon = (c) => CATEGORY_ICONS[c] || 'bi-box-seam';

export function labelBadge(label, size = '') {
  const l = LABELS[label] || LABELS.HOLD;
  return `<span class="badge text-bg-${l.cls} ${size}"><i class="bi ${l.icon} me-1"></i>${l.text}</span>`;
}

export function toast(message, type = 'dark') {
  let box = $('#toast-box');
  if (!box) {
    box = document.createElement('div');
    box.id = 'toast-box';
    box.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    document.body.append(box);
  }
  const el = document.createElement('div');
  el.className = `toast align-items-center text-bg-${type} border-0`;
  el.role = 'alert';
  el.innerHTML = `<div class="d-flex"><div class="toast-body">${esc(message)}</div>
    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>`;
  box.append(el);
  new bootstrap.Toast(el, { delay: 3000 }).show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
}

export function showError(err, target) {
  const msg = err?.message || '요청을 처리하지 못했습니다.';
  if (target) target.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-triangle me-1"></i>${esc(msg)}</div>`;
  else toast(msg, 'danger');
}

export const spinner = (text = '불러오는 중…') =>
  `<div class="text-center text-secondary py-5"><div class="spinner-border spinner-border-sm me-2"></div>${esc(text)}</div>`;

function renderNav(active, user) {
  const items = [...NAV, ...(user?.role === 'ADMIN' ? ADMIN_NAV : [])];
  const links = items.map((n) => `<li class="nav-item"><a class="nav-link${n.key === active ? ' active' : ''}" href="${n.href}">
      <i class="bi ${n.icon} me-1"></i>${n.text}${n.key === 'alerts' ? '<span id="nav-alert-count" class="badge rounded-pill text-bg-danger ms-1 d-none"></span>' : ''}</a></li>`).join('');
  const right = user
    ? `<span class="navbar-text small me-3"><i class="bi bi-person-circle me-1"></i>${esc(user.name || user.email)}</span>
       <button class="btn btn-outline-light btn-sm" id="btn-logout">로그아웃</button>`
    : `<a class="btn btn-light btn-sm" href="login.html">로그인</a>`;
  $('#app-nav').outerHTML = `
  ${DEMO ? `<div class="demo-banner text-center small py-1"><i class="bi bi-info-circle me-1"></i>데모 모드 — 서버 없이 브라우저 목업 데이터로 동작합니다 (API_BASE_URL 설정 시 실제 API 연동)</div>` : ''}
  <nav class="navbar navbar-expand-lg navbar-dark bg-brand sticky-top">
    <div class="container">
      <a class="navbar-brand fw-bold" href="index.html"><i class="bi bi-clock-history me-1"></i>BuyTiming</a>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#nav-main" aria-label="메뉴"><span class="navbar-toggler-icon"></span></button>
      <div class="collapse navbar-collapse" id="nav-main">
        <ul class="navbar-nav me-auto">${links}</ul>
        <div class="d-flex align-items-center mt-2 mt-lg-0">${right}</div>
      </div>
    </div>
  </nav>`;
  $('#btn-logout')?.addEventListener('click', () => { auth.clear(); location.href = 'login.html'; });
}

function renderFooter() {
  const f = $('#app-footer');
  if (f) f.outerHTML = `<footer class="border-top py-4 mt-5 text-center small text-secondary">
    바이타이밍(BuyTiming) · Final-Project 3조 · 가격 예측은 과거 데이터 기반 참고 정보이며 실제 가격과 다를 수 있습니다.</footer>`;
}

async function refreshAlertCount() {
  try {
    const { unread } = await api.get('/alerts');
    const el = $('#nav-alert-count');
    if (el && unread > 0) { el.textContent = unread; el.classList.remove('d-none'); }
  } catch { /* 알림 배지는 실패해도 무시 */ }
}

/** 공통 초기화: 내비게이션·인증 확인. 로그인이 필요한 화면은 user를 반환한다. */
export async function initPage({ active = '', requireAuth = true, admin = false } = {}) {
  let user = auth.user();
  if (DEMO && !user && requireAuth) user = await auth.demoLogin(qs('as') === 'admin' ? 'admin' : 'demo');
  if (requireAuth && !user) {
    location.href = `login.html?next=${encodeURIComponent(location.pathname.split('/').pop() + location.search)}`;
    return new Promise(() => {});
  }
  if (admin && user?.role !== 'ADMIN') {
    renderNav(active, user);
    renderFooter();
    $('#app').innerHTML = `<div class="alert alert-warning">관리자만 접근할 수 있는 화면입니다.</div>`;
    return new Promise(() => {});
  }
  renderNav(active, user);
  renderFooter();
  if (user) refreshAlertCount();
  return user;
}

export function productCard(p, extra = '') {
  return `<div class="col-12 col-sm-6 col-lg-4">
    <a class="card product-card h-100 text-decoration-none" href="product.html?id=${p.id}">
      <div class="card-body d-flex gap-3">
        <div class="product-thumb"><i class="bi ${categoryIcon(p.category)}"></i></div>
        <div class="flex-grow-1 min-w-0">
          <div class="small text-secondary">${esc(p.category)} · ${esc(p.brand || '')}</div>
          <div class="fw-semibold text-body text-truncate">${esc(p.name)}</div>
          <div class="d-flex align-items-center gap-2 mt-1 flex-wrap">${extra}</div>
        </div>
      </div>
    </a></div>`;
}

export function scoreBar(score, label) {
  const l = LABELS[label] || LABELS.HOLD;
  const value = score ?? 0;
  return `<div class="progress score-bar" role="progressbar" aria-valuenow="${value}" aria-valuemin="0" aria-valuemax="100">
    <div class="progress-bar bg-${l.cls}" style="width:${value}%">${score == null ? '' : score}</div></div>`;
}
