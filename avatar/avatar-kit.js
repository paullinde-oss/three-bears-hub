/*
 * AvatarKit: a self-contained layered avatar renderer and editor.
 *
 *   await AvatarKit.load('avatar/parts.json');
 *   img.src = AvatarKit.toDataURL(config, { crop: true, size: 160, number: 7, captain: true });
 *   AvatarKit.openEditor({ config, number: 7, body: 'goalie', onSave: cfg => ... });
 *
 * parts.json (built by tools/canva_import.py) lists PNG layers. Each part is { src, x, y, w, h } on a
 * size[0] x size[1] canvas, so layers simply stack in `order`. Parts in a slot with `tint` can be
 * recoloured: their brightness is mapped onto a 5-stop colour ramp (dark -> light), except when the
 * chosen colour is the part's `native` colour, which draws the original art untouched.
 * No dependencies; drop the avatar/ folder into any project.
 */
(function (global) {
  'use strict';

  let P = null, BASE = '';
  const images = new Map();    // src -> HTMLImageElement
  const tinted = new Map();    // src|colour -> canvas
  const cache = new Map();     // rendered data URLs

  const DEFAULTS = { v: 2, skin: 'default', hair: null, hairColor: 'brown', facialHair: null, facialHairColor: 'brown',
                     hat: null, hatColor: 'navy', glasses: null, earring: null };

  const hex = h => { const n = parseInt(h.slice(1), 16); return [n >> 16, (n >> 8) & 255, n & 255]; };
  const loadImg = src => new Promise((res, rej) => {
    const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error('Could not load ' + src)); im.src = BASE + src;
  });

  async function load(src) {
    if (typeof src === 'string') { BASE = src.replace(/[^/]*$/, ''); P = await (await fetch(src)).json(); }
    else P = src;
    images.clear(); tinted.clear(); cache.clear();
    const all = [];
    for (const slot of Object.values(P.slots))
      for (const part of Object.values(slot.options || {}))
        if (part.src && !images.has(part.src)) { images.set(part.src, null); all.push(loadImg(part.src).then(im => images.set(part.src, im))); }
    await Promise.all(all);
    return P;
  }

  const slot = name => P.slots[name] || { options: {} };
  const has = (name, key) => !!(slot(name).options || {})[key];

  function normalize(cfg) {
    const c = Object.assign({}, DEFAULTS, cfg || {});
    for (const s of ['hair', 'facialHair', 'hat', 'glasses', 'earring']) c[s] = c[s] && has(s, c[s]) ? c[s] : null;
    if (!has('skin', c.skin)) c.skin = Object.keys(slot('skin').options)[0] || 'default';
    const ramps = P.ramps || {};
    if (!(ramps.hair || {})[c.hairColor]) c.hairColor = 'brown';
    if (!(ramps.hair || {})[c.facialHairColor]) c.facialHairColor = c.hairColor;
    if (!(ramps.gear || {})[c.hatColor]) c.hatColor = 'navy';
    return c;
  }

  // Recoloured copy of a part: brightness (normalised by the part's own range) -> colour ramp
  function tintedCanvas(part, rampName, ramp) {
    const key = part.src + '|' + rampName;
    if (tinted.has(key)) return tinted.get(key);
    const im = images.get(part.src);
    const cv = document.createElement('canvas'); cv.width = part.w; cv.height = part.h;
    const ctx = cv.getContext('2d'); ctx.drawImage(im, 0, 0);
    const d = ctx.getImageData(0, 0, part.w, part.h), px = d.data;
    const stops = ramp.map(hex), [lo, hi] = part.lum || [0, 255], span = Math.max(1, hi - lo);
    for (let i = 0; i < px.length; i += 4) {
      if (!px[i + 3]) continue;
      let t = ((0.299 * px[i] + 0.587 * px[i + 1] + 0.114 * px[i + 2]) - lo) / span;
      t = Math.min(1, Math.max(0, t)) * (stops.length - 1);
      const k = Math.min(stops.length - 2, Math.floor(t)), f = t - k, a = stops[k], b = stops[k + 1];
      px[i] = a[0] + (b[0] - a[0]) * f; px[i + 1] = a[1] + (b[1] - a[1]) * f; px[i + 2] = a[2] + (b[2] - a[2]) * f;
    }
    ctx.putImageData(d, 0, 0);
    tinted.set(key, cv);
    return cv;
  }

  // Jersey number: chunky pixel digits rotated to run along the sleeve, like the original player art
  const DIGITS = {
    0: ['01110', '11011', '11011', '11011', '11011', '11011', '01110'], 1: ['00110', '01110', '00110', '00110', '00110', '00110', '01111'],
    2: ['01110', '11011', '00011', '00110', '01100', '11000', '11111'], 3: ['11110', '00011', '00011', '01110', '00011', '00011', '11110'],
    4: ['00011', '00111', '01011', '11011', '11111', '00011', '00011'], 5: ['11111', '11000', '11110', '00011', '00011', '11011', '01110'],
    6: ['01110', '11000', '11110', '11011', '11011', '11011', '01110'], 7: ['11111', '00011', '00011', '00110', '00110', '00110', '00110'],
    8: ['01110', '11011', '11011', '01110', '11011', '11011', '01110'], 9: ['01110', '11011', '11011', '01111', '00011', '00011', '01110'] };
  function drawNumber(ctx, n) {
    const spec = P.number; const s = String(n ?? '').replace(/\D/g, '').slice(0, 2);
    if (!spec || !s) return;
    // draw the 5x7 digits as crisp blocks at full size, then rotate smoothly onto the sleeve
    const u = spec.unit, w = (s.length * 6 - 1) * u, h = 7 * u, g = document.createElement('canvas');
    g.width = w; g.height = h;
    const gx = g.getContext('2d'); gx.fillStyle = spec.color;
    [...s].forEach((ch, k) => DIGITS[ch].forEach((row, j) => [...row].forEach((c, i) => { if (c === '1') gx.fillRect((k * 6 + i) * u, j * u, u, u); })));
    ctx.save();
    ctx.imageSmoothingEnabled = true;
    ctx.translate(spec.center[0], spec.center[1]);
    ctx.rotate((spec.angle || 0) * Math.PI / 180);
    ctx.drawImage(g, -w / 2, -h / 2);
    ctx.restore();
  }

  // Render onto a full-size canvas. opts: { body: 'skater'|'goalie', number, captain }
  function render(cfg, opts = {}) {
    if (!P) throw new Error('AvatarKit.load() first');
    const c = normalize(cfg); const [W, H] = P.size;
    const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
    const ctx = cv.getContext('2d');
    const hatPart = c.hat ? slot('hat').options[c.hat] : null;
    for (const name of P.order) {
      if (name === 'number') { drawNumber(ctx, opts.number); continue; }
      const def = slot(name);
      let key;
      if (name === 'body') key = has('body', opts.body) ? opts.body : 'skater';
      else if (name === 'captain') key = opts.captain ? 'C' : null;
      else key = c[name];
      const part = key && def.options[key];
      if (!part || part.none || !images.get(part.src)) continue;
      let src = images.get(part.src);
      if (def.tint && def.colorKey) {
        const colour = c[def.colorKey];
        if (colour && colour !== part.native && P.ramps[def.tint][colour]) src = tintedCanvas(part, colour, P.ramps[def.tint][colour]);
      }
      if (name === 'hair' && hatPart && hatPart.clipHairAbove != null) {
        const cut = Math.max(0, hatPart.clipHairAbove - part.y);       // hide hair under the crown of the hat
        if (cut < part.h) ctx.drawImage(src, 0, cut, part.w, part.h - cut, part.x, part.y + cut, part.w, part.h - cut);
        continue;
      }
      ctx.drawImage(src, part.x, part.y, part.w, part.h);
    }
    return cv;
  }

  // PNG data URL. opts.crop gives the head-and-shoulders profile picture; opts.size is the output width in px.
  function toDataURL(cfg, opts = {}) {
    const r = opts.crop ? P.crop : { x: 0, y: 0, w: P.size[0], h: P.size[1] };
    const size = opts.size || r.w;
    const key = JSON.stringify([normalize(cfg), opts.body || 'skater', opts.number ?? '', !!opts.captain, !!opts.crop, size]);
    if (cache.has(key)) return cache.get(key);
    const src = render(cfg, opts);
    const out = document.createElement('canvas'); out.width = size; out.height = Math.round(size * r.h / r.w);
    const ctx = out.getContext('2d'); ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(src, r.x, r.y, r.w, r.h, 0, 0, out.width, out.height);
    const url = out.toDataURL('image/png');
    if (cache.size > 300) cache.clear();
    cache.set(key, url);
    return url;
  }

  function random() {
    const pick = a => a[Math.floor(Math.random() * a.length)];
    const keys = s => Object.keys(slot(s).options || {});
    const hairColor = pick(Object.keys(P.ramps.hair));
    const maybe = (s, p) => keys(s).length && Math.random() < p ? pick(keys(s)) : null;
    return normalize({
      skin: pick(keys('skin')), hair: Math.random() < 0.9 ? maybe('hair', 1) : null, hairColor,
      facialHair: maybe('facialHair', 0.6), facialHairColor: hairColor,
      hat: maybe('hat', 0.25), hatColor: pick(Object.keys(P.ramps.gear)),
      glasses: maybe('glasses', 0.2), earring: maybe('earring', 0.15)
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
  .avk-full{width:300px;height:300px;background:radial-gradient(circle at 50% 40%,#e7eef4,#c9d7e2);border-radius:12px;border:1px solid #c5d3df}
  .avk-crop-row{display:flex;align-items:center;gap:10px;font-size:12px;color:#666}
  .avk-crop{width:72px;height:72px;border-radius:50%;background:#f2ede2;border:2px solid #ddd3bf}
  .avk-side{flex:1;min-width:0;display:flex;flex-direction:column}
  .avk-tabs{display:flex;gap:4px;overflow-x:auto;border-bottom:1px solid #ddd3bf;margin-bottom:10px;scrollbar-width:none}
  .avk-tabs::-webkit-scrollbar{display:none}
  .avk-tab{background:none;border:none;padding:8px 10px;font-size:13px;font-weight:600;color:#777;cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap}
  .avk-tab.on{color:#1a1a1a;border-bottom-color:#c75a2c}
  .avk-sec{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:#888;margin:10px 0 6px;font-weight:700}
  .avk-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(76px,1fr));gap:8px}
  .avk-opt{background:#fff;border:2px solid #e2d9c6;border-radius:10px;padding:4px 2px 2px;cursor:pointer;display:flex;flex-direction:column;align-items:center;font-size:10px;color:#555;text-align:center}
  .avk-opt img{width:64px;height:64px;border-radius:50%}
  .avk-opt.on{border-color:#c75a2c;box-shadow:0 0 0 2px rgba(199,90,44,.25)}
  .avk-none{width:64px;height:64px;display:flex;align-items:center;justify-content:center;font-size:22px;color:#bbb}
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

  // Tabs only appear when parts.json has options for them
  const TABS = [
    { id: 'skin', label: 'Skin', parts: [['skin', 'Skin tone']], colors: [] },
    { id: 'hair', label: 'Hair', parts: [['hair', 'Hairstyle']], colors: [['hairColor', 'hair', 'Hair colour']] },
    { id: 'facial', label: 'Facial Hair', parts: [['facialHair', 'Facial hair']], colors: [['facialHairColor', 'hair', 'Facial hair colour']] },
    { id: 'acc', label: 'Accessories', parts: [['hat', 'Hat'], ['glasses', 'Glasses'], ['earring', 'Earring']], colors: [['hatColor', 'gear', 'Hat colour']] },
  ];

  function openEditor(o = {}) {
    if (!P) throw new Error('AvatarKit.load() first');
    injectCSS();
    let cfg = normalize(o.config);
    const opts = { body: o.body || 'skater', number: o.number, captain: !!o.captain };
    const tabs = TABS.filter(t => t.parts.some(([s]) => Object.keys(slot(s).options || {}).length > (s === 'skin' ? 1 : 0)));
    let tab = (tabs.find(t => t.id === 'hair') || tabs[0] || {}).id;
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
    // option thumbnails: no number/captain, and hairstyles are shown without a hat
    const thumb = (c, s) => toDataURL(s === 'hair' ? Object.assign({}, c, { hat: null }) : c, { body: opts.body, crop: true, size: 128 });

    function paint() {
      $('.avk-full').src = toDataURL(cfg, Object.assign({}, opts, { size: 600 }));
      $('.avk-crop').src = toDataURL(cfg, Object.assign({}, opts, { crop: true, size: 144 }));
      $('.avk-tabs').innerHTML = tabs.map(t => `<button class="avk-tab${t.id === tab ? ' on' : ''}" data-tab="${t.id}">${t.label}</button>`).join('');
      const t = tabs.find(x => x.id === tab);
      let h = '';
      if (t) {
        for (const [s, title] of t.parts) {
          const def = slot(s), entries = Object.entries(def.options || {});
          if (!entries.length) continue;
          h += `<div class="avk-sec">${title}</div><div class="avk-grid">`;
          if (def.optional) h += `<div class="avk-opt${cfg[s] == null ? ' on' : ''}" data-slot="${s}" data-v="">${s === 'hair'
            ? `<img src="${thumb(Object.assign({}, cfg, { hair: null }), 'hair')}" alt="">` : '<div class="avk-none">∅</div>'}${def.noneLabel || 'None'}</div>`;
          for (const [k, part] of entries)
            h += `<div class="avk-opt${cfg[s] === k ? ' on' : ''}" data-slot="${s}" data-v="${k}"><img src="${thumb(Object.assign({}, cfg, { [s]: k }), s)}" alt="">${part.label || k}</div>`;
          h += '</div>';
        }
        for (const [key, kind, title] of t.colors) {
          if (key === 'hatColor' && !cfg.hat) continue;
          h += `<div class="avk-sec">${title}</div><div class="avk-sw">`;
          for (const [name, ramp] of Object.entries(P.ramps[kind] || {}))
            h += `<div class="avk-dot${cfg[key] === name ? ' on' : ''}" title="${name.replace(/_/g, ' ')}" data-color="${key}" data-v="${name}" style="background:${ramp[3]}"></div>`;
          h += '</div>';
        }
      }
      $('.avk-pane').innerHTML = h;
    }

    function close() { ov.remove(); document.removeEventListener('keydown', onKey); }
    function onKey(e) { if (e.key === 'Escape') { close(); o.onCancel && o.onCancel(); } }
    ov.addEventListener('click', e => {
      const el = e.target.closest('[data-a],[data-tab],[data-slot],[data-color]');
      if (!el) { if (e.target === ov) { close(); o.onCancel && o.onCancel(); } return; }
      if (el.dataset.tab) { tab = el.dataset.tab; paint(); return; }
      if (el.dataset.slot) { cfg = normalize(Object.assign({}, cfg, { [el.dataset.slot]: el.dataset.v || null })); paint(); return; }
      if (el.dataset.color) {
        const k = el.dataset.color, v = el.dataset.v, patch = { [k]: v };
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
