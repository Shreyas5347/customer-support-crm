from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


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