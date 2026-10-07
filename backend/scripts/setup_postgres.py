import asyncio
import asyncpg

async def setup():
    try:
        # Connect to default postgres DB
        print("Connecting to PostgreSQL at localhost:5432 with user 'postgres'...")
        conn = await asyncpg.connect(
            user="postgres",
            password=" tripathi",
            host="localhost",
            port=5432,
            database="postgres"
        )

        print(" Connected to PostgreSQL server!")

        # Check if animal_guardian_db exists
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname='animal_guardian_db'")
        if not exists:
            await conn.execute("CREATE DATABASE animal_guardian_db")
            print(" Created database 'animal_guardian_db'!")
        else:
            print(" Database 'animal_guardian_db' already exists!")
        await conn.close()

        # Connect to animal_guardian_db to enable extensions
        print("Connecting to 'animal_guardian_db'...")
        db_conn = await asyncpg.connect(
            user="postgres",
            password=" tripathi",
            host="localhost",
            port=5432,
            database="animal_guardian_db"
        )

        # Extensions
        extensions = ["uuid-ossp", "postgis", "vector"]
        for ext in extensions:
            try:
                await db_conn.execute(f'CREATE EXTENSION IF NOT EXISTS "{ext}"')
                print(f" Extension '{ext}' enabled successfully!")
            except Exception as e:
                print(f" Extension '{ext}' note: {e}")

        tables = await db_conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
        print("\n=== TABLES IN POSTGRESQL (animal_guardian_db) ===")
        for t in tables:
            print(f" -> {t['table_name']}")
        print("=================================================\n")

        await db_conn.close()
        print(" PostgreSQL setup complete!")


    except Exception as e:
        print(f" Error connecting to PostgreSQL: {e}")

if __name__ == "__main__":
    asyncio.run(setup())
