
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/raw")

files = sorted(
    list(DATA_DIR.glob("*.xls"))
    + list(DATA_DIR.glob("*.xlsx"))
)

print(f"총 {len(files)}개 파일을 찾았습니다.")

for file in files:
    print("\n" + "=" * 60)
    print("파일명:", file.name)

    try:
        # .xls 확장자를 가진 HTML 표를 읽기
        tables = pd.read_html(
            file,
            encoding="utf-8"
        )

        print(f"표 개수: {len(tables)}")

        for i, df in enumerate(tables):
            print(f"\n[표 {i + 1}]")
            print("행과 열:", df.shape)
            print("열 이름:", df.columns.tolist())
            print(df.head(10).to_string(index=False))

    except Exception as e:
        print("읽기 오류:", e)
