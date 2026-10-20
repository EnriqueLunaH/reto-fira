// Exercise the production request function with a deterministic clock and no server.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../static/js/risk.js'), 'utf8');
const start = source.indexOf('  async function request(');
const end = source.indexOf('\n  function setBusy', start);
assert.ok(start >= 0 && end > start, 'The production request function must be present.');

function fixture(fetch) {
  let now = 0, nextId = 0;
  const pending = new Map(), scheduled = [], cleared = [], calls = [];
  const context = vm.createContext({
    AbortController,
    fetch(url, options) {
      calls.push({url, options});
      return fetch(url, options);
    },
    setTimeout(callback, delay) {
      const id = ++nextId;
      pending.set(id, {callback, at: now + delay});
      scheduled.push({id, delay});
      return id;
    },
    clearTimeout(id) {
      cleared.push(id);
      pending.delete(id);
    }
  });
  vm.runInContext(source.slice(start, end) + '\nthis.request = request;', context);
  return {
    request: context.request, calls, scheduled, cleared, pending,
    advance(milliseconds) {
      now += milliseconds;
      for (const [id, timer] of pending) {
        if (timer.at <= now) {
          pending.delete(id);
          timer.callback();
        }
      }
    },
    assertCleaned() {
      assert.deepEqual(scheduled.map(timer => timer.delay), [15000]);
      assert.deepEqual(cleared, [scheduled[0].id]);
      assert.equal(pending.size, 0);
    }
  };
}

const response = (payload, status = 200) => ({
  status, ok: status >= 200 && status < 300, json: async () => payload
});
const flush = () => new Promise(resolve => setImmediate(resolve));

test('success preserves request options, returns JSON and clears the deadline', async () => {
  const payload = {scenario: {mean_margin_per_ha: 950.5}};
  const f = fixture(async () => response(payload));
  const result = await f.request('/api/risk/simulate', {
    method: 'POST', body: 'price_per_t=7375', headers: {'Content-Type': 'application/x-www-form-urlencoded'}
  });
  assert.equal(result, payload);
  assert.equal(f.calls[0].url, '/api/risk/simulate');
  assert.equal(f.calls[0].options.credentials, 'same-origin');
  assert.equal(f.calls[0].options.method, 'POST');
  assert.equal(f.calls[0].options.body, 'price_per_t=7375');
  assert.equal(f.calls[0].options.headers['Content-Type'], 'application/x-www-form-urlencoded');
  assert.equal(f.calls[0].options.signal.aborted, false);
  f.assertCleaned();
  f.advance(15000);
  assert.equal(f.calls[0].options.signal.aborted, false, 'A completed request must not be aborted later.');
});

test('a slow request can finish before the deadline', async () => {
  let resolveFetch;
  const f = fixture(() => new Promise(resolve => { resolveFetch = resolve; }));
  const pending = f.request('/api/risk/context');
  f.advance(14999);
  assert.equal(f.calls[0].options.signal.aborted, false);
  resolveFetch(response({parcels: []}));
  assert.deepEqual(await pending, {parcels: []});
  f.assertCleaned();
});

test('a fetch that never responds times out and aborts at 15 seconds', async () => {
  const f = fixture(() => new Promise(() => {}));
  const rejection = assert.rejects(f.request('/api/risk/context'), /La solicitud tardó más de 15 segundos\. Vuelve a intentar\./);
  f.advance(14999);
  assert.equal(f.calls[0].options.signal.aborted, false);
  f.advance(1);
  await rejection;
  assert.equal(f.calls[0].options.signal.aborted, true);
  f.assertCleaned();
});

test('the same deadline covers a stalled JSON body after headers arrive', async () => {
  let readingBody = false;
  const f = fixture(async () => ({status: 200, ok: true, json() {
    readingBody = true;
    return new Promise(() => {});
  }}));
  const rejection = assert.rejects(f.request('/api/risk/simulate'), /15 segundos/);
  await flush();
  assert.equal(readingBody, true);
  f.advance(15000);
  await rejection;
  assert.equal(f.calls[0].options.signal.aborted, true);
  f.assertCleaned();
});

test('JSON reading uses the remaining time instead of starting a second deadline', async () => {
  let resolveFetch, readingBody = false;
  const f = fixture(() => new Promise(resolve => { resolveFetch = resolve; }));
  const rejection = assert.rejects(f.request('/api/risk/simulate'), /15 segundos/);
  f.advance(14000);
  resolveFetch({status: 200, ok: true, json() {
    readingBody = true;
    return new Promise(() => {});
  }});
  await flush();
  assert.equal(readingBody, true);
  f.advance(1000);
  await rejection;
  f.assertCleaned();
});

test('abort-triggered network rejection retains the timeout message', async () => {
  const f = fixture((url, {signal}) => new Promise((resolve, reject) => {
    signal.addEventListener('abort', () => reject(new Error('aborted')), {once: true});
  }));
  const rejection = assert.rejects(f.request('/api/risk/context'), /15 segundos/);
  f.advance(15000);
  await rejection;
  f.assertCleaned();
});

const failures = [
  ['network rejection', async () => { throw new Error('offline'); }, 'No se pudo conectar con el servidor. Comprueba la conexión y vuelve a intentar.'],
  ['invalid JSON', async () => ({status: 200, ok: true, json: async () => { throw new SyntaxError('invalid'); }}), 'El servidor no devolvió un resultado válido. Vuelve a intentar.'],
  ['expired session', async () => response({}, 401), 'Tu sesión terminó. Vuelve a iniciar sesión.'],
  ['forbidden request', async () => response({}, 403), 'No se pudo autorizar la solicitud. Recarga la página y vuelve a intentar.'],
  ['HTTP error detail', async () => response({error: 'Precio inválido.'}, 400), 'Precio inválido.'],
  ['HTTP message detail', async () => response({message: 'Servicio ocupado.'}, 503), 'Servicio ocupado.'],
  ['HTTP fallback', async () => response({}, 500), 'No se pudo completar el cálculo. Revisa los datos y vuelve a intentar.']
];
for (const [name, fetch, message] of failures) {
  test(`${name} preserves its message and clears the deadline`, async () => {
    const f = fixture(fetch);
    await assert.rejects(f.request('/api/risk/simulate'), error => error.message === message);
    assert.equal(f.calls[0].options.signal.aborted, false);
    f.assertCleaned();
  });
}
