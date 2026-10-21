import { api, auth } from '../api.js';
import { $, initPage, showError } from '../common.js';

await initPage({ requireAuth: false });

$('#signup-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = e.target;
  if (!form.checkValidity()) {
    form.classList.add('was-validated');
    return;
  }
  const btn = e.submitter;
  btn.disabled = true;
  $('#signup-error').innerHTML = '';
  const body = { name: $('#name').value.trim(), email: $('#email').value.trim(), password: $('#password').value };
  try {
    await api.post('/auth/signup', body);
    await auth.login(body.email, body.password);
    location.href = 'index.html';
  } catch (err) {
    showError(err, $('#signup-error'));
  } finally {
    btn.disabled = false;
  }
});
