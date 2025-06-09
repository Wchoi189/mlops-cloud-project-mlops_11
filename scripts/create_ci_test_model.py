#!/usr/bin/env python3
"""
CI/CD 환경용 최소 모델 생성 스크립트
Creates minimal test model for CI/CD environments
"""

import os
import sys
from pathlib import Path
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_minimal_test_model():
    """CI/CD 테스트용 최소 모델 생성"""
    
    try:
        import numpy as np
        import joblib
        from datetime import datetime
        
        logger.info("🔧 CI/CD용 최소 테스트 모델 생성 중...")
        
        # 모델 디렉토리 생성
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)
        
        # 최소 테스트 데이터 생성
        np.random.seed(42)
        n_samples = 50  # CI에서 빠른 실행을 위해 적은 수
        
        # 간단한 mock 모델 클래스
        class MockModel:
            def __init__(self):
                self.n_estimators = 10
                self.max_depth = 3
                
            def predict(self, X):
                # 간단한 휴리스틱 기반 예측
                if hasattr(X, 'shape') and len(X.shape) == 2:
                    predictions = []
                    for sample in X:
                        # startYear, runtimeMinutes, numVotes 순서 가정
                        base_rating = 6.0
                        
                        if len(sample) >= 3:
                            # 정규화된 값들을 역정규화 (대략적으로)
                            year = sample[0] * 30 + 1990 if abs(sample[0]) < 10 else sample[0]
                            runtime = sample[1] * 120 + 80 if abs(sample[1]) < 10 else sample[1] 
                            votes = sample[2] * 100000 + 1000 if abs(sample[2]) < 10 else sample[2]
                            
                            # 휴리스틱 규칙
                            if year > 2010:
                                base_rating += 0.3
                            if 90 <= runtime <= 150:
                                base_rating += 0.2
                            if votes > 10000:
                                base_rating += 0.1
                                
                        # 노이즈 추가
                        base_rating += np.random.normal(0, 0.2)
                        predictions.append(np.clip(base_rating, 1.0, 10.0))
                    
                    return np.array(predictions)
                else:
                    return np.array([6.5])  # 기본값
        
        # Mock 스케일러 클래스
        class MockScaler:
            def __init__(self):
                # 각 피처의 평균과 표준편차 (대략적)
                self.mean_ = np.array([2005, 120, 25000])
                self.scale_ = np.array([15, 30, 50000])
                
            def transform(self, X):
                # 간단한 표준화
                return (X - self.mean_) / self.scale_
                
            def fit_transform(self, X):
                return self.transform(X)
        
        # 피처 이름 정의
        feature_names = ["startYear", "runtimeMinutes", "numVotes"]
        
        # Mock 모델 및 스케일러 생성
        model = MockModel()
        scaler = MockScaler()
        
        # 타임스탬프 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 모델 정보 딕셔너리 생성
        model_info = {
            "model": model,
            "feature_names": feature_names,
            "model_type": "random_forest",
            "created_at": datetime.now().isoformat(),
            "dataset_size": n_samples,
            "performance": {
                "rmse": 0.75,  # Mock 성능
                "r2": 0.25,
                "mae": 0.60
            },
            "ci_test_model": True,
            "environment": "ci_cd",
            "note": "Mock model for CI/CD testing - not for production use"
        }
        
        # 모델 저장
        model_path = models_dir / f"random_forest_model_{timestamp}.joblib"
        joblib.dump(model_info, model_path)
        logger.info(f"✅ 테스트 모델 저장: {model_path}")
        
        # 스케일러 저장
        scaler_path = models_dir / f"scaler_{timestamp}.joblib"
        joblib.dump(scaler, scaler_path)
        logger.info(f"✅ 스케일러 저장: {scaler_path}")
        
        # 테스트 예측
        test_array = np.array([[2020, 120, 15000]])
        test_scaled = scaler.transform(test_array)
        test_prediction = model.predict(test_scaled)[0]
        
        logger.info(f"✅ 테스트 예측: {test_prediction:.2f}/10")
        
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️ 일부 패키지 없음: {e}")
        logger.info("📝 기본 numpy만 사용하여 생성 시도...")
        
        # numpy만 사용한 fallback 방법
        try:
            import numpy as np
            import pickle
            from datetime import datetime
            
            models_dir = Path("models")
            models_dir.mkdir(exist_ok=True)
            
            # 매우 간단한 모델 정보만 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            simple_model_info = {
                "model": "fallback",
                "feature_names": ["startYear", "runtimeMinutes", "numVotes"],
                "model_type": "random_forest",
                "ci_test_model": True,
                "environment": "ci_cd_minimal"
            }
            
            # 파일 생성 (pickle 사용)
            model_path = models_dir / f"random_forest_model_{timestamp}.joblib"
            with open(model_path, 'wb') as f:
                pickle.dump(simple_model_info, f)
                
            logger.info(f"✅ 최소 테스트 모델 생성: {model_path}")
            return True
            
        except Exception as e2:
            logger.error(f"❌ Fallback 모델 생성도 실패: {e2}")
            return False
        
    except Exception as e:
        logger.error(f"❌ 모델 생성 실패: {e}")
        return False


def main():
    """메인 함수"""
    
    print("🤖 CI/CD Test Model Creator")
    print("=" * 40)
    
    # 환경 확인
    models_dir = Path("models")
    existing_models = list(models_dir.glob("*forest*.joblib")) if models_dir.exists() else []
    
    if existing_models:
        print(f"📦 기존 모델 발견: {len(existing_models)}개")
        print("   기존 모델이 있으므로 새로 생성하지 않습니다.")
        return True
    
    print("📝 기존 모델이 없습니다. CI/CD용 테스트 모델을 생성합니다.")
    
    # 모델 생성
    success = create_minimal_test_model()
    
    if success:
        print("✅ 테스트 모델 생성 성공!")
    else:
        print("❌ 테스트 모델 생성 실패")
    
    return success


if __name__ == "__main__":
    main()