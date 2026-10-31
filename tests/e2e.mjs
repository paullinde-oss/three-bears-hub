// End-to-end: real app page + Firebase Auth/Database emulators with the real rules. Nothing touches production:
// every request except localhost is aborted, and the Firebase SDK is pointed at the emulators.
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT || 'playwright');
import fs from 'fs';
// FB: folder containing node_modules/firebase@8.10.1 (served in place of the CDN copy). SHOTS: screenshot folder.
const FB = process.env.FB || '.', SHOTS = process.env.SHOTS || '.';
const NS = 'demo-tb-default-rtdb', DB = `http://127.0.0.1:9000`, AUTH = 'http://127.0.0.1:9099';
const DOMAIN = '@three-bears-hub.firebaseapp.com';
const owner = { Authorization: 'Bearer owner', 'Content-Type': 'application/json' };
const put = (path, v) => fetch(`${DB}/${path}.json?ns=${NS}`, { method: 'PUT', headers: owner, body: JSON.stringify(v) });
const getv = async path => (await fetch(`${DB}/${path}.json?ns=${NS}`, { headers: owner })).json();
let fails = 0; const check = (label, ok, extra = '') => { if (!ok) fails++; console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${extra ? '  ' + extra : ''}`); };

// --- seed: admin login (Paul), season with Paul + Ben, Ben's phone registered
const su = await (await fetch(`${AUTH}/identitytoolkit.googleapis.com/v1/accounts:signUp?key=fake`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: '6040000001' + DOMAIN, password: 'adminpass1', returnSecureToken: true }) })).json();
const S = 'S1';
const state = { schemaVersion: 3, team: { name: 'Three Bears', league: 'Test' }, pricePerBeer: 3, adminPin: '1234', activeSeasonId: S,
  seasons: [{ id: S, name: 'SUMMER 2026', teamFees: 0, playoffMinGames: 4, fullTimeDefault: 467, partTimeDefault: 233, archived: false }],
  players: [{ id: 'pA', name: 'Paul', position: 'F', startingBeerBalance: 0 }, { id: 'pB', name: 'Ben', position: 'F/D', startingBeerBalance: 10 }],
  rosters: { [S]: { pA: { type: 'full', jerseyNumber: '7', allocated: 467 }, pB: { type: 'full', jerseyNumber: '16', allocated: 467 } } },
  games: [{ id: 'g1', seasonId: S, number: 8, date: '2026-07-01', opponent: 'Icemen' }], attendance: { g1: { pA: 'in', pB: 'in' } },
  beers: { g1: { pB: 2 } }, payments: [], lineups: {} };
await put('hubdev', { 'three-bears-state-v3': { value: JSON.stringify(state), ts: 1 }, admins: { [su.localId]: true },
  users: { [su.localId]: { playerId: 'pA', pwChanged: true } }, phoneIndex: { '6045551234': 'pB' } });

const b = await chromium.launch({ args: ['--disable-features=LocalNetworkAccessChecks,BlockInsecurePrivateNetworkRequests,PrivateNetworkAccessChecks'] });
const ctx = await b.newContext({ viewport: { width: 1100, height: 900 } });
const pg = await ctx.newPage();
const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !m.text().includes('ERR_FAILED')) console.log('  console:', m.text().slice(0,200)); });
const V8 = `${FB}/node_modules/firebase/`;
await ctx.route('**/*', async r => {
  const u = new URL(r.request().url());
  if (u.hostname === 'www.gstatic.com' && u.pathname.includes('/firebasejs/8.10.1/'))
    return r.fulfill({ contentType: 'application/javascript', body: fs.readFileSync(V8 + u.pathname.split('/').pop()) });
  if (['localhost','127.0.0.1'].includes(u.hostname) && u.port === '8765' && u.pathname.endsWith('/index.html')) {
    const res = await r.fetch(); let html = await res.text();
    // point the app's Firebase at the local emulators
    html = html.replace('<script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-auth.js"></script>', `<script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-auth.js"></script><script>
      (function(){ const init = firebase.initializeApp.bind(firebase);
        firebase.initializeApp = cfg => { const app = init(Object.assign({}, cfg, { databaseURL: '${DB}?ns=${NS}' }));
          app.database().useEmulator('127.0.0.1', 9000); app.auth().useEmulator('${AUTH}'); return app; }; })();</script>`);
    return r.fulfill({ response: res, body: html, headers: Object.assign({}, res.headers(), { 'content-type': 'text/html' }) });
  }
  if (['localhost', '127.0.0.1'].includes(u.hostname)) return r.continue();
  return r.abort();
});
const shot = n => pg.screenshot({ path: `${SHOTS}/${n}.png` });
const modalText = async () => (await pg.locator('#modal').innerText()).replace(/\s+/g, ' ');
await pg.goto('http://127.0.0.1:8765/index.html?dev=1'); await pg.waitForTimeout(2500);
await pg.evaluate(() => document.getElementById('splashScreen')?.remove());

console.log('-- logged out');
console.log('  state:', await pg.evaluate(() => JSON.stringify({ root: DATA_ROOT, players: state.players.length, fb: _firebaseReady, err: _firebaseError })));
check('pill says Log In', (await pg.locator('#adminPill').innerText()).includes('Log In'));
check('dashboard shows players', await pg.locator('tr[data-pid="pB"]').count() === 1);
await pg.locator('tr[data-pid="pB"] .stk-3').click(); await pg.waitForTimeout(300);
check('clicking a player asks to log in', (await modalText()).includes('Log in to see player profiles'));
await pg.evaluate(() => closeModal());

console.log('-- admin logs in');
await pg.click('#adminPill'); await pg.fill('#loginPhone', '604-000-0001'); await pg.fill('#loginPw', 'adminpass1'); await pg.click('#loginBtn');
await pg.waitForTimeout(2500);
check('pill shows admin', (await pg.locator('#adminPill').innerText()).includes('Paul · Admin'), await pg.locator('#adminPill').innerText());
await pg.evaluate(() => setActiveTab('settings')); await pg.waitForTimeout(400);
await pg.fill('#teamPwInput', 'bears2027'); await pg.click('text=Set Team Password'); await pg.waitForTimeout(800);
const st1 = JSON.parse((await getv('hubdev/three-bears-state-v3')).value);
check('team password hash saved by admin', !!st1.loginDefaultHash);
check('old PIN removed from public data', st1.adminPin === undefined);
await shot('e2e_settings_admin');
await pg.evaluate(() => openEditPlayer('pB')); await pg.waitForTimeout(300);
await pg.check('input[name=captain]'); await pg.click('#editPlayerForm button[type=submit]'); await pg.waitForTimeout(800);
const st2 = JSON.parse((await getv('hubdev/three-bears-state-v3')).value);
check('admin set Ben as captain', st2.rosters[S].pB.captain === true);
await pg.evaluate(() => logOut()); await pg.waitForTimeout(800);

console.log('-- Ben logs in for the first time with the team password');
await pg.click('#adminPill'); await pg.fill('#loginPhone', '(604) 555-1234'); await pg.fill('#loginPw', 'bears2027'); await pg.click('#loginBtn');
await pg.waitForTimeout(3000);
check('asked to pick own password', (await modalText()).includes('Pick your password'));
await shot('e2e_first_login');
await pg.fill('#newPw1', 'bears2027'); await pg.fill('#newPw2', 'bears2027'); await pg.click('text=Save Password'); await pg.waitForTimeout(500);
check('team password rejected as personal password', (await modalText()).includes('other than the team password'));
await pg.fill('#newPw1', 'benpass99'); await pg.fill('#newPw2', 'benpass99'); await pg.click('text=Save Password'); await pg.waitForTimeout(1500);
const users = await getv('hubdev/users');
const benUid = Object.keys(users).find(u => users[u].playerId === 'pB');
check('Ben login linked to roster player', !!benUid && users[benUid].pwChanged === true);
check('pill shows Ben (not admin)', (await pg.locator('#adminPill').innerText()).trim() === '👤 Ben', await pg.locator('#adminPill').innerText());
check('no admin buttons for Ben', await pg.locator('text=+ Add Player').count() === 0);

console.log('-- Ben views his profile');
await pg.click('#adminPill'); await pg.click('text=My Profile'); await pg.waitForTimeout(400);
const prof = await modalText();
check('profile shows season folder + All-time', prof.includes('SUMMER 2026') && prof.includes('All-time'));
check('profile shows captain badge', await pg.locator('.profile-info h3 span[title=Captain]').count() === 1);
await shot('e2e_profile');
await pg.evaluate(() => closeModal());
const ok = await pg.evaluate(async () => saveState());
check("Ben can't save team data", ok === false);

console.log('-- log out / log back in with personal password');
await pg.evaluate(() => logOut()); await pg.waitForTimeout(800);
await pg.click('#adminPill'); await pg.fill('#loginPhone', '6045551234'); await pg.fill('#loginPw', 'bears2027'); await pg.click('#loginBtn'); await pg.waitForTimeout(2000);
check('team password no longer works for Ben', (await pg.locator('#loginErr').innerText()).includes('Wrong'));
await pg.fill('#loginPw', 'benpass99'); await pg.click('#loginBtn'); await pg.waitForTimeout(2500);
check('personal password works', (await pg.locator('#adminPill').innerText()).includes('Ben'));

console.log('-- stranger with unregistered number + team password');
await pg.evaluate(() => logOut()); await pg.waitForTimeout(800);
await pg.click('#adminPill'); await pg.fill('#loginPhone', '6047777777'); await pg.fill('#loginPw', 'bears2027'); await pg.click('#loginBtn'); await pg.waitForTimeout(3000);
check('stranger is refused and logged out', (await modalText()).includes("isn't on the roster") && (await pg.locator('#adminPill').innerText()).includes('Log In'));
console.log('page errors:', errs);
await b.close();
console.log(fails ? `${fails} FAILED` : 'ALL PASSED');
process.exit(fails || errs.length ? 1 : 0);
