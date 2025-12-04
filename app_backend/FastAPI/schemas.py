from pydantic import BaseModel, EmailStr, Field
from typing import Any, Dict, List, Optional
from datetime import date

# ... (기존 스키마들 유지) ...

class AnalysisInput(BaseModel):
    speech_text: str

class SentimentOutput(BaseModel):
    label: str
    confidence_score: float

class PredictionOutput(BaseModel):
    label: str
    probability: float

class UserCreate(BaseModel):
    email: EmailStr         
    username: str           
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class SearchInput(BaseModel):
    type: str             
    query: Optional[str] = None 
    committee: Optional[str] = None 
    filters: Optional[Dict[str, Any]] = {}

class SearchResponse(BaseModel):
    results: List[dict]
    total_count: int
    message: Optional[str] = None

class DimensionBase(BaseModel):
    member_id: int | None = None
    name: str | None = None
    party_id: int | None = None
    party: str | None = None
    district: str | None = None
    gender: str | None = None
    elected_time: int | None = None
    elected_type: str | None = None
    birthdate: date | None = None
    committee_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    exit_reason: str | None = None
    age: int | None = None  
    
class DimensionCreate(DimensionBase):
    pass    
    
class DimensionUpdate(BaseModel):
    member_id: int | None = None
    name: str | None = None
    party_id: int | None = None
    party: str | None = None
    district: str | None = None
    gender: str | None = None
    elected_time: int | None = None
    elected_type: str | None = None
    birthdate: date | None = None
    committee_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    exit_reason: str | None = None
    age: int | None = None  
    
class DimensionRead(DimensionBase):
    member_id: int
    class Config:
        from_attributes = True

class DimensionResponse(BaseModel):
    member_id: int
    name: Optional[str] = None
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
        from_attributes = True

class SpeechData(BaseModel):
    speech_id: int
    meeting_id: int
    bills: Optional[str] = None
    member_id: str 
    member_name: str
    speech_order: int
    speech_text: str
    tf_trigger: bool
    delib_order: Optional[int] = None
    bill_review: List[Any] = []
    agenda_items: List[Any] = []
    agenda_range_str: Optional[str] = None
    sentiment_label: Optional[str] = None
    sentiment_prob: Optional[float] = None
    skip_reason: Optional[str] = None

# --- [신규] 테이블별 조회용 스키마 ---

# 1. bills (의안 정보)
class Bill(BaseModel):
    bill_id: int = Field(alias="의안번호")
    bill_name: Optional[str] = Field(None, alias="의안명")
    proposer: Optional[str] = Field(None, alias="대표발의 의원명")
    proposer_type: Optional[str] = Field(None, alias="제안자구분")
    content: Optional[str] = Field(None, alias="제안이유 및 주요내용")
    propose_date: Optional[date] = Field(None, alias="제안일자")
    decision_date: Optional[date] = Field(None, alias="의결일자")
    decision_result: Optional[str] = Field(None, alias="의결결과")
    status: Optional[str] = Field(None, alias="심사진행상태")
    url: Optional[str] = Field(None, alias="URL")

# 2. committees
class Committee(BaseModel):
    committee_id: int
    name: str

# 3. committees_history
class CommitteeHistory(BaseModel):
    number: int
    member_id: int
    committee_id: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    committee: Optional[str] = None

# 4. meetings
class Meeting(BaseModel):
    meeting_id: int
    meeting_category: Optional[str] = None
    daesu: Optional[int] = None
    meeting_specification: Optional[str] = None
    commitee: Optional[str] = None 
    number_of_meetings: Optional[int] = None
    chasu: Optional[int] = None
    meeting_date: Optional[str] = None

# 5. member_bill_stats
class MemberBillStats(BaseModel):
    member_id: Optional[int] = None
    member_name: Optional[str] = None
    bill_review: Optional[str] = None
    n_speeches: Optional[int] = None
    total_speech_length_bill: Optional[int] = None
    avg_speech_length_bill: Optional[float] = None
    score_prob_mean: Optional[float] = None
    stance: Optional[str] = None

# 6. member_stats
class MemberStats(BaseModel):
    member_id: Optional[int] = None
    total_speeches: Optional[int] = None
    total_speech_length: Optional[int] = None
    avg_speech_length: Optional[float] = None
    avg_prob_coop: Optional[str] = None
    avg_prob_noncoop: Optional[str] = None
    avg_prob_neutral: Optional[str] = None
    cooperation_score_prob: Optional[str] = None
    bills_count: Optional[int] = None
    member_name: Optional[str] = None
    controversy_rate: Optional[float] = None
    count_label_0: Optional[int] = None
    count_label_1: Optional[int] = None
    count_label_2: Optional[int] = None

# 7. parties
class Party(BaseModel):
    party_id: int
    name: str
    ruling_start_date: Optional[date] = None
    ruling_end_date: Optional[date] = None

# 8. parties_history
class PartyHistory(BaseModel):
    number: int
    member_id: int
    name: str
    party_id: int
    start_date: date
    end_date: date
    note: Optional[str] = Field(None, alias="비고")

# 9. speeches
class Speech(BaseModel):
    speech_id: int
    meeting_id: int
    bills: Optional[str] = None
    member_id: Optional[int] = None
    member_name: str
    speech_order: int
    speech_text: str
    delib_id: Optional[int] = None
    is_trigger: Optional[str] = None