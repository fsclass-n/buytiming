import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api.js';
import { won } from '../lib/format.js';
import { ErrorBox, Icon, LabelBadge, Modal, Spinner } from '../components/ui.jsx';
import { useToast } from '../components/Toast.jsx';

export default function Watchlist() {
  const toast = useToast();
  const [items, setItems] = useState(null);
  const [error, setError] = useState(null);
  const [edit, setEdit] = useState(null);
  const load = useCallback(() => api.get('/watchlist').then((r) => setItems(r.items)).catch(setError), []);
  useEffect(() => { load(); }, [load]);

  const save = async (e) => {
    e.preventDefault();
    try {
      await api.patch(`/watchlist/${edit.id}`, { target_price: edit.value ? Number(edit.value) : null });
      toast('목표가를 저장했습니다.', 'success'); setEdit(null); load();
    } catch (err) { toast(err.message, 'danger'); }
  };
  const remove = async (w) => {
    if (!window.confirm(`'${w.product.name}'을(를) 관심 상품에서 삭제할까요?`)) return;
    try { await api.del(`/watchlist/${w.id}`); toast('삭제했습니다.'); load(); } catch (err) { toast(err.message, 'danger'); }
  };

  return (
    <>
      <h1 className="text-3xl">관심 상품</h1>
      <p className="mt-1 text-sm text-slate-500">목표가에 도달하거나 판정이 바뀌면 알림을 보내 드립니다.</p>
      <div className="mt-4"><ErrorBox error={error} /></div>
      <section className="card mt-4 overflow-x-auto">
        {!items ? <Spinner /> : !items.length ? <p className="p-6 text-sm text-slate-500">관심 상품이 없습니다. 상품 상세 화면에서 등록해 보세요.</p> : (
          <table className="table-x">
            <thead><tr><th>상품</th><th className="text-right">현재 최저가</th><th className="text-right">목표가</th><th>판정</th><th className="text-right">관리</th></tr></thead>
            <tbody>{items.map((w) => (
              <tr key={w.id}>
                <td><Link to={`/product/${w.product.id}`} className="font-semibold hover:text-brand-600">{w.product.name}</Link><div className="text-xs text-slate-500">{w.product.category}</div></td>
                <td className="text-right">{won(w.current_price)}</td>
                <td className="text-right">{w.target_price ? won(w.target_price) : '-'} {w.reached && <span className="badge ml-1 bg-emerald-100 text-emerald-700">도달</span>}</td>
                <td><LabelBadge value={w.label} /> <span className="text-xs text-slate-500">{w.score ?? ''}</span></td>
                <td className="whitespace-nowrap text-right">
                  <button className="btn-outline px-3 py-1.5" onClick={() => setEdit({ id: w.id, value: w.target_price ?? '' })}>목표가</button>
                  <button className="btn-ghost ml-1 px-3 py-1.5 text-rose-600" onClick={() => remove(w)} aria-label="삭제"><Icon name="fa-trash" /></button></td>
              </tr>))}</tbody>
          </table>)}
      </section>
      <Modal open={!!edit} title="목표가 설정" onClose={() => setEdit(null)}>
        <form onSubmit={save} className="space-y-4">
          <label className="block text-sm font-medium">목표가(원) — 비우면 해제<input className="input mt-1" type="number" min="0" value={edit?.value ?? ''} onChange={(e) => setEdit({ ...edit, value: e.target.value })} /></label>
          <button className="btn-primary w-full">저장</button>
        </form>
      </Modal>
    </>
  );
}
