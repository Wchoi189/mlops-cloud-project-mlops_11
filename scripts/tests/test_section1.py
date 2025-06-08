#!/usr/bin/env python3
"""
Section 1 (데이터 파이프라인) 테스트 스크립트
Data Pipeline Implementation Test
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_section1():
    """Section 1 구현 테스트"""

    print("🧪 Section 1: 데이터 파이프라인 테스트 시작")
    print("=" * 50)

    # 1. 필요한 파일 및 디렉토리 확인
    print("\n1️⃣ 필요한 파일 및 디렉토리 확인...")

    required_items = [
        ("src/data/data_loader.py", "file"),
        ("scripts/validate_data.py", "file"),
        ("data/", "dir"),
        ("data/raw/", "dir"),
        ("data/processed/", "dir"),
    ]

    missing_items = []
    for item_path, item_type in required_items:
        if item_type == "file" and os.path.isfile(item_path):
            print(f"✅ {item_path}")
        elif item_type == "dir" and os.path.isdir(item_path):
            print(f"✅ {item_path}")
        else:
            print(f"❌ {item_path}")
            missing_items.append(item_path)

    if missing_items:
        print(f"\n❌ 누락된 항목들: {missing_items}")
        print("먼저 Section 1 구현을 완료하세요.")
        return False

    # 2. 필요한 라이브러리 확인
    print("\n2️⃣ 필요한 라이브러리 확인...")

    try:
        import pandas as pd

        print("✅ pandas")
        import requests

        print("✅ requests")
        import gzip

        print("✅ gzip")

    except ImportError as e:
        print(f"❌ 라이브러리 오류: {e}")
        print("필요한 라이브러리를 설치하세요: pip install pandas requests")
        return False

    # 3. 모듈 import 테스트
    print("\n3️⃣ 모듈 import 테스트...")

    try:
        from src.data.data_loader import IMDbDataLoader

        print("✅ IMDbDataLoader 클래스 import 성공")

    except ImportError as e:
        print(f"❌ Import 오류: {e}")
        print("src/data/data_loader.py 파일을 확인하세요.")
        return False

    # 4. 데이터 로더 초기화 테스트
    print("\n4️⃣ 데이터 로더 초기화 테스트...")

    try:
        loader = IMDbDataLoader()
        print("✅ IMDbDataLoader 초기화 성공")

        # 데이터 URL 확인 (실제 구현에 맞게 수정)
        if hasattr(loader, "IMDB_URLS") and loader.IMDB_URLS:
            print(f"✅ IMDB URLs 설정 확인됨")
            # URL 개수만 표시 (너무 길어서)
            print(f"   설정된 데이터셋: {list(loader.IMDB_URLS.keys())}")
        else:
            print("⚠️  IMDB URLs 미설정 - 실제 구현을 확인하세요")

    except Exception as e:
        print(f"❌ 초기화 오류: {e}")
        return False

    # 5. 데이터 다운로드 테스트
    print("\n5️⃣ 데이터 다운로드 기능 테스트...")

    try:
        # 실제 파일명으로 확인 (구현에 맞게)
        expected_files = ["title_basics.tsv.gz", "title_ratings.tsv.gz"]
        existing_files = [f for f in expected_files if os.path.exists(f"data/raw/{f}")]

        if len(existing_files) == len(expected_files):
            print(f"✅ 모든 필요한 데이터 파일 존재: {existing_files}")
            skip_download = True
        else:
            print(f"📥 일부 데이터 파일 누락. 기존 파일: {existing_files}")
            print("다운로드를 시도합니다...")
            skip_download = False

        # 다운로드 메서드 존재 확인
        if hasattr(loader, "download_imdb_file"):
            print("✅ download_imdb_file 메서드 존재")

            if not skip_download:
                print("⏳ 데이터 다운로드 중... (시간이 걸릴 수 있습니다)")
                try:
                    # 구현에 맞는 데이터셋 이름 사용
                    dataset_names = ["title_basics", "title_ratings"]

                    for dataset_name in dataset_names:
                        print(f"   다운로드 중: {dataset_name}")
                        loader.download_imdb_file(dataset_name)

                    print("✅ 데이터 다운로드 완료")
                except Exception as download_error:
                    print(f"⚠️  다운로드 중 오류 발생: {download_error}")
                    print("   네트워크 연결을 확인하거나 나중에 다시 시도하세요.")
                    # 다운로드 실패해도 기존 파일이 있으면 계속 진행
                    if not existing_files:
                        return False
            else:
                print("✅ 기존 데이터 파일 사용")

        else:
            print("❌ download_imdb_file 메서드가 없습니다.")
            print("   실제 구현된 메서드명을 확인하세요.")
            # 기존 파일이 있으면 계속 진행
            if not existing_files:
                return False

    except Exception as e:
        print(f"❌ 다운로드 테스트 오류: {e}")
        return False

    # 6. 데이터 처리 테스트
    print("\n6️⃣ 데이터 처리 테스트...")

    try:
        print("⏳ 영화 데이터셋 생성 중...")
        movies_df = loader.create_movie_dataset()

        if movies_df is not None and len(movies_df) > 0:
            print(f"✅ 영화 데이터셋 생성 성공: {len(movies_df):,}개 행")
            print(f"   컬럼 수: {len(movies_df.columns)}개")
            print(f"   주요 컬럼: {list(movies_df.columns[:5])}...")  # 처음 5개만 표시

            # 기본 통계 확인
            if "averageRating" in movies_df.columns:
                print(f"   평균 평점: {movies_df['averageRating'].mean():.2f}")
                print(
                    f"   평점 범위: {movies_df['averageRating'].min():.1f} ~ {movies_df['averageRating'].max():.1f}"
                )

        else:
            print("❌ 데이터셋 생성 실패 또는 빈 데이터셋")
            return False

    except Exception as e:
        print(f"❌ 데이터 처리 오류: {e}")
        print(f"   오류 상세: {str(e)}")
        return False

    # 7. 데이터 저장 확인
    print("\n7️⃣ 데이터 저장 확인...")

    try:
        processed_file = "data/processed/movies_with_ratings.csv"

        if os.path.exists(processed_file):
            print(f"✅ 처리된 데이터 파일 존재: {processed_file}")

            # 파일 크기 확인
            file_size_mb = os.path.getsize(processed_file) / (1024 * 1024)
            print(f"   파일 크기: {file_size_mb:.1f} MB")

            # 파일 내용 간단 확인
            test_df = pd.read_csv(processed_file, nrows=5)
            print(f"   저장된 컬럼 수: {len(test_df.columns)}개")

        else:
            print(f"⚠️  처리된 데이터 파일이 없습니다: {processed_file}")
            print("   데이터 처리 과정에서 저장이 누락되었을 수 있습니다.")

    except Exception as e:
        print(f"❌ 파일 확인 오류: {e}")

    # 8. 데이터 검증 스크립트 테스트
    print("\n8️⃣ 데이터 검증 스크립트 테스트...")

    try:
        import subprocess

        # validate_data.py 실행
        result = subprocess.run(
            [sys.executable, "scripts/validate_data.py"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=30,
        )

        if result.returncode == 0:
            print("✅ 데이터 검증 스크립트 실행 성공")
            if result.stdout.strip():
                print("   검증 결과 (마지막 몇 줄):")
                lines = result.stdout.strip().split("\n")
                for line in lines[-3:]:  # 마지막 3줄만 표시
                    if line.strip():
                        print(f"   {line}")
        else:
            print(
                f"⚠️  데이터 검증 스크립트 실행 중 문제 발생 (종료코드: {result.returncode})"
            )
            if result.stderr.strip():
                print(f"   오류: {result.stderr.strip()}")

    except subprocess.TimeoutExpired:
        print("⚠️  데이터 검증 스크립트가 시간 초과되었습니다.")
    except Exception as e:
        print(f"❌ 검증 스크립트 테스트 오류: {e}")

    # 9. 전체 파이프라인 상태 확인
    print("\n9️⃣ 전체 파이프라인 상태 확인...")

    # 실제 파일명으로 확인
    pipeline_status = {
        "raw_data_basics": os.path.exists("data/raw/title_basics.tsv.gz"),
        "raw_data_ratings": os.path.exists("data/raw/title_ratings.tsv.gz"),
        "processed_data": os.path.exists("data/processed/movies_with_ratings.csv"),
        "data_loader": True,  # 이미 위에서 확인함
    }

    print("파이프라인 구성요소 상태:")
    for component, status in pipeline_status.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {component.replace('_', ' ')}")

    all_good = all(pipeline_status.values())

    print("\n" + "=" * 50)
    if all_good:
        print("🎉 Section 1 모든 테스트 통과!")
        print("\n📝 다음 단계:")
        print("   1. Section 2 (데이터 전처리) 진행")
        print("   2. 데이터 품질 추가 확인: python scripts/validate_data.py")
        print("   3. 처리된 데이터 확인: head data/processed/movies_with_ratings.csv")
    else:
        print("⚠️  일부 구성요소가 완전하지 않습니다.")
        failed_components = [k for k, v in pipeline_status.items() if not v]
        print(f"   실패한 구성요소: {failed_components}")
        print("   누락된 구성요소를 확인하고 완성하세요.")

    return all_good


def run_manual_commands():
    """원래 수동 명령어들을 실행하는 함수"""

    print("\n🔧 수동 명령어 실행 모드")
    print("=" * 30)

    try:
        print("\n📥 데이터 로드 및 처리...")
        print(
            "실행: from src.data.data_loader import IMDbDataLoader; loader = IMDbDataLoader(); movies_df = loader.create_movie_dataset()"
        )

        from src.data.data_loader import IMDbDataLoader

        loader = IMDbDataLoader()
        movies_df = loader.create_movie_dataset()

        if movies_df is not None:
            print(f"✅ 데이터 처리 완료: {len(movies_df):,}개 영화")
            return True
        else:
            print("❌ 데이터 처리 실패")
            return False

    except Exception as e:
        print(f"❌ 데이터 로드 오류: {e}")
        return False


def run_validation_only():
    """데이터 검증만 실행하는 함수"""

    print("\n🔍 데이터 검증 실행")
    print("=" * 25)

    try:
        print("실행: python scripts/validate_data.py")

        import subprocess

        result = subprocess.run(
            [sys.executable, "scripts/validate_data.py"], cwd=project_root
        )

        if result.returncode == 0:
            print("✅ 데이터 검증 완료")
            return True
        else:
            print("⚠️  데이터 검증에서 경고 또는 오류 발생")
            return False

    except Exception as e:
        print(f"❌ 데이터 검증 오류: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Section 1 데이터 파이프라인 테스트")
    parser.add_argument(
        "--manual", action="store_true", help="원래 수동 명령어들만 실행"
    )
    parser.add_argument(
        "--validate-only", action="store_true", help="데이터 검증만 실행"
    )

    args = parser.parse_args()

    if args.manual:
        success = run_manual_commands()
    elif args.validate_only:
        success = run_validation_only()
    else:
        success = test_section1()

    sys.exit(0 if success else 1)
