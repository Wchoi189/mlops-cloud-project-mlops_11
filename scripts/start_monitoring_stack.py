#!/usr/bin/env python3
"""
Monitoring Stack Quick Start Script
One-click deployment for Prometheus + Grafana + AlertManager
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

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


def check_prerequisites():
    """사전 요구사항 확인"""
    print("🔍 모니터링 스택 사전 요구사항 확인...")

    # Docker 확인
    success, stdout, stderr = run_command("docker --version")
    if not success:
        print("❌ Docker가 설치되지 않았습니다.")
        return False
    print(f"✅ {stdout.strip()}")

    # Docker Compose 확인
    success, stdout, stderr = run_command("docker-compose --version")
    if not success:
        print("❌ Docker Compose가 설치되지 않았습니다.")
        return False
    print(f"✅ {stdout.strip()}")

    # 필요한 파일 확인
    required_files = [
        "docker/docker-compose.monitoring.yml",
        "docker/monitoring/prometheus.yml",
        "docker/monitoring/alertmanager.yml",
    ]

    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} 누락")
            return False

    return True


def create_monitoring_directories():
    """모니터링 디렉토리 생성"""
    print("\n📁 모니터링 디렉토리 생성 중...")

    directories = [
        "docker/monitoring",
        "docker/monitoring/rules",
        "docker/monitoring/grafana/provisioning/datasources",
        "docker/monitoring/grafana/provisioning/dashboards",
        "docker/monitoring/grafana/dashboards",
        "logs",
        "mlruns",
        "mlartifacts",
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ {directory}")


def install_prometheus_client():
    """Prometheus client 설치"""
    print("\n📦 Prometheus client 설치 확인...")

    try:
        import prometheus_client

        from utils.enhanced import get_package_version

        prometheus_version = get_package_version("prometheus-client")
        # print(f"✅ prometheus_client 이미 설치됨: {prometheus_client.__version__}")
        print(f"✅ prometheus_client 이미 설치됨: {prometheus_version}")
        return True
    except ImportError:
        print("📦 prometheus_client 설치 중...")
        success, stdout, stderr = run_command("pip install prometheus_client")
        if success:
            print("✅ prometheus_client 설치 완료")
            return True
        else:
            print(f"❌ prometheus_client 설치 실패: {stderr}")
            return False


def start_monitoring_stack():
    """모니터링 스택 시작"""
    print("\n🚀 모니터링 스택 시작 중...")

    # 기존 스택 정리
    print("🧹 기존 모니터링 스택 정리...")
    run_command(
        "cd docker && docker-compose -f docker-compose.monitoring.yml down --remove-orphans"
    )

    # 네트워크 생성 (필요한 경우)
    run_command("docker network create mlops-network 2>/dev/null || true")

    # 모니터링 스택 시작
    print("🔄 모니터링 서비스 시작...")
    success, stdout, stderr = run_command(
        "cd docker && docker-compose -f docker-compose.monitoring.yml up -d",
        timeout=300,
    )

    if not success:
        print(f"❌ 모니터링 스택 시작 실패: {stderr}")
        return False

    print("✅ 모니터링 스택 시작 완료")
    return True


def wait_for_services():
    """서비스 준비 대기"""
    print("\n⏳ 모니터링 서비스 준비 대기 중...")

    services = {
        "Prometheus": {"url": "http://localhost:9090/-/ready", "timeout": 60},
        "Grafana": {"url": "http://localhost:3000/api/health", "timeout": 90},
        "AlertManager": {"url": "http://localhost:9093/-/ready", "timeout": 60},
        "API (if running)": {"url": "http://localhost:8000/health", "timeout": 30},
    }

    for service_name, config in services.items():
        url = config["url"]
        timeout = config["timeout"]

        print(f"🔄 {service_name} 대기 중...")

        for i in range(timeout):
            try:
                response = requests.get(url, timeout=2)
                if response.status_code in [200, 204]:
                    print(f"✅ {service_name} 준비 완료")
                    break
            except requests.exceptions.RequestException:
                pass

            time.sleep(1)
            if i % 10 == 9:  # 10초마다 진행상황 출력
                print(f"   대기 중... ({i+1}/{timeout}초)")
        else:
            if "API" in service_name:
                print(f"⚠️ {service_name} 대기 시간 초과 (API가 실행되지 않을 수 있음)")
            else:
                print(f"⚠️ {service_name} 대기 시간 초과")

    return True


def test_monitoring_endpoints():
    """모니터링 엔드포인트 테스트"""
    print("\n🧪 모니터링 엔드포인트 테스트...")

    tests = [
        {
            "name": "Prometheus Targets",
            "url": "http://localhost:9090/api/v1/targets",
            "expected_key": "data",
        },
        {
            "name": "Prometheus Rules",
            "url": "http://localhost:9090/api/v1/rules",
            "expected_key": "data",
        },
        {
            "name": "AlertManager Status",
            "url": "http://localhost:9093/api/v1/status",
            "expected_key": "data",
        },
        {
            "name": "Grafana Health",
            "url": "http://localhost:3000/api/health",
            "expected_key": "database",
        },
    ]

    for test in tests:
        try:
            response = requests.get(test["url"], timeout=10)
            if response.status_code == 200:
                data = response.json()
                if test["expected_key"] in data:
                    print(f"✅ {test['name']}")
                else:
                    print(f"⚠️ {test['name']} - 예상 키 누락")
            else:
                print(f"⚠️ {test['name']} - HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {test['name']} - 오류: {str(e)}")


def setup_grafana_datasource():
    """Grafana 데이터소스 설정 확인"""
    print("\n📊 Grafana 설정 확인...")

    try:
        # Grafana API를 통한 데이터소스 확인
        headers = {"Content-Type": "application/json"}
        auth = ("admin", "mlops123")

        # 데이터소스 목록 조회
        response = requests.get(
            "http://localhost:3000/api/datasources",
            auth=auth,
            headers=headers,
            timeout=10,
        )

        if response.status_code == 200:
            datasources = response.json()
            prometheus_ds = [ds for ds in datasources if ds.get("type") == "prometheus"]

            if prometheus_ds:
                print(f"✅ Prometheus 데이터소스 설정됨: {len(prometheus_ds)}개")
            else:
                print("⚠️ Prometheus 데이터소스 미설정")

            return True
        else:
            print(f"⚠️ Grafana API 응답 오류: {response.status_code}")
            return False

    except Exception as e:
        print(f"⚠️ Grafana 설정 확인 실패: {e}")
        return False


def test_api_metrics():
    """API 메트릭 테스트"""
    print("\n📈 API 메트릭 테스트...")

    # API가 실행 중인지 확인
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("⚠️ API가 실행되지 않음 - 메트릭 테스트 스킵")
            return True
    except:
        print("⚠️ API가 실행되지 않음 - 메트릭 테스트 스킵")
        return True

    # 메트릭 엔드포인트 테스트
    try:
        response = requests.get("http://localhost:8000/metrics", timeout=10)
        if response.status_code == 200:
            metrics_data = response.text

            # 예상 메트릭 확인
            expected_metrics = [
                "http_requests_total",
                "model_predictions_total",
                "model_accuracy_score",
            ]

            found_metrics = []
            for metric in expected_metrics:
                if metric in metrics_data:
                    found_metrics.append(metric)

            print(
                f"✅ API 메트릭 수집: {len(found_metrics)}/{len(expected_metrics)} 메트릭 발견"
            )

            if found_metrics:
                print(f"   발견된 메트릭: {', '.join(found_metrics)}")

            return True
        else:
            print(f"⚠️ API 메트릭 엔드포인트 오류: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ API 메트릭 테스트 실패: {e}")
        return False


def generate_sample_metrics():
    """샘플 메트릭 생성"""
    print("\n📊 샘플 메트릭 생성...")

    try:
        # API 호출을 통한 메트릭 생성
        sample_requests = [
            ("GET", "http://localhost:8000/health"),
            ("GET", "http://localhost:8000/model/info"),
            (
                "POST",
                "http://localhost:8000/predict/movie",
                {
                    "title": "Sample Movie",
                    "startYear": 2020,
                    "runtimeMinutes": 120,
                    "numVotes": 5000,
                },
            ),
        ]

        successful_requests = 0

        for method, url, *data in sample_requests:
            try:
                if method == "GET":
                    response = requests.get(url, timeout=5)
                else:
                    response = requests.post(
                        url, json=data[0] if data else {}, timeout=5
                    )

                if response.status_code == 200:
                    successful_requests += 1
                    print(f"✅ {method} {url}")
                else:
                    print(f"⚠️ {method} {url} - HTTP {response.status_code}")

            except Exception as e:
                print(f"❌ {method} {url} - 오류: {str(e)}")

        print(f"✅ {successful_requests}개 샘플 요청 완료")
        return True

    except Exception as e:
        print(f"❌ 샘플 메트릭 생성 실패: {e}")
        return False


def show_dashboard_urls():
    """대시보드 URL 표시"""
    print("\n🌐 모니터링 대시보드 접속 정보")
    print("=" * 50)

    dashboards = [
        {
            "name": "Prometheus",
            "url": "http://localhost:9090",
            "description": "메트릭 수집 및 쿼리",
        },
        {
            "name": "Grafana",
            "url": "http://localhost:3000",
            "description": "시각화 대시보드 (admin/mlops123)",
        },
        {
            "name": "AlertManager",
            "url": "http://localhost:9093",
            "description": "알림 관리",
        },
        {
            "name": "API Metrics",
            "url": "http://localhost:8000/metrics",
            "description": "API 메트릭 (Prometheus 형식)",
        },
        {
            "name": "API Health",
            "url": "http://localhost:8000/health",
            "description": "API 상태 확인",
        },
    ]

    for dashboard in dashboards:
        print(f"📊 {dashboard['name']}: {dashboard['url']}")
        print(f"   {dashboard['description']}")
        print()


def show_useful_commands():
    """유용한 명령어 표시"""
    print("💡 유용한 명령어")
    print("=" * 50)

    commands = [
        (
            "모니터링 스택 상태 확인",
            "docker-compose -f docker/docker-compose.monitoring.yml ps",
        ),
        (
            "모니터링 로그 확인",
            "docker-compose -f docker/docker-compose.monitoring.yml logs -f",
        ),
        (
            "Prometheus 로그",
            "docker-compose -f docker/docker-compose.monitoring.yml logs -f prometheus",
        ),
        (
            "Grafana 로그",
            "docker-compose -f docker/docker-compose.monitoring.yml logs -f grafana",
        ),
        (
            "모니터링 스택 중지",
            "docker-compose -f docker/docker-compose.monitoring.yml down",
        ),
        (
            "모니터링 스택 재시작",
            "docker-compose -f docker/docker-compose.monitoring.yml restart",
        ),
        ("API 메트릭 확인", "curl http://localhost:8000/metrics"),
        ("Prometheus 타겟 확인", "curl http://localhost:9090/api/v1/targets"),
    ]

    for description, command in commands:
        print(f"# {description}")
        print(f"  {command}")
        print()


def main():
    """메인 실행 함수"""
    print("🚀 MLOps 모니터링 스택 빠른 시작")
    print("=" * 50)
    print(f"🕐 시작 시간: {datetime.now()}")
    print()

    # 1. 사전 요구사항 확인
    if not check_prerequisites():
        return False

    # 2. 디렉토리 생성
    create_monitoring_directories()

    # 3. Prometheus client 설치
    if not install_prometheus_client():
        print("⚠️ Prometheus client 설치 실패 - 계속 진행")

    # 4. 모니터링 스택 시작
    if not start_monitoring_stack():
        return False

    # 5. 서비스 준비 대기
    wait_for_services()

    # 6. 엔드포인트 테스트
    test_monitoring_endpoints()

    # 7. Grafana 설정 확인
    setup_grafana_datasource()

    # 8. API 메트릭 테스트
    test_api_metrics()

    # 9. 샘플 메트릭 생성
    generate_sample_metrics()

    # 10. 결과 표시
    print("\n" + "=" * 50)
    print("🎉 모니터링 스택 배포 완료!")
    print("=" * 50)

    show_dashboard_urls()
    show_useful_commands()

    print("📝 다음 단계:")
    print("   1. Grafana에서 MLOps 대시보드 확인")
    print("   2. API 호출하여 메트릭 생성")
    print("   3. Prometheus에서 메트릭 쿼리 테스트")
    print("   4. AlertManager에서 알림 규칙 확인")
    print("   5. Section 6.2: CI/CD Pipeline 구축")

    return True


def stop_monitoring():
    """모니터링 스택 중지"""
    print("🛑 모니터링 스택 중지 중...")

    success, stdout, stderr = run_command(
        "cd docker && docker-compose -f docker-compose.monitoring.yml down"
    )

    if success:
        print("✅ 모니터링 스택 중지 완료")
    else:
        print(f"❌ 모니터링 스택 중지 실패: {stderr}")

    return success


def status_check():
    """모니터링 스택 상태 확인"""
    print("📊 모니터링 스택 상태 확인")
    print("=" * 30)

    # Docker 컨테이너 상태
    success, stdout, stderr = run_command(
        "cd docker && docker-compose -f docker-compose.monitoring.yml ps"
    )

    if success:
        print("🐳 컨테이너 상태:")
        print(stdout)

    # 서비스 상태 확인
    services = [
        ("Prometheus", "http://localhost:9090/-/ready"),
        ("Grafana", "http://localhost:3000/api/health"),
        ("AlertManager", "http://localhost:9093/-/ready"),
    ]

    print("\n🌐 서비스 상태:")
    for name, url in services:
        try:
            response = requests.get(url, timeout=5)
            status = (
                "✅ 정상"
                if response.status_code in [200, 204]
                else f"⚠️ HTTP {response.status_code}"
            )
        except:
            status = "❌ 연결 실패"

        print(f"   {name}: {status}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MLOps 모니터링 스택 관리")
    parser.add_argument("--stop", action="store_true", help="모니터링 스택 중지")
    parser.add_argument("--status", action="store_true", help="모니터링 스택 상태 확인")

    args = parser.parse_args()

    try:
        if args.stop:
            success = stop_monitoring()
        elif args.status:
            success = status_check()
            success = True  # Status check always succeeds
        else:
            success = main()

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⏹️ 사용자에 의해 중단됨")
        sys.exit(1)
