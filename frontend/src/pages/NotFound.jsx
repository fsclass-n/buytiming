import { Link } from 'react-router-dom';
import { Icon } from '../components/ui.jsx';

export default function NotFound() {
  return (
    <div className="py-20 text-center">
      <Icon name="fa-compass text-6xl text-brand-500" />
      <h1 className="mt-4 text-3xl">페이지를 찾을 수 없습니다</h1>
      <p className="mt-2 text-slate-500">주소가 바뀌었거나 삭제된 페이지입니다.</p>
      <Link className="btn-primary mt-6" to="/"><Icon name="fa-house" />홈으로</Link>
    </div>
  );
}
