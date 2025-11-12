import requests
from pymongo import MongoClient
from datetime import datetime
import time

# -----------------------------
# 1. MongoDB Atlas 연결
# -----------------------------
ATLAS_URI = "mongodb+srv://bluman2:lotte8492@cluster0.h4sfdv2.mongodb.net/assembly?retryWrites=true&w=majority"
client = MongoClient(ATLAS_URI)
db = client["assembly"]
dimension_col = db["dimension"]

# -----------------------------
# 2. RESTful API 호출
# -----------------------------
BASE_URL = "https://open.assembly.go.kr/portal/openapi/ALLNAMEMBER"
API_KEY = "627bdec10a6e474788bd85f08ea9be9f"

all_members = []
page_no = 1
pSize = 1000  # 한 페이지 최대 요청 수

while True:
    params = {
        "key": API_KEY,
        "type": "json",
        "pIndex": page_no,
        "pSize": pSize
    }

    resp = requests.get(BASE_URL, params=params)
    if resp.status_code != 200:
        print(f"API 호출 실패: {resp.status_code}")
        break

    data = resp.json()
    # 최신 API 구조: 'ALLNAMEMBER' -> [0]=head, [1]=row
    rows = []
    allnamember = data.get("ALLNAMEMBER", [])
    if len(allnamember) > 1:
        rows = allnamember[1].get("row", [])

    if not rows:
        break

    all_members.extend(rows)
    page_no += 1
    time.sleep(0.2)

print(f"총 의원 수집: {len(all_members)}명")

# -----------------------------
# 3. 21대 국회의원 필터링
# -----------------------------
members_21 = []
for m in all_members:
    gtelts = m.get("GTELT_ERACO")
    if gtelts and "21대" in gtelts:  # None 체크 추가
        members_21.append(m)

print(f"21대 국회의원 수: {len(members_21)}")

# -----------------------------
# 4. MongoDB 삽입
# -----------------------------
def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except:
        return None

for m in members_21:
    member_doc = {
        "members": {
            "name": m.get("NAAS_NM", ""),
            "gender": m.get("NTR_DIV", ""),
            "birthyear": parse_date(m.get("BIRDY_DT")),
            "district": m.get("ELECD_NM", ""),
            "start_date": None,  # API 미제공
            "end_date": None     # API 미제공
        },
        "member_party_history": {
            "party_1": m.get("PLPT_NM", ""),
            "party_1_start_date": None,
            "party_1_end_date": None,
            "party_2": m.get("PLPT_NM", ""),
            "party_2_start_date": None, 
            "party_2_end_date": None
        },
        "member_committee_history": {
            "committee_1": m.get("CMIT_NM", ""),
            "committee_2": m.get("BLNG_CMIT_NM", ""),
            "committee_1_start_date": None,
            "committee_1_end_date": None,
            "committee_2_start_date": None,
            "committee_2_end_date": None
        },
        "committee_id": m.get("BLNG_CMIT_NM", ""),
        "bills": {
            "bill_id": 0,
            "title": ""
        },
        "party_id": m.get("PLPT_NM", "")
    }

    # _id를 NAAS_CD로 지정, $set에는 _id 포함하지 않음
    filter_doc = {"_id": m.get("NAAS_CD")}
    update_doc = member_doc.copy()
    update_doc.pop("_id", None)

    dimension_col.update_one(filter_doc, {"$set": update_doc}, upsert=True)

print("dimension 컬렉션에 21대 국회의원 삽입 완료")