'''
data_separator.py
'''
import pandas as pd
from sklearn.model_selection import train_test_split

# 1. 원본 데이터 로드
df_all = pd.read_csv("./sentiment_analysis/original_data/all_sentiment_data.csv")

# 2. Train(80%)과 Temp(20%)로 1차 분할
# 'label' 컬럼을 기준으로 층화 샘플링 (Stratify) 적용
df_train, df_temp = train_test_split(
    df_all, 
    test_size=0.2, 
    random_state=42, # 결과 재현을 위한 랜덤 시드
    stratify=df_all['label'] # 라벨 비율 유지
)

# 3. Temp(20%)를 Validation(10%)과 Test(10%)로 2차 분할
# (2차 분할에서 test_size=0.5를 하면 원래 비율 20%의 절반인 10%가 됨)
df_validation, df_test = train_test_split(
    df_temp, 
    test_size=0.5, 
    random_state=42, 
    stratify=df_temp['label'] # 라벨 비율 유지
)

# 4. data 폴더에 저장
df_train.to_csv("./sentiment_analysis/data/train.csv", index=False)
df_validation.to_csv("./sentiment_analysis/data/validation.csv", index=False)
df_test.to_csv("./sentiment_analysis/data/test.csv", index=False)

print(f"총 데이터 수: {len(df_all)}")
print(f"train.csv: {len(df_train)}개 (약 80%)")
print(f"validation.csv: {len(df_validation)}개 (약 10%)")
print(f"test.csv: {len(df_test)}개 (약 10%)")