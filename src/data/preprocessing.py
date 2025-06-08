import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IMDbPreprocessor:
    """
    IMDb 영화 데이터 전처리 파이프라인
    MLOps 친화적 설계: 재사용 가능, 스케일러블, 검증 내장
    """

    def __init__(self, processed_data_path: str = "data/processed"):
        self.processed_data_path = Path(processed_data_path)
        self.processed_data_path.mkdir(exist_ok=True)

        # 전처리 설정
        self.top_genres = None  # 상위 장르 목록
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_fitted = False

        # 하이퍼파라미터
        self.top_n_genres = 8  # 상위 8개 장르만 사용
        self.min_year = 1900  # 최소 연도
        self.max_year = 2025  # 최대 연도

    def load_data(self) -> pd.DataFrame:
        """처리된 영화 데이터 로드"""
        data_path = self.processed_data_path / "movies_with_ratings.csv"

        if not data_path.exists():
            raise FileNotFoundError(f"데이터 파일이 없습니다: {data_path}")

        logger.info(f"데이터 로드: {data_path}")
        df = pd.read_csv(data_path)
        logger.info(f"로드된 데이터: {len(df):,} 행")

        return df

    def extract_top_genres(self, df: pd.DataFrame) -> List[str]:
        """상위 장르 추출"""
        logger.info("상위 장르 분석 중...")

        # 모든 장르 수집
        all_genres = []
        for genres_str in df["genres"].dropna():
            if genres_str and genres_str != "\\N":
                genres = [g.strip() for g in genres_str.split(",")]
                all_genres.extend(genres)

        # 장르 빈도 계산
        genre_counts = pd.Series(all_genres).value_counts()
        top_genres = genre_counts.head(self.top_n_genres).index.tolist()

        logger.info(f"상위 {self.top_n_genres}개 장르: {top_genres}")

        return top_genres

    def create_genre_features(
        self, df: pd.DataFrame, genres_list: List[str]
    ) -> pd.DataFrame:
        """장르 원-핫 인코딩 피처 생성"""
        logger.info("장르 피처 생성 중...")

        genre_df = df.copy()

        # 각 장르별 원-핫 인코딩
        for genre in genres_list:
            column_name = f"genre_{genre.lower().replace('-', '_')}"
            genre_df[column_name] = genre_df["genres"].apply(
                lambda x: 1 if isinstance(x, str) and genre in x else 0
            )

        logger.info(f"생성된 장르 피처: {len(genres_list)}개")
        return genre_df

    def create_numerical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """숫자형 피처 생성 및 정제"""
        logger.info("숫자형 피처 생성 중...")

        feature_df = df.copy()

        # 1. 연도 피처 (정규화)
        feature_df["year_normalized"] = pd.to_numeric(
            feature_df["startYear"], errors="coerce"
        )
        feature_df["year_normalized"] = feature_df["year_normalized"].fillna(
            feature_df["year_normalized"].median()
        )

        # 연도 범위 제한
        feature_df["year_normalized"] = feature_df["year_normalized"].clip(
            self.min_year, self.max_year
        )

        # 2. 런타임 피처 (결측값 처리)
        feature_df["runtime_minutes"] = pd.to_numeric(
            feature_df["runtimeMinutes"], errors="coerce"
        )
        runtime_median = feature_df["runtime_minutes"].median()
        feature_df["runtime_minutes"] = feature_df["runtime_minutes"].fillna(
            runtime_median
        )

        # 3. 투표수 피처 (로그 변환)
        feature_df["votes_log"] = np.log1p(
            feature_df["numVotes"]
        )  # log(1+x) for stability

        # 4. 제목 길이 피처
        feature_df["title_length"] = feature_df["primaryTitle"].str.len()

        # 5. 타겟 변수 (평점)
        feature_df["target_rating"] = feature_df["averageRating"]

        logger.info("숫자형 피처 생성 완료")
        return feature_df

    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """최종 피처 데이터프레임 준비"""
        logger.info("최종 피처 준비 중...")

        # 상위 장르 추출 (훈련 시에만)
        if self.top_genres is None:
            self.top_genres = self.extract_top_genres(df)

        # 장르 피처 생성
        df_with_genres = self.create_genre_features(df, self.top_genres)

        # 숫자형 피처 생성
        df_with_features = self.create_numerical_features(df_with_genres)

        # 최종 피처 컬럼 선택
        feature_columns = []

        # 장르 피처 추가
        for genre in self.top_genres:
            column_name = f"genre_{genre.lower().replace('-', '_')}"
            feature_columns.append(column_name)

        # 숫자형 피처 추가
        numerical_features = [
            "year_normalized",
            "runtime_minutes",
            "votes_log",
            "title_length",
        ]
        feature_columns.extend(numerical_features)

        # 피처 데이터프레임 생성
        X = df_with_features[feature_columns].copy()

        # 결측값 최종 체크
        X = X.fillna(0)

        logger.info(f"최종 피처: {len(feature_columns)}개")
        logger.info(f"피처 목록: {feature_columns}")

        return X, feature_columns

    def fit_transform(
        self, df: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """훈련 데이터에 대한 전처리 (fit + transform)"""
        logger.info("🔧 훈련 데이터 전처리 시작...")

        # 피처 준비
        X, feature_names = self.prepare_features(df)
        self.feature_names = feature_names

        # 타겟 준비
        y = df["averageRating"].values

        # 스케일링 (StandardScaler)
        X_scaled = self.scaler.fit_transform(X)

        self.is_fitted = True
        logger.info("✅ 훈련 데이터 전처리 완료")

        return X_scaled, y, feature_names

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """새로운 데이터에 대한 전처리 (transform only)"""
        if not self.is_fitted:
            raise ValueError(
                "전처리기가 아직 fit되지 않았습니다. fit_transform을 먼저 실행하세요."
            )

        logger.info("🔄 새로운 데이터 전처리 중...")

        # 피처 준비 (동일한 장르 목록 사용)
        X, _ = self.prepare_features(df)

        # 스케일링 (이미 fit된 scaler 사용)
        X_scaled = self.scaler.transform(X)

        logger.info("✅ 새로운 데이터 전처리 완료")

        return X_scaled

    def create_train_test_split(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> Tuple:
        """훈련/테스트 데이터 분할"""
        logger.info(f"데이터 분할 중... (test_size={test_size})")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=None
        )

        logger.info(f"훈련 데이터: {X_train.shape[0]:,} 샘플")
        logger.info(f"테스트 데이터: {X_test.shape[0]:,} 샘플")

        return X_train, X_test, y_train, y_test

    def save_preprocessor(self, filepath: str = None):
        """전처리기 저장 (재사용을 위해)"""
        if filepath is None:
            filepath = self.processed_data_path / "preprocessor.pkl"

        preprocessor_data = {
            "top_genres": self.top_genres,
            "scaler": self.scaler,
            "feature_names": self.feature_names,
            "is_fitted": self.is_fitted,
            "top_n_genres": self.top_n_genres,
            "min_year": self.min_year,
            "max_year": self.max_year,
        }

        with open(filepath, "wb") as f:
            pickle.dump(preprocessor_data, f)

        logger.info(f"전처리기 저장: {filepath}")

    def load_preprocessor(self, filepath: str = None):
        """저장된 전처리기 로드"""
        if filepath is None:
            filepath = self.processed_data_path / "preprocessor.pkl"

        with open(filepath, "rb") as f:
            preprocessor_data = pickle.load(f)

        self.top_genres = preprocessor_data["top_genres"]
        self.scaler = preprocessor_data["scaler"]
        self.feature_names = preprocessor_data["feature_names"]
        self.is_fitted = preprocessor_data["is_fitted"]
        self.top_n_genres = preprocessor_data["top_n_genres"]
        self.min_year = preprocessor_data["min_year"]
        self.max_year = preprocessor_data["max_year"]

        logger.info(f"전처리기 로드: {filepath}")


# 사용 예시
if __name__ == "__main__":
    # 전처리기 생성
    preprocessor = IMDbPreprocessor()

    # 데이터 로드
    df = preprocessor.load_data()

    # 훈련 데이터 전처리
    X, y, feature_names = preprocessor.fit_transform(df)

    # 데이터 분할
    X_train, X_test, y_train, y_test = preprocessor.create_train_test_split(X, y)

    # 전처리기 저장
    preprocessor.save_preprocessor()

    print(f"🎯 전처리 완료!")
    print(f"  피처 수: {len(feature_names)}")
    print(f"  훈련 데이터: {X_train.shape}")
    print(f"  테스트 데이터: {X_test.shape}")
    print(f"  피처 목록: {feature_names}")
