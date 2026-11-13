"""읽기 전용 달력 DB로 루트 응답의 크기와 TestClient 처리 시간을 측정한다."""
import argparse
import json
from pathlib import Path
import statistics
import sys
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session
from core.dependencies import get_db
from main import app

SAMPLES = (
    dict(year=1995, month='5', day='12', hour=14, min=30, sl='sol', gen='남'),
    dict(year=1990, month='1', day='8', hour=18, min=0, sl='sol', gen='남'),
    dict(year=2023, month='2', day='1', hour=0, min=0, sl='lun_y', gen='여'),
    dict(year=2000, month='2', day='29', hour=23, min=59, sl='sol', gen='남'),
)


def measure(database: Path, repeat: int) -> list[dict]:
    database = Path(database).resolve()
    if not database.is_file():
        raise FileNotFoundError(f'기존 달력 DB가 없습니다: {database}')
    if repeat < 1:
        raise ValueError('반복 횟수는 1 이상이어야 합니다.')
    # SQLite URI의 file: 접두어와 mode=ro로 원본 데이터의 쓰기를 차단한다.
    engine = create_engine(URL.create('sqlite', database=database.as_uri(),
                                     query={'mode': 'ro', 'uri': 'true'}))

    def readonly_db():
        with Session(engine) as session:
            yield session

    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = readonly_db
    results = []
    try:
        with TestClient(app) as client:
            for params in SAMPLES:
                response = client.get('/', params=params)
                response.raise_for_status()
                timings = []
                for _ in range(repeat):
                    start = perf_counter()
                    response = client.get('/', params=params)
                    timings.append((perf_counter() - start) * 1000)
                    response.raise_for_status()
                body = response.json()
                results.append({
                    'input': params, 'repeat': repeat,
                    'median_ms': round(statistics.median(timings), 2),
                    'response_bytes': len(response.content),
                    'section_bytes': {key: len(json.dumps(value, ensure_ascii=False,
                                                         separators=(',', ':')).encode())
                                      for key, value in body.items()},
                })
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous
        engine.dispose()
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path,
                        default=Path(__file__).resolve().parents[1] / 'manseryuk.db')
    parser.add_argument('--repeat', type=int, default=8)
    args = parser.parse_args()
    if args.repeat < 1:
        parser.error('--repeat는 1 이상이어야 합니다.')
    print(json.dumps(measure(args.database, args.repeat), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
