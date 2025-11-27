import json
import os

def main():
    input_file = r"C:\pythonproject\k_legisight\model_prep\committee_output\2021년2월부터_제21대 국회 소위원회 과학기술정보방송통신위원회 회의록 데이터셋_speeches.json"
    target_meeting_id = 52894    # ✅ 원하는 meeting_id로 변경

    # ✅ 저장 폴더 지정
    save_dir = r"C:\pythonproject\k_legisight\model_prep\meeting_number_filltered"
    os.makedirs(save_dir, exist_ok=True)  # 폴더 없으면 자동 생성

    # 1. 출력 파일 이름 자동 생성
    file_name = f"speeches_meeting_{target_meeting_id}.json"
    output_file = os.path.join(save_dir, file_name)

    # 2. JSON 파일 읽기
    with open(input_file, "r", encoding="utf-8") as f:
        speeches = json.load(f)

    # 3. meeting_id로 필터링
    filtered = [s for s in speeches if s.get("meeting_id") == target_meeting_id]

    # 4. 결과 저장
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

    print(f"✅ meeting_id={target_meeting_id} 에 해당하는 {len(filtered)}개 항목이 '{output_file}' 파일로 저장되었습니다.")

if __name__ == "__main__":
    main()
