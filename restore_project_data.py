from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

TABLES = [
    "auth_user",
    "events_category",
    "events_userprofile",
    "events_event",
    "events_rsvp",
    "events_comment",
    "events_favoriteevent",
    "events_eventhistory",
]

def table_exists(conn: sqlite3.Connection, schema: str, table: str) -> bool:
    row = conn.execute(
        f"SELECT 1 FROM {schema}.sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None

def columns(conn: sqlite3.Connection, schema: str, table: str) -> list[str]:
    return [row[1] for row in conn.execute(f"PRAGMA {schema}.table_info('{table}')")]

def count(conn: sqlite3.Connection, schema: str, table: str) -> int:
    return conn.execute(f'SELECT COUNT(*) FROM {schema}."{table}"').fetchone()[0]

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safely merge recovered Windsor project data into the current Django SQLite database."
    )
    parser.add_argument(
        "--target",
        default="db.sqlite3",
        help="Current Django database path (default: db.sqlite3)",
    )
    parser.add_argument(
        "--source",
        default="RECOVERED_DATA.sqlite3",
        help="Recovered database path (default: RECOVERED_DATA.sqlite3)",
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    source = Path(args.source).resolve()

    if not target.exists():
        print(f"ERROR: Target database not found: {target}")
        return 1
    if not source.exists():
        print(f"ERROR: Recovery database not found: {source}")
        return 1
    if target == source:
        print("ERROR: Source and target databases must be different files.")
        return 1

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = target.with_name(f"{target.stem}_before_restore_{timestamp}{target.suffix}")
    shutil.copy2(target, backup)
    print(f"Safety backup created: {backup}")

    conn = sqlite3.connect(target)
    try:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("ATTACH DATABASE ? AS recovered", (str(source),))

        for table in TABLES:
            if not table_exists(conn, "main", table):
                print(f"SKIP {table}: target table does not exist")
                continue
            if not table_exists(conn, "recovered", table):
                print(f"SKIP {table}: recovery table does not exist")
                continue

            main_cols = columns(conn, "main", table)
            recovered_cols = columns(conn, "recovered", table)
            common_cols = [col for col in main_cols if col in recovered_cols]

            if not common_cols:
                print(f"SKIP {table}: no matching columns")
                continue

            quoted = ", ".join(f'"{col}"' for col in common_cols)
            before = count(conn, "main", table)

            conn.execute(f'DELETE FROM main."{table}"')
            conn.execute(
                f'INSERT INTO main."{table}" ({quoted}) '
                f'SELECT {quoted} FROM recovered."{table}"'
            )

            after = count(conn, "main", table)
            recovered_count = count(conn, "recovered", table)
            print(
                f"RESTORED {table}: target before={before}, "
                f"recovered={recovered_count}, target after={after}"
            )

        conn.commit()
        conn.execute("DETACH DATABASE recovered")
    except Exception:
        conn.rollback()
        print("Restore failed. The safety backup was not changed.")
        raise
    finally:
        conn.close()

    print("\nRestore completed.")
    print("Expected key totals: Category=5, Event=11, RSVP=1, FavoriteEvent=1, EventHistory=5.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
