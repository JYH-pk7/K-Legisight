#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
xlsx_to_json_2020년모두제외.py로 만든 JSON(발언 리스트)을 읽어서
1) meeting_id 별로 나누어 개별 파일로 저장
2) 단, "bills"에 "예산안"과 "결산" 두 키워드가 모두 등장하는
   발언이 하나라도 있으면 그 meeting_id 전체를 제외

사용법:
(macOS)
python /Users/mac/vscode/K-Legisight/preprocess_model/02_split_by_meeting_id_exclude_budget.py --json "/Users/mac/vscode/K-Legisight/preprocess_model/output/2020년제외_제21대 국회 소위원회 과학기술정보방송통신위원회 회의록 데이터셋_speeches.json" --outdir /Users/mac/vscode/K-Legisight/preprocess_model/과학기술정보방송통신위원회_meetings_speeches
(windosw)

출력 파일명 예시:
./out_meetings_speeches/2020년제외_제21대 국회 소위원회 과학기술정보방송통신위원회 회의록 데이터셋_speeches_meeting_50756.json
※ "개의"가 bills에 들어 있는 것은 허용 (별도 필터 X)
"""

import json
import argparse
import os
from collections import defaultdict


def load_speeches(json_path):
    """JSON 파일을 읽어서 발언 리스트(list[dict])로 반환."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # data가 바로 리스트 형태라고 가정
    if isinstance(data, list):
        return data

    # 혹시 {"speeches": [...]} 형태일 수도 있으니 방어 코드
    if isinstance(data, dict):
        if "speeches" in data and isinstance(data["speeches"], list):
            return data["speeches"]

    raise ValueError("지원하지 않는 JSON 구조입니다. 리스트 또는 {'speeches': [...]} 형태여야 합니다.")


def group_by_meeting(speeches):
    """meeting_id 기준으로 발언들을 묶어서 dict[meeting_id] = [speeches...] 형태로 반환."""
    grouped = defaultdict(list)
    for sp in speeches:
        meeting_id = sp.get("meeting_id")
        if meeting_id is None:
            # meeting_id 없는 데이터는 스킵
            continue
        grouped[meeting_id].append(sp)
    return grouped


def should_exclude_meeting(speeches_for_meeting):
    """
    하나의 meeting(=같은 meeting_id에 속한 발언들)에 대해
    bills에 "예산안"과 "결산"이 모두 포함된 발언이 있는지 검사.
    있으면 True(=제외), 없으면 False(=포함).
    """
    for sp in speeches_for_meeting:
        bills = sp.get("bills") or ""
        if not isinstance(bills, str):
            continue

        # "예산안"과 "결산" 둘 다 등장하면 제외
        if "예산안" in bills or "결산" in bills:
            return True

    return False


def save_grouped_meetings(grouped, out_dir, base_name):
    """
    meeting_id별로 JSON 파일 저장.
    제외 조건을 만족하는 meeting_id는 저장하지 않음.
    파일 이름 예시: {base_name}_meeting_50756.json
    """
    os.makedirs(out_dir, exist_ok=True)

    excluded_meetings = []
    saved_count = 0

    for meeting_id, speeches in grouped.items():
        if should_exclude_meeting(speeches):
            excluded_meetings.append(meeting_id)
            continue

        out_path = os.path.join(out_dir, f"{base_name}_meeting_{meeting_id}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(speeches, f, ensure_ascii=False, indent=2)

        saved_count += 1

    return saved_count, excluded_meetings


def main():
    parser = argparse.ArgumentParser(
        description="xlsx_to_json_2020년모두제외.py 결과 JSON을 meeting_id별로 분리 저장 (예산안/결산 회의 제외)"
    )
    parser.add_argument(
        "--json",
        required=True,
        help="입력 JSON 파일 경로 (xlsx_to_json_2020년모두제외.py로 생성한 speeches JSON)",
    )
    # --outdir의 기본값을 입력 JSON 파일명 기반으로 설정
    # 먼저 --json만 미리 파싱해서 basename을 얻은 뒤 outdir 인자를 추가
    parsed_partial, _ = parser.parse_known_args()
    json_basename = os.path.splitext(os.path.basename(parsed_partial.json))[0]
    default_outdir = f"{json_basename}_meetings"

    parser.add_argument(
        "--outdir",
        default=default_outdir,
        help=f"meeting_id별 JSON을 저장할 출력 디렉토리 (기본: {default_outdir})",
    )

    args = parser.parse_args()

    # 1. 전체 발언 로드
    speeches = load_speeches(args.json)

    # 2. meeting_id별로 그룹화
    grouped = group_by_meeting(speeches)

    # 3. 조건에 따라 저장 + 제외
    base_name = os.path.splitext(os.path.basename(args.json))[0]
    saved_count, excluded_meetings = save_grouped_meetings(grouped, args.outdir, base_name)

    print(f"[완료] 저장된 meeting 파일 개수: {saved_count}")
    if excluded_meetings:
        print("예산안 & 결산 키워드 때문에 제외된 meeting_id 목록:")
        for mid in sorted(excluded_meetings):
            print("  ", mid)
    else:
        print("제외된 meeting_id 없음.")


if __name__ == "__main__":
    main()
