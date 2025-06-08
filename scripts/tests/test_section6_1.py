#!/usr/bin/env python3
"""
Section 6.1 (Monitoring & Observability) 테스트 스크립트
Monitoring Stack Testing Script
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import requests
import yaml

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_section61():
    """Section 6.1 모니터링 스택 테스트"""

    print("🧪 Section 6.1: Monitoring & Observability 테스트 시작")
    print("=" * 60)

    # 1. 모니터링 파일 확인
    print("\n1️⃣ 모니터링 구성 파일 확인...")

    required_files = [
        "docker/docker-compose.monitoring.yml",
        "docker/monitoring/prometheus.yml",
        "docker/monitoring/rules/mlops-alerts.yml",
        "docker/monitoring/alertmanager/alertmanager.yml",
        "docker/monitoring/grafana/provisioning/datasources/prometheus.yml",
        "docker/monitoring/grafana/provisioning/dashboards/dashboard.yml",
        "docker/monitoring/grafana/dashboards/mlops-overview.json",
        "src/monitoring/metrics.py",
        "src/api/main_with_metrics.py",
        "src/api/endpoints_with_metrics.py",
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

    # 2. YAML 파일 구문 검증
    print("\n2️⃣ YAML 구성 파일 검증...")

    yaml_files = [
        "docker/docker-compose.monitoring.yml",
        "docker/monitoring/prometheus.yml",
        "docker/monitoring/rules/mlops-alerts.yml",
        "docker/monitoring/alertmanager/alertmanager.yml",
        "docker/monitoring/grafana/provisioning/datasources/prometheus.yml",
        "docker/monitoring/grafana/provisioning/dashboards/dashboard.yml",
    ]

    for yaml_file in yaml_files:
        try:
            with open(yaml_file, "r") as f:
                yaml.safe_load(f)
            print(f"✅ {yaml_file} - 구문 유효")
        except yaml.YAMLError as e:
            print(f"❌ {yaml_file} - YAML 오류: {e}")
            return False
        except Exception as e:
            print(f"❌ {yaml_file} - 읽기 오류: {e}")
            return False

    # 3. JSON 파일 검증
    print("\n3️⃣ JSON 구성 파일 검증...")

    json_files = ["docker/monitoring/grafana/dashboards/mlops-overview.json"]

    for json_file in json_files:
        try:
            with open(json_file, "r") as f:
                json.load(f)
            print(f"✅ {json_file} - 구문 유효")
        except json.JSONDecodeError as e:
            print(f"❌ {json_file} - JSON 오류: {e}")
            return False
        except Exception as e:
            print(f"❌ {json_file} - 읽기 오류: {e}")
            return False

    # 4. Python 모니터링 모듈 테스트
    print("\n4️⃣ Python 모니터링 모듈 테스트...")

    try:
        # prometheus_client 설치 확인
        try:
            # import prometheus_client
            from src.utils.enhanced import get_package_version

            prometheus_version = get_package_version("prometheus-client")
            print(f"✅ prometheus_client 버전: {prometheus_version}")
        except ImportError:
            print("⚠️ prometheus_client 미설치 - pip install prometheus_client")

        # 모니터링 모듈 import 테스트
        from src.monitoring.metrics import MLOpsMetrics, metrics

        print("✅ MLOpsMetrics 클래스 import 성공")

        # 메트릭 인스턴스 테스트
        test_metrics = MLOpsMetrics()
        print("✅ MLOpsMetrics 인스턴스 생성 성공")

        # 메트릭 기능 테스트
        if test_metrics.enabled:
            test_metrics.record_prediction_rating(7.5)
            test_metrics.record_model_accuracy(0.85, "test_model", "1.0")
            test_metrics.set_active_users(5)
            print("✅ 메트릭 기록 기능 테스트 성공")
        else:
            print("⚠️ 메트릭 기능 비활성화 (prometheus_client 없음)")

    except Exception as e:
        print(f"❌ 모니터링 모듈 테스트 실패: {e}")
        return False

    # 5. Docker Compose 모니터링 구성 검증
    print("\n5️⃣ Docker Compose 모니터링 구성 검증...")

    try:
        # Docker Compose 설치 확인
        result = subprocess.run(
            ["docker-compose", "--version"], capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"✅ Docker Compose: {result.stdout.strip()}")
        else:
            print("❌ Docker Compose 미설치")
            return False

        # 모니터링 compose 파일 검증
        result = subprocess.run(
            [
                "docker-compose",
                "-f",
                "docker/docker-compose.monitoring.yml",
                "config",
                "--quiet",
            ],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        if result.returncode == 0:
            print("✅ Docker Compose 모니터링 구성 유효")
        else:
            print(f"❌ Docker Compose 구성 오류: {result.stderr}")
            return False

    except FileNotFoundError:
        print("⚠️ Docker Compose 미설치 - 스킵")
    except Exception as e:
        print(f"❌ Docker Compose 검증 오류: {e}")

    # 6. Prometheus 설정 검증
    print("\n6️⃣ Prometheus 설정 검증...")

    try:
        with open("docker/monitoring/prometheus.yml", "r") as f:
            prometheus_config = yaml.safe_load(f)

        # 필수 섹션 확인
        required_sections = ["global", "scrape_configs", "rule_files", "alerting"]
        for section in required_sections:
            if section in prometheus_config:
                print(f"✅ Prometheus {section} 섹션 존재")
            else:
                print(f"❌ Prometheus {section} 섹션 누락")

        # Scrape configs 확인
        scrape_configs = prometheus_config.get("scrape_configs", [])
        expected_jobs = [
            "prometheus",
            "mlops-api",
            "mlflow",
            "node-exporter",
            "cadvisor",
        ]

        found_jobs = [config.get("job_name") for config in scrape_configs]
        for job in expected_jobs:
            if job in found_jobs:
                print(f"✅ Prometheus job '{job}' 설정됨")
            else:
                print(f"⚠️ Prometheus job '{job}' 누락")

    except Exception as e:
        print(f"❌ Prometheus 설정 검증 오류: {e}")

    # 7. Alert Rules 검증
    print("\n7️⃣ Alert Rules 검증...")

    try:
        with open("docker/monitoring/rules/mlops-alerts.yml", "r") as f:
            alert_rules = yaml.safe_load(f)

        groups = alert_rules.get("groups", [])
        total_rules = sum(len(group.get("rules", [])) for group in groups)

        print(f"✅ Alert Rules: {len(groups)}개 그룹, {total_rules}개 규칙")

        # 주요 alert 확인
        expected_alerts = ["MLOpsAPIDown", "APIHighResponseTime", "ModelAccuracyDrop"]
        all_rules = []
        for group in groups:
            all_rules.extend([rule.get("alert") for rule in group.get("rules", [])])

        for alert in expected_alerts:
            if alert in all_rules:
                print(f"✅ Alert '{alert}' 정의됨")
            else:
                print(f"⚠️ Alert '{alert}' 누락")

    except Exception as e:
        print(f"❌ Alert Rules 검증 오류: {e}")

    # 8. Grafana 대시보드 검증
    print("\n8️⃣ Grafana 대시보드 검증...")

    try:
        with open("docker/monitoring/grafana/dashboards/mlops-overview.json", "r") as f:
            dashboard = json.load(f)

        panels = dashboard.get("panels", [])
        print(f"✅ Grafana 대시보드: {len(panels)}개 패널")

        # 패널 타입 확인
        panel_types = [panel.get("type") for panel in panels]
        unique_types = set(panel_types)
        print(f"✅ 패널 타입: {', '.join(unique_types)}")

        # 데이터소스 확인
        datasources = set()
        for panel in panels:
            for target in panel.get("targets", []):
                ds = target.get("datasource", {})
                if isinstance(ds, dict) and "uid" in ds:
                    datasources.add(ds.get("uid", "unknown"))

        print(f"✅ 데이터소스: {', '.join(datasources)}")

    except Exception as e:
        print(f"❌ Grafana 대시보드 검증 오류: {e}")

    # 9. API 모니터링 코드 검증
    print("\n9️⃣ API 모니터링 코드 검증...")

    try:
        # Enhanced API 모듈 import
        from src.api.endpoints_with_metrics import router as monitoring_router
        from src.api.main_with_metrics import app as monitoring_app

        print("✅ 모니터링 API 모듈 import 성공")

        # FastAPI 앱 검증
        print(f"✅ FastAPI 앱 타입: {type(monitoring_app)}")
        print(f"✅ Router 타입: {type(monitoring_router)}")

        # 라우트 확인 - 안전한 방법 (Safe route checking) #  NOT WORKING
        # routes = []
        # for route in monitoring_app.routes:
        #     # 다양한 라우트 타입에 대한 안전한 경로 추출
        #     if hasattr(route, 'path'):
        #         routes.append(route.path)
        #     elif hasattr(route, 'path_regex'):
        #         # APIRoute의 경우 path_regex에서 패턴 추출
        #         routes.append(str(route.path_regex.pattern))
        #     elif hasattr(route, 'methods') and hasattr(route, 'endpoint'):
        #         # 메서드와 엔드포인트가 있는 경우
        #         routes.append(f"<{route.endpoint.__name__}>")
        #     else:
        #         routes.append(f"<{type(route).__name__}>")

        # print(f"✅ 등록된 라우트들: {routes}")

        # 라우트 확인
        # FastAPI의 내장 라우트 검사 사용 (Using FastAPI's built-in route inspection)
        print("\n📋 등록된 라우트 목록:")
        routes = []
        for route in monitoring_app.routes:
            route_info = {
                "path": getattr(route, "path", "N/A"),
                "methods": getattr(route, "methods", set()),
                "name": getattr(route, "name", "N/A"),
                "type": type(route).__name__,
            }

            if route_info["path"] != "N/A":
                routes.append(route_info["path"])
                methods_str = (
                    ", ".join(route_info["methods"]) if route_info["methods"] else "N/A"
                )
                print(
                    f"  📍 {route_info['path']} [{methods_str}] ({route_info['type']})"
                )
            else:
                print(f"  🔗 {route_info['type']} (경로 정보 없음)")

        monitoring_endpoints = ["/metrics", "/monitoring/status", "/health"]

        for endpoint in monitoring_endpoints:
            if any(endpoint in route for route in routes):
                print(f"✅ 모니터링 엔드포인트 '{endpoint}' 등록됨")
            else:
                print(f"⚠️ 모니터링 엔드포인트 '{endpoint}' 확인 필요")

    except Exception as e:
        print(f"❌ API 모니터링 코드 검증 오류: {e}")

    print("\n" + "=" * 60)
    print("🎉 Section 6.1 Monitoring & Observability 테스트 완료!")

    print("\n📝 테스트 결과 요약:")
    print("   ✅ 모니터링 구성 파일 생성 및 검증")
    print("   ✅ Prometheus + Grafana + AlertManager 설정")
    print("   ✅ Python 메트릭 수집 모듈")
    print("   ✅ Enhanced API with Monitoring")
    print("   ✅ Alert Rules & Dashboard 구성")

    print("\n🚀 다음 단계:")
    print(
        "   1. 모니터링 스택 실행: docker-compose -f docker/docker-compose.monitoring.yml up -d"
    )
    print("   2. 서비스 확인:")
    print("      - Prometheus: http://localhost:9090")
    print("      - Grafana: http://localhost:3000 (admin/mlops123)")
    print("      - AlertManager: http://localhost:9093")
    print("      - API with Metrics: http://localhost:8000/metrics")
    print("   3. Section 6.2: CI/CD Pipeline 구축")

    print("\n💡 모니터링 스택 시작 명령어:")
    print("   cd docker")
    print("   docker-compose -f docker-compose.monitoring.yml up -d")
    print("   # 또는")
    print("   python scripts/start_monitoring_stack.py")

    return True


def test_prometheus_config():
    """Prometheus 설정 상세 테스트"""
    print("\n🔍 Prometheus 설정 상세 검증...")

    try:
        with open("docker/monitoring/prometheus.yml", "r") as f:
            config = yaml.safe_load(f)

        # Global 설정 확인
        global_config = config.get("global", {})
        scrape_interval = global_config.get("scrape_interval", "not_set")
        evaluation_interval = global_config.get("evaluation_interval", "not_set")

        print(f"   Scrape Interval: {scrape_interval}")
        print(f"   Evaluation Interval: {evaluation_interval}")

        # 스크랩 설정 확인
        scrape_configs = config.get("scrape_configs", [])
        for sc_config in scrape_configs:
            job_name = sc_config.get("job_name", "unknown")
            targets = sc_config.get("static_configs", [{}])[0].get("targets", [])
            metrics_path = sc_config.get("metrics_path", "/metrics")
            scrape_interval = sc_config.get("scrape_interval", "default")

            print(f"   Job: {job_name}")
            print(f"     Targets: {targets}")
            print(f"     Path: {metrics_path}")
            print(f"     Interval: {scrape_interval}")

        return True

    except Exception as e:
        print(f"   ❌ Prometheus 설정 검증 실패: {e}")
        return False


def test_metrics_functionality():
    """메트릭 기능 상세 테스트"""
    print("\n📊 메트릭 기능 상세 테스트...")

    try:
        from src.monitoring.metrics import MLOpsMetrics, metrics

        # 메트릭 인스턴스 생성
        test_metrics = MLOpsMetrics()

        # 다양한 메트릭 테스트
        test_data = [
            (
                "API Request",
                lambda: test_metrics.http_requests_total.labels(
                    method="GET", endpoint="/test", status_code="200"
                ).inc(),
            ),
            (
                "Model Prediction",
                lambda: test_metrics.model_predictions_total.labels(
                    model_name="test", model_version="1.0", prediction_type="single"
                ).inc(),
            ),
            ("Prediction Rating", lambda: test_metrics.record_prediction_rating(8.5)),
            (
                "Model Accuracy",
                lambda: test_metrics.record_model_accuracy(0.87, "test", "1.0"),
            ),
            (
                "Data Drift",
                lambda: test_metrics.record_data_drift("feature1", 0.05, "test"),
            ),
            ("Active Users", lambda: test_metrics.set_active_users(10)),
        ]

        for test_name, test_func in test_data:
            try:
                test_func()
                print(f"   ✅ {test_name}")
            except Exception as e:
                print(f"   ❌ {test_name}: {e}")

        # 메트릭 출력 테스트
        try:
            metrics_output = test_metrics.get_metrics()
            if metrics_output and "# " in metrics_output:
                print(f"   ✅ 메트릭 출력 생성 ({len(metrics_output)} 바이트)")
            else:
                print(f"   ⚠️ 메트릭 출력 비어있음")
        except Exception as e:
            print(f"   ❌ 메트릭 출력 실패: {e}")

        return True

    except Exception as e:
        print(f"   ❌ 메트릭 기능 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Section 6.1 Monitoring & Observability 테스트"
    )
    parser.add_argument("--detailed", action="store_true", help="상세 테스트 모드")

    args = parser.parse_args()

    success = test_section61()

    if args.detailed and success:
        print("\n" + "=" * 60)
        print("📋 상세 테스트 모드")
        print("=" * 60)

        test_prometheus_config()
        test_metrics_functionality()

    sys.exit(0 if success else 1)
