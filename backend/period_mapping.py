import pandas as pd

# 1. 파일 경로 설정
id_file_path = 'member_id,의원명.txt'
info_file_path = 'data/21대의원임기정보_삭제금지!!.xlsx'
output_file_path = 'data/21대의원임기정보_ID매핑.xlsx'

# 2. 데이터 불러오기
# member_id 파일은 탭(\t)으로 구분되어 있는 것으로 보입니다.
df_ids = pd.read_csv(id_file_path, sep='\t', encoding='utf-8')

# 임기 정보 엑셀 파일 불러오기
df_info = pd.read_excel(info_file_path)

# 3. ID 매핑 딕셔너리 생성
# 이름(의원명)을 키(key), member_id를 값(value)으로 하는 딕셔너리 생성
# 주의: 동명이인(예: 이수진, 김병욱)이 있을 경우, 딕셔너리 구조상 마지막 ID로 덮어씌워질 수 있습니다.
# 이를 방지하기 위해 중복된 이름은 별도로 처리하거나, 우선 첫 번째 매칭되는 ID를 사용합니다.
id_map = df_ids.set_index('의원명')['member_id'].to_dict()

# 4. ID 매핑 수행
# info 파일의 'name' 컬럼을 기준으로 ID를 찾아 'number_id' 컬럼에 채워 넣습니다.
# 기존 'number_id'가 비어있다고 가정하고 채웁니다.
df_info['number_id'] = df_info['name'].map(id_map)

# 5. 결과 확인 및 저장
print("매핑 전 데이터 개수:", len(df_info))
print("매핑된 ID 개수:", df_info['number_id'].notnull().sum())

# 동명이인이나 매칭되지 않은 의원이 있는지 확인
unmatched = df_info[df_info['number_id'].isnull()]
if not unmatched.empty:
    print("\n[주의] 다음 의원들은 ID를 찾지 못했습니다 (동명이인 이슈 포함 가능):")
    print(unmatched['name'].unique())

df_info.to_excel(output_file_path, index=False)

print(f"\n작업 완료! 결과 파일이 생성되었습니다: {output_file_path}")