#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
all_trigger_deliber_x.py
------------------------
meeting_split_all 에 있는 모든 회의 JSON을 입력으로 받아
trigger_deliber_x.py 를 반복 실행하여 안정화된 심사구간 결과를 생성.

폴더 구조:
- meeting_split_all/      ← 입력
- trigger_results/        ← 최종 결과 JSON
- trigger_logs/           ← trigger_deliber_x 로그
- trigger_summary/        ← 회의별 요약 & 전체 요약
- trigger_deliber_temp/   ← 임시파일
"""

import os
import json
import subprocess
from hashlib import md5
from collections import defaultdict

PYTHON = "python"
TARGET_SCRIPT = "trigger_deliber_x.py"

# ============================================
# 경로 설정
# ============================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = "C:/pythonproject/k_legisight/model_prep/meeting_split_all"

TEMP_DIR = os.path.join(BASE_DIR, "trigger_deliber_temp")
RESULT_DIR = os.path.join(BASE_DIR, "trigger_results")
LOG_DIR = os.path.join(BASE_DIR, "trigger_logs")
SUMMARY_DIR = os.path.join(BASE_DIR, "trigger_summary")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SUMMARY_DIR, exist_ok=True)

MAX_RUNS = 10
MAJ_THRESHOLD = 3



# ============================================
# 시그니처 생성
# ============================================
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



# ============================================
# 회의 ID 자동 수집
# ============================================
def collect_meeting_ids():
    ids = []
    for root, dirs, files in os.walk(INPUT_DIR):
        for fn in files:
            if fn.startswith("speeches_meeting_") and fn.endswith(".json"):
                mid = fn.replace("speeches_meeting_", "").replace(".json", "")
                if mid.isdigit():
                    ids.append(int(mid))
    ids.sort()
    return ids



# ============================================
# 회의별 요약 파일 저장
# ============================================
def write_summary(meeting_id, run_records, signature_counts, final_sig, final_path):
    summary_path = os.path.join(SUMMARY_DIR, f"allrun_summary_{meeting_id}.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"=== All-run Trigger-Deliber Summary (Meeting: {meeting_id}) ===\n\n")
        f.write(f"[1] 실행 횟수: {len(run_records)}회\n")
        f.write(f"[2] 안정화 기준: majority ≥ {MAJ_THRESHOLD}\n\n")

        f.write("[3] Run별 Signature:\n")
        for idx, sig in enumerate(run_records, start=1):
            f.write(f"  Run {idx}: {sig[:10]}...\n")
        f.write("\n")

        f.write("[4] Signature 등장 횟수:\n")
        for sig, cnt in signature_counts.items():
            f.write(f"  {sig[:10]}... : {cnt}회\n")
        f.write("\n")

        f.write(f"[5] 최종 선택된 Signature: {final_sig[:10]}...\n")
        f.write(f"[6] 최종 결과 파일: {final_path}\n")

    print(f"📝 요약 파일 생성 → {summary_path}")


# ============================================
# MAIN
# ============================================
def main():
    meeting_ids = collect_meeting_ids()
    print(f"🔍 총 {len(meeting_ids)}개 회의 자동 처리 예정\n")

    for mid in meeting_ids:
        print(f"\n================================")
        print(f"▶ 회의 {mid} 처리 시작")
        print(f"================================")

        run_records = []
        signature_counts = defaultdict(int)

        confirmed_sig = None
        confirmed_output = None

        for run_idx in range(1, MAX_RUNS + 1):
            print(f"\n  ➜ [{run_idx}/{MAX_RUNS}] trigger_deliber_x 실행 중...")

            temp_out = os.path.join(TEMP_DIR, f"{mid}_run{run_idx}.json")

            # trigger_deliber_x.py 실행
            cmd = [PYTHON, TARGET_SCRIPT, str(mid), temp_out]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print("  ⚠️ 실행 실패:", result.stderr)
                continue

            sig = extract_signature(temp_out)
            if not sig:
                print("  ⚠️ signature 생성 실패")
                continue

            print(f"  → signature={sig[:10]}...")

            run_records.append(sig)
            signature_counts[sig] += 1

            if signature_counts[sig] >= MAJ_THRESHOLD:
                print(f"\n  🎉 안정화 도달 ({sig[:10]}...)")
                confirmed_sig = sig
                confirmed_output = temp_out
                break

        # 안정화 성공
        if confirmed_sig and confirmed_output:
            final_path = os.path.join(RESULT_DIR, f"speeches_triggerdeliber_{mid}.json")
            os.replace(confirmed_output, final_path)

            write_summary(mid, run_records, signature_counts, confirmed_sig, final_path)

            print(f"  ✅ 회의 {mid} 최종 결과 저장 완료")
        else:
            print(f"  ❌ 회의 {mid} 안정화 실패")

        # 임시파일 삭제
        for fn in os.listdir(TEMP_DIR):
            if fn.startswith(f"{mid}_run"):
                os.remove(os.path.join(TEMP_DIR, fn))


    # ================================================
    # 전체 요약
    # ================================================
    total = len(meeting_ids)
    success = 0
    failed_ids = []

    for mid in meeting_ids:
        if os.path.exists(os.path.join(RESULT_DIR, f"speeches_triggerdeliber_{mid}.json")):
            success += 1
        else:
            failed_ids.append(mid)

    fail = len(failed_ids)

    print("\n=======================")
    print("📊 전체 실행 결과 요약")
    print("=======================")
    print(f"총 회의 수      : {total}")
    print(f"성공(안정화)    : {success}")
    print(f"실패(불안정)    : {fail}")
    print(f"성공률          : {success / total * 100:.2f}%\n")

    summary_path = os.path.join(SUMMARY_DIR, "overall_run_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("=== 전체 Trigger-Deliber 실행 요약 ===\n\n")
        f.write(f"총 회의 수 : {total}\n")
        f.write(f"성공(안정화) : {success}\n")
        f.write(f"실패(불안정) : {fail}\n")
        f.write(f"성공률 : {success / total * 100:.2f}%\n\n")

        if fail > 0:
            f.write("❌ 실패한 meeting_id:\n")
            for mid in failed_ids:
                f.write(f"- {mid}\n")
        else:
            f.write("🎉 모든 회의가 성공적으로 안정화됨!\n")

    print(f"\n📁 전체 요약 파일 저장됨 → {summary_path}")
    print("\n🎯 전체 회의 처리 완료!")


if __name__ == "__main__":
    main()
