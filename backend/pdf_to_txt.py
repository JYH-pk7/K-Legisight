# data 폴더내 pdf파일의 텍스트만 추출하여 output폴더의 txt파일로 저장하는 코드
import pymupdf
import os

pdf_file_path = "data/(파일이름).pdf"   # PDF 파일 경로 설정
doc = pymupdf.open(pdf_file_path)

header_height = 80  # 헤더 높이 설정
footer_height = 80  # 푸터 높이 설정
full_text = ""


for page in doc :   # 문서 페이지 반복
    rect = page.rect    # 페이지 크기 가져오기

    header = page.get_text(clip=(0,0, rect.width, header_height))  # 헤더 영역 텍스트 추출
    footer = page.get_text(clip=(0, rect.height - footer_height, rect.width, rect.height))  # 푸터 영역 텍스트 추출
    text = page.get_text(clip=(0, header_height, rect.width, rect.height - footer_height))  # 본문 영역 텍스트 추출

    full_text += text  


# 파일명만 추출
pdf_file_name = os.path.basename(pdf_file_path)
pdf_file_name = os.path.splitext(pdf_file_name)[0]  # 확장자 제거

txt_file_path = f"output/{pdf_file_name}_with_preprocessing.txt"    # 저장할 텍스트 파일 경로 설정

with open(txt_file_path, "w", encoding="utf-8") as f:
    f.write(full_text)