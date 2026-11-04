import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, auth } from '../lib/api.js';
import { useAuth } from '../lib/auth.jsx';
import { ErrorBox, Spinner } from '../components/ui.jsx';

/** 소셜 로그인 완료: 서버가 #token=...&next=... 로 돌려보낸 토큰을 저장한다 */
export default function OAuthCallback() {
  const { setUser } = useAuth();
  const nav = useNavigate();
  const [error, setError] = useState(null);
  useEffect(() => {
    const h = new URLSearchParams(window.location.hash.slice(1));
    const token = h.get('token');
    const next = h.get('next') || '/';
    if (!token) return setError(new Error('로그인 정보를 받지 못했습니다.'));
    localStorage.setItem('bt_token', token);
    api.get('/users/me').then((u) => {
      auth.save(token, u);
      setUser(u);
      nav(next.startsWith('/') && !next.startsWith('//') ? next : '/', { replace: true });
    }).catch(setError);
  }, [nav, setUser]);
  return <div className="mx-auto max-w-md p-10">{error ? <ErrorBox error={error} /> : <Spinner text="소셜 로그인 처리 중…" />}</div>;
}
