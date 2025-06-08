"""
2단계: 피처 스토어 및 ML 플랫폼 도구들

이 패키지는 ML 모델 학습을 위한 재사용 가능한 피처 관리 체계를 제공합니다.

주요 모듈:
- engineering: 피처 엔지니어링 로직
- pipeline: 피처 생성 파이프라인
- store: 피처 스토어 구현
- validation: 피처 검증 및 테스트
"""

__version__ = "1.0.0"
__author__ = "MLOps Team"

from .engineering import *
from .pipeline import *
from .store import *
from .validation import *
