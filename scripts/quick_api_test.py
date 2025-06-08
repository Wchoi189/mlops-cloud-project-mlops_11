#!/usr/bin/env python3
"""
빠른 API 테스트 스크립트
Quick API Testing Script for Section 4
"""

import json
import time
from datetime import datetime

import requests


def test_api_endpoints():
    """API 엔드포인트 빠른 테스트"""

    base_url = "http://localhost:8000"

    print("🧪 API 엔드포인트 빠른 테스트")
    print("=" * 40)
    print(f"📡 API URL: {base_url}")
    print(f"🕐 테스트 시간: {datetime.now()}")
    print()

    # 테스트 케이스들
    tests = [
        {
            "name": "헬스 체크",
            "method": "GET",
            "url": f"{base_url}/health",
            "data": None,
        },
        {
            "name": "루트 엔드포인트",
            "method": "GET",
            "url": f"{base_url}/",
            "data": None,
        },
        {
            "name": "모델 정보",
            "method": "GET",
            "url": f"{base_url}/model/info",
            "data": None,
        },
        {
            "name": "API 상태",
            "method": "GET",
            "url": f"{base_url}/status",
            "data": None,
        },
        {
            "name": "영화 평점 예측 - 좋은 영화",
            "method": "POST",
            "url": f"{base_url}/predict/movie",
            "data": {
                "title": "The Dark Knight",
                "startYear": 2008,
                "runtimeMinutes": 152,
                "numVotes": 2500000,
            },
        },
        {
            "name": "영화 평점 예측 - 평범한 영화",
            "method": "POST",
            "url": f"{base_url}/predict/movie",
            "data": {
                "title": "Average Movie",
                "startYear": 2015,
                "runtimeMinutes": 95,
                "numVotes": 10000,
            },
        },
        {
            "name": "영화 평점 예측 - 저예산 영화",
            "method": "POST",
            "url": f"{base_url}/predict/movie",
            "data": {
                "title": "Low Budget Film",
                "startYear": 2022,
                "runtimeMinutes": 85,
                "numVotes": 500,
            },
        },
        {
            "name": "레거시 예측 (텍스트)",
            "method": "POST",
            "url": f"{base_url}/predict",
            "data": {"text": "This is an amazing movie with great acting!"},
        },
    ]

    results = []

    for i, test in enumerate(tests, 1):
        print(f"{i}️⃣ {test['name']} 테스트...")

        try:
            start_time = time.time()

            if test["method"] == "GET":
                response = requests.get(test["url"], timeout=10)
            else:
                response = requests.post(
                    test["url"],
                    json=test["data"],
                    headers={"Content-Type": "application/json"},
                    timeout=10,
                )

            elapsed = time.time() - start_time

            if response.status_code == 200:
                result_data = response.json()
                print(f"   ✅ 성공 ({response.status_code}) - {elapsed:.2f}초")

                # 응답 내용 요약 출력
                if test["name"] == "헬스 체크":
                    print(f"      상태: {result_data.get('status', 'N/A')}")
                    print(f"      모델 로드: {result_data.get('model_loaded', 'N/A')}")

                elif test["name"] == "모델 정보":
                    print(f"      모델명: {result_data.get('name', 'N/A')}")
                    print(f"      버전: {result_data.get('version', 'N/A')}")

                elif test["name"] == "루트 엔드포인트":
                    print(f"      API: {result_data.get('message', 'N/A')}")
                    print(f"      피처: {result_data.get('features_used', [])}")

                elif "영화 평점 예측" in test["name"]:
                    print(f"      제목: {result_data.get('title', 'N/A')}")
                    print(
                        f"      예측 평점: {result_data.get('predicted_rating', 'N/A')}/10"
                    )

                elif test["name"] == "레거시 예측 (텍스트)":
                    print(f"      감정: {result_data.get('sentiment', 'N/A')}")
                    print(f"      신뢰도: {result_data.get('confidence', 'N/A')}")

                results.append(
                    {
                        "test": test["name"],
                        "status": "SUCCESS",
                        "code": response.status_code,
                        "time": elapsed,
                    }
                )

            else:
                print(f"   ⚠️ 응답 코드: {response.status_code}")
                print(f"      오류: {response.text[:100]}...")

                results.append(
                    {
                        "test": test["name"],
                        "status": "FAILED",
                        "code": response.status_code,
                        "time": elapsed,
                    }
                )

        except requests.exceptions.ConnectionError:
            print(f"   ❌ 연결 실패 - API 서버가 실행되지 않음")
            results.append(
                {
                    "test": test["name"],
                    "status": "CONNECTION_ERROR",
                    "code": None,
                    "time": 0,
                }
            )

        except requests.exceptions.Timeout:
            print(f"   ❌ 시간 초과 (10초)")
            results.append(
                {"test": test["name"], "status": "TIMEOUT", "code": None, "time": 10}
            )

        except Exception as e:
            print(f"   ❌ 오류: {str(e)}")
            results.append(
                {"test": test["name"], "status": "ERROR", "code": None, "time": 0}
            )

        print()

    # 결과 요약
    print("=" * 40)
    print("📊 테스트 결과 요약")
    print("=" * 40)

    success_count = len([r for r in results if r["status"] == "SUCCESS"])
    total_count = len(results)

    print(f"✅ 성공: {success_count}/{total_count}")
    print(f"❌ 실패: {total_count - success_count}/{total_count}")
    print(
        f"⚡ 평균 응답 시간: {sum(r['time'] for r in results if r['time'] > 0) / max(1, len([r for r in results if r['time'] > 0])):.2f}초"
    )

    if success_count == total_count:
        print("\n🎉 모든 테스트 통과! API가 정상 작동합니다.")
    elif success_count > 0:
        print(
            f"\n⚠️ 일부 테스트 실패. {success_count}개 성공, {total_count - success_count}개 실패"
        )
    else:
        print("\n💥 모든 테스트 실패. API 서버 상태를 확인하세요.")
        print("\n💡 API 서버 시작 방법:")
        print("   uvicorn src.api.main:app --reload --port 8000")

    print("\n🔗 유용한 링크:")
    print(f"   API 문서: {base_url}/docs")
    print(f"   API 상태: {base_url}/status")
    print(f"   헬스 체크: {base_url}/health")

    return success_count == total_count


def demo_predictions():
    """예측 데모"""

    print("\n🎬 영화 평점 예측 데모")
    print("=" * 30)

    base_url = "http://localhost:8000"

    demo_movies = [
        {
            "title": "Avengers: Endgame",
            "startYear": 2019,
            "runtimeMinutes": 181,
            "numVotes": 1000000,
        },
        {
            "title": "Parasite",
            "startYear": 2019,
            "runtimeMinutes": 132,
            "numVotes": 750000,
        },
        {
            "title": "Joker",
            "startYear": 2019,
            "runtimeMinutes": 122,
            "numVotes": 1200000,
        },
        {
            "title": "The Room",
            "startYear": 2003,
            "runtimeMinutes": 99,
            "numVotes": 100000,
        },
        {
            "title": "Independent Film",
            "startYear": 2023,
            "runtimeMinutes": 95,
            "numVotes": 1000,
        },
    ]

    for movie in demo_movies:
        try:
            response = requests.post(f"{base_url}/predict/movie", json=movie, timeout=5)

            if response.status_code == 200:
                result = response.json()
                rating = result.get("predicted_rating", 0)
                print(f"🎬 {movie['title']} ({movie['startYear']})")
                print(f"   예측 평점: {rating:.1f}/10")
                print(
                    f"   런타임: {movie['runtimeMinutes']}분, 투표수: {movie['numVotes']:,}"
                )
                print()
            else:
                print(f"❌ {movie['title']} 예측 실패")

        except Exception as e:
            print(f"❌ {movie['title']} 오류: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="빠른 API 테스트")
    parser.add_argument("--demo", action="store_true", help="예측 데모 실행")

    args = parser.parse_args()

    try:
        if args.demo:
            demo_predictions()
        else:
            success = test_api_endpoints()
            exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⏹️ 테스트 중단됨")
        exit(1)
