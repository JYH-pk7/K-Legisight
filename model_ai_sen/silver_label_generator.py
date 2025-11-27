# silver_label_generator.py
import openai
import pandas as pd
import os
import time
from dotenv import load_dotenv

# =====================================================
# CONFIG
# =====================================================

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-5.1"

TARGET_COUNTS = {0: 2000, 1: 2000, 2: 2000}  # 비협력 / 협력 / 중립
OUTPUT_FILE = "silver_label_set.csv"


# =====================================================
# BASE PROMPT (few-shot 직접 넣기 + 최소 라벨 정의)
# =====================================================

BASE_PROMPT = """
당신은 한국 국회의원의 발언을 모방해 전문적으로 작성하는 전문가입니다.
아래 규칙에 따라 발언(speech_text), 라벨(label), reason을 생성하십시오.

[라벨 정의]
0 = 비협력 : 법안에 대해 부정적·우려·반대·처리에 대한 어려움 표현
1 = 협력   : 법안에 대해 긍정적·찬성·이견 없음·원안 처리 가능 표현
2 = 중립   : 정보 전달·사실 설명·입장 보류, 법안에 대한 찬반이 드러나지 않음

[발언 규칙]
- 길이: 50~600자
- 문체: 국회 소위원회 회의록에서 국회의원의 공식 말투
- 출력은 아래 3줄만 생성:
  speech_text: <내용>
  label: <0/1/2>
  reason: <한 문장, 20단어 이하>

-------------------------------------------------------
### FEW-SHOT EXAMPLES
-------------------------------------------------------

speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---
speech_text: ""
label: 
reason: 
---



-------------------------------------------------------
이제 아래 라벨에 맞는 발언 1개를 생성하라:
라벨: {TARGET_LABEL}
-------------------------------------------------------
"""


# =====================================================
# GPT CALL
# =====================================================

def generate_sample(target_label):
    prompt = BASE_PROMPT.replace("{TARGET_LABEL}", str(target_label))

    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        extra_headers={"X-Enable-Caching": "true"}  # 비용 절감
    )

    return response["choices"][0]["message"]["content"]


# =====================================================
# PARSE
# =====================================================

def parse_output(text):
    speech = label = reason = None

    for line in text.splitlines():
        clean = line.strip()

        if clean.lower().startswith("speech:"):
            speech = clean.split(":", 1)[1].strip()

        elif clean.lower().startswith("label:"):
            try:
                label = int(clean.split(":", 1)[1].strip())
            except:
                label = None

        elif clean.lower().startswith("reason:"):
            reason = clean.split(":", 1)[1].strip()

    return speech, label, reason


# =====================================================
# MAIN LOOP
# =====================================================

def generate_dataset():
    data = []

    for label in [0, 1, 2]:
        print(f"\n=== 라벨 {label} 생성 시작 ===")
        created = 0

        while created < TARGET_COUNTS[label]:

            raw = generate_sample(label)
            speech, parsed_label, reason = parse_output(raw)

            # 검증
            if None in [speech, parsed_label, reason]:
                print("⚠ 파싱 실패 → 재시도")
                continue

            if parsed_label != label:
                print("⚠ 라벨 불일치 → 재시도")
                continue

            if not (50 <= len(speech) <= 300):
                print("⚠ 길이 조건 불만족 → 재시도")
                continue

            # 저장
            data.append({
                "speech_text": speech,
                "reason": reason,
                "label": parsed_label
            })

            created += 1
            if created % 50 == 0:
                print(f"  ✔ {created}/{TARGET_COUNTS[label]} 완료")

            time.sleep(0.05)

    pd.DataFrame(data).to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n🎉 Silver 9000개 생성 완료 → {OUTPUT_FILE}")


# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":
    generate_dataset()
