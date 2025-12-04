from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from contextlib import asynccontextmanager
from database import supabase
from sqlalchemy.ext.asyncio import AsyncSession
import schemas
import random 
from typing import List, Optional

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Server đang khởi động...")
    print("✅ Đã kết nối Supabase!")
    yield
    print("🔥 Server đã tắt.")

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "http://localhost:5174",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        user = supabase.auth.get_user(token)
        if not user:
             raise HTTPException(status_code=401, detail="Token không hợp lệ")
        return user.user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# ==========================================
# 1. 테이블별 데이터 조회 API (Schema 기반)
# ==========================================

# 1. Bills (의안 정보)
# [수정] bill_id(의안번호) 파라미터 추가
@app.get("/api/bills", response_model=List[schemas.Bill])
def get_bills(bill_id: Optional[int] = None, proposer: Optional[str] = None):
    try:
        # 기본 쿼리 생성
        query = supabase.table('bills').select("*")
        
        # bill_id(의안번호)가 있으면 필터링
        if bill_id:
            query = query.eq('의안번호', bill_id)

        # proposer(대표발의 의원명)가 있으면 필터링
        if proposer:
            query = query.eq('대표발의 의원명', proposer)
            
        response = query.execute()
        return response.data
    except Exception as e:
        print("Error fetching bills:", e)
        return []

# 2. Committees (위원회 정보)
@app.get("/api/committees", response_model=List[schemas.Committee])
def get_committees():
    try:
        response = supabase.table('committees').select("*").execute()
        return response.data
    except Exception as e:
        print("Error fetching committees:", e)
        return []

# 3. Committees History (위원회 활동 이력)
@app.get("/api/committees-history", response_model=List[schemas.CommitteeHistory])
def get_committees_history():
    try:
        response = supabase.table('committees_history').select("*").execute()
        return response.data
    except Exception as e:
        print("Error fetching committees_history:", e)
        return []

# 4. Dimension (의원 기본 정보) - 기존 /api/legislators 대체 가능
@app.get("/api/dimension", response_model=List[schemas.DimensionResponse])
def get_dimensions():
    try:
        response = supabase.table('dimension').select("*").execute()
        return response.data
    except Exception as e:
        print("Error fetching dimension:", e)
        return []

# 5. Meetings (회의 정보)
@app.get("/api/meetings", response_model=List[schemas.Meeting])
def get_meetings():
    try:
        response = supabase.table('meetings').select("*").execute()
        return response.data
    except Exception as e:
        print("Error fetching meetings:", e)
        return []

# 6. Member Bill Stats (의원 법안 통계)
@app.get("/api/member-bill-stats", response_model=List[schemas.MemberBillStats])
def get_member_bill_stats():
    try:
        response = supabase.table('member_bill_stats').select("*").execute()
        return response.data
    except Exception as e:
        print("Error fetching member_bill_stats:", e)
        return []

# 7. Member Stats (의원 활동 통계)
@app.get("/api/member-stats", response_model=List[schemas.MemberStats])
def get_member_stats():
    try:
        response = supabase.table('member_stats').select("*").execute()
        return response.data
    except Exception as e:
        print("Error fetching member_stats:", e)
        return []

# 8. Parties (정당 정보)
@app.get("/api/parties", response_model=List[schemas.Party])
def get_parties():
    try:
        response = supabase.table('parties').select("*").execute()
        return response.data
    except Exception as e:
        print("Error fetching parties:", e)
        return []

# 9. Parties History (정당 이력)
@app.get("/api/parties-history", response_model=List[schemas.PartyHistory])
def get_parties_history():
    try:
        response = supabase.table('parties_history').select("*").execute()
        return response.data
    except Exception as e:
        print("Error fetching parties_history:", e)
        return []

# 10. Speeches (발언 정보)
@app.get("/api/speeches", response_model=List[schemas.Speech])
def get_speeches():
    try:
        response = supabase.table('speeches').select("*").execute()
        return response.data
    except Exception as e:
        print("Error fetching speeches:", e)
        return []


# ==========================================
# 2. 기존 로직 및 기타 API
# ==========================================

# --- [기존] 프론트엔드용 가공된 의원 목록 API ---
@app.get("/api/legislators")
def get_all_legislators():
    try:
        response = supabase.table('dimension').select("*").execute()
        data = response.data
        results = []
        for item in data:
            score = random.randint(60, 99)
            results.append({
                "id": item.get('member_id'), 
                "name": item.get('name'),
                "party": item.get('party'),
                "region": item.get('district') or item.get('region') or "비례대표",
                "committee": "정보 없음", 
                "gender": item.get('gender', '-'),
                "count": f"{item.get('elected_time', 0)}선" if item.get('elected_time') else "초선",
                "method": item.get('elected_type', '지역구'),
                "score": score, 
                "img": ""
            })
        return results
    except Exception as e:
        print("Lỗi lấy danh sách:", e)
        return []

@app.get("/api/filters")
def get_filters():
    try:
        response = supabase.table('dimension').select("party, committee_id, gender, district").execute()
        data = response.data
        return {
            "parties": sorted(list(set([x['party'] for x in data if x.get('party')]))),
            "committees": [], 
            "genders": sorted(list(set([x['gender'] for x in data if x.get('gender')]))),
            "regions": sorted(list(set([x['district'] for x in data if x.get('district')]))),
            "counts": ["초선", "재선", "3선", "4선", "5선", "6선"],
            "methods": ["지역구", "비례대표"],
        }
    except Exception as e:
        print("Lỗi Filter:", e)
        return {"parties": [], "committees": []}

@app.post("/register", response_model=schemas.UserOut)
def register_user(user: schemas.UserCreate):
    try:
        response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "options": {"data": {"username": user.username, "full_name": user.full_name}}
        })
        if not response.user:
             raise HTTPException(status_code=400, detail="Đăng ký thất bại.")
        return {
             "email": response.user.email,
             "username": response.user.user_metadata.get("username"),
             "full_name": response.user.user_metadata.get("full_name")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/token")
def login_for_access_token(user_data: schemas.UserLogin):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": user_data.email, "password": user_data.password
        })
        return {
            "access_token": response.session.access_token, "token_type": "bearer",
            "user": {"email": response.user.email, "username": response.user.user_metadata.get("username")}
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu sai.")

@app.post("/api/search", response_model=schemas.SearchResponse)
def search_analysis(data: schemas.SearchInput):
    try:
        query = supabase.table('dimension').select("*, committees(name)")
        if data.query:
            query = query.ilike('name', f"%{data.query}%")
        
        committee_val = data.committee or data.filters.get("committee")
        if committee_val and committee_val != "전체":
            query = query.eq('committee_id', int(committee_val))
        
        response = query.execute()
        found = response.data
        
        if not found: 
            return {"results": [], "total_count": 0, "message": "검색 결과가 없습니다."}
        
        results = []
        for item in found:
            committee_info = item.get('committees')
            committee_name = committee_info.get('name') if committee_info else "정보 없음"
            results.append({
                "id": item.get('member_id'),
                "name": item.get('name'),
                "party": item.get('party'),
                "committee": committee_name,
                "region": item.get('district', '-'),
                "img": item.get('image_url', ''),
                "gender": item.get('gender'),
                "count": f"{item.get('elected_time', 0)}선" if item.get('elected_time') else "초선",
                "method": item.get('elected_type', '지역구')
            })

        return {
            "results": results,
            "total_count": len(results),
            "message": "성공적으로 조회되었습니다."
        }
    except Exception as e:
        print("Lỗi Search:", e)
        raise HTTPException(status_code=500, detail=str(e))

# --- [신규] JSON 데이터 수신 API (기존 유지) ---
@app.post("/api/speech")
def process_speech_data(data: schemas.SpeechData):
    try:
        print(f"Received speech data: ID={data.speech_id}, Member={data.member_name}")
        return {
            "message": "데이터가 성공적으로 수신되었습니다.",
            "received_id": data.speech_id,
            "speaker": data.member_name,
            "status": "success"
        }
    except Exception as e:
        print("Lỗi Speech API:", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sentiment", response_model=schemas.SentimentOutput)
def analyze_sentiment(data_in: schemas.AnalysisInput, current_user = Depends(get_current_user)):
    return {"label": "협력 (Hợp tác)", "confidence_score": 0.95}

@app.post("/prediction", response_model=schemas.PredictionOutput)
def predict_legislation(data_in: schemas.AnalysisInput, current_user = Depends(get_current_user)):
    return {"label": "가결 (Thông qua)", "probability": 0.88}

@app.get("/api/dashboard-stats")
def get_dashboard_stats():
    return {
        "sentiment": {"cooperative": 65, "non_cooperative": 35, "neutral": 0},
        "prediction": {"bill_name": "AI 기본법 (안)", "probability": 87, "status": "예측 완료"}
    }

@app.get("/")
def read_root():
    return {"message": "K-LegiSight API is running!"}

@app.get("/personal-bills")
def get_personal_bills(current_user = Depends(get_current_user)):
    return [
        {"bill_id": 1, "title": "AI 발전 촉진법", "status": "심사 중"},
        {"bill_id": 2, "title": "데이터 보호법", "status": "통과"},
    ]