import pandas as pd
import re

# 1. 파일 읽기
file_path = 'data/21대의원_위원회이력_최종.csv'
df = pd.read_csv(file_path)

# 2. 데이터 파싱 및 변환
parsed_data = []

# 정규표현식: 날짜(YYYY.MM.DD) ~ 날짜(YYYY.MM.DD) [제21대] 위원회명
# 예: 2022.08.02 ~ 2023.06.13 제21대 연금개혁특별위원회
pattern = re.compile(r'(\d{4}\.\d{2}\.\d{2})\s*~\s*(\d{4}\.\d{2}\.\d{2})\s+(?:제\d+대\s+)?(.+)')

for _, row in df.iterrows():
    member_id = row['member_id']
    history_text = row['committees_history']
    
    if pd.isna(history_text):
        continue
        
    # 줄바꿈으로 분리하여 각 이력 처리
    for line in history_text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        match = pattern.search(line)
        if match:
            start_date = match.group(1)
            end_date = match.group(2)
            committee = match.group(3).strip()
            
            parsed_data.append({
                'member_id': member_id,
                'committee': committee,
                'start_date': start_date,
                'end_date': end_date
            })

# 3. 데이터프레임 생성
result_df = pd.DataFrame(parsed_data)

# 4. CSV 파일로 저장
output_path = 'data/의원별_위원회_활동이력_정리.csv'
result_df.to_csv(output_path, index=False, encoding='utf-8-sig')
print(output_path, "로 파일 생성 완료")