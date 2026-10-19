# System Architecture: India-First AI Lead Generation & Voice Calling SaaS ("AI Lead & Voice Desk")

**Status:** Draft for Review (Phase 0 / Architectural Baseline)  
**Date:** 19 October 2026  
**Primary AI Engine:** Sarvam AI  
**Telephony Abstraction:** Pluggable Telephony Adapter Layer (Sarvam Vobiz, Exotel, Smartflo, Mock)

---

## 1. Architectural Principles & High-Level Design

The system is structured as a **Modular Monolith** designed for high developer velocity, clear domain boundaries, horizontal scalability, and strict tenant isolation.

```
                  +-------------------------------------------------+
                  |       Web Dashboard & Mobile View (Next.js)     |
                  +-------------------------------------------------+
                                           |  HTTPS (REST + WebSockets)
                                           v
                  +-------------------------------------------------+
                  |               API Gateway / FastAPI             |
                  |  - Auth & RBAC Middleware                       |
                  |  - Tenant Scope Context Injection (RLS)         |
                  |  - Rate Limiting & Webhook Signature Verifier   |
                  +-------------------------------------------------+
                         |                 |                 |
         +---------------+                 |                 +---------------+
         v                                 v                                 v
+------------------+             +-------------------+             +-------------------+
|  Lead CRM Domain |             | Telephony & Voice |             | Knowledge & RAG   |
|  - Intake / CSV  |             |  - Outbound/Inbound|             |  - SSRF Safe Scraper
|  - Consent Ledger|             |  - Telephony Adap.|             |  - Fact Extraction|
|  - Task Engine   |             |  - Sarvam Adapter |             |  - pgvector RAG   |
+------------------+             +-------------------+             +-------------------+
         |                                 |                                 |
         +---------------------------------+---------------------------------+
                                           |
                                           v
                  +-------------------------------------------------+
                  |          Database & Persistence Layer           |
                  |  - PostgreSQL 16 + pgvector (RLS Enforced)      |
                  |  - Redis 7 (Queues, Pub/Sub, Idempotency Caches)|
                  |  - S3 / MinIO (Recordings, Uploaded Docs)       |
                  +-------------------------------------------------+
```

---

## 2. Core Domains & Modules

### 2.1 Identity & Multi-Tenancy (`apps.tenancy`)
- **Tenant Context:** Every request sets a scoped context variable `current_organization_id`.
- **Database Connection Pool:** Injects tenant context into PostgreSQL session via `SET LOCAL app.current_tenant_id = :org_id` before query execution, ensuring Row-Level Security (RLS) acts as a hardware-level defense in depth.
- **RBAC:** Enforces permissions (`admin:write`, `campaign:dial`, `lead:read`, `billing:manage`) across all endpoints.

### 2.2 Telephony Adapter Layer (`apps.telephony`)
To avoid vendor lock-in and address India-specific carrier constraints, all telecom operations are mediated through a unified interface:

```python
class TelephonyProvider(ABC):
    @abstractmethod
    async def validate_credentials(self, config: Dict[str, Any]) -> bool: ...

    @abstractmethod
    async def initiate_call(self, request: OutboundCallRequest) -> OutboundCallResponse: ...

    @abstractmethod
    async def parse_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> NormalizedCallEvent: ...

    @abstractmethod
    async def transfer_call(self, call_sid: str, destination_number: str) -> TransferResult: ...

    @abstractmethod
    async def terminate_call(self, call_sid: str) -> bool: ...

    @abstractmethod
    async def get_capabilities(self) -> ProviderCapabilities: ...
```

#### Provider Concrete Implementations:
1. **`SarvamVobizAdapter`**: Interacts with Sarvam-managed telephony (Vobiz infrastructure). Supports end-to-end self-serve call transfer, automated number allocation, and unified billing.
2. **`ExotelAdapter`**: Connects to Exotel's Voice API and bidirectional media stream websocket for enterprise custom voicebot pipelines.
3. **`SmartfloAdapter`**: Integrates with Tata Tele Business Services Smartflo REST API for outbound click-to-call and IVR routing.
4. **`MockTelephonyAdapter`**: In-memory and stateful mock provider for automated unit, integration, and CI/CD tests. Simulates ringing, answer, DTMF, transfer, and hangup webhook events without network dependencies.

### 2.3 Sarvam AI Voice Engine (`apps.voice_agent`)
- **Sarvam Voice Agents Client:** Communicates with Sarvam API (`https://api.sarvam.ai`) for:
  - Agent creation and prompt configuration.
  - Indian language selection (Hindi, Indian English, Tamil, Telugu, Kannada, Bengali, Gujarati, Marathi, Malayalam).
  - Speech-to-Text (Saaras) and Text-to-Speech (Bulbul) synthesis.
  - Call webhook ingestion, transcript extraction, and automated post-call summarization.
- **Prompt & Script Studio:** Generates persona-aligned, strictly grounded system prompts incorporating approved business knowledge, mandatory identity disclosure ("Hello, I am an automated assistant calling from..."), and structured qualification checkpoints.

### 2.4 Lead CRM & Consent Engine (`apps.crm`)
- **Ingestion Pipeline:** Validates lead data, normalizes Indian mobile numbers to E.164 (`+91XXXXXXXXXX`), detects duplicates, and attributes lead sources (Web, CSV, Meta Ads, WhatsApp).
- **Consent Ledger:** Records explicit consent metadata:
  - Timestamp, Consent Source, IP address, Consent Statement.
  - Opt-Out & Suppression List: Real-time query prevents outbound dialing to any suppressed or opted-out contact.
- **Regulatory Calling Hours Check:** Enforces calling restrictions (09:00 - 21:00 IST).

### 2.5 Knowledge Ingestion & RAG (`apps.knowledge`)
- **Safe Web Scraper:** 
  - Validates scheme (`http`/`https` only).
  - Performs DNS resolution before issuing HTTP requests; strictly denies private IP ranges (RFC 1918: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, loopback `127.0.0.1`, link-local `169.254.169.254`, IPv6 equivalents).
  - Follows robots.txt directives and domain constraints.
- **Document Parser:** Extracts text from PDF and DOCX uploads using sanitized processing sandboxes.
- **Human Approval Gate:** Chunked knowledge records are set to `status = 'draft'`. A tenant administrator must review and approve facts before they are indexed for voice agent prompt injection.

### 2.6 Messaging Connectors (`apps.channels`)
- **WhatsApp Business Cloud API:** Ingests inbound user messages, supports automated template messaging for call follow-ups (e.g. quote summary, location card, appointment confirmation).
- **Instagram Direct Messaging API:** Webhook listener for lead generation from brand engagement.

---

## 3. Database Schema Overview

PostgreSQL 16 serves as the primary relational and vector store:

```
[organizations] 1---* [users]
       |
       +---* [phone_numbers]
       +---* [provider_connections]
       +---* [business_profiles]
       +---* [knowledge_documents] 1---* [knowledge_chunks]
       +---* [agent_templates] 1---* [agent_versions]
       +---* [campaigns] 1---* [campaign_recipients]
       +---* [leads] 1---* [calls] 1---* [transcripts]
       |       |            |
       |       |            +---* [call_events]
       |       +---* [tasks]
       +---* [consent_events]
       +---* [suppression_entries]
       +---* [usage_events]
       +---* [audit_logs]
```

---

## 4. Asynchronous Processing & Idempotency

- **Task Queue:** Celery / ARQ backed by Redis handles:
  - Batch outbound campaign dialing with rate limiting (calls per second) and concurrency controls.
  - Webhook processing with exponential backoff and dead-letter queues.
  - Background website crawling and vector embedding generation.
- **Idempotency Guarantee:** All webhook handlers check Redis for `idempotency:{event_id}` with a 24-hour TTL before processing.
