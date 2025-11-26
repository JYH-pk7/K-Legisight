'''
finetune_bert.py
'''
import pandas as pd
from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer, ElectraTokenizerFast, AutoModelForSequenceClassification, TrainingArguments, Trainer
import numpy as np
from sklearn.metrics import accuracy_score, f1_score
import sys 

# =========================================
# 1. 설정값 정의
# =========================================
# MODEL_CHECKPOINT = "klue/bert-base" 
# MODEL_CHECKPOINT = "JiyoungP/QOD-Korean-Political-Sentiment-BERT"
# MODEL_CHECKPOINT = "WhitePeak/bert-base-cased-Korean-sentiment"
# MODEL_CHECKPOINT = "klue/roberta-base"
# MODEL_CHECKPOINT = "FacebookAI/xlm-roberta-base"
MODEL_CHECKPOINT = "beomi/kcbert-base"

NUM_LABELS = 3

# 저장 폴더
# OUTPUT_DIR = "./sentiment_analysis/models/klue_bert_v1"
# OUTPUT_DIR = "./sentiment_analysis/models/jy_bert_v2"
OUTPUT_DIR = "./backend/sentiment_analysis/models/beomi_kcbert_v10"

# 라벨 매핑: 모델 출력과 사람이 읽는 라벨을 연결
LABEL_MAP = {
    0: "협력", 
    1: "중립", 
    2: "비협력"
}


# =========================================
# 2. 데이터 준비 및 전처리 (토큰화)
# =========================================
def load_and_tokenize_data(tokenizer):
    """
    학습 및 검증 데이터를 로드하고 토크나이징하여 데이터셋을 준비합니다.
    
    데이터셋 파일(train.csv, validation.csv)이 존재하지 않으면 오류 메시지를 출력하고 None을 반환합니다.
    
    Args:
        tokenizer (transformers.PreTrainedTokenizer): 각각의 모델에 맞는 토크나이저 객체.
    """    
    try:
        df_train = pd.read_csv("./backend/sentiment_analysis/data/train.csv")
        df_valid = pd.read_csv("./backend/sentiment_analysis/data/validation.csv")
    except FileNotFoundError:
        print("🚨 오류: data/train.csv 또는 data/validation.csv 파일을 찾을 수 없습니다.")
        print("   데이터 파일을 data 폴더에 넣고 스크립트를 실행해주세요.")
        return None

    # Pandas DataFrame을 Hugging Face Dataset으로 변환
    raw_datasets = DatasetDict({
        "train": Dataset.from_pandas(df_train),
        "validation": Dataset.from_pandas(df_valid)
    })
    
    # 텍스트 컬럼 이름: 'speech_text', 라벨 컬럼 이름: 'label' 이라고 가정
    def tokenize_function(examples):
        # 모델의 최대 입력 길이에 맞게 자르고(truncation), 패딩(padding) 적용
        return tokenizer(examples["speech_text"], truncation=True, padding="max_length")

    tokenized_datasets = raw_datasets.map(tokenize_function, batched=True)
    # 텍스트 컬럼만 제거하고, 없는 __index_level_0__는 제거 목록에서 제외
    tokenized_datasets = tokenized_datasets.remove_columns(["speech_text"])
    tokenized_datasets = tokenized_datasets.rename_column("label", "labels")
    tokenized_datasets.set_format("torch")
    
    return tokenized_datasets


# =========================================
# 3. 평가 지표 정의
# =========================================
def compute_metrics(p):
    # p는 (predictions, label_ids) 튜플
    preds = np.argmax(p.predictions, axis=1) # 가장 높은 로짓을 가진 클래스 선택
    
    # 다중 클래스 분류에서 F1-score는 'weighted'로 계산하는 것이 일반적
    return {
        "accuracy": accuracy_score(p.label_ids, preds),
        "f1_weighted": f1_score(p.label_ids, preds, average="weighted"),
        "f1_macro": f1_score(p.label_ids, preds, average="macro"),
    }


# =========================================
# 4. 모델 로드 및 학습 실행
# 학습 완료 후, 최종 모델과 토크나이저를 OUTPUT_DIR에 저장
# =========================================
def run_finetuning():
    tokenizer = AutoTokenizer.from_pretrained(
    MODEL_CHECKPOINT, 
    trust_remote_code=True
)

    model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_CHECKPOINT, 
    num_labels=NUM_LABELS,
    trust_remote_code=True,
    ignore_mismatched_sizes=True
)
    tokenized_datasets = load_and_tokenize_data(tokenizer)

    # 학습 인자 설정
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=3,
        weight_decay=0.01,
        evaluation_strategy="epoch", # 매 에포크마다 검증
        save_strategy="epoch",       # 매 에포크마다 저장
        load_best_model_at_end=True, # 학습 종료 시 최적 모델 로드
        metric_for_best_model="f1_weighted", # 최적 모델 선정 기준
    )

# Trainer 인스턴스 생성
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
        # tokenizer=tokenizer, # ★★★ 이 줄은 주석 처리 또는 삭제되어 있어야 함 (OK)
        compute_metrics=compute_metrics,
    )

    print("🚀 파인튜닝 시작...")
    trainer.train()
    
    # 1. 모델 가중치 저장 (Trainer가 저장)
    trainer.save_model(OUTPUT_DIR)
    
    # 2. 토크나이저 저장 (KoBERT 버그 우회를 위한 try-except 블록)
    try:
        # 표준 방식으로 먼저 시도 (대부분의 모델에 유효)
        tokenizer.save_pretrained(OUTPUT_DIR) 
        
    except TypeError as e:
        # TypeError 발생 시 (KoBERT의 filename_prefix 문제), 수동 복구 로직 실행
        if "filename_prefix" in str(e):
            print("⚠️ KoBERT 토크나이저 저장 오류 발생: 'filename_prefix' 문제. 수동 복구 로직 실행.")
            
            # 토크나이저의 파일들 (vocab.txt 등)만 수동으로 저장
            vocab_files = tokenizer.save_vocabulary(OUTPUT_DIR)
            print(f"   -> 필수 Vocab 파일들을 저장했습니다: {vocab_files}")
        else:
            # 예상치 못한 다른 TypeError면 그냥 다시 발생시킴
            raise e
        
    # 3. 모델 저장 완료 메시지
    print(f"✅ 파인튜닝 완료! 모델이 {OUTPUT_DIR}에 저장되었습니다.")

if __name__ == "__main__":
    run_finetuning()
