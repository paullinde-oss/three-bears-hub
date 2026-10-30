import { initializeApp, deleteApp } from 'firebase/app';
import { getAuth, connectAuthEmulator, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut } from 'firebase/auth';
import { getDatabase, connectDatabaseEmulator, ref, get, set, update } from 'firebase/database';
const DOMAIN = '@three-bears-hub.firebaseapp.com';
let n = 0, fails = 0;
function mk(name) {
  const app = initializeApp({ apiKey: 'fake', projectId: 'demo-tb', databaseURL: 'http://127.0.0.1:9000?ns=demo-tb-default-rtdb' }, name);
  const auth = getAuth(app); connectAuthEmulator(auth, 'http://127.0.0.1:9099', { disableWarnings: true });
  const db = getDatabase(app); connectDatabaseEmulator(db, '127.0.0.1', 9000);
  return { app, auth, db };
}
async function expect(label, shouldPass, fn) {
  n++;
  let ok = true, err = '';
  try { await fn(); } catch (e) { ok = false; err = e.code || e.message; }
  const good = ok === shouldPass;
  if (!good) fails++;
  console.log(`${good ? 'PASS' : 'FAIL'}  ${shouldPass ? 'allowed' : 'denied '}  ${label}${!ok ? '  (' + err + ')' : ''}`);
}
const ENV = 'hubdev';
const admin = mk('admin'), player = mk('player'), stranger = mk('stranger'), anon = mk('anon');
// --- bootstrap: admin account + admin flag written with emulator admin access (simulates the console step)
const adminCred = await createUserWithEmailAndPassword(admin.auth, '6040000001' + DOMAIN, 'adminpass1');
const adminUid = adminCred.user.uid;
await fetch(`http://127.0.0.1:9000/${ENV}/admins/${adminUid}.json?ns=demo-tb-default-rtdb`, { method: 'PUT', headers: { Authorization: 'Bearer owner' }, body: 'true' });
await fetch(`http://127.0.0.1:9000/${ENV}/three-bears-state-v3.json?ns=demo-tb-default-rtdb`, { method: 'PUT', headers: { Authorization: 'Bearer owner' }, body: JSON.stringify({ value: '{"x":1}', ts: 1 }) });

console.log('\n-- Logged-out visitor');
await expect('read team state', true, () => get(ref(anon.db, `${ENV}/three-bears-state-v3`)));
await expect('read avatars', true, () => get(ref(anon.db, `${ENV}/avatars`)));
await expect('write team state', false, () => set(ref(anon.db, `${ENV}/three-bears-state-v3`), { value: 'hack', ts: 2 }));
await expect('read phone numbers', false, () => get(ref(anon.db, `${ENV}/phoneIndex`)));
await expect('read users', false, () => get(ref(anon.db, `${ENV}/users`)));

console.log('\n-- Admin');
await expect('write team state', true, () => set(ref(admin.db, `${ENV}/three-bears-state-v3`), { value: '{"x":2}', ts: 2 }));
await expect('register phone 6045551234 -> player P1', true, () => set(ref(admin.db, `${ENV}/phoneIndex/6045551234`), 'P1'));
await expect('reject malformed phone key', false, () => set(ref(admin.db, `${ENV}/phoneIndex/12345`), 'P9'));
await expect('read all phone numbers', true, () => get(ref(admin.db, `${ENV}/phoneIndex`)));
await expect('link own login to player P0', true, () => set(ref(admin.db, `${ENV}/users/${adminUid}/playerId`), 'P0'));
await expect('edit any avatar (P1)', true, () => set(ref(admin.db, `${ENV}/avatars/P1`), { v: 1, hair: 'mullet' }));

console.log('\n-- Player P1 first login (account created with the default password, then claims their player)');
const pCred = await createUserWithEmailAndPassword(player.auth, '6045551234' + DOMAIN, 'bears2027');
const pUid = pCred.user.uid;
await expect('read own phone index entry', true, () => get(ref(player.db, `${ENV}/phoneIndex/6045551234`)));
await expect("read someone else's phone entry", false, () => get(ref(player.db, `${ENV}/phoneIndex/6040000001`)));
await expect('read all phone numbers', false, () => get(ref(player.db, `${ENV}/phoneIndex`)));
await expect('claim the WRONG player (P2)', false, () => set(ref(player.db, `${ENV}/users/${pUid}/playerId`), 'P2'));
await expect('claim own player (P1)', true, () => set(ref(player.db, `${ENV}/users/${pUid}/playerId`), 'P1'));
await expect('re-point claim to P2 afterwards', false, () => set(ref(player.db, `${ENV}/users/${pUid}/playerId`), 'P2'));
await expect('set pwChanged flag', true, () => set(ref(player.db, `${ENV}/users/${pUid}/pwChanged`), true));
await expect('read own user record', true, () => get(ref(player.db, `${ENV}/users/${pUid}`)));
await expect("read admin's user record", false, () => get(ref(player.db, `${ENV}/users/${adminUid}`)));
await expect('save own avatar', true, () => set(ref(player.db, `${ENV}/avatars/P1`), { v: 1, hair: 'buzz', hairColor: 'blond', updatedAt: 5 }));
await expect('save avatar with unknown field', false, () => set(ref(player.db, `${ENV}/avatars/P1`), { v: 1, evil: 'x' }));
await expect('save avatar with huge value', false, () => set(ref(player.db, `${ENV}/avatars/P1`), { v: 1, hair: 'x'.repeat(200) }));
await expect("edit someone else's avatar (P0)", false, () => set(ref(player.db, `${ENV}/avatars/P0`), { v: 1, hair: 'buzz' }));
await expect('write team state (beers/payments)', false, () => set(ref(player.db, `${ENV}/three-bears-state-v3`), { value: 'x', ts: 9 }));
await expect('make self admin', false, () => set(ref(player.db, `${ENV}/admins/${pUid}`), true));
await expect('register a phone number', false, () => set(ref(player.db, `${ENV}/phoneIndex/6049999999`), 'P1'));

console.log('\n-- Stranger with an unregistered phone number');
const sCred = await createUserWithEmailAndPassword(stranger.auth, '6047777777' + DOMAIN, 'whatever1');
await expect('claim player P1', false, () => set(ref(stranger.db, `${ENV}/users/${sCred.user.uid}/playerId`), 'P1'));
await expect('read P1 phone entry', false, () => get(ref(stranger.db, `${ENV}/phoneIndex/6045551234`)));
await expect('edit avatar P1', false, () => set(ref(stranger.db, `${ENV}/avatars/P1`), { v: 1 }));

console.log('\n-- Live data path (hub) behaves the same, other roots are refused');
await expect('admin of hubdev cannot write hub state', false, () => set(ref(admin.db, `hub/three-bears-state-v3`), { value: 'x', ts: 1 }));
await expect('anyone reads hub state', true, () => get(ref(anon.db, `hub/three-bears-state-v3`)));
await expect('write to an unknown root', false, () => set(ref(admin.db, `other/admins/${adminUid}`), true));

console.log(`\n${n - fails}/${n} checks behaved as expected`);
for (const c of [admin, player, stranger, anon]) await deleteApp(c.app);
process.exit(fails ? 1 : 0);
