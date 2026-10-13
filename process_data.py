
from pathlib import Path
import pandas as pd

# 프로젝트 폴더 경로
BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 분석할 품목과 파일 이름
PRODUCT_FILES = {
    "감자": "감자 21~26.xls",
    "배추": "배추 21~26.xls",
    "사과": "사과 21~26.xls",
    "쌀": "쌀 21~26.xls",
    "양파": "양파 21~26.xls",
}


def read_price_table(file_path):
    """HTML 형식으로 저장된 가격표에서 첫 번째 표를 읽는다."""
    tables = pd.read_html(file_path, encoding="utf-8")

    if not tables:
        raise ValueError("가격표를 찾을 수 없습니다.")

    # 첫 번째 표만 사용해 중복 집계를 방지한다.
    return tables[0]


def clean_product(product, filename):
    file_path = RAW_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    df = read_price_table(file_path)

    # 월 정보가 있는 행만 사용한다.
    df = df[df["구분"].astype(str).str.match(r"^\d{1,2}월$")].copy()

    # '01월' -> 1, '10월' -> 10
    df["월"] = df["구분"].astype(str).str.extract(r"(\d{1,2})").astype(int)

    # 연도별 열을 행으로 변환한다.
    year_columns = [
        col for col in df.columns
        if str(col).endswith("년") and str(col)[:4].isdigit()
    ]

    long_df = df.melt(
        id_vars=["월"],
        value_vars=year_columns,
        var_name="연도",
        value_name="가격",
    )

    long_df["연도"] = (
        long_df["연도"].astype(str).str.replace("년", "", regex=False).astype(int)
    )

    # '-'나 빈칸은 결측값으로 유지한다.
    long_df["가격"] = pd.to_numeric(
        long_df["가격"].replace("-", pd.NA),
        errors="coerce",
    )

    # 날짜 생성
    long_df["날짜"] = pd.to_datetime(
        {
            "year": long_df["연도"],
            "month": long_df["월"],
            "day": 1,
        },
        errors="coerce",
    )

    long_df["품목"] = product

    # 2021년 1월 이후부터 현재 데이터 범위까지만 사용한다.
    long_df = long_df[
        (long_df["날짜"] >= "2021-01-01")
        & (long_df["날짜"] <= pd.Timestamp.today().replace(day=1))
    ]

    return long_df[["날짜", "품목", "가격"]]


def main():
    all_data = []

    for product, filename in PRODUCT_FILES.items():
        print(f"\n[{product}] 처리 중...")

        try:
            product_df = clean_product(product, filename)
            all_data.append(product_df)

            print(f"  전체 월 수: {len(product_df)}")
            print(f"  가격 있음: {product_df['가격'].notna().sum()}")
            print(f"  가격 없음: {product_df['가격'].isna().sum()}")

        except Exception as e:
            print(f"  오류: {e}")
            return

    result = pd.concat(all_data, ignore_index=True)
    result = result.sort_values(["품목", "날짜"]).reset_index(drop=True)

    # 같은 품목·날짜가 중복되었는지 확인한다.
    duplicates = result.duplicated(["품목", "날짜"]).sum()

    output_path = OUTPUT_DIR / "농산물_월별가격.csv"
    result.to_csv(output_path, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 50)
    print("데이터 정리 완료")
    print(f"총 행 수: {len(result)}")
    print(f"중복 행 수: {duplicates}")
    print(f"저장 위치: {output_path}")
    print("\n품목별 데이터 수:")
    print(result.groupby("품목").size().to_string())
    print("\n데이터 미리보기:")
    print(result.head(15).to_string(index=False))


if __name__ == "__main__":
    main()
