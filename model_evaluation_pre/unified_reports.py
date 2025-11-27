#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
unified_reports.py
--------------------
evaluation_model/reports 폴더 내의 repeat_result_*.json 파일을 읽어
위원회별 성능을 통합 요약 및 시각화한다.

출력:
 - unified_summary.csv
 - unified_summary.json
 - unified_summary_plot.png  (위원회별 평균 F1-score 시각화)
"""

import os
import json
import csv
import matplotlib.pyplot as plt

# ================================
# 기본 경로 설정
# ================================
BASE_DIR = r"C:\pythonproject\k_legisight\evaluation_model\reports"

# ================================
# JSON 파일 스캔
# ================================
def load_all_results():
    results = []
    for filename in os.listdir(BASE_DIR):
        if filename.startswith("repeat_result_") and filename.endswith(".json"):
            path = os.path.join(BASE_DIR, filename)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                results.append(data)
    return results


# ================================
# 위원회 단위 요약 생성
# ================================
def build_master_table(results):
    master = []

    for r in results:
        master.append({
            "committee": r.get("committee"),
            "meeting_id": r.get("meeting_id"),
            "avg_precision": r.get("avg_precision"),
            "avg_recall": r.get("avg_recall"),
            "avg_f1": r.get("avg_f1"),
            "stdev_f1": r.get("stdev_f1"),
            "best_f1": r.get("best_f1"),
            "best_runs": r.get("best_runs"),
        })

    # 🔥 F1-score 기준 내림차순 정렬
    master = sorted(master, key=lambda x: x["avg_f1"], reverse=True)

    return master


# ================================
# CSV 저장
# ================================
def save_csv(master):
    csv_path = os.path.join(BASE_DIR, "unified_summary.csv")

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "committee", "meeting_id",
            "avg_precision", "avg_recall", "avg_f1",
            "stdev_f1", "best_f1", "best_runs"
        ])

        for row in master:
            writer.writerow([
                row["committee"],
                row["meeting_id"],
                f"{row['avg_precision']:.3f}",
                f"{row['avg_recall']:.3f}",
                f"{row['avg_f1']:.3f}",
                f"{row['stdev_f1']:.3f}",
                f"{row['best_f1']:.3f}",
                ", ".join(f"#{r}" for r in row["best_runs"])
            ])

    print(f"📄 unified_summary.csv 생성 완료 → {csv_path}")


# ================================
# JSON 저장
# ================================
def save_json(master):
    json_path = os.path.join(BASE_DIR, "unified_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(master, f, ensure_ascii=False, indent=2)

    print(f"📄 unified_summary.json 생성 완료 → {json_path}")


# ================================
# 시각화 생성 (위원회별 평균 F1-score)
# ================================
def create_plot(master):
    committees = [m["committee"].upper() for m in master]
    f1_scores = [m["avg_f1"] for m in master]

    plt.figure(figsize=(12, 6))
    plt.bar(committees, f1_scores, color="#4C72B0")
    plt.title("Average F1-score by Committee (Sorted)", fontsize=14)
    plt.xlabel("Committee")
    plt.ylabel("Average F1-score")
    plt.xticks(rotation=45, ha="right")
    plt.grid(axis="y", linestyle="--", alpha=0.5)

    plot_path = os.path.join(BASE_DIR, "unified_summary_plot.png")
    plt.tight_layout()
    plt.savefig(plot_path, dpi=300)
    plt.close()

    print(f"📊 시각화 이미지 생성 완료 → {plot_path}")


# ================================
# 실행 메인
# ================================
def main():
    print("📥 결과 파일 스캔 중...")
    results = load_all_results()

    if not results:
        print("⚠️ repeat_result_*.json 파일을 찾을 수 없습니다.")
        return

    print(f"🔍 총 {len(results)}개의 평가 결과 로드 완료")
    print("📊 unified summary 생성 중...")

    master = build_master_table(results)

    save_csv(master)
    save_json(master)
    create_plot(master)

    print("\n✅ Unified Summary 생성 완료!")
    print("   → unified_summary.csv (본 보고서용)")
    print("   → unified_summary.json (분석용)")
    print("   → unified_summary_plot.png (시각화)")


if __name__ == "__main__":
    main()
