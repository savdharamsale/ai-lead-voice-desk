# Provider Capability Matrix: Indian Cloud Telephony & AI Voice

**Status:** Verified Baseline (Phase 0 / Superpowers Research)  
**Date:** 19 October 2026  
**Market:** India  
**Sources:** Sarvam AI Docs, Exotel Developer Docs, Tata Tele Business Services Smartflo Docs, TRAI Regulations.

---

## 1. Provider Comparison Matrix

| Capability | Sarvam Telephony (Vobiz Powered) | Exotel | Tata Tele Smartflo | Direct Vobiz Account | Mock Telephony Adapter |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Primary Product Role** | **Default MVP & Fast Pilot** | **Preferred India Production** | **Enterprise Alternative** | **Alternative Direct Route** | **Automated Tests & CI/CD** |
| **Number Rental / Provisioning** | ✅ Self-serve in Sarvam portal (₹59/mo per number) | ⚠️ Manual KYC + Account Manager allocation | ⚠️ Enterprise onboarding + KYC required | ⚠️ Direct Vobiz onboarding + KYC | ✅ Simulated instant provisioning |
| **Inbound Call Handling** | ✅ Direct routing to Sarvam Voice Agents | ✅ Supported via Applets/Webhooks | ✅ Supported via Smartflo IVR Flow | ✅ Supported via Sarvam webhook | ✅ Fully simulated |
| **Outbound Calling API** | ✅ Sarvam outbound campaign / dial API | ✅ Exotel REST Call API (`/v1/Accounts/{sid}/Calls/connect`) | ✅ Smartflo Click-to-call / Campaign API | ✅ Vobiz Outbound Call API | ✅ Fully simulated with instant response |
| **Call Status Webhooks** | ✅ Granular events (ringing, connected, completed) | ✅ Passthru / StatusCallback URLs | ✅ Webhook notifications configured in portal | ✅ Standard event webhooks | ✅ Instant mock webhook generator |
| **Live Audio Streaming / Voicebot** | ✅ Native built-in Sarvam Agent integration | ✅ Exotel Voicebot Stream (WebSockets / Media Stream) | ⚠️ Custom integration via SIP Trunk / Voice Gateway | ✅ Native Sarvam integration | ✅ Simulated mock audio stream |
| **Human Call Transfer (Live)** | ✅ **Fully supported end-to-end (self-serve)** | ⚠️ **Not self-serve in Sarvam** (Requires custom Exotel applet) | ⚠️ **Not self-serve in Sarvam** (Requires custom Smartflo IVR transfer) | ✅ **Fully supported end-to-end (self-serve)** | ✅ Simulated instant transfer & fallback |
| **DTMF Input Detection** | ✅ Supported in Sarvam Voice Agents | ✅ Supported via Exotel Applets | ✅ Supported via Smartflo IVR nodes | ✅ Supported | ✅ Simulated DTMF events |
| **Call Recording & Metadata** | ✅ Configurable recording URL + metadata | ✅ S3/Exotel recording URL with retention | ✅ Smartflo portal recording storage | ✅ Vobiz recording storage | ✅ Mock recording URLs & metadata |
| **Transcript & AI Summaries** | ✅ Provided directly in Sarvam call webhook | ⚠️ Requires downstream ASR/Sarvam pipeline | ⚠️ Requires downstream ASR/Sarvam pipeline | ✅ Provided when routed via Sarvam | ✅ Synthetic structured summaries |
| **Usage & Cost Reporting** | ✅ Documented rates (₹0.20/30s pulse + ₹3.50/min agent) | ⚠️ Variable per-minute carrier billing + platform fee | ⚠️ Enterprise SLA contract billing | ⚠️ Direct Vobiz carrier rates | ✅ Deterministic simulated billing |

*Legend: ✅ Confirmed Supported | ⚠️ Requires Custom Integration / Provider Approval / Unverified | ❌ Not Supported*

---

## 2. Indicative Pricing & Commercial Comparison

> [!WARNING]
> Published rates are indicative as of October 2026 and exclude 18% GST. Rates must be verified with providers prior to commercial deployment.

### 2.1 Sarvam AI & Telephony
- **Voice Agent Engine:**
  - *Pay-as-you-go:* ₹3.50 / agent minute
  - *Pro Plan:* ₹3.25 / agent minute + ₹9,999 / month base
  - *Growth Plan:* ₹3.15 / agent minute + ₹49,999 / month base
- **Sarvam Telephony (Vobiz infrastructure):**
  - *Outbound / Inbound Pulse:* ₹0.20 per 30-second pulse (₹0.40 / minute equivalent)
  - *PSTN Call Forwarding (Transfer):* ₹0.40 per 30-second pulse (₹0.80 / minute)
  - *SIP Forwarding:* ₹0.35 per 30-second pulse
  - *Virtual Phone Number Rental:* ₹59 per number / 30 days
- **Cost Calculation Example:**
  - A 45-second qualified lead call with human transfer:
    - Sarvam Agent: 1 minute billable = ₹3.50
    - Telephony Pulses: 2 pulses (45s rounded up to 60s) @ ₹0.20 = ₹0.40
    - PSTN Forwarding: 1 pulse (say 20s talk with human) @ ₹0.40 = ₹0.40
    - **Total Call Cost:** ₹4.30 + GST

### 2.2 Exotel (Indicative)
- Cloud PBX / Voicebot subscriptions typically start with software platform retainers (~₹20,000–₹50,000/year) plus outgoing call pulse rates (~₹0.45–₹0.70/min) and incoming virtual number rents.
- Voicebot bidirectional media streaming requires an approved Exotel developer account and plan add-on.

### 2.3 Tata Tele Smartflo (Indicative)
- Enterprise multi-agent cloud communication package billed annually or semi-annually. Custom quotes based on concurrent call channels and PRI/SIP trunking rates.

---

## 3. KYC, Regulatory & Provisioning Requirements (India)

### 3.1 Regulatory Framework
1. **TRAI TCCCPR (Telecom Commercial Communications Customer Preference Regulations):**
   - Commercial calls must adhere to DLT (Distributed Ledger Technology) requirements.
   - Senders must register as Principal Entities (PE) on telecom DLT portals (Jio, Airtel, Vodafone Idea, BSNL).
   - Calling hours are strictly restricted to 09:00 AM to 09:00 PM IST for promotional communications.
2. **Mandatory KYC for Number Allocation:**
   - Certificate of Incorporation / GST Certificate / Shop & Establishment License.
   - Authorized Signatory PAN Card and Aadhaar (with OTP verification).
   - Utility bill / proof of business address in India.
   - Letter of authorization on company letterhead.
3. **Call Transfer Reality & Architectural Fallback:**
   - **Crucial Architectural Rule:** Because self-serve call transfer is confirmed only for Vobiz and Plivo in Sarvam's documentation, our platform **must never assume transfer is globally available**.
   - If a tenant uses Exotel or Smartflo, the system checks the `can_transfer_live` capability flag. If `False`, the agent gracefully triggers the **Human Fallback Workflow**:
     1. Informs the customer: *"Our specialist is currently assisting another client. I have logged your priority callback request."*
     2. Immediately creates a high-priority `Task` in the CRM.
     3. Dispatches instant SMS / WhatsApp / Email alert to the business admin.
