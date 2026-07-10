# Hang Frontend

![React](https://img.shields.io/badge/React-TypeScript-61DAFB)

---

## Frontend Architecture

Built with React, TypeScript, Vite and Tailwind CSS.

### Core Components
| Module | Description |
|---|---|
| Auth | Login, registration, Google OAuth |
| Discovery | Swipe interface |
| Profile | View profile, edit own profile, update info |
| Messaging | Chat, typing indicators |
| Settings | Blocking, reports, password, delete account |

- **Routing**: React Router manages authentication, discovery, messaging, profile and settings routes.
- **Components**: Reusable UI for cards, forms, chat, navigation and dialogs.
- **State Management**: Application state separates authentication, profile data, conversations and UI state.
- **API Layer**: Centralized API client for REST endpoints and WebSocket integration.

---

## Project Layout

```text
hang-frontend/
│
├── src/
│    ├── api/
│    ├── components/
│    ├── pages/
│    ├── routes/
│    │ 
│    ├── assets/
│    ├── constants
│    │
│    ├──App.tsx
│    ├── index.css
│    └── main.tsx
│
├── index.html
│
├── package.json
├── package-lock.json
│
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── vite.config.ts
│
└── README.md
```

---

## Build Process
Multi-stage Docker build compiles Vite assets and serves them with Nginx.

---

## Docker
```bash
bash ../start.sh
```
If you want to build frontend only you have to do so manually as now it is coupled with nginx container, this is intended.

---

## Local Development
```bash
npm install
npm run dev
```