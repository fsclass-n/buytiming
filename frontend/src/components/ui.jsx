import { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { categoryIcon, label } from '../lib/format.js';

export const Icon = ({ name, className = '' }) => <i className={`fa-solid ${name} ${className}`} aria-hidden="true" />;

export function Spinner({ text = '불러오는 중…' }) {
  return <div className="py-12 text-center text-sm text-slate-500"><Icon name="fa-spinner" className="mr-2 animate-spin" />{text}</div>;
}

export function ErrorBox({ error }) {
  if (!error) return null;
  return <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"><Icon name="fa-triangle-exclamation" className="mr-2" />{error.message || String(error)}</div>;
}

export function LabelBadge({ value, large = false }) {
  const l = label(value);
  return <span className={`badge ${l.cls} ${large ? 'px-3 py-1 text-sm' : ''}`}><Icon name={l.icon} />{l.text}</span>;
}

export function ScoreBar({ score, value }) {
  const l = label(value);
  return (
    <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100" role="progressbar" aria-valuenow={score ?? 0} aria-valuemin="0" aria-valuemax="100">
      <div className={`h-full ${l.bar} transition-all duration-700`} style={{ width: `${score ?? 0}%` }} />
    </div>
  );
}

export function ProductCard({ p, children }) {
  return (
    <Link to={`/product/${p.id}`} className="card group flex gap-4 p-4 transition hover:-translate-y-0.5 hover:border-brand-500 hover:shadow-md">
      <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-xl text-brand-600 group-hover:bg-brand-100">
        <Icon name={categoryIcon(p.category)} />
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-xs text-slate-500">{p.category} · {p.brand}</div>
        <div className="truncate font-semibold text-slate-900">{p.name}</div>
        <div className="mt-1.5 flex flex-wrap items-center gap-2 text-sm">{children}</div>
      </div>
    </Link>
  );
}

export function Modal({ open, title, onClose, children }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-900/50 p-4" onClick={onClose}>
      <div className="card w-full max-w-md p-6" role="dialog" aria-modal="true" aria-label={title} onClick={(e) => e.stopPropagation()}>
        <div className="mb-4 flex items-center justify-between"><h2 className="text-lg">{title}</h2>
          <button className="btn-ghost px-2" onClick={onClose} aria-label="닫기"><Icon name="fa-xmark" /></button></div>
        {children}
      </div>
    </div>
  );
}

export function StatCard({ label: text, value, icon }) {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-2 text-xs text-slate-500"><Icon name={icon} className="text-brand-500" />{text}</div>
      <div className="mt-1 text-2xl font-bold text-slate-900">{value}</div>
    </div>
  );
}

/** Plotly(CDN) 차트 — index.html에서 지연 로드된 window.Plotly 사용 */
export function Plot({ data, layout, height = 320 }) {
  const ref = useRef(null);
  useEffect(() => {
    let alive = true;
    const draw = () => {
      if (!alive || !ref.current) return;
      if (!window.Plotly) return setTimeout(draw, 150);
      window.Plotly.react(ref.current, data, { height, margin: { l: 60, r: 20, t: 10, b: 40 }, font: { family: 'Pretendard Variable, Malgun Gothic' },
        legend: { orientation: 'h', y: -0.2 }, paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', ...layout }, { displayModeBar: false, responsive: true });
    };
    draw();
    return () => { alive = false; };
  }, [data, layout, height]);
  return <div ref={ref} style={{ minHeight: height }} />;
}
