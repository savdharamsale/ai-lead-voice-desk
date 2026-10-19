# Requirements Specification: India-First AI Lead Generation & Voice Calling SaaS ("AI Lead & Voice Desk")

**Status:** Draft for Review (Phase 0 / Superpowers Brainstorming Gate)  
**Date:** 19 October 2026  
**Target Market:** India  
**Primary AI Voice Platform:** Sarvam AI  
**Baseline Document:** `India_First_AI_Lead_Generation_Voice_SaaS_Research_and_Master_Prompt.docx`

---

## 1. Executive Overview & Product Mission

"AI Lead & Voice Desk" is a production-oriented, multi-tenant B2B SaaS platform engineered specifically for the Indian business ecosystem. It empowers businesses—especially hotels/hospitality, hospital administration (non-clinical appointments and callbacks), restaurants/catering, and generic B2B enterprises—to:

1. **Ingest Leads Multichannel:** Capture inbound leads via manual entry, bulk CSV imports, public embeddable website forms, authenticated REST APIs, ad-lead webhooks (Google/Meta), and official WhatsApp Business / Instagram Messaging conversations.
2. **Ground Knowledge from Business Content:** Ingest tenant-approved public website content and uploaded documents (PDFs, brochures) with strict SSRF protection, sanitization, human review, and vector/full-text search.
3. **Draft & Approve AI Voice Scripts:** Synthesize grounded conversational scripts adhering to business tone, opening AI disclosure, qualification questions, objection handling, and human escalation rules. Scripts strictly prohibit fabricating prices, availability, or clinical diagnosis.
4. **Autonomous Voice Calling (Inbound & Outbound):** Execute outbound AI voice calls and receive inbound calls through an abstracted Indian cloud telephony layer. The AI agent speaks fluent Indian English, Hindi, Telugu, and other regional languages powered by Sarvam AI.
5. **Strict Regulatory & Consent Guardrails:** Guarantee strict compliance with Indian telecom regulations (TRAI/TCCCPR/DLT frameworks), verifying consent records, quiet hours (9:00 PM – 9:00 AM local time), frequency caps, and immediate suppression list enforcement.
6. **Live Human Escalation & Follow-up CRM:** Gracefully transfer live callers to tenant staff when supported by the provider, or create instant callback/follow-up tasks with automated notification pipelines.
7. **Strict Multi-Tenancy & Usage Metering:** Ensure ironclad data isolation via tenant identifiers and PostgreSQL Row-Level Security (RLS), with granular metering for agent minutes, telephony pulses (30-second pulses), number rentals, and message volume.

---

## 2. Functional Requirements

### 2.1 Multi-Tenancy, Organization & RBAC
- **FR-1.1 Tenant Onboarding:** Self-serve and admin-driven creation of Organizations and Workspaces with unique slugs and isolation keys (`organization_id`).
- **FR-1.2 Business Profile:** Tenant configuration of company details, industry vertical, business hours, escalation phone numbers, calling windows, and brand preferences.
- **FR-1.3 User Management & Roles:** Role-Based Access Control supporting:
  - `Platform Admin`: Global administrative operations, billing management, and platform telemetry.
  - `Tenant Admin`: Organization configuration, user invitations, provider credentials, billing, and script approvals.
  - `Sales/CRM Manager`: Lead management, campaign approvals, analytics, and CRM workflows.
  - `Call Agent/Staff`: Call review, manual dialing (click-to-call), and follow-up task handling.
- **FR-1.4 Audit Logging:** Immutable log of all administrative actions, credential updates, script activations, and bulk exports.

### 2.2 Lead Intake & CRM
- **FR-2.1 Lead Capture Channels:**
  - Manual single lead creation via dashboard.
  - Bulk CSV import with field mapping, syntax validation, duplicate phone detection, and consent verification.
  - Public embeddable web form endpoint with anti-abuse rate limits and CAPTCHA support.
  - Authenticated REST API & Inbound Webhooks for CRM integrations (HubSpot, Zoho, Salesforce).
  - Official WhatsApp Business & Instagram Direct conversation-to-lead ingestion.
- **FR-2.2 Lead Lifecycle & Stages:**
  - Standardized pipeline stages: `New`, `Needs Review`, `Eligible to Contact`, `Queued`, `Attempted`, `Connected`, `Qualified`, `Follow-up`, `Escalated`, `Converted`, `Not Interested`, `Invalid`, `Do Not Contact`.
- **FR-2.3 Attribution & Provenance:** Store source, campaign ID, UTM parameters, referrer, and timestamps.
- **FR-2.4 Consent & Contact Suppression:**
  - Record explicit consent provenance (timestamp, channel, consent text/purpose).
  - Centralized Suppression List ("Do Not Call" / Opt-Out).
  - Automatic suppression on verbal opt-out during calls or text opt-out via WhatsApp/SMS ("STOP").

### 2.3 Website Ingestion & Knowledge Base (RAG)
- **FR-3.1 Scoped Web Crawling:** Tenant-authorized domain crawling. Strict enforcement of allowed domains and path whitelists.
- **FR-3.2 Document Processing:** Extraction of text from uploaded brochures, rate cards, menus, and FAQs (PDF, DOCX, TXT).
- **FR-3.3 Extraction & Fact Formulation:** Clean boilerplate, navigation noise, scripts; parse structured business facts (services, policies, operating hours, FAQs).
- **FR-3.4 Tenant Review Gate:** Extracted facts are stored in `Draft` state; voice agents cannot access unapproved facts. Tenant admins must review and explicitly approve each chunk or document.
- **FR-3.5 Grounded Knowledge Retrieval:** PostgreSQL full-text search combined with `pgvector` semantic embeddings to provide contextual citations for voice scripts and agent prompts.

### 2.4 Prompt & Voice Script Studio
- **FR-4.1 Script Generation Engine:** Synthesizes structured conversational scripts based on approved business facts, industry vertical, primary objective, and desired tone.
- **FR-4.2 AI Identity Disclosure:** Standardized mandatory opening statement disclosing the synthetic/AI nature of the caller in adherence to responsible AI practices.
- **FR-4.3 Industry Templates:**
  - *Hotel / Hospitality:* Check-in/check-out dates, room tier, occupancy, dining/banquet inquiries.
  - *Hospital / Healthcare Administration:* Clinic department routing, doctor consultation window requests, administrative callback scheduling. **Strict anti-hallucination guardrail:** Zero clinical diagnosis, triage, or prescription discussions.
  - *Restaurant / Catering:* Party size, dietary preferences, event date, venue location, booking confirmation.
  - *Generic B2B:* B2B qualification (budget, authority, need, timeline - BANT), meeting scheduling.
- **FR-4.4 Versioning & Approval:** Every script revision creates an immutable version (`v1`, `v2`). Only tenant-approved scripts can be deployed to live campaigns.

### 2.5 India-First Cloud Telephony & Voice Agent Workflows
- **FR-5.1 Provider-Agnostic Adapter:** Pluggable interface (`TelephonyProvider`) supporting:
  - *Sarvam-Managed Telephony (powered by Vobiz):* Primary path for rapid MVP, number rental, outbound campaigns, and native call transfer.
  - *Exotel:* Primary candidate for Indian production deployments (custom SIP/media streaming, REST dialer).
  - *Tata Tele Smartflo:* Enterprise cloud telephony alternative.
  - *Mock Adapter:* Complete automated testing adapter with webhook simulator.
- **FR-5.2 Outbound Calling Workflow:**
  - One-click click-to-call from lead dashboard for authorized staff.
  - Batch automated campaigns with concurrency throttling, retry policies (max attempts, exponential backoff), and tenant quiet-hour validation.
  - Calling window enforcement: Automatically block outbound calls between 21:00 and 09:00 IST.
  - Pre-call consent verification against suppression ledger.
- **FR-5.3 Inbound Calling Workflow:**
  - Dedicated virtual numbers mapped to tenant organizations.
  - Inbound webhook processing: Greeting, intent extraction, real-time query resolution using approved knowledge, and lead creation/update.
- **FR-5.4 Human Call Transfer & Fallback:**
  - Live call bridging to tenant escalation number when the caller asks for a human agent or upon escalation triggers.
  - Dynamic fallback: If telephony provider does not support native transfer (or if destination is busy/unanswered), capture callback details, inform caller transparently, and spawn a high-priority follow-up task.
- **FR-5.5 Call Outcome & Telemetry:**
  - Ingestion of provider call status webhooks (queued, ringing, answered, completed, failed, busy, no-answer).
  - Persistence of call duration, cost breakdown, audio recording metadata (if enabled and consented), transcript, AI summary, and qualification field extractions.

### 2.6 Follow-up Tasks & Messaging Channels
- **FR-6.1 Task Engine:** Automatic generation of follow-up tasks linked to leads, with due dates, priorities, assignee, and status tracking.
- **FR-6.2 Official Meta Channels:**
  - WhatsApp Business Cloud API integration for sending approved template follow-ups (e.g., booking confirmations, brochures).
  - Instagram Messaging API integration for managing lead inquiries.
  - Opt-out synchronization across all communication channels.

### 2.7 SaaS Usage Metering & Billing
- **FR-7.1 Usage Metrics:**
  - AI Voice Agent minutes (calculated per second or 60s minimums per plan).
  - Telephony outbound/inbound pulses (30-second pulse intervals).
  - Number rental monthly charges.
  - WhatsApp/SMS conversation fees.
- **FR-7.2 Budget Caps & Alerts:** Tenant-configurable hard caps and warning thresholds (80%, 100%) to prevent unexpected billing overruns.

---

## 3. Non-Functional Requirements

### 3.1 Security & Tenant Isolation
- **NFR-1.1 Ironclad Data Isolation:** Strict enforcement of `organization_id` partitioning across all database tables, queries, background workers, and S3 file keys.
- **NFR-1.2 PostgreSQL Row-Level Security (RLS):** Activated on all tenant-scoped tables with session-variable validation (`app.current_tenant_id`).
- **NFR-1.3 Anti-SSRF Architecture:** Outbound HTTP clients for website crawling must enforce DNS resolution checks, blocking private IP spaces (RFC 1918, RFC 3927, RFC 4193, loopback, link-local, AWS/GCP metadata endpoints `169.254.169.254`).
- **NFR-1.4 Secret Management:** Telephony and Sarvam credentials stored encrypted at rest (AES-256-GCM / KMS). Credentials never exposed via frontend API responses or client-side bundles.

### 3.2 Performance & Reliability
- **NFR-2.1 Webhook Processing Latency:** Sub-100ms response time for incoming telephony webhooks, offloading heavy processing to asynchronous job queues.
- **NFR-2.2 Idempotency:** Webhook and call dispatch handlers must use idempotency keys (Provider Call SID, Webhook Event ID) to prevent duplicate calls, duplicate billing, or duplicate CRM entries.
- **NFR-2.3 System Availability:** Designed for 99.9% uptime with graceful degradation (e.g., if AI speech service is degraded, switch to automated callback scheduling).

### 3.3 Compliance & Regulatory Adherence (India)
- **NFR-3.1 TRAI & TCCCPR Alignment:** Strict enforcement of calling window hours (09:00 to 21:00 IST), opt-out mechanisms, and DLT header/template attribution documentation.
- **NFR-3.2 Privacy & Consent:** Clear recording notices and purpose-bound data storage.
- **NFR-3.3 Medical Non-Interference:** Strict guardrails preventing AI agents from giving medical advice or handling emergency triage.
