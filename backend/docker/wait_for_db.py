import os
import time
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

# Try to connect for up to ~60 seconds
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

deadline = time.time() + 60
last_err = None

while time.time() < deadline:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("DB is ready.")
        break
    except Exception as e:
        last_err = e
        print("Waiting for DB...")
        time.sleep(2)
else:
    raise RuntimeError(f"DB not ready after timeout. Last error: {last_err}")
