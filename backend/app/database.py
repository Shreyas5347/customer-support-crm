from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


import os
import re
from urllib.parse import quote, unquote

db_url = settings.database_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Auto-encode special characters (like '@') in the database password if present
url_match = re.match(r"^(postgres(?:ql)?://)([^:]+):(.+)@([^@:]+(?::\d+)?(?:/.*)?)$", db_url)
if url_match:
    prefix, user, raw_pass, host_part = url_match.groups()
    encoded_pass = quote(unquote(raw_pass), safe="")
    db_url = f"{prefix}{user}:{encoded_pass}@{host_part}"

# Safe diagnostic print (hiding the password) so Render logs show the exact host being used
masked_url = re.sub(r":([^:@]+)@", ":****@", db_url)
print(f"[DB] Initializing database connection: {masked_url}", flush=True)

if os.environ.get("RENDER") and ("localhost" in db_url or "127.0.0.1" in db_url):
    print(
        "[DB ERROR] Render service is attempting to connect to 'localhost', but Render does not run PostgreSQL locally.\n"
        "[DB ERROR] Please update DATABASE_URL in your Render Dashboard (Settings/Environment) with your Supabase connection string.",
        flush=True
    )

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()