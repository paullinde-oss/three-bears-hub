/*
 * AvatarKit: a self-contained pixel avatar renderer and editor.
 *
 * Usage:
 *   await AvatarKit.load('avatar/parts.json');            // or pass the parsed object
 *   const url = AvatarKit.toDataURL(config, { crop: true, scale: 3, number: 7, captain: true });
 *   AvatarKit.openEditor({ config, number: 7, body: 'goalie', onSave: cfg => ... });
 *
 * Parts format (parts.json): every part is { x, y, rows, pal? } on a size[0] x size[1] canvas.
 * In rows, '.' is transparent, '0'-'4' are shade levels tinted with the slot's colour ramp
 * (dark -> light), and any other character indexes into the part's own `pal` list.
 * No dependencies; drop the avatar/ folder into any project.
 */
(function (global) {
  'use strict';

  const FIXED_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!#$%&*+<=>?@^~';
  let P = null;                // loaded parts
  const cache = new Map();     // rendered data URLs keyed by config + options

  // Which config key picks the colour ramp for each tint channel
  const TINT_KEY = { skin: ['skin', 'skin'], eyes: ['eyes', 'eyeColor'], hair: ['hair', 'hairColor'],
                     facialHair: ['hair', 'facialHairColor'], gear: ['gear', 'hatColor'] };

  const DEFAULTS = {
    v: 1, skin: 'light', eyes: 'normal', eyeColor: 'brown', brows: 'normal', mouth: 'smile',
    hair: 'crew', hairColor: 'brown', facialHair: null, facialHairColor: 'brown',
    hat: null, hatColor: 'navy', glasses: null, earring: null
  };

  function hexToRgb(h) { const n = parseInt(h.slice(1), 16); return [n >> 16, (n >> 8) & 255, n & 255]; }

  async function load(src) {
    P = typeof src === 'string' ? await (await fetch(src)).json() : src;
    // pre-parse colours
    for (const kind of Object.keys(P.ramps))
      for (const name of Object.keys(P.ramps[kind]))
        P.ramps[kind][name] = P.ramps[kind][name].map(c => typeof c === 'string' ? hexToRgb(c) : c);
    for (const slot of Object.values(P.slots))
      for (const part of Object.values(slot.options || {}))
        if (part.pal) part._pal = part.pal.map(hexToRgb);
    cache.clear();
    return P;
  }

  function normalize(cfg) {
    const c = Object.assign({}, DEFAULTS, cfg || {});
    const ok = (slot, v) => v == null ? (P.slots[slot].optional ? null : Object.keys(P.slots[slot].options)[0])
                                      : (P.slots[slot].options[v] ? v : Object.keys(P.slots[slot].options)[0]);
    c.eyes = ok('eyes', c.eyes); c.brows = ok('brows', c.brows); c.mouth = ok('mouth', c.mouth);
    for (const s of ['hair', 'facialHair', 'hat', 'glasses', 'earring']) c[s] = c[s] == null ? null : (P.slots[s].options[c[s]] ? c[s] : null);
    const ramp = (kind, v, d) => P.ramps[kind][v] ? v : d;
    c.skin = ramp('skin', c.skin, 'light'); c.eyeColor = ramp('eyes', c.eyeColor, 'brown');
    c.hairColor = ramp('hair', c.hairColor, 'brown'); c.facialHairColor = ramp('hair', c.facialHairColor, c.hairColor);
    c.hatColor = ramp('gear', c.hatColor, 'navy');
    return c;
  }

  function blit(buf, W, part, ramp, clipAbove) {
    const pal = part._pal;
    for (let j = 0; j < part.rows.length; j++) {
      const y = part.y + j;
      if (clipAbove != null && y < clipAbove) continue;
      const row = part.rows[j];
      for (let i = 0; i < row.length; i++) {
        const ch = row[i];
        if (ch === '.') continue;
        let rgb;
        if (ch >= '0' && ch <= '4') { if (!ramp) continue; rgb = ramp[ch.charCodeAt(0) - 48]; }
        else rgb = pal[FIXED_CHARS.indexOf(ch)];
        if (!rgb) continue;
        const o = (y * W + part.x + i) * 4;
        buf[o] = rgb[0]; buf[o + 1] = rgb[1]; buf[o + 2] = rgb[2]; buf[o + 3] = 255;
      }
    }
  }

  function drawNumber(buf, W, n) {
    const spec = P.slots.number; const s = String(n).replace(/\D/g, '').slice(0, 2);
    if (!s) return;
    const [x0, y0] = s.length === 2 ? spec.at.two : spec.at.one;
    const rgb = hexToRgb(spec.color);
    [...s].forEach((d, k) => spec.digits[d].forEach((row, j) => [...row].forEach((c, i) => {
      if (c !== '1') return;
      const o = ((y0 + j) * W + x0 + k * spec.spacing + i) * 4;
      buf[o] = rgb[0]; buf[o + 1] = rgb[1]; buf[o + 2] = rgb[2]; buf[o + 3] = 255;
    })));
  }

  // Render to a size x size canvas. opts: { body: 'skater'|'goalie', number, captain }
  function render(cfg, opts = {}) {
    if (!P) throw new Error('AvatarKit.load() first');
    const c = normalize(cfg); const [W, H] = P.size;
    const buf = new Uint8ClampedArray(W * H * 4);
    const rampFor = slot => { const t = TINT_KEY[P.slots[slot].tint]; return t ? P.ramps[t[0]][c[t[1]]] : null; };
    for (const slot of P.order) {
      const def = P.slots[slot];
      if (slot === 'number') { if (opts.number != null && opts.number !== '') drawNumber(buf, W, opts.number); continue; }
      if (slot === 'captain') { if (opts.captain) blit(buf, W, def.options.C, null); continue; }
      let key;
      if (slot === 'body') key = def.options[opts.body] ? opts.body : 'skater';
      else if (def.options.default) key = 'default';
      else key = c[slot];
      if (!key) continue;
      const clip = slot === 'hair' && c.hat ? P.slots.hat.clipHairAbove : null;
      blit(buf, W, def.options[key], rampFor(slot), clip);
    }
    const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
    cv.getContext('2d').putImageData(new ImageData(buf, W, H), 0, 0);
    return cv;
  }

  // PNG data URL. opts.crop = true gives the head-and-shoulders profile crop.
  function toDataURL(cfg, opts = {}) {
    const key = JSON.stringify([normalize(cfg), opts.body || 'skater', opts.number ?? '', !!opts.captain, !!opts.crop, opts.scale || 1]);
    if (cache.has(key)) return cache.get(key);
    const src = render(cfg, opts);
    const r = opts.crop ? P.crop : { x: 0, y: 0, w: P.size[0], h: P.size[1] };
    const s = opts.scale || 1;
    const out = document.createElement('canvas'); out.width = r.w * s; out.height = r.h * s;
    const ctx = out.getContext('2d'); ctx.imageSmoothingEnabled = false;
    ctx.drawImage(src, r.x, r.y, r.w, r.h, 0, 0, r.w * s, r.h * s);
    const url = out.toDataURL('image/png');
    if (cache.size > 400) cache.clear();
    cache.set(key, url);
    return url;
  }

  function random() {
    const pick = a => a[Math.floor(Math.random() * a.length)];
    const opt = s => Object.keys(P.slots[s].options);
    const hairColor = pick(Object.keys(P.ramps.hair));
    return normalize({
      skin: pick(Object.keys(P.ramps.skin)), eyes: pick(opt('eyes')), eyeColor: pick(Object.keys(P.ramps.eyes)),
      brows: pick(opt('brows')), mouth: pick(opt('mouth')),
      hair: Math.random() < 0.1 ? null : pick(opt('hair')), hairColor,
      facialHair: Math.random() < 0.4 ? null : pick(opt('facialHair')), facialHairColor: hairColor,
      hat: Math.random() < 0.75 ? null : pick(opt('hat')), hatColor: pick(Object.keys(P.ramps.gear)),
      glasses: Math.random() < 0.8 ? null : pick(opt('glasses')), earring: Math.random() < 0.85 ? null : pick(opt('earring'))
    });
  }

  // ---------------- Editor ----------------
  const CSS = `
  .avk-ov{position:fixed;inset:0;background:rgba(10,12,18,.72);z-index:10050;display:flex;align-items:center;justify-content:center;padding:12px;font-family:system-ui,-apple-system,'Segoe UI',sans-serif}
  .avk-panel{background:#f6f2e8;color:#1a1a1a;border-radius:14px;width:100%;max-width:820px;max-height:96vh;display:flex;flex-direction:column;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.45)}
  .avk-head{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-bottom:1px solid #ddd3bf}
  .avk-head h3{margin:0;font-size:18px;font-weight:800}
  .avk-x{background:none;border:none;font-size:24px;cursor:pointer;color:#777;line-height:1}
  .avk-body{display:flex;gap:14px;padding:14px 16px;overflow:auto;flex:1;min-height:0}
  .avk-stage{flex:0 0 300px;display:flex;flex-direction:column;align-items:center;gap:10px}
  .avk-full{width:300px;height:300px;image-rendering:pixelated;background:radial-gradient(circle at 50% 40%,#e7eef4,#c9d7e2);border-radius:12px;border:1px solid #c5d3df}
  .avk-crop-row{display:flex;align-items:center;gap:10px;font-size:12px;color:#666}
  .avk-crop{width:72px;height:72px;border-radius:50%;image-rendering:pixelated;background:#f2ede2;border:2px solid #ddd3bf}
  .avk-side{flex:1;min-width:0;display:flex;flex-direction:column}
  .avk-tabs{display:flex;gap:4px;overflow-x:auto;border-bottom:1px solid #ddd3bf;margin-bottom:10px;scrollbar-width:none}
  .avk-tabs::-webkit-scrollbar{display:none}
  .avk-tab{background:none;border:none;padding:8px 10px;font-size:13px;font-weight:600;color:#777;cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap}
  .avk-tab.on{color:#1a1a1a;border-bottom-color:#c75a2c}
  .avk-sec{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:#888;margin:10px 0 6px;font-weight:700}
  .avk-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(72px,1fr));gap:8px}
  .avk-opt{background:#fff;border:2px solid #e2d9c6;border-radius:10px;padding:4px 2px 2px;cursor:pointer;display:flex;flex-direction:column;align-items:center;font-size:10px;color:#555}
  .avk-opt img{width:60px;height:60px;image-rendering:pixelated}
  .avk-opt.on{border-color:#c75a2c;box-shadow:0 0 0 2px rgba(199,90,44,.25)}
  .avk-none{width:60px;height:60px;display:flex;align-items:center;justify-content:center;font-size:22px;color:#bbb}
  .avk-sw{display:flex;flex-wrap:wrap;gap:8px}
  .avk-dot{width:30px;height:30px;border-radius:50%;border:2px solid #fff;box-shadow:0 0 0 1px #ccc;cursor:pointer}
  .avk-dot.on{box-shadow:0 0 0 3px #c75a2c}
  .avk-foot{display:flex;gap:8px;padding:12px 16px;border-top:1px solid #ddd3bf;justify-content:space-between;align-items:center}
  .avk-btn{border:none;border-radius:8px;padding:10px 16px;font-size:14px;font-weight:700;cursor:pointer}
  .avk-btn.ghost{background:transparent;border:1px solid #cbbfa6;color:#333}
  .avk-btn.go{background:#c75a2c;color:#fff}
  @media(max-width:700px){.avk-body{flex-direction:column}.avk-stage{flex:none}.avk-full{width:220px;height:220px}}
  `;
  function injectCSS() {
    if (document.getElementById('avk-css')) return;
    const st = document.createElement('style'); st.id = 'avk-css'; st.textContent = CSS; document.head.appendChild(st);
  }

  const TABS = [
    { id: 'skin', label: 'Skin', parts: [], colors: [['skin', 'skin', 'Skin tone']] },
    { id: 'eyes', label: 'Eyes', parts: [['eyes', 'Eye shape']], colors: [['eyeColor', 'eyes', 'Eye colour']] },
    { id: 'brows', label: 'Brows', parts: [['brows', 'Eyebrows']], colors: [['hairColor', 'hair', 'Colour (matches hair)']] },
    { id: 'mouth', label: 'Mouth', parts: [['mouth', 'Mouth']], colors: [] },
    { id: 'hair', label: 'Hair', parts: [['hair', 'Hairstyle']], colors: [['hairColor', 'hair', 'Hair colour']] },
    { id: 'facial', label: 'Facial Hair', parts: [['facialHair', 'Facial hair']], colors: [['facialHairColor', 'hair', 'Facial hair colour']] },
    { id: 'acc', label: 'Accessories', parts: [['hat', 'Hat'], ['glasses', 'Glasses'], ['earring', 'Earring']], colors: [['hatColor', 'gear', 'Hat colour']] },
  ];

  function openEditor(o = {}) {
    if (!P) throw new Error('AvatarKit.load() first');
    injectCSS();
    let cfg = normalize(o.config);
    const opts = { body: o.body || 'skater', number: o.number, captain: !!o.captain };
    let tab = 'hair';
    const ov = document.createElement('div'); ov.className = 'avk-ov';
    ov.innerHTML = `<div class="avk-panel" role="dialog" aria-label="Avatar editor">
      <div class="avk-head"><h3>${o.title || 'Edit Avatar'}</h3><button class="avk-x" data-a="cancel" aria-label="Close">×</button></div>
      <div class="avk-body">
        <div class="avk-stage"><img class="avk-full" alt="Avatar preview">
          <div class="avk-crop-row"><img class="avk-crop" alt="Profile picture preview"><span>Profile picture</span></div></div>
        <div class="avk-side"><div class="avk-tabs"></div><div class="avk-pane"></div></div>
      </div>
      <div class="avk-foot"><button class="avk-btn ghost" data-a="random">🎲 Random</button>
        <div style="display:flex;gap:8px"><button class="avk-btn ghost" data-a="cancel">Cancel</button><button class="avk-btn go" data-a="save">Save</button></div></div>
    </div>`;
    const $ = s => ov.querySelector(s);
    // option thumbnails: no number/captain badge, and hairstyles are shown without a hat
    const thumb = (c, slot) => toDataURL(slot === 'hair' ? Object.assign({}, c, { hat: null }) : c,
                                         { body: opts.body, crop: true, scale: 2 });

    function paint() {
      $('.avk-full').src = toDataURL(cfg, Object.assign({}, opts, { scale: 3 }));
      $('.avk-crop').src = toDataURL(cfg, Object.assign({}, opts, { crop: true, scale: 2 }));
      $('.avk-tabs').innerHTML = TABS.map(t => `<button class="avk-tab${t.id === tab ? ' on' : ''}" data-tab="${t.id}">${t.label}</button>`).join('');
      const t = TABS.find(x => x.id === tab);
      let h = '';
      for (const [slot, title] of t.parts) {
        const def = P.slots[slot];
        h += `<div class="avk-sec">${title}</div><div class="avk-grid">`;
        if (def.optional) h += `<div class="avk-opt${cfg[slot] == null ? ' on' : ''}" data-slot="${slot}" data-v=""><div class="avk-none">${slot === 'hair' ? '' : '∅'}${slot === 'hair' ? `<img src="${thumb(Object.assign({}, cfg, { hair: null }), 'hair')}" alt="">` : ''}</div>${def.noneLabel || 'None'}</div>`;
        for (const [k, part] of Object.entries(def.options)) {
          const c2 = Object.assign({}, cfg, { [slot]: k });
          h += `<div class="avk-opt${cfg[slot] === k ? ' on' : ''}" data-slot="${slot}" data-v="${k}"><img src="${thumb(c2, slot)}" alt="">${part.label || k}</div>`;
        }
        h += '</div>';
      }
      for (const [key, kind, title] of t.colors) {
        h += `<div class="avk-sec">${title}</div><div class="avk-sw">`;
        for (const [name, ramp] of Object.entries(P.ramps[kind])) {
          const c = ramp[3];
          h += `<div class="avk-dot${cfg[key] === name ? ' on' : ''}" title="${name.replace(/_/g, ' ')}" data-color="${key}" data-v="${name}" style="background:rgb(${c[0]},${c[1]},${c[2]})"></div>`;
        }
        h += '</div>';
      }
      if (tab === 'skin') {
        h += `<div class="avk-sec">Preview</div><div class="avk-grid">` + Object.keys(P.ramps.skin).map(n =>
          `<div class="avk-opt${cfg.skin === n ? ' on' : ''}" data-color="skin" data-v="${n}"><img src="${thumb(Object.assign({}, cfg, { skin: n }))}" alt="">${n}</div>`).join('') + '</div>';
      }
      $('.avk-pane').innerHTML = h;
    }

    function close() { ov.remove(); document.removeEventListener('keydown', onKey); }
    function onKey(e) { if (e.key === 'Escape') { close(); o.onCancel && o.onCancel(); } }
    ov.addEventListener('click', e => {
      const el = e.target.closest('[data-a],[data-tab],[data-slot],[data-color]');
      if (!el) { if (e.target === ov) { close(); o.onCancel && o.onCancel(); } return; }
      if (el.dataset.tab) { tab = el.dataset.tab; paint(); return; }
      if (el.dataset.slot) {
        const v = el.dataset.v || null;
        cfg = normalize(Object.assign({}, cfg, { [el.dataset.slot]: v }));
        paint(); return;
      }
      if (el.dataset.color) {
        const k = el.dataset.color, v = el.dataset.v;
        const patch = { [k]: v };
        if (k === 'hairColor' && cfg.facialHairColor === cfg.hairColor) patch.facialHairColor = v;  // beard follows hair until changed
        cfg = normalize(Object.assign({}, cfg, patch)); paint(); return;
      }
      const a = el.dataset.a;
      if (a === 'random') { cfg = random(); paint(); }
      else if (a === 'cancel') { close(); o.onCancel && o.onCancel(); }
      else if (a === 'save') { close(); o.onSave && o.onSave(cfg); }
    });
    document.addEventListener('keydown', onKey);
    (o.mount || document.body).appendChild(ov);
    paint();
    return { close };
  }

  global.AvatarKit = { load, render, toDataURL, openEditor, random, normalize, defaults: () => Object.assign({}, DEFAULTS),
                       get parts() { return P; } };
})(typeof window !== 'undefined' ? window : this);
