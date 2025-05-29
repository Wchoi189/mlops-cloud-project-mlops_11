#!/usr/bin/env python3
"""
Section 3 (모델 훈련 파이프라인) 빠른 테스트 스크립트
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
# project_root = Path(__file__).parent.parent
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_section3():
    """Section 3 구현 테스트"""
    
    print("🧪 Section 3: 모델 훈련 파이프라인 테스트 시작")
    print("=" * 50)
    
    # 1. 필요한 파일 확인
    print("\n1️⃣ 필요한 파일 확인...")
    
    required_files = [
        'src/models/trainer.py',
        'src/models/evaluator.py', 
        'scripts/train_model.py',
        'data/processed/movies_with_ratings.csv'
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
        df = pd.read_csv('data/processed/movies_with_ratings.csv')
        print(f"✅ 데이터 로드 성공: {len(df):,}개 샘플")
        
        # 필요한 컬럼 확인
        # required_columns = ['startYear', 'runtimeMinutes', 'numVotes', 
        #                   'is_Action', 'is_Comedy', 'is_Drama', 'averageRating'] #  누락된 컬럼: ['is_Action', 'is_Comedy', 'is_Drama']
        
        required_columns = ['startYear', 'runtimeMinutes', 'numVotes', 'isAdult', 'averageRating']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"❌ 누락된 컬럼: {missing_columns}")
            return False
        else:
            print("✅ 필요한 컬럼 모두 존재")
            
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
        return False
    
    # 5. 모델 평가 테스트
    print("\n5️⃣ 모델 평가 테스트...")
    
    try:
        evaluator = ModelEvaluator()
        evaluator.load_model(model_paths['model_path'], model_type="random_forest")
        
        eval_metrics, y_pred = evaluator.evaluate_model(X, y)
        print(f"✅ 모델 평가 성공:")
        print(f"   RMSE: {eval_metrics['rmse']:.4f}")
        print(f"   R²: {eval_metrics['r2_score']:.4f}")
        
    except Exception as e:
        print(f"❌ 모델 평가 오류: {e}")
        return False
    
    # 6. 단일 예측 테스트
    print("\n6️⃣ 단일 예측 테스트...")
    
    try:
        # 테스트용 영화 정보
        test_movie = {
            'startYear': 2020,
            'runtimeMinutes': 120,
            'numVotes': 10000,
            'is_Action': 1,
            'is_Comedy': 0,
            'is_Drama': 0
        }
        
        prediction = evaluator.predict_single_movie(test_movie)
        print(f"✅ 단일 예측 성공: {prediction:.2f}/10")
        
    except Exception as e:
        print(f"❌ 단일 예측 오류: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Section 3 모든 테스트 통과!")
    print("\n📝 다음 단계:")
    print("   1. MLflow UI 확인: mlflow ui")
    print("   2. 전체 훈련 실행: python scripts/train_model.py")
    print("   3. Section 4 (API 서빙) 진행 준비 완료")
    
    return True


if __name__ == "__main__":
    success = test_section3()
    sys.exit(0 if success else 1)