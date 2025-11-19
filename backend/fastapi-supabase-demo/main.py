import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional, List

# .env 파일에서 환경 변수 로드
load_dotenv()

# Supabase 연결 정보
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Supabase 클라이언트 초기화
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    # 실제 프로덕션에서는 여기서 앱을 중단하거나 기본값을 설정할 수 있습니다.
    supabase = None

app = FastAPI()

# --- Pydantic 모델 정의 ---
# 요청 본문(Request Body)용 모델

class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    pass

# 응답 본문(Response Body)용 모델 (DB에서 가져온 id 포함)
class ItemResponse(ItemBase):
    id: int
    created_at: str

    class Config:
        orm_mode = True # SQLAlchemy 같은 ORM 외에도 dict에서 모델을 매핑할 수 있게 함


# --- API 엔드포인트 ---

@app.on_event("startup")
async def startup_event():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client could not be initialized. Check .env file.")

@app.get("/")
def read_root():
    return {"message": "FastAPI가 Supabase와 연결되었습니다!"}

# 1. 아이템 생성 (Create)
@app.post("/items/", response_model=ItemResponse)
def create_item(item: ItemCreate):
    try:
        # Supabase 'items' 테이블에 데이터 삽입
        response = supabase.table("items").insert(item.dict()).execute()
        
        # Supabase Python 클라이언트는 .execute() 후 'data' 속성에 결과를 담아 반환
        if response.data:
            # 반환된 데이터(리스트의 첫 번째 항목)를 ItemResponse 모델에 맞게 변환
            created_item = response.data[0]
            created_item['created_at'] = str(created_item['created_at']) # 날짜/시간 객체를 문자열로
            return created_item
        else:
            raise HTTPException(status_code=400, detail="Item could not be created")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. 모든 아이템 조회 (Read All)
@app.get("/items/", response_model=List[ItemResponse])
def read_items():
    try:
        response = supabase.table("items").select("*").order("created_at", desc=True).execute()
        if response.data:
            # Supabase에서 반환된 각 항목의 created_at을 문자열로 변환
            items_list = []
            for item in response.data:
                item['created_at'] = str(item['created_at'])
                items_list.append(item)
            return items_list
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. 특정 아이템 조회 (Read One)
@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int):
    try:
        # .eq()는 'equals' 필터
        # .single()은 결과가 정확히 하나일 것으로 예상할 때 사용 (없거나 많으면 에러)
        # 여기서는 .execute() 후 수동으로 확인하는 것이 더 안전할 수 있습니다.
        response = supabase.table("items").select("*").eq("id", item_id).execute()
        
        if response.data:
            item = response.data[0]
            item['created_at'] = str(item['created_at'])
            return item
        else:
            raise HTTPException(status_code=404, detail="Item not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. 아이템 수정 (Update)
@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: ItemCreate):
    try:
        response = supabase.table("items").update(item.dict()).eq("id", item_id).execute()
        
        if response.data:
            updated_item = response.data[0]
            updated_item['created_at'] = str(updated_item['created_at'])
            return updated_item
        else:
            raise HTTPException(status_code=404, detail="Item not found or could not be updated")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. 아이템 삭제 (Delete)
@app.delete("/items/{item_id}", response_model=ItemResponse)
def delete_item(item_id: int):
    try:
        # 삭제는 먼저 항목을 조회하고 반환값을 준비한 뒤 삭제를 실행
        select_response = supabase.table("items").select("*").eq("id", item_id).execute()
        
        if not select_response.data:
            raise HTTPException(status_code=404, detail="Item not found")
            
        deleted_item_data = select_response.data[0]
        deleted_item_data['created_at'] = str(deleted_item_data['created_at'])

        # 삭제 실행
        delete_response = supabase.table("items").delete().eq("id", item_id).execute()
        
        if delete_response.data:
            return deleted_item_data # 미리 저장해둔 삭제된 아이템 정보 반환
        else:
            raise HTTPException(status_code=500, detail="Error deleting item")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))