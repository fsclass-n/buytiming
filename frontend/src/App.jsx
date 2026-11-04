import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './lib/auth.jsx';
import { ToastProvider } from './components/Toast.jsx';
import Layout from './components/Layout.jsx';
import { Spinner } from './components/ui.jsx';
import Home from './pages/Home.jsx';
import Login from './pages/Login.jsx';
import Signup from './pages/Signup.jsx';
import OAuthCallback from './pages/OAuthCallback.jsx';
import Search from './pages/Search.jsx';
import Product from './pages/Product.jsx';
import Chat from './pages/Chat.jsx';
import Watchlist from './pages/Watchlist.jsx';
import Alerts from './pages/Alerts.jsx';
import Admin from './pages/Admin.jsx';
import AdminAI from './pages/AdminAI.jsx';
import AdminUsers from './pages/AdminUsers.jsx';
import NotFound from './pages/NotFound.jsx';

/** 로그인이 필요한 화면. 데모 모드에서는 데모 계정으로 자동 로그인한다. admin이면 관리자만 */
function Protected({ children, admin = false }) {
  const { user, ready } = useAuth();
  const loc = useLocation();
  if (!ready) return <Spinner />;
  if (!user) return <Navigate to={`/login?next=${encodeURIComponent(loc.pathname + loc.search)}`} replace />;
  if (admin && user.role !== 'ADMIN') {
    return <div className="card p-6 text-amber-700"><i className="fa-solid fa-lock mr-2" />관리자만 접근할 수 있는 화면입니다.</div>;
  }
  return children;
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/oauth/callback" element={<OAuthCallback />} />
          <Route element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="search" element={<Protected><Search /></Protected>} />
            <Route path="product/:id" element={<Protected><Product /></Protected>} />
            <Route path="chat/:id" element={<Protected><Chat /></Protected>} />
            <Route path="watchlist" element={<Protected><Watchlist /></Protected>} />
            <Route path="alerts" element={<Protected><Alerts /></Protected>} />
            <Route path="admin" element={<Protected admin><Admin /></Protected>} />
            <Route path="admin/ai" element={<Protected admin><AdminAI /></Protected>} />
            <Route path="admin/users" element={<Protected admin><AdminUsers /></Protected>} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </AuthProvider>
    </ToastProvider>
  );
}
