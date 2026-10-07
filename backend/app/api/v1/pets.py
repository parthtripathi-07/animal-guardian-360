"""
Lost & Found Pet API: Post registration, CLIP vector embedding generation,
geographical radius search (25 km), ranked AI visual matching, and sightings map.
"""
from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError, ForbiddenError
from app.models.user import User
from app.models.pet import Pet, LostFoundPost, PetEmbedding, Match
from app.schemas.pet import (
    PetCreate,
    PetResponse,
    LostFoundPostCreate,
    LostFoundPostResponse,
    MatchSummaryResponse,
)
from app.services.ai_embedding import ai_embedding_service
from app.services.google_maps import calculate_haversine_distance

router = APIRouter(prefix="/pets", tags=["Lost & Found Pets"])


def build_match_summary(m: Match, current_post_id: str) -> MatchSummaryResponse:
    # Identify whether the opposite post is lost or found
    opposite = m.found_post if m.lost_post_id == current_post_id else m.lost_post
    photo = opposite.photo_urls[0] if opposite.photo_urls else None

    return MatchSummaryResponse(
        match_id=m.id,
        matched_post_id=opposite.id,
        matched_post_type=opposite.post_type,
        similarity_score=round(m.similarity_score, 3),
        confidence_percent=round(m.similarity_score * 100, 1),
        distance_km=round(m.distance_meters / 1000.0, 1),
        matched_photo_url=photo,
        species=opposite.species,
        breed=opposite.breed,
        address_text=opposite.address_text,
        incident_date=opposite.incident_date
    )


def build_post_response(post: LostFoundPost) -> LostFoundPostResponse:
    all_matches = []
    # Combine matches where post is either lost or found
    for m in (post.matches_as_lost or []):
        if m.found_post:
            all_matches.append(build_match_summary(m, post.id))
    for m in (post.matches_as_found or []):
        if m.lost_post:
            all_matches.append(build_match_summary(m, post.id))

    all_matches.sort(key=lambda x: x.similarity_score, reverse=True)

    return LostFoundPostResponse(
        id=post.id,
        user_id=post.user_id,
        post_type=post.post_type,
        species=post.species,
        breed=post.breed,
        primary_color=post.primary_color,
        secondary_color=post.secondary_color,
        gender=post.gender,
        distinctive_marks=post.distinctive_marks,
        collar_info=post.collar_info,
        incident_date=post.incident_date,
        latitude=post.latitude,
        longitude=post.longitude,
        address_text=post.address_text,
        photo_urls=post.photo_urls or [],
        status=post.status,
        masked_contact_enabled=post.masked_contact_enabled,
        created_at=post.created_at,
        matches=all_matches
    )


@router.post(
    "",
    response_model=PetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user's pet profile"
)
async def register_pet(
    payload: PetCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    pet = Pet(
        owner_id=current_user.id,
        name=payload.name,
        species=payload.species,
        breed=payload.breed,
        primary_color=payload.primary_color,
        secondary_color=payload.secondary_color,
        gender=payload.gender,
        microchip_id=payload.microchip_id,
        photo_url=payload.photo_url
    )
    db.add(pet)
    await db.commit()
    await db.refresh(pet)
    return PetResponse.model_validate(pet)


@router.post(
    "/posts",
    response_model=LostFoundPostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publish a Lost, Found, or Sighting pet report (triggers automatic vector search)"
)
async def create_lost_found_post(
    payload: LostFoundPostCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Publishes a pet alert.
    1. Generates a 512-dimensional vector embedding.
    2. Searches for opposite listings within 25 km.
    3. Ranks candidates by cosine similarity.
    4. Auto-notifies owners if similarity >= threshold (default 0.75).
    """
    post = LostFoundPost(
        user_id=current_user.id,
        pet_id=payload.pet_id,
        post_type=payload.post_type,
        species=payload.species.lower().strip(),
        breed=payload.breed,
        primary_color=payload.primary_color,
        secondary_color=payload.secondary_color,
        gender=payload.gender,
        distinctive_marks=payload.distinctive_marks,
        collar_info=payload.collar_info,
        incident_date=payload.incident_date,
        latitude=payload.latitude,
        longitude=payload.longitude,
        address_text=payload.address_text,
        photo_urls=payload.photo_urls,
        status="active",
        masked_contact_enabled=payload.masked_contact_enabled
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    # Generate and store embedding
    meta_tag = f"{post.species}:{post.breed}:{post.primary_color}:{post.secondary_color}"
    vector = ai_embedding_service.generate_image_embedding(
        image_url_or_meta=payload.photo_urls[0] if payload.photo_urls else meta_tag
    )

    embedding_rec = PetEmbedding(
        post_id=post.id,
        image_url=payload.photo_urls[0] if payload.photo_urls else "",
        vector_data=vector,
        model_name="open_clip:ViT-B-32"
    )
    db.add(embedding_rec)
    await db.commit()

    # Run AI similarity search against opposite posts within 25 km
    await ai_embedding_service.match_post_against_database(
        db=db,
        new_post=post,
        max_radius_km=25.0,
        threshold=0.75
    )

    # Reload post with full match relationships
    stmt = (
        select(LostFoundPost)
        .where(LostFoundPost.id == post.id)
        .options(
            selectinload(LostFoundPost.matches_as_lost).selectinload(Match.found_post),
            selectinload(LostFoundPost.matches_as_found).selectinload(Match.lost_post),
            selectinload(LostFoundPost.embeddings)
        )
    )
    res = await db.execute(stmt)
    full_post = res.scalar_one()

    return build_post_response(full_post)


@router.get(
    "/posts",
    response_model=List[LostFoundPostResponse],
    status_code=status.HTTP_200_OK,
    summary="Browse community pet alerts and sightings map with filters"
)
async def list_lost_found_posts(
    post_type: Optional[str] = Query(None, pattern="^(lost|found|sighting)$"),
    species: Optional[str] = None,
    breed: Optional[str] = None,
    color: Optional[str] = None,
    status_filter: Optional[str] = Query("active"),
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: Optional[float] = Query(25.0, ge=1.0, le=200.0),
    db: AsyncSession = Depends(get_db)
):
    """
    Community sightings query with multi-attribute and geographical radius filters.
    """
    stmt = (
        select(LostFoundPost)
        .options(
            selectinload(LostFoundPost.matches_as_lost).selectinload(Match.found_post),
            selectinload(LostFoundPost.matches_as_found).selectinload(Match.lost_post)
        )
        .order_by(LostFoundPost.created_at.desc())
    )

    if post_type:
        stmt = stmt.where(LostFoundPost.post_type == post_type)
    if species:
        stmt = stmt.where(LostFoundPost.species == species.lower().strip())
    if breed:
        stmt = stmt.where(LostFoundPost.breed.ilike(f"%{breed}%"))
    if color:
        stmt = stmt.where(
            or_(
                LostFoundPost.primary_color.ilike(f"%{color}%"),
                LostFoundPost.secondary_color.ilike(f"%{color}%")
            )
        )
    if status_filter:
        stmt = stmt.where(LostFoundPost.status == status_filter)

    res = await db.execute(stmt)
    posts = res.scalars().all()

    # Geographical filtering if lat and lng provided
    if lat is not None and lng is not None:
        radius_meters = (radius_km or 25.0) * 1000.0
        filtered = []
        for p in posts:
            dist = calculate_haversine_distance(lat, lng, p.latitude, p.longitude)
            if dist <= radius_meters:
                filtered.append(p)
        posts = filtered

    return [build_post_response(p) for p in posts]


@router.get(
    "/posts/{post_id}",
    response_model=LostFoundPostResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single lost/found pet post with ranked matches"
)
async def get_post_details(
    post_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(LostFoundPost)
        .where(LostFoundPost.id == post_id)
        .options(
            selectinload(LostFoundPost.matches_as_lost).selectinload(Match.found_post),
            selectinload(LostFoundPost.matches_as_found).selectinload(Match.lost_post),
            selectinload(LostFoundPost.embeddings)
        )
    )
    res = await db.execute(stmt)
    post = res.scalar_one_or_none()
    if not post:
        raise NotFoundError("Lost & found post not found")

    return build_post_response(post)


@router.patch(
    "/posts/{post_id}/reunited",
    response_model=LostFoundPostResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark lost or found pet as reunited"
)
async def mark_pet_reunited(
    post_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Marks the listing as reunited and updates corresponding matches.
    """
    stmt = (
        select(LostFoundPost)
        .where(LostFoundPost.id == post_id)
        .options(
            selectinload(LostFoundPost.matches_as_lost).selectinload(Match.found_post),
            selectinload(LostFoundPost.matches_as_found).selectinload(Match.lost_post)
        )
    )
    res = await db.execute(stmt)
    post = res.scalar_one_or_none()
    if not post:
        raise NotFoundError("Post not found")

    if post.user_id != current_user.id and current_user.role.name != "admin":
        raise ForbiddenError("You can only update your own pet listings")

    post.status = "reunited"

    # Update associated matches to confirmed_reunited
    for m in (post.matches_as_lost or []):
        m.status = "confirmed_reunited"
    for m in (post.matches_as_found or []):
        m.status = "confirmed_reunited"

    await db.commit()
    await db.refresh(post)
    return build_post_response(post)
