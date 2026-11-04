import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../lib/api.js';
import { useAuth } from '../lib/auth.jsx';
import { PASSWORD_RULE } from '../lib/format.js';
import { ErrorBox, Icon } from '../components/ui.jsx';

const CHECKS = [
  ['8자 이상', (p) => p.length >= 8],
  ['영문 대문자', (p) => /[A-Z]/.test(p)],
  ['영문 소문자', (p) => /[a-z]/.test(p)],
  ['숫자', (p) => /\d/.test(p)],
  ['특수문자', (p) => /[^A-Za-z0-9\s]/.test(p)],
];

export default function Signup() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [f, setF] = useState({ name: '', email: '', password: '', confirm: '' });
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const valid = PASSWORD_RULE.test(f.password);
  const match = f.password && f.password === f.confirm;

  const submit = async (e) => {
    e.preventDefault();
    if (!valid) return setError(new Error('비밀번호는 영문 대문자·소문자·숫자·특수문자를 모두 포함해 8자 이상이어야 합니다.'));
    if (!match) return setError(new Error('비밀번호 확인이 일치하지 않습니다.'));
    setBusy(true);
    setError(null);
    try {
      await api.post('/auth/signup', { name: f.name.trim(), email: f.email.trim(), password: f.password });
      await login(f.email.trim(), f.password);
      nav('/', { replace: true });
    } catch (err) { setError(err); } finally { setBusy(false); }
  };
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-50 to-white p-6">
      <div className="card w-full max-w-md p-8">
        <Link to="/" className="mb-6 flex items-center gap-2 text-xl"><Icon name="fa-clock-rotate-left text-brand-600" /><span className="font-display">PickTiming</span></Link>
        <h1 className="text-3xl">회원가입</h1>
        <p className="mt-1 text-sm text-slate-500">이미 계정이 있으신가요? <Link className="font-semibold text-brand-600" to="/login">로그인</Link></p>
        <form className="mt-6 space-y-4" onSubmit={submit}>
          <label className="block text-sm font-medium">이름<input className="input mt-1" required maxLength={50} value={f.name} onChange={set('name')} /></label>
          <label className="block text-sm font-medium">이메일<input className="input mt-1" type="email" required value={f.email} onChange={set('email')} /></label>
          <label className="block text-sm font-medium">비밀번호<input className="input mt-1" type="password" autoComplete="new-password" required value={f.password} onChange={set('password')} /></label>
          <ul className="grid grid-cols-3 gap-1.5 text-xs" aria-label="비밀번호 규칙">
            {CHECKS.map(([t, fn]) => {
              const ok = fn(f.password);
              return <li key={t} className={ok ? 'text-emerald-600' : 'text-slate-400'}><Icon name={ok ? 'fa-circle-check' : 'fa-circle'} className="mr-1" />{t}</li>;
            })}
          </ul>
          <label className="block text-sm font-medium">비밀번호 확인<input className="input mt-1" type="password" autoComplete="new-password" required value={f.confirm} onChange={set('confirm')} />
            {f.confirm && !match && <span className="mt-1 block text-xs text-rose-600">비밀번호가 일치하지 않습니다.</span>}</label>
          <ErrorBox error={error} />
          <button className="btn-primary w-full py-3" disabled={busy || !valid || !match}><Icon name="fa-user-plus" />가입하기</button>
        </form>
      </div>
    </div>
  );
}
