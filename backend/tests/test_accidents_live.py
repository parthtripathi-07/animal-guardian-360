import pytest
from httpx import AsyncClient
from app.models.hospital import VetHospital
from app.models.accident import AccidentAlert
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_accident_live_status_endpoint(client: AsyncClient, test_db_session: AsyncSession):
    # Seed hospital & alert
    hosp = VetHospital(
        name="CP Emergency Veterinary Center",
        phone="+919876543210",
        address="Connaught Place, New Delhi",
        latitude=28.632,
        longitude=77.218,
        is_24x7=True,
        ambulance_available=True,
        rating=4.9
    )
    test_db_session.add(hosp)
    await test_db_session.commit()
    await test_db_session.refresh(hosp)

    alert = AccidentAlert(
        animal_type="dog",
        condition_description="Injured paw",
        latitude=28.6315,
        longitude=77.2167,
        status="accepted",
        accepted_hospital_id=hosp.id,
        eta_minutes=15
    )
    test_db_session.add(alert)
    await test_db_session.commit()
    await test_db_session.refresh(alert)

    resp = await client.get(f"/api/v1/accidents/{alert.id}/live-status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["alert_id"] == alert.id
    assert data["status"] == "accepted"
    assert data["accepted_hospital_name"] == hosp.name
    assert data["eta_minutes"] == 15
    assert data["dispatches_count"] == 0


@pytest.mark.asyncio
async def test_accident_live_status_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/accidents/non-existent-alert-id/live-status")
    assert resp.status_code == 404

