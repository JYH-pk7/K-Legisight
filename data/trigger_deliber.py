#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
trigger_deliber.py
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
- 입력:  ./out/speeches_meeting_<MEETING_ID>.json
- 출력:  ./division_out/speeches_triggerdeliber_<MEETING_ID>.json
- 로그:  ./logs/trigger_deliber_<MEETING_ID>.log
"""

import os
import re
import json
import requests
from datetime import datetime

# =========================================
# 설정
# =========================================
OLLAMA_API = "http://localhost:11434/api/generate"
MODEL = "gpt-oss:120b-cloud"
TEMPERATURE = 0.1
TIMEOUT = 300

MEETING_ID = 50825  # 회의 번호만 바꿔가며 사용


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
        return f"⚠️ LLM 호출 오류: {type(e).__name__}: {e}"


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
        print("⚠️ JSON 파싱 오류:", e)
        # 실패하면 빈 리스트 반환
        return []


def is_valid_llm_response(resp: str) -> bool:
    """LLM 응답이 사용 가능한지 간단히 검사."""
    if not resp:
        return False
    if "⚠️" in resp:  # 우리가 만든 에러 문자열
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
소위원장 발언만 보고, 각 발언이 새로운 안건 심사/의결을 시작하는
'트리거 발언'인지 판단하고, 실제로 지금부터 다루게 되는
의사일정 항 번호들을 찾아야 한다.

====================
[해야 할 일]

각 소위원장 발언에 대해 다음을 판단하라.

1) tf_trigger (true/false)
   - 이 발언에서 새로운 안건의 심사/의결을 시작하면 true
   - 단순 진행 멘트, 회의 마무리, 인사만 하면 false

2) agenda_items (정수 배열)
   - 이 발언에서 **지금부터 또는 다음으로** 심사/의결/계속심사/추후심사 하겠다고
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

1) 범위 / 열거 / 단일 항 모두 인식
   - "제4항부터 제7항까지" → [4, 5, 6, 7]
   - "제8항, 제9항, 제11항" → [8, 9, 11]
   - "제30항" → [30]
   - "의사일정 제5항, 6항, 7항" → [5, 6, 7]

2) 상정만 한 구간은 제외
   - "의사일정 제1항부터 제47항까지 상정합니다"처럼
     **상정**만 하는 구간은 agenda_items에 넣지 않는다.
   - 같은 발언 안에서 바로 이어서
     "의사일정 제1항부터 제3항까지를 심사하도록 하겠습니다"라고 하면
     → agenda_items에는 [1, 2, 3]만 넣는다.

3) 소위원회로 넘기는 계속심사는 제외
   - "의사일정 제40항부터 제47항까지는 소위원회에서 계속 심사하도록 하겠습니다"
     는 이 회의가 아닌 소위원회로 넘기는 것이므로
     → [40, 41, …, 47]은 agenda_items에 넣지 않는다.
   - 같은 발언 안에서 이어서
     "의사일정 제4항 … 에 대해서 보고해 주시기 바랍니다"
     또는 "심사하도록 하겠습니다"라고 하면
     → 이 발언은 트리거(tf_trigger=true)이고, agenda_items = [4]가 된다.
     (실제 예시는 아래 예시 6 참조)

4) 이미 끝난 안건을 정리 의결하는 부분 vs 새로 시작하는 안건 구분
   - 한 발언 안에서,
     앞부분은 "…은 원안대로 의결하고자 하는데, 가결되었음을 선포합니다"처럼
     이미 심사해 둔 안건을 의결/선포만 하고,
     뒷부분에서 "다음은 의사일정 제5항부터 제7항까지 … 심사하도록 하겠습니다"
     처럼 **새로운 심사 구간**을 여는 경우가 있다.
   - 이때 이 발언의 agenda_items에는
     **뒷부분에서 '다음은/그러면 … 심사하도록 하겠습니다'라고 선언한 구간만**
     넣는다.

   - 또한 "… 제1․2․3항을 다시 심사하도록 하겠습니다"처럼
     **'다시 심사' / '재심사'를 선언하는 경우도 새로운 심사 구간으로 보고**,
     그 숫자들만 agenda_items에 넣는다.

5) 이미 심사 끝난 구간 vs 이제부터 심사할 구간
   - "의사일정 제1항부터 제3항까지는 이미 심사를 마쳤고,
      다음으로 제4항부터 제7항까지 … 심사하도록 하겠습니다."
     → agenda_items = [4, 5, 6, 7]

6) 한 발언에서 여러 심사/의결 구간을 동시에 시작하면 모두 포함
   - 예: "의사일정 제11항과 제16항을 일괄하여 심사하도록 하겠습니다."
     → agenda_items = [11, 16]

7) 이전 발언의 내용을 추론해서 항 번호를 추가하지 말 것
   - 이 발언 안에 **숫자로 등장하지 않은** 의사일정 항 번호는 절대 넣지 않는다.

====================
[예시]

예시 1)
발언:
"의사일정 제1항부터 제3항까지 이상 3건의 서민의 금융생활 지원에 관한 법률 일부개정법률안을 일괄하여 심사하도록 하겠습니다."

→ 출력:
{{
  "speech_order": 25,
  "tf_trigger": true,
  "agenda_items": [1, 2, 3]
}}

예시 2)
발언:
"의사일정 제8항, 9항, 10항, 11항 그리고 제30항, 이상 5건의 자본시장과 금융투자업에 관한 법률 일부개정법률안은
각각 본회의에 부의하지 아니하고 지금까지 심사한 결과를 반영하여 이를 통합 조정한 우리 위원회의 대안을 마련하여
전체회의에 보고하고자 하는데 이의 없으십니까?"

→ 출력:
{{
  "speech_order": 300,
  "tf_trigger": true,
  "agenda_items": [8, 9, 10, 11, 30]
}}

예시 3)
발언:
"의사일정 제5항 예금자보호법 일부개정법률안을 심사하도록 하겠습니다."

→ 출력:
{{
  "speech_order": 310,
  "tf_trigger": true,
  "agenda_items": [5]
}}

예시 4)
발언:
"의사일정 제1항부터 제3항까지는 이미 심사를 마쳤고,
다음으로 제4항부터 제7항까지 이상 4건의 법률안을 일괄하여 심사하도록 하겠습니다."

→ 출력:
{{
  "speech_order": 400,
  "tf_trigger": true,
  "agenda_items": [4, 5, 6, 7]
}}

예시 5) (상정만 한 뒤, 실제 심사 구간은 따로 지정)
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

예시 6) (소위원회 계속심사 + 본회의 심사 시작, 299번 패턴)
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

예시 7) (여러 의결 후, 다음 심사 구간 시작, 345번 패턴 단순화)
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

예시 8) (여러 의결 후, 1·2·3항 재심사 시작 – 624 패턴)
발언:
"… 의사일정 제8항, 9항, 10항, 11항, 30항은 각각 가결되었음을 선포합니다.
그리고 오전에 논의했던 제1․2․3항을 다시 심사하도록 하겠습니다."

→ 출력:
{{
  "speech_order": 624,
  "tf_trigger": true,
  "agenda_items": [1, 2, 3]
}}


예시 9) (트리거가 아닌 경우)
발언:
"회의를 준비해 주신 관계자 여러분께 감사드립니다. 산회를 선포합니다."

→ 출력:
{{
  "speech_order": 350,
  "tf_trigger": false,
  "agenda_items": []
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
                f"⚠️ LLM 결과에 없는 소위원장 발언 speech_order={so} → 기본값(tf_trigger=False)으로 처리\n"
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
            log.write(f"⚠️ bill_pool에 없는 의사일정 항 번호: {idx}\n")
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
        log.write("⚠️ tf_trigger=True이고 agenda_items가 비어있지 않은 트리거가 없습니다.\n")
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
    meeting_id = MEETING_ID

    input_file = f"./out/speeches_meeting_{meeting_id}.json"
    output_file = f"./division_out/speeches_triggerdeliber_{meeting_id}.json"
    log_file = f"./logs/trigger_deliber_{meeting_id}.log"

    os.makedirs("./logs", exist_ok=True)
    os.makedirs("./division_out", exist_ok=True)

    with open(input_file, "r", encoding="utf-8") as f:
        speeches = json.load(f)

    print(f"📥 입력 파일 로드 완료: {input_file}")
    print(f"총 발언 수: {len(speeches)}")

    with open(log_file, "w", encoding="utf-8") as log:
        log.write(
            f"=== Trigger Deliber Log (meeting_id={meeting_id}) {datetime.now()} ===\n\n"
        )
        log.write(f"총 발언 수: {len(speeches)}\n")

        # bill_pool 생성
        bill_pool = build_bill_pool_from_all(speeches)
        log.write(f"bill_pool 크기(의사일정 항 개수): {len(bill_pool)}\n\n")
        print(f"📚 bill_pool 생성 완료 (의사일정 항 개수: {len(bill_pool)})")

        if not bill_pool:
            log.write("⚠️ bill_pool이 비어 있습니다. 종료.\n")
            print("⚠️ bill_pool 비어 있음. 로그 확인 후 입력 데이터를 점검하세요.")
            return

        # 소위원장 발언 추출
        chair_speeches = [
            s for s in speeches if "소위원장" in (s.get("member_name") or "")
        ]
        log.write(f"소위원장 발언 수: {len(chair_speeches)}\n\n")
        print(f"🧑‍⚖️ 소위원장 발언 추출 완료: {len(chair_speeches)}개")

        if not chair_speeches:
            log.write("⚠️ 소위원장 발언이 없습니다. 종료.\n")
            print("⚠️ 소위원장 발언이 없습니다. member_name 필드를 다시 확인해 주세요.")
            return

        # 프롬프트 구성 및 LLM 호출
        print("▶ LLM 호출 시작 (소위원장 발언 분석 중)...")
        prompt = build_prompt_for_chair_triggers(chair_speeches, bill_pool)
        resp = call_llm(prompt)

        # 디버깅용: 응답 길이 출력
        print(f"LLM raw response length: {len(resp) if resp else 0}")

        if not is_valid_llm_response(resp):
            log.write("⚠️ LLM 응답이 유효하지 않습니다.\n")
            log.write("=== Raw LLM Response Start ===\n")
            log.write(str(resp) + "\n")
            log.write("=== Raw LLM Response End ===\n")
            print("⚠️ LLM 응답이 유효하지 않음. 로그 파일에서 원본 응답을 확인하세요.")
            return

        raw_results = extract_json_array(resp)
        if not raw_results:
            log.write("⚠️ JSON 배열 파싱 결과가 비어 있습니다.\n")
            log.write("=== Raw LLM Response (for parsing error) ===\n")
            log.write(str(resp) + "\n")
            print("⚠️ LLM 응답에서 JSON 배열을 찾지 못했습니다. 로그의 원문 응답을 확인하고 프롬프트를 점검하세요.")
            return


        print(f"✅ LLM 응답 수신 및 JSON 파싱 완료 (항목 수: {len(raw_results)})")

        # 결과 정규화
        chair_results = normalize_chair_results(chair_speeches, raw_results, log)

        log.write("\n=== 소위원장 트리거 판별 결과 ===\n\n")
        for r in chair_results:
            so = r["speech_order"]
            tf = r["tf_trigger"]
            items = r["agenda_items"]
            speech = next((s for s in chair_speeches if s["speech_order"] == so), None)
            text_short = ""
            if speech:
                text_short = (speech.get("speech_text") or "").replace("\n", " ")[:150]
            log.write(f"- speech_order={so}, tf_trigger={tf}, agenda_items={items}\n")
            log.write(f"  발언 요약: {text_short}\n\n")

        # 심사구간 생성
        print("🧩 소위원장 트리거를 기반으로 심사구간 생성 중...")
        segments = build_segments(speeches, chair_results, bill_pool, log)
        if not segments:
            print("⚠️ 트리거/심사구간이 생성되지 않았습니다. 로그를 확인하세요.")
            return

        print(f"🎯 생성된 심사구간 수: {len(segments)}")

        # 원본 JSON에 반영
        print("📌 심사구간 정보를 원본 발언에 적용 중...")
        new_speeches = apply_segments_to_speeches(speeches, segments)

    # 결과 저장
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(new_speeches, f, ensure_ascii=False, indent=2)

    print(f"✅ trigger_deliber 처리 완료 → {output_file}")
    print(f"🪵 로그 파일 → {log_file}")


if __name__ == "__main__":
    main()
