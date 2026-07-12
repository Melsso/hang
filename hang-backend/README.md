# Hang Backend

![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688)

---

## 🏗 Backend Architecture

Stateless FastAPI service designed for horizontal scaling behind Nginx.

### Core Components
| Component | Purpose |
|---|---|
| FastAPI | REST + WebSockets |
| SQLAlchemy | ORM |
| PostgreSQL | Persistent data |
| Redis | Cache + Pub/Sub |
| JWT | Authentication |
| S3 | Cloud data storage |
| Google OAuth | Federated login |

- **Authentication**: Email/password, Google OAuth, JWT in HTTP-only cookies, password changes and account deletion.
- **Profiles**: CRUD, interests, preferences, images via S3 abstraction.
- **Messaging**: Realtime messaging over WebSockets with typing events, pagination and read state.
- **Redis Pub/Sub**: Synchronizes realtime events across multiple FastAPI instances.

---

## API Layout

```text
hang-backend/
│
├── src/
│   └── hang/
│       ├── core/
│       ├── helpers/
│       ├── routes/
│       ├── schemas/
│       ├── models/
│       └── main.py
│
├── tests/
├── smoke_tests/
│
├── Dockerfile.hang
├── logging.json
│
├── dev_utils/
│   ├── resources/
│   └── inject_data.py
│
├── poetry.lock
├── pyproject.toml
│
├── .api.env.example
├── .db.env.example
│
└── README.md
```

---

## Docker
Runs as container behind Nginx. Multiple instances supported.

---

## Local Development
```bash
poetry run uvicorn app.main:app --reload
```

---

## Scaling
```bash
bash ../start.sh 3
```
Launches three backend containers behind Nginx.

---

## Engineering Decisions

- Stateless services
- Dependency injection
- Pydantic validation
- ORM abstraction
- Metrics endpoint for Prometheus
- Room based websockets with redis pub/sub system
- Cursor based pagination
- Cloud file storage using s3
- Structured JSON logs
- Request level logging
