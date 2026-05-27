"""Run migration.sql directly against Supabase using asyncpg with SSL."""
import asyncio
import ssl
import pathlib
import asyncpg

HOST = "aws-0-us-east-1.pooler.supabase.com"
PORT = 6543
USER = "postgres.wrspszdkmjdrhupvjblu"
PASSWORD = "0507362238Bb"
DATABASE = "postgres"

SQL_FILE = pathlib.Path(__file__).parent / "migration.sql"


async def main():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    print(f"Connecting to {HOST}:{PORT} ...")
    conn = await asyncpg.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        ssl=ctx,
    )
    print("Connected.")

    sql = SQL_FILE.read_text(encoding="utf-8")

    print("Running migration.sql ...")
    try:
        await conn.execute(sql)
        print("Migration complete.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()


asyncio.run(main())
