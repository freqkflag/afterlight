# Afterlight

**Digital Estate Planning — Early Access**

You have a will for your physical assets. What about your digital life?

Afterlight helps you catalog digital assets and prove you’re alive — so the people you trust get a clear checklist when it matters.

> **Status: Alpha.** Core owner flows (inventory, vault, dead man’s switch, executor invites) and an executor portal are available. Family Circles and production email delivery are not shipped yet.

## What works today

| Feature | Description |
|---|---|
| **Digital Inventory** | Catalog accounts, subscriptions, and digital assets |
| **Encrypted Vault** | Client-side encrypted storage for passwords, seed phrases, and notes (Web Crypto AES-GCM; master password never leaves the browser) |
| **Dead Man’s Switch** | Check-in system with configurable intervals, trusted contacts, and pause/resume |
| **Executor Portal** | Invite executors; they can accept and see an estate checklist |
| **Legacy Messages** | Compose encrypted messages scheduled for release triggers |

## Coming later

- Family Circles (shared family spaces)
- Production SMTP/SMS for overdue reminders and release notifications
- Rate limiting middleware

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                   │
│  React UI  ·  Web Crypto (AES-GCM + PBKDF2)  ·  Vault   │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTPS (ciphertext for vault)
┌──────────────────────────▼──────────────────────────────┐
│                   Backend (FastAPI)                      │
│  Auth · Vault · Assets · DMS · Legacy · Executor         │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                         PostgreSQL                       │
└─────────────────────────────────────────────────────────┘
```

## Client-side vault encryption

1. You choose a **vault master password** (separate from login)
2. The browser derives a key with **PBKDF2** using your salt from the server
3. That key wraps a random **Data Encryption Key (DEK)**
4. Vault item plaintext is encrypted in the browser with **AES-GCM**
5. The server stores ciphertext, nonces, and the wrapped DEK — never your master password

## Dead Man’s Switch

```
ACTIVE → OVERDUE → ESCALATING → RELEASED
```

1. **ACTIVE**: Check in every N days (default: 30)
2. **OVERDUE**: Missed check-in (reminders require SMTP configuration)
3. **ESCALATING**: Trusted contacts are recorded for notification
4. **RELEASED**: Release protocol marks the estate for executor access

The system is designed to be conservative — false positives are catastrophic.

## Quick Start

### Prerequisites

- Docker + Docker Compose, **or**
- Node.js 22+ and Python 3.12+

### Run with Docker

```bash
git clone https://github.com/freqkflag/afterlight.git
cd afterlight
cp .env.example .env
docker compose up -d
docker compose exec api alembic upgrade head
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
alembic upgrade head
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
| `POST /auth/login` | Get access + refresh tokens |
| `POST /auth/refresh` | Exchange refresh token |
| `GET /auth/me` | Current user |
| `GET/PUT /auth/key-bundle` | Vault salt + wrapped DEK |
| `GET/POST /vault` | List/create vault items (includes ciphertext) |
| `GET/POST /assets` | List/create assets |
| `POST /dead-mans-switch/check-in` | Record check-in |
| `GET /dead-mans-switch/status` | Switch status |
| `POST /dead-mans-switch/configure` | Update intervals |
| `GET/POST /dead-mans-switch/trusted-contacts` | Trusted contacts |
| `GET/POST /legacy-messages` | Legacy messages |
| `GET/POST /executor` | Manage executors (owner) |
| `GET /executor/dashboard/summary` | Owner dashboard summary |
| `POST /executor/portal/accept` | Accept an invite |
| `GET /executor/portal/estates` | Estates granted to you |

## Project Structure

```
afterlight/
├── backend/
│   ├── app/
│   ├── migrations/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── types/
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Security notes

- Vault master password stays in the browser
- Account password is hashed server-side with Argon2id
- JWT access tokens (short-lived) + refresh tokens
- Audit logging for executor and check-in events
- CORS origin allowlist via config

## License

MIT

---

*Your digital life, handled with care when you're gone.*
