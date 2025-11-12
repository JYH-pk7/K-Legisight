import os
import win32com.client
import win32clipboard
import time

# ✅ 1. 입력 & 출력 폴더 설정
input_folder = r"data/hwp"       # .hwp 파일들이 들어 있는 폴더
output_folder = r"output/hwp_txt"    # 추출된 .txt 파일 저장 폴더

input_folder = os.path.abspath(input_folder)
output_folder = os.path.abspath(output_folder)
os.makedirs(output_folder, exist_ok=True)

# ✅ 2. HWP 실행
hwp = win32com.client.gencache.EnsureDispatch("HWPFrame.HwpObject")
hwp.RegisterModule("FilePathCheckDLL", "SecurityModule")  # 보안 모듈 필수

# (선택) 한글 창 숨기기
try:
    hwp.XHwpWindows.Item(0).Visible = False
except:
    pass

# ✅ 3. 폴더 내 모든 .hwp 파일 처리
for filename in os.listdir(input_folder):
    if filename.lower().endswith(".hwp"):
        hwp_path = os.path.join(input_folder, filename)
        hwp_path = os.path.abspath(hwp_path)

        print(f"📂 처리 중: {filename}")

        try:
            # 파일 열기
            hwp.Open(hwp_path)

            # 전체 선택 & 복사
            hwp.Run("SelectAll")
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.CloseClipboard()

            hwp.Run("Copy")
            time.sleep(0.7)

            # 클립보드에서 텍스트 가져오기 (오류 대비 재시도)
            text = ""
            for i in range(5):
                try:
                    win32clipboard.OpenClipboard()
                    text = win32clipboard.GetClipboardData()
                    win32clipboard.CloseClipboard()
                    break
                except:
                    time.sleep(0.5)

            # 저장할 파일 경로 설정
            txt_filename = os.path.splitext(filename)[0] + ".txt"
            output_path = os.path.join(output_folder, txt_filename)

            # 텍스트 저장
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"✅ 저장 완료 → {output_path}")

        except Exception as e:
            print(f"⚠️ 오류 발생 ({filename}): {e}")

# 종료
hwp.Quit()
print("\n🎉 모든 작업 완료!")