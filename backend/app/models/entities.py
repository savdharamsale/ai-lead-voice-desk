from datetime import datetime, timezone
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import TenantScopedModel, TimestampMixin, generate_uuid


# 1. Organizations (Top-level Tenant)
class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    billing_plan = Column(String(50), default="pay_as_you_go", nullable=False)
    budget_cap_inr = Column(Float, default=10000.0, nullable=False)
    current_month_spend_inr = Column(Float, default=0.0, nullable=False)


# 2. Users (Global user table)
class User(Base, TimestampMixin):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_platform_admin = Column(Boolean, default=False, nullable=False)


# 3. Memberships & Roles
class Membership(TenantScopedModel):
    __tablename__ = "memberships"
    
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    role = Column(String(50), default="sales_agent", nullable=False)  # tenant_admin, sales_agent, viewer


class Role(Base, TimestampMixin):
    __tablename__ = "roles"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    slug = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    permissions = Column(JSON, default=list, nullable=False)


# 4. Subscriptions & Usage Events
class Subscription(TenantScopedModel):
    __tablename__ = "subscriptions"
    
    plan_name = Column(String(50), nullable=False)
    status = Column(String(50), default="active", nullable=False)
    starts_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime, nullable=True)


class UsageEvent(TenantScopedModel):
    __tablename__ = "usage_events"
    
    event_type = Column(String(50), index=True, nullable=False)  # voice_minute, telephony_pulse, message, number_rental
    quantity = Column(Float, nullable=False)
    unit_cost_inr = Column(Float, nullable=False)
    total_cost_inr = Column(Float, nullable=False)
    reference_id = Column(String(100), index=True, nullable=True)  # call_id or message_id


# 5. Telephony Providers & Virtual Numbers
class ProviderConnection(TenantScopedModel):
    __tablename__ = "provider_connections"
    
    provider_type = Column(String(50), index=True, nullable=False)  # sarvam_vobiz, exotel, smartflo, mock
    encrypted_credentials = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class PhoneNumber(TenantScopedModel):
    __tablename__ = "phone_numbers"
    
    provider_connection_id = Column(String(36), ForeignKey("provider_connections.id"), nullable=True)
    phone_number = Column(String(20), index=True, nullable=False)  # E.164: +91XXXXXXXXXX
    provider_number_id = Column(String(100), nullable=True)
    number_type = Column(String(50), default="virtual_local", nullable=False)
    status = Column(String(50), default="active", nullable=False)
    friendly_name = Column(String(100), nullable=True)


class ChannelConnection(TenantScopedModel):
    __tablename__ = "channel_connections"
    
    channel_type = Column(String(50), index=True, nullable=False)  # whatsapp, instagram
    account_id = Column(String(100), nullable=False)
    encrypted_token = Column(Text, nullable=False)
    webhook_verify_token = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


# 6. Business Profile & Ingestion Constraints
class BusinessProfile(TenantScopedModel):
    __tablename__ = "business_profiles"
    
    company_name = Column(String(255), nullable=False)
    industry_vertical = Column(String(50), nullable=False)  # hospitality, hospital_admin, food_catering, generic_b2b
    website_url = Column(String(500), nullable=True)
    primary_escalation_phone = Column(String(20), nullable=True)
    business_hours = Column(JSON, default=dict, nullable=False)
    trai_principal_entity_id = Column(String(100), nullable=True)
    dlt_header = Column(String(50), nullable=True)


class AllowedDomain(TenantScopedModel):
    __tablename__ = "allowed_domains"
    
    domain = Column(String(255), index=True, nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)


# 7. Knowledge Documents & Grounded Chunks
class CrawledPage(TenantScopedModel):
    __tablename__ = "crawled_pages"
    
    url = Column(String(1000), index=True, nullable=False)
    status = Column(String(50), default="completed", nullable=False)
    http_status = Column(Integer, default=200, nullable=False)
    page_title = Column(String(500), nullable=True)
    text_content = Column(Text, nullable=False)
    page_hash = Column(String(64), nullable=True)
    crawled_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class KnowledgeDocument(TenantScopedModel):
    __tablename__ = "knowledge_documents"
    
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt
    storage_path = Column(String(1000), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    parsing_status = Column(String(50), default="parsed", nullable=False)


class KnowledgeChunk(TenantScopedModel):
    __tablename__ = "knowledge_chunks"
    
    document_id = Column(String(36), ForeignKey("knowledge_documents.id"), nullable=True)
    crawled_page_id = Column(String(36), ForeignKey("crawled_pages.id"), nullable=True)
    chunk_index = Column(Integer, default=0, nullable=False)
    title = Column(String(255), nullable=False)
    fact_text = Column(Text, nullable=False)
    status = Column(String(50), default="draft", index=True, nullable=False)  # draft, approved, rejected
    embedding = Column(JSON, nullable=True)  # pgvector representation or JSON vector


# 8. Agent Templates, Scripts & Versions
class AgentTemplate(Base, TimestampMixin):
    __tablename__ = "agent_templates"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    industry_vertical = Column(String(50), index=True, nullable=False)
    template_name = Column(String(100), nullable=False)
    default_system_prompt = Column(Text, nullable=False)
    default_disclosure = Column(Text, nullable=False)
    is_system_template = Column(Boolean, default=True, nullable=False)


class AgentVersion(TenantScopedModel):
    __tablename__ = "agent_versions"
    
    template_id = Column(String(36), ForeignKey("agent_templates.id"), nullable=True)
    version_number = Column(Integer, default=1, nullable=False)
    prompt_text = Column(Text, nullable=False)
    tone = Column(String(50), default="polite_professional", nullable=False)
    opening_disclosure = Column(Text, nullable=False)
    supported_languages = Column(JSON, default=lambda: ["hi-IN", "en-IN"], nullable=False)
    status = Column(String(50), default="draft", nullable=False)  # draft, active, archived


class Script(TenantScopedModel):
    __tablename__ = "scripts"
    
    agent_version_id = Column(String(36), ForeignKey("agent_versions.id"), nullable=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=False, nullable=False)


# 9. Lead CRM, Sources & Consent
class Lead(TenantScopedModel):
    __tablename__ = "leads"
    
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), index=True, nullable=False)  # E.164
    email = Column(String(255), nullable=True)
    stage = Column(String(50), default="New", index=True, nullable=False)
    source = Column(String(100), default="manual", nullable=False)
    is_suppressed = Column(Boolean, default=False, index=True, nullable=False)
    custom_fields = Column(JSON, default=dict, nullable=False)


class LeadSource(TenantScopedModel):
    __tablename__ = "lead_sources"
    
    name = Column(String(100), nullable=False)
    source_type = Column(String(50), nullable=False)  # web_form, csv_import, meta_ads, api
    is_active = Column(Boolean, default=True, nullable=False)


class ConsentEvent(TenantScopedModel):
    __tablename__ = "consent_events"
    
    lead_id = Column(String(36), ForeignKey("leads.id"), index=True, nullable=True)
    consent_type = Column(String(50), nullable=False)  # web_opt_in, paper_form, inbound_call
    consent_statement = Column(Text, nullable=False)
    channel = Column(String(50), nullable=False)
    ip_address = Column(String(50), nullable=True)
    consented_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class SuppressionEntry(TenantScopedModel):
    __tablename__ = "suppression_entries"
    
    phone_number = Column(String(20), index=True, nullable=False)
    reason = Column(String(100), nullable=False)  # opt_out_call, opt_out_sms, dnd_list, admin_block
    source_channel = Column(String(50), default="call", nullable=False)
    suppressed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


# 10. Campaigns & Recipient Queues
class Campaign(TenantScopedModel):
    __tablename__ = "campaigns"
    
    name = Column(String(255), nullable=False)
    script_id = Column(String(36), ForeignKey("scripts.id"), nullable=False)
    phone_number_id = Column(String(36), ForeignKey("phone_numbers.id"), nullable=False)
    status = Column(String(50), default="draft", nullable=False)  # draft, scheduled, running, paused, completed
    concurrency_limit = Column(Integer, default=5, nullable=False)
    max_retries = Column(Integer, default=2, nullable=False)
    scheduled_start = Column(DateTime, nullable=True)


class CampaignRecipient(TenantScopedModel):
    __tablename__ = "campaign_recipients"
    
    campaign_id = Column(String(36), ForeignKey("campaigns.id"), index=True, nullable=False)
    lead_id = Column(String(36), ForeignKey("leads.id"), index=True, nullable=False)
    call_id = Column(String(36), nullable=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, queued, dialed, completed, failed
    attempts = Column(Integer, default=0, nullable=False)


# 11. Calls, Transcripts, Summaries & Audio Events
class Call(TenantScopedModel):
    __tablename__ = "calls"
    
    lead_id = Column(String(36), ForeignKey("leads.id"), index=True, nullable=True)
    phone_number_id = Column(String(36), ForeignKey("phone_numbers.id"), nullable=True)
    provider_type = Column(String(50), nullable=False)
    provider_call_sid = Column(String(100), unique=True, index=True, nullable=False)
    direction = Column(String(20), default="outbound", nullable=False)  # outbound, inbound
    status = Column(String(50), default="queued", index=True, nullable=False)  # queued, ringing, in_progress, completed, failed, busy, no_answer
    destination = Column(String(20), nullable=False)
    duration_seconds = Column(Integer, default=0, nullable=False)
    agent_minutes_billed = Column(Integer, default=0, nullable=False)
    telephony_pulses_billed = Column(Integer, default=0, nullable=False)
    cost_inr = Column(Float, default=0.0, nullable=False)
    recording_url = Column(String(1000), nullable=True)


class CallEvent(TenantScopedModel):
    __tablename__ = "call_events"
    
    call_id = Column(String(36), ForeignKey("calls.id"), index=True, nullable=False)
    event_type = Column(String(50), nullable=False)  # ringing, answered, dtmf, transfer_attempt, hangup
    payload = Column(JSON, default=dict, nullable=False)
    occurred_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class Transcript(TenantScopedModel):
    __tablename__ = "transcripts"
    
    call_id = Column(String(36), ForeignKey("calls.id"), index=True, nullable=False)
    raw_transcript_json = Column(JSON, default=list, nullable=False)
    full_text = Column(Text, nullable=False)
    speaker_diarization = Column(JSON, default=list, nullable=True)


class CallSummary(TenantScopedModel):
    __tablename__ = "call_summaries"
    
    call_id = Column(String(36), ForeignKey("calls.id"), index=True, nullable=False)
    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=True)
    summary_text = Column(Text, nullable=False)
    sentiment = Column(String(50), default="neutral", nullable=False)
    qualification_data_json = Column(JSON, default=dict, nullable=False)
    recommended_next_action = Column(String(255), nullable=True)


# 12. Tasks, Conversations & Escalation Rules
class Task(TenantScopedModel):
    __tablename__ = "tasks"
    
    lead_id = Column(String(36), ForeignKey("leads.id"), index=True, nullable=True)
    call_id = Column(String(36), ForeignKey("calls.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(50), default="medium", nullable=False)  # low, medium, high, urgent
    status = Column(String(50), default="pending", nullable=False)  # pending, in_progress, completed
    due_date = Column(DateTime, nullable=True)
    assigned_to_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)


class EscalationRule(TenantScopedModel):
    __tablename__ = "escalation_rules"
    
    trigger_type = Column(String(50), nullable=False)  # customer_requested_human, qualification_urgent, booking_value_high
    destination_phone = Column(String(20), nullable=False)
    notify_email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class Conversation(TenantScopedModel):
    __tablename__ = "conversations"
    
    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=True)
    channel_type = Column(String(50), nullable=False)  # whatsapp, instagram
    external_conversation_id = Column(String(100), index=True, nullable=False)


class Message(TenantScopedModel):
    __tablename__ = "messages"
    
    conversation_id = Column(String(36), ForeignKey("conversations.id"), index=True, nullable=False)
    sender_type = Column(String(50), nullable=False)  # user, agent, system
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="text", nullable=False)
    status = Column(String(50), default="sent", nullable=False)


# 13. Audit Logs, Webhooks & Integration Syncs
class AuditLog(TenantScopedModel):
    __tablename__ = "audit_logs"
    
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=True)
    metadata_json = Column(JSON, default=dict, nullable=False)
    ip_address = Column(String(50), nullable=True)


class WebhookEvent(TenantScopedModel):
    __tablename__ = "webhook_events"
    
    provider_name = Column(String(50), index=True, nullable=False)
    provider_event_id = Column(String(100), index=True, nullable=False)
    payload_json = Column(JSON, nullable=False)
    is_processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime, nullable=True)


class IntegrationSync(TenantScopedModel):
    __tablename__ = "integration_syncs"
    
    external_system = Column(String(100), nullable=False)  # zoho, salesforce, hubspot
    status = Column(String(50), default="active", nullable=False)
    last_sync_at = Column(DateTime, nullable=True)
