from sqlalchemy import Column, Integer, String, Date, Text
from .database import Base


# 회원 테이블 모델
class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=True)

class Dimension(Base):
    __tablename__ = "dimension"

    member_id    = Column(Integer, primary_key=True, index=True)
    name         = Column(String, nullable=True)
    party_id     = Column(Integer, nullable=True)
    party        = Column(String, nullable=True)
    district     = Column(String, nullable=True)
    gender       = Column(String, nullable=True)
    elected_time = Column(Integer, nullable=True)
    elected_type = Column(String, nullable=True)
    birthdate    = Column(Date, nullable=True)
    committee_id = Column(Integer, nullable=True)
    start_date   = Column(Date, nullable=True)
    end_date     = Column(Date, nullable=True)
    exit_reason  = Column(Text, nullable=True)
    age          = Column(Integer, nullable=True)