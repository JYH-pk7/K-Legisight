import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from collections.abc import AsyncGenerator
# SQLAlchemy의 기본 연결 풀을 사용하지 않도록 NullPool을 임포트합니다.
from sqlalchemy.pool import NullPool

load_dotenv()

DATABASE_URL = os.getenv("SUPABASE_DB_URL")

if DATABASE_URL is None:
    raise ValueError("SUPABASE_DB_URL 환경변수가 설정되어 있지 않습니다.")

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    # [변경] SQLAlchemy의 기본 풀러를 끄거나 (NullPool), 
    # asyncpg 자체 풀러를 사용하도록 명시적으로 설정합니다.
    # asyncpg는 내부적으로 풀링을 관리하므로, pool_size는 asyncpg에 맡깁니다.
    poolclass=NullPool,
    
    # asyncpg 드라이버로 전달될 인수
    connect_args={
        # PgBouncer 환경에서는 statement_cache_size=0 유지가 여전히 권장됩니다.
        "statement_cache_size": 0, 
        # asyncpg 풀에 대한 min/max 연결 수를 명시할 수도 있습니다.
        # "min_size": 5, 
        # "max_size": 10,
    },
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session