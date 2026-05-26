# 📡 Hang — Real-Time Messaging System
A production-style real-time messaging system built with **FastAPI, WebSockets, Redis Pub/Sub, PostgreSQL, and Dockerized multi-instance deployment behind Nginx load balancing**.

This project demonstrates a **scalable distributed backend architecture for real-time communication systems**, not just a basic chat application.

---

# ⚡ Why this project matters
This project was built to simulate a **real-world scalable messaging infrastructure**, focusing on:
- Real-time WebSocket communication at scale
- Distributed event propagation using Redis Pub/Sub
- Horizontal scaling of stateless backend services
- Production-style deployment using Docker + Nginx

---

# 🚀 Key Features
## 💬 Real-time Messaging
- WebSocket-based messaging system
- Instant message delivery across connected clients
- Room-based routing per conversation

## 🔄 Pub/Sub Architecture (Redis)
- Redis-backed event propagation across multiple app instances
- Enables horizontal scaling of WebSocket servers

## 👥 Conversation System
- Multi-conversation support per user
- Real-time conversation preview updates
- Unread message tracking

## ✍️ Typing & Read Indicators
- Live typing indicators
- Read receipts per message
- Cross-client synchronization

## 📄 Pagination
- Cursor-based pagination for messages
- Efficient scroll-based message loading
- Optimized for large conversations

## ⚙️ Scalable Infrastructure
- Multi-instance FastAPI deployment
- Nginx reverse proxy with load balancing
- Stateless application design

## 🐳 Full Dockerized Environment
- Containerized backend, Redis, PostgreSQL, and Nginx
- One-command startup scripts
- Reproducible development environment

---

# 🧱 Architecture Overview
                ┌──────────────┐
                │    Nginx     │
                │ Load Balancer│
                └──────┬───────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌──────────────┐             ┌──────────────┐
│ FastAPI App  │             │ FastAPI App  │
│  Instance 1  │             │  Instance 2  │
└──────┬───────┘             └──────┬───────┘
       │                             │
       └──────────────┬──────────────┘
                      │
                ┌────────────┐
                │   Redis    │
                │ Pub/Sub    │
                └────────────┘
                      │
                ┌────────────┐
                │ PostgreSQL │
                └────────────┘

---

# 🛠 Tech Stack
- Backend: FastAPI (Python 3.11)
- Realtime: WebSockets
- Messaging Infra: Redis Pub/Sub
- Database: PostgreSQL
- Reverse Proxy: Nginx
- Containerization: Docker
- Auth: OAuth (Google)
- Storage: S3-compatible (AWS / R2)

---

# 📦 Project Structure
    hang/
    │
    ├── src/
    │   └── hang/
    │       ├── core/
    │       ├── helpers/
    │       ├── routes/
    │       ├── schemas/
    │       ├── models/
    │       ├── static/
    │       └── main.py
    │
    ├── Dockerfile.hang
    ├── logging.json
    │
    ├── infra/
    │   ├── grafana
    │   ├── nginx
    │   ├── prometheus
    │   ├── Dockerfile.db
    │   ├── Dockerfile.redis
    │
    ├── dev_utils/
    │   ├── start.sh
    │   └── stop.sh
    │
    ├── docker-compose.yml
    ├── .api.env.example
    ├── .db.env.example
    │
    ├── README.md

---

# ⚡ Quick Start
1. Clone the repository
```bash
    git clone https://github.com/Melsso/hang
    cd hang
```

2. Configure environment variables
Copy template and fill required values:
```bash
    cp .api.env.example .api_env
    cp .db.env.example .db_env
```
Required services:
- PostgreSQL credentials
- Redis connection
- Google OAuth credentials
- S3 / R2 storage credentials

3. Start the system
Option A — Recommended (Docker Compose)
```bash
    docker compose up --build
```

Option B — Convenience script
```bash
    ./dev_utils/start.sh NUMBER-OF-INSTANCES
```
This script:
- creates required docker network
- ensures Redis & PostgreSQL containers are running
- builds and starts application services

4. Stop system
Option A — Recommended (Docker Compose)
```bash
    docker compose down
```
Option B — Convenience script
```bash
    ./dev_utils/stop.sh
```

---

# 🌐 Access
API: http://localhost:8000/api/auth/

---

# 🧠 System Design Highlights
- **Stateless backend architecture**: All FastAPI instances are stateless, enabling horizontal scaling behind a load balancer.
- **Redis Pub/Sub event propagation**: Ensures real-time synchronization of messages across multiple backend instances.
- **WebSocket room model**: Users join conversation-specific rooms for isolated message broadcasting.
- **Cursor-based pagination**: Efficient loading of large message histories without full dataset fetching.

---

# 📊 Observability
- Structured JSON logging across all services
- Request-level logging with event tracing
- Grafana integration for metrics visualization

---

# 🔐 Authentication
- Google OAuth login flow
- Token-based session management
- 30-minute token expiry policy (stateless enforcement)

---

# ⚠️ Notes
- External services (OAuth, S3, etc.) require valid credentials in .api_env
- This system is designed for distributed deployment, not single-process execution
- WebSocket scaling is handled via Redis pub/sub layer

---

# 📌 Future Improvements
- Distributed tracing (request correlation across WS + HTTP)
- Advanced message delivery guarantees (ACK system)
- Push notifications for offline users
- Mobile client integration

---

# 🧾 License
MIT

---

# ⭐ Project Summary
This project demonstrates:
- real-time system design (WebSockets + pub/sub)
- distributed backend architecture
- scalable service orchestration
- production-style Docker deployment
- pagination + state management in real-time systems