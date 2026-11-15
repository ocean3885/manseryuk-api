"""일주·월지 공통 해설의 영속 대기열과 조회."""
from contextlib import closing
from pathlib import Path
import sqlite3
import time

from core.interpretation_database import DEFAULT_DATABASE, ensure_database

STEMS = '甲乙丙丁戊己庚辛壬癸'
BRANCHES = '子丑寅卯辰巳午未申酉戌亥'
LEASE_SECONDS = 120
RETRY_SECONDS = 3600


def validate_pair(day_pillar: str, month_branch: str):
    if (not isinstance(day_pillar, str) or len(day_pillar) != 2 or
            day_pillar[0] not in STEMS or day_pillar[1] not in BRANCHES or
            STEMS.index(day_pillar[0]) % 2 != BRANCHES.index(day_pillar[1]) % 2 or
            not isinstance(month_branch, str) or month_branch not in BRANCHES):
        raise ValueError('유효한 60갑자 일주와 월지가 필요합니다.')


def lookup_or_queue(day_pillar: str, month_branch: str,
                    database: Path = DEFAULT_DATABASE) -> tuple[str | None, bool]:
    """완성본과 생성 필요 여부를 반환한다. 없는 파일은 생성한다."""
    validate_pair(day_pillar, month_branch)
    path = ensure_database(database)
    now = int(time.time())
    with closing(sqlite3.connect(path, timeout=10)) as connection, connection:
        row = connection.execute('''SELECT explanation, status, retry_after
            FROM day_month_interpretations WHERE day_pillar=? AND month_branch=?''',
            (day_pillar, month_branch)).fetchone()
        if row is None:
            connection.execute('''INSERT OR IGNORE INTO day_month_interpretations
                (day_pillar, month_branch, status, updated_at) VALUES (?, ?, 'pending', ?)''',
                (day_pillar, month_branch, now))
            row = connection.execute('''SELECT explanation, status, retry_after
                FROM day_month_interpretations WHERE day_pillar=? AND month_branch=?''',
                (day_pillar, month_branch)).fetchone()
    if row[1] == 'ready':
        return row[0], False
    return None, row[1] == 'pending' or row[2] <= now


def claim_generation(day_pillar: str, month_branch: str,
                     database: Path = DEFAULT_DATABASE) -> int | None:
    """동시 요청 중 하나만 외부 생성 호출을 진행한다."""
    validate_pair(day_pillar, month_branch)
    now = int(time.time())
    with closing(sqlite3.connect(database, timeout=10)) as connection, connection:
        updated = connection.execute('''UPDATE day_month_interpretations
            SET status='generating', attempts=attempts+1, retry_after=?, updated_at=?
            WHERE day_pillar=? AND month_branch=? AND
            (status='pending' OR (status IN ('failed','generating') AND retry_after<=?))''',
            (now + LEASE_SECONDS, now, day_pillar, month_branch, now))
        if updated.rowcount != 1:
            return None
        return connection.execute('''SELECT attempts FROM day_month_interpretations
            WHERE day_pillar=? AND month_branch=?''', (day_pillar, month_branch)).fetchone()[0]


def finish_generation(day_pillar: str, month_branch: str, attempt: int,
                      explanation: str, model_name: str,
                      database: Path = DEFAULT_DATABASE) -> bool:
    if not isinstance(explanation, str) or not explanation.strip():
        raise ValueError('빈 해설을 저장할 수 없습니다.')
    with closing(sqlite3.connect(database, timeout=10)) as connection, connection:
        changed = connection.execute('''UPDATE day_month_interpretations
            SET status='ready', explanation=?, model_name=?, retry_after=0, updated_at=?
            WHERE day_pillar=? AND month_branch=? AND status='generating' AND attempts=?''',
            (explanation.strip(), model_name, int(time.time()), day_pillar, month_branch, attempt))
        return changed.rowcount == 1


def fail_generation(day_pillar: str, month_branch: str, attempt: int,
                    database: Path = DEFAULT_DATABASE):
    now = int(time.time())
    with closing(sqlite3.connect(database, timeout=10)) as connection, connection:
        connection.execute('''UPDATE day_month_interpretations
            SET status='failed', retry_after=?, updated_at=?
            WHERE day_pillar=? AND month_branch=? AND status='generating' AND attempts=?''',
            (now + RETRY_SECONDS, now, day_pillar, month_branch, attempt))
