"""
Comprehensive unit and integration tests for Authentication and User flows.
"""
import pytest
from httpx import AsyncClient
from app.models.user import User


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Animal Guardian 360" in data["app"]


@pytest.mark.asyncio
async def test_send_otp_phone_success(client: AsyncClient):
    payload = {
        "identifier": "+919876543210",
        "purpose": "login"
    }
    response = await client.post("/api/v1/auth/otp/send", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["identifier"] == "+919876543210"
    assert "dev_otp" in data
    assert len(data["dev_otp"]) == 6


@pytest.mark.asyncio
async def test_send_otp_indian_phone_auto_normalization(client: AsyncClient):
    # Pass 10-digit standard Indian number without +91 prefix
    payload = {
        "identifier": "9876543210",
        "purpose": "login"
    }
    response = await client.post("/api/v1/auth/otp/send", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["identifier"] == "+919876543210"


@pytest.mark.asyncio
async def test_send_otp_email_success(client: AsyncClient):
    payload = {
        "identifier": "rescue.hero@example.com",
        "purpose": "login"
    }
    response = await client.post("/api/v1/auth/otp/send", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["identifier"] == "rescue.hero@example.com"
    assert data["dev_otp"] is not None


@pytest.mark.asyncio
async def test_send_otp_invalid_phone(client: AsyncClient):
    payload = {
        "identifier": "12345",  # Invalid number
        "purpose": "login"
    }
    response = await client.post("/api/v1/auth/otp/send", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_verify_otp_and_login_new_user(client: AsyncClient):
    phone = "+919812345678"

    # Step 1: Send OTP
    send_res = await client.post("/api/v1/auth/otp/send", json={"identifier": phone, "purpose": "login"})
    assert send_res.status_code == 200
    otp = send_res.json()["dev_otp"]

    # Step 2: Verify OTP
    verify_res = await client.post(
        "/api/v1/auth/otp/verify",
        json={"identifier": phone, "code": otp, "purpose": "login"}
    )
    assert verify_res.status_code == 200
    data = verify_res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["phone"] == phone
    assert data["user"]["is_verified"] is True
    assert data["user"]["role"] == "user"


@pytest.mark.asyncio
async def test_verify_otp_incorrect_code(client: AsyncClient):
    phone = "+919812345679"
    await client.post("/api/v1/auth/otp/send", json={"identifier": phone, "purpose": "login"})

    # Submit wrong OTP
    verify_res = await client.post(
        "/api/v1/auth/otp/verify",
        json={"identifier": phone, "code": "000000", "purpose": "login"}
    )
    assert verify_res.status_code == 400
    data = verify_res.json()
    assert data["error_code"] == "INVALID_OTP"
    assert "Incorrect verification code" in data["message"]


@pytest.mark.asyncio
async def test_refresh_token_lifecycle(client: AsyncClient):
    phone = "+919877766554"
    send_res = await client.post("/api/v1/auth/otp/send", json={"identifier": phone, "purpose": "login"})
    otp = send_res.json()["dev_otp"]

    verify_res = await client.post(
        "/api/v1/auth/otp/verify",
        json={"identifier": phone, "code": otp, "purpose": "login"}
    )
    refresh_token = verify_res.json()["refresh_token"]

    # Use refresh token to get a new pair
    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.corrupted.token"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient, regular_user: User, user_token: str):
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == regular_user.id
    assert data["full_name"] == regular_user.full_name
    assert data["email"] == regular_user.email
    assert data["role"] == "user"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_me_profile(client: AsyncClient, regular_user: User, user_token: str):
    update_payload = {
        "full_name": "Aarav S. (Updated)",
        "preferred_locale": "hi"
    }
    response = await client.patch(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {user_token}"},
        json=update_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Aarav S. (Updated)"
    assert data["preferred_locale"] == "hi"


@pytest.mark.asyncio
async def test_update_me_email_conflict(client: AsyncClient, regular_user: User, user_token: str, admin_user: User):
    # Try to set regular_user's email to admin_user's existing email
    response = await client.patch(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"email": admin_user.email}
    )
    assert response.status_code == 409
    assert response.json()["error_code"] == "RESOURCE_CONFLICT"


@pytest.mark.asyncio
async def test_otp_max_attempts_lockout(client: AsyncClient):
    phone = "+919876543999"
    send_res = await client.post("/api/v1/auth/otp/send", json={"identifier": phone, "purpose": "login"})
    assert send_res.status_code == 200

    # Submit 3 wrong attempts
    for _ in range(3):
        res = await client.post(
            "/api/v1/auth/otp/verify",
            json={"identifier": phone, "code": "000000", "purpose": "login"}
        )
        assert res.status_code == 400

    # 4th attempt should be blocked due to invalidation / max attempts exceeded
    fourth_res = await client.post(
        "/api/v1/auth/otp/verify",
        json={"identifier": phone, "code": "000000", "purpose": "login"}
    )
    assert fourth_res.status_code == 400
    assert "No active verification code found" in fourth_res.json()["message"] or "invalidated" in fourth_res.json()["message"]


@pytest.mark.asyncio
async def test_role_authorization_check(client: AsyncClient, regular_user: User, user_token: str, admin_token: str):
    from app.core.dependencies import require_roles
    from fastapi import Depends

    # Attach temporary test routes with role dependencies
    @client._transport.app.get("/test-admin-only")
    async def admin_only_endpoint(user: User = Depends(require_roles(["admin"]))):
        return {"authorized": True, "user_id": user.id}

    # Regular user attempting admin endpoint -> 403 Forbidden
    user_res = await client.get("/test-admin-only", headers={"Authorization": f"Bearer {user_token}"})
    assert user_res.status_code == 403
    assert user_res.json()["error_code"] == "PERMISSION_DENIED"

    # Admin user accessing admin endpoint -> 200 OK
    admin_res = await client.get("/test-admin-only", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_res.status_code == 200
    assert admin_res.json()["authorized"] is True


@pytest.mark.asyncio
async def test_require_active_reporter_suspended(client: AsyncClient, regular_user: User, user_token: str, test_db_session):
    from datetime import datetime, timedelta, timezone
    from app.core.dependencies import require_active_reporter
    from fastapi import Depends

    @client._transport.app.get("/test-reporter-only")
    async def reporter_only_endpoint(user: User = Depends(require_active_reporter)):
        return {"authorized": True}

    # Initially not suspended
    res_ok = await client.get("/test-reporter-only", headers={"Authorization": f"Bearer {user_token}"})
    assert res_ok.status_code == 200

    # Suspend user
    regular_user.reporting_suspended_until = datetime.now(timezone.utc) + timedelta(days=7)
    await test_db_session.commit()

    # Now should be blocked with 403 Account Suspended
    res_blocked = await client.get("/test-reporter-only", headers={"Authorization": f"Bearer {user_token}"})
    assert res_blocked.status_code == 403
    assert res_blocked.json()["error_code"] == "ACCOUNT_SUSPENDED"
