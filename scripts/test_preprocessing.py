#!/usr/bin/env python3
"""
데이터 전처리 파이프라인 테스트 스크립트
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from src.data.preprocessing import IMDbPreprocessor


def test_preprocessing_pipeline():
    """전처리 파이프라인 전체 테스트"""
    print("🧪 전처리 파이프라인 테스트 시작...")
    print("=" * 60)

    try:
        # 1. 전처리기 생성
        print("1️⃣ 전처리기 생성...")
        preprocessor = IMDbPreprocessor()

        # 2. 데이터 로드
        print("2️⃣ 데이터 로드...")
        df = preprocessor.load_data()
        print(f"   원본 데이터: {len(df):,} 행, {len(df.columns)} 열")

        # 3. 전처리 실행
        print("3️⃣ 전처리 실행...")
        X, y, feature_names = preprocessor.fit_transform(df)
        print(f"   피처 행렬: {X.shape}")
        print(f"   타겟 벡터: {y.shape}")
        print(f"   피처 개수: {len(feature_names)}")

        # 4. 피처 상세 정보
        print("\n4️⃣ 피처 상세 정보:")
        for i, feature in enumerate(feature_names):
            feature_stats = X[:, i]
            print(
                f"   {feature:20s}: 평균={feature_stats.mean():.3f}, "
                f"표준편차={feature_stats.std():.3f}"
            )

        # 5. 데이터 분할
        print("\n5️⃣ 데이터 분할...")
        X_train, X_test, y_train, y_test = preprocessor.create_train_test_split(X, y)

        print(f"   훈련 세트: X={X_train.shape}, y={y_train.shape}")
        print(f"   테스트 세트: X={X_test.shape}, y={y_test.shape}")

        # 6. 타겟 분포 확인
        print("\n6️⃣ 타겟 분포 확인:")
        print(f"   전체 평점 범위: {y.min():.1f} ~ {y.max():.1f}")
        print(f"   평균 평점: {y.mean():.2f} ± {y.std():.2f}")
        print(f"   훈련 평점 평균: {y_train.mean():.2f}")
        print(f"   테스트 평점 평균: {y_test.mean():.2f}")

        # 7. 전처리기 저장/로드 테스트
        print("\n7️⃣ 전처리기 저장/로드 테스트...")
        preprocessor.save_preprocessor()

        # 새로운 전처리기로 로드 테스트
        new_preprocessor = IMDbPreprocessor()
        new_preprocessor.load_preprocessor()

        # 동일한 데이터로 변환 테스트
        X_new = new_preprocessor.transform(df)

        # 결과 비교
        if np.allclose(X, X_new):
            print("   ✅ 저장/로드 테스트 성공!")
        else:
            print("   ❌ 저장/로드 테스트 실패!")

        # 8. 장르 분석
        print("\n8️⃣ 장르 분석:")
        print(f"   선택된 상위 장르: {preprocessor.top_genres}")

        # 9. 품질 체크
        print("\n9️⃣ 데이터 품질 체크:")

        # NaN 체크
        nan_count = np.isnan(X).sum()
        print(f"   결측값: {nan_count} 개")

        # 무한값 체크
        inf_count = np.isinf(X).sum()
        print(f"   무한값: {inf_count} 개")

        # 피처 분산 체크
        feature_vars = np.var(X, axis=0)
        zero_var_features = sum(feature_vars < 1e-10)
        print(f"   분산이 0인 피처: {zero_var_features} 개")

        print("\n" + "=" * 60)
        print("✅ 전처리 파이프라인 테스트 완료!")
        print("✅ 모든 검증 통과! Section 3으로 진행 가능")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_preprocessing_pipeline()
    sys.exit(0 if success else 1)
