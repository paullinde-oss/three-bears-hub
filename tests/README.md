# Tests

Both run against the local Firebase emulators, never the real project.

**Security rules** (`../database.rules.json`): 33 checks of who can read and write what.

```sh
npm i firebase-tools@14 firebase@10
npx firebase emulators:exec --config firebase.json --only auth,database --project demo-tb "node rules.test.mjs"
```

**End to end** (`e2e.mjs`): drives the real app in Chromium. It covers admin login, the team password, first login with a forced password change, profile folders, saving an avatar, and rules blocking players and strangers.
It needs Playwright, plus `firebase@8.10.1` in a folder passed as `FB` (served in place of the CDN copy). Serve the repo root on port 8765 first.

```sh
(cd .. && python3 -m http.server 8765 &)
npm i firebase@8.10.1 --prefix ./v8
FB=./v8 npx firebase emulators:exec --config firebase.json --only auth,database --project demo-tb "node e2e.mjs"
```
