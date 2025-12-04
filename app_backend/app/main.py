from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .database import Base, engine, get_db
from .schemas import (
    MemberCreate, 
    MemberUpdate, 
    MemberRead, 
    DimensionCreate, 
    DimensionUpdate, 
    DimensionRead,
    DimensionResponse # NULL 처리가 된 안전한 스키마
)
from .crud import (
    create_member,
    get_members,
    get_member,
    update_member,
    delete_member,
    create_dimension,
    get_dimensions,
    get_dimension,
    update_dimension,
    delete_dimension,
)

# 앱 시작 시 테이블 자동 생성 (개발용)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 실행
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 종료 시 실행 (필요하다면 추가)

app = FastAPI(
    title="Supabase + FastAPI + SQLAlchemy Members REST API",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# ----------------------------------------------------------------
# Member 관련 API
# ----------------------------------------------------------------

@app.post("/members", response_model=MemberRead, status_code=201)
async def api_create_member(
    member_in: MemberCreate,
    db: AsyncSession = Depends(get_db),
):
    member = await create_member(db, member_in)
    return member

@app.get("/members", response_model=List[MemberRead])
async def api_get_members(
    db: AsyncSession = Depends(get_db),
):
    members = await get_members(db)
    return members

@app.get("/members/{member_id}", response_model=MemberRead)
async def api_get_member(
    member_id: int,
    db: AsyncSession = Depends(get_db),
):
    member = await get_member(db, member_id)
    return member

@app.put("/members/{member_id}", response_model=MemberRead)
async def api_update_member(
    member_id: int,
    member_in: MemberUpdate,
    db: AsyncSession = Depends(get_db),
):
    member = await update_member(db, member_id, member_in)
    return member

@app.delete("/members/{member_id}", status_code=204)
async def api_delete_member(
    member_id: int,
    db: AsyncSession = Depends(get_db),
):
    await delete_member(db, member_id)
    return None

# ----------------------------------------------------------------
# Dimension 관련 API
# ----------------------------------------------------------------

@app.post("/dimension", response_model=DimensionResponse, status_code=201)
async def api_create_dimension(
    dimension_in: DimensionCreate,
    db: AsyncSession = Depends(get_db),
):
    dimension = await create_dimension(db, dimension_in)
    return dimension

@app.get("/dimension", response_model=List[DimensionResponse])
async def api_get_dimensions(
    db: AsyncSession = Depends(get_db),
):
    """
    모든 Dimension 정보를 가져옵니다.
    """
    dimensions = await get_dimensions(db)
    return dimensions

# [수정 완료] get_dimension 함수가 404를 처리하므로, 여기서는 변경 없음
@app.get("/dimension/{member_id}", response_model=DimensionResponse)
async def api_get_dimension(
    member_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    특정 멤버(member_id)의 Dimension 정보를 가져옵니다.
    값이 없는(NULL) 필드가 있어도 안전한 DimensionResponse 스키마를 사용합니다.
    """
    dimension = await get_dimension(db, member_id)
    return dimension

@app.put("/dimension/{member_id}", response_model=DimensionResponse)
async def api_update_dimension(
    member_id: int,
    dimension_in: DimensionUpdate,
    db: AsyncSession = Depends(get_db),
):
    dimension = await update_dimension(db, member_id, dimension_in)
    return dimension

@app.delete("/dimension/{member_id}", status_code=204)
async def api_delete_dimension(
    member_id: int,
    db: AsyncSession = Depends(get_db),
):
    await delete_dimension(db, member_id)
    return None