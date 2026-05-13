# ⚡ FastAPI Task Manager — Production-Ready Backend

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-0.115.5-009688?style=for-the-badge&logo=fastapi" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-Neon-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0-red?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Alembic-1.14-blueviolet?style=for-the-badge" />
  <img src="https://img.shields.io/badge/JWT-Auth-orange?style=for-the-badge&logo=jsonwebtokens" />
</p>

A **production-ready** REST API built with **FastAPI**, **SQLAlchemy 2.0**, **Neon PostgreSQL**, **JWT authentication**, and **secure HTTP-only cookies**. Includes full CRUD for Users and Tasks, Alembic migrations, dependency injection, and Pydantic v2 validation.

---

## 📁 Project Structure

```
.
├── .env.example              # Copy to .env and fill in secrets
├── alembic.ini               # Alembic configuration
├── requirements.txt
├── alembic/
│   ├── env.py                # Reads DATABASE_URL from .env
│   ├── script.py.mako
│   └── versions/             # Migration history
└── app/
    ├── main.py               # App entry point, CORS, lifespan
    ├── config.py             # Pydantic-Settings
    ├── database.py           # Engine, SessionLocal, get_db()
    ├── models.py             # User + Task ORM models
    ├── schemas.py            # Pydantic v2 request/response models
    ├── auth.py               # JWT, bcrypt, cookie helpers
    └── routers/
        ├── users.py          # /api/v1/users
        └── tasks.py          # /api/v1/tasks
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/coddies/FastAPI-fullapp.git
cd FastAPI-fullapp

pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Neon DATABASE_URL and a strong SECRET_KEY
```

Generate a secure key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Run Migrations

```bash
alembic upgrade head
```

### 4. Start the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📖 API Endpoints

### 🔐 Users  `base: /api/v1/users`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/register` | ❌ | Register new user |
| `POST` | `/login` | ❌ | Login → JWT cookie + token body |
| `POST` | `/logout` | ✅ | Clear auth cookie |
| `GET` | `/me` | ✅ | Current user profile |
| `PUT` | `/me` | ✅ | Update profile |
| `GET` | `/` | ✅ Superuser | List all users |
| `DELETE` | `/{user_id}` | ✅ Superuser | Delete user |

### 📋 Tasks  `base: /api/v1/tasks`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/` | Create task |
| `GET` | `/` | List tasks (paginated + filtered) |
| `GET` | `/{task_id}` | Get single task |
| `PUT` | `/{task_id}` | Full update |
| `PATCH` | `/{task_id}` | Partial update |
| `DELETE` | `/{task_id}` | Delete task |

**Task filters:** `?status=todo&priority=high&is_completed=false&search=keyword&page=1&page_size=20`

---

## 🔑 Authentication

Tokens are delivered two ways:
1. **HTTP-only secure cookie** — automatically sent by browsers
2. **Response body** — for programmatic/mobile clients using `Authorization: Bearer <token>`

```bash
# Register
curl -X POST http://localhost:8000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"john","password":"SecurePass1"}'

# Login
curl -X POST http://localhost:8000/api/v1/users/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"username":"john","password":"SecurePass1"}'

# Authenticated request (via cookie)
curl http://localhost:8000/api/v1/users/me -b cookies.txt

# Authenticated request (via Bearer)
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <your_token>"
```

---

## 📐 Enums

| Field | Values |
|-------|--------|
| `status` | `todo` · `in_progress` · `done` · `cancelled` |
| `priority` | `low` · `medium` · `high` · `critical` |

---

## 🔒 Password Rules

- Minimum **8 characters**
- At least **1 uppercase** letter
- At least **1 digit**

---

## 🛠 Alembic Migrations

```bash
# After changing models.py
alembic revision --autogenerate -m "Your description"
alembic upgrade head

# Rollback
alembic downgrade -1

# History
alembic history --verbose
```

---

## ⚙️ Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Neon PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret |
| `ALGORITHM` | `HS256` (default) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token TTL in minutes (default: `30`) |

---

## 📚 Tech Stack

| Library | Version | Purpose |
|---------|---------|---------|
| FastAPI | 0.115.5 | Web framework |
| SQLAlchemy | 2.0.36 | ORM |
| Alembic | 1.14.0 | DB migrations |
| psycopg2-binary | 2.9.10 | PostgreSQL driver |
| python-jose | 3.3.0 | JWT |
| passlib[bcrypt] | 1.7.4 | Password hashing |
| pydantic | 2.10.3 | Validation |
| pydantic-settings | 2.6.1 | Config from .env |
| uvicorn | 0.32.1 | ASGI server |

---

## 🌐 Interactive Docs

Once running, open:
- **Swagger UI** → http://localhost:8000/docs
- **ReDoc** → http://localhost:8000/redoc

---

## 📄 License

MIT © 2025
