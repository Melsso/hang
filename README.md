# 🖤 Hang — Full-Stack Social Discovery Platform

A production-style real-time social discovery platform built with **FastAPI, WebSockets, Redis Pub/Sub, PostgreSQL, React, TypeScript, and Dockerized multi-instance deployment behind Nginx load balancing**.

This project demonstrates a **scalable distributed backend architecture for real-time communication systems**.

---

# ⚡ Quick Summary

The platform allows users to:
- Create and customize profiles
- Discover users through swipe interactions
- Match through mutual interests
- Communicate through real-time conversations
- Manage account settings, reports, and blocked users

The project focuses on building a realistic production architecture with:
- containerized services
- reverse proxy routing
- horizontal scaling of stateless backend services
- real-time WebSocket communication at scale
- persistent relational data
- monitoring infrastructure

---

# ✨ Features

## 🔐 Authentication
- Email/password authentication
- Google OAuth login
- Secure HTTP-only cookie sessions

## 👤 User Profiles
- Profile creation and editing
- User images
- Interests and preferences
- Country and demographic information

## ⚙️ Account Management
- Change password
- Delete account
- View reports
- Block/unblock users

## ❤️ Swipe System
- Like/pass interactions
- Persistent swipe history
- Match creation through mutual likes
- Swipe state persistence

## 🔄 Pub/Sub Architecture (Redis)
- Redis-backed event propagation across multiple app instances
- Enables horizontal scaling of WebSocket servers

## 💬 Real-Time Messaging
- WebSocket communication
- Room-based routing per conversation
- Live typing indicators
- Unread message tracking
- Read receipts per message

## 📄 Pagination
- Cursor-based pagination for messages
- Efficient scroll-based message loading
- Optimized for large conversations

## ⚙️ Scalable Infrastructure
- Multi-instance FastAPI deployment
- Nginx reverse proxy with load balancing
- Stateless application design

## 🐳 Full Dockerized Environment
- Containerized backend, Redis, PostgreSQL, Nginx and isolated React frontend
- One-command startup scripts
- Reproducible development environment

---

# 🏗 Architecture Overview

```text
                              Users
                                │
                                ▼
                      ┌─────────────────┐
                      │      Nginx      │
                      │ Reverse Proxy & │
                      │ Static Hosting  │
                      └────────┬────────┘
                               │
             ┌─────────────────┴─────────────────┐
             │                                   │
             │                              FastAPI Instances
             │                                REST API
             │                              WebSockets             
             │                                   │ 
             │                       ┌───────────┴───────────┐
             ▼                       ▼                       ▼
    React Frontend (Vite)       ┌─────────┐              ┌─────────┐
        Static Assets           │FastAPI-1│              │FastAPI-2│
                                └─────┬───┘              └─────┬───┘
                                      └──────────┬─────────────┘
                                                 │
                           ┌─────────────────────┼─────────────────────┐
                           │                     │                     │
                           ▼                     ▼                     ▼
                    PostgreSQL              Redis Pub/Sub       S3-Compatible
                      Database            Cache & Messaging     Object Storage
              
    ─────────────────────────────────────────────────────────────────────────
                                                 ▲
                                                 │
                                          /metrics endpoint
                                                 │
                                         ┌───────────────┐
                                         │  Prometheus   │
                                         └───────┬───────┘
                                                 │
                                                 ▼
                                         ┌─────────────┐
                                         │   Grafana   │
                                         │ Dashboards  │
                                         └─────────────┘
```

---

# 🐳 Infrastructure

The entire system runs using Docker containers:

Services:

| Service | Purpose |
|---|---|
| nginx | Reverse proxy + frontend serving |
| api | FastAPI backend |
| postgres | Persistent database |
| redis | Cache + realtime event layer |
| prometheus | Metrics collection |
| grafana | Monitoring dashboards |

---

# 🛠 Tech Stack

- Backend: FastAPI
- Realtime: WebSockets
- Authentication: JWT, OAuth (Google)
- Storage: S3-compatible (AWS / R2)
- Database: PostgreSQL
- Frontend: React
- Reverse Proxy: Nginx
- Containerization: Docker
- Monitoring: Prometheus, Grafana

---

# 📂 Project Structure

```text
hang/
│
├── hang-frontend/
│ ├── src/
│ ├── vite.config.ts
│ └── README.md
│
├── hang-backend/
│ ├── src/
│ │ └── hang/
│ ├── Dockerfile.hang
│ ├── dev_utils/
│ ├── .api.env.example
│ ├── .db.env.example
│ └── README.md
│
├── infra/
│ ├── nginx/
│ ├── prometheus/
│ ├── grafana/
│ ├── Dockerfile.db
│ └── Dockerfile.redis
│
├── docker-compose.yml
├── start.sh
├── stop.sh
└── README.md
```

---

# 🚀 Running Locally

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
```bash
    ./start.sh NUMBER-OF-INSTANCES
```
This script:
- creates required docker network
- ensures Redis & PostgreSQL containers are running
- builds and starts application services

4. Stop system
```bash
    ./stop.sh
```

---

# 🌐 Access

Application: http://localhost:8000/
or whichever port you decide to bind nginx to.

---

# 🧠 Engineering Highlights

- **Production-style routing**: Nginx acts as the single entry point, serves frontend assets, proxies API requests and handles WebSocket upgrades
- **Stateless backend architecture**: All FastAPI instances are stateless, enabling horizontal scaling behind a load balancer.
- **Redis Pub/Sub event propagation**: Ensures real-time synchronization of messages across multiple backend instances.
- **Containerized deployment**: Every infrastructure component runs independently and can be rebuilt reproducibly.

---

# ⚠️ Notes
- External services (OAuth, S3, etc.) require valid credentials in .api_env

---

# 📌 Future Improvements
- Distributed tracing (request correlation across WS + HTTP)
- Advanced message delivery guarantees (ACK system)
- Push notifications for offline users
- Mobile client integration
- CI/CD pipeline
- Cloud deployment

---

# 📄 License
MIT