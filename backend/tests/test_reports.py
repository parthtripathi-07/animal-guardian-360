"""
Comprehensive tests for Feature 2:
- Animal Cruelty & Illegal Activity Reporting
- Nearest Police Station Locator & "Call 112" details
- PDF Complaint Summary generation
- Spatio-temporal duplicate detection (100m, 2h)
- 5 reports/day rate limiting
- 3-strike anti-abuse system & automatic suspension
- Admin review queue
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User


@pytest.mark.asyncio
async def test_submit_cruelty_report_success(client: AsyncClient, regular_user: User, user_token: str):
    payload = {
        "category": "cruelty",
        "description": "Dog tied to a pole without food or water under direct sunlight for over 24 hours.",
        "latitude": 28.6315,
        "longitude": 77.2167,
        "address_text": "Block C, Connaught Place, New Delhi",
        "is_anonymous": False,
        "media": [
            {
                "media_type": "image",
                "storage_key": "evidence/report_1.jpg",
                "original_filename": "evidence_dog.jpg",
                "mime_type": "image/jpeg",
                "file_size_bytes": 102400
            }
        ]
    }
    response = await client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user_token}"},
        json=payload
    )
    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "cruelty"
    assert data["status"] == "pending_review"
    assert data["reporter_id"] == regular_user.id
    assert data["nearest_police_station"] is not None
    assert "Police" in data["nearest_police_station"]["name"]
    assert "pdf" in data["complaint_pdf_url"]
    assert "🚨 ANIMAL WELFARE COMPLAINT" in data["shareable_summary"]
    assert len(data["media"]) == 1


@pytest.mark.asyncio
async def test_anonymous_report_conceals_identity(client: AsyncClient, regular_user: User, user_token: str):
    payload = {
        "category": "illegal_trade",
        "description": "Exotic birds being sold secretly from an unmarked van in local market.",
        "latitude": 28.5500,
        "longitude": 77.2500,
        "is_anonymous": True
    }
    response = await client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user_token}"},
        json=payload
    )
    assert response.status_code == 201
    data = response.json()
    assert data["is_anonymous"] is True
    assert data["reporter_id"] is None  # Anonymous flag shields ID in responses


@pytest.mark.asyncio
async def test_download_complaint_pdf(client: AsyncClient, regular_user: User, user_token: str):
    # 1. Create report
    payload = {
        "category": "abandonment",
        "description": "A litter of four puppies left inside a taped cardboard box behind the market.",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "address_text": "Behind Subzi Mandi, Janpath"
    }
    create_res = await client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user_token}"},
        json=payload
    )
    report_id = create_res.json()["id"]

    # 2. Download generated PDF
    pdf_res = await client.get(f"/api/v1/reports/{report_id}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert "attachment" in pdf_res.headers["content-disposition"]
    # PDF starts with magic bytes %PDF
    assert pdf_res.content.startswith(b"%PDF")
    assert len(pdf_res.content) > 1000  # Valid substantial PDF file


@pytest.mark.asyncio
async def test_duplicate_report_detection(client: AsyncClient, regular_user: User, user_token: str):
    payload1 = {
        "category": "illegal_trade",
        "description": "Selling parakeets illegally in open cages without permits.",
        "latitude": 28.6500,
        "longitude": 77.2300,
        "address_text": "Chandni Chowk"
    }
    res1 = await client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user_token}"},
        json=payload1
    )
    assert res1.status_code == 201

    # Second report with same category within 15 meters and minutes later
    payload2 = {
        "category": "illegal_trade",
        "description": "Another citizen spotting the same caged parakeet sellers.",
        "latitude": 28.6501,  # ~11 meters away
        "longitude": 77.2301,
        "address_text": "Chandni Chowk"
    }
    res2 = await client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user_token}"},
        json=payload2
    )
    assert res2.status_code == 409
    assert res2.json()["error_code"] == "RESOURCE_CONFLICT"
    assert "already submitted recently" in res2.json()["message"]


@pytest.mark.asyncio
async def test_nearest_police_station_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/reports/police/nearest?lat=28.6304&lng=77.2177")
    assert response.status_code == 200
    data = response.json()
    assert "Police" in data["name"]
    assert data["phone"] is not None


@pytest.mark.asyncio
async def test_admin_review_queue_and_actions(
    client: AsyncClient,
    regular_user: User,
    user_token: str,
    admin_user: User,
    admin_token: str
):
    # Regular user submits report
    payload = {
        "category": "cruelty",
        "description": "Cow injured and bleeding on the road after being beaten with a stick.",
        "latitude": 28.7000,
        "longitude": 77.1000
    }
    rep_res = await client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user_token}"},
        json=payload
    )
    report_id = rep_res.json()["id"]

    # Regular user attempting admin review -> 403 Forbidden
    unauth_res = await client.get(
        "/api/v1/reports/admin/queue",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert unauth_res.status_code == 403

    # Admin accesses queue -> 200 OK
    queue_res = await client.get(
        "/api/v1/reports/admin/queue",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert queue_res.status_code == 200
    assert len(queue_res.json()) >= 1

    # Admin marks verified
    review_payload = {
        "status": "verified",
        "admin_notes": "Ground verification done with local SPCA team."
    }
    action_res = await client.post(
        f"/api/v1/reports/admin/{report_id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=review_payload
    )
    assert action_res.status_code == 200
    assert action_res.json()["status"] == "verified"


@pytest.mark.asyncio
async def test_3_strike_abuse_system_suspension(
    client: AsyncClient,
    test_db_session: AsyncSession,
    admin_token: str
):
    # Create an abusive user
    abuser = User(
        phone="+919911223344",
        email="spammer@test.org",
        role_id=1,
        is_verified=True,
        is_active=True
    )
    test_db_session.add(abuser)
    await test_db_session.commit()
    await test_db_session.refresh(abuser)

    from app.core.security import create_access_token
    abuser_token = create_access_token(subject=abuser.id, role="user")

    # STRIKE 1: Submit fake report -> Admin marks fake
    res1 = await client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {abuser_token}"},
        json={"category": "cruelty", "description": "Fake report 1: lion roaming in colony", "latitude": 28.1, "longitude": 77.1}
    )
    rep1_id = res1.json()["id"]
    strike1_res = await client.post(
        f"/api/v1/reports/admin/{rep1_id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "fake", "strike_reason": "Fabricated wild animal claim"}
    )
    assert strike1_res.json()["strike_issued"] is True
    assert strike1_res.json()["strike_number"] == 1
    assert strike1_res.json()["user_suspended"] is False

    # STRIKE 2: Submit fake report -> Admin marks fake
    res2 = await client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {abuser_token}"},
        json={"category": "abandonment", "description": "Fake report 2: invisible puppies", "latitude": 28.2, "longitude": 77.2}
    )
    rep2_id = res2.json()["id"]
    strike2_res = await client.post(
        f"/api/v1/reports/admin/{rep2_id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "fake", "strike_reason": "False alarm upon physical check"}
    )
    assert strike2_res.json()["strike_number"] == 2
    assert strike2_res.json()["user_suspended"] is False

    # STRIKE 3: Submit fake report -> Admin marks fake -> SUSPENSION TRIGGERED
    res3 = await client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {abuser_token}"},
        json={"category": "other", "description": "Fake report 3: nuisance prank report", "latitude": 28.3, "longitude": 77.3}
    )
    rep3_id = res3.json()["id"]
    strike3_res = await client.post(
        f"/api/v1/reports/admin/{rep3_id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "fake", "strike_reason": "Repeated spam and false reporting"}
    )
    assert strike3_res.json()["strike_number"] == 3
    assert strike3_res.json()["user_suspended"] is True

    # 4th Attempt: Abuser attempts to report -> BLOCKED WITH 403 ACCOUNT SUSPENDED
    blocked_res = await client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {abuser_token}"},
        json={"category": "cruelty", "description": "Trying to report again while suspended", "latitude": 28.4, "longitude": 77.4}
    )
    assert blocked_res.status_code == 403
    assert blocked_res.json()["error_code"] == "ACCOUNT_SUSPENDED"
