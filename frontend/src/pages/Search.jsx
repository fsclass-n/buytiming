import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../lib/api.js';
import { won } from '../lib/format.js';
import { ErrorBox, Icon, LabelBadge, ProductCard, Spinner } from '../components/ui.jsx';
import { useToast } from '../components/Toast.jsx';

export default function Search() {
  const [params, setParams] = useSearchParams();
  const toast = useToast();
  const [q, setQ] = useState(params.get('q') || '');
  const [items, setItems] = useState(null);
  const [error, setError] = useState(null);
  const [reg, setReg] = useState({ url: '', name: '' });

  const search = useCallback((query) => {
    setItems(null);
    setError(null);
    api.get(`/products/search?q=${encodeURIComponent(query)}`).then((r) => setItems(r.items)).catch(setError);
  }, []);
  useEffect(() => { search(params.get('q') || ''); }, [params, search]);

  const register = async (e) => {
    e.preventDefault();
    try {
      const res = await api.post('/products', { url: reg.url.trim(), name: reg.name.trim() || null });
      toast(res.message, 'success');
      setReg({ url: '', name: '' });
      search(q.trim());
    } catch (err) { toast(err.message, 'danger'); }
  };

  return (
    <>
      <h1 className="text-3xl">상품 검색</h1>
      <form className="mt-4 flex gap-2" onSubmit={(e) => { e.preventDefault(); setParams(q.trim() ? { q: q.trim() } : {}); }}>
        <input className="input py-3" value={q} onChange={(e) => setQ(e.target.value)} placeholder="상품명·브랜드·카테고리·모델 번호" aria-label="검색어" />
        <button className="btn-primary px-6"><Icon name="fa-magnifying-glass" />검색</button>
      </form>
      <div className="mt-6"><ErrorBox error={error} /></div>
      {!items ? <Spinner text="검색 중…" /> : items.length ? (
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((p) => <ProductCard key={p.id} p={p}><LabelBadge value={p.label} /><span className="ml-auto font-semibold">{won(p.lowest_price)}</span></ProductCard>)}
        </div>) : <p className="mt-4 text-sm text-slate-500">검색 결과가 없습니다. 아래에서 상품 URL로 등록할 수 있습니다.</p>}

      <section className="card mt-10 p-6">
        <h2 className="text-lg"><Icon name="fa-link text-brand-600" className="mr-2" />상품 URL로 등록</h2>
        <p className="mt-1 text-sm text-slate-500">수집이 허용된 쇼핑몰의 상품 URL만 등록할 수 있습니다. 다음 수집 주기(매시 정각)부터 가격이 반영됩니다.</p>
        <form className="mt-4 grid gap-3 md:grid-cols-[2fr_1fr_auto]" onSubmit={register}>
          <input className="input" type="url" required placeholder="https://..." value={reg.url} onChange={(e) => setReg({ ...reg, url: e.target.value })} aria-label="상품 URL" />
          <input className="input" placeholder="상품 이름(선택)" value={reg.name} onChange={(e) => setReg({ ...reg, name: e.target.value })} aria-label="상품 이름" />
          <button className="btn-primary"><Icon name="fa-plus" />등록</button>
        </form>
      </section>
    </>
  );
}
