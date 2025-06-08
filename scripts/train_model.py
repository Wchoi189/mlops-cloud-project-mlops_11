#!/usr/bin/env python3
"""
모델 훈련 스크립트 - Section 3 & 4 연동
Enhanced Model Training Script for API Serving
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """메인 훈련 파이프라인"""

    print("🚀 MLOps 영화 평점 예측 모델 훈련 시작")
    print("=" * 50)

    try:
        # 1. 환경 확인
        print("1️⃣ 환경 확인...")

        # 필요한 데이터 파일 확인
        data_file = "data/processed/movies_with_ratings.csv"
        if not os.path.exists(data_file):
            print(f"❌ 데이터 파일이 없습니다: {data_file}")
            print("   먼저 Section 1, 2를 완료하세요:")
            print("   python scripts/tests/test_section1.py")
            print("   python scripts/tests/test_section2.py")
            return False

        print(f"✅ 데이터 파일 확인: {data_file}")

        # 2. 모듈 import
        print("\n2️⃣ 모듈 import...")
        from src.models.trainer import MovieRatingTrainer, run_training_pipeline

        print("✅ 훈련 모듈 import 완료")

        # 3. 데이터 로드 및 기본 정보
        print("\n3️⃣ 데이터 기본 정보...")
        import pandas as pd

        df = pd.read_csv(data_file)
        print(f"✅ 데이터 로드: {len(df):,}개 영화")
        print(
            f"   평점 범위: {df['averageRating'].min():.1f} ~ {df['averageRating'].max():.1f}"
        )
        print(f"   평균 평점: {df['averageRating'].mean():.2f}")

        # 4. 모델 훈련 실행
        print("\n4️⃣ 모델 훈련 실행...")
        print("⏳ Random Forest 모델 훈련 중... (시간이 걸릴 수 있습니다)")

        model_info = run_training_pipeline()

        # 5. 결과 확인
        print("\n5️⃣ 훈련 결과 확인...")
        print("✅ 모델 훈련 완료!")
        print(f"📦 저장된 모델: {model_info['model_path']}")
        print(f"📦 저장된 스케일러: {model_info['scaler_path']}")
        print(f"🔧 사용된 피처: {model_info['feature_names']}")

        # 6. API 준비 상태 확인
        print("\n6️⃣ API 서빙 준비 상태 확인...")

        models_dir = Path("models")
        model_files = list(models_dir.glob("*forest*.joblib"))
        scaler_files = list(models_dir.glob("scaler_*.joblib"))

        print(f"✅ 모델 파일: {len(model_files)}개")
        print(f"✅ 스케일러 파일: {len(scaler_files)}개")

        if model_files and scaler_files:
            print("\n🎉 Section 4 (API 서빙) 준비 완료!")
            print("\n📝 다음 단계:")
            print("   1. API 서버 시작: uvicorn src.api.main:app --reload --port 8000")
            print("   2. API 테스트: python scripts/tests/test_section4.py")
            print("   3. API 문서 확인: http://localhost:8000/docs")
            print("   4. 영화 예측 테스트:")
            print('      curl -X POST "http://localhost:8000/predict/movie" \\')
            print('           -H "Content-Type: application/json" \\')
            print(
                '           -d \'{"title":"영화제목","startYear":2020,"runtimeMinutes":120,"numVotes":5000}\''
            )
        else:
            print("⚠️ 일부 파일이 누락되었습니다.")

        return True

    except Exception as e:
        print(f"\n❌ 훈련 중 오류 발생: {e}")
        import traceback

        print("\n상세 오류:")
        traceback.print_exc()
        return False


def quick_test():
    """빠른 테스트 모드"""

    print("🔧 빠른 테스트 모드")
    print("=" * 25)

    try:
        # 작은 샘플로 빠른 훈련
        import pandas as pd

        from src.models.trainer import MovieRatingTrainer

        # 데이터 로드
        df = pd.read_csv("data/processed/movies_with_ratings.csv")
        sample_df = df.sample(n=min(1000, len(df)), random_state=42)

        print(f"📊 샘플 데이터: {len(sample_df)}개")

        # 빠른 훈련
        trainer = MovieRatingTrainer("quick_test")
        X, y = trainer.prepare_features(sample_df)
        metrics = trainer.train_model(X, y)
        model_info = trainer.save_model()

        print("✅ 빠른 테스트 완료!")
        print(f"   RMSE: {metrics['rmse']:.4f}")
        print(f"   R²: {metrics['r2_score']:.4f}")
        print(f"   모델: {model_info['model_path']}")

        return True

    except Exception as e:
        print(f"❌ 빠른 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="영화 평점 예측 모델 훈련")
    parser.add_argument(
        "--quick", action="store_true", help="빠른 테스트 모드 (소량 데이터)"
    )

    args = parser.parse_args()

    if args.quick:
        success = quick_test()
    else:
        success = main()

    if success:
        print("\n🎯 훈련 완료! API 서빙 준비됨")
    else:
        print("\n💥 훈련 실패")

    sys.exit(0 if success else 1)
