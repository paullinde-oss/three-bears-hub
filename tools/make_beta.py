#!/usr/bin/env python3
"""Build beta/index.html from index.html.

The beta copy is served at /three-bears-hub/beta/ and uses the separate test data (/hubdev in Firebase),
so new features can be tried on real phones without touching the live site or the real team data.
Run from the repo root:  python3 tools/make_beta.py
"""
import os, re
src = open('index.html', encoding='utf-8').read()
out = src.replace('<head>', '<head>\n<base href="../">', 1)            # assets resolve to the repo root
out = re.sub(r'>(v[\d.]+)</div>', r'>\1 beta</div>', out, count=1)
os.makedirs('beta', exist_ok=True)
open('beta/index.html', 'w', encoding='utf-8').write(out)
print('wrote beta/index.html')
