#!/usr/bin/env python3
"""
Section 2 (데이터 전처리 파이프라인 구현) 테스트 스크립트
Data Preprocessing Pipeline Test
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_section2():
    """Section 2 전처리 파이프라인 테스트"""

    print("🧪 Section 2: 데이터 전처리 파이프라인 테스트 시작")
    print("=" * 50)

    try:
        # 1. 필요한 파일 확인
        print("1️⃣ 필요한 파일 확인...")

        required_files = [
            "src/data/preprocessing.py",
            "data/processed/movies_with_ratings.csv",
        ]

        for file_path in required_files:
            if os.path.exists(file_path):
                print(f"✅ {file_path}")
            else:
                print(f"❌ {file_path} 누락")
                print(f"먼저 {file_path}를 생성하세요.")
                return False

        # 2. 모듈 import
        print("\n2️⃣ 모듈 import...")
        from src.data.preprocessing import IMDbPreprocessor

        print("✅ IMDbPreprocessor import 성공")

        # 3. 전처리기 초기화
        print("\n3️⃣ 전처리기 초기화...")
        p = IMDbPreprocessor()
        print("✅ IMDbPreprocessor 초기화 성공")

        # 4. 데이터 로드
        print("\n4️⃣ 데이터 로드...")
        df = p.load_data()
        if df is not None and len(df) > 0:
            print(f"✅ 데이터 로드 성공: {len(df):,}개 행")
        else:
            print("❌ 데이터 로드 실패")
            return False

        # 5. 전처리 실행
        print("\n5️⃣ 전처리 실행...")
        X, y, features = p.fit_transform(df)

        if X is not None and y is not None and features:
            print("✅ 전처리 완료!")
            print(f"   피처 수: {len(features)}")
            print(f"   데이터 크기: {X.shape}")
            print(f"   타겟 크기: {y.shape}")
            print(f"   피처 목록: {features}")
        else:
            print("❌ 전처리 실패")
            return False

        # 6. 전처리기 저장
        print("\n6️⃣ 전처리기 저장...")
        save_result = p.save_preprocessor()
        if save_result:
            print("✅ 전처리기 저장 완료")
        else:
            print("⚠️  전처리기 저장 실패 (하지만 계속 진행)")

        print("\n" + "=" * 50)
        print("🎉 Section 2 테스트 완료!")
        print("\n📝 결과 요약:")
        print(f"   📊 처리된 데이터: {X.shape[0]:,}개 샘플")
        print(f"   🔢 피처 개수: {len(features)}개")
        print(f"   📋 피처 목록: {', '.join(features)}")

        return True

    except ImportError as e:
        print(f"❌ Import 오류: {e}")
        print("src/data/preprocessing.py 파일이 있는지 확인하세요.")
        return False

    except Exception as e:
        print(f"❌ 실행 중 오류: {e}")
        print(f"오류 세부사항: {type(e).__name__}: {str(e)}")
        return False


def run_simple_test():
    """당신의 원래 버전 (간단 버전)"""

    print("🔧 간단 테스트 모드")
    print("=" * 25)

    try:
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

        return True

    except Exception as e:
        print(f"오류 발생: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Section 2 데이터 전처리 테스트")
    parser.add_argument(
        "--simple", action="store_true", help="간단 테스트 모드 (원래 버전)"
    )

    args = parser.parse_args()

    if args.simple:
        success = run_simple_test()
    else:
        success = test_section2()

    sys.exit(0 if success else 1)
