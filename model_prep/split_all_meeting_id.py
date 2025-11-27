import os
import subprocess
from pathlib import Path

# 실행할 스크립트 경로 (현재 폴더 기준)
SCRIPT_PATH = Path(__file__).parent / "split_meeting_id.py"

# 입력 JSON 파일들이 있는 디렉토리
INPUT_DIR = Path("C:/pythonproject/k_legisight/model_prep/committee_output")

# 결과 출력 폴더 (자동 생성됨)
OUTPUT_BASE = Path("C:/pythonproject/k_legisight/model_prep/meeting_split_all")

def main():
    if not SCRIPT_PATH.exists():
        print(f"❌ 실행 스크립트가 존재하지 않습니다: {SCRIPT_PATH}")
        return

    # 출력 폴더 생성
    OUTPUT_BASE.mkdir(exist_ok=True)

    # "_speeches.json" 파일들 찾기
    json_files = sorted(INPUT_DIR.glob("*_speeches.json"))

    if not json_files:
        print("⚠️ '_speeches.json' 파일을 찾을 수 없습니다.")
        return

    # 각 파일 순회 실행
    for json_file in json_files:
        print(f"\n▶ 실행 중: {json_file.name}")
        output_dir = OUTPUT_BASE / json_file.stem
        output_dir.mkdir(exist_ok=True)

        cmd = [
            "python",
            str(SCRIPT_PATH),
            "--json", str(json_file),
            "--outdir", str(output_dir)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print(f"⚠️ stderr:\n{result.stderr}")
        except Exception as e:
            print(f"❌ {json_file.name} 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
