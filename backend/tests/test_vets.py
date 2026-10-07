"""
Comprehensive tests for Feature 1:
- Nearby Vet Hospitals (Haversine distance, sorting, 10-minute caching)
- Road Accident SOS Flow
- One-time secure dispatch action & atomic acceptance lock
- Anti-collision concurrency guard (first accept wins)
- 5-minute escalation trigger (advancing to round 2)
- Hospital live dashboard & case status progression
"""
from datetime import datetime, timedelta, timezone
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.hospital import VetHospital
from app.models.accident import AccidentAlert, AlertDispatch
from app.core.security import create_access_token


@pytest_asyncio.fixture
async def seeded_hospitals(test_db_session: AsyncSession):
    """Seed 5 veterinary hospitals around Connaught Place, New Delhi (28.6315, 77.2167)."""
    hospitals = [
        VetHospital(
            name="Delhi Pet Care Center (0.5 km)",
            phone="+911123456701",
            address="CP Radial Road 1, New Delhi",
            latitude=28.6330,
            longitude=27.2180 if False else 77.2180,
            is_24x7=True,
            ambulance_available=True,
            rating=4.9
        ),
        VetHospital(
            name="Karol Bagh Emergency Vet (3.0 km)",
            phone="+911123456702",
            address="Pusa Road, Karol Bagh, New Delhi",
            latitude=28.6450,
            longitude=77.1850,
            is_24x7=True,
            ambulance_available=True,
            rating=4.7
        ),
        VetHospital(
            name="South Ex Animal Hospital (6.5 km)",
            phone="+911123456703",
            address="Ring Road, South Extension, New Delhi",
            latitude=28.5720,
            longitude=77.2200,
            is_24x7=False,
            ambulance_available=False,
            rating=4.5
        ),
        VetHospital(
            name="Noida Pet Emergency (15.0 km)",
            phone="+911202345604",
            address="Sector 18, Noida",
            latitude=28.5700,
            longitude=77.3200,
            is_24x7=True,
            ambulance_available=True,
            rating=4.6
        ),
        VetHospital(
            name="Gurugram Wildlife & Pet Clinic (28.0 km)",
            phone="+911242345605",
            address="DLF Phase 2, Gurugram",
            latitude=28.4800,
            longitude=77.0800,
            is_24x7=False,
            ambulance_available=False,
            rating=4.3
        ),
    ]
    for h in hospitals:
        test_db_session.add(h)
    await test_db_session.commit()
    return hospitals


@pytest.mark.asyncio
async def test_register_vet_hospital(client: AsyncClient):
    payload = {
        "name": "Friendicoes SECA Emergency",
        "phone": "+911124314982",
        "address": "271 & 273 Defence Colony Flyover, New Delhi",
        "latitude": 28.5735,
        "longitude": 77.2341,
        "is_24x7": True,
        "ambulance_available": True
    }
    response = await client.post("/api/v1/vets/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["is_24x7"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_get_nearby_vets_distance_sorting(client: AsyncClient, seeded_hospitals):
    # Query from Connaught Place center
    cp_lat = 28.6315
    cp_lng = 77.2167
    response = await client.get(f"/api/v1/vets/nearby?lat={cp_lat}&lng={cp_lng}&radius=20.0")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["count"] >= 4  # Within 20km (CP, Karol Bagh, South Ex, Noida)

    vets = data["vets"]
    # Check that distances are in strictly ascending order
    distances = [v["distance_meters"] for v in vets]
    assert distances == sorted(distances)
    assert "Delhi Pet Care Center" in vets[0]["name"]


@pytest.mark.asyncio
async def test_nearby_vets_redis_caching(client: AsyncClient, seeded_hospitals):
    cp_lat = 28.6315
    cp_lng = 77.2167

    # First call: cache miss
    res1 = await client.get(f"/api/v1/vets/nearby?lat={cp_lat}&lng={cp_lng}&radius=10.0")
    assert res1.status_code == 200
    assert res1.json()["cached"] is False

    # Second call: cache hit from Redis/memory
    res2 = await client.get(f"/api/v1/vets/nearby?lat={cp_lat}&lng={cp_lng}&radius=10.0")
    assert res2.status_code == 200
    assert res2.json()["cached"] is True
    assert res2.json()["count"] == res1.json()["count"]


@pytest.mark.asyncio
async def test_create_sos_accident_dispatches_3_nearest(client: AsyncClient, seeded_hospitals):
    sos_payload = {
        "animal_type": "dog",
        "condition_description": "Hit by car, bleeding from leg, conscious",
        "photo_url": "https://example.com/photos/injured_dog.jpg",
        "latitude": 28.6315,
        "longitude": 77.2167,
        "address_text": "Outer Circle, Connaught Place, New Delhi",
        "reporter_phone": "+919876543210"
    }

    response = await client.post("/api/v1/accidents/sos", json=sos_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "alerted"
    assert data["animal_type"] == "dog"
    assert len(data["dispatches"]) == 3  # Exactly the 3 nearest hospitals dispatched!

    dispatched_names = [d["hospital_name"] for d in data["dispatches"]]
    assert any("Delhi Pet Care" in n for n in dispatched_names)
    assert any("Karol Bagh" in n for n in dispatched_names)
    assert any("South Ex" in n for n in dispatched_names)


@pytest.mark.asyncio
async def test_hospital_accept_dispatch_atomic_lock(client: AsyncClient, seeded_hospitals, test_db_session: AsyncSession):
    # 1. Report SOS
    sos_payload = {
        "animal_type": "cat",
        "condition_description": "Fractured paw, needs ambulance",
        "latitude": 28.6315,
        "longitude": 77.2167,
        "reporter_phone": "+919876543210"
    }
    sos_res = await client.post("/api/v1/accidents/sos", json=sos_payload)
    alert_id = sos_res.json()["id"]

    # 2. Retrieve one-time secure tokens from DB
    from sqlalchemy import select
    stmt = select(AlertDispatch).where(AlertDispatch.alert_id == alert_id)
    res = await test_db_session.execute(stmt)
    dispatches = res.scalars().all()
    assert len(dispatches) == 3

    hosp1_dispatch = dispatches[0]
    token1 = hosp1_dispatch.secure_token

    # 3. View dispatch details via secure link
    view_res = await client.get(f"/api/v1/accidents/dispatch/{token1}")
    assert view_res.status_code == 200
    assert view_res.json()["alert"]["animal_type"] == "cat"

    # 4. Hospital 1 accepts the case with 20 minutes ETA
    action_payload = {
        "action": "accept",
        "eta_minutes": 20
    }
    accept_res = await client.post(f"/api/v1/accidents/dispatch/{token1}/action", json=action_payload)
    assert accept_res.status_code == 200
    acc_data = accept_res.json()
    assert acc_data["success"] is True
    assert acc_data["alert_status"] == "accepted"
    assert acc_data["eta_minutes"] == 20

    # 5. Verify alert status is updated
    alert_res = await client.get(f"/api/v1/accidents/{alert_id}")
    assert alert_res.status_code == 200
    assert alert_res.json()["status"] == "accepted"
    assert alert_res.json()["eta_minutes"] == 20
    assert alert_res.json()["accepted_hospital_id"] == hosp1_dispatch.hospital_id


@pytest.mark.asyncio
async def test_competing_hospital_collision_guard(client: AsyncClient, seeded_hospitals, test_db_session: AsyncSession):
    # Report SOS
    sos_payload = {
        "animal_type": "cow",
        "condition_description": "Lying on roadside divider",
        "latitude": 28.6315,
        "longitude": 77.2167,
        "reporter_phone": "+919876543210"
    }
    sos_res = await client.post("/api/v1/accidents/sos", json=sos_payload)
    alert_id = sos_res.json()["id"]

    stmt = select(AlertDispatch).where(AlertDispatch.alert_id == alert_id)
    res = await test_db_session.execute(stmt)
    dispatches = res.scalars().all()
    token1 = dispatches[0].secure_token
    token2 = dispatches[1].secure_token

    # Hospital 1 accepts first
    await client.post(f"/api/v1/accidents/dispatch/{token1}/action", json={"action": "accept", "eta_minutes": 15})

    # Hospital 2 attempts to accept after Hospital 1 -> 409 Conflict (case already locked)
    second_res = await client.post(
        f"/api/v1/accidents/dispatch/{token2}/action",
        json={"action": "accept", "eta_minutes": 10}
    )
    assert second_res.status_code == 409
    assert "already been accepted" in second_res.json()["message"]


@pytest.mark.asyncio
async def test_hospital_decline_dispatch(client: AsyncClient, seeded_hospitals, test_db_session: AsyncSession):
    sos_payload = {
        "animal_type": "bird",
        "condition_description": "Fallen from tree, wing injury",
        "latitude": 28.6315,
        "longitude": 77.2167
    }
    sos_res = await client.post("/api/v1/accidents/sos", json=sos_payload)
    alert_id = sos_res.json()["id"]

    stmt = select(AlertDispatch).where(AlertDispatch.alert_id == alert_id)
    res = await test_db_session.execute(stmt)
    token1 = res.scalars().first().secure_token

    decline_res = await client.post(
        f"/api/v1/accidents/dispatch/{token1}/action",
        json={"action": "decline", "decline_reason": "No avian specialist currently on duty"}
    )
    assert decline_res.status_code == 200
    assert "declined" in decline_res.json()["message"]

    # Alert should still be 'alerted'
    alert_status_res = await client.get(f"/api/v1/accidents/{alert_id}")
    assert alert_status_res.json()["status"] == "alerted"


@pytest.mark.asyncio
async def test_escalation_to_round_2_after_timeout(client: AsyncClient, seeded_hospitals, test_db_session: AsyncSession):
    # 1. Create SOS alert
    sos_payload = {
        "animal_type": "dog",
        "condition_description": "Hit and run, urgent",
        "latitude": 28.6315,
        "longitude": 77.2167
    }
    sos_res = await client.post("/api/v1/accidents/sos", json=sos_payload)
    alert_id = sos_res.json()["id"]

    # 2. Simulate 5-minute timeout passing by updating expires_at to 10 minutes ago
    stmt = select(AlertDispatch).where(AlertDispatch.alert_id == alert_id)
    res = await test_db_session.execute(stmt)
    dispatches = res.scalars().all()
    assert len(dispatches) == 3

    past_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    for d in dispatches:
        d.expires_at = past_time
    await test_db_session.commit()

    # 3. Trigger escalation worker endpoint
    esc_res = await client.post("/api/v1/accidents/cron/escalate")
    assert esc_res.status_code == 200
    assert esc_res.json()["escalated_alerts"] >= 1

    # 4. Check alert now has round 2 dispatches
    updated_alert = await client.get(f"/api/v1/accidents/{alert_id}")
    all_dispatches = updated_alert.json()["dispatches"]
    # 3 initial + 2 remaining hospitals in the seed (Noida & Gurugram)
    rounds = [d["escalation_round"] for d in all_dispatches]
    assert 2 in rounds


@pytest.mark.asyncio
async def test_hospital_dashboard_and_status_advancement(client: AsyncClient, seeded_hospitals, test_db_session: AsyncSession):
    # Create hospital user
    hosp_user = User(
        phone="+919876500001",
        email="hospital.staff@test.org",
        role_id=2,  # hospital role
        is_verified=True,
        is_active=True
    )
    test_db_session.add(hosp_user)
    await test_db_session.commit()
    await test_db_session.refresh(hosp_user)

    # Link user to first hospital
    h1 = seeded_hospitals[0]
    h1.user_id = hosp_user.id
    await test_db_session.commit()

    hosp_token = create_access_token(subject=hosp_user.id, role="hospital")

    # Create and accept an alert
    sos_res = await client.post("/api/v1/accidents/sos", json={
        "animal_type": "dog",
        "latitude": 28.6315,
        "longitude": 77.2167
    })
    alert_id = sos_res.json()["id"]

    # Get dispatch token for this hospital
    stmt = select(AlertDispatch).where(
        AlertDispatch.alert_id == alert_id,
        AlertDispatch.hospital_id == h1.id
    )
    res = await test_db_session.execute(stmt)
    token = res.scalar_one().secure_token

    # Accept case
    await client.post(f"/api/v1/accidents/dispatch/{token}/action", json={"action": "accept", "eta_minutes": 10})

    # View hospital dashboard
    dash_res = await client.get(
        "/api/v1/accidents/hospital/dashboard",
        headers={"Authorization": f"Bearer {hosp_token}"}
    )
    assert dash_res.status_code == 200
    alerts = dash_res.json()
    assert len(alerts) >= 1
    assert any(a["id"] == alert_id for a in alerts)

    # Update case status to 'reached'
    reached_res = await client.patch(
        f"/api/v1/accidents/{alert_id}/status",
        headers={"Authorization": f"Bearer {hosp_token}"},
        json={"status": "reached"}
    )
    assert reached_res.status_code == 200
    assert reached_res.json()["status"] == "reached"

    # Update case status to 'closed'
    closed_res = await client.patch(
        f"/api/v1/accidents/{alert_id}/status",
        headers={"Authorization": f"Bearer {hosp_token}"},
        json={"status": "closed"}
    )
    assert closed_res.status_code == 200
    assert closed_res.json()["status"] == "closed"
