# Hang Frontend

React 19 + TypeScript single-page app built with Vite and styled with Tailwind CSS 4.

## Structure

```text
src/
├── api/          fetch wrappers for each backend area and the WebSocket hook
├── components/
│   ├── conversations/   conversation list and chat panel
│   ├── global/          header, action bar, buttons, toasts, RequireAuth route guard
│   ├── profile/         image panel (drag to reorder), info panel, selects
│   ├── settings/        settings rows and modals
│   └── swipes/          swipe card and actions
├── constants/    interest list
├── pages/        Landing, Login, Register, Swipes, Profile, Conversations, Settings
├── routes/       router setup
└── App.tsx, main.tsx, index.css
```

## Behavior worth knowing

- **Route guards:** `/swipes`, `/profile`, `/conversations` and `/settings` are wrapped in `RequireAuth`,
  which calls `/api/auth/session` and redirects to `/login` when there is no session.
- **WebSocket:** one connection per Conversations page, URL derived from the page origin
  (`ws://` or `wss://`). The hook answers server pings with pongs, which keeps the connection alive.
- **Feed:** swipe profiles are fetched in pages of up to 20; when the last one is swiped, the next page is
  fetched. Google accounts without a birthdate see an empty feed until they set one.
- **Super like:** the UI uses `super-like` and `api/swipes.ts` converts it to the API's `super_like`.

## Development

```bash
npm install
npm run dev
```

The dev server proxies `/api` (including WebSockets) to `http://localhost:8000`, so the backend stack
must be running.

## Scripts

| Command           | Purpose                         |
| ----------------- | ------------------------------- |
| `npm run dev`     | Vite dev server                 |
| `npm run build`   | Type-check and production build |
| `npm run format`  | Code formatting using prettier  |
| `npm run lint`    | ESLint                          |
| `npm run preview` | Preview the production build    |

## Production build

The nginx image (`infra/nginx/Dockerfile`) builds the frontend in a multi-stage Docker build and serves
`dist/`. The frontend is not built or run on its own in Docker.
