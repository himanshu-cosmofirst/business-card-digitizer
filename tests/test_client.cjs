const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const path = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');

const html = readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const ready = () => Response.json({ok: true, app: 'business-card-digitizer-v2'});

async function page() {
  const elements = new Map();
  const requests = [];
  const context = vm.createContext({
    location: {protocol: 'http:'},
    Response,
    crypto: {randomUUID: () => 'card-id'},
    setTimeout: () => {},
    document: {querySelector(selector) {
      if (!elements.has(selector)) elements.set(selector, {
        textContent: '', style: {}, classList: {
          values: new Set(),
          add(value) { this.values.add(value); },
          remove(value) { this.values.delete(value); },
          toggle() {},
        },
      });
      return elements.get(selector);
    }},
    fetch: async (url, options) => { requests.push({url, options}); return ready(); },
    FileReader: class {
      readAsDataURL() { this.result = 'data:image/jpeg;base64,aW1hZ2U='; this.onload(); }
    },
  });
  vm.runInContext(script, context);
  await vm.runInContext('health()', context);
  vm.runInContext('render=()=>{}', context);
  requests.length = 0;
  return {context, elements, requests, run: code => vm.runInContext(code, context)};
}

test('HTML API responses provide startup instructions without a JSON parse error', async () => {
  const p = await page();
  for (const status of [200, 404, 500]) {
    p.context.response = new Response('<!doctype html><html>Preview</html>', {
      status, headers: {'Content-Type': 'text/html'},
    });
    await assert.rejects(p.run('readApiJSON(response)'), error =>
      error.message.includes('http://127.0.0.1:8000') &&
      !error.message.includes('Unexpected token'));
  }
});

test('JSON error messages from the backend are preserved', async () => {
  const p = await page();
  p.context.response = Response.json({ok: false, error: 'Unsupported or damaged image.'}, {status: 400});
  await assert.rejects(p.run('readApiJSON(response)'), /Unsupported or damaged image/);
});

test('opening the HTML file directly does not attempt an API request', async () => {
  const p = await page();
  p.context.location.protocol = 'file:';
  await assert.rejects(p.run("apiFetch('/api/health')"), /start.command/);
  assert.equal(p.requests.length, 0);
});

test('static preview fails before sending the image and leaves a visible explanation', async () => {
  const p = await page();
  p.context.fetch = async url => {
    p.requests.push({url});
    return new Response('<!doctype html>', {headers: {'Content-Type': 'text/html'}});
  };
  await p.run("processFiles([{name:'IMG_1947 1.jpg'}])");
  assert.deepEqual(p.requests.map(r => r.url), ['/api/health']);
  assert.match(p.elements.get('#status').textContent, /http:\/\/127.0.0.1:8000/);
  assert.equal(p.run('state.busy'), false);
});

test('an HTML upload error counts as a failed photo and resets the upload state', async () => {
  const p = await page();
  p.context.fetch = async url => url === '/api/health' ? ready() :
    new Response('<!doctype html>', {status: 500, headers: {'Content-Type': 'text/html'}});
  await p.run("processFiles([{name:'IMG_1947 1.jpg'}])");
  assert.match(p.elements.get('#status').textContent, /1 photo failed.*IMG_1947 1.jpg/);
  assert.equal(p.run('state.cards.length'), 0);
  assert.equal(p.run('state.busy'), false);
  assert.ok(p.elements.get('#progress').classList.values.has('hidden'));
});

test('a successful upload keeps the source filename and produces a review card', async () => {
  const p = await page();
  p.context.fetch = async (url, options) => {
    p.requests.push({url, options});
    return url === '/api/health' ? ready() : Response.json({ok: true, cards: [{fields: {name: 'Jane Doe'}}]});
  };
  await p.run("processFiles([{name:'IMG_1947 1.jpg'}])");
  assert.equal(p.run('state.cards[0].sourceImage'), 'IMG_1947 1.jpg');
  assert.equal(p.run('state.cards[0].confirmed'), false);
  const upload = p.requests.find(r => r.url === '/api/process');
  assert.equal(JSON.parse(upload.options.body).name, 'IMG_1947 1.jpg');
  assert.equal(p.elements.get('#status').textContent, 'Done. 1 card detected.');
});

test('an HTML export response is not downloaded as an Excel workbook', async () => {
  const p = await page();
  p.context.fetch = async () => new Response('<!doctype html>', {headers: {'Content-Type': 'text/html'}});
  p.run("state.cards=[{confirmed:true, fields:{name:'Jane Doe'}, sourceImage:'card.jpg'}]");
  await p.elements.get('#export').onclick();
  assert.match(p.elements.get('#toast').textContent, /Unexpected Excel export response/);
});

test('hosted connection failures point to the online service', async () => {
  const p = await page();
  p.context.location.hostname = 'digitizer.onrender.com';
  // The message is chosen at page load, as it is in a browser.
  const online = vm.createContext({...p.context, location: {protocol: 'https:', hostname: 'digitizer.onrender.com'}});
  vm.runInContext(script, online);
  online.fetch = async () => { throw new Error('Network unavailable'); };
  await assert.rejects(vm.runInContext("apiFetch('/api/process')", online), error =>
    error.message.includes('online OCR server') && !error.message.includes('127.0.0.1'));
});
