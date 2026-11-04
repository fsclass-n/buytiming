import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { DEMO, api } from '../lib/api.js';
import { useAuth } from '../lib/auth.jsx';
import { Icon } from './ui.jsx';

const NAV = [
  { to: '/', text: '홈', icon: 'fa-house', end: true },
  { to: '/search', text: '상품 검색', icon: 'fa-magnifying-glass' },
  { to: '/watchlist', text: '관심 상품', icon: 'fa-star' },
  { to: '/alerts', text: '알림', icon: 'fa-bell', alerts: true },
];
const ADMIN_NAV = [
  { to: '/admin', text: '수집·모델', icon: 'fa-microchip', end: true },
  { to: '/admin/ai', text: 'AI 사용량', icon: 'fa-wand-magic-sparkles' },
  { to: '/admin/users', text: '회원 관리', icon: 'fa-users-gear' },
];

function Brand() {
  return (
    <Link to="/" className="flex items-center gap-2 text-xl text-slate-900" aria-label="바이타이밍 홈">
      <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white"><Icon name="fa-clock-rotate-left" /></span>
      <span className="font-display">BuyTiming</span>
    </Link>
  );
}

function Header() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const loc = useLocation();
  const nav = useNavigate();
  const items = [...NAV, ...(user?.role === 'ADMIN' ? ADMIN_NAV : [])];

  useEffect(() => setOpen(false), [loc.pathname]);
  useEffect(() => { document.body.style.overflow = open ? 'hidden' : ''; }, [open]);
  useEffect(() => {
    if (!user) return setUnread(0);
    api.get('/alerts').then((a) => setUnread(a.unread || 0)).catch(() => {});
  }, [user, loc.pathname]);

  const out = () => { logout(); nav('/login'); };
  const link = ({ isActive }) => `flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition ${isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-100'}`;
  const badge = (n) => (n.alerts && unread > 0 ? <span className="badge bg-rose-500 text-white">{unread}</span> : null);

  return (
    <>
      {DEMO && <div className="bg-amber-100 py-1.5 text-center text-xs text-amber-800"><Icon name="fa-circle-info" className="mr-1" />데모 모드 — 서버 없이 브라우저 목업 데이터로 동작합니다</div>}
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="container-x flex h-16 items-center gap-6">
          <Brand />
          <nav className="hidden flex-1 items-center gap-1 lg:flex" aria-label="주 메뉴">
            {items.map((n) => <NavLink key={n.to} to={n.to} end={n.end} className={link}><Icon name={n.icon} />{n.text}{badge(n)}</NavLink>)}
          </nav>
          <div className="ml-auto hidden items-center gap-3 lg:flex">
            {user ? (<><span className="text-sm text-slate-600"><Icon name="fa-circle-user" className="mr-1" />{user.name || user.email}</span>
              <button className="btn-outline py-2" onClick={out}>로그아웃</button></>)
              : (<><Link className="btn-ghost" to="/signup">회원가입</Link><Link className="btn-primary py-2" to="/login">로그인</Link></>)}
          </div>
          <button className={`burger relative ml-auto h-6 w-6 text-slate-800 lg:hidden ${open ? 'open' : ''}`} onClick={() => setOpen(!open)}
            aria-label={open ? '메뉴 닫기' : '메뉴 열기'} aria-expanded={open} aria-controls="mobile-drawer">
            <span /><span /><span />
          </button>
        </div>
      </header>

      {/* 모바일 드로어: 오른쪽 → 왼쪽으로 밀려 들어옴 */}
      <div className={`fixed inset-0 z-50 bg-slate-900/40 transition-opacity duration-300 lg:hidden ${open ? 'opacity-100' : 'pointer-events-none opacity-0'}`} onClick={() => setOpen(false)} />
      <aside id="mobile-drawer" className={`fixed right-0 top-0 z-50 flex h-full w-80 max-w-[85%] flex-col bg-white shadow-2xl transition-transform duration-300 ease-out lg:hidden ${open ? 'translate-x-0' : 'translate-x-full'}`}
        aria-hidden={!open}>
        <div className="flex h-16 items-center justify-between border-b border-slate-100 px-5"><Brand />
          <button className={`burger open relative h-6 w-6`} onClick={() => setOpen(false)} aria-label="메뉴 닫기"><span /><span /><span /></button></div>
        <div className="border-b border-slate-100 p-5">
          {user ? <div className="text-sm"><Icon name="fa-circle-user" className="mr-2 text-brand-600" />{user.name || user.email}<div className="text-xs text-slate-500">{user.role === 'ADMIN' ? '관리자' : '일반 회원'}</div></div>
            : <div className="grid grid-cols-2 gap-2"><Link className="btn-primary" to="/login">로그인</Link><Link className="btn-outline" to="/signup">회원가입</Link></div>}
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto p-3" aria-label="모바일 메뉴">
          {items.map((n, i) => (
            <NavLink key={n.to} to={n.to} end={n.end} className={link} style={{ transitionDelay: open ? `${i * 30}ms` : '0ms' }}>
              <Icon name={n.icon} className="w-5" />{n.text}{badge(n)}
            </NavLink>))}
        </nav>
        {user && <div className="border-t border-slate-100 p-4"><button className="btn-outline w-full" onClick={out}><Icon name="fa-right-from-bracket" />로그아웃</button></div>}
      </aside>
    </>
  );
}

function Footer() {
  const [show, setShow] = useState(false);
  useEffect(() => {
    const onScroll = () => setShow(window.scrollY > 300);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);
  return (
    <footer className="mt-16 border-t border-slate-200 bg-white">
      <div className="container-x grid gap-8 py-10 md:grid-cols-3">
        <div><Brand /><p className="mt-3 text-sm text-slate-500">쇼핑몰 가격을 1시간마다 비교하고, AI가 과거 패턴으로 구매 적기를 알려 드립니다.</p></div>
        <div className="text-sm"><div className="mb-2 font-semibold text-slate-900">서비스</div>
          <ul className="space-y-1 text-slate-500"><li><Link to="/search">상품 검색</Link></li><li><Link to="/watchlist">관심 상품</Link></li><li><Link to="/alerts">가격 알림</Link></li></ul></div>
        <div className="text-sm text-slate-500"><div className="mb-2 font-semibold text-slate-900">Final-Project 3조</div>
          박미금(팀장) · 김모란 · 이오리 · 홍기흥
          <div className="mt-2"><a className="hover:text-brand-600" href="https://github.com/fsclass-n/buytiming" target="_blank" rel="noreferrer"><Icon name="fa-code-branch" className="mr-1" />GitHub</a></div></div>
      </div>
      <div className="border-t border-slate-100 py-4 text-center text-xs text-slate-400">가격 예측은 과거 데이터 기반 참고 정보이며 실제 가격과 다를 수 있습니다. © BuyTiming</div>
      <button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} aria-label="맨 위로"
        className={`fixed bottom-6 right-6 z-30 flex h-12 w-12 items-center justify-center rounded-full bg-brand-600 text-white shadow-lg transition-all duration-300 hover:bg-brand-700 ${show ? 'translate-y-0 opacity-100' : 'pointer-events-none translate-y-4 opacity-0'}`}>
        <Icon name="fa-arrow-up" />
      </button>
    </footer>
  );
}

export default function Layout() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="container-x flex-1 py-8"><Outlet /></main>
      <Footer />
    </div>
  );
}
