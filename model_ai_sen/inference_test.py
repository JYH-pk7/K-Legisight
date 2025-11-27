"""
inference_test.py
"""
import json
import torch
import numpy as np
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from tqdm import tqdm
import os 
import sys

# =========================================
# 1. 설정값 및 모델 로드 (경로 수정됨!)
# =========================================

if len(sys.argv) < 3:
    print("🚨 오류: 입력 및 출력 파일 경로를 지정해야 합니다.")
    print("사용법: python 스크립트명.py <입력_JSON_경로> <출력_JSON_경로>")
    # 예시: python inference_test.py ./data/speeches_1.json ./output/result_1.json
    sys.exit(1)

# 인수로 받은 경로를 변수에 할당 (공백 기준으로 할당 sys[0]:실행파일, sys[1]:인풋파일, sys[2]:아웃풋파일)
INPUT_JSON_FILE = sys.argv[1] 
OUTPUT_JSON_FILE = sys.argv[2] 
# ---------------------------------------------------------------> python (inference_test.py) (./data/speeches_50176.json) (./division_out/result_50176_3.json)

# MODEL_PATH = "./sentiment_analysis/models/bert_sentiment_v1" 
MODEL_PATH = "./sentiment_analysis/models/hufgging_ji_sentiment_v2" 
# MODEL_PATH = "./sentiment_analysis/models/monologg_kobert_sentiment_v3" 

LABELS = ["협력", "중립", "비협력"] # 라벨 매핑 (0, 1, 2)

# 모델 및 토크나이저 로드
try:
    print(f"모델 로드 중... ({MODEL_PATH})")

    # 🚨🚨🚨 trust_remote_code=True 옵션 추가 🚨🚨🚨
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True, trust_remote_code=True)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH, local_files_only=True, trust_remote_code=True)
    model.eval()

except Exception as e:
    print(f"🚨 모델 로드 실패: {e}")
    print(f"경로: {MODEL_PATH}에 모델 파일이 제대로 있는지 확인하세요.")
    exit()

# GPU 설정
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
print(f"✅ 모델 로드 완료. 사용 장치: {device}")


# =========================================
# 2. 예측 및 확률값 추출 함수
# =========================================
def get_sentiment_probabilities(text: str):
    """
    하나의 발화 텍스트를 받아 3가지 감성 확률값과 최종 예측 라벨을 반환
    """
    if not text.strip():
        # 텍스트가 비어있으면 중립으로 처리
        return {
            "prediction": "중립",
            "probabilities": {"협력": 0.0, "중립": 1.0, "비협력": 0.0}
        }
    
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits

    probabilities = torch.softmax(logits, dim=1).squeeze().tolist() 

    predicted_index = np.argmax(probabilities)
    predicted_label = LABELS[predicted_index]
    
    return {
        "prediction": predicted_label,
        "probabilities": {label: prob for label, prob in zip(LABELS, probabilities)}
    }


# =========================================
# 3. 메인 파이프라인 실행
# =========================================
def run_inference_pipeline():
    # 출력 디렉토리가 없으면 생성 (division_out)
    output_dir = os.path.dirname(OUTPUT_JSON_FILE)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"디렉토리 생성: {output_dir}")

    print(f"📥 JSON 파일 로드 중: {INPUT_JSON_FILE}")
    try:
        # JSON 파일을 로드할 때, C:\Project\K-Legisight를 기준으로 경로를 맞춰야 함
        with open(INPUT_JSON_FILE, 'r', encoding='utf-8') as f:
            speeches = json.load(f)
    except FileNotFoundError:
        # 파일이 없을 경우, 현재 실행 위치와 경로를 확인하라는 안내 메시지 출력
        print(f"🚨 JSON 파일을 찾을 수 없습니다.")
        print(f"기대한 경로: {os.path.abspath(INPUT_JSON_FILE)}")
        print("실행 위치(Current Working Directory)를 확인하거나, 경로를 수정해 주세요.")
        return
    except json.JSONDecodeError:
        print("🚨 JSON 파일 형식이 올바르지 않습니다. 파일 내용을 확인하세요.")
        return
    
    print(f"총 발화 수: {len(speeches)}개. 감성 분석 시작...")
    
    processed_speeches = []
    # tqdm을 사용해 진행률 표시
    for speech in tqdm(speeches, desc="Sentiment Analysis"):
        speech_text = speech.get("speech_text", "")
        
        # 감성 분석 수행
        sentiment_data = get_sentiment_probabilities(speech_text)
        
        # 원본 JSON 데이터에 새로운 필드 추가
        speech_new = dict(speech)
        speech_new["sentiment_result"] = {
            "predicted_label": sentiment_data["prediction"],
            "probabilities": sentiment_data["probabilities"]
        }
        
        processed_speeches.append(speech_new)
        
    print(f"\n✅ 감성 분석 완료! 결과를 {OUTPUT_JSON_FILE}에 저장합니다.")

    # 결과 JSON 저장
    with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(processed_speeches, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    run_inference_pipeline()