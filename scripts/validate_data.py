#!/usr/bin/env python3
"""
IMDb 영화 데이터 검증 스크립트 - MLOps 파이프라인용
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from src.data.data_loader import IMDbDataLoader


def validate_imdb_data():
    """IMDb 영화 데이터셋 검증 및 품질 확인"""
    print("🔍 IMDb 영화 데이터셋 검증 시작...")

    # 데이터 로드 (빠른 테스트를 위해 작은 샘플)
    loader = IMDbDataLoader()
    movies_df = loader.create_movie_dataset(sample_size=30000)

    print("=" * 60)
    print("📊 데이터셋 기본 정보")
    print("=" * 60)
    print(f"총 영화 수: {len(movies_df):,}")
    print(f"컬럼 수: {len(movies_df.columns)}")
    print(f"컬럼 목록: {list(movies_df.columns)}")

    print("\n" + "=" * 60)
    print("⭐ 평점 통계 (Target Variable)")
    print("=" * 60)
    rating_stats = movies_df["averageRating"].describe()
    print(f"평균 평점: {rating_stats['mean']:.2f}")
    print(f"표준편차: {rating_stats['std']:.2f}")
    print(f"최고 평점: {rating_stats['max']:.1f}")
    print(f"최저 평점: {rating_stats['min']:.1f}")
    print(f"중간값: {rating_stats['50%']:.2f}")

    # 평점 분포
    print(f"\n평점 분포:")
    for rating in range(1, 11):
        count = len(
            movies_df[movies_df["averageRating"].between(rating - 0.5, rating + 0.5)]
        )
        print(f"  {rating}점대: {count:,} 영화")

    print("\n" + "=" * 60)
    print("🎭 피처 분석 (Feature Analysis)")
    print("=" * 60)

    # 장르 분포 (상위 10개)
    if "genres" in movies_df.columns:
        print("인기 장르 TOP 10:")
        genre_counts = movies_df["genres"].value_counts().head(10)
        for genre, count in genre_counts.items():
            print(f"  {genre}: {count:,} 영화")

    # 연도별 분포
    if "startYear" in movies_df.columns and len(movies_df) > 0:
        year_stats = movies_df["startYear"].describe()
        if not pd.isna(year_stats["min"]):
            print(f"\n📅 개봉 연도 통계:")
            print(f"가장 오래된 영화: {int(year_stats['min'])}")
            print(f"가장 최근 영화: {int(year_stats['max'])}")
            print(f"평균 개봉 연도: {year_stats['mean']:.0f}")
        else:
            print(f"\n📅 연도 데이터 없음")
    elif len(movies_df) == 0:
        print(f"\n⚠️ 데이터가 없습니다! 필터링 조건을 확인해주세요.")

        # 최근 20년 영화 비율
        recent_movies = len(movies_df[movies_df["startYear"] >= 2004])
        print(
            f"2004년 이후 영화: {recent_movies:,} ({recent_movies/len(movies_df)*100:.1f}%)"
        )

    # 투표 수 통계
    print(f"\n👥 투표 수 통계:")
    vote_stats = movies_df["numVotes"].describe()
    print(f"평균 투표 수: {vote_stats['mean']:,.0f}")
    print(f"중간값 투표 수: {vote_stats['50%']:,.0f}")
    print(f"최대 투표 수: {vote_stats['max']:,}")

    print("\n" + "=" * 60)
    print("🏆 샘플 데이터 (고평점 영화)")
    print("=" * 60)
    top_movies = movies_df.nlargest(5, "averageRating")[
        ["primaryTitle", "startYear", "genres", "averageRating", "numVotes"]
    ]

    for idx, movie in top_movies.iterrows():
        print(f"{movie['primaryTitle']} ({int(movie['startYear'])})")
        print(f"  장르: {movie['genres']}")
        print(f"  평점: {movie['averageRating']:.1f}/10 (투표: {movie['numVotes']:,})")
        print()

    print("=" * 60)
    print("✅ 데이터 검증 완료! MLOps 파이프라인 구축 준비됨")
    print("=" * 60)

    # 다음 단계 안내
    print("\n🚀 다음 단계:")
    print("1. Section 2: 데이터 전처리 파이프라인 구현")
    print("2. Section 3: 모델 훈련 파이프라인 구현")
    print("3. Section 4: API 서빙 파이프라인 구현")


if __name__ == "__main__":
    validate_imdb_data()
