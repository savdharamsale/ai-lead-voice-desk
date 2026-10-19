# REST API Contract Specification: "AI Lead & Voice Desk"

**Version:** 1.0.0-rc1  
**Base URL:** `/api/v1`  
**Authentication:** HTTP Bearer JWT (`Authorization: Bearer <token>`) with embedded `organization_id` & `role`.  
**Tenant Header:** Optional override for platform admins `X-Organization-ID: <uuid>`.

---

## 1. Authentication & Tenancy

### `POST /auth/login`
- **Request:**
  ```json
  { "email": "admin@tajpalace.com", "password": "secure_password" }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "id": "usr_9021",
      "email": "admin@tajpalace.com",
      "name": "Arjun Sharma",
      "role": "tenant_admin",
      "organization_id": "org_taj_mumbai"
    }
  }
  ```

---

## 2. Lead Management & Ingestion

### `POST /leads`
Creates a single lead with consent provenance.
- **Request:**
  ```json
  {
    "first_name": "Rohan",
    "last_name": "Mehta",
    "phone": "+919876543210",
    "email": "rohan@example.com",
    "source": "website_form",
    "campaign_id": null,
    "consent_statement": "User opted in via banquet contact form on 2026-10-19",
    "custom_fields": {
      "event_type": "Wedding Reception",
      "guest_count": 250,
      "preferred_date": "2026-12-15"
    }
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "id": "lead_1048",
    "organization_id": "org_taj_mumbai",
    "phone": "+919876543210",
    "stage": "Eligible to Contact",
    "is_suppressed": false,
    "created_at": "2026-10-19T11:30:00Z"
  }
  ```

### `POST /leads/import-csv`
Bulk imports leads with duplicate detection and consent verification.
- **Multipart Form:** `file`: `leads.csv`, `consent_provenance`: string.
- **Response (200 OK):**
  ```json
  {
    "total_rows": 150,
    "imported_count": 142,
    "duplicate_count": 5,
    "suppressed_count": 3,
    "batch_id": "batch_8819"
  }
  ```

### `POST /leads/public-form`
Unauthenticated public web form endpoint rate-limited by IP and tenant key.
- **Headers:** `X-Tenant-Key: pub_live_90df8a...`
- **Request:** Standard lead form payload.

---

## 3. Knowledge Ingestion & RAG

### `POST /knowledge/crawl`
Submits a public domain for SSRF-safe crawling.
- **Request:**
  ```json
  {
    "url": "https://tajhotels.com/en-in/taj-mahal-palace-mumbai/",
    "max_depth": 2,
    "max_pages": 15
  }
  ```
- **Response (202 Accepted):**
  ```json
  {
    "crawl_job_id": "crawl_7719",
    "status": "queued",
    "target_domain": "tajhotels.com"
  }
  ```

### `GET /knowledge/chunks?status=draft`
Lists extracted facts pending human review and approval.
- **Response (200 OK):**
  ```json
  {
    "items": [
      {
        "id": "chunk_331",
        "source_url": "https://tajhotels.com/dining/wasabi",
        "title": "Wasabi by Morimoto Operating Hours",
        "fact_text": "Lunch is served from 12:30 PM to 2:45 PM. Dinner is served from 7:00 PM to 11:45 PM. Smart casual dress code is enforced.",
        "status": "draft"
      }
    ]
  }
  ```

### `POST /knowledge/chunks/{chunk_id}/approve`
Approves an extracted chunk for inclusion in the voice agent's RAG knowledge base.
- **Response (200 OK):** `{"id": "chunk_331", "status": "approved"}`

---

## 4. Voice Scripts & Prompt Studio

### `POST /scripts/generate-draft`
Generates a grounded conversational script draft from approved knowledge.
- **Request:**
  ```json
  {
    "industry_template": "hospitality",
    "language": "hi-IN",
    "tone": "courteous_luxury",
    "goal": "qualify_banquet_inquiry"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "script_id": "scr_5521",
    "version": 1,
    "status": "draft",
    "opening_disclosure": "नमस्ते, मैं ताज होटल से एक स्वचालित डिजिटल सहायक बोल रहा हूँ...",
    "qualification_questions": [
      "आप किस तारीख के लिए आयोजन की योजना बना रहे हैं?",
      "अतिथियों की अनुमानित संख्या कितनी होगी?"
    ],
    "approved_fact_citations": ["chunk_331"]
  }
  ```

### `POST /scripts/{script_id}/activate`
Requires tenant administrator approval to activate a script version for live calling.

---

## 5. Telephony & Calling Operations

### `POST /calls/dispatch`
Initiates an immediate outbound AI voice call (Click-to-Call) for an eligible lead.
- **Request:**
  ```json
  {
    "lead_id": "lead_1048",
    "phone_number_id": "num_vobiz_01",
    "script_id": "scr_5521"
  }
  ```
- **Pre-flight Checks:**
  1. Lead consent exists and lead is not in suppression ledger.
  2. Current time is within IST calling window (09:00 - 21:00 IST).
  3. Tenant has available balance / minutes.
- **Response (202 Accepted):**
  ```json
  {
    "call_id": "call_9901",
    "provider_call_sid": "vob_sid_abc123",
    "status": "initiated",
    "lead_id": "lead_1048",
    "destination": "+919876543210"
  }
  ```

### `POST /telephony/webhooks/{provider_name}`
Standardized webhook receiver for provider call status events (Sarvam, Exotel, Smartflo).
- **Security:** Verifies `X-Provider-Signature` header.
- **Payload Example:**
  ```json
  {
    "event_id": "evt_991823",
    "provider_call_sid": "vob_sid_abc123",
    "call_status": "completed",
    "duration_seconds": 64,
    "transcript": [
      {"speaker": "agent", "text": "नमस्ते, क्या आप 15 दिसंबर को बैंक्वेट बुक करना चाहते हैं?"},
      {"speaker": "user", "text": "हाँ, लगभग 200 लोगों के लिए।"}
    ],
    "summary": "Customer confirmed wedding reception for 200 guests on 15 Dec. Requested quote.",
    "qualification_extracted": {
      "budget": "premium",
      "date": "2026-12-15",
      "guest_count": 200
    },
    "recording_url": "https://storage.provider.com/rec_abc123.mp3"
  }
  ```
- **Response (200 OK):** `{"status": "processed", "idempotent": true}`

### `POST /calls/{call_id}/transfer`
Triggers live human call transfer if supported by the provider, otherwise spawns an urgent callback task.

---

## 6. Campaigns & Follow-up Tasks

### `POST /campaigns`
Creates a batch outbound dialing campaign with concurrency limit and schedule.
- **Request:**
  ```json
  {
    "name": "Diwali Banquet Outreach",
    "script_id": "scr_5521",
    "lead_filter": {"stage": "New", "source": "diwali_promo"},
    "concurrency_limit": 5,
    "max_retries": 2,
    "scheduled_start": "2026-10-20T10:00:00+05:30"
  }
  ```

### `GET /tasks`
Retrieves auto-generated lead follow-up tasks.
- **Query Params:** `status=pending&priority=high`
- **Response (200 OK):** List of follow-up tasks with lead details and action items.

---

## 7. Channels & Compliance

### `POST /channels/whatsapp/webhook`
Receives inbound WhatsApp customer replies and opt-outs (`STOP`). Automatically suppresses opted-out phone numbers.

### `GET /compliance/suppression`
Retrieves tenant suppression list. Supports manual phone addition.
