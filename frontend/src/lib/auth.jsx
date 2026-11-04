import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { DEMO, api, auth } from './api.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(auth.user());
  const [ready, setReady] = useState(!DEMO || !!auth.user());

  const finish = useCallback((res) => {
    auth.save(res.access_token, res.user);
    setUser(res.user);
    return res.user;
  }, []);

  const login = useCallback((email, password) => api.post('/auth/login', { email, password }).then(finish), [finish]);
  const demoLogin = useCallback((kind = 'user') => api.post('/auth/demo-login', { kind }).then(finish), [finish]);
  const logout = useCallback(() => { auth.clear(); setUser(null); }, []);

  useEffect(() => {
    // 데모 모드: 보호 화면을 바로 볼 수 있게 데모 사용자로 자동 로그인
    if (DEMO && !auth.user()) demoLogin('user').finally(() => setReady(true));
    const onLogout = () => setUser(null);
    window.addEventListener('pt:logout', onLogout);
    return () => window.removeEventListener('pt:logout', onLogout);
  }, [demoLogin]);

  return <AuthContext.Provider value={{ user, ready, login, demoLogin, logout, finish, setUser }}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
