import pandas as pd

# CSV 불러오기
df = pd.read_csv("assembly.dimension_birthday_converted.csv")

df.to_csv("dimension_converted.csv", index=False, sep=",", encoding="utf-8")

print("CSV 변환 완료")