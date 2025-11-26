===================
모델 성능지표 출력
===================

import json
import torch
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from transformers import AutoTokenizer, AutoModelForSequenceClassification, ElectraTokenizerFast, BertTokenizerFast
from tqdm import tqdm
import sys
import os 
import pandas as pd

# =========================================
# 1. 설정값 및 모델 로드 (경로 일반화)
# =========================================
# ★★★ 필수 확인: Test JSON 파일 경로를 인수로 받음 ★★★
if len(sys.argv) < 2:
    print("🚨 오류: 테스트 JSON 파일 경로를 지정해야 합니다.")
    print("사용법: python evaluation_test.py <테스트_JSON_경로>")
    sys.exit(1)

TEST_JSON_FILE = sys.argv[1]
LABELS = ["협력", "중립", "비협력"]
LABEL_TO_ID = {label: i for i, label in enumerate(LABELS)}

BASE_MODEL_DIR = "./sentiment_analysis/models/kobert_v3/" 

# 제일 좋은 체크포인트의 가중치 적용 
FINE_TUNED_MODEL_DIR = "./sentiment_analysis/models/kobert_v3/checkpoint-18"
# 모델 및 토크나이저 로드 (GPU가 안되면 자동으로 CPU 사용)
try:
    print(f"모델 로드 중... ({FINE_TUNED_MODEL_DIR})")
    
    # 🚨 토크나이저는 베이스 경로에서 로드 🚨
    tokenizer = BertTokenizerFast.from_pretrained(
        BASE_MODEL_DIR, 
        local_files_only=True,      
        trust_remote_code=True      
    )

    # 🚨 모델 가중치는 체크포인트 경로에서 로드 🚨
    model = AutoModelForSequenceClassification.from_pretrained(
        FINE_TUNED_MODEL_DIR,
        local_files_only=True,
        trust_remote_code=True
    )
    model.eval()
except Exception as e:
    print(f"🚨 모델 로드 실패: {e}")
    print(f"경로: {FINE_TUNED_MODEL_DIR}에 모델 파일이 제대로 있는지 확인하세요.")
    sys.exit(1)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
print(f"✅ 모델 로드 완료. 사용 장치: {device}")


# =========================================
# 2. 예측 및 평가 함수
# =========================================
def run_evaluation():
    # 1. 데이터 로드 (Test set)
    print(f"📥 테스트 데이터 로드 중: {TEST_JSON_FILE}")
    try:
        # 🚨🚨🚨 json.load 대신 pandas.read_csv 사용 🚨🚨🚨
        # 파일 이름이 .csv이므로 pandas로 읽어야 함
        test_df = pd.read_csv(TEST_JSON_FILE)
        
        # DataFrame을 리스트 오브젝트로 변환 (기존 코드와 호환을 위해)
        test_data = test_df.to_dict('records') 
        
    except FileNotFoundError:
        print(f"🚨 오류: {TEST_JSON_FILE} 파일을 찾을 수 없습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"🚨 오류: 파일 로드 중 문제가 발생했습니다: {e}")
        sys.exit(1)
    
    true_labels = [] # 실제 정답 라벨
    predictions = [] # 모델 예측 라벨
    
    print(f"총 테스트 데이터 수: {len(test_data)}개. 예측 시작...")
    
    # 2. 예측 수행 및 결과 저장
    for item in tqdm(test_data, desc="Evaluating Model"):
        text = item.get("speech_text", "")
        
        # 🚨🚨🚨 CSV에서 숫자로 읽어온 'label' 값을 가져와 문자열로 변환 🚨🚨🚨
        true_label_int = item.get("label", -1) # 숫자로 가져옴
        
        # LABELS 리스트에 맞게 숫자를 문자열로 변환
        if true_label_int in [0, 1, 2]:
            true_label_str = LABELS[true_label_int] # 0:'협력', 1:'중립', 2:'비협력'으로 변환
        else:
            true_label_str = "" # 유효하지 않은 값은 빈 문자열 처리

        if not text.strip() or true_label_str not in LABELS:
            continue

        # 이제 true_labels.append(LABEL_TO_ID[true_label_str]) 코드가 정상 작동함!
        true_labels.append(LABEL_TO_ID[true_label_str])
        
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
        
        predicted_index = torch.argmax(logits, dim=1).item()
        predictions.append(predicted_index)

    # 3. 성능 지표 계산
    if not true_labels:
        print("🚨 유효한 테스트 데이터가 없습니다.")
        sys.exit(1)

    accuracy = accuracy_score(true_labels, predictions)
    f1_weighted = f1_score(true_labels, predictions, average='weighted', zero_division=0)
    f1_macro = f1_score(true_labels, predictions, average='macro', zero_division=0)
    precision = precision_score(true_labels, predictions, average='weighted', zero_division=0)
    recall = recall_score(true_labels, predictions, average='weighted', zero_division=0)

    # 4. 결과 출력
    print("\n" + "="*50)
    print("           🤖 모델 최종 성능 평가 결과 🤖")
    print("="*50)
    print(f"테스트 데이터셋 크기: {len(true_labels)}개")
    print(f"정확도 (Accuracy): {accuracy:.4f}")
    print(f"F1-Score (Weighted): {f1_weighted:.4f}")
    print(f"F1-Score (Macro): {f1_macro:.4f}")
    print(f"정밀도 (Precision): {precision:.4f}")
    print(f"재현율 (Recall): {recall:.4f}")
    print("="*50)


if __name__ == "__main__":

    run_evaluation()
