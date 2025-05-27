from src.data.preprocessing import IMDbPreprocessor

# 전처리 파이프라인 실행
p = IMDbPreprocessor()
df = p.load_data()
X, y, features = p.fit_transform(df)
p.save_preprocessor()
print("전처리 완료!")
print(f"피처 수: {len(features)}")
print(f"데이터 크기: {X.shape}")
print(f"피처 목록: {features}")
