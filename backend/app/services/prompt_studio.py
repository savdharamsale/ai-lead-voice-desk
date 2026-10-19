from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.entities import AgentTemplate, AgentVersion, KnowledgeChunk, Script
from backend.app.services.knowledge import get_approved_knowledge

INDUSTRY_TEMPLATES = {
    "hospitality": {
        "title": "Hotel & Hospitality Guest Concierge",
        "opening_disclosure": (
            "नमस्ते! मैं {company_name} की ओर से एक डिजिटल वॉइस असिस्टेंट बोल रहा हूँ। "
            "यह कॉल आपके हालिया पूछताछ के संबंध में है।"
        ),
        "system_guardrails": (
            "You are a polite, courteous, luxury hospitality booking assistant for {company_name}.\n"
            "MANDATORY IDENTITY DISCLOSURE: In your very first sentence, state clearly that you are an AI/automated assistant calling from {company_name}.\n"
            "STRICT GROUNDING: Answer questions ONLY using facts provided in <approved_knowledge>. "
            "NEVER invent room rates, banquet package pricing, discounts, or dates. "
            "If asked about something not in <approved_knowledge>, state: 'I will connect you with our reservations manager to confirm this detail.'\n"
            "QUALIFICATION GOALS: Identify event/stay date, number of guests/rooms, catering preference, and budget.\n"
            "HUMAN TRANSFER: If the caller asks to speak to a person or manager, trigger the transfer tool immediately."
        ),
        "qualification_questions": [
            "आप किस तारीख के लिए बुकिंग की योजना बना रहे हैं?",
            "अतिथियों अथवा कमरों की संख्या कितनी होगी?",
            "क्या आपको बैंक्वेट या डाइनिंग सुविधा की भी आवश्यकता है?"
        ]
    },
    "hospital_admin": {
        "title": "Hospital & Clinic Administration (Non-Clinical)",
        "opening_disclosure": (
            "Hello, I am an automated administrative assistant calling from {company_name}. "
            "This is regarding your appointment inquiry."
        ),
        "system_guardrails": (
            "You are an administrative scheduling assistant for {company_name}.\n"
            "MANDATORY IDENTITY DISCLOSURE: Disclose in your first sentence that you are an automated assistant.\n"
            "CRITICAL NON-CLINICAL SAFETY DIRECTIVE:\n"
            "1. NEVER provide medical diagnosis, symptom triage, health advice, or prescription guidance under any circumstances.\n"
            "2. If the caller describes emergency medical symptoms (chest pain, severe bleeding, breathing distress), immediately urge them: "
            "'Please contact emergency services (112 / 108) or visit the nearest emergency room immediately.'\n"
            "3. Limit your conversation strictly to clinic timings, doctor availability windows, department routing, and booking callbacks.\n"
            "QUALIFICATION GOALS: Identify requested department/specialty, preferred consultation date, and patient contact details."
        ),
        "qualification_questions": [
            "Which department or specialist would you like to consult?",
            "Do you prefer a morning or evening appointment window?",
            "Is this your first visit to our hospital or a follow-up consultation?"
        ]
    },
    "food_catering": {
        "title": "Restaurant & Event Catering Planner",
        "opening_disclosure": (
            "नमस्ते, मैं {company_name} से एक डिजिटल सहायक बोल रहा हूँ। "
            "आपकी कैटरिंग पूछताछ के लिए धन्यवाद।"
        ),
        "system_guardrails": (
            "You are a catering specialist assistant for {company_name}.\n"
            "MANDATORY IDENTITY DISCLOSURE: Disclose synthetic assistant identity in opening greeting.\n"
            "STRICT GROUNDING: Quotes and menus must be grounded strictly in <approved_knowledge>.\n"
            "QUALIFICATION GOALS: Event date, venue location, guest count, vegetarian/non-vegetarian preferences."
        ),
        "qualification_questions": [
            "आपके कार्यक्रम की तारीख और स्थान क्या है?",
            "कितने अतिथियों के लिए भोजन व्यवस्था करनी है?",
            "क्या आपकी कोई विशेष मेनू अथवा शाकाहारी/मांसाहारी प्राथमिकता है?"
        ]
    },
    "generic_b2b": {
        "title": "B2B Sales Qualification (BANT)",
        "opening_disclosure": (
            "Hello, I am an automated AI assistant calling from {company_name}. "
            "I'm reaching out regarding your business inquiry."
        ),
        "system_guardrails": (
            "You are a professional B2B business development assistant for {company_name}.\n"
            "MANDATORY IDENTITY DISCLOSURE: State AI identity up front.\n"
            "QUALIFICATION GOALS: Assess BANT (Budget, Authority, Need, Timeline). Schedule an executive demo."
        ),
        "qualification_questions": [
            "What is the primary business challenge your team is looking to solve?",
            "What is your target timeline for evaluating and deploying a solution?",
            "Would you be open to a 20-minute product demonstration with our solutions architect?"
        ]
    }
}


def synthesize_voice_script(
    db: Session,
    organization_id: str,
    industry_vertical: str,
    company_name: str,
    language: str = "hi-IN",
    tone: str = "polite_professional"
) -> Script:
    """Synthesizes a grounded, unactivated voice script containing only approved tenant knowledge."""
    template_config = INDUSTRY_TEMPLATES.get(industry_vertical) or INDUSTRY_TEMPLATES["generic_b2b"]
    
    # 1. Fetch ONLY approved knowledge chunks
    approved_chunks = get_approved_knowledge(db, organization_id)
    knowledge_text = "\n\n".join([f"[{c.title}]: {c.fact_text}" for c in approved_chunks])
    if not knowledge_text:
        knowledge_text = "No custom knowledge approved yet. Answer only generic contact inquiries."

    opening_disclosure = template_config["opening_disclosure"].format(company_name=company_name)
    base_guardrails = template_config["system_guardrails"].format(company_name=company_name)

    full_system_prompt = (
        f"{base_guardrails}\n\n"
        f"LANGUAGE: Primary conversation language is {language}.\n"
        f"TONE: {tone}.\n\n"
        f"MANDATORY OPENING GREETING:\n\"{opening_disclosure}\"\n\n"
        f"<approved_knowledge>\n{knowledge_text}\n</approved_knowledge>\n\n"
        f"QUALIFICATION CHECKPOINTS:\n" +
        "\n".join([f"- {q}" for q in template_config["qualification_questions"]])
    )

    # Create AgentVersion and Script in Draft state
    agent_version = AgentVersion(
        organization_id=organization_id,
        version_number=1,
        prompt_text=full_system_prompt,
        tone=tone,
        opening_disclosure=opening_disclosure,
        supported_languages=[language],
        status="draft"
    )
    db.add(agent_version)
    db.flush()

    script = Script(
        organization_id=organization_id,
        agent_version_id=agent_version.id,
        title=f"{company_name} - {template_config['title']} (Draft)",
        content=full_system_prompt,
        is_approved=False  # Requires explicit tenant admin approval before activation
    )
    db.add(script)
    db.commit()
    db.refresh(script)
    return script


def approve_script(db: Session, organization_id: str, script_id: str) -> Optional[Script]:
    """Activates a script for production calling after tenant admin review."""
    script = db.query(Script).filter(
        Script.organization_id == organization_id,
        Script.id == script_id
    ).first()
    if script:
        script.is_approved = True
        if script.agent_version_id:
            version = db.query(AgentVersion).filter(AgentVersion.id == script.agent_version_id).first()
            if version:
                version.status = "active"
        db.commit()
        db.refresh(script)
    return script
