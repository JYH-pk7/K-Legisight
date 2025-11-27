#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
run_failed_stable_trigger.py
---------------------------------------------
all_trigger_deliber_x 의 최종 실패 회의만
trigger_deliber_x.py를 다시 10회 반복 실행하여
signature 안정화(majority vote ≥ 3)를 시도하는 스크립트.

출력:
- trigger_results_failed/         ← 안정화된 성공 결과 저장
- trigger_logs_failed/            ← 회의별 실행 로그
- trigger_summary_failed/         ← 요약 정보
"""

import os
import json
import subprocess
from hashlib import md5
from collections import defaultdict

# ===========================
# 실행 설정
# ===========================
PYTHON = "python"
TARGET_SCRIPT = "trigger_deliber_x.py"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "trigger_deliber_failed_temp")
RESULT_DIR = os.path.join(BASE_DIR, "trigger_results_failed")
LOG_DIR = os.path.join(BASE_DIR, "trigger_logs_failed")
SUMMARY_DIR = os.path.join(BASE_DIR, "trigger_summary_failed")

for d in [TEMP_DIR, RESULT_DIR, LOG_DIR, SUMMARY_DIR]:
    os.makedirs(d, exist_ok=True)

MAX_RUNS = 15
MAJ_THRESHOLD = 3

# ===========================
# 실패 회의 ID 목록
# ===========================
FAILED = [
    50967, 51069, 51104, 51154, 51197,
    51512, 51578, 51598, 51616, 51640,
    51670, 51700, 51746, 51758, 51815,
    51818, 51830, 51929, 52056, 52463,
    52529, 52940, 52942, 52947, 52982,
    53121, 53215
]

# ===========================
# signature 생성 함수
# ===========================
def extract_signature(path_json):
    try:
        with open(path_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        return None

    segments = {}
    for sp in data:
        d = sp.get("delib_order")
        if d is None:
            continue
        if d not in segments:
            segments[d] = {
                "agenda_items": sp.get("agenda_items") or [],
                "agenda_range_str": sp.get("agenda_range_str") or None,
            }

    canonical = json.dumps(segments, ensure_ascii=False, sort_keys=True)
    return md5(canonical.encode("utf-8")).hexdigest()

# ===========================
# Summary 작성
# ===========================
def write_summary(meeting_id, run_records, counts, final_sig, final_path):
    out = os.path.join(SUMMARY_DIR, f"summary_failed_{meeting_id}.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"=== FAILED 회의 안정화 Summary (meeting={meeting_id}) ===\n\n")
        f.write("[Run Signatures]\n")
        for i, sig in enumerate(run_records,1):
            f.write(f"  Run {i}: {sig[:12]}...\n")
        f.write("\n[Signature Counts]\n")
        for sig, cnt in counts.items():
            f.write(f"  {sig[:12]}... : {cnt}회\n")
        f.write("\nFinal Signature : " + final_sig[:12] + "...\n")
        f.write("Final Result File : " + final_path + "\n")

    print(f"✔ Summary 저장 완료: {out}")

# ===========================
# MAIN
# ===========================
def main():
    print("\n=====================================")
    print(" 최종 실패 회의 10회 안정화 실행 시작")
    print("=====================================\n")

    success_list = []
    fail_list = []

    for mid in FAILED:
        print(f"\n--------------------------------------")
        print(f" 회의 {mid} 안정화 실행")
        print("--------------------------------------")

        run_records = []
        counts = defaultdict(int)

        confirmed_sig = None
        confirmed_output = None

        for run_idx in range(1, MAX_RUNS + 1):
            print(f"  → Run {run_idx}/{MAX_RUNS}")

            temp_out = os.path.join(TEMP_DIR, f"{mid}_run{run_idx}.json")
            cmd = [PYTHON, TARGET_SCRIPT, str(mid), temp_out]

            result = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")

            if result.returncode != 0:
                print("    ❌ 실행 오류:", result.stderr[:200])
                continue

            sig = extract_signature(temp_out)
            if not sig:
                print("    ❌ signature 추출 실패")
                continue

            print(f"    signature={sig[:12]}...")
            run_records.append(sig)
            counts[sig] += 1

            # 다수결 안정화 달성
            if counts[sig] >= MAJ_THRESHOLD:
                print("    🎉 안정화 성공!")
                confirmed_sig = sig
                confirmed_output = temp_out
                break

        if confirmed_sig:
            final_path = os.path.join(RESULT_DIR, f"speeches_triggerdeliber_{mid}.json")
            os.replace(confirmed_output, final_path)
            write_summary(mid, run_records, counts, confirmed_sig, final_path)
            success_list.append(mid)
        else:
            print("    ❌ 안정화 실패")
            fail_list.append(mid)

        # temp 파일 정리
        for fn in os.listdir(TEMP_DIR):
            if fn.startswith(f"{mid}_run"):
                os.remove(os.path.join(TEMP_DIR, fn))

    # 전체 요약
    final_out = os.path.join(SUMMARY_DIR, "overall_failed_summary.txt")
    total = len(FAILED)

    with open(final_out, "w", encoding="utf-8") as f:
        f.write("=== FAILED 회의 안정화 전체 요약 ===\n\n")
        f.write(f"총 실패 회의 수     : {total}\n")
        f.write(f"안정화 성공         : {len(success_list)}\n")
        f.write(f"안정화 실패         : {len(fail_list)}\n")
        f.write(f"성공률              : {(len(success_list)/total*100):.2f}%\n\n")
        if fail_list:
            f.write("[안정화 실패 회의]\n")
            for m in fail_list:
                f.write(f"- {m}\n")

    print("\n=====================================")
    print(" 모든 실패 회의 안정화 시도 완료")
    print("=====================================")
    print(f"전체 요약: {final_out}")


if __name__ == "__main__":
    main()
