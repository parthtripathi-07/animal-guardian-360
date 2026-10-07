import io
import pytest
from httpx import AsyncClient, ASGITransport
from PIL import Image

from app.main import app
from app.services.media_service import media_service
from app.services.notification import notification_service


@pytest.mark.asyncio
async def test_media_service_exif_stripping():
    # Create test JPEG with mock info
    img = Image.new("RGB", (64, 64), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    raw_bytes = buf.getvalue()

    clean_bytes = media_service.strip_exif_metadata(raw_bytes, format="JPEG")
    assert isinstance(clean_bytes, bytes)
    assert len(clean_bytes) > 0


@pytest.mark.asyncio
async def test_media_service_malware_scanner():
    clean_ok, status = media_service.scan_for_malware("photo.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 20)
    assert clean_ok is True
    assert status == "clean"

    bad_ext, status = media_service.scan_for_malware("trojan.exe", b"test")
    assert bad_ext is False
    assert "infected" in status

    bad_bin, status = media_service.scan_for_malware("picture.png", b"MZ\x90\x00\x03")
    assert bad_bin is False
    assert "infected" in status


@pytest.mark.asyncio
async def test_media_upload_endpoint():
    # Create valid dummy image
    img = Image.new("RGB", (32, 32), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("test_rescue.jpg", buf.getvalue(), "image/jpeg")}
        data = {"folder": "reports"}
        response = await client.post("/api/v1/media/upload", files=files, data=data)

        assert response.status_code == 201
        data = response.json()
        assert "storage_key" in data
        assert data["media_type"] == "image"
        assert data["exif_stripped"] is True
        assert data["virus_scan_status"] == "clean"


@pytest.mark.asyncio
async def test_media_presign_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "filename": "injured_dog.png",
            "content_type": "image/png",
            "folder": "accidents"
        }
        response = await client.post("/api/v1/media/presign", json=payload)
        assert response.status_code == 200
        res = response.json()
        assert "upload_url" in res
        assert "storage_key" in res
        assert "public_url" in res


@pytest.mark.asyncio
async def test_notification_service_dispatches():
    # Test emergency dispatch
    await notification_service.send_emergency_dispatch(
        hospital_name="Apollo Veterinary Hospital",
        hospital_email="emergency@apollovet.org",
        hospital_phone="+919876543210",
        animal_type="street dog",
        address="Connaught Place, New Delhi",
        secure_token="tok_test_emergency_123",
        round_number=1
    )

    # Test reporter acceptance
    await notification_service.notify_reporter_case_accepted(
        reporter_phone="+919876543210",
        hospital_name="Apollo Veterinary Hospital",
        hospital_phone="+919876543210",
        eta_minutes=15
    )

    # Test 80G receipt email
    await notification_service.send_80g_receipt_email(
        donor_name="Vikram Sharma",
        donor_email="vikram@example.com",
        receipt_number="AG360-80G-TEST1234",
        amount_inr=5000.0,
        pan_number="ABCDE1234F",
        pdf_bytes=b"%PDF-1.4 mock content"
    )

