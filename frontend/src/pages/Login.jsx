import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { DEMO, api, oauthStartUrl } from '../lib/api.js';
import { useAuth } from '../lib/auth.jsx';
import { ErrorBox, Icon } from '../components/ui.jsx';

const SOCIAL = [
  { id: 'google', text: 'Google로 계속하기', icon: 'fa-brands fa-google', cls: 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50' },
  { id: 'naver', text: '네이버로 계속하기', icon: 'fa-solid fa-n', cls: 'bg-[#03C75A] text-white hover:brightness-95' },
  { id: 'kakao', text: '카카오로 계속하기', icon: 'fa-solid fa-comment', cls: 'bg-[#FEE500] text-[#191919] hover:brightness-95' },
];

/** 로그인 화면 — 좌: 브랜드 비주얼, 우: 로그인 폼 */
export default function Login() {
  const { login, demoLogin } = useAuth();
  const [params] = useSearchParams();
  const nav = useNavigate();
  const next = params.get('next') || '/';
  const [form, setForm] = useState({ email: '', password: '' });
  const [providers, setProviders] = useState({ demo_login: DEMO });
  const [error, setError] = useState(params.get('oauth_error') ? new Error(params.get('oauth_error')) : null);
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.get('/auth/providers').then(setProviders).catch(() => {}); }, []);

  const run = async (fn) => {
    setBusy(true);
    setError(null);
    try { await fn(); nav(next, { replace: true }); } catch (e) { setError(e); } finally { setBusy(false); }
  };
  const submit = (e) => { e.preventDefault(); run(() => login(form.email.trim(), form.password)); };
  const social = (id) => {
    if (!providers[id]) return setError(new Error(`${id} 로그인은 아직 설정되지 않았습니다. 관리자에게 문의하세요.`));
    window.location.href = oauthStartUrl(id, next);
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <section className="relative hidden overflow-hidden bg-gradient-to-br from-brand-700 via-brand-600 to-indigo-500 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <Link to="/" className="flex items-center gap-2 text-2xl"><Icon name="fa-clock-rotate-left" /><span className="font-display">BuyTiming</span></Link>
        <div>
          <h1 className="text-5xl leading-tight">지금 사도<br />될까요?</h1>
          <p className="mt-4 max-w-md text-lg text-white/80">쇼핑몰 가격을 1시간마다 비교하고, AI가 과거 가격 패턴으로 구매 적기를 알려 드립니다.</p>
          <div className="mt-10 grid max-w-md grid-cols-3 gap-3 text-center">
            {[['fa-chart-line', '가격 추이'], ['fa-robot', 'AI 조언'], ['fa-bell', '목표가 알림']].map(([i, t]) => (
              <div key={t} className="rounded-2xl bg-white/10 p-4 backdrop-blur"><Icon name={`${i} text-2xl`} /><div className="mt-2 text-sm">{t}</div></div>))}
          </div>
        </div>
        <div className="text-sm text-white/60">© BuyTiming · Final-Project 3조</div>
        <div className="pointer-events-none absolute -right-24 -top-24 h-80 w-80 rounded-full bg-white/10 blur-2xl" />
        <div className="pointer-events-none absolute -bottom-32 -left-16 h-96 w-96 rounded-full bg-indigo-300/20 blur-3xl" />
      </section>

      <section className="flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md">
          <Link to="/" className="mb-8 flex items-center gap-2 text-xl lg:hidden"><Icon name="fa-clock-rotate-left text-brand-600" /><span className="font-display">BuyTiming</span></Link>
          <h2 className="text-3xl text-slate-900">로그인</h2>
          <p className="mt-1 text-sm text-slate-500">계정이 없으신가요? <Link className="font-semibold text-brand-600" to="/signup">회원가입</Link></p>

          {providers.demo_login && (
            <div className="mt-6 grid grid-cols-2 gap-3">
              <button className="btn-outline" disabled={busy} onClick={() => run(() => demoLogin('user'))}><Icon name="fa-user" />일반 사용자 테스트</button>
              <button className="btn-outline" disabled={busy} onClick={() => run(() => demoLogin('admin'))}><Icon name="fa-user-shield" />관리자 테스트</button>
            </div>
          )}

          <form className="mt-6 space-y-4" onSubmit={submit}>
            <label className="block text-sm font-medium">이메일
              <input className="input mt-1" type="email" autoComplete="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="you@example.com" /></label>
            <label className="block text-sm font-medium">비밀번호
              <input className="input mt-1" type="password" autoComplete="current-password" required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></label>
            <ErrorBox error={error} />
            <button className="btn-primary w-full py-3" disabled={busy}>{busy ? <Icon name="fa-spinner animate-spin" /> : <Icon name="fa-right-to-bracket" />}로그인</button>
          </form>

          <div className="my-6 flex items-center gap-3 text-xs text-slate-400"><span className="h-px flex-1 bg-slate-200" />SNS 계정으로 로그인<span className="h-px flex-1 bg-slate-200" /></div>
          <div className="space-y-2.5">
            {SOCIAL.map((s) => (
              <button key={s.id} type="button" onClick={() => social(s.id)} className={`btn w-full py-3 ${s.cls} ${providers[s.id] ? '' : 'opacity-60'}`} title={providers[s.id] ? '' : '설정 필요'}>
                <i className={s.icon} aria-hidden="true" />{s.text}{!providers[s.id] && <span className="text-xs font-normal">(설정 필요)</span>}
              </button>))}
          </div>
        </div>
      </section>
    </div>
  );
}
