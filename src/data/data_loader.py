import gzip
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IMDbDataLoader:
    """IMDb 데이터셋 로더 - MLOps 파이프라인용 최소 구성"""

    # 필수 2개 파일만 사용 (MLOps 파이프라인 중심)
    IMDB_URLS = {
        "title_basics": "https://datasets.imdbws.com/title.basics.tsv.gz",
        "title_ratings": "https://datasets.imdbws.com/title.ratings.tsv.gz",
    }

    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def download_imdb_file(self, dataset_name: str) -> Path:
        """IMDb 데이터셋 파일 다운로드"""
        if dataset_name not in self.IMDB_URLS:
            raise ValueError(f"지원하지 않는 데이터셋: {dataset_name}")

        url = self.IMDB_URLS[dataset_name]
        filename = f"{dataset_name}.tsv.gz"
        filepath = self.data_dir / filename

        # 이미 파일이 있으면 스킵
        if filepath.exists():
            logger.info(f"파일이 이미 존재합니다: {filepath}")
            return filepath

        logger.info(f"다운로드 시작: {dataset_name}")

        # 파일 다운로드 (진행상황 표시)
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\r진행률: {percent:.1f}%", end="", flush=True)

        print()  # 새 줄
        logger.info(f"다운로드 완료: {filepath}")
        return filepath

    def load_imdb_tsv(
        self, dataset_name: str, nrows: Optional[int] = None
    ) -> pd.DataFrame:
        """IMDb TSV 파일을 pandas DataFrame으로 로드"""
        filepath = self.download_imdb_file(dataset_name)

        logger.info(f"파일 로드 중: {filepath}")

        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            df = pd.read_csv(f, sep="\t", na_values="\\N", nrows=nrows)

        logger.info(f"로드 완료: {dataset_name} - {len(df):,} 행")
        return df

    def create_movie_dataset(self, sample_size: int = 50000) -> pd.DataFrame:
        """
        영화 평점 예측용 통합 데이터셋 생성 (MLOps 파이프라인용)

        Args:
            sample_size: 샘플 크기 (기본: 50K - 빠른 처리를 위해)

        Returns:
            pd.DataFrame: 영화 평점 예측용 데이터셋
        """
        logger.info("🎬 영화 평점 예측 데이터셋 생성 시작...")

        # 1. 기본 영화 정보 로드 (샘플링으로 빠른 처리)
        logger.info("📁 title.basics 로드 중...")
        title_basics = self.load_imdb_tsv("title_basics", nrows=sample_size)

        # 2. 평점 정보 로드
        logger.info("⭐ title.ratings 로드 중...")
        title_ratings = self.load_imdb_tsv("title_ratings")

        # 3. 영화만 필터링 (TV 시리즈 제외)
        logger.info("🎭 영화 데이터 필터링 중...")
        movies = title_basics[title_basics["titleType"] == "movie"].copy()
        logger.info(f"영화 데이터: {len(movies):,} 개")

        # 4. 평점 정보와 조인
        logger.info("🔗 평점 데이터와 조인 중...")
        movie_ratings = movies.merge(title_ratings, on="tconst", how="inner")
        logger.info(f"평점 있는 영화: {len(movie_ratings):,} 개")

        # 5. 데이터 품질 향상을 위한 필터링
        logger.info("🧹 데이터 정제 중...")

        # 필수 컬럼 결측값 제거
        movie_ratings = movie_ratings.dropna(subset=["averageRating", "numVotes"])

        # 연도 데이터 타입 변환 (결측값 허용)
        movie_ratings["startYear"] = pd.to_numeric(
            movie_ratings["startYear"], errors="coerce"
        )

        # 더 관대한 필터링
        min_votes = 50  # 최소 50표로 낮춤
        movie_ratings = movie_ratings[movie_ratings["numVotes"] >= min_votes]

        # 연도 필터링을 더 관대하게 (1900년 이후)
        movie_ratings = movie_ratings[
            (movie_ratings["startYear"].isna()) | (movie_ratings["startYear"] >= 1900)
        ]

        # 디버깅 정보 추가
        logger.info(f"필터링 단계별 개수:")
        logger.info(f"  - 평점 있는 영화: {len(movie_ratings)} 개")
        logger.info(f"✅ 최종 데이터셋: {len(movie_ratings):,} 영화")

        # 6. 결과 저장
        output_path = self.data_dir.parent / "processed" / "movies_with_ratings.csv"
        output_path.parent.mkdir(exist_ok=True)
        movie_ratings.to_csv(output_path, index=False)

        logger.info(f"💾 데이터셋 저장: {output_path}")

        return movie_ratings


# 사용 예시 및 테스트
if __name__ == "__main__":
    loader = IMDbDataLoader()

    # 영화 데이터셋 생성 (작은 샘플로 빠른 테스트)
    movies_df = loader.create_movie_dataset(sample_size=100000)

    # 기본 정보 출력
    print(f"\n📊 데이터셋 정보:")
    print(f"전체 영화 수: {len(movies_df):,}")
    print(f"평균 평점: {movies_df['averageRating'].mean():.2f}")
    print(
        f"평점 범위: {movies_df['averageRating'].min():.1f} - {movies_df['averageRating'].max():.1f}"
    )
    print(f"컬럼: {list(movies_df.columns)}")
