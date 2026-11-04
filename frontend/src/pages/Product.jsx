import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../lib/api.js';
import { categoryIcon, dt, label, pct, won } from '../lib/format.js';
import { ErrorBox, Icon, LabelBadge, Modal, Plot, ScoreBar, Spinner } from '../components/ui.jsx';
import { useToast } from '../components/Toast.jsx';

const COLORS = ['#7c4dff', '#0ea5e9', '#f97316', '#14b8a6'];

export default function Product() {
  const { id } = useParams();
  const toast = useToast();
  const [p, setP] = useState(null);
  const [cmp, setCmp] = useState(null);
  const [chart, setChart] = useState(null);
  const [days, setDays] = useState(90);
  const [timing, setTiming] = useState(null);
  const [advice, setAdvice] = useState(null);
  const [adviceErr, setAdviceErr] = useState(null);
  const [error, setError] = useState(null);
  const [watchOpen, setWatchOpen] = useState(false);
  const [target, setTarget] = useState('');

  useEffect(() => {
    setError(null);
    api.get(`/products/${id}`).then((x) => { setP(x); document.title = `${x.name} · 바이타이밍`; }).catch(setError);
    api.get(`/products/${id}/compare`).then(setCmp).catch(setError);
    api.get(`/products/${id}/timing`).then(setTiming).catch(setError);
    api.post(`/products/${id}/advice`).then(setAdvice).catch(setAdviceErr);
  }, [id]);
  useEffect(() => { api.get(`/products/${id}/prices?days=${days}`).then(setChart).catch(setError); }, [id, days]);

  const traces = useMemo(() => {
    if (!chart?.dates.length) return null;
    const t = chart.malls.map((m, i) => ({ x: chart.dates, y: m.values, name: m.mall, mode: 'lines', line: { width: 1.5, color: COLORS[i % 4] }, opacity: 0.55 }));
    t.push({ x: chart.dates, y: chart.lowest, name: '최저 실구매가', mode: 'lines+markers', line: { width: 3, color: '#10b981' }, marker: { size: days <= 30 ? 5 : 3 } });
    return t;
  }, [chart, days]);
  const layout = useMemo(() => {
    const min = chart?.all_time_min?.price;
    return { hovermode: 'x unified', yaxis: { tickformat: ',d', ticksuffix: '원' }, xaxis: { type: 'date', tickformat: '%m-%d' },
      shapes: min ? [{ type: 'line', xref: 'paper', x0: 0, x1: 1, y0: min, y1: min, line: { dash: 'dot', color: '#e11d48', width: 1.5 } }] : [],
      annotations: min ? [{ xref: 'paper', x: 0, y: min, text: `역대 최저 ${won(min)}`, showarrow: false, yanchor: 'bottom', xanchor: 'left', font: { size: 11, color: '#e11d48' } }] : [] };
  }, [chart]);

  const addWatch = async (e) => {
    e.preventDefault();
    try {
      await api.post('/watchlist', { product_id: Number(id), target_price: target ? Number(target) : null });
      setWatchOpen(false);
      toast('관심 상품으로 등록했습니다.', 'success');
    } catch (err) { toast(err.message, 'danger'); }
  };

  if (error && !p) return <ErrorBox error={error} />;
  if (!p) return <Spinner />;
  const l = label(timing?.label);
  return (
    <>
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-50 text-2xl text-brand-600"><Icon name={categoryIcon(p.category)} /></div>
        <div className="flex-1"><div className="text-sm text-slate-500">{p.category} · {p.brand} · {p.model_no}</div><h1 className="text-3xl">{p.name}</h1></div>
        <div className="flex gap-2">
          <button className="btn-outline" onClick={() => setWatchOpen(true)}><Icon name="fa-star" />관심 상품</button>
          <Link className="btn-primary" to={`/chat/${p.id}`}><Icon name="fa-wand-magic-sparkles" />AI 상담</Link>
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <section className="card p-5">
            <div className="mb-3 flex items-center justify-between"><h2 className="text-lg">쇼핑몰별 가격 비교</h2><span className="text-xs text-slate-500">{cmp?.collected_at ? `수집 ${dt(cmp.collected_at)}` : ''}</span></div>
            {!cmp ? <Spinner /> : !cmp.items.length ? <p className="text-sm text-slate-500">아직 수집된 가격이 없습니다. 다음 수집 주기(매시 정각)에 반영됩니다.</p> : (
              <div className="overflow-x-auto"><table className="table-x">
                <thead><tr><th>쇼핑몰</th><th className="text-right">판매가</th><th className="text-right">배송비</th><th className="text-right">실구매가</th><th /></tr></thead>
                <tbody>{cmp.items.map((i) => (
                  <tr key={i.listing_id ?? i.mall} className={`${i.is_lowest ? 'bg-emerald-50/60' : ''} ${i.in_stock ? '' : 'text-slate-400'}`}>
                    <td className="font-medium">{i.mall} {i.is_lowest && <span className="badge ml-1 bg-emerald-100 text-emerald-700">최저가</span>}{!i.in_stock && <span className="badge ml-1 bg-slate-100">품절</span>}</td>
                    <td className="text-right">{won(i.price)}</td><td className="text-right">{i.shipping_fee ? won(i.shipping_fee) : '무료'}</td>
                    <td className="text-right font-bold">{won(i.total_price)}</td>
                    <td className="text-right"><a className={`btn-outline px-3 py-1.5 ${i.in_stock ? '' : 'pointer-events-none opacity-50'}`} href={i.url} target="_blank" rel="noopener noreferrer">구매하기</a></td>
                  </tr>))}</tbody></table></div>)}
          </section>

          <section className="card p-5">
            <div className="mb-2 flex items-center justify-between"><h2 className="text-lg">가격 추이</h2>
              <div className="flex gap-1" role="group" aria-label="기간">{[30, 90, 120].map((d) => (
                <button key={d} className={`rounded-lg px-3 py-1 text-sm ${days === d ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-600'}`} onClick={() => setDays(d)}>{d}일</button>))}</div></div>
            {!chart ? <Spinner /> : traces ? <Plot data={traces} layout={layout} height={340} /> : <p className="text-sm text-slate-500">가격 이력이 없습니다.</p>}
          </section>
        </div>

        <div className="space-y-6">
          <section className="card p-5">
            <h2 className="text-lg">구매 적기 판정</h2>
            {!timing ? <Spinner text="구매 적기 분석 중…" /> : (<>
              <div className="mt-3 flex items-end gap-3"><div className={`font-display text-6xl ${l.cls.split(' ')[1]}`}>{timing.score ?? '–'}</div>
                <div className="pb-2"><LabelBadge value={timing.label} large /><div className="mt-1 text-xs text-slate-500">적기 점수 (0~100, 높을수록 지금이 저렴)</div></div></div>
              <div className="mt-3"><ScoreBar score={timing.score} value={timing.label} /></div>
              <dl className="mt-4 space-y-1.5 text-sm">{[
                ['현재 최저 실구매가', won(timing.current_price)], ['90일 최저가', won(timing.min_90d)],
                ['90일 가격 위치', timing.percentile_90d == null ? '-' : `하위 ${pct(timing.percentile_90d)}`],
                ['7일 내 5% 하락 확률', pct(timing.prob_drop_7d)], ['가격 이력', `${timing.history_days}일`]].map(([k, v]) => (
                <div key={k} className="flex justify-between"><dt className="text-slate-500">{k}</dt><dd className="font-semibold">{v}</dd></div>))}</dl>
              <div className="mt-3 text-xs text-slate-400"><Icon name="fa-microchip" className="mr-1" />모델 {timing.model_version || '-'}</div>
            </>)}
          </section>

          <section className="card p-5">
            <div className="flex items-center justify-between"><h2 className="text-lg"><Icon name="fa-wand-magic-sparkles text-brand-600" className="mr-1" />AI 구매 조언</h2>
              {advice && <span className="badge bg-slate-100 text-slate-600">{advice.source === 'gemini' ? 'Gemini' : '규칙 기반'}{advice.cached ? ' · 캐시' : ''}</span>}</div>
            {adviceErr ? <div className="mt-3 rounded-xl bg-amber-50 p-3 text-sm text-amber-700">{adviceErr.message}</div> : !advice ? (
              <div className="mt-3"><div className="skeleton w-3/4" /><div className="skeleton" /><div className="skeleton w-1/2" /></div>) : (<>
              <p className="mt-3 font-bold">{advice.verdict}</p><p className="mt-1 text-sm">{advice.summary}</p>
              <ul className="mt-3 space-y-1.5 text-sm">{advice.reasons.map((r) => <li key={r} className="flex gap-2"><Icon name="fa-circle-check text-emerald-500 mt-0.5" />{r}</li>)}</ul>
              <p className="mt-4 border-t border-slate-100 pt-3 text-xs text-slate-500"><Icon name="fa-circle-info" className="mr-1" />{advice.caution}{advice.remaining != null && ` · 오늘 남은 AI 사용 ${advice.remaining}회`}</p>
            </>)}
          </section>
        </div>
      </div>

      <Modal open={watchOpen} title="관심 상품 등록" onClose={() => setWatchOpen(false)}>
        <form onSubmit={addWatch} className="space-y-4">
          <label className="block text-sm font-medium">목표가(원, 선택)<input className="input mt-1" type="number" min="0" value={target} onChange={(e) => setTarget(e.target.value)} placeholder="예: 120000" /></label>
          <p className="text-xs text-slate-500">현재 최저가가 목표가 이하로 내려가면 알림을 보내 드립니다.</p>
          <button className="btn-primary w-full"><Icon name="fa-star" />등록</button>
        </form>
      </Modal>
    </>
  );
}
