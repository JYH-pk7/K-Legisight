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


def clean_party_name(text):
    if not text:
        return ""
    text = text.lstrip("/")                     # ① 맨 앞의 슬래시 제거
    parts = [p for p in text.split("/") if p]   # ② '/'로 분리
    unique = []
    for p in parts:
        if p not in unique:                     # ③ 중복 제거
            unique.append(p)
    return "/".join(unique)

def clean_party_name(text):
    if not text:
        return ""
    text = text.lstrip("/")                     # ① 맨 앞의 슬래시 제거
    parts = [p for p in text.split("/") if p]   # ② '/'로 분리
    unique = []
    for p in parts:
        if p not in unique:                     # ③ 중복 제거
            unique.append(p)
    return "/".join(unique)

# 테스트
samples = [
    "/미래통합당/국민의힘",
    "/더불어민주당/더불어민주당",
    "/국민의힘/국민의힘/자유한국당",
    None
]

for s in samples:
    print(clean_party_name(s))

