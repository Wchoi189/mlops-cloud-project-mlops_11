#!/usr/bin/env python3
"""
Section 3 (모델 훈련 파이프라인) 빠른 테스트 스크립트 - 수정된 버전
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_section3():
    """Section 3 구현 테스트"""

    print("🧪 Section 3: 모델 훈련 파이프라인 테스트 시작")
    print("=" * 50)

    # 1. 필요한 파일 확인
    print("\n1️⃣ 필요한 파일 확인...")

    required_files = [
        "src/models/trainer.py",
        "src/models/evaluator.py",
        "scripts/train_model.py",
        "data/processed/movies_with_ratings.csv",
    ]

    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n❌ 누락된 파일들: {missing_files}")
        print("먼저 이전 섹션들을 완료하세요.")
        return False

    # 2. 모듈 import 테스트
    print("\n2️⃣ 모듈 import 테스트...")

    try:
        import mlflow

        print(f"MLflow version: {mlflow.__version__}")

        from src.models.trainer import MovieRatingTrainer, run_training_pipeline

        print("✅ trainer 모듈 import 성공")

        from src.models.evaluator import ModelEvaluator

        print("✅ evaluator 모듈 import 성공")

    except ImportError as e:
        print(f"❌ Import 오류: {e}")
        print("필요한 라이브러리를 설치하세요: pip install -r requirements.txt")
        return False

    # 3. 데이터 로드 테스트
    print("\n3️⃣ 데이터 로드 테스트...")

    try:
        import pandas as pd

        df = pd.read_csv("data/processed/movies_with_ratings.csv")
        print(f"✅ 데이터 로드 성공: {len(df):,}개 샘플")

        # 🎯 수정: 실제 사용하는 피처로 확인
        from src.models.trainer import MovieRatingTrainer

        trainer_temp = MovieRatingTrainer("temp")
        required_columns = trainer_temp.BASE_FEATURES + [trainer_temp.TARGET_COLUMN]

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"❌ 누락된 컬럼: {missing_columns}")
            print(f"   사용가능한 컬럼: {list(df.columns)}")
            return False
        else:
            print("✅ 필요한 컬럼 모두 존재")
            print(f"   사용할 피처: {trainer_temp.BASE_FEATURES}")
            print(f"   타겟 컬럼: {trainer_temp.TARGET_COLUMN}")

    except Exception as e:
        print(f"❌ 데이터 로드 오류: {e}")
        return False

    # 4. 간단한 모델 훈련 테스트
    print("\n4️⃣ 간단한 모델 훈련 테스트...")

    try:
        # 소량 데이터로 빠른 테스트
        df_sample = df.sample(n=min(1000, len(df)), random_state=42)

        trainer = MovieRatingTrainer("test_experiment")
        X, y = trainer.prepare_features(df_sample)

        print(f"✅ 피처 준비 성공: {X.shape}")
        print(f"   피처 이름: {trainer.get_feature_names()}")

        # Random Forest로 빠른 훈련
        metrics = trainer.train_model(X, y, model_type="random_forest")

        print(f"✅ 모델 훈련 성공:")
        print(f"   RMSE: {metrics['rmse']:.4f}")
        print(f"   R²: {metrics['r2_score']:.4f}")

        # 모델 저장 테스트
        model_paths = trainer.save_model()
        print(f"✅ 모델 저장 성공: {model_paths['model_path']}")

    except Exception as e:
        print(f"❌ 모델 훈련 오류: {e}")
        import traceback

        traceback.print_exc()
        return False

    # 5. 모델 평가 테스트
    print("\n5️⃣ 모델 평가 테스트...")

    try:
        evaluator = ModelEvaluator()
        model_path = model_paths["model_path"]
        if isinstance(model_path, list):
            model_path = model_path[0]
        evaluator.load_model(model_path, model_type="random_forest")

        eval_metrics, y_pred = evaluator.evaluate_model(X, y)
        print(f"✅ 모델 평가 성공:")
        print(f"   RMSE: {eval_metrics['rmse']:.4f}")
        print(f"   R²: {eval_metrics['r2_score']:.4f}")

        # 모델 정보 확인
        model_info = evaluator.get_model_info()
        print(f"   모델 정보: {model_info}")

    except Exception as e:
        print(f"❌ 모델 평가 오류: {e}")
        import traceback

        traceback.print_exc()
        return False

    # 6. 단일 예측 테스트 - 🎯 수정된 피처 사용
    print("\n6️⃣ 단일 예측 테스트...")

    try:
        # 🎯 실제 모델에서 사용하는 피처로 테스트 데이터 생성
        test_movie = {"startYear": 2020, "runtimeMinutes": 120, "numVotes": 10000}

        print(f"   테스트 영화 정보: {test_movie}")
        print(f"   모델이 사용하는 피처: {evaluator.get_feature_names()}")

        prediction = evaluator.predict_single_movie(test_movie)
        print(f"✅ 단일 예측 성공: {prediction:.2f}/10")

        # 추가 테스트: 피처가 부분적으로 누락된 경우
        test_movie_partial = {
            "startYear": 2015,
            "runtimeMinutes": 90,
            # numVotes 누락 - 기본값으로 처리되어야 함
        }

        prediction_partial = evaluator.predict_single_movie(test_movie_partial)
        print(f"✅ 부분 피처 예측 성공: {prediction_partial:.2f}/10")

    except Exception as e:
        print(f"❌ 단일 예측 오류: {e}")
        import traceback

        traceback.print_exc()
        return False

    # 7. 배치 예측 테스트
    print("\n7️⃣ 배치 예측 테스트...")

    try:
        # 소량 데이터로 배치 예측
        batch_sample = df.sample(n=min(10, len(df)), random_state=42)
        predictions = evaluator.batch_predict(batch_sample)

        print(f"✅ 배치 예측 성공: {len(predictions)}개 샘플")
        print(f"   예측 범위: {predictions.min():.2f} ~ {predictions.max():.2f}")

        # 실제값과 비교
        actual_ratings = batch_sample[trainer.TARGET_COLUMN].to_numpy()
        print(f"   실제 범위: {actual_ratings.min():.2f} ~ {actual_ratings.max():.2f}")

    except Exception as e:
        print(f"❌ 배치 예측 오류: {e}")
        import traceback

        traceback.print_exc()
        return False

    print("\n" + "=" * 50)
    print("🎉 Section 3 모든 테스트 통과!")
    print("\n📝 핵심 성과:")
    print(f"   🎯 사용된 피처: {trainer.get_feature_names()}")
    print(f"   📊 모델 성능: RMSE={metrics['rmse']:.4f}, R²={metrics['r2_score']:.4f}")
    print(f"   💾 저장된 모델: {model_paths['model_path']}")
    print(f"   🔧 MLflow 실험: {trainer.experiment_name}")

    print("\n📝 다음 단계:")
    print("   1. MLflow UI 확인: mlflow ui --port 5000")
    print("   2. 전체 훈련 실행: python scripts/train_model.py")
    print("   3. Section 4 (API 서빙) 진행 준비 완료")
    print("   4. 저장된 모델 경로: models/ 디렉토리 확인")

    return True


if __name__ == "__main__":
    success = test_section3()
    sys.exit(0 if success else 1)
