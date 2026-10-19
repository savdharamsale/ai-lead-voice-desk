from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_healthz_endpoint():
    res = client.get("/healthz")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "AI Lead & Voice Desk" in data["app"]


def test_login_and_crm_endpoints():
    # 1. Login with seeded tenant admin
    login_res = client.post("/api/v1/auth/login", json={
        "email": "manager@grandregal.in",
        "password": "RegalAdmin2026!"
    })
    assert login_res.status_code == 200
    token_data = login_res.json()
    token = token_data["access_token"]
    assert token is not None

    headers = {"Authorization": f"Bearer {token}"}

    # 2. List Leads
    leads_res = client.get("/api/v1/leads", headers=headers)
    assert leads_res.status_code == 200
    leads = leads_res.json()
    assert len(leads) >= 1
    assert any(l["phone"] in ("+919876543210", "+919820123456", "+919876599999") for l in leads)

    # 3. List Scripts
    scripts_res = client.get("/api/v1/scripts", headers=headers)
    assert scripts_res.status_code == 200
    scripts = scripts_res.json()
    assert len(scripts) >= 1

    # 4. Dispatch Click-to-Call
    target_lead_id = leads[0]["id"]
    target_script_id = scripts[0]["id"]
    dispatch_res = client.post("/api/v1/calls/dispatch", headers=headers, json={
        "lead_id": target_lead_id,
        "script_id": target_script_id,
        "provider_name": "mock"
    })
    assert dispatch_res.status_code == 200
    dispatch_data = dispatch_res.json()
    call_sid = dispatch_data["provider_call_sid"]
    assert call_sid.startswith("mock_sid_")

    # 5. Send Carrier Webhook Completion
    webhook_res = client.post("/api/v1/telephony/webhooks/mock", json={
        "event_id": "evt_api_test_101",
        "call_sid": call_sid,
        "status": "completed",
        "duration": 48,
        "summary": "Customer confirmed booking for 100 people.",
        "qualification_extracted": {"guests": 100}
    })
    assert webhook_res.status_code == 200
    assert webhook_res.json()["status"] == "processed"

    # 6. Verify Task Created
    tasks_res = client.get("/api/v1/tasks", headers=headers)
    assert tasks_res.status_code == 200
    tasks = tasks_res.json()
    assert len(tasks) >= 1
    assert any("Follow up" in t["title"] for t in tasks)
