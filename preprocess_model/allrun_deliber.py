#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
allrun_deliber.py
-----------------
여러 회의를 대상으로 trigger_deliber_1.py를 반복 실행하여
정교 해시 기반으로 안정화된 최종 심사구간 결과를 생성한다.

정책:
- signature = 전체 구간 구조(JSON) md5 해시
- 동일 signature 가 3회(MAJ_THRESHOLD) 이상 나오면 확정
- 최대 MAX_RUNS = 10
"""

import os
import json
import subprocess
from hashlib import md5
from collections import defaultdict

PYTHON = "python"
TARGET_SCRIPT = "trigger_deliber_1.py"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "meeting_number_filltered")
TEMP_DIR = os.path.join(BASE_DIR, "trigger_deliber_temp")
FINAL_DIR = os.path.join(BASE_DIR, "trigger_deliber_output")
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(FINAL_DIR, exist_ok=True)

MAX_RUNS = 10
MAJ_THRESHOLD = 3


# ============================================
# 시그니처 생성 (정교 해시 방식)
# ============================================
def extract_signature(path_json):
    """
    trigger_deliber_1.py 실행 결과 JSON에서
    delib_order별 구간 구조만 추출하여 정렬된 JSON → md5 hash 생성
    """
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

    # segments를 canonical JSON string으로
    canonical = json.dumps(segments, ensure_ascii=False, sort_keys=True)
    return md5(canonical.encode("utf-8")).hexdigest()


# ============================================
# 회의 ID 자동 수집
# ============================================
def collect_meeting_ids():
    ids = []
    for fn in os.listdir(INPUT_DIR):
        if fn.startswith("speeches_meeting_") and fn.endswith(".json"):
            mid = fn.replace("speeches_meeting_", "").replace(".json", "")
            if mid.isdigit():
                ids.append(int(mid))
    ids.sort()
    return ids


# ============================================
# 요약 파일 생성
# ============================================
def write_summary(meeting_id, run_records, signature_counts, final_sig, final_path):
    summary_path = os.path.join(FINAL_DIR, f"allrun_summary_{meeting_id}.txt")
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

        f.write("\n============================================\n")

    print(f"📝 요약 파일 생성 → {summary_path}")


# ============================================
# main
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
            print(f"\n  ➜ [{run_idx}/{MAX_RUNS}] trigger_deliber 실행 중...")

            temp_out = os.path.join(TEMP_DIR, f"{mid}_run{run_idx}.json")

            # trigger_deliber_1.py 실행
            cmd = [PYTHON, TARGET_SCRIPT, str(mid), temp_out]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print("  ⚠️ 실행 실패:", result.stderr)
                continue

            # signature 생성
            sig = extract_signature(temp_out)
            if not sig:
                print("  ⚠️ signature 생성 실패")
                continue

            print(f"  → signature={sig[:10]}...")

            run_records.append(sig)
            signature_counts[sig] += 1

            # 안정화 판정
            if signature_counts[sig] >= MAJ_THRESHOLD:
                print(f"\n  🎉 안정화 도달 ({sig[:10]}...)")
                confirmed_sig = sig
                confirmed_output = temp_out
                break

        # --------------------------
        # 결과 저장
        # --------------------------
        if confirmed_sig and confirmed_output:
            final_path = os.path.join(FINAL_DIR, f"speeches_triggerdeliber_{mid}.json")
            os.replace(confirmed_output, final_path)

            # 요약 파일 생성
            write_summary(mid, run_records, signature_counts, confirmed_sig, final_path)

            print(f"  ✅ 회의 {mid} 최종 결과 저장 완료")
        else:
            print(f"  ❌ 회의 {mid} 안정화 실패 (최대 {MAX_RUNS}회 실행)")

        # temp 정리
        for fn in os.listdir(TEMP_DIR):
            if fn.startswith(f"{mid}_run"):
                os.remove(os.path.join(TEMP_DIR, fn))

    print("\n🎯 전체 회의 처리 완료!")


if __name__ == "__main__":
    main()
