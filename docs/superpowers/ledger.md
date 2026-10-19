# Superpowers Decision & Verification Ledger: "AI Lead & Voice Desk"

**Project:** India-First AI Lead Generation & Voice Calling SaaS  
**Initialized:** 19 October 2026  
**Status:** Active  

---

## 1. Architectural & Product Decisions

| Decision ID | Date | Area | Decision Summary | Rationale & Alternatives Considered |
| :--- | :--- | :--- | :--- | :--- |
| **DEC-001** | 2026-10-19 | Telephony Layer | Use pluggable `TelephonyProvider` adapter pattern with Mock, Sarvam/Vobiz, Exotel, and Smartflo implementations. | Avoids hard-coding business logic to a single telco. Sarvam/Vobiz chosen for fast MVP; Exotel evaluated for India production; Mock adapter enables complete offline CI/CD without paying for carrier numbers. |
| **DEC-002** | 2026-10-19 | Call Transfer | Treat Call Transfer as a conditional provider capability (`can_transfer_live`), with automatic fallback to high-priority task creation. | Sarvam docs confirm self-serve transfer only on Vobiz and Plivo, not Exotel/Smartflo. Assuming universal transfer would lead to runtime failures on other carriers. |
| **DEC-003** | 2026-10-19 | Stack Choice | FastAPI (Python 3.11+) backend + Next.js (TypeScript) dashboard + PostgreSQL 16 (pgvector) + Redis. | Python provides native integration with AI/ML tools, Sarvam SDKs, and clean async networking. Next.js delivers reactive multi-tenant SaaS interfaces. |
| **DEC-004** | 2026-10-19 | Multi-Tenancy | Enforce `organization_id` on all entities in conjunction with PostgreSQL Row-Level Security (RLS). | Software-level tenant checks can suffer from developer oversight; RLS provides defense-in-depth against data leakage across tenants. |
| **DEC-005** | 2026-10-19 | Web Crawler SSRF | Perform pre-flight DNS resolution and check against RFC 1918, RFC 3927, link-local, loopback, and metadata IPs before making HTTP requests. | Prevents attackers from scanning internal cloud infrastructure (AWS/GCP metadata services, local Redis, database) via the tenant website scanner. |
| **DEC-006** | 2026-10-19 | Knowledge Approval | Require explicit tenant admin approval for extracted website chunks before voice agent prompt ingestion. | Protects voice agents from prompt injections and hallucinating unauthorized rates, discounts, or medical advice. |
| **DEC-007** | 2026-10-19 | Regulatory Calling Gate | Hard-code TRAI commercial calling window check (09:00 - 21:00 IST) and real-time suppression ledger check before initiating any call. | Non-negotiable legal requirement under Indian telecom regulations. Prevents fines and carrier blacklisting. |
| **DEC-008** | 2026-10-19 | Contact Extraction (Harvey) | Adopt EthanPlusAI/Harvey heuristics for autonomous contact extraction, phone normalization, team profile detection, and corporate email prediction (`{f}.{l}@{domain}`) paired with anti-SSRF crawling. | Enables automated discovery of decision makers and telecom lines from business websites without paid external data vendors, directly feeding verified leads into the AI Voice dialer. |
| **DEC-009** | 2026-10-19 | Voice Audio & Verification | Build native Web Audio tone synthesizer (telecom ringback cadence) and Web Speech API turn-by-turn conversation engine into browser caller, with full conversation persistence to Lead objects and dedicated recording playback modal. | Provides complete audio feedback during dialing and conversation without external audio files, while allowing operators to inspect, verify, and replay recorded conversations for every qualified lead. |

---

## 2. Verification Log

| Verification ID | Phase | Target Module | Test Command / Procedure | Result | Evidence / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **VER-001** | Phase 0 | Master Document Discovery | `python3 -c "import zipfile..."` | PASS | Successfully located in `/Users/lhuser/Downloads/` and extracted 22,247 characters from `India_First_AI_Lead_Generation_Voice_SaaS_Research_and_Master_Prompt.docx`. |
| **VER-002** | Phase 0 | Documentation Suite | Inspection of `docs/*.md` | PASS | Created `requirements.md`, `architecture.md`, `provider-capability-matrix.md`, `threat-model.md`, `api-contract.md`, `deployment.md`. |
| **VER-003** | Milestone 1 | Tenancy & RLS Isolation | `pytest backend/tests/test_tenancy_rls.py` | PASS | Verified PBKDF2 password hashing, credential encryption, JWT claims, and strict cross-tenant boundary isolation. |
| **VER-004** | Milestone 2 | Telephony Adapters & Fallback | `pytest backend/tests/test_telephony.py` | PASS | Verified Mock adapter, Sarvam/Vobiz native transfer, and Exotel/Smartflo graceful fallback to callback task creation. |
| **VER-005** | Milestone 3 | Consent & TRAI Calling Window | `pytest backend/tests/test_consent_gate.py` | PASS | Verified Indian E.164 normalization, TRAI 09:00-21:00 IST calling hours enforcement, suppression checks, and CSV bulk import. |
| **VER-006** | Milestone 4 | SSRF Defense & Knowledge Review | `pytest backend/tests/test_crawler_ssrf.py` | PASS | Verified rejection of loopback, RFC 1918, link-local, AWS/GCP metadata (`169.254.169.254`), and draft-to-approved knowledge gating. |
| **VER-007** | Milestone 5 | Voice Script Studio & Guardrails | `pytest backend/tests/test_prompt_studio.py` | PASS | Verified grounding in approved facts, mandatory AI identity disclosure, and hospital non-clinical safety directives. |
| **VER-008** | Milestone 6 | End-to-End Vertical Slice | `pytest backend/tests/test_vertical_slice.py` | PASS | Executed complete lifecycle: Lead intake -> Consent -> Script Approval -> Call Dispatch -> Webhook -> Metering -> Qualification -> Task Spawn -> Idempotency. |
| **VER-009** | Milestone 7 | Full REST API Test Suite | `pytest backend/tests/test_api_endpoints.py` | PASS | Verified healthz, tenant login, lead listing, click-to-call dispatch, webhook reception, and follow-up task generation. (22/22 tests passing). |
| **VER-010** | Milestone 8 | Frontend Web Build | `npm run build` | PASS | Vite + React 18 production build compiled in 1.84s with 0 errors. |
| **VER-011** | UX/UI Overhaul | shadcn/ui Redesign & Modals | Interactive UI validation & `npm run build` | PASS | Implemented shadcn/ui design system with zinc dark tokens, real authentication, functional "+ New Lead" modal, CSV bulk import, and live call dialog with human transfer. |
| **VER-012** | Live Runtime | Full-Stack Runtime Verification | Live curl to FastAPI (8000) & Vite (3000) | PASS | Verified live JWT login, lead creation via API, healthz check, and Vite dev server running on port 3000. |
| **VER-013** | Docker Packaging | Docker Compose Multi-Container Stack | `docker compose up -d --build` & container verification | PASS | Built `ai-lead-voice-desk-backend:latest` and `ai-lead-voice-desk-frontend:latest`. Containers `desk_backend`, `desk_frontend` (ports 3000 & 3001), `desk_postgres`, and `desk_redis` running healthy. Verified Nginx reverse proxy, PostgreSQL seed data, and JWT auth through port 3000. |
| **VER-014** | Version Control | GitHub Repository Deployment | `git push -u origin main` | PASS | Successfully committed 71 files (9,819 insertions) with clean `.gitignore` and pushed branch `main` to `https://github.com/savdharamsale/ai-lead-voice-desk.git`. |
| **VER-015** | Feature Integration | Harvey Contact Extractor & Web Scraper | `pytest backend/tests/ -v` & `npm run build` | PASS | Integrated EthanPlusAI/Harvey contact discovery engine into FastAPI & React. Implemented real website crawling in Knowledge Base replacing mock timeouts. 27/27 unit & integration tests passing. |
| **VER-016** | Container & Remote Update | Docker Rebuild & GitHub Push | `docker compose up -d --build` & `git push` | PASS | Rebuilt frontend with Harvey Contact Discovery UI modal. Containers healthy. Pushed all changes to GitHub main. |
| **VER-017** | Audio & Verification | Real-Time Call Audio & Playback Player | `npm run build` & Docker rebuild | PASS | Implemented audible ringing and real-time speech dialogue, automatic conversation recording attachment to Lead entities, and interactive Call Recording Player & Verification modal. Extracted Facts Review Queue immediately removes rejected items. |

---

## 3. Unresolved Issues & External Dependencies Tracker

| Issue ID | Category | Description | Mitigating Strategy / Blocker Status |
| :--- | :--- | :--- | :--- |
| **UNRES-001** | Regulatory / KYC | Production Indian Virtual Number allocation requires entity registration and KYC approval from telecom provider. | Fully abstracted behind `MockTelephonyAdapter` for development and automated testing. Real provider switched on once tenant KYC is approved. |
| **UNRES-002** | Telecom DLT | TRAI DLT header and template registration takes 3-7 business days with Indian telcos. | System stores DLT Template IDs and Principal Entity IDs in `business_profiles` ready for production activation. |
| **UNRES-003** | Meta Verification | Official WhatsApp Business API access requires Meta Business Manager verification. | Meta API adapter supports sandbox developer credentials and mock event payloads during development. |
