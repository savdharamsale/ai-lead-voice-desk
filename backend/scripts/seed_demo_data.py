from datetime import datetime, timezone
from backend.app.core.database import SessionLocal, Base, engine
from backend.app.core.security import hash_password
from backend.app.models.entities import (
    Organization, User, Membership, PhoneNumber,
    BusinessProfile, Lead, KnowledgeChunk, Script
)
from backend.app.services.prompt_studio import synthesize_voice_script, approve_script
from backend.app.services.knowledge import approve_knowledge_chunk

Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    print("🌱 Seeding Demo Tenants for India-First AI Lead & Voice Desk...")

    # ========================================================
    # Tenant 1: The Grand Regal Hotel (Hospitality)
    # ========================================================
    hotel_org = db.query(Organization).filter(Organization.slug == "grand-regal").first()
    if not hotel_org:
        hotel_org = Organization(
            name="The Grand Regal Hotel & Palace",
            slug="grand-regal",
            billing_plan="pro",
            budget_cap_inr=25000.0,
            current_month_spend_inr=420.0
        )
        db.add(hotel_org)
        db.flush()

        hotel_admin = User(
            email="manager@grandregal.in",
            hashed_password=hash_password("RegalAdmin2026!"),
            full_name="Rajesh Singhania",
            is_active=True,
            is_platform_admin=False
        )
        db.add(hotel_admin)
        db.flush()

        db.add(Membership(organization_id=hotel_org.id, user_id=hotel_admin.id, role="tenant_admin"))
        
        # Phone number
        db.add(PhoneNumber(
            organization_id=hotel_org.id,
            phone_number="+912267890001",
            friendly_name="Mumbai Central Virtual Line"
        ))

        # Business Profile
        db.add(BusinessProfile(
            organization_id=hotel_org.id,
            company_name="The Grand Regal Hotel & Palace",
            industry_vertical="hospitality",
            website_url="https://grandregal.in",
            primary_escalation_phone="+919820011223",
            business_hours={"mon_sun": "08:00 - 23:00"},
            trai_principal_entity_id="110293847561",
            dlt_header="GRREGAL"
        ))

        # Approved Knowledge Chunks
        chunk1 = KnowledgeChunk(
            organization_id=hotel_org.id,
            title="Crystal Ballroom Capacity & Pricing",
            fact_text="The Crystal Ballroom accommodates up to 450 guests. Banquet packages start at ₹2,800 per plate for vegetarian and ₹3,200 for non-vegetarian.",
            status="approved"
        )
        chunk2 = KnowledgeChunk(
            organization_id=hotel_org.id,
            title="Luxury Suites Amenities",
            fact_text="All Royal Suites include complimentary airport transfers, high-speed Wi-Fi, and 24-hour butler service.",
            status="approved"
        )
        db.add_all([chunk1, chunk2])
        db.flush()

        # Script
        script1 = synthesize_voice_script(
            db=db,
            organization_id=hotel_org.id,
            industry_vertical="hospitality",
            company_name="The Grand Regal Hotel",
            language="hi-IN"
        )
        approve_script(db, hotel_org.id, script1.id)

        # Sample Leads
        db.add_all([
            Lead(
                organization_id=hotel_org.id,
                first_name="Vikram",
                last_name="Malhotra",
                phone="+919876543210",
                email="vikram@malhotragroup.in",
                stage="Eligible to Contact",
                source="website_inquiry",
                custom_fields={"event": "Daughter's Wedding", "guests": 300}
            ),
            Lead(
                organization_id=hotel_org.id,
                first_name="Ananya",
                last_name="Deshmukh",
                phone="+919820123456",
                email="ananya.d@deshmukh.com",
                stage="Qualified",
                source="meta_ads",
                custom_fields={"event": "Corporate Annual Gala", "guests": 150}
            )
        ])

    # ========================================================
    # Tenant 2: Apollo Care Clinics (Healthcare Admin)
    # ========================================================
    clinic_org = db.query(Organization).filter(Organization.slug == "apollo-care").first()
    if not clinic_org:
        clinic_org = Organization(
            name="Apollo Care Specialty Clinics",
            slug="apollo-care",
            billing_plan="growth",
            budget_cap_inr=50000.0,
            current_month_spend_inr=1150.0
        )
        db.add(clinic_org)
        db.flush()

        clinic_admin = User(
            email="reception@apollocare.in",
            hashed_password=hash_password("ApolloAdmin2026!"),
            full_name="Dr. Sneha Patil",
            is_active=True,
            is_platform_admin=False
        )
        db.add(clinic_admin)
        db.flush()

        db.add(Membership(organization_id=clinic_org.id, user_id=clinic_admin.id, role="tenant_admin"))
        
        db.add(PhoneNumber(
            organization_id=clinic_org.id,
            phone_number="+918045678901",
            friendly_name="Bangalore Clinic Appointment Line"
        ))

        db.add(BusinessProfile(
            organization_id=clinic_org.id,
            company_name="Apollo Care Specialty Clinics",
            industry_vertical="hospital_admin",
            website_url="https://apollocare.in",
            primary_escalation_phone="+919880099887",
            business_hours={"mon_sat": "08:00 - 20:00"},
            trai_principal_entity_id="110293847599",
            dlt_header="APLCARE"
        ))

        chunk_clinic = KnowledgeChunk(
            organization_id=clinic_org.id,
            title="OPD Clinic Timings and Specialty Services",
            fact_text="Cardiology and Orthopedics OPD operates from 9:00 AM to 1:00 PM and 4:00 PM to 8:00 PM Monday through Saturday.",
            status="approved"
        )
        db.add(chunk_clinic)
        db.flush()

        script2 = synthesize_voice_script(
            db=db,
            organization_id=clinic_org.id,
            industry_vertical="hospital_admin",
            company_name="Apollo Care Specialty Clinics",
            language="en-IN"
        )
        approve_script(db, clinic_org.id, script2.id)

        db.add(Lead(
            organization_id=clinic_org.id,
            first_name="Sunita",
            last_name="Rao",
            phone="+919945012345",
            email="sunita.rao@example.com",
            stage="Eligible to Contact",
            source="doctor_portal_booking",
            custom_fields={"department": "Cardiology Consultation"}
        ))

    db.commit()
    db.close()
    print("✅ Seed data populated successfully!")


if __name__ == "__main__":
    seed()
