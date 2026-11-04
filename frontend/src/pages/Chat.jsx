import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../lib/api.js';
import { pct, won } from '../lib/format.js';
import { ErrorBox, Icon, LabelBadge, Spinner } from '../components/ui.jsx';

const SUGGESTS = ['다음 주까지 기다리면 더 싸질까?', '역대 최저가는 언제였어?', '할인은 보통 언제 해?', '어느 쇼핑몰이 제일 싸?'];

export default function Chat() {
  const { id } = useParams();
  const [p, setP] = useState(null);
  const [t, setT] = useState(null);
  const [error, setError] = useState(null);
  const [msgs, setMsgs] = useState([]);
  const [q, setQ] = useState('');
  const [busy, setBusy] = useState(false);
  const [remaining, setRemaining] = useState(null);
  const box = useRef(null);

  useEffect(() => {
    Promise.all([api.get(`/products/${id}`), api.get(`/products/${id}/timing`)]).then(([prod, timing]) => {
      setP(prod); setT(timing);
      setMsgs([{ role: 'ai', text: `안녕하세요! ${prod.name}의 가격과 구매 시점에 대해 물어보세요.` }]);
    }).catch(setError);
  }, [id]);
  useEffect(() => { box.current?.scrollTo({ top: box.current.scrollHeight, behavior: 'smooth' }); }, [msgs]);

  const ask = async (question) => {
    if (!question.trim() || busy) return;
    setQ('');
    setBusy(true);
    setMsgs((m) => [...m, { role: 'user', text: question }, { role: 'ai', text: '답변을 준비하고 있어요…', pending: true }]);
    try {
      const res = await api.post('/ai/chat', { product_id: Number(id), question });
      setRemaining(res.remaining);
      setMsgs((m) => [...m.slice(0, -1), { role: 'ai', text: res.answer }]);
    } catch (err) {
      setMsgs((m) => [...m.slice(0, -1), { role: 'ai', text: err.message, error: true }]);
    } finally { setBusy(false); }
  };

  if (error) return <ErrorBox error={error} />;
  if (!p || !t) return <Spinner />;
  return (
    <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
      <aside className="card h-fit p-5">
        <div className="text-xs text-slate-500">{p.category} · {p.brand}</div><h1 className="mt-1 text-xl">{p.name}</h1>
        <div className="mt-3 flex items-center gap-2"><LabelBadge value={t.label} /><span className="text-xs text-slate-500">적기 점수 {t.score ?? '-'}</span></div>
        <dl className="mt-4 space-y-1.5 text-sm">{[['현재 최저가', won(t.current_price)], ['90일 최저가', won(t.min_90d)], ['7일 하락 확률', pct(t.prob_drop_7d)]].map(([k, v]) => (
          <div key={k} className="flex justify-between"><dt className="text-slate-500">{k}</dt><dd>{v}</dd></div>))}</dl>
        <Link className="btn-outline mt-4 w-full" to={`/product/${id}`}>상품 상세로</Link>
      </aside>
      <section className="card flex h-[70vh] flex-col">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3"><h2 className="text-lg"><Icon name="fa-robot text-brand-600" className="mr-2" />AI 상담</h2>
          <span className="text-xs text-slate-500">{remaining != null && `오늘 남은 질문 ${remaining}회`}</span></div>
        <div ref={box} className="flex-1 space-y-3 overflow-y-auto p-5">
          {msgs.map((m, i) => (
            <div key={i} className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm ${m.role === 'user' ? 'ml-auto bg-brand-600 text-white' : m.error ? 'bg-rose-50 text-rose-700' : 'bg-slate-100'} ${m.pending ? 'animate-pulse' : ''}`}>{m.text}</div>))}
        </div>
        <div className="border-t border-slate-100 p-4">
          <div className="mb-3 flex flex-wrap gap-2">{SUGGESTS.map((s) => <button key={s} className="rounded-full border border-slate-200 px-3 py-1 text-xs hover:border-brand-500 hover:text-brand-600" onClick={() => ask(s)} disabled={busy}>{s}</button>)}</div>
          <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); ask(q); }}>
            <input className="input" value={q} onChange={(e) => setQ(e.target.value)} maxLength={300} placeholder="질문을 입력하세요" aria-label="질문" />
            <button className="btn-primary" disabled={busy} aria-label="보내기"><Icon name="fa-paper-plane" /></button>
          </form>
        </div>
      </section>
    </div>
  );
}
