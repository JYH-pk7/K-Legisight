from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
from sqlalchemy import Column, Integer, String, Date, Text
from .database import Base

class MemberBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None

class MemberCreate(MemberBase):
    """회원 생성용 스키마"""
    pass

class MemberUpdate(BaseModel):
    """회원 수정(부분 수정 포함) 스키마"""
    username: str | None = None
    email: EmailStr | None = None
    full_name: str | None = None

class MemberRead(MemberBase):
    """응답용 스키마"""
    id: int

    class Config:
        from_attributes = True  # SQLAlchemy 객체 → Pydantic 변환

class DimensionBase(BaseModel):
    member_id: int | None = None
    name: str | None = None
    party_id: int | None = None
    party: str | None = None
    district: str | None = None
    gender: str | None = None
    elected_time: int | None = None
    elected_type: str | None = None
    # [수정] DATE 타입 필드를 str 대신 date 타입으로 변경
    birthdate: date | None = None
    committee_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    exit_reason: str | None = None
    age: int | None = None  
    
class DimensionCreate(DimensionBase):
    """Dimension 생성용 스키마"""
    pass    
    
class DimensionUpdate(BaseModel):
    """Dimension 수정(부분 수정 포함) 스키마"""
    member_id: int | None = None
    name: str | None = None
    party_id: int | None = None
    party: str | None = None
    district: str | None = None
    gender: str | None = None
    elected_time: int | None = None
    elected_type: str | None = None
    # [수정] DATE 타입 필드를 str 대신 date 타입으로 변경
    birthdate: date | None = None
    committee_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    exit_reason: str | None = None
    age: int | None = None  
    
class DimensionRead(DimensionBase):
    """응답용 스키마"""
    member_id: int

    class Config:
        from_attributes = True  # SQLAlchemy 객체 → Pydantic 변환

# Dimension 데이터를 조회할 때 사용할 스키마
class DimensionResponse(BaseModel):
    member_id: int
    name: Optional[str] = None          # 이름이 없을 수도 있음
    party_id: Optional[int] = None
    party: Optional[str] = None
    district: Optional[str] = None
    gender: Optional[str] = None
    elected_time: Optional[int] = None
    elected_type: Optional[str] = None
    birthdate: Optional[str] = None    
    committee_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    exit_reason: Optional[str] = None
    age: Optional[int] = None

    class Config:
        from_attributes = True  # ORM 객체를 Pydantic 모델로 변환 허용