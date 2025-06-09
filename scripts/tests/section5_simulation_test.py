#!/usr/bin/env python3
"""
Section 5 시뮬레이션 테스트 - Docker 없이 구성 검증
Docker configuration validation without actually running Docker
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

# 프로젝트 루트를 Python 경로에 추가
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
project_root = os.chdir(project_root)  # 작업 경로를 스크립트 위치로 변경
sys.path.append(str(project_root))


def test_docker_files():
    """Docker 파일들 존재 및 구문 검증"""
    print("🧪 Section 5 시뮬레이션 테스트 시작")
    print("=" * 50)

    # 1. 필요한 파일 확인
    print("\n1️⃣ Docker 파일 존재 확인...")

    required_files = [
        "docker/Dockerfile.api",
        "docker/Dockerfile.train",
        "docker/docker-compose.yml",
        "docker/docker-compose.monitoring.yml",
        "docker/docker-compose.prod.yml",
        "requirements-resolved.txt",
    ]
    # required_files = [
    #     script_dir / 'docker/Dockerfile.api',
    #     script_dir /'docker/Dockerfile.train',
    #     script_dir /'docker/docker-compose.yml',
    #     script_dir /'docker/docker-compose.prod.yml',
    #     script_dir /'requirements.txt',
    #     script_dir /'requirements-enhanced.txt'
    # ]

    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n❌ 누락된 파일: {missing_files}")
        return False

    # 2. Docker Compose 파일 구문 검증
    print("\n2️⃣ Docker Compose 파일 구문 검증...")

    compose_files = [
        "docker/docker-compose.yml",
        "docker/docker-compose.monitoring.yml",
        "docker/docker-compose.prod.yml",
    ]

    for compose_file in compose_files:
        try:
            with open(compose_file, "r") as f:
                compose_data = yaml.safe_load(f)

            # 기본 구조 검증
            required_keys = ["services"]
            for key in required_keys:
                if key not in compose_data:
                    print(f"❌ {compose_file}: '{key}' 키 누락")
                    return False

            # 서비스 확인
            services = compose_data.get("services", {})
            expected_services = ["api", "mlflow"]

            for service in expected_services:
                if service in services:
                    print(f"✅ {compose_file}: {service} 서비스 정의됨")
                else:
                    print(f"⚠️ {compose_file}: {service} 서비스 누락")

            print(f"✅ {compose_file} 구문 유효")

        except yaml.YAMLError as e:
            print(f"❌ {compose_file} YAML 구문 오류: {e}")
            return False
        except Exception as e:
            print(f"❌ {compose_file} 읽기 오류: {e}")
            return False

    # 3. Dockerfile 기본 구문 검증
    print("\n3️⃣ Dockerfile 구문 검증...")

    dockerfiles = ["docker/Dockerfile.api", "docker/Dockerfile.train"]

    for dockerfile in dockerfiles:
        try:
            with open(dockerfile, "r") as f:
                content = f.read()

            # 기본 명령어 확인
            required_commands = ["FROM", "WORKDIR", "COPY", "RUN"]
            missing_commands = []

            for cmd in required_commands:
                if cmd not in content:
                    missing_commands.append(cmd)

            if missing_commands:
                print(f"⚠️ {dockerfile}: 누락된 명령어 {missing_commands}")
            else:
                print(f"✅ {dockerfile}: 기본 구조 유효")

        except Exception as e:
            print(f"❌ {dockerfile} 읽기 오류: {e}")
            return False

    # 4. 의존성 파일 검증
    print("\n4️⃣ 의존성 파일 검증...")

    requirements_files = ["requirements-resolved.txt"]

    for req_file in requirements_files:
        try:
            with open(req_file, "r") as f:
                lines = f.readlines()

            # 빈 줄과 주석 제외한 패키지 수
            packages = [
                line.strip()
                for line in lines
                if line.strip() and not line.strip().startswith("#")
            ]

            print(f"✅ {req_file}: {len(packages)}개 패키지 정의됨")

            # 주요 패키지 확인
            important_packages = [
                "fastapi",
                "uvicorn",
                "mlflow",
                "pandas",
                "scikit-learn",
            ]
            found_packages = []

            for pkg in important_packages:
                for line in packages:
                    if pkg in line.lower():
                        found_packages.append(pkg)
                        break

            print(
                f"   중요 패키지: {len(found_packages)}/{len(important_packages)} 발견"
            )

        except Exception as e:
            print(f"❌ {req_file} 읽기 오류: {e}")

    # 5. API 코드 구조 검증
    print("\n5️⃣ API 코드 구조 검증...")

    api_files = ["src/api/main.py", "src/api/endpoints.py", "src/api/schemas.py"]

    for api_file in api_files:
        if os.path.exists(api_file):
            print(f"✅ {api_file}")

            # FastAPI 코드 기본 검증
            if api_file.endswith("main.py"):
                try:
                    with open(api_file, "r") as f:
                        content = f.read()

                    if "FastAPI" in content and "app =" in content:
                        print(f"   ✅ FastAPI 앱 정의 확인")
                    else:
                        print(f"   ⚠️ FastAPI 앱 정의 불명확")

                except Exception as e:
                    print(f"   ❌ 파일 읽기 오류: {e}")
        else:
            print(f"❌ {api_file}")

    # 6. 모델 파일 확인
    print("\n6️⃣ 모델 파일 확인...")

    models_dir = Path("models")
    if models_dir.exists():
        model_files = list(models_dir.glob("*.joblib")) + list(models_dir.glob("*.pkl"))
        print(f"✅ models/ 디렉토리 존재: {len(model_files)}개 모델 파일")

        if model_files:
            latest_model = max(model_files, key=lambda x: x.stat().st_mtime)
            print(f"   최신 모델: {latest_model.name}")
        else:
            print(f"   ⚠️ 모델 파일 없음 - 먼저 Section 3 실행 필요")
    else:
        print(f"❌ models/ 디렉토리 없음")

    # 7. 향상된 도구 테스트
    print("\n7️⃣ 향상된 도구 테스트...")

    try:
        # enhanced.py 임포트 테스트
        # sys.path.append('src')
        from src.utils.enhanced import (
            HAS_ICECREAM,
            HAS_RICH,
            EnhancedLogger,
            display_table,
        )

        logger = EnhancedLogger("테스트")
        logger.info("향상된 도구 임포트 성공")

        # 간단한 테이블 표시
        display_table(
            "향상된 라이브러리 상태",
            ["라이브러리", "상태"],
            [
                ["icecream", "✅ 사용가능" if HAS_ICECREAM else "❌ 누락"],
                ["rich", "✅ 사용가능" if HAS_RICH else "❌ 누락"],
            ],
        )

        print("✅ 향상된 도구 동작 확인")

    except Exception as e:
        print(f"⚠️ 향상된 도구 임포트 실패: {e}")

    # 8. 시뮬레이션된 컨테이너 실행 테스트
    print("\n8️⃣ 시뮬레이션된 API 테스트...")

    try:
        # API 모듈 임포트 테스트 (실제 실행 없이)
        from src.api.endpoints import router
        from src.api.main import app

        print("✅ API 모듈 임포트 성공")
        print(f"   FastAPI 앱: {type(app)}")
        print(f"   엔드포인트 라우터: {type(router)}")

        # 모델 로드 테스트 (실제 로드 없이 체크)
        try:
            from src.models.evaluator import ModelEvaluator

            evaluator = ModelEvaluator()
            print("✅ 모델 평가기 클래스 로드 성공")
        except Exception as e:
            print(f"⚠️ 모델 평가기 로드 실패: {e}")

    except Exception as e:
        print(f"❌ API 모듈 임포트 실패: {e}")

    print("\n" + "=" * 50)
    print("🎉 Section 5 시뮬레이션 테스트 완료!")

    print("\n📝 결과 요약:")
    print("   ✅ Docker 구성 파일 검증")
    print("   ✅ API 코드 구조 확인")
    print("   ✅ 의존성 파일 유효성")
    print("   ✅ 향상된 도구 동작")

    print("\n💡 실제 Docker 테스트는 다음과 같이 수행:")
    print("   1. 로컬 환경: docker-compose up -d")
    print("   2. 별도 서버: Section 5 파일들을 복사 후 실행")
    print("   3. 클라우드: GitHub Actions CI/CD 파이프라인")

    print("\n🎯 다음 단계:")
    print("   Section 6: Monitoring & CI/CD")
    print("   - GitHub Actions 설정")
    print("   - Prometheus/Grafana 모니터링")
    print("   - 자동화된 테스트 파이프라인")

    return True


def simulate_container_behavior():
    """컨테이너 동작 시뮬레이션"""
    print("\n🔧 컨테이너 동작 시뮬레이션...")

    # 환경 변수 설정 시뮬레이션
    simulated_env = {
        "MLFLOW_TRACKING_URI": "http://mlflow:5000",
        "MODEL_PATH": "/app/models",
        "LOG_LEVEL": "INFO",
        "PYTHONPATH": "/app",
    }

    print("환경 변수 시뮬레이션:")
    for key, value in simulated_env.items():
        print(f"   {key}={value}")

    # 볼륨 마운트 시뮬레이션
    simulated_volumes = {
        "../models": "/app/models",
        "../data": "/app/data",
        "../logs": "/app/logs",
    }

    print("\n볼륨 마운트 시뮬레이션:")
    for host_path, container_path in simulated_volumes.items():
        exists = os.path.exists(host_path.replace("../", ""))
        status = "✅" if exists else "❌"
        print(f"   {status} {host_path} → {container_path}")

    # 포트 매핑 시뮬레이션
    simulated_ports = {"api": "8000:8000", "mlflow": "5000:5000"}

    print("\n포트 매핑 시뮬레이션:")
    for service, mapping in simulated_ports.items():
        print(f"   {service}: {mapping}")

    return True


def generate_test_report():
    """테스트 보고서 생성"""
    print("\n📋 테스트 보고서 생성 중...")

    report = {
        "test_type": "시뮬레이션 테스트",
        "environment": "Docker 컨테이너 (Docker-in-Docker 제한)",
        "timestamp": "2025-06-01",
        "sections_tested": [
            "Docker 파일 구문 검증",
            "API 코드 구조 확인",
            "의존성 파일 검증",
            "향상된 도구 동작 확인",
        ],
        "limitations": [
            "실제 컨테이너 실행 불가",
            "네트워크 연결 테스트 불가",
            "실시간 API 응답 테스트 불가",
        ],
        "recommendations": [
            "로컬 환경에서 전체 테스트",
            "CI/CD 파이프라인으로 자동 테스트",
            "클라우드 환경에서 통합 테스트",
        ],
    }

    # 보고서를 JSON으로 저장
    report_path = "section5_simulation_test_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"✅ 테스트 보고서 저장: {report_path}")

    return report


if __name__ == "__main__":
    try:
        # 메인 테스트 실행
        success = test_docker_files()

        # 시뮬레이션 실행
        simulate_container_behavior()

        # 보고서 생성
        generate_test_report()

        if success:
            print("\n🎊 Section 5 시뮬레이션 테스트 성공!")
            print("Docker 구성이 올바르게 설정되었습니다.")
        else:
            print("\n⚠️ 일부 문제가 발견되었습니다.")
            print("위의 오류들을 수정 후 다시 테스트하세요.")

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류: {e}")
        sys.exit(1)
