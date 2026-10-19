# Deployment & Operations Guide: "AI Lead & Voice Desk"

**Status:** Draft for Review (Phase 0 / Superpowers Operations)  
**Date:** 19 October 2026  
**Stack:** FastAPI (Python 3.11+) + Next.js (Node 20+) + PostgreSQL 16 (pgvector) + Redis 7 + MinIO / S3

---

## 1. System Topology & Prerequisites

The platform is designed to run either:
1. **Locally / Developer Mode:** Via single-command `docker compose up -d`.
2. **Cloud Production:** Kubernetes (EKS/GKE), AWS ECS Fargate, or containerized VMs with managed RDS PostgreSQL and ElastiCache.

### Minimum Hardware Requirements:
- **Local Dev:** 4 CPU cores, 8 GB RAM, 15 GB free disk space.
- **Production (Small Cluster):** 2 API replicas (2 vCPU, 4GB RAM), 2 Celery Worker replicas, 1 Managed PostgreSQL instance (db.t4g.medium).

---

## 2. Local Docker Compose Architecture

The development bundle contains:
- `db`: PostgreSQL 16 with `pgvector` and standard full-text search extensions.
- `redis`: Redis 7 alpine for Celery queue, distributed rate-limiting, and idempotency cache.
- `minio`: S3-compatible local object storage for uploaded brochures, PDFs, and synthetic call audio.
- `backend`: FastAPI Python application running with Uvicorn reload.
- `worker`: Celery / ARQ worker daemon handling campaign dialing and async crawling.
- `frontend`: Next.js 14+ / React application with Tailwind CSS dashboard.

---

## 3. Environment Configuration (`.env.example`)

```bash
# ========================================================
# Platform Environment Variables
# ========================================================
APP_ENV=development
APP_SECRET_KEY=generate_a_random_32_byte_hex_string
ENCRYPTION_KEY=generate_a_random_32_byte_aes_key_base64
LOG_LEVEL=INFO

# ========================================================
# Database & Storage
# ========================================================
DATABASE_URL=postgresql://desk_user:desk_password@db:5432/desk_db
REDIS_URL=redis://redis:6379/0
S3_ENDPOINT_URL=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=desk-recordings-and-docs
S3_REGION=ap-south-1

# ========================================================
# AI Voice Provider (Sarvam AI)
# ========================================================
SARVAM_API_KEY=your_sarvam_api_key_here
SARVAM_BASE_URL=https://api.sarvam.ai

# ========================================================
# Telephony Providers (Configurable per Tenant or Platform Default)
# ========================================================
TELEPHONY_DEFAULT_PROVIDER=mock  # Options: mock, sarvam_vobiz, exotel, smartflo
VOBIZ_ACCOUNT_ID=
VOBIZ_AUTH_TOKEN=
EXOTEL_API_KEY=
EXOTEL_API_TOKEN=
EXOTEL_ACCOUNT_SID=
EXOTEL_SUBDOMAIN=api.exotel.com
SMARTFLO_API_KEY=
SMARTFLO_API_SECRET=

# ========================================================
# Messaging Channels (Meta / WhatsApp / Instagram)
# ========================================================
META_APP_ID=
META_APP_SECRET=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_ACCESS_TOKEN=
WEBHOOK_VERIFY_TOKEN=desk_webhook_verify_secret

# ========================================================
# Regulatory & Calling Guardrails
# ========================================================
ENFORCE_CALLING_HOURS=true
CALLING_WINDOW_START_IST=09:00
CALLING_WINDOW_END_IST=21:00
```

---

## 4. Database Migrations & Initial Seeding

```bash
# 1. Run database schema migrations
docker compose exec backend alembic upgrade head

# 2. Seed initial demo tenants and industry templates
docker compose exec backend python -m scripts.seed_demo_data
```

### Seed Tenant Profiles Included:
1. **The Grand Regal Hotel & Palace (Hospitality):** Banquet inquiries, luxury suite booking script, room service FAQ.
2. **Apollo Care Clinics (Healthcare Administration):** OPD specialist appointment scheduling, health checkup inquiries, strict anti-clinical-advice guardrails.
3. **Royal Feast Catering (Food/Catering):** Wedding and corporate catering packages, menu customization, guest count qualification.

---

## 5. Production Readiness & Security Checklist

- [ ] All database connections enforce SSL (`sslmode=require`).
- [ ] PostgreSQL Row-Level Security (RLS) is validated through automated multi-tenant penetration tests.
- [ ] No API secrets or encryption keys are logged or returned in responses.
- [ ] Webhook endpoints enforce cryptographic HMAC signature checks.
- [ ] Outbound web crawler enforces strict SSRF protections against internal IPs and AWS/GCP metadata services (`169.254.169.254`).
- [ ] Real Indian phone numbers have passed KYC with telecom providers (Vobiz / Exotel / Tata Tele Smartflo).
- [ ] TRAI DLT registration and template headers are configured before launching commercial promotional campaigns.
