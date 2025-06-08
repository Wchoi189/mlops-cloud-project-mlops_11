#!/usr/bin/env python3
"""
Docker 빠른 시작 스크립트
Quick Docker deployment and testing script
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

import requests

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
os.chdir(project_root)


def run_command(cmd, timeout=None, cwd=None):
    """명령어 실행 헬퍼"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=cwd
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"


def check_docker():
    """Docker 설치 및 실행 상태 확인"""
    print("🔍 Docker 환경 확인 중...")

    # Docker 설치 확인
    success, stdout, stderr = run_command("docker --version")
    if not success:
        print("❌ Docker가 설치되지 않았습니다.")
        print("💡 Docker 설치: https://docs.docker.com/get-docker/")
        return False

    print(f"✅ {stdout.strip()}")

    # Docker Compose 확인
    success, stdout, stderr = run_command("docker-compose --version")
    if not success:
        print("❌ Docker Compose가 설치되지 않았습니다.")
        return False

    print(f"✅ {stdout.strip()}")

    # Docker 데몬 실행 확인
    success, stdout, stderr = run_command("docker info")
    if not success:
        print("❌ Docker 데몬이 실행되지 않았습니다.")
        print("💡 Docker 시작: sudo systemctl start docker")
        return False

    print("✅ Docker 데몬 실행 중")
    return True


def build_images():
    """Docker 이미지 빌드"""
    print("\n🔨 Docker 이미지 빌드 중...")

    # API 이미지 빌드
    print("📦 API 이미지 빌드...")
    success, stdout, stderr = run_command(
        "docker build -f docker/Dockerfile.api -t mlops-imdb-api:latest .", timeout=600
    )

    if not success:
        print(f"❌ API 이미지 빌드 실패: {stderr[-200:]}")
        return False

    print("✅ API 이미지 빌드 완료")

    # 훈련 이미지 빌드
    print("📦 훈련 이미지 빌드...")
    success, stdout, stderr = run_command(
        "docker build -f docker/Dockerfile.train -t mlops-imdb-trainer:latest .",
        timeout=600,
    )

    if not success:
        print(f"❌ 훈련 이미지 빌드 실패: {stderr[-200:]}")
        return False

    print("✅ 훈련 이미지 빌드 완료")
    return True


def start_services():
    """Docker Compose로 서비스 시작"""
    print("\n🚀 MLOps 서비스 시작 중...")

    # 기존 서비스 정리
    run_command("cd docker && docker-compose down --remove-orphans")

    # 서비스 시작
    success, stdout, stderr = run_command(
        "cd docker && docker-compose up -d", timeout=180
    )

    if not success:
        print(f"❌ 서비스 시작 실패: {stderr}")
        return False

    print("✅ 서비스 시작 완료")
    return True


def wait_for_services():
    """서비스 준비 대기"""
    print("\n⏳ 서비스 준비 대기 중...")

    services = {
        "MLflow": "http://localhost:5000/health",
        "API": "http://localhost:8000/health",
    }

    for service_name, url in services.items():
        print(f"🔄 {service_name} 서비스 대기...")

        for i in range(60):  # 최대 60초 대기
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    print(f"✅ {service_name} 서비스 준비 완료")
                    break
            except:
                pass

            time.sleep(1)
            if i % 10 == 9:  # 10초마다 진행상황 출력
                print(f"   대기 중... ({i+1}/60초)")
        else:
            print(f"⚠️ {service_name} 서비스 대기 시간 초과")
            return False

    return True


def test_api():
    """API 기능 테스트"""
    print("\n🧪 API 기능 테스트 중...")

    test_cases = [
        {"name": "헬스 체크", "url": "http://localhost:8000/health", "method": "GET"},
        {
            "name": "모델 정보",
            "url": "http://localhost:8000/model/info",
            "method": "GET",
        },
        {
            "name": "영화 예측",
            "url": "http://localhost:8000/predict/movie",
            "method": "POST",
            "data": {
                "title": "The Dark Knight",
                "startYear": 2008,
                "runtimeMinutes": 152,
                "numVotes": 2500000,
            },
        },
    ]

    for test in test_cases:
        print(f"🔧 {test['name']} 테스트...")

        try:
            if test["method"] == "GET":
                response = requests.get(test["url"], timeout=10)
            else:
                response = requests.post(
                    test["url"], json=test.get("data", {}), timeout=10
                )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ {test['name']} 성공")

                # 특별한 결과 출력
                if test["name"] == "영화 예측":
                    rating = result.get("predicted_rating", "N/A")
                    print(f"   예측 평점: {rating}/10")
                elif test["name"] == "헬스 체크":
                    status = result.get("status", "unknown")
                    model_loaded = result.get("model_loaded", False)
                    print(f"   상태: {status}, 모델 로드: {model_loaded}")

            else:
                print(f"⚠️ {test['name']} 실패: HTTP {response.status_code}")

        except Exception as e:
            print(f"❌ {test['name']} 오류: {str(e)}")

    return True


def show_status():
    """서비스 상태 표시"""
    print("\n📊 서비스 상태:")

    # Docker Compose 상태
    success, stdout, stderr = run_command("cd docker && docker-compose ps")
    if success:
        print(stdout)

    print("\n🔗 접속 URL:")
    print("   📡 API 서비스: http://localhost:8000")
    print("   📚 API 문서: http://localhost:8000/docs")
    print("   📈 MLflow UI: http://localhost:5000")

    print("\n💡 유용한 명령어:")
    print("   # 로그 확인")
    print("   cd docker && docker-compose logs -f")
    print("   # 서비스 중지")
    print("   cd docker && docker-compose down")
    print("   # 서비스 재시작")
    print("   cd docker && docker-compose restart")


def main():
    """메인 실행 함수"""
    print("🚀 MLOps IMDB Docker 빠른 시작")
    print("=" * 40)

    # 1. Docker 환경 확인
    if not check_docker():
        return False

    # 2. 이미지 빌드
    if not build_images():
        return False

    # 3. 서비스 시작
    if not start_services():
        return False

    # 4. 서비스 준비 대기
    if not wait_for_services():
        print("⚠️ 일부 서비스가 완전히 준비되지 않았을 수 있습니다.")

    # 5. API 테스트
    test_api()

    # 6. 상태 표시
    show_status()

    print("\n🎉 Docker 배포 완료!")
    print("📝 다음 단계: 브라우저에서 http://localhost:8000/docs 접속")

    return True


def stop_services():
    """서비스 중지"""
    print("🛑 MLOps 서비스 중지 중...")

    success, stdout, stderr = run_command("cd docker && docker-compose down")

    if success:
        print("✅ 서비스 중지 완료")
    else:
        print(f"❌ 서비스 중지 실패: {stderr}")

    return success


def quick_test():
    """빠른 테스트 (빌드 없이)"""
    print("🔧 빠른 Docker 테스트")
    print("=" * 25)

    if not check_docker():
        return False

    # 기존 서비스 상태 확인
    success, stdout, stderr = run_command("cd docker && docker-compose ps")
    if success and "Up" in stdout:
        print("✅ 서비스가 이미 실행 중입니다.")
        test_api()
        show_status()
    else:
        print("📦 서비스가 실행되지 않았습니다.")
        print("💡 전체 시작: python scripts/docker_quick_start.py")

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MLOps Docker 빠른 시작")
    parser.add_argument("--stop", action="store_true", help="서비스 중지")
    parser.add_argument("--test", action="store_true", help="빠른 테스트 (빌드 없이)")

    args = parser.parse_args()

    try:
        if args.stop:
            success = stop_services()
        elif args.test:
            success = quick_test()
        else:
            success = main()

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⏹️ 사용자에 의해 중단됨")
        sys.exit(1)
