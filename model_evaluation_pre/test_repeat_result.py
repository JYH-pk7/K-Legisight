#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_repeat_result.py
------------------------
LLM 기반 trigger_deliber_x.py 결과를 동일 회의록에 대해 N회 반복 수행하고
각 run마다 compare_segments.py로 평가하여 평균 / 분산 / 최고 성능 run 계산
결과를 JSON + TXT 보고서로 저장
실행 커맨드 python test_repeat_result.py --committee (이름) --meeting (번호) --repeat 10 
"""

import sys, os
import json
import subprocess
import argparse
import statistics
import importlib   # ✅ 추가

# ✅ 상위 폴더 import 가능하도록 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_evaluation_pre.compare_segments import compare_meeting


def main():
    parser = argparse.ArgumentParser(description="반복 테스트 및 결과 요약 보고서 생성")
    parser.add_argument("--committee", required=True)
    parser.add_argument("--meeting", type=int, required=True)
    parser.add_argument("--repeat", type=int, default=10)
    args = parser.parse_args()

    committee = args.committee.strip().lower()
    meeting_id = args.meeting
    n_repeat = args.repeat

    print(f"\n🚀 {committee} 위원회 회의({meeting_id}) 반복 테스트 시작 ({n_repeat}회 반복)\n")

    # ✅ 동적으로 정답 세트 import
    try:
        mod = importlib.import_module(f"model_evaluation_pre.answers.answers_{committee}")
        answer_segments = mod.answer_segments
    except ModuleNotFoundError:
        print(f"⚠️ 정답세트 파일을 찾을 수 없습니다: answers_{committee}.py")
        return

    # ✅ 경로 설정
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    trigger_path = os.path.join(base_dir, "preprocess_model", "trigger_deliber_1.py")
    output_dir = os.path.join(base_dir, "preprocess_model", "trigger_deliber_output")

    if not os.path.exists(trigger_path):
        print(f"⚠️ trigger_deliber_1.py 파일을 찾을 수 없습니다: {trigger_path}")
        return

    f1_scores, precisions, recalls = [], [], []

    # ✅ 반복 수행
    for i in range(n_repeat):
        print(f"🔁 [{i+1}/{n_repeat}] trigger_deliber_1.py 실행 중...")
        subprocess.run(["python", trigger_path],
                       cwd=os.path.join(base_dir, "preprocess_model"),
                       check=True)

        print("⚖️  compare_segments 평가 중...")
        gold_segments = answer_segments.get(meeting_id)
        if not gold_segments:
            print(f"⚠️ {committee} 위원회 {meeting_id} 회의의 정답 세트가 없습니다.")
            return

        result = compare_meeting(meeting_id, gold_segments, output_dir=output_dir)
        if result:
            precisions.append(result["precision"])
            recalls.append(result["recall"])
            f1_scores.append(result["f1"])

    # ✅ 통계 계산
    avg_p = sum(precisions) / len(precisions) if precisions else 0
    avg_r = sum(recalls) / len(recalls) if recalls else 0
    avg_f = sum(f1_scores) / len(f1_scores) if f1_scores else 0
    var_f = statistics.variance(f1_scores) if len(f1_scores) > 1 else 0.0
    std_f = statistics.stdev(f1_scores) if len(f1_scores) > 1 else 0.0

    best_score = max(f1_scores) if f1_scores else 0
    best_runs = [i + 1 for i, f in enumerate(f1_scores) if f == best_score]
    best_rate = len(best_runs) / n_repeat if n_repeat > 0 else 0
    fail_rate = sum(f < 0.5 for f in f1_scores) / n_repeat if n_repeat > 0 else 0
    stability = max(0.0, 1 - std_f)  # 1에 가까울수록 안정적

    # ✅ 콘솔 요약 출력
    print("\n📊 반복 테스트 결과 요약")
    print("────────────────────────────")
    print(f"총 반복 횟수     : {n_repeat}")
    print(f"평균 Precision   : {avg_p:.3f}")
    print(f"평균 Recall      : {avg_r:.3f}")
    print(f"평균 F1-score    : {avg_f:.3f}")
    print(f"F1-score 분산    : {var_f:.5f}")
    print(f"표준편차(σ)      : {std_f:.5f}")
    print(f"최고 성능 Run    : {', '.join('#'+str(r) for r in best_runs)} (F1={best_score:.3f})")
    print(f"Best Run 확률    : {best_rate:.2f} ({len(best_runs)}/{n_repeat}회)")
    print(f"Fail Run 비율    : {fail_rate:.2f} (F1<0.5)")
    print(f"모델 안정도(1−σ) : {stability:.2f}")
    print("────────────────────────────\n")

    # ✅ 결과 저장 디렉토리
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    os.makedirs(report_dir, exist_ok=True)

    # ✅ JSON 결과 저장
    json_path = os.path.join(report_dir, f"repeat_result_{committee}_{meeting_id}.json")
    result_data = {
        "committee": committee,
        "meeting_id": meeting_id,
        "repeat": n_repeat,
        "avg_precision": avg_p,
        "avg_recall": avg_r,
        "avg_f1": avg_f,
        "variance_f1": var_f,
        "stdev_f1": std_f,
        "best_f1": best_score,
        "best_runs": best_runs,
        "best_rate": best_rate,
        "fail_rate": fail_rate,
        "stability": stability,
        "f1_scores": f1_scores,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    # ✅ TXT 보고서 저장
    txt_path = os.path.join(report_dir, f"repeat_summary_{committee}_{meeting_id}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"📄 {committee.upper()} 위원회 회의 {meeting_id} 반복 테스트 결과\n")
        f.write("────────────────────────────\n")
        f.write(f"총 반복 횟수     : {n_repeat}\n")
        f.write(f"평균 Precision   : {avg_p:.3f}\n")
        f.write(f"평균 Recall      : {avg_r:.3f}\n")
        f.write(f"평균 F1-score    : {avg_f:.3f}\n")
        f.write(f"F1-score 분산    : {var_f:.5f}\n")
        f.write(f"표준편차(σ)      : {std_f:.5f}\n")
        f.write(f"최고 성능 Run    : {', '.join('#'+str(r) for r in best_runs)} (F1={best_score:.3f})\n")
        f.write(f"Best Run 확률    : {best_rate:.2f} ({len(best_runs)}/{n_repeat}회)\n")
        f.write(f"Fail Run 비율    : {fail_rate:.2f} (F1<0.5)\n")
        f.write(f"모델 안정도(1−σ) : {stability:.2f}\n")
        f.write("────────────────────────────\n\n")

    # ✅ 유사도 기반 보조 평가 지표 (옵션)
        f.write("📈 보조 평가 지표 (참고용)\n")
        f.write("- Best Run 확률이 높을수록 모델이 일관된 패턴을 보임\n")
        f.write("- Fail Run 비율이 높으면 온도나 LLM randomness 조정 필요\n")
        f.write("- 모델 안정도(1−σ)는 1에 가까울수록 결과가 일정함\n")
        f.write("────────────────────────────\n\n")

        f.write("Run별 F1-score:\n")
        for i, f1 in enumerate(f1_scores, 1):
            bar = "█" * int(f1 * 20)
            f.write(f"  Run {i:2d}: {f1:.3f} | {bar}\n")

    print(f"💾 결과 저장 완료 → {json_path}")
    print(f"📝 요약 보고서 저장 → {txt_path}")


if __name__ == "__main__":
    main()