# Afterlight

**Digital Estate Planning & Legacy Infrastructure**

You have a will for your physical assets. What about your digital life?

Afterlight is the executor-grade platform for digital death. Encrypted vault, dead man's switch, legacy messages, and a clean dashboard for the people you trust.

## Features

| Feature | Description |
|---|---|
| **Digital Inventory** | Catalog accounts, subscriptions, and digital assets |
| **Smart Vault** | Zero-knowledge encrypted storage for passwords, seed phrases, documents |
| **Dead Man's Switch** | Check-in system with escalation cascade and release protocol |
| **Executor Dashboard** | Clean interface for executors: "here's everything, here's what to do" |
| **Legacy Messages** | Scheduled messages delivered at milestones or after death |
| **Family Circles** | Shared family spaces with role-based access |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                   │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  React UI   │  │ Client-Side  │  │  Web Crypto    │  │
│  │  Dashboard  │  │  Encryption  │  │  (libsodium)   │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTPS (ciphertext only)
┌──────────────────────────▼──────────────────────────────┐
│                   Backend (FastAPI)                      │
│  ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌──────────┐ │
│  │   Auth   │ │   Vault   │ │   DMS     │ │ Executor │ │
│  │  Router  │ │  Router   │ │  Engine   │ │  Router  │ │
│  └──────────┘ └───────────┘ └───────────┘ └──────────┘ │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Zero-Knowledge Encryption Layer           │  │
│  │    Server NEVER sees plaintext or master password │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│              PostgreSQL (Ciphertext Only)                │
└─────────────────────────────────────────────────────────┘
```

## Zero-Knowledge Security Model

Afterlight uses a **zero-knowledge architecture**:

1. **Master password** never leaves the client
2. Client derives a **Key Encryption Key (KEK)** using Argon2id
3. KEK encrypts the user's **Data Encryption Key (DEK)**
4. DEK encrypts all vault items **client-side** (XChaCha20-Poly1305)
5. Server stores **only ciphertext** + encrypted DEK

The server cannot read your data. If breached, attackers get only encrypted blobs.

## Dead Man's Switch

The check-in lifecycle:

```
ACTIVE → OVERDUE → ESCALATING → RELEASED
```

1. **ACTIVE**: User checks in every N days (default: 30)
2. **OVERDUE**: Missed check-in → reminders sent
3. **ESCALATING**: Trusted contacts notified after M missed check-ins
4. **RELEASED**: Full release protocol executed after grace period

The system is **extremely conservative** — false positives are catastrophic.

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Node.js 22+ (for local frontend dev)
- Python 3.12+ (for local backend dev)

### Run with Docker

```bash
# Clone and enter
git clone https://github.com/yourusername/afterlight.git
cd afterlight

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start all services
docker compose up -d

# Run migrations
docker compose exec api alembic upgrade head

# Access
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Local Development

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## API Endpoints

| Endpoint | Description |
|---|---|
| `POST /auth/register` | Create account |
| `POST /auth/login` | Get access token |
| `GET /auth/me` | Get current user |
| `GET/POST /vault` | List/create vault items |
| `GET/POST /assets` | List/create assets |
| `POST /dead-mans-switch/check-in` | Record check-in |
| `GET /dead-mans-switch/status` | Get switch status |
| `GET/POST /legacy-messages` | List/create messages |
| `GET/POST /executor` | List/create executors |
| `GET /executor/dashboard/summary` | Dashboard summary |

## Project Structure

```
afterlight/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models/              # ORM models
│   │   ├── routers/             # API endpoints
│   │   ├── services/            # Business logic
│   │   └── core/                # Security, dependencies
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js pages
│   │   ├── components/          # React components
│   │   ├── lib/                 # Utilities
│   │   └── types/               # TypeScript types
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

## Security Considerations

- **Zero-knowledge**: Server never sees plaintext
- **Argon2id**: Password hashing with memory-hard parameters
- **JWT**: Short-lived access tokens (24h) + refresh tokens (30d)
- **Audit logging**: All sensitive operations logged
- **Rate limiting**: Built into API layer
- **CORS**: Configurable origin allowlist

## License

MIT

## Contributing

This is an active project. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

*Your digital life, handled with care when you're gone.*
