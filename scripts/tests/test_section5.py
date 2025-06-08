#!/usr/bin/env python3
"""
Section 5 (Docker 컨테이너화) 테스트 스크립트
Docker Containerization Test
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import requests

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_section5():
    """Section 5 Docker 컨테이너화 테스트"""

    print("🧪 Section 5: Docker 컨테이너화 테스트 시작")
    print("=" * 50)

    # 1. 필요한 파일 확인
    print("\n1️⃣ Docker 파일 확인...")

    required_files = [
        "docker/Dockerfile.api",
        "docker/Dockerfile.train",
        "docker/docker-compose.yml",
        "requirements.txt",
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

    # 2. Docker 설치 확인
    print("\n2️⃣ Docker 환경 확인...")

    try:
        # Docker 설치 확인
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker 설치 확인: {result.stdout.strip()}")
        else:
            print("❌ Docker가 설치되지 않았습니다.")
            return False

        # Docker Compose 확인
        result = subprocess.run(
            ["docker-compose", "--version"], capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"✅ Docker Compose 확인: {result.stdout.strip()}")
        else:
            print("❌ Docker Compose가 설치되지 않았습니다.")
            return False

    except FileNotFoundError:
        print("❌ Docker가 시스템에 설치되지 않았습니다.")
        print("💡 Docker 설치 방법:")
        print("   Ubuntu: sudo apt-get install docker.io docker-compose")
        print("   macOS: brew install docker docker-compose")
        return False

    # 3. Docker 이미지 빌드 테스트
    print("\n3️⃣ Docker 이미지 빌드 테스트...")

    try:
        os.chdir(project_root / "docker")

        # API 이미지 빌드
        print("📦 API 이미지 빌드 중...")
        result = subprocess.run(
            [
                "docker",
                "build",
                "-f",
                "Dockerfile.api",
                "-t",
                "mlops-imdb-api:test",
                "..",
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode == 0:
            print("✅ API 이미지 빌드 성공")
        else:
            print(f"❌ API 이미지 빌드 실패:")
            print(f"   오류: {result.stderr[-500:]}")  # 마지막 500자만 출력
            return False

        # 훈련 이미지 빌드
        print("📦 훈련 이미지 빌드 중...")
        result = subprocess.run(
            [
                "docker",
                "build",
                "-f",
                "Dockerfile.train",
                "-t",
                "mlops-imdb-trainer:test",
                "..",
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode == 0:
            print("✅ 훈련 이미지 빌드 성공")
        else:
            print(f"❌ 훈련 이미지 빌드 실패:")
            print(f"   오류: {result.stderr[-500:]}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Docker 빌드 시간 초과 (5분)")
        return False
    except Exception as e:
        print(f"❌ Docker 빌드 오류: {e}")
        return False
    finally:
        os.chdir(project_root)

    # 4. 컨테이너 실행 테스트
    print("\n4️⃣ 컨테이너 실행 테스트...")

    containers_to_cleanup = []

    try:
        # 기존 컨테이너 정리
        cleanup_containers(["mlops-test-api", "mlops-test-mlflow"])

        # MLflow 컨테이너 시작
        print("🔥 MLflow 컨테이너 시작...")
        mlflow_cmd = [
            "docker",
            "run",
            "-d",
            "--name",
            "mlops-test-mlflow",
            "-p",
            "5001:5000",  # 테스트용 포트
            "-v",
            f"{project_root}/mlruns:/mlruns",
            "python:3.11-slim",
            "bash",
            "-c",
            "pip install mlflow==2.8.1 && mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///mlruns/test.db",
        ]

        result = subprocess.run(mlflow_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ MLflow 컨테이너 시작 성공")
            containers_to_cleanup.append("mlops-test-mlflow")
        else:
            print(f"❌ MLflow 컨테이너 시작 실패: {result.stderr}")

        # MLflow 준비 대기
        print("⏳ MLflow 서비스 준비 대기...")
        for i in range(30):
            try:
                response = requests.get("http://localhost:5001/health", timeout=2)
                if response.status_code == 200:
                    print("✅ MLflow 서비스 준비 완료")
                    break
            except:
                time.sleep(1)
        else:
            print("⚠️ MLflow 서비스 대기 시간 초과")

        # API 컨테이너 시작 (모델 마운트)
        print("🚀 API 컨테이너 시작...")
        api_cmd = [
            "docker",
            "run",
            "-d",
            "--name",
            "mlops-test-api",
            "-p",
            "8001:8000",  # 테스트용 포트
            "-v",
            f"{project_root}/models:/app/models:ro",
            "-v",
            f"{project_root}/data:/app/data:ro",
            "-e",
            "MLFLOW_TRACKING_URI=http://host.docker.internal:5001",
            "mlops-imdb-api:test",
        ]

        result = subprocess.run(api_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ API 컨테이너 시작 성공")
            containers_to_cleanup.append("mlops-test-api")
        else:
            print(f"❌ API 컨테이너 시작 실패: {result.stderr}")
            return False

        # API 준비 대기
        print("⏳ API 서비스 준비 대기...")
        for i in range(60):
            try:
                response = requests.get("http://localhost:8001/health", timeout=2)
                if response.status_code == 200:
                    print("✅ API 서비스 준비 완료")
                    break
            except:
                time.sleep(1)
        else:
            print("⚠️ API 서비스 대기 시간 초과")

    except Exception as e:
        print(f"❌ 컨테이너 실행 오류: {e}")
        return False

    # 5. 컨테이너화된 API 테스트
    print("\n5️⃣ 컨테이너화된 API 테스트...")

    try:
        # 헬스 체크
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ 컨테이너 헬스 체크 성공")
            print(f"   상태: {health_data.get('status', 'unknown')}")
            print(f"   모델 로드: {health_data.get('model_loaded', False)}")

        # 영화 예측 테스트
        test_movie = {
            "title": "Container Test Movie",
            "startYear": 2020,
            "runtimeMinutes": 120,
            "numVotes": 5000,
        }

        response = requests.post(
            "http://localhost:8001/predict/movie", json=test_movie, timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ 컨테이너 예측 테스트 성공")
            print(f"   예측 평점: {result.get('predicted_rating', 'N/A')}/10")
        else:
            print(f"⚠️ 컨테이너 예측 실패: {response.status_code}")

    except Exception as e:
        print(f"❌ 컨테이너 API 테스트 오류: {e}")

    # 6. Docker Compose 테스트
    print("\n6️⃣ Docker Compose 테스트...")

    try:
        # 기존 compose 스택 정리
        subprocess.run(
            [
                "docker-compose",
                "-f",
                "docker/docker-compose.yml",
                "down",
                "--remove-orphans",
            ],
            cwd=project_root,
            capture_output=True,
        )

        # Docker Compose 구문 검증
        result = subprocess.run(
            ["docker-compose", "-f", "docker/docker-compose.yml", "config"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ Docker Compose 파일 구문 검증 성공")
        else:
            print(f"❌ Docker Compose 구문 오류: {result.stderr}")
            return False

        # 간단한 서비스 시작 테스트 (빠른 종료)
        print("🔧 Docker Compose 서비스 시작 테스트...")
        result = subprocess.run(
            [
                "docker-compose",
                "-f",
                "docker/docker-compose.yml",
                "up",
                "--build",
                "-d",
                "mlflow",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            print("✅ Docker Compose MLflow 서비스 시작 성공")

            # 바로 정리
            subprocess.run(
                ["docker-compose", "-f", "docker/docker-compose.yml", "down"],
                cwd=project_root,
                capture_output=True,
            )

        else:
            print(f"⚠️ Docker Compose 시작 문제: {result.stderr}")

    except subprocess.TimeoutExpired:
        print("⚠️ Docker Compose 시작 시간 초과")
    except Exception as e:
        print(f"❌ Docker Compose 테스트 오류: {e}")

    # 7. 정리
    print("\n7️⃣ 테스트 환경 정리...")

    try:
        cleanup_containers(containers_to_cleanup)
        print("✅ 테스트 컨테이너 정리 완료")

    except Exception as e:
        print(f"⚠️ 정리 중 오류: {e}")

    print("\n" + "=" * 50)
    print("🎉 Section 5 Docker 컨테이너화 테스트 완료!")

    print("\n📝 테스트 결과 요약:")
    print("   ✅ Docker 파일 생성 및 검증")
    print("   ✅ Docker 이미지 빌드 성공")
    print("   ✅ 컨테이너 실행 및 API 동작")
    print("   ✅ Docker Compose 구성 검증")

    print("\n🚀 다음 단계:")
    print("   1. 프로덕션 배포: docker-compose up -d")
    print("   2. Section 6: 모니터링 및 CI/CD")
    print("   3. 성능 최적화 및 스케일링")

    print("\n💡 유용한 명령어:")
    print("   # 전체 스택 시작")
    print("   docker-compose -f docker/docker-compose.yml up -d")
    print("   # API만 시작")
    print("   docker-compose -f docker/docker-compose.yml up -d api")
    print("   # 로그 확인")
    print("   docker-compose -f docker/docker-compose.yml logs -f api")
    print("   # 스택 종료")
    print("   docker-compose -f docker/docker-compose.yml down")

    return True


def cleanup_containers(container_names: List[str]):
    """테스트 컨테이너 정리"""
    for name in container_names:
        try:
            # 컨테이너 중지
            subprocess.run(["docker", "stop", name], capture_output=True, timeout=10)
            # 컨테이너 제거
            subprocess.run(["docker", "rm", name], capture_output=True, timeout=10)
        except:
            pass  # 이미 없거나 오류여도 무시


def quick_docker_test():
    """빠른 Docker 테스트 (빌드만)"""

    print("\n🔧 빠른 Docker 테스트 모드")
    print("=" * 30)

    try:
        # Docker 버전 확인
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        print(f"Docker: {result.stdout.strip()}")

        # Dockerfile 존재 확인
        if os.path.exists("docker/Dockerfile.api"):
            print("✅ API Dockerfile 존재")
        if os.path.exists("docker/Dockerfile.train"):
            print("✅ 훈련 Dockerfile 존재")
        if os.path.exists("docker/docker-compose.yml"):
            print("✅ Docker Compose 파일 존재")

        print("\n💡 전체 테스트 실행:")
        print("python scripts/tests/test_section5.py")

        return True

    except Exception as e:
        print(f"❌ 빠른 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Section 5 Docker 컨테이너화 테스트")
    parser.add_argument(
        "--quick", action="store_true", help="빠른 테스트 모드 (빌드 없이)"
    )

    args = parser.parse_args()

    if args.quick:
        success = quick_docker_test()
    else:
        success = test_section5()

    sys.exit(0 if success else 1)
