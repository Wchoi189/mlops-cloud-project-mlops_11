#!/usr/bin/env python3
"""
현재 처리된 데이터의 컬럼 구조 확인
"""

import os

import pandas as pd


def check_data_structure():
    """현재 데이터 파일의 구조 확인"""

    data_path = "data/processed/movies_with_ratings.csv"

    if not os.path.exists(data_path):
        print(f"❌ 데이터 파일이 존재하지 않습니다: {data_path}")
        return

    # 데이터 로드
    df = pd.read_csv(data_path)

    print("📊 현재 데이터 구조 분석")
    print("=" * 50)
    print(f"🔢 데이터 개수: {len(df):,}개")
    print(f"📋 컬럼 개수: {len(df.columns)}개")
    print()

    print("📝 현재 컬럼 목록:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")
    print()

    print("🎬 장르 관련 컬럼 확인:")
    genre_cols = [
        col for col in df.columns if "genre" in col.lower() or col.startswith("is_")
    ]
    if genre_cols:
        for col in genre_cols:
            print(f"  ✅ {col}")
    else:
        print("  ❌ 장르 관련 컬럼이 없습니다!")
    print()

    print("🔍 데이터 샘플 (첫 3행):")
    print(df.head(3).to_string())
    print()

    print("📈 기본 통계:")
    print(df.describe())

    # 필요한 컬럼들 확인
    required_cols = ["is_Action", "is_Comedy", "is_Drama"]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        print(f"\n❌ 누락된 필수 컬럼: {missing_cols}")
        print("➡️ Section 2의 전처리 코드를 수정해야 합니다.")
    else:
        print(f"\n✅ 모든 필수 컬럼이 존재합니다!")


if __name__ == "__main__":
    check_data_structure()
