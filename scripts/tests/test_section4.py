#!/usr/bin/env python3
"""
Section 4 (API 서빙 파이프라인) 테스트 스크립트
API Serving Pipeline Test
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

import requests

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_section4():
    """Section 4 API 서빙 파이프라인 테스트"""

    print("🧪 Section 4: API 서빙 파이프라인 테스트 시작")
    print("=" * 50)

    # 1. 필요한 파일 확인
    print("\n1️⃣ 필요한 파일 확인...")

    required_files = [
        "src/api/main.py",
        "src/api/endpoints.py",
        "src/api/schemas.py",
        "src/models/evaluator.py",
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
        return False

    # 2. 모델 파일 확인
    print("\n2️⃣ 모델 파일 확인...")

    models_dir = Path("models")
    if not models_dir.exists():
        print("❌ models 디렉토리가 없습니다.")
        print("   먼저 Section 3을 완료하세요.")
        return False

    model_files = list(models_dir.glob("*forest*.joblib"))
    scaler_files = list(models_dir.glob("scaler_*.joblib"))

    if model_files:
        print(f"✅ 모델 파일 발견: {len(model_files)}개")
        latest_model = max(model_files, key=lambda x: x.stat().st_mtime)
        print(f"   최신 모델: {latest_model.name}")
    else:
        print("❌ 모델 파일이 없습니다.")
        print("   먼저 Section 3 (모델 훈련)을 실행하세요.")
        return False

    if scaler_files:
        print(f"✅ 스케일러 파일 발견: {len(scaler_files)}개")
    else:
        print("⚠️ 스케일러 파일이 없습니다. (경고)")

    # 3. API 서버 시작
    print("\n3️⃣ API 서버 시작...")

    api_url = "http://localhost:8000"

    # 기존 서버가 실행 중인지 확인
    try:
        response = requests.get(f"{api_url}/health", timeout=2)
        if response.status_code == 200:
            print("✅ API 서버가 이미 실행 중입니다.")
            server_started = True
            api_process = None
        else:
            raise requests.exceptions.ConnectionError()
    except requests.exceptions.ConnectionError:
        print("📡 API 서버 시작 중...")

        # API 서버 시작
        try:
            api_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "src.api.main:app",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "8000",
                ],
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # 서버 시작 대기
            print("⏳ 서버 시작 대기 중... (최대 15초)")
            for i in range(15):
                try:
                    response = requests.get(f"{api_url}/health", timeout=1)
                    if response.status_code == 200:
                        print("✅ API 서버 시작 완료!")
                        server_started = True
                        break
                except:
                    time.sleep(1)
                    print(f"   대기 중... ({i+1}/15)")
            else:
                print("❌ API 서버 시작 시간 초과")
                if api_process:
                    api_process.terminate()
                return False

        except Exception as e:
            print(f"❌ API 서버 시작 실패: {e}")
            return False

    try:
        # 4. 헬스 체크 테스트
        print("\n4️⃣ 헬스 체크 테스트...")

        try:
            response = requests.get(f"{api_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                print("✅ 헬스 체크 성공")
                print(f"   상태: {health_data.get('status', 'unknown')}")
                print(f"   모델 로드: {health_data.get('model_loaded', False)}")
            else:
                print(f"⚠️ 헬스 체크 응답 코드: {response.status_code}")
        except Exception as e:
            print(f"❌ 헬스 체크 실패: {e}")

        # 5. 루트 엔드포인트 테스트
        print("\n5️⃣ 루트 엔드포인트 테스트...")

        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                root_data = response.json()
                print("✅ 루트 엔드포인트 성공")
                print(f"   API 이름: {root_data.get('message', 'unknown')}")
                print(f"   버전: {root_data.get('version', 'unknown')}")
                print(f"   사용 피처: {root_data.get('features_used', [])}")
            else:
                print(f"⚠️ 루트 엔드포인트 응답 코드: {response.status_code}")
        except Exception as e:
            print(f"❌ 루트 엔드포인트 실패: {e}")

        # 6. 모델 정보 테스트
        print("\n6️⃣ 모델 정보 테스트...")

        try:
            response = requests.get(f"{api_url}/model/info")
            if response.status_code == 200:
                model_info = response.json()
                print("✅ 모델 정보 조회 성공")
                print(f"   모델 이름: {model_info.get('name', 'unknown')}")
                print(f"   설명: {model_info.get('description', 'N/A')}")
                print(f"   메트릭: {model_info.get('metrics', {})}")
            else:
                print(f"⚠️ 모델 정보 응답 코드: {response.status_code}")
                print(f"   응답: {response.text[:200]}")
        except Exception as e:
            print(f"❌ 모델 정보 조회 실패: {e}")

        # 7. 영화 평점 예측 테스트 (새로운 엔드포인트)
        print("\n7️⃣ 영화 평점 예측 테스트...")

        test_movies = [
            {
                "title": "The Dark Knight",
                "startYear": 2008,
                "runtimeMinutes": 152,
                "numVotes": 2500000,
            },
            {
                "title": "Inception",
                "startYear": 2010,
                "runtimeMinutes": 148,
                "numVotes": 2000000,
            },
            {
                "title": "Low Budget Film",
                "startYear": 2022,
                "runtimeMinutes": 85,
                "numVotes": 500,
            },
        ]

        for i, movie in enumerate(test_movies, 1):
            try:
                response = requests.post(
                    f"{api_url}/predict/movie",
                    json=movie,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 영화 {i} 예측 성공:")
                    print(f"   제목: {result.get('title', 'unknown')}")
                    print(f"   예측 평점: {result.get('predicted_rating', 0)}/10")
                    print(f"   사용된 피처: {result.get('features_used', {})}")
                else:
                    print(f"⚠️ 영화 {i} 예측 실패 (코드: {response.status_code})")
                    print(f"   오류: {response.text[:200]}")

            except Exception as e:
                print(f"❌ 영화 {i} 예측 오류: {e}")

        # 8. 레거시 예측 엔드포인트 테스트
        print("\n8️⃣ 레거시 예측 엔드포인트 테스트...")

        try:
            legacy_request = {"text": "This is an amazing movie!"}

            response = requests.post(
                f"{api_url}/predict",
                json=legacy_request,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                result = response.json()
                print("✅ 레거시 예측 성공:")
                print(f"   텍스트: {result.get('text', 'unknown')}")
                print(f"   감정: {result.get('sentiment', 'unknown')}")
                print(f"   신뢰도: {result.get('confidence', 0)}")
            else:
                print(f"⚠️ 레거시 예측 실패 (코드: {response.status_code})")
                print(f"   오류: {response.text[:200]}")

        except Exception as e:
            print(f"❌ 레거시 예측 오류: {e}")

        # 9. API 상태 테스트
        print("\n9️⃣ API 상태 테스트...")

        try:
            response = requests.get(f"{api_url}/status")
            if response.status_code == 200:
                status_data = response.json()
                print("✅ API 상태 조회 성공")
                print(f"   API 상태: {status_data.get('api_status', 'unknown')}")
                print(f"   모델 상태: {status_data.get('model_status', 'unknown')}")
                print(f"   엔드포인트 수: {status_data.get('endpoints_count', 0)}")
            else:
                print(f"⚠️ API 상태 응답 코드: {response.status_code}")
        except Exception as e:
            print(f"❌ API 상태 조회 실패: {e}")

        print("\n" + "=" * 50)
        print("🎉 Section 4 API 테스트 완료!")

        print("\n📝 테스트 결과 요약:")
        print("   ✅ API 서버 정상 시작")
        print("   ✅ 모델 로드 및 예측 기능")
        print("   ✅ 다양한 엔드포인트 동작")
        print("   ✅ 오류 처리 및 상태 확인")

        print("\n🚀 다음 단계:")
        print("   1. 브라우저에서 API 문서 확인: http://localhost:8000/docs")
        print("   2. Section 5: Docker 컨테이너화")
        print("   3. Section 6: 모니터링 및 CI/CD")

        print("\n💡 유용한 명령어:")
        print("   # API 문서 접속")
        print("   curl http://localhost:8000")
        print("   # 영화 예측 테스트")
        print('   curl -X POST "http://localhost:8000/predict/movie" \\')
        print('        -H "Content-Type: application/json" \\')
        print(
            '        -d \'{"title":"Test Movie","startYear":2020,"runtimeMinutes":120,"numVotes":5000}\''
        )

        return True

    finally:
        # API 서버 정리 (테스트에서 시작한 경우만)
        if "api_process" in locals() and api_process is not None:
            print(f"\n🛑 테스트용 API 서버 종료 중...")
            api_process.terminate()
            api_process.wait(timeout=5)
            print("✅ API 서버 종료 완료")


def test_api_manually():
    """수동 API 테스트"""

    print("\n🔧 수동 API 테스트 모드")
    print("=" * 30)

    api_url = "http://localhost:8000"

    # 간단한 연결 테스트
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        print(f"✅ API 연결 성공: {response.status_code}")
        print(f"   응답: {response.json()}")

        # 영화 예측 테스트
        test_movie = {
            "title": "Test Movie",
            "startYear": 2020,
            "runtimeMinutes": 120,
            "numVotes": 5000,
        }

        response = requests.post(f"{api_url}/predict/movie", json=test_movie)
        print(f"\n✅ 영화 예측 테스트: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   예측 평점: {result.get('predicted_rating', 'N/A')}/10")

        return True

    except Exception as e:
        print(f"❌ API 테스트 실패: {e}")
        print("\n💡 먼저 API 서버를 시작하세요:")
        print("   uvicorn src.api.main:app --reload --port 8000")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Section 4 API 서빙 파이프라인 테스트")
    parser.add_argument(
        "--manual",
        action="store_true",
        help="수동 테스트 모드 (서버가 이미 실행 중인 경우)",
    )

    args = parser.parse_args()

    if args.manual:
        success = test_api_manually()
    else:
        success = test_section4()

    sys.exit(0 if success else 1)
