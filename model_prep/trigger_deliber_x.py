#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
trigger_deliber_x.py
-----------------
1) 회의 전체 JSON에서 bill_pool(의사일정 항 전체) 생성
2) 소위원장 발언만 LLM에 던져서:
   - tf_trigger (트리거 발언 여부)
   - agenda_items (의사일정 제○항 번호 리스트) 추출
3) 트리거 발언의 speech_order 기준으로 심사구간(delib_order) 분할
4) 각 심사구간에 해당하는 bill_review(해당 구간에서 심사되는 법안 목록)를
   구간 안 모든 발언에 부여
5) 결과를 원래 JSON 구조에 필드만 추가해서 저장

입출력
- 입력:  ./meeting_number_filltered/speeches_meeting_<MEETING_ID>.json
- 출력:  ./trigger_deliber_output/speeches_triggerdeliber_<MEETING_ID>.json
- 로그:  ./trigger_deliber_output/trigger_deliber_<MEETING_ID>.log
"""

import os
import re
import json
import requests
from datetime import datetime
import sys
import glob

# =========================================
# 설정
# =========================================
OLLAMA_API = "http://localhost:11434/api/generate"
MODEL = "gemini-3-pro-preview"
TEMPERATURE = 0.005
TIMEOUT = 1500

# CLI에서 meeting_id 를 받아 처리
if len(sys.argv) != 2 and len(sys.argv) != 3:
    print("사용법: python trigger_deliber_x.py <MEETING_ID> [OUTPUT_FILE]")
    sys.exit(1)

MEETING_ID = sys.argv[1] 

# =========================================
# 트리거 후보 전처리 키워드
# =========================================
INCLUDE_KEYWORDS = [
    # 1. 안건 번호/절차 진입
    "의사일정",

    # 2. 심사 시작/진행
    "심사를 하겠습니다",
    "심사하겠습니다",
    "심사하도록",
    "심사합니다",
    "심의합니다",
    "심의하기로",
    "심의하도록",

    # 3. 상정 + 일괄심사/계속심사
    "상정합니다",
    "일괄하여 심사",
    "일괄 심사",
    "함께 심사",
    "병합하여 심사",
    "재심사",

    # 4. 전문위원/수석전문위원 보고·설명 요청
    "보고해 주시기 바랍니다",
    "보고하여 주시기 바랍니다",
    "보고해 주십시오",
    "보고해 주시기",
    "설명 바랍니다",
    "설명해 주시기 바랍니다",
    "설명하여 주시기 바랍니다",
    "설명해 주십시오",
    "설명하여 주십시오",
    "주요 내용을 설명",
    "주요 사항을 설명",

    # 5. 안건 전환/새 구간 시작 신호
    "다음으로",
    "다음 안건",
    "이어서",
]

def is_trigger_candidate(text: str) -> bool:
    """트리거 발언이 될 가능성이 있는지 키워드 기반으로 1차 필터."""
    if not text:
        return False

    # 정회 + 산회 관련 표현은 전부 후보 제외
    RECESS_KEYWORDS = [
        "정회를 선포합니다",
        "정회하겠습니다",
        "정회하도록 하겠습니다",
        "정회를 하겠습니다"
    ]
    if "산회" in text:
        return False

    if any(p in text for p in RECESS_KEYWORDS):
        return False

    # 기본 포함 키워드
    return any(kw in text for kw in INCLUDE_KEYWORDS)

# =========================================
# LLM 호출 / JSON 파싱 유틸
# =========================================
def call_llm(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": TEMPERATURE,
        },
    }
    try:
        res = requests.post(OLLAMA_API, json=payload, timeout=TIMEOUT)
        res.raise_for_status()
        return res.json().get("response", "")
    except Exception as e:
        # 여기서 에러 타입도 같이 찍고 있음
        return f" LLM 호출 오류: {type(e).__name__}: {e}"


def extract_json_array(resp: str):
    """
    응답 문자열에서 JSON 배열만 추출해서 파싱.
    LLM이 약간 틀린 JSON을 내도 (True/False, trailing comma 등)
    최대한 보정해서 파싱하려고 시도한다.
    """
    if not resp:
        return []

    # 대충이라도 어디부터 어디까지가 JSON 배열인지 먼저 잡기
    m = re.search(r"\[.*\]", resp, re.DOTALL)
    if not m:
        return []

    text = m.group(0)

    # 1) Python 스타일 True/False/None → JSON 스타일 true/false/null 로 보정
    text = re.sub(r"\bTrue\b", "true", text)
    text = re.sub(r"\bFalse\b", "false", text)
    text = re.sub(r"\bNone\b", "null", text)

    # 2) 마지막 요소 뒤에 붙은 trailing comma 제거
    #    [..., ]  / {..., }  이런 패턴들
    text = re.sub(r",\s*([\]\}])", r"\1", text)

    try:
        return json.loads(text)
    except Exception as e:
        # 디버깅용으로 한 번 찍어보면 좋음
        print(" JSON 파싱 오류:", e)
        # 실패하면 빈 리스트 반환
        return []


def is_valid_llm_response(resp: str) -> bool:
    """LLM 응답이 사용 가능한지 간단히 검사."""
    if not resp:
        return False
    if "LLM 호출 오류" in resp:  # 우리가 만든 에러 문자열
        return False
    # 최소한 JSON 배열 대괄호는 있어야 함
    if "[" not in resp:
        return False
    return True

# =========================================
# bill_pool 생성 (전체 수집 후 중복 제거)
# =========================================
def build_bill_pool_from_all(speeches):
    """
    회의 JSON 전체에서 모든 bills를 모아서 bill_pool을 만든다.

    bills의 각 줄은 보통 다음과 같은 형식이다.
      "1. 서민의 금융생활 지원에 관한 법률 일부개정법률안(정부 제출)(의안번호 2104052)"

    여기서 맨 앞의 숫자(1, 2, ..., 86 등)를
    '의사일정 제1항, 제2항, ...'의 번호로 그대로 사용한다.
    """

    bill_pool = {}  # key = agenda_idx (의사일정 항 번호), value = dict(raw=원본 문자열, bill_no=의안번호)

    for s in speeches:
        bills_text = s.get("bills")
        if not bills_text:
            continue

        for line in bills_text.split("\n"):
            line = line.strip()
            if not line:
                continue

            # 맨 앞 번호 추출: "  48. ..." → idx=48, 나머지는 그대로 raw로 둔다
            m = re.match(r"^\s*(\d+)\.\s*(.*)$", line)
            if not m:
                continue

            agenda_idx = int(m.group(1))
            raw = line  # 원문 그대로

            if agenda_idx not in bill_pool:
                # 의안번호도 참고용으로 뽑아둔다 (필수는 아님)
                m_no = re.search(r"의안번호\s*(\d+)", raw)
                bill_no = m_no.group(1) if m_no else None
                bill_pool[agenda_idx] = {
                    "idx": agenda_idx,
                    "raw": raw,
                    "bill_no": bill_no,
                }
            # 이미 있으면 첫번째 것을 유지 (대부분 동일)

    return bill_pool

# =========================================
# 프롬프트 구성: 소위원장 발언만
# =========================================
def build_prompt_for_chair_triggers(chair_speeches, bill_pool):
    """
    소위원장 발언들만 가지고,
    각 발언이 안건 심사 트리거인지, 몇 항부터 몇 항까지/몇 항들인지
    (bill_pool의 agenda_idx를 기준으로) 뽑게 하는 프롬프트.
    """

    chair_block = "\n\n".join(
        f"[{s['speech_order']}] {s['member_name']}: {s['speech_text']}"
        for s in chair_speeches
    )

    bills_block = "\n".join(
        bill_pool[idx]["raw"] for idx in sorted(bill_pool.keys())
    )

    return f"""
너는 대한민국 국회 회의록을 분석하는 전문가다.
소위원장 발언만 보고, 각 발언이 새로운 안건 심사를 시작하는
'트리거 발언'인지 판단하고, 실제로 지금부터 다루게 되는
의사일정 항 번호들을 찾아야 한다.

====================
[해야 할 일]

각 소위원장 발언에 대해 다음을 판단하라.

1) tf_trigger (true/false)
   - 이 발언에서 새로운 안건의 심사/의결을 시작하면 true
   - 단순 진행 멘트, 회의 마무리, 인사만 하면 false
   - 반드시 최소 한 개 이상의 발언은 tf_trigger=true로 판단해야 한다.

2) agenda_items (정수 배열)
   - 이 발언에서 **지금부터 또는 다음으로** 심사/계속심사/심의 하겠다고
     선언하는 의사일정 항 번호들을 모두 넣는다.
   - 이전 발언에서 다뤘던 항 번호를 이어받아 넣지 말고,
     **반드시 이 발언 텍스트 안에서 숫자로 등장한 항 번호만** 사용하라.

의사일정 항 번호는 아래 [안건(법률안) 목록]의 번호(1, 2, 3, …)와 같다고 가정한다.

====================
[출력 형식]

반드시 아래와 같은 JSON 배열만 출력하라.

[
  {{
    "speech_order": <정수>,
    "tf_trigger": <true or false>,
    "agenda_items": [<정수들>]
  }},
  ...
]

- 배열의 각 원소는 하나의 소위원장 발언에 대한 결과이다.
- "speech_order" 값은 아래 소위원장 발언 목록에 나온 번호를 그대로 사용한다.
- 트리거가 아닌 경우: "tf_trigger": false, "agenda_items": [] 로 둔다.

====================
[해석 규칙]

각 발언을 해석할 때 아래 네 가지 규칙을 모두 함께 고려하여,
텍스트의 실제 의미에 가장 잘 맞는 해석을 선택하라.
애매한 경우에는 바로 아래 [예시]들 중 가장 유사한 패턴을 기준으로 판단하라.

1) 심사/설명/보고/재심사/심의 “선언이 있는 문장만” 트리거로 취급한다.
   - 다음과 같은 표현이 포함되면, 이 발언은 심사 개시 트리거(tf_trigger=true)가 될 가능성이 높다.
     예:
       - "심사하도록 하겠습니다"
       - "심사하겠습니다"
       - "일괄하여 심사하겠습니다"
       - "함께 심사하겠습니다"
       - "함께 심사하도록 하겠습니다"
       - "다시 심사하도록 하겠습니다"
       - "재심사하도록 하겠습니다"
       - "계속 설명해 주시기 바랍니다"
       - "계속 설명하여 주시기 바랍니다"
       - "설명해 주시기 바랍니다"
       - "설명하여 주시기 바랍니다"
       - "보고해 주십시오"
       - "보고해 주시기 바랍니다"
       - "보고하여 주시기 바랍니다"
       - "다음은 의사일정 제○항부터 제○항까지 … 심사하도록 하겠습니다"
       - "다음은 의사일정 제○항 … 심사하도록 하겠습니다"
       - "먼저 의사일정 제○항 … 심사하도록 하겠습니다"
   - 특히 "수석전문위원님" 또는 "전문위원님"이 등장하고,
     같은 발언 안에 "의사일정 제○항"과
     "설명해 주시기 바랍니다/설명하여 주시기 바랍니다/설명해 주시기 바랍니다."와 같은 표현이 함께 나오면,
     항상 해당 발언을 심사 개시 트리거(tf_trigger=true)로 간주하고,
     그 문장 안에서 언급된 의사일정 항 번호들을 agenda_items에 포함하라.
   - 위와 같은 심사/설명/보고/재심사/심의 표현이 전혀 없다면,
     그 발언은 보통 단순 진행/의결/인사/정회/산회 등의 멘트이므로
     tf_trigger=false, agenda_items=[] 로 둔다.

2) “상정만 한 구간”과 “소위원회 계속심사만 언급한 구간”은 제외한다.
   - 아래와 같은 표현만 있고, 그 안에 심사/설명/보고/재심사 표현이 없다면
     그 부분에서 언급된 항 번호는 agenda_items에 넣지 않는다.
     예:
       - "의사일정 제1항부터 제47항까지 이상 47건의 법률안을 일괄하여 상정합니다."
       - "의사일정 제40항부터 제47항까지는 소위원회에서 계속 심사하도록 하겠습니다."
   - 이 표현 이후에 같은 발언 안 뒤쪽에서
     "의사일정 제○항을 심사하도록 하겠습니다",
     "의사일정 제○항에 대하여 설명해 주시기 바랍니다",
     "전문위원께서는 설명해 주시기 바랍니다",
     "수석전문위원(전문위원) 보고해 주시기 바랍니다"
     "전문위원님 보고해주시기 바랍니다"
     와 같이 **실제로 심사/설명/보고를 시작하는 구간이 나오면**,
     → 그 뒤에 언급된 심사 구간만 트리거로 보고, 해당 숫자들만 agenda_items에 넣는다.
     (앞의 상정/소위원회 계속심사 구간에서 언급된 숫자는 무시한다.)

3) 항 번호는 “이 발언 안에서 실제로 숫자로 등장한 의사일정 항 번호만” 사용한다.
   - 반드시 이 발언 내부에서 숫자로 언급된 항 번호만 agenda_items에 포함하라.
   - 이전 발언이나 회의 전체 내용을 추론하여 항 번호를 추가하지 마라.
   - 숫자 인식 규칙:
       - "제4항부터 제7항까지" → [4, 5, 6, 7]
       - "제8항, 제9항, 제11항" → [8, 9, 11]
       - "제1․2․3항" → [1, 2, 3]
       - "의사일정 제5항, 6항, 7항" → [5, 6, 7]
   - 의결/가결/“이의 없으십니까” 등 이미 심사를 마친 안건에 대한
     단순 의결·선포 멘트에서 언급된 숫자는 agenda_items에 넣지 않는다.
   - 소위원회에서 계속심사하기로 한 구간(이 회의에서 실제로 다루지 않는 구간)의 숫자도
     agenda_items에 넣지 않는다.

4) 한 발언 안에 여러 구간(상정/의결/계속심사/새 심사 시작 등)이 섞여 있을 경우,
   “발언 가장 마지막에 등장하는 실제 심사/설명/보고 구간만” agenda_items로 사용한다.
   - 예)
     "의사일정 제1항부터 제47항까지 이상 47건의 법률안을 일괄하여 상정합니다.
      그러면 의사일정 제1항부터 제3항까지 이상 3건의 서민의 금융생활 지원에 관한 법률 일부개정법률안을 일괄하여 심사하도록 하겠습니다."
     → 상정 구간(1~47항)은 무시하고,
       실제 심사 구간인 제1~3항만 agenda_items = [1, 2, 3] 으로 사용한다.
   - 예)
     "… 의사일정 제4항 … 가결되었음을 선포합니다. … 의사일정 제25항 … 가결되었음을 선포합니다.
      의사일정 제32항 … 가결되었음을 선포합니다.
      다음은 의사일정 제5항부터 제7항까지 이상 3건의 자본시장과 금융투자업에 관한 법률 일부개정법률안을 일괄하여 심사하도록 하겠습니다."
     → 의결된 4, 25, 32항은 이미 끝난 안건이므로 제외하고,
       마지막에 나온 심사 구간인 제5~7항만 agenda_items = [5, 6, 7] 로 사용한다.
   - 예)
     "의사일정 제40항부터 제47항까지는 보다 심도 있는 심사를 위해서 소위원회에서 계속 심사하도록 하겠습니다.
      의사일정 제4항 금융혁신지원 특별법 일부개정법률안에 대해서 우리 수석전문위원님께서 보고해 주시기 바랍니다."
     → 40~47항(소위 계속심사)은 이 회의에서 실제로 심사하는 구간이 아니므로 제외하고,
       제4항만 agenda_items = [4] 로 사용한다.
   - 이 원칙은 ‘보류 후 다음 심사’, ‘다시 1항부터 19항으로 돌아가겠습니다’,
     ‘여러 항을 함께 심사’, ‘전문위원에게 설명 요청’ 등
     아래 예시들 전체에 동일하게 적용된다.

위 네 가지 규칙과 아래 [예시]들을 함께 참고하여,
각 발언의 tf_trigger와 agenda_items을 결정하라.

====================
[예시]

[예시]

예시 1) (기본적인 심사선언)
발언:
"의사일정 제1항부터 제3항까지 이상 3건의 서민의 금융생활 지원에 관한 법률 일부개정법률안을 일괄하여 심사하도록 하겠습니다."

→ 출력:
{{
  "speech_order": 25,
  "tf_trigger": true,
  "agenda_items": [1, 2, 3]
}}

예시 2) (앞 구간 종료 후 다음 구간 심사 선언)
발언:
"의사일정 제1항부터 제3항까지는 이미 심사를 마쳤고,
다음으로 제4항부터 제7항까지 이상 4건의 법률안을 일괄하여 심사하도록 하겠습니다."

→ 출력:
{{
  "speech_order": 400,
  "tf_trigger": true,
  "agenda_items": [4, 5, 6, 7]
}}

예시 3) (상정만 한 뒤, 실제 심사 구간은 따로 지정)
발언:
"그러면 심사할 안건을 상정하겠습니다. 의사일정 제1항부터 제47항까지 이상 47건의 법률안을 일괄하여 상정합니다.
그러면 의사일정 제1항부터 제3항까지 이상 3건의 서민의 금융생활 지원에 관한 법률 일부개정법률안을 일괄하여 심사하도록 하겠습니다."

→ 출력:
{{
  "speech_order": 10,
  "tf_trigger": true,
  "agenda_items": [1, 2, 3]
}}
(앞부분의 제1항~제47항은 상정만 했으므로 제외하고, 실제 심사 대상인 제1~3항만 포함.)

예시 4) (계속심사 구간 + 전문위원에게 보고 요청으로 심사 개시)
발언:
"의사일정 제40항부터 제47항까지는 보다 심도 있는 심사를 위해서 소위원회에서 계속 심사하도록 하겠습니다.
의사일정 제4항 금융혁신지원 특별법 일부개정법률안에 대해서 우리 수석전문위원님께서 보고해 주시기 바랍니다."

→ 출력:
{{
  "speech_order": 299,
  "tf_trigger": true,
  "agenda_items": [4]
}}
(40~47항은 소위원회 계속심사이므로 제외, 실제로 지금 심사하는 것은 제4항.)

예시 5) (여러 의결 후, 다음 심사 구간 시작)
발언:
"… 의사일정 제4항 … 가결되었음을 선포합니다. … 의사일정 제25항 … 가결되었음을 선포합니다.
의사일정 제32항 … 가결되었음을 선포합니다.
다음은 의사일정 제5항부터 제7항까지 이상 3건의 자본시장과 금융투자업에 관한 법률 일부개정법률안을 일괄하여 심사하도록 하겠습니다."

→ 출력:
{{
  "speech_order": 345,
  "tf_trigger": true,
  "agenda_items": [5, 6, 7]
}}
(앞의 4, 25, 32항은 이미 심사를 마친 안건에 대한 의결/선포이고,
마지막 "다음은 … 심사하도록 하겠습니다" 부분이 새 심사 구간이므로 5~7만 포함.)

예시 6) (여러 의결 후, 앞에서 다룬 1·2·3항 재심사 시작)
발언:
"… 의사일정 제8항, 9항, 10항, 11항, 30항은 각각 가결되었음을 선포합니다.
그리고 오전에 논의했던 제1․2․3항을 다시 심사하도록 하겠습니다."

→ 출력:
{{
  "speech_order": 624,
  "tf_trigger": true,
  "agenda_items": [1, 2, 3]
}}


예시 7) (앞 항을 의결 후 다시 1~19항 심사 선언으로 돌아가기)
발언: 
"의사일정 제24항은 수정 의결하고자 하는데 이의 없으십니까? (「예」 하는 위원 있음)
가결되었음을 선포합니다. 다시 1항부터 19항으로 돌아가겠습니다."

→ 출력:
{{
  "speech_order": 450,
  "tf_trigger": true,
  "agenda_items": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
}}


예시 8) (보류 후 다음 안건 심사 시작)
발언:
"이것은 보류하겠습니다. 그래서 이따 저녁 식사 시간에 다시 한번 논의하겠고요.
다음, 의사일정 제4항 신현영 의원이 대표발의한 남북 보건의료의 교류협력 증진에 관한 법률안을 심사하겠습니다.
전문위원께서 이 안건의 주요 내용에 대해서 계속 설명해 주시기 바랍니다."

→ 출력:
{{
  "speech_order": 133,
  "tf_trigger": true,
  "agenda_items": [4]
}}
(‘보류하겠습니다’가 먼저 나와도, 바로 이어서 ‘다음 의사일정 제○항 … 심사하겠습니다’가 나오면
새로운 심사 구간으로 간주한다.)


예시 9) (앞 구간을 제시하고, 이어지는 문장에서 추가 구간을 함께 심사한다고 하면서 합쳐서 심사)

발언:
"더 이상 의견이 없으시면 이 안건은 계속 심사하도록 하겠습니다.
다음은 의사일정 제12항부터 제16항 김홍걸 의원, 송영길 의원, 임종성 의원, 안민석 의원이 각각 대표발의한
남북관계 발전에 관한 법률 일부개정법률안과 관련 청원을 심사하겠습니다.
이 안건의 심사와 관련하여 의사일정 제17항부터 제19항의 남북교류협력법 일부개정법률안에도
같은 취지로 대북전단지 살포 제한 내용이 있어 함께 심사하도록 하겠습니다.
전문위원께서는 이들 안건 전체의 심사 경과와 주요 내용을 설명해 주시기 바랍니다."

→ 출력:
{{
  "speech_order": 210,
  "tf_trigger": true,
  "agenda_items": [12, 13, 14, 15, 16, 17, 18, 19]
}}

예시 10) (전문위원을 부르면서 특정 항목 설명 요청)
발언:
"의석을 정돈하여 주시기 바랍니다. 성원이 되었으므로 회의를 속개하겠습니다.
수석전문위원님, 의사일정 제38항과 제39항에 대하여 설명하여 주시기 바랍니다."

→ 출력:
{{
  "speech_order": 510,
  "tf_trigger": true,
  "agenda_items": [38, 39]
}}

예시 11) (오늘 방금 심사한 안건에 대해 계속심사만 선언하는 경우)

발언:
"위원님들 말씀해 주십시오. (「없습니다」 하는 위원 있음)
그러면 오늘 방금 심사한 의사일정 제6항부터 제11항까지 6건의 방위사업법 일부개정법률안은
보다 심도 있는 논의를 위해서 계속 심사하도록 하겠습니다.
다음번에 법안소위를 3월 달에 임시회가 열리면 조금 더 시간을 할애해서 또 심도 깊은 토의를 하도록 하겠습니다. …"

→ 출력:
{{
  "speech_order": <해당 번호>,
  "tf_trigger": false,
  "agenda_items": []
}}

(이미 '오늘 방금 심사한' 안건에 대해
이 회의에서는 더 이상 심사를 진행하지 않고
다음 회의로 넘기는 '계속심사' 결정만 하는 발언이므로
새로운 심사 구간 트리거가 아니다.)

예시 12) (여러 건 상정 후 곧바로 전문위원 설명 요청)
발언:
"의사일정 제56항 이재정 의원이 대표발의한 국제기구 분담금 관리에 관한 법률안부터
의사일정 제60항 조태용 의원이 대표발의한 미국 신행정부 출범에 즈음한
한미동맹의 미래 발전을 위한 특별결의안까지 이상 5건을 일괄하여 상정합니다.
이 안건의 심사 경과와 합의된 사항에 대하여 수석전문위원께서 설명해 주시기 바랍니다."

→ 출력:
{{
  "speech_order": <해당 번호>,
  "tf_trigger": true,
  "agenda_items": [56, 57, 58, 59, 60]
}}
(이 발언은 단순 상정만 하는 것이 아니라,
곧바로 "수석전문위원께서 설명해 주시기 바랍니다"라고 하여
지금 이 회의에서 해당 안건들의 심사·설명을 시작하므로
새로운 심사 구간을 여는 트리거로 본다.)

예시 13) (수정부분이 있고 전문위원에게 설명 요청)
발언:
"지금 저희가 처리해야 될 의사일정 제13항․14항에 대한 수정 부분이 있는데요.
전문위원님 설명해 주시기 바라겠습니다."

→ 출력:
{{
"speech_order": <해당 번호>,
"tf_trigger": true,
"agenda_items": [13, 14]
}}

(해당 발언에서 제13항·14항을 지칭한 뒤 곧바로
“전문위원님 설명해 주시기 바랍니다”라는 설명 요청이 나타나므로
이는 새로운 심사 구간 개시로 판단한다.)

예시 14) (문장이 끊겼고 뒤에 ‘심사/설명/보고’가 아직 없는 경우는 트리거 아님)
발언: 
"의사일정 제49항부터 제57항까지 이상 9건의 농수산물 유통 및 가격안정에 관한……"
→ 출력:
{{
"speech_order": <해당 번호>,
  "tf_trigger": false,
  "agenda_items": []
}}

예시 15) ('심사 후 의결하겠습니다' 발언 + 바로 이어지는 '전문위원 설명요청' = 지금 심사 개시)
발언: 
"교육기본법 개정안을 의결하기에 앞서 효율적인 진행을 위해서 동일 제명인 
의사일정 제54항부터 제56항까지 정일영 의원, 강득구 의원, 이탄희 의원이 각각 대표발의한 
3건의 교육기본법 일부개정법률안까지 심사를 마친 후에 한꺼번에 의결하겠습니다.
전문위원 보고해 주시기 바랍니다."
→ 출력: 
{{
  "speech_order": 787,
  "tf_trigger": true,
  "agenda_items": [54, 55, 56]
}}


예시 16) (‘계속 심사하도록 하겠습니다 + 전문위원 설명요청’ 패턴)
 발언:
"그러면 다음은 의사일정 제5항부터 9항까지 계속 심사하도록 하겠습니다. 전문위원님 보고해 주시기 바랍니다."
→ 출력:
{{
  "speech_order": <번호>,
  "tf_trigger": true,
  "agenda_items": [5, 6, 7, 8, 9]
}}

예시 17) (‘심사를 마치도록 하겠습니다 + 전문위원 설명요청' 패턴)
발언: 
"그러면 10항부터 13항까지 심사를 마치도록 하겠습니다.
… 제49항과 제50항도 함께 심사한 후에 의결하도록 하겠습니다. 전문위원 보고해 주시기 바랍니다."
{{
  "speech_order": <번호>,
  "tf_trigger": true,
  "agenda_items": [49,50]
}}

예시 18) (앞 항은 계속 심사, 뒤 항에서 실제 심사 시작 + 전문위원 보고 요청)
발언: 
“그러면 의사일정 제17항은 계속 심사하는 것으로 하겠습니다.
의사일정 제18항에 대해서 전문위원 보고해 주시기 바랍니다.”
→ 출력:
{{
  "speech_order": <번호>,
  "tf_trigger": true,
  "agenda_items": [18]
}}

예시 19) (계속심사 + 새로운 심사 구간 + 전문위원 보고요청)
벌언: 
“이 안건은 소위원회에서 계속 심사하도록 하겠습니다.
잠깐만요. 그러면 15항에 앞서 16항부터 19항까지를 먼저 심사하도록 하겠습니다.
의사일정 제16항 노인복지법 및 17항 장애인복지법 일부개정법률안을 일괄하여 심사하겠습니다.
유인규 전문위원님, 2건의 법률안에 대해서 일괄하여 보고해 주시기 바랍니다.”
→ 출력:
{{
  "speech_order": <해당 번호>,
  "tf_trigger": true,
  "agenda_items": [16, 17]
}}

예시 20) (의사일정 언급 후 심사 개시 발언, 차관께 보고 요청하는 사항)
발언:
"이어서 의사일정 제13항과 제14항, 5․18민주화운동 관련자 보상 등에 관한 법률 일부개정법률안을 계속해서 심사하겠습니다.
오전에 위원님들께서 확인을 요청하신 상황에 대해서 차관께서 보고해 주시기 바라겠습니다."
→ 출력:
{{
  "speech_order": <해당 번호>,
  "tf_trigger": true,
  "agenda_items": [13, 14]
}}

예시 21) (안건 묶음 + 연속 안건 + 단일 안건이 모두 등장하며 일괄 심사 대상이 되는 경우)
발언: 
"의사일정 제18항 사회보장급여의 이용․제공 및 수급권자 발굴에 관한 법률 일부개정법률안은 원안대로 의결하고자 하는데 이의 없으십니까? (「예」 하는 위원 있음)
가결되었음을 선포합니다.
의사일정 제19항 및 제20항의 국제입양 관련 2건의 제정법률안과
의사일정 제21항부터 제24항까지 총 4건의 입양특례법 개정법률안,
의사일정 제35항의 아동복지법 일부개정법률안까지
총 7개의 법률안을 일괄하여 심사하겠습니다.
전문위원 보고해 주세요."
→ 출력:
{{
  "speech_order": <해당 번호>,
  "tf_trigger": true,
  "agenda_items": [19, 20, 21, 22, 23, 24, 35]
}}


====================
[소위원장 발언 목록]

아래는 이 회의에서 소위원장이 실제로 발언한 내용이다.
각 발언의 speech_order 번호를 반드시 그대로 사용하라.

{chair_block}

====================
[안건(법률안) 목록]

다음은 이 회의에서 다루는 전체 법률안 목록이다.
번호는 의사일정의 항 번호(제1항, 제2항, …)와 대응한다고 가정한다.

{bills_block}
"""


# =========================================
# LLM 결과 정규화
# =========================================
def normalize_chair_results(chair_speeches, raw_results, log):
    """
    LLM이 준 raw_results를 정리해서,
    모든 소위원장 발언에 대해 최소한의 결과를 갖도록 만든다.
    (누락된 발언은 tf_trigger=False, agenda_items=[] 로 채움)
    """
    # speech_order → 결과 맵
    by_order = {}
    for r in raw_results:
        so = r.get("speech_order")
        try:
            so = int(so)
        except Exception:
            continue

        tf = bool(r.get("tf_trigger"))
        items_raw = r.get("agenda_items") or []
        items = []
        for it in items_raw:
            try:
                items.append(int(it))
            except Exception:
                continue

        by_order[so] = {
            "speech_order": so,
            "tf_trigger": tf,
            "agenda_items": items,
        }

    normalized = []
    for s in chair_speeches:
        so = s.get("speech_order")
        if so in by_order:
            normalized.append(by_order[so])
        else:
            # 누락된 경우 기본값
            normalized.append(
                {
                    "speech_order": so,
                    "tf_trigger": False,
                    "agenda_items": [],
                }
            )
            log.write(
                f" LLM 결과에 없는 소위원장 발언 speech_order={so} → 기본값(tf_trigger=False)으로 처리\n"
            )

    # speech_order 기준 정렬
    normalized.sort(key=lambda x: x["speech_order"])
    return normalized


# =========================================
# 심사구간(segments) 생성
# =========================================
def build_bill_review(bill_pool, agenda_items, log):
    """agenda_items(항 번호 리스트) → bill_pool에서 raw 문자열 배열로 변환"""
    bill_review = []
    for idx in agenda_items:
        bill = bill_pool.get(idx)
        if bill:
            bill_review.append(bill["raw"])
        else:
            log.write(f" bill_pool에 없는 의사일정 항 번호: {idx}\n")
    return bill_review


def build_segments(speeches, chair_results, bill_pool, log):
    """
    chair_results에서 tf_trigger=True && agenda_items 있는 것만 트리거로 삼고,
    speech_order를 기준으로 심사구간(delib_order)을 정의한다.
    """

    # 전체 speech_order 최댓값
    valid_orders = [s.get("speech_order") for s in speeches if s.get("speech_order") is not None]
    max_order = max(valid_orders) if valid_orders else 0

    # speech_order → 전체 발언 맵
    by_order_speech = {s["speech_order"]: s for s in speeches if s.get("speech_order") is not None}

    # 트리거만 추출
    triggers = [
        r for r in chair_results if r["tf_trigger"] and r["agenda_items"]
    ]

    if not triggers:
        log.write(" tf_trigger=True이고 agenda_items가 비어있지 않은 트리거가 없습니다.\n")
        return []

    # speech_order 기준으로 정렬
    triggers.sort(key=lambda x: x["speech_order"])

    def format_agenda_range(items):
        if not items:
            return ""
        items_sorted = sorted(set(items))
        if len(items_sorted) == 1:
            return f"의사일정 제{items_sorted[0]}항"
        # 연속 구간인지 확인
        is_contiguous = all(
            items_sorted[i + 1] == items_sorted[i] + 1
            for i in range(len(items_sorted) - 1)
        )
        if is_contiguous:
            return f"의사일정 제{items_sorted[0]}항부터 제{items_sorted[-1]}항까지"
        # 아니면 개별 나열
        return "의사일정 " + ", ".join(f"제{i}항" for i in items_sorted)

    segments = []
    for i, t in enumerate(triggers):
        start_order = t["speech_order"]
        if i + 1 < len(triggers):
            end_order = triggers[i + 1]["speech_order"] - 1
        else:
            end_order = max_order

        if end_order < start_order:
            # 이상한 경우 방어
            end_order = start_order

        bill_review = build_bill_review(bill_pool, t["agenda_items"], log)
        agenda_range_str = format_agenda_range(t["agenda_items"])

        trigger_speech = by_order_speech.get(start_order, {})
        seg = {
            "delib_order": i + 1,
            "trigger_speech_order": start_order,
            "trigger_speech_id": trigger_speech.get("speech_id"),
            "trigger_member_name": trigger_speech.get("member_name"),
            "start_order": start_order,
            "end_order": end_order,
            "agenda_items": sorted(set(t["agenda_items"])),
            "agenda_range_str": agenda_range_str,
            "bill_review": bill_review,
        }
        segments.append(seg)

    # 로그에 요약
    log.write("\n=== 최종 심사구간(deliberation segments) ===\n\n")
    for seg in segments:
        log.write(
            f"[delib {seg['delib_order']}] "
            f"trigger_speech_order={seg['trigger_speech_order']} "
            f"(speech_id={seg['trigger_speech_id']})\n"
        )
        log.write(
            f"  발언자: {seg['trigger_member_name']}\n"
            f"  구간: speech_order {seg['start_order']} ~ {seg['end_order']}\n"
        )
        log.write(
            f"  심사 의사일정: {seg['agenda_range_str']} "
            f"(raw: {seg['agenda_items']})\n"
        )
        if seg["bill_review"]:
            log.write("  bill_review (bill_pool 매칭 결과):\n")
            for br in seg["bill_review"]:
                log.write(f"    - {br}\n")
        else:
            log.write("  bill_review: [] (LLM 또는 bill_pool 매칭 실패)\n")
        log.write("\n")

    return segments


# =========================================
# 원본 JSON에 필드 부여
# =========================================
def apply_segments_to_speeches(speeches, segments):
    """
    각 발언에 대해:
      - tf_trigger: 이 발언이 트리거 발언인지 여부
      - delib_order: 심사구간 번호 (해당 구간 없으면 None)
      - bill_review: 해당 구간에서 심사되는 법안 목록 (구간 없으면 [])
      - agenda_items: 해당 구간에서 심사되는 의사일정 항 번호 리스트
      - agenda_range_str: 사람이 읽기 쉬운 "의사일정 제X항~제Y항" 문자열
    """

    # speech_order → segment 맵
    order_to_segment = {}
    for seg in segments:
        for so in range(seg["start_order"], seg["end_order"] + 1):
            order_to_segment[so] = seg

    new_speeches = []
    for s in speeches:
        so = s.get("speech_order")
        seg = order_to_segment.get(so)

        # 기본값
        tf_trigger = False
        delib_order = None
        bill_review = []
        agenda_items = []
        agenda_range_str = None

        if seg:
            delib_order = seg["delib_order"]
            bill_review = seg["bill_review"]
            agenda_items = seg["agenda_items"]
            agenda_range_str = seg.get("agenda_range_str")
            # 트리거 발언 여부: 이 구간의 trigger_speech_order와 같고, 소위원장인 경우
            if (
                so == seg["trigger_speech_order"]
                and "소위원장" in (s.get("member_name") or "")
            ):
                tf_trigger = True

        s_new = dict(s)
        s_new["tf_trigger"] = tf_trigger
        s_new["delib_order"] = delib_order
        s_new["bill_review"] = bill_review
        s_new["agenda_items"] = agenda_items
        s_new["agenda_range_str"] = agenda_range_str
        new_speeches.append(s_new)

    return new_speeches


# =========================================
# main
# =========================================
def main():
    # sys.argv[1]로 meeting_id 받기
    if len(sys.argv) > 1:
        meeting_id = int(sys.argv[1])
    else:
        meeting_id = MEETING_ID  # 기본값(기존 사용 방식)

    # 추가 인수: 출력파일 경로
    if len(sys.argv) > 2:
        manual_output = sys.argv[2]
    else:
        manual_output = None

    # ====== meeting_split_all에서 해당 meeting_id JSON 파일 자동 검색 ======
    search_dir = "C:/pythonproject/k_legisight/model_prep/meeting_split_all"
    pattern = os.path.join(search_dir, f"**/*{meeting_id}.json")
    matches = glob.glob(pattern, recursive=True)

    if not matches:
        print(f"입력 JSON을 찾을 수 없습니다: meeting_id={meeting_id}")
        return

    input_file = matches[0]
    print(f"입력 파일 자동 감지됨: {input_file}")
    # ===============================================================

    # 출력 폴더 설정
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "trigger_deliber_output")
    os.makedirs(output_dir, exist_ok=True)

    # 기본 출력 파일 경로
    if manual_output:
        output_file = manual_output
    else:
        output_file = os.path.join(output_dir, f"speeches_triggerdeliber_{meeting_id}.json")

    log_file = os.path.join(output_dir, f"trigger_deliber_{meeting_id}.log")

    # 입력 로드
    with open(input_file, "r", encoding="utf-8") as f:
        speeches = json.load(f)

    print(f"입력 파일 로드 완료: {input_file}")
    print(f"총 발언 수: {len(speeches)}")

    with open(log_file, "w", encoding="utf-8") as log:
        log.write(
            f"=== Trigger Deliber Log (meeting_id={meeting_id}) {datetime.now()} ===\n\n"
        )
        log.write(f"총 발언 수: {len(speeches)}\n")
        
        # bill_pool 생성
        bill_pool = build_bill_pool_from_all(speeches)
        log.write(f"bill_pool 크기(의사일정 항 개수): {len(bill_pool)}\n\n")
        print(f" bill_pool 생성 완료 (의사일정 항 개수: {len(bill_pool)})")
        bill_pool_txt = os.path.join(output_dir, f"bill_pool_{meeting_id}.txt")
        with open(bill_pool_txt, "w", encoding="utf-8") as bf:
            bf.write("=== bill_pool (의사일정 전체 목록) ===\n\n")
            for idx in sorted(bill_pool.keys()):
                bf.write(f"{bill_pool[idx]['raw']}\n")

        print(f" bill_pool TXT 저장 완료 → {bill_pool_txt}")
        log.write(f"bill_pool 텍스트 저장: {bill_pool_txt}\n\n")

        if not bill_pool:
            log.write(" bill_pool이 비어 있습니다. 종료.\n")
            print(" bill_pool 비어 있음. 로그 확인 후 입력 데이터를 점검하세요.")
            return

        # 소위원장 발언 추출
        chair_speeches = [
            s for s in speeches if "소위원장" in (s.get("member_name") or "")
        ]
        log.write(f"소위원장 발언 수(전체): {len(chair_speeches)}\n")
        print(f" 소위원장 발언 추출 완료: {len(chair_speeches)}개")

        if not chair_speeches:
            log.write(" 소위원장 발언이 없습니다. 종료.\n")
            print(" 소위원장 발언이 없습니다. member_name 필드를 다시 확인해 주세요.")
            return

        # ✅ 전처리: 키워드 기반 트리거 후보 소위원장 발언만 추리기
        chair_trigger_candidates = [
            s for s in chair_speeches
            if is_trigger_candidate(s.get("speech_text", ""))
        ]

        log.write(f"소위원장 트리거 후보 발언 수(키워드 필터): {len(chair_trigger_candidates)}\n\n")
        print(f" 소위원장 트리거 후보 발언 수: {len(chair_trigger_candidates)}개")

        # 후보 발언 TXT로 저장해서 눈으로 확인할 수 있게
        chair_candidate_txt = os.path.join(
            output_dir, f"chair_trigger_candidates_{meeting_id}.txt"
        )
        with open(chair_candidate_txt, "w", encoding="utf-8") as cf:
            cf.write("=== 소위원장 트리거 후보 발언 목록 ===\n\n")
            for s in chair_trigger_candidates:
                cf.write(f"[speech_order={s.get('speech_order')}] {s.get('member_name', '')}\n")
                cf.write((s.get("speech_text") or "").replace("\n", " ") + "\n\n")

        log.write(f"소위원장 트리거 후보 TXT 저장: {chair_candidate_txt}\n\n")
        print(f" 소위원장 트리거 후보 TXT 저장 완료 → {chair_candidate_txt}")

        if not chair_trigger_candidates:
            log.write(" 키워드 기반 소위원장 트리거 후보 발언이 없습니다. 종료.\n")
            print(" 트리거 후보 발언이 없습니다. INCLUDE_KEYWORDS 또는 입력 데이터를 점검하세요.")
            return

        # 프롬프트 구성 및 LLM 호출
        print("▶ LLM 호출 시작 (소위원장 트리거 후보 발언 분석 중)...")
        prompt = build_prompt_for_chair_triggers(chair_trigger_candidates, bill_pool)
        resp = call_llm(prompt)

        # 디버깅용: 응답 길이 출력
        print(f"LLM raw response length: {len(resp) if resp else 0}")

        if not is_valid_llm_response(resp):
            log.write(" LLM 응답이 유효하지 않습니다.\n")
            log.write("=== Raw LLM Response Start ===\n")
            log.write(str(resp) + "\n")
            log.write("=== Raw LLM Response End ===\n")
            print(" LLM 응답이 유효하지 않음. 로그 파일에서 원본 응답을 확인하세요.")
            return

        raw_results = extract_json_array(resp)
        if not raw_results:
            log.write(" JSON 배열 파싱 결과가 비어 있습니다.\n")
            log.write("=== Raw LLM Response (for parsing error) ===\n")
            log.write(str(resp) + "\n")
            print(" LLM 응답에서 JSON 배열을 찾지 못했습니다. 로그의 원문 응답을 확인하고 프롬프트를 점검하세요.")
            return


        print(f" LLM 응답 수신 및 JSON 파싱 완료 (항목 수: {len(raw_results)})")

        # 결과 정규화 ( 이제는 '후보 발언들' 기준으로 정규화)
        chair_results = normalize_chair_results(chair_trigger_candidates, raw_results, log)

        log.write("\n=== 소위원장 트리거 판별 결과 (후보 발언 기준) ===\n\n")
        for r in chair_results:
            so = r["speech_order"]
            tf = r["tf_trigger"]
            items = r["agenda_items"]
            # 로그용 발언 텍스트는 전체 소위원장 발언에서 찾아도 되고, 후보 리스트에서 찾아도 됨
            speech = next((s for s in chair_speeches if s["speech_order"] == so), None)
            text_short = ""
            if speech:
                text_short = (speech.get("speech_text") or "").replace("\n", " ")[:150]
            log.write(f"- speech_order={so}, tf_trigger={tf}, agenda_items={items}\n")
            log.write(f"  발언 요약: {text_short}\n\n")

        # 심사구간 생성
        print(" 소위원장 트리거를 기반으로 심사구간 생성 중...")
        segments = build_segments(speeches, chair_results, bill_pool, log)
        if not segments:
            print(" 트리거/심사구간이 생성되지 않았습니다. 로그를 확인하세요.")
            return

        print(f" 생성된 심사구간 수: {len(segments)}")

        # 원본 JSON에 반영
        print(" 심사구간 정보를 원본 발언에 적용 중...")
        new_speeches = apply_segments_to_speeches(speeches, segments)

    # 결과 저장
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(new_speeches, f, ensure_ascii=False, indent=2)

    print(f" trigger_deliber 처리 완료 → {output_file}")
    print(f" 로그 파일 → {log_file}")


if __name__ == "__main__":
    main()
