# Implementation Plan: India-First AI Lead Generation & Voice Calling SaaS ("AI Lead & Voice Desk")

**Status:** Approved for Execution (Superpowers Phase 1)  
**Execution Strategy:** Test-Driven Development (TDD) with Milestone Verification  
**Primary Tech Stack:** Python 3.11+ (FastAPI, SQLAlchemy, Pydantic, Pytest), Next.js 14+ (TypeScript, Tailwind CSS), PostgreSQL 16 + pgvector, Redis 7

---

## Architecture & Codebase Layout

```
/Users/lhuser/Documents/GoogleAi/
├── backend/
│   ├── app/
│   │   ├── core/                  # Config, database, security, RLS session context, logging
│   │   ├── models/                # SQLAlchemy multi-tenant ORM models (all 28 entities)
│   │   ├── schemas/               # Pydantic v2 validation & API schemas
│   │   ├── api/                   # REST API routers (auth, leads, calls, knowledge, scripts, webhooks)
│   │   ├── services/
│   │   │   ├── tenancy.py         # Organization, workspace, RBAC, usage metering
│   │   │   ├── crm.py             # Lead lifecycle, CSV ingestion, stage transitions
│   │   │   ├── consent.py         # Consent provenance, TRAI quiet hours (09:00-21:00 IST), suppression
│   │   │   ├── crawler.py         # SSRF-safe website ingestion, DNS resolver guardrails
│   │   │   ├── knowledge.py       # Document parsing, chunking, draft/approval review pipeline
│   │   │   ├── prompt_studio.py   # Grounded script synthesizer, industry templates, AI disclosure
│   │   │   ├── sarvam_client.py   # Sarvam API integration (prompts, languages, speech, webhooks)
│   │   │   ├── dispatcher.py      # Call queueing, pre-flight gate, rate limiting, kill-switch
│   │   │   └── tasks.py           # Auto-generated follow-up task engine
│   │   ├── telephony/
│   │   │   ├── base.py            # TelephonyProvider abstract base contract & capability flags
│   │   │   ├── mock_adapter.py    # Complete stateful mock adapter for unit/integration tests
│   │   │   ├── sarvam_vobiz.py    # Sarvam-managed Vobiz telephony adapter (with native transfer)
│   │   │   ├── exotel.py          # Exotel telephony adapter (with media stream & applet transfer)
│   │   │   ├── smartflo.py        # Tata Tele Smartflo adapter
│   │   │   └── registry.py        # Dynamic provider loader per tenant configuration
│   │   └── main.py                # FastAPI application entrypoint with middleware
│   ├── tests/                     # Comprehensive Pytest test suite
│   │   ├── test_tenancy_rls.py    # Cross-tenant data isolation & RLS tests
│   │   ├── test_crawler_ssrf.py   # SSRF defense tests (loopback, 169.254, RFC1918)
│   │   ├── test_consent_gate.py   # TRAI quiet hours & suppression tests
│   │   ├── test_telephony.py      # Provider adapters & call lifecycle tests
│   │   ├── test_webhooks.py       # HMAC verification, idempotency, duplicate event handling
│   │   ├── test_vertical_slice.py # Complete end-to-end integration test
│   │   └── conftest.py
│   ├── scripts/
│   │   └── seed_demo_data.py      # Production-ready demo tenants (Hospitality, Healthcare, Catering)
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/                      # Next.js 14+ TypeScript dashboard
│   ├── src/
│   │   ├── app/                   # App router pages (dashboard, leads, calls, scripts, knowledge, settings)
│   │   ├── components/            # Reusable UI widgets (Click-to-Call, TranscriptViewer, LeadTable)
│   │   └── lib/                   # API client, auth helpers, types
│   ├── package.json
│   └── tailwind.config.js
├── docker-compose.yml             # Single-command local dev orchestration
├── .env.example
└── docs/                          # Architectural & regulatory documentation suite
```

---

## Milestone Breakdown & Implementation Tasks

### Milestone 1: Multi-Tenant Foundation, Database Models & Row-Level Security
- [ ] Task 1.1: Initialize `backend/` project structure, dependencies (`requirements.txt`), and configuration.
- [ ] Task 1.2: Implement database session manager with PostgreSQL Row-Level Security (RLS) support (`SET LOCAL app.current_tenant_id = :org_id`).
- [ ] Task 1.3: Define complete SQLAlchemy ORM models with universal `organization_id`:
  - Organizations, Users, Memberships, Roles, Subscriptions, UsageEvents
  - BusinessProfiles, AllowedDomains, CrawledPages, KnowledgeDocuments, KnowledgeChunks
  - AgentTemplates, AgentVersions, Scripts
  - Leads, LeadSources, ConsentEvents, SuppressionEntries
  - ProviderConnections, PhoneNumbers, Calls, CallEvents, Transcripts, CallSummaries
  - Tasks, EscalationRules, WebhookEvents, AuditLogs
- [ ] Task 1.4: Implement Multi-tenant context middleware and JWT authentication handlers.
- [ ] Task 1.5: Write unit tests in `tests/test_tenancy_rls.py` verifying cross-tenant access is strictly blocked.

### Milestone 2: Telephony Abstraction & Provider Adapters
- [ ] Task 2.1: Implement `TelephonyProvider` abstract base class with declared capabilities (`ProviderCapabilities`).
- [ ] Task 2.2: Implement `MockTelephonyAdapter` with stateful call state machine, simulated ringing, answer, DTMF, transfer, and webhook generation.
- [ ] Task 2.3: Implement `SarvamVobizAdapter` supporting Sarvam-managed telephony, self-serve transfer, and webhook normalizer.
- [ ] Task 2.4: Implement `ExotelAdapter` and `SmartfloAdapter` with fallback for non-self-serve transfer.
- [ ] Task 2.5: Implement Provider Registry and write unit tests in `tests/test_telephony.py`.

### Milestone 3: Lead CRM, Consent Ledger & TRAI Compliance Gate
- [ ] Task 3.1: Implement Lead CRM service (Lead CRUD, stage progression, duplicate detection).
- [ ] Task 3.2: Implement CSV bulk import parser with field mapping, phone normalization to E.164 (`+91`), and duplicate suppression.
- [ ] Task 3.3: Implement Consent Engine:
  - Provenance tracking (timestamp, channel, consent statement).
  - Indian Standard Time (IST) calling hours validator (strictly blocking outbound dialing from 21:00 to 09:00 IST).
  - Centralized Suppression List check (blocking any number marked Do Not Call or opt-out).
- [ ] Task 3.4: Write unit tests in `tests/test_consent_gate.py`.

### Milestone 4: SSRF-Safe Website Scraper & Knowledge Ingestion
- [ ] Task 4.1: Implement `SafeCrawler` with synchronous pre-flight DNS resolver:
  - Strictly blocks RFC 1918 private IPs (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`).
  - Strictly blocks loopback (`127.0.0.0/8`), link-local (`169.254.0.0/16`), AWS/GCP metadata endpoints (`169.254.169.254`), and IPv6.
  - Enforces domain whitelisting, depth limits, and response size limits.
- [ ] Task 4.2: Implement Document & Text Chunker (HTML boilerplate removal, PDF/text parser).
- [ ] Task 4.3: Implement Human-in-the-Loop Review Pipeline: Extracted facts default to `status = 'draft'`; only tenant-approved chunks can be injected into voice agent prompts.
- [ ] Task 4.4: Write unit tests in `tests/test_crawler_ssrf.py` testing hostile URLs and private IP injection.

### Milestone 5: Sarvam Voice Agent & Grounded Prompt Studio
- [ ] Task 5.1: Implement Prompt Studio engine that generates conversational voice scripts grounded strictly in approved knowledge chunks.
- [ ] Task 5.2: Enforce mandatory AI identity disclosure ("Hello, I am an automated assistant calling on behalf of...") and strict anti-hallucination guardrails.
- [ ] Task 5.3: Implement Industry Template library:
  - Hospitality (Hotels/Resorts: banquet, room inquiries).
  - Hospital Administration (OPD routing, appointments; strict refusal of medical advice/diagnosis).
  - Food & Catering (Menu, guest counts, delivery radius).
  - Generic B2B (BANT qualification, meeting scheduling).
- [ ] Task 5.4: Implement Sarvam API client wrapper with multi-language support (Hindi, Indian English, Telugu, etc.).

### Milestone 6: Call Orchestrator, Webhook Processing & Human Escalation
- [ ] Task 6.1: Implement Call Dispatcher (`/calls/dispatch`) with multi-factor pre-flight verification (consent, suppression, calling hours, tenant wallet balance, concurrency limit).
- [ ] Task 6.2: Implement Webhook receiver (`/telephony/webhooks/{provider}`) with HMAC signature validation and Redis idempotency ledger (`idempotency:{event_id}`).
- [ ] Task 6.3: Implement Call Outcome Parser: updates lead stage, saves duration, calculates exact cost (Sarvam minutes + carrier pulses), extracts qualification data, stores transcript.
- [ ] Task 6.4: Implement Human Call Transfer & Fallback: live transfer when provider supports it (`can_transfer_live`), otherwise immediate callback task and priority notification dispatch.
- [ ] Task 6.5: Write comprehensive integration test in `tests/test_vertical_slice.py` executing the complete lifecycle:
  `Tenant Login -> Ingest Lead -> Consent Check -> Outbound Call -> Webhook -> Lead Stage & Task Created`.

### Milestone 7: Frontend Web Dashboard
- [ ] Task 7.1: Setup Next.js 14 dashboard with responsive layouts (Sidebar, Header, Organization switcher).
- [ ] Task 7.2: Build Lead Management Screen (Table, Filters, CSV Uploader, Click-to-Call button).
- [ ] Task 7.3: Build Knowledge Base & Scraper Screen (URL submission, Crawl status, Fact approval cards).
- [ ] Task 7.4: Build Prompt & Script Studio (Template picker, AI disclosure editor, Approved facts citations, Version activation).
- [ ] Task 7.5: Build Call Analytics & Logs Screen (Audio player, Live transcript viewer, Qualification details, Cost breakdown).
- [ ] Task 7.6: Build Follow-up Task Board and Compliance Suppression Manager.

### Milestone 8: Demo Seeding, Verification & Packaging
- [ ] Task 8.1: Create `scripts/seed_demo_data.py` populating realistic demo tenants (The Grand Regal Hotel, Apollo Care Clinics, Royal Feast Catering).
- [ ] Task 8.2: Create `docker-compose.yml` and `.env.example`.
- [ ] Task 8.3: Execute full automated test suite and generate verification reports in `docs/superpowers/ledger.md`.
