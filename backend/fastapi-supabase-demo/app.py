# app.py
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import httpx

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY in .env")

# Base REST endpoint
SUPABASE_REST_BASE = f"{SUPABASE_URL.rstrip('/')}/rest/v1"
# Use fully qualified table name: assembly.meetings
TABLE_PATH = "assembly.meetings"

app = FastAPI(title="Assembly Meetings API (Supabase)")

# Pydantic model for output (matching your DDL)
class MeetingOut(BaseModel):
    meeting_id: int
    meeting_category: Optional[str] = None
    daesu: Optional[int] = None
    meeting_specification: Optional[str] = None
    commitee: Optional[str] = None
    number_of_meetings: Optional[int] = None
    chasu: Optional[int] = None
    meeting_date: Optional[str] = None

async def supabase_request(method: str, table: str = TABLE_PATH, path: str = "", params=None, json=None, headers=None):
    # Note: PostgREST path for schema-qualified table: /rest/v1/<schema>.<table>
    url = f"{SUPABASE_REST_BASE}/{table}{path}"
    default_headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if headers:
        default_headers.update(headers)
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.request(method, url, params=params, json=json, headers=default_headers)
    return resp

# List meetings (optionally filter by meeting_category or limit)
@app.get("/meetings", response_model=List[MeetingOut])
async def list_meetings(meeting_category: Optional[str] = None, limit: int = 100):
    params = {"select": "*", "limit": limit}
    if meeting_category:
        params["meeting_category"] = f"eq.{meeting_category}"
    resp = await supabase_request("GET", path="", params=params)
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

# Get single meeting by meeting_id (bigint)
@app.get("/meetings/{meeting_id}", response_model=MeetingOut)
async def get_meeting(meeting_id: int):
    # Use query: ?select=*&meeting_id=eq.<value>
    resp = await supabase_request("GET", path=f"?select=*&meeting_id=eq.{meeting_id}")
    if resp.status_code == 200:
        items = resp.json()
        if not items:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return items[0]
    raise HTTPException(status_code=resp.status_code, detail=resp.text)