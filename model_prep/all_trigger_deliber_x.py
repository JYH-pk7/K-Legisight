#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
all_trigger_deliber_x.py (Clean Stable Version)
-----------------------------------------------
meeting_split_all 내부의 모든 회의를 자동으로 탐색하여
trigger_deliber_x.py 를 반복 실행(기본 10회)하고,
signature majority(>=3) 규칙으로 안정화된 결과를 생성한다.

폴더 구조:
- meeting_split_all/    ← 입력 JSON
- trigger_deliber_temp/ ← 임시파일 저장
- trigger_results/      ← 안정화된 최종 결과
- trigger_logs/         ← 실행 로그
- trigger_summary/      ← 회의별/전체 요약
"""

import os
import re
import json
import subprocess
from hashlib import md5
from collections import defaultdict


# =========================================================
# 경로 / 실행 설정
# =========================================================
PYTHON = "python"
TARGET_SCRIPT = "trigger_deliber_x.py"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "meeting_split_all")

TEMP_DIR = os.path.join(BASE_DIR, "trigger_deliber_temp")
RESULT_DIR = os.path.join(BASE_DIR, "trigger_results")
LOG_DIR = os.path.join(BASE_DIR, "trigger_logs")
SUMMARY_DIR = os.path.join(BASE_DIR, "trigger_summary")

for d in [TEMP_DIR, RESULT_DIR, LOG_DIR, SUMMARY_DIR]:
    os.makedirs(d, exist_ok=True)

MAX_RUNS = 10        # 기본 10회
MAJ_THRESHOLD = 3    # signature majority 임계값
RETRY_RUNS = 5        # 2차 재시도 횟수


# =========================================================
# Signature 생성
# =========================================================
def extract_signature(path_json):
    """결과 JSON에서 delib_order 기반 signature 생성"""
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


# =========================================================
# 회의 ID 자동 수집 (중첩 폴더 포함)
# =========================================================
def collect_meeting_ids():
    ids = []
    for root, dirs, files in os.walk(INPUT_DIR):
        for fn in files:
            if "speeches_meeting_" in fn and fn.endswith(".json"):
                m = re.search(r"speeches_meeting_(\d+)\.json", fn)
                if m:
                    ids.append(int(m.group(1)))
    ids.sort()
    return ids


# =========================================================
# 회의별 Summary 파일 저장
# =========================================================
def write_summary(meeting_id, run_records, signature_counts, final_sig, final_path):
    summary_path = os.path.join(SUMMARY_DIR, f"summary_{meeting_id}.txt")

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"=== Trigger-Deliber Summary (meeting_id={meeting_id}) ===\n\n")
        f.write("[Run Records]\n")
        for i, sig in enumerate(run_records, 1):
            f.write(f"  Run {i}: {sig[:12]}...\n")
        f.write("\n")

        f.write("[Signature Counts]\n")
        for sig, cnt in signature_counts.items():
            f.write(f"  {sig[:12]}... : {cnt}회\n")
        f.write("\n")

        f.write(f"Final Signature  : {final_sig[:12]}...\n")
        f.write(f"Final Result File: {final_path}\n")

    print(f"> 요약 저장 완료 → {summary_path}")


# =========================================================
# MAIN
# =========================================================
def main():
    meeting_ids = collect_meeting_ids()
    print(f"총 {len(meeting_ids)}개 회의 자동처리 시작\n")

    if len(meeting_ids) == 0:
        print("⚠️ meeting_split_all 안에 회의 JSON이 없습니다.")
        return

    success_list = []
    fail_list = []

    # -----------------------------------------------------
    # 1차 반복 실행 (10회)
    # -----------------------------------------------------
    for mid in meeting_ids:
        print(f"\n====================================")
        print(f"[1차] 회의 {mid} 처리 시작")
        print("====================================")

        run_records = []
        signature_counts = defaultdict(int)

        confirmed_sig = None
        confirmed_output = None

        for run_idx in range(1, MAX_RUNS + 1):
            print(f"   - Run {run_idx}/{MAX_RUNS} 실행 중...")

            temp_out = os.path.join(TEMP_DIR, f"{mid}_run{run_idx}.json")
            cmd = [PYTHON, TARGET_SCRIPT, str(mid), temp_out]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print("     실행 오류:", result.stderr[:200])
                continue

            sig = extract_signature(temp_out)
            if not sig:
                print("     signature 생성 실패")
                continue

            print(f"     signature={sig[:12]}...")

            run_records.append(sig)
            signature_counts[sig] += 1

            if signature_counts[sig] >= MAJ_THRESHOLD:
                print("     → 안정화 달성!")
                confirmed_sig = sig
                confirmed_output = temp_out
                break

        if confirmed_sig and confirmed_output:
            final_path = os.path.join(RESULT_DIR, f"speeches_triggerdeliber_{mid}.json")
            os.replace(confirmed_output, final_path)
            write_summary(mid, run_records, signature_counts, confirmed_sig, final_path)
            success_list.append(mid)
        else:
            print(f"❌ 1차 실패: {mid}")
            fail_list.append(mid)

        # temp 정리
        for fn in os.listdir(TEMP_DIR):
            if fn.startswith(f"{mid}_run"):
                os.remove(os.path.join(TEMP_DIR, fn))

    # -----------------------------------------------------
    # 2차 재시도
    # -----------------------------------------------------
    retry_success = []
    retry_fail = []

    if fail_list:
        print("\n==============================")
        print("1차 실패 회의 재시도 진행")
        print("==============================")

    for mid in fail_list:
        print(f"\n--- 재시도: 회의 {mid} ---")

        run_records = []
        signature_counts = defaultdict(int)

        confirmed_sig = None
        confirmed_output = None

        for r in range(1, RETRY_RUNS + 1):
            print(f"   재시도 Run {r}/{RETRY_RUNS}...")

            temp_out = os.path.join(TEMP_DIR, f"{mid}_retry{r}.json")
            cmd = [PYTHON, TARGET_SCRIPT, str(mid), temp_out]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print("   재시도 오류:", result.stderr[:200])
                continue

            sig = extract_signature(temp_out)
            if not sig:
                print("   signature 실패")
                continue

            print(f"   signature={sig[:12]}...")
            run_records.append(sig)
            signature_counts[sig] += 1

            if signature_counts[sig] >= MAJ_THRESHOLD:
                print("   → 재시도 안정화 성공!")
                confirmed_sig = sig
                confirmed_output = temp_out
                break

        if confirmed_sig:
            final_path = os.path.join(RESULT_DIR, f"speeches_triggerdeliber_{mid}.json")
            os.replace(confirmed_output, final_path)
            write_summary(mid, run_records, signature_counts, confirmed_sig, final_path)
            retry_success.append(mid)
        else:
            retry_fail.append(mid)

        # temp 정리
        for fn in os.listdir(TEMP_DIR):
            if fn.startswith(f"{mid}_retry"):
                os.remove(os.path.join(TEMP_DIR, fn))

    # -----------------------------------------------------
    # 전체 요약
    # -----------------------------------------------------
    total = len(meeting_ids)
    final_success = success_list + retry_success
    final_fail = retry_fail

    overall = os.path.join(SUMMARY_DIR, "overall_summary.txt")
    with open(overall, "w", encoding="utf-8") as f:
        f.write("=== 전체 Trigger-Deliber 실행 요약 ===\n\n")
        f.write(f"총 회의 수 : {total}\n")
        f.write(f"1차 성공 : {len(success_list)}\n")
        f.write(f"재시도 성공 : {len(retry_success)}\n")
        f.write(f"최종 성공 : {len(final_success)}\n")
        f.write(f"최종 실패 : {len(final_fail)}\n")
        if total > 0:
            f.write(f"성공률 : {(len(final_success) / total * 100):.2f}%\n\n")

        if final_fail:
            f.write("[최종 실패 회의]\n")
            for m in final_fail:
                f.write(f"- {m}\n")

    print("\n=============================")
    print(" 전체 처리 완료!")
    print("=============================")
    print(f"전체 요약 저장 → {overall}")


if __name__ == "__main__":
    main()
