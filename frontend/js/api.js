import { handleMock } from './mock.js';

const BASE = (window.APP_CONFIG?.API_BASE_URL || '').trim();
/** API_BASE_URL이 없으면 데모 모드: 같은 REST 계약을 브라우저 목업으로 처리 */
export const DEMO = BASE === '';
const API_ROOT = `${BASE.replace(/\/+$/, '')}/api/v1`;

const TOKEN_KEY = 'bt_token';
const USER_KEY = 'bt_user';

export class ApiError extends Error {
  constructor(status, code, message) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export const auth = {
  token: () => localStorage.getItem(TOKEN_KEY),
  user: () => JSON.parse(localStorage.getItem(USER_KEY) || 'null'),
  save(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
  async login(email, password) {
    const res = await api.post('/auth/login', { email, password });
    auth.save(res.access_token, res.user);
    return res.user;
  },
  async demoLogin(kind) {
    return auth.login(kind === 'admin' ? 'admin@buytiming.demo' : 'demo@buytiming.demo', 'demo');
  },
};

async function request(method, path, body) {
  const token = auth.token();
  if (DEMO) {
    const res = await handleMock(method, path, body, token);
    if (res.status >= 400) throw new ApiError(res.status, res.body.code, res.body.message);
    return res.body;
  }
  let resp;
  try {
    resp = await fetch(API_ROOT + path, {
      method,
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, 'NETWORK_ERROR', 'API 서버에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.');
  }
  const data = resp.status === 204 ? null : await resp.json().catch(() => ({}));
  if (resp.status === 401 && path !== '/auth/login') {
    auth.clear();
    location.href = `login.html?next=${encodeURIComponent(location.pathname.split('/').pop() + location.search)}`;
  }
  if (!resp.ok) throw new ApiError(resp.status, data?.code, data?.message || data?.detail || `요청 실패 (${resp.status})`);
  return data;
}

export const api = {
  get: (path) => request('GET', path),
  post: (path, body = {}) => request('POST', path, body),
  patch: (path, body = {}) => request('PATCH', path, body),
  del: (path) => request('DELETE', path),
};
