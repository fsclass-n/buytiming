import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../lib/api.js';
import { useAuth } from '../lib/auth.jsx';
import { pct, won } from '../lib/format.js';
import { ErrorBox, Icon, LabelBadge, ProductCard, Spinner } from '../components/ui.jsx';

export default function Home() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [deals, setDeals] = useState(null);
  const [alerts, setAlerts] = useState(null);
  const [error, setError] = useState(null);
  const [q, setQ] = useState('');

  useEffect(() => { api.get('/deals/today').then(setDeals).catch(setError); }, []);
  useEffect(() => { if (user) api.get('/alerts').then(setAlerts).catch(() => {}); }, [user]);
  const unread = alerts?.items.filter((a) => !a.is_read).slice(0, 3) || [];

  return (
    <>
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand-700 via-brand-600 to-indigo-500 px-6 py-12 text-white sm:px-12">
        <h1 className="text-4xl sm:text-5xl">지금 사도 될까요?</h1>
        <p className="mt-3 max-w-xl text-white/85">쇼핑몰 가격을 1시간마다 비교하고, AI가 과거 패턴으로 구매 적기를 알려 드립니다.</p>
        <form className="mt-8 flex max-w-xl gap-2" onSubmit={(e) => { e.preventDefault(); nav(`/search?q=${encodeURIComponent(q.trim())}`); }}>
          <input className="input border-0 py-3.5 text-base text-slate-800" value={q} onChange={(e) => setQ(e.target.value)} placeholder="상품명 검색 (예: 이어폰, 세제)" aria-label="상품 검색" />
          <button className="btn bg-white px-5 text-brand-700 hover:bg-brand-50" aria-label="검색"><Icon name="fa-magnifying-glass" /></button>
        </form>
        <div className="mt-8 flex flex-wrap gap-6 text-sm text-white/80">
          <span><Icon name="fa-store" className="mr-1" />쇼핑몰 가격 비교</span><span><Icon name="fa-chart-line" className="mr-1" />90일 가격 추이</span>
          <span><Icon name="fa-robot" className="mr-1" />Gemini AI 조언</span></div>
        <Icon name="fa-tags pointer-events-none absolute -bottom-6 right-6 text-[10rem] text-white/10" />
      </section>

      <div className="mt-6">
        {!user ? (
          <div className="card flex flex-wrap items-center justify-between gap-3 p-4 text-sm">
            <span><Icon name="fa-circle-user" className="mr-2 text-brand-600" />로그인하면 관심 상품의 목표가 알림과 AI 구매 조언을 받을 수 있습니다.</span>
            <Link className="btn-primary py-2" to="/login">로그인</Link></div>
        ) : unread.length > 0 && (
          <div className="card p-4"><div className="mb-2 flex justify-between"><strong><Icon name="fa-bell" className="mr-1 text-amber-500" />새 알림 {alerts.unread}건</strong>
            <Link to="/alerts" className="text-sm text-brand-600">전체 보기</Link></div>
            {unread.map((a) => <Link key={a.id} className="block py-1 text-sm text-slate-600 hover:text-brand-600" to={`/product/${a.product_id}`}>• {a.message}</Link>)}</div>
        )}
      </div>

      <ErrorBox error={error} />
      <h2 className="section-title"><Icon name="fa-bolt text-brand-600" />오늘의 구매 적기</h2>
      {!deals ? <Spinner /> : deals.timing.length ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {deals.timing.map((p) => <ProductCard key={p.id} p={p}><LabelBadge value={p.label} /><span className="text-xs text-slate-500">점수 {p.score}</span><span className="ml-auto font-semibold">{won(p.current_price)}</span></ProductCard>)}
        </div>) : <p className="text-sm text-slate-500">판정 가능한 상품이 아직 없습니다.</p>}

      <h2 className="section-title"><Icon name="fa-arrow-trend-down text-brand-600" />7일 가격 하락 추천</h2>
      {deals && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {deals.drops.map((p) => (
            <ProductCard key={p.id} p={p}>
              <span className={`badge ${p.change_7d < 0 ? 'bg-sky-100 text-sky-700' : 'bg-slate-100 text-slate-600'}`}><Icon name={p.change_7d < 0 ? 'fa-arrow-down' : 'fa-arrow-up'} />{pct(Math.abs(p.change_7d), 1)}</span>
              <span className="ml-auto font-semibold">{won(p.current_price)}</span></ProductCard>))}
        </div>)}
    </>
  );
}
