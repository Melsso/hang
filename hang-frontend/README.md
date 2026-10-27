# Hang Frontend

React 19 + TypeScript single-page app built with Vite and styled with Tailwind CSS 4.

## Structure

```text
src/
├── api/          fetch wrappers for each backend area, the shared apiFetch client and the WebSocket hook
├── components/
│   ├── conversations/   conversation list and chat panel
│   ├── global/          header, action bar, buttons, toasts, RequireAuth route guard
│   ├── profile/         image panel (drag to reorder), info panel, selects
│   ├── settings/        settings rows and modals
│   └── swipes/          swipe card, actions and match overlay
├── constants/    interest list
├── pages/        Landing, Login, Register, Swipes, Profile, Conversations, Settings
├── routes/       router setup
└── App.tsx, main.tsx, index.css

tests/
├── api/
├── components/
├── pages/
└── setup.ts
```

## Behavior worth knowing

- **Route guards:** `/swipes`, `/profile`, `/conversations` and `/settings` are wrapped in `RequireAuth`,
  which calls `/api/auth/session` and redirects to `/login` when there is no session.
- **401 handling:** every API call goes through `apiFetch` in `src/api/client.ts`, which always sends
  credentials. A 401 redirects once to `/login?expired=1`, and the login page explains why. It is skipped on
  the login, register, session and logout endpoints (where 401 means bad credentials or no session) and on
  public pages.
- **WebSocket:** one connection per Conversations page, URL derived from the page origin (`ws://` or
  `wss://`). The hook answers server pings with pongs, and reconnects after an unexpected close with
  exponential backoff and jitter (1 s up to 30 s, reset when the server sends `ready`). Before each retry it
  checks the session, so an expired login goes to `/login` instead of retrying forever. It exposes a
  `connected` flag, and `send` reports whether the frame was actually sent, so the chat input keeps the text
  when the socket is down.
- **Resync after reconnect:** the server does not replay events, so after every reconnect the Conversations
  page refetches the conversation list and the open conversation.
- **Feed:** swipe profiles are fetched in pages of up to 20; when the last one is swiped, the next page is
  fetched. Google accounts without a birthdate see an empty feed until they set one.
- **Google sign-in:** a refused sign-in returns to `/login?error=google` and shows a toast.
- **Super like:** the UI uses `super-like` and `api/swipes.ts` converts it to the API's `super_like`.

## Development

```bash
npm install
npm run dev
```

The dev server proxies `/api` (including WebSockets) to a running environment, so the stack must be up
(`./start.sh dev` from the repository root). The proxy target is set in `vite.config.ts`:

```ts
proxy: {
  "/api": { target: "https://dev.localtest.me:8443", ws: true, changeOrigin: true, secure: false },
},
```

The auth cookie is `Secure`. Chrome accepts it on `http://localhost`; other browsers may not. If login does
not stick, use the deployed URL instead and rebuild with `./start.sh`.

## Scripts

| Command                | Purpose                         |
| ---------------------- | ------------------------------- |
| `npm run dev`          | Vite dev server                 |
| `npm run build`        | Type-check and production build |
| `npm run format`       | Format with Prettier            |
| `npm run format:check` | Prettier check (run in CI)      |
| `npm run lint`         | ESLint (run in CI)              |
| `npm test`             | Run the test suite (run in CI)  |
| `npm run test:watch`   | Tests in watch mode             |
| `npm run preview`      | Preview the production build    |

## Production build

The image in `hang-frontend/Dockerfile` builds the app in a multi-stage build and serves `dist/` with nginx
(`nginx.conf` falls back to `index.html` for client-side routes). In the cluster it runs as the `frontend`
deployment behind the ingress, which routes `/api` to the API and everything else here.
