#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compare_segments.py
--------------------
위원회 이름(committee)을 명령줄 인자로 받아서
실행 커맨드 / python compare_segments.py --committee (예시 Kukbang)
해당 answers_xxx.py 정답세트와 LLM 결과(JSON)를 비교 평가합니다.
Precision / Recall / F1-score 계산 후 콘솔에 요약 출력.
기존 Precision/Recall/F1 외에도
- Jaccard 평균 (부분 일치 기반 유사도)
- Soft-F1 (0.7×Jaccard + 0.3×F1) 통합 점수 표시.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import argparse
import importlib

# --------------------------------------------------------
# 유틸 함수
# --------------------------------------------------------
def jaccard(a, b):
    """agenda_items 리스트 간 Jaccard 유사도"""
    a, b = set(a or []), set(b or [])
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


# --------------------------------------------------------
# 한 회의(meeting_id) 단위 비교
# --------------------------------------------------------
def compare_meeting(meeting_id: int, gold_segments: list, output_dir=None):
    if output_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, "preprocess_model", "trigger_deliber_output")
    path = os.path.join(output_dir, f"speeches_triggerdeliber_{meeting_id}.json")
    if not os.path.exists(path):
        print(f"⚠️ 결과 파일 없음: {path}")
        return None

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # delib_order별 예측/정답 추출
    preds = {s["delib_order"]: s["agenda_items"] for s in data if s.get("delib_order")}
    golds = {g["delib_order"]: g["agenda_items"] for g in gold_segments}

    # 완전일치 기반 F1 계산
    tp = sum(1 for k in golds if k in preds and preds[k] == golds[k])
    precision = tp / len(preds) if preds else 0
    recall = tp / len(golds) if golds else 0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0

    # 부분일치 기반 Jaccard 평균 계산
    jaccard_scores = []
    for k in golds:
        if k in preds:
            jaccard_scores.append(jaccard(preds[k], golds[k]))
        else:
            jaccard_scores.append(0.0)
    avg_j = sum(jaccard_scores) / len(jaccard_scores) if jaccard_scores else 0

    # Soft-F1 계산 (절충형)
    soft_f1 = 0.7 * avg_j + 0.3 * f1

    print(f"[회의 {meeting_id}] Precision={precision:.2f}, Recall={recall:.2f}, "
          f"F1={f1:.2f}, Jaccard={avg_j:.2f}, Soft-F1={soft_f1:.2f}")

    return {
        "meeting_id": meeting_id,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "jaccard": avg_j,
        "soft_f1": soft_f1
    }


# --------------------------------------------------------
# 메인
# --------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="LLM 분할 결과 vs 정답 세트 비교 (Soft-F1 포함)")
    parser.add_argument("--committee", required=True, help="위원회 이름 (예: kukbang, jungmu, bokji 등)")
    args = parser.parse_args()

    committee = args.committee.strip().lower()

    try:
        mod = importlib.import_module(f"model_evaluation_pre.answers.answers_{committee}")
        answer_segments = mod.answer_segments
    except ModuleNotFoundError:
        print(f"⚠️ 정답세트 파일을 찾을 수 없습니다: answers_{committee}.py")
        return

    results = []
    for meeting_id, gold_segments in answer_segments.items():
        r = compare_meeting(meeting_id, gold_segments)
        if r:
            results.append(r)

    if results:
        p_avg = sum(r["precision"] for r in results) / len(results)
        r_avg = sum(r["recall"] for r in results) / len(results)
        f_avg = sum(r["f1"] for r in results) / len(results)
        j_avg = sum(r["jaccard"] for r in results) / len(results)
        sf_avg = sum(r["soft_f1"] for r in results) / len(results)

        print("\n📊 위원회 전체 평균")
        print("────────────────────────────")
        print(f"Precision 평균 : {p_avg:.3f}")
        print(f"Recall 평균    : {r_avg:.3f}")
        print(f"F1 평균        : {f_avg:.3f}")
        print(f"Jaccard 평균   : {j_avg:.3f}")
        print(f"Soft-F1 평균   : {sf_avg:.3f}")
        print("────────────────────────────\n")

    else:
        print("⚠️ 비교 가능한 회의 결과가 없습니다.")


if __name__ == "__main__":
    main()