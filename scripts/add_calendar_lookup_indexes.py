"""기존 달력 SQLite에 조회 인덱스만 추가한다. 날짜 행과 중복 판정은 유지한다."""
import argparse
import json
from pathlib import Path
import sys

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from models.calenda_data import CalendaData

LOOKUP_INDEX_NAMES = (
    'ix_calenda_data_solar_date',
    'ix_calenda_data_lunar_date',
)


def add_lookup_indexes(database: Path) -> dict:
    database = Path(database).resolve()
    if not database.is_file():
        raise FileNotFoundError(f'기존 달력 DB가 없습니다: {database}')
    engine = create_engine(URL.create('sqlite', database=str(database)))
    created, existing = [], []
    try:
        with engine.begin() as connection:
            schema = inspect(connection)
            if not schema.has_table('calenda_data'):
                raise ValueError('기존 calenda_data 테이블이 필요합니다.')
            indexes = {index.name: index for index in CalendaData.__table__.indexes}
            current = {index['name']: index for index in schema.get_indexes('calenda_data')}
            # 같은 이름의 다른 인덱스를 유효한 적용으로 오인하지 않는다.
            for name in LOOKUP_INDEX_NAMES:
                expected = [column.name for column in indexes[name].columns]
                if name in current and (current[name]['column_names'] != expected or
                                        current[name]['unique'] or
                                        current[name].get('dialect_options')):
                    raise ValueError(f'{name}: 기존 인덱스 정의가 조회 계약과 다릅니다.')
            for name in LOOKUP_INDEX_NAMES:
                if name in current:
                    existing.append(name)
                else:
                    indexes[name].create(connection)
                    created.append(name)
    finally:
        engine.dispose()
    return {'created': created, 'existing': existing}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path,
                        default=Path(__file__).resolve().parents[1] / 'manseryuk.db')
    args = parser.parse_args()
    print(json.dumps(add_lookup_indexes(args.database), ensure_ascii=False))


if __name__ == '__main__':
    main()
