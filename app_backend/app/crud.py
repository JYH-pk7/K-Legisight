from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException

from .models import Member, Dimension
from .schemas import MemberCreate, MemberUpdate, DimensionCreate, DimensionUpdate

# 회원 생성
async def create_member(db: AsyncSession, member_in: MemberCreate) -> Member:
    # username 또는 email 중복 체크
    result = await db.execute(
        select(Member).where(
            (Member.username == member_in.username) |
            (Member.email == member_in.email)
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자입니다.")

    member = Member(
        username=member_in.username,
        email=member_in.email,
        full_name=member_in.full_name,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member

# 전체 회원 목록
async def get_members(db: AsyncSession) -> List[Member]:
    result = await db.execute(select(Member).order_by(Member.id))
    return result.scalars().all()

# 단일 회원 조회
async def get_member(db: AsyncSession, member_id: int) -> Member:
    result = await db.execute(select(Member).where(Member.id == member_id))
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return member

# 회원 수정
async def update_member(db: AsyncSession, member_id: int, member_in: MemberUpdate) -> Member:
    member = await get_member(db, member_id)

    if member_in.username is not None:
        member.username = member_in.username
    if member_in.email is not None:
        member.email = member_in.email
    if member_in.full_name is not None:
        member.full_name = member_in.full_name

    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member

# 회원 삭제
async def delete_member(db: AsyncSession, member_id: int) -> None:
    member = await get_member(db, member_id)
    # [수정] db.delete()를 await로 감싸서 비동기 실행을 명확히 합니다.
    await db.delete(member)
    await db.commit()

# Dimension 생성
async def create_dimension(db: AsyncSession, dimension_in: DimensionCreate) -> Dimension:
    dimension = Dimension(
        member_id=dimension_in.member_id,
        name=dimension_in.name,
        party_id=dimension_in.party_id,
        party=dimension_in.party,
        district=dimension_in.district,
        gender=dimension_in.gender,
        elected_time=dimension_in.elected_time,
        elected_type=dimension_in.elected_type,
        # birthdate, start_date, end_date는 이제 date 객체로 들어옴
        birthdate=dimension_in.birthdate,
        committee_id=dimension_in.committee_id,
        start_date=dimension_in.start_date,
        end_date=dimension_in.end_date,
        exit_reason=dimension_in.exit_reason,
        age=dimension_in.age,
    )
    db.add(dimension)
    await db.commit()
    await db.refresh(dimension)
    return dimension    
    
# Dimension 전체 목록
# Dimension 전체 목록
async def get_dimensions(db: AsyncSession) -> List[Dimension]:
    """모든 Dimension 정보를 가져옵니다."""
    result = await db.execute(select(Dimension).order_by(Dimension.member_id))
    dimensions = result.scalars().all()
    
    # -----------------------------------------------------
    # [디버깅 코드 추가] 첫 10개 레코드의 날짜 필드를 확인합니다.
    # -----------------------------------------------------
    print("\n--- DIMENSION DEBUG START ---")
    for i, dim in enumerate(dimensions[:10]):
        print(f"Record {i}: member_id={dim.member_id}")
        print(f"  Birthdate Type: {type(dim.birthdate)}, Value: {dim.birthdate}")
        print(f"  Start_date Type: {type(dim.start_date)}, Value: {dim.start_date}")
        # 만약 여기서 <class 'str'> 같은 것이 나오면 DB에 잘못 저장된 것입니다.
    print("--- DIMENSION DEBUG END ---\n")
    # -----------------------------------------------------

    return dimensions # ORM 객체 리스트 반환

# Dimension 단일 조회
async def get_dimension(db: AsyncSession, member_id: int) -> Dimension:
    result = await db.execute(select(Dimension).where(Dimension.member_id == member_id))
    dimension = result.scalar_one_or_none()
    # [유효성 검사] 데이터가 없을 경우 HTTPException을 발생시켜 500 오류를 방지합니다.
    if dimension is None:
        raise HTTPException(status_code=404, detail="Dimension을 찾을 수 없습니다.")
    return dimension

# Dimension 수정
async def update_dimension(db: AsyncSession, member_id: int, dimension_in: DimensionUpdate) -> Dimension:
    dimension = await get_dimension(db, member_id)

    # 모든 필드 업데이트 로직 (타입 변경에 맞춰 수정 필요 없음, 값만 대입)
    if dimension_in.name is not None:
        dimension.name = dimension_in.name
    if dimension_in.party_id is not None:
        dimension.party_id = dimension_in.party_id
    if dimension_in.party is not None:
        dimension.party = dimension_in.party
    if dimension_in.district is not None:
        dimension.district = dimension_in.district
    if dimension_in.gender is not None:
        dimension.gender = dimension_in.gender
    if dimension_in.elected_time is not None:
        dimension.elected_time = dimension_in.elected_time
    if dimension_in.elected_type is not None:
        dimension.elected_type = dimension_in.elected_type
    if dimension_in.birthdate is not None:
        dimension.birthdate = dimension_in.birthdate
    if dimension_in.committee_id is not None:
        dimension.committee_id = dimension_in.committee_id
    if dimension_in.start_date is not None:
        dimension.start_date = dimension_in.start_date
    if dimension_in.end_date is not None:
        dimension.end_date = dimension_in.end_date
    if dimension_in.exit_reason is not None:
        dimension.exit_reason = dimension_in.exit_reason
    if dimension_in.age is not None:
        dimension.age = dimension_in.age    
        
    db.add(dimension)
    await db.commit()
    await db.refresh(dimension)
    return dimension

# Dimension 삭제
async def delete_dimension(db: AsyncSession, member_id: int) -> None:
    dimension = await get_dimension(db, member_id)
    await db.delete(dimension)
    await db.commit()