"""
Comprehensive Demo Data Seeder for Animal Guardian 360°
Populates local PostgreSQL with realistic Indian animal welfare sample data:
- Admin, Hospital & Citizen demo users
- 5 Verified Veterinary Hospitals with 24x7 ambulance in Delhi NCR
- 3 Active Donation Campaigns with realistic fund progression
- Public Transparency Ledger fund allocations
- Lost & Found sample pets with visual embeddings
- Active sample Road Accident SOS alert
"""
import asyncio
from datetime import datetime, timezone, timedelta, date
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User, Role
from app.models.hospital import VetHospital
from app.models.donation import Campaign, FundAllocation
from app.models.pet import Pet, LostFoundPost, PetEmbedding
from app.models.accident import AccidentAlert, AlertDispatch
from app.services.ai_embedding import ai_embedding_service


async def seed():
    async with AsyncSessionLocal() as session:
        print("[*] Starting Animal Guardian 360 Demo Data Seeding...")

        # 1. Ensure Roles exist
        role_map = {}
        for r_name in ["user", "hospital", "admin"]:
            stmt = select(Role).where(Role.name == r_name)
            res = await session.execute(stmt)
            role_obj = res.scalar_one_or_none()
            if not role_obj:
                role_obj = Role(name=r_name, description=f"{r_name.capitalize()} role")
                session.add(role_obj)
                await session.flush()
            role_map[r_name] = role_obj

        # 2. Seed Demo Users
        users_data = [
            {"phone": "+919999999999", "name": "Platform Administrator", "email": "admin@animalguardian360.org", "role": "admin"},
            {"phone": "+919876543210", "name": "Dr. Arvind Sharma (Max Vet)", "email": "hospital@maxvet.org", "role": "hospital"},
            {"phone": "+919811122233", "name": "Rohit Verma (Animal Guardian Citizen)", "email": "rohit@example.com", "role": "user"},
        ]

        created_users = {}
        for u in users_data:
            stmt = select(User).where(User.phone == u["phone"])
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()
            if not existing:
                new_user = User(
                    phone=u["phone"],
                    full_name=u["name"],
                    email=u["email"],
                    role_id=role_map[u["role"]].id,
                    is_verified=True,
                    is_active=True
                )
                session.add(new_user)
                await session.flush()
                created_users[u["role"]] = new_user
                print(f"  [+] Created user: {u['name']} ({u['phone']}) - Role: {u['role']}")
            else:
                created_users[u["role"]] = existing

        # 3. Seed Verified Veterinary Hospitals
        hospitals_data = [
            {
                "name": "Friendicoes SECA Emergency Hospital",
                "phone": "+911124314982",
                "email": "emergency@friendicoes.org",
                "address": "271 & 273 Defence Colony Flyover, New Delhi",
                "latitude": 28.5735,
                "longitude": 77.2341,
                "is_24x7": True,
                "ambulance_available": True,
                "rating": 4.9,
                "is_verified": True
            },
            {
                "name": "Sanjay Gandhi Animal Care Centre (SGACC)",
                "phone": "+911125447751",
                "email": "rescue@sgacc.in",
                "address": "Raja Garden, Near Shivaji College, New Delhi",
                "latitude": 28.6534,
                "longitude": 77.1215,
                "is_24x7": True,
                "ambulance_available": True,
                "rating": 4.8,
                "is_verified": True
            },
            {
                "name": "Apollo Veterinary Trauma & Critical Care",
                "phone": "+919876543210",
                "email": "emergency@apollovet.org",
                "address": "Connaught Place Radial 3, New Delhi",
                "latitude": 28.6315,
                "longitude": 77.2167,
                "is_24x7": True,
                "ambulance_available": True,
                "rating": 4.9,
                "is_verified": True
            },
            {
                "name": "Noida Pet Care & Critical Emergency Unit",
                "phone": "+911202345604",
                "email": "care@noidapetcare.org",
                "address": "Atta Market, Sector 18, Noida",
                "latitude": 28.5700,
                "longitude": 77.3200,
                "is_24x7": True,
                "ambulance_available": True,
                "rating": 4.7,
                "is_verified": True
            },
            {
                "name": "Max Vets 24/7 Multi-Speciality Animal Hospital",
                "phone": "+911141604160",
                "email": "info@maxvets.com",
                "address": "S-Block, Greater Kailash 1, New Delhi",
                "latitude": 28.5432,
                "longitude": 77.2345,
                "is_24x7": True,
                "ambulance_available": True,
                "rating": 4.8,
                "is_verified": True
            },
            {
                "name": "Government Veterinary Hospital (Gorakhpur)",
                "phone": "+915512200111",
                "email": "gkp.vet@up.gov.in",
                "address": "Civil Lines, Near Commissioner Office, Gorakhpur, UP",
                "latitude": 26.7588,
                "longitude": 83.3697,
                "is_24x7": True,
                "ambulance_available": True,
                "rating": 4.8,
                "is_verified": True
            },
            {
                "name": "Gorakhpur Pet Care Clinic & 24x7 Emergency",
                "phone": "+915512200222",
                "email": "emergency@gkpvetcare.org",
                "address": "Golghar Central Plaza, Gorakhpur, UP",
                "latitude": 26.7540,
                "longitude": 83.3730,
                "is_24x7": True,
                "ambulance_available": True,
                "rating": 4.9,
                "is_verified": True
            }
        ]

        seeded_hospitals = []
        for h in hospitals_data:
            stmt = select(VetHospital).where(VetHospital.name == h["name"])
            res = await session.execute(stmt)
            h_obj = res.scalar_one_or_none()
            if not h_obj:
                h_obj = VetHospital(**h)
                session.add(h_obj)
                await session.flush()
                print(f"  [+] Seeded Hospital: {h['name']} ({h['phone']})")
            seeded_hospitals.append(h_obj)

        # 4. Seed Active Donation Campaigns
        campaigns_data = [
            {
                "title": "Winter Trauma Care & Emergency Ambulance Fund 2026",
                "slug": "winter-trauma-care-2026",
                "description": "Funding critical nighttime road accident rescue ambulances, trauma surgeries, thermal blankets, and high-protein nutrition for injured street animals across Delhi NCR.",
                "target_amount_inr": 500000.0,
                "raised_amount_inr": 312500.0,
                "cover_image_url": "https://images.unsplash.com/photo-1548767797-d8c844163c4c?w=1200&auto=format&fit=crop&q=80",
                "is_active": True
            },
            {
                "title": "Critical Surgeries & Orthopedic Rehabilitation Drive",
                "slug": "critical-surgeries-rehab",
                "description": "Providing specialized orthopedic surgeries, bone pin implants, fracture casts, and physical rehabilitation for animals injured in severe vehicle collisions.",
                "target_amount_inr": 350000.0,
                "raised_amount_inr": 218000.0,
                "cover_image_url": "https://images.unsplash.com/photo-1576201836106-db1758fd1c97?w=1200&auto=format&fit=crop&q=80",
                "is_active": True
            },
            {
                "title": "Daily Community Feeding & Anti-Rabies Vaccination for 500+ Dogs",
                "slug": "community-feeding-vaccination",
                "description": "Ensuring daily nutritious meals and herd-immunity rabies vaccinations across underserved industrial areas and highway corridors.",
                "target_amount_inr": 150000.0,
                "raised_amount_inr": 115000.0,
                "cover_image_url": "https://images.unsplash.com/photo-1537151625747-768eb6cf92b2?w=1200&auto=format&fit=crop&q=80",
                "is_active": True
            }
        ]

        seeded_campaigns = []
        for c in campaigns_data:
            stmt = select(Campaign).where(Campaign.slug == c["slug"])
            res = await session.execute(stmt)
            c_obj = res.scalar_one_or_none()
            if not c_obj:
                c_obj = Campaign(**c)
                session.add(c_obj)
                await session.flush()
                print(f"  [+] Seeded Campaign: {c['title']} (Raised INR {c['raised_amount_inr']:,.0f})")
            seeded_campaigns.append(c_obj)

        # 5. Seed Transparency Ledger (Fund Allocations)
        stmt = select(FundAllocation)
        res = await session.execute(stmt)
        existing_allocs = res.scalars().all()
        if not existing_allocs:
            alloc_data = [
                {
                    "category": "rescue_ops",
                    "title": "Apollo Vet Emergency Orthopedic Surgeries",
                    "description": "Orthopedic surgery kits, spinal stabilizers, and IV fluids for 14 accident-hit stray dogs.",
                    "amount_inr": 85000.0,
                    "allocation_date": date(2026, 1, 15),
                    "receipt_url": "https://animalguardian360.org/invoices/inv-med-2026-001.pdf",
                    "verified_by_id": created_users["admin"].id
                },
                {
                    "category": "rescue_ops",
                    "title": "Ambulance Emergency Fuel (Delhi NCR Fleet)",
                    "description": "CNG & Diesel fuel for 2 emergency animal rescue ambulances operating 24x7 in Jan-Feb 2026.",
                    "amount_inr": 28500.0,
                    "allocation_date": date(2026, 1, 28),
                    "receipt_url": "https://animalguardian360.org/invoices/inv-fuel-2026-012.pdf",
                    "verified_by_id": created_users["admin"].id
                },
                {
                    "category": "medical_supplies",
                    "title": "Post-Op Antibiotics & Wound Healing Sprays",
                    "description": "Post-op antibiotics (Ceftriaxone), painkillers (Meloxicam), wound healing sprays, and sterile bandages.",
                    "amount_inr": 45000.0,
                    "allocation_date": date(2026, 2, 5),
                    "receipt_url": "https://animalguardian360.org/invoices/inv-pharma-2026-044.pdf",
                    "verified_by_id": created_users["admin"].id
                },
                {
                    "category": "food_feeding",
                    "title": "High-Nutrition Feeding Drive (1,200 kg Grains/Broth)",
                    "description": "1,200 kg of boiled rice, eggs, and recovery broth for malnourished strays in Okhla & Narela.",
                    "amount_inr": 62000.0,
                    "allocation_date": date(2026, 2, 14),
                    "receipt_url": "https://animalguardian360.org/invoices/inv-food-2026-088.pdf",
                    "verified_by_id": created_users["admin"].id
                }
            ]
            for a in alloc_data:
                alloc_obj = FundAllocation(**a)
                session.add(alloc_obj)
            print("  [+] Seeded 4 Public Transparency Ledger Allocations")

        # 6. Seed Sample Lost & Found Pets with Vector Embeddings
        pets_sample = [
            {
                "species": "dog",
                "breed": "Indian Pariah / Indie",
                "name": "Sheru",
                "primary_color": "Tan",
                "secondary_color": "White",
                "gender": "male",
                "microchip_id": "981098200145678",
                "post_type": "lost",
                "city": "New Delhi",
                "area": "Connaught Place Central Park",
                "description": "Friendly male Indie dog. Wearing a bright red nylon collar with a small brass bell. Responds to the name Sheru.",
                "photo_url": "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=800&auto=format&fit=crop&q=80"
            },
            {
                "species": "cat",
                "breed": "Persian Longhair",
                "name": "Milo",
                "primary_color": "White",
                "secondary_color": "Cream",
                "gender": "female",
                "microchip_id": None,
                "post_type": "lost",
                "city": "New Delhi",
                "area": "Hauz Khas Enclave",
                "description": "Pure white Persian cat with striking blue eyes and fluffy bushy tail. Shy around strangers.",
                "photo_url": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=800&auto=format&fit=crop&q=80"
            },
            {
                "species": "dog",
                "breed": "Indian Pariah / Indie",
                "name": "Found Indie Dog",
                "primary_color": "Tan",
                "secondary_color": "White",
                "gender": "male",
                "microchip_id": None,
                "post_type": "found",
                "city": "New Delhi",
                "area": "Barakhamba Road Metro Gate 2",
                "description": "Found a very affectionate tan dog near Barakhamba Road wearing a red collar. Well-groomed, clearly a lost pet! Safe with security guard.",
                "photo_url": "https://images.unsplash.com/photo-1537151625747-768eb6cf92b2?w=800&auto=format&fit=crop&q=80"
            }
        ]

        stmt = select(Pet)
        res = await session.execute(stmt)
        existing_pets = res.scalars().all()
        if not existing_pets:
            for p in pets_sample:
                pet_rec = Pet(
                    owner_id=created_users["user"].id,
                    species=p["species"],
                    breed=p["breed"],
                    name=p["name"],
                    primary_color=p["primary_color"],
                    secondary_color=p["secondary_color"],
                    gender=p["gender"],
                    microchip_id=p["microchip_id"],
                    photo_url=p["photo_url"]
                )
                session.add(pet_rec)
                await session.flush()

                post_rec = LostFoundPost(
                    user_id=created_users["user"].id,
                    pet_id=pet_rec.id,
                    post_type=p["post_type"],
                    species=p["species"],
                    breed=p["breed"],
                    primary_color=p["primary_color"],
                    secondary_color=p["secondary_color"],
                    gender=p["gender"],
                    distinctive_marks=p["description"],
                    incident_date=datetime.now(timezone.utc) - timedelta(days=2),
                    latitude=28.6315,
                    longitude=77.2167,
                    address_text=f"{p['area']}, {p['city']}",
                    photo_urls=[p["photo_url"]],
                    status="active"
                )
                session.add(post_rec)
                await session.flush()

                # Generate and store embedding
                emb_vec = ai_embedding_service.generate_image_embedding(
                    image_url_or_meta=f"{p['species']} {p['breed']} {p['primary_color']} {p['description']}"
                )
                pet_emb = PetEmbedding(
                    post_id=post_rec.id,
                    image_url=p["photo_url"],
                    vector_data=emb_vec,
                    model_name="open_clip:ViT-B-32"
                )
                session.add(pet_emb)
                print(f"  [+] Seeded {p['post_type'].upper()} Pet: {p['name']} ({p['breed']})")

        # 7. Seed Active Road Accident SOS Alert
        stmt = select(AccidentAlert)
        res = await session.execute(stmt)
        existing_alerts = res.scalars().all()
        if not existing_alerts and seeded_hospitals:
            apollo_hosp = seeded_hospitals[2]
            sos_alert = AccidentAlert(
                reporter_id=created_users["user"].id,
                reporter_phone="+919811122233",
                animal_type="street dog",
                condition_description="Injured right hind leg due to bike hit, bleeding slightly but conscious.",
                photo_url="https://images.unsplash.com/photo-1548767797-d8c844163c4c?w=800&auto=format&fit=crop&q=80",
                latitude=28.6325,
                longitude=77.2185,
                address_text="Near Rajiv Chowk Metro Gate 5, Connaught Place, New Delhi",
                status="accepted",
                accepted_hospital_id=apollo_hosp.id,
                accepted_at=datetime.now(timezone.utc) - timedelta(minutes=6),
                eta_minutes=12
            )
            session.add(sos_alert)
            await session.flush()

            dispatch = AlertDispatch(
                alert_id=sos_alert.id,
                hospital_id=apollo_hosp.id,
                escalation_round=1,
                secure_token="tok_demo_active_dispatch_token",
                status="accepted",
                dispatched_at=datetime.now(timezone.utc) - timedelta(minutes=8),
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
                responded_at=datetime.now(timezone.utc) - timedelta(minutes=6)
            )
            session.add(dispatch)
            print("  [+] Seeded Active Road Accident SOS Alert (Accepted by Apollo Vet, ETA 12 mins)")

        await session.commit()
        print("\n[+] All Demo Data Successfully Seeded into local PostgreSQL (animal_guardian_db)!")


if __name__ == "__main__":
    asyncio.run(seed())
