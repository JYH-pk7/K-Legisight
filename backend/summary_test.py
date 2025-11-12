from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

# ✅ 실제 존재하는 NER 모델로 변경
MODEL_NAME = "TAKEZO-KO/Legal-BERT-NER-Korean"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForTokenClassification.from_pretrained(MODEL_NAME)

ner = pipeline("token-classification", model=model, tokenizer=tokenizer, grouped_entities=True)

text = "국방부는 군인사법 개정안과 병역자원 재배치를 추진하고 있습니다."
print(ner(text))