import { DEMO, auth } from '../api.js';
import { $, initPage, qs, showError } from '../common.js';

await initPage({ requireAuth: false });

if (DEMO) {
  $('#demo-hint').innerHTML = `<div class="alert alert-info small">데모 모드: 아무 이메일·비밀번호로 로그인됩니다.<br>
    <code>admin@…</code>으로 시작하는 이메일은 관리자 화면까지 볼 수 있습니다.</div>`;
  $('#email').value = 'demo@buytiming.demo';
}

$('#login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = e.submitter;
  btn.disabled = true;
  $('#login-error').innerHTML = '';
  try {
    await auth.login($('#email').value.trim(), $('#password').value || (DEMO ? 'demo' : ''));
    location.href = qs('next') || 'index.html';
  } catch (err) {
    showError(err, $('#login-error'));
  } finally {
    btn.disabled = false;
  }
});
