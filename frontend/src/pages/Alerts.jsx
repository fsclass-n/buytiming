import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api.js';
import { dt } from '../lib/format.js';
import { ErrorBox, Icon, Spinner } from '../components/ui.jsx';

const ICON = { TARGET_PRICE: 'fa-bullseye text-emerald-500', TIMING_CHANGE: 'fa-arrows-rotate text-sky-500' };

export default function Alerts() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const load = useCallback(() => api.get('/alerts').then(setData).catch(setError), []);
  useEffect(() => { load(); }, [load]);
  const readAll = () => api.post('/alerts/read-all').then(load).catch(setError);

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3"><h1 className="text-3xl">알림</h1>
        <button className="btn-outline" onClick={readAll}><Icon name="fa-check-double" />모두 읽음</button></div>
      <div className="mt-4"><ErrorBox error={error} /></div>
      <section className="card mt-4 divide-y divide-slate-100">
        {!data ? <Spinner /> : !data.items.length ? <p className="p-6 text-sm text-slate-500">알림이 없습니다.</p> : data.items.map((a) => (
          <Link key={a.id} to={`/product/${a.product_id}`} className={`flex gap-4 p-4 transition hover:bg-slate-50 ${a.is_read ? 'text-slate-400' : ''}`}>
            <Icon name={`${ICON[a.type] || 'fa-bell'} text-xl`} />
            <div className="flex-1"><div className={a.is_read ? '' : 'font-semibold'}>{a.message}</div><div className="text-xs text-slate-500">{dt(a.created_at)}</div></div>
            {!a.is_read && <span className="badge h-fit bg-rose-100 text-rose-600">새 알림</span>}
          </Link>))}
      </section>
    </>
  );
}
