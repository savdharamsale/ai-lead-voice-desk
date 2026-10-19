import pytest
from backend.app.models.entities import Organization
from backend.app.services.knowledge import approve_knowledge_chunk, ingest_crawled_content
from backend.app.services.prompt_studio import (
    INDUSTRY_TEMPLATES,
    approve_script,
    synthesize_voice_script,
)
from backend.app.services.sarvam_client import SarvamVoiceAgentClient


def test_hospitality_script_grounding(db):
    org = Organization(name="The Taj Palace", slug="taj-palace")
    db.add(org)
    db.commit()

    # 1. Ingest & Approve a specific fact
    crawled = ingest_crawled_content(
        db=db,
        organization_id=org.id,
        url="https://taj.example/banquets",
        page_title="Ballroom",
        raw_content="The Crystal Ballroom accommodates 350 banquet guests with mandatory 50% advance booking."
    )
    from backend.app.models.entities import KnowledgeChunk
    chunk = db.query(KnowledgeChunk).filter(KnowledgeChunk.organization_id == org.id).first()
    approve_knowledge_chunk(db, org.id, chunk.id)

    # 2. Synthesize script
    script = synthesize_voice_script(
        db=db,
        organization_id=org.id,
        industry_vertical="hospitality",
        company_name="The Taj Palace",
        language="hi-IN"
    )

    assert script.is_approved is False
    assert "The Crystal Ballroom accommodates 350 banquet guests" in script.content
    assert "<approved_knowledge>" in script.content
    assert "MANDATORY IDENTITY DISCLOSURE" in script.content
    assert "The Taj Palace" in script.content

    # 3. Approve script
    approved = approve_script(db, org.id, script.id)
    assert approved.is_approved is True


def test_hospital_admin_anti_clinical_directive(db):
    org = Organization(name="Apollo Care", slug="apollo-care")
    db.add(org)
    db.commit()

    script = synthesize_voice_script(
        db=db,
        organization_id=org.id,
        industry_vertical="hospital_admin",
        company_name="Apollo Care Clinic",
        language="en-IN"
    )

    # Must contain critical non-clinical directives
    assert "NEVER provide medical diagnosis" in script.content
    assert "CRITICAL NON-CLINICAL SAFETY DIRECTIVE" in script.content
    assert "emergency services (112 / 108)" in script.content


@pytest.mark.asyncio
async def test_sarvam_voice_client():
    client = SarvamVoiceAgentClient()
    langs = client.get_supported_languages()
    assert "hi-IN" in langs
    assert "te-IN" in langs
    assert "en-IN" in langs

    res = await client.create_voice_agent(
        agent_name="Taj Reception Bot",
        system_prompt="You are a hotel receptionist.",
        language_code="hi-IN"
    )
    assert "agent_id" in res
    assert res["status"] == "ready"
