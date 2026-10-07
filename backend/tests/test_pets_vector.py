"""
Comprehensive tests for Feature 3:
- Pet Registration
- Vector embedding generation (512 dimensions, L2 normalization)
- Cosine similarity computation
- Spatial-temporal AI matching against opposite listings within 25 km
- Reunited status progression
- Community sightings filtering
"""
import math
import pytest
from httpx import AsyncClient
from app.models.user import User
from app.services.ai_embedding import ai_embedding_service


def test_embedding_vector_dimensions_and_normalization():
    # Test generation from string / metadata
    vector = ai_embedding_service.generate_image_embedding(
        image_url_or_meta="dog:beagle:tricolor:white_tip_tail"
    )
    assert len(vector) == 512
    # Check L2 Norm = 1.0
    norm = math.sqrt(sum(v * v for v in vector))
    assert pytest.approx(norm, 0.01) == 1.0


def test_cosine_similarity_math():
    v1 = ai_embedding_service.generate_image_embedding(image_url_or_meta="pet_signature_alpha")
    v2 = ai_embedding_service.generate_image_embedding(image_url_or_meta="pet_signature_alpha")
    # Identical should have similarity 1.0
    sim_same = ai_embedding_service.compute_cosine_similarity(v1, v2)
    assert pytest.approx(sim_same, 0.001) == 1.0

    v3 = ai_embedding_service.generate_image_embedding(image_url_or_meta="pet_signature_beta")
    sim_diff = ai_embedding_service.compute_cosine_similarity(v1, v3)
    assert sim_diff < 1.0


@pytest.mark.asyncio
async def test_register_pet_profile(client: AsyncClient, regular_user: User, user_token: str):
    payload = {
        "name": "Rocky",
        "species": "dog",
        "breed": "German Shepherd",
        "primary_color": "black",
        "secondary_color": "tan",
        "gender": "male",
        "microchip_id": "981098109810"
    }
    response = await client.post(
        "/api/v1/pets",
        headers={"Authorization": f"Bearer {user_token}"},
        json=payload
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Rocky"
    assert data["species"] == "dog"
    assert data["owner_id"] == regular_user.id


@pytest.mark.asyncio
async def test_lost_and_found_match_within_25km(client: AsyncClient, regular_user: User, user_token: str):
    # Step 1: User A posts "Lost" Dog in Connaught Place (28.6315, 77.2167)
    lost_payload = {
        "post_type": "lost",
        "species": "dog",
        "breed": "Golden Retriever",
        "primary_color": "golden",
        "secondary_color": "cream",
        "latitude": 28.6315,
        "longitude": 77.2167,
        "address_text": "Inner Circle, Connaught Place",
        "photo_urls": ["https://example.com/photos/golden_lost.jpg"]
    }
    lost_res = await client.post(
        "/api/v1/pets/posts",
        headers={"Authorization": f"Bearer {user_token}"},
        json=lost_payload
    )
    assert lost_res.status_code == 201
    lost_id = lost_res.json()["id"]

    # Step 2: Citizen B posts "Found" Dog at India Gate (28.6129, 77.2295, ~2.5 km away)
    found_payload = {
        "post_type": "found",
        "species": "dog",
        "breed": "Golden Retriever",
        "primary_color": "golden",
        "secondary_color": "cream",
        "latitude": 28.6129,
        "longitude": 77.2295,
        "address_text": "India Gate Lawns, New Delhi",
        "photo_urls": ["https://example.com/photos/golden_lost.jpg"]  # Same image signature
    }
    found_res = await client.post(
        "/api/v1/pets/posts",
        headers={"Authorization": f"Bearer {user_token}"},
        json=found_payload
    )
    assert found_res.status_code == 201
    found_data = found_res.json()

    # Step 3: Verify AI vector match is detected
    assert len(found_data["matches"]) >= 1
    match = found_data["matches"][0]
    assert match["matched_post_id"] == lost_id
    assert match["similarity_score"] >= 0.75
    assert match["distance_km"] < 5.0  # ~2.5 km away


@pytest.mark.asyncio
async def test_different_species_does_not_match(client: AsyncClient, regular_user: User, user_token: str):
    # User posts Lost cat
    lost_cat = await client.post(
        "/api/v1/pets/posts",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "post_type": "lost",
            "species": "cat",
            "breed": "Persian",
            "primary_color": "white",
            "latitude": 28.6315,
            "longitude": 77.2167
        }
    )
    assert lost_cat.status_code == 201

    # User posts Found dog at exact same spot
    found_dog = await client.post(
        "/api/v1/pets/posts",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "post_type": "found",
            "species": "dog",
            "breed": "Pug",
            "primary_color": "fawn",
            "latitude": 28.6315,
            "longitude": 77.2167
        }
    )
    assert found_dog.status_code == 201
    assert len(found_dog.json()["matches"]) == 0  # No species cross-match


@pytest.mark.asyncio
async def test_distance_over_25km_filtered_out(client: AsyncClient, regular_user: User, user_token: str):
    # Lost dog in New Delhi (28.6315, 77.2167)
    await client.post(
        "/api/v1/pets/posts",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "post_type": "lost",
            "species": "dog",
            "breed": "Beagle",
            "primary_color": "tricolor",
            "latitude": 28.6315,
            "longitude": 77.2167
        }
    )

    # Found dog in Jaipur (~240 km away, 26.9124, 75.7873)
    found_jaipur = await client.post(
        "/api/v1/pets/posts",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "post_type": "found",
            "species": "dog",
            "breed": "Beagle",
            "primary_color": "tricolor",
            "latitude": 26.9124,
            "longitude": 75.7873
        }
    )
    assert found_jaipur.status_code == 201
    # Beyond 25 km threshold -> should not be paired
    assert len(found_jaipur.json()["matches"]) == 0


@pytest.mark.asyncio
async def test_mark_post_reunited(client: AsyncClient, regular_user: User, user_token: str):
    post_res = await client.post(
        "/api/v1/pets/posts",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "post_type": "lost",
            "species": "dog",
            "latitude": 28.6000,
            "longitude": 77.2000
        }
    )
    post_id = post_res.json()["id"]

    # Mark as reunited
    reunited_res = await client.patch(
        f"/api/v1/pets/posts/{post_id}/reunited",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert reunited_res.status_code == 200
    assert reunited_res.json()["status"] == "reunited"


@pytest.mark.asyncio
async def test_community_sightings_filters(client: AsyncClient, regular_user: User, user_token: str):
    # Post 1: Cat
    await client.post(
        "/api/v1/pets/posts",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"post_type": "sighting", "species": "cat", "latitude": 28.60, "longitude": 77.20}
    )
    # Post 2: Dog
    await client.post(
        "/api/v1/pets/posts",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"post_type": "sighting", "species": "dog", "latitude": 28.60, "longitude": 77.20}
    )

    # Filter species=cat
    filter_res = await client.get("/api/v1/pets/posts?species=cat")
    assert filter_res.status_code == 200
    posts = filter_res.json()
    assert len(posts) >= 1
    assert all(p["species"] == "cat" for p in posts)
