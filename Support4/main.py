"""
main.py
-------
Search for counterexamples to EFX/EFR with 4 types of goods.

Features:
  - Multiprocessing: --workers 0 uses all CPU cores
  - Checkpointing: progress saved to SQLite, resume on interruption
  - Early stopping: finds ONE no-EFX and ONE no-EFR instance, then stops
  - CPU throttling: --sleep to yield between batches

Usage:
    python main.py --all --workers 0
    python main.py --all --workers 2 --sleep 0.1
    python main.py --dist 3 2 2 1 --workers 4
    python main.py --all --workers 0 --no-resume
"""

import argparse
import sqlite3
import sys
import time
from multiprocessing import Pool, cpu_count
from os import path

from fast_search import (
    check_pair_batch, fast_tasks, total_batches, total_instances,
    format_instance, CANONICAL_SEARCH,
)
from instance import DISTRIBUTIONS


def checkpoint_file(output_file):
    return f"{output_file}.checkpoint.sqlite3"


def init_checkpoint(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS completed_batches (
            task_id INTEGER PRIMARY KEY,
            checked INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS counterexamples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            formatted TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def completed_task_ids(conn):
    return {row[0] for row in conn.execute("SELECT task_id FROM completed_batches")}


def has_counterexample(conn, category):
    return conn.execute(
        "SELECT 1 FROM counterexamples WHERE category=? LIMIT 1", (category,)
    ).fetchone() is not None


def save_counterexample(conn, category, formatted):
    conn.execute(
        "INSERT INTO counterexamples (category, formatted) VALUES (?, ?)",
        (category, formatted),
    )
    conn.commit()


def save_batch(conn, task_id, checked):
    conn.execute(
        "INSERT OR REPLACE INTO completed_batches (task_id, checked) VALUES (?, ?)",
        (task_id, checked),
    )
    conn.commit()


def write_results(conn, output_file):
    prefix, suffix = path.splitext(output_file)
    categories = {
        'efr_not_efx': f"{prefix}_efr_not_efx{suffix}",
        'neither': f"{prefix}_neither{suffix}",
    }
    counts = {}
    for cat, fpath in categories.items():
        rows = conn.execute(
            "SELECT formatted FROM counterexamples WHERE category=? ORDER BY id", (cat,)
        ).fetchall()
        with open(fpath, 'w') as f:
            for (formatted,) in rows:
                f.write(formatted + "\n\n")
        counts[cat] = len(rows)
        if rows:
            print(f"  {cat}: {counts[cat]} -> {fpath}")
    return counts


def process_result(result_type, dist, pv, em, no_efx, no_efr, conn):
    formatted = format_instance(dist, pv, em)
    if result_type == 'efr_not_efx':
        if not no_efx:
            no_efx = True
            save_counterexample(conn, 'efr_not_efx', formatted)
            print(f"  FOUND no-EFX instance!")
    elif result_type == 'neither':
        if not no_efr:
            no_efr = True
            save_counterexample(conn, 'neither', formatted)
            print(f"  FOUND no-EFR instance!")
        if not no_efx:
            no_efx = True
            print(f"  FOUND no-EFX instance!")
    return no_efx, no_efr


def main():
    parser = argparse.ArgumentParser(description="Search for EFX/EFR counterexamples (4 types)")
    parser.add_argument('--dist', nargs=4, type=int, metavar=('sA', 'sB', 'sC', 'sD'))
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--output', default='results.txt')
    parser.add_argument('--workers', type=int, default=1,
                        help='Parallel workers. 0 = all CPU cores. Default: 1')
    parser.add_argument('--sleep', type=float, default=0,
                        help='Seconds to sleep between batches (CPU throttling). Default: 0')
    parser.add_argument('--no-resume', action='store_true')
    parser.add_argument('--task-start', type=int, default=0,
                        help='First task_id to process (inclusive). For matrix splitting.')
    parser.add_argument('--task-end', type=int, default=None,
                        help='Last task_id to process (exclusive). For matrix splitting.')
    args = parser.parse_args()

    if args.all:
        distributions = DISTRIBUTIONS
    elif args.dist:
        dist = tuple(args.dist)
        if dist not in DISTRIBUTIONS:
            print(f"Unknown distribution {dist}. Valid: {DISTRIBUTIONS}")
            sys.exit(1)
        distributions = [dist]
    else:
        parser.print_help()
        sys.exit(0)

    workers = cpu_count() if args.workers == 0 else args.workers
    db_path = checkpoint_file(args.output)
    conn = init_checkpoint(db_path)
    done_ids = set() if args.no_resume else completed_task_ids(conn)
    all_expected = total_instances(len(distributions))
    all_expected_batches = total_batches(len(distributions))
    task_end = args.task_end if args.task_end is not None else all_expected_batches

    expected_batches_in_range = max(0, task_end - args.task_start)
    expected = expected_batches_in_range * len(CANONICAL_SEARCH[distributions[0]]['exc_masks']) if distributions else 0

    total_checked = sum(
        row[0] for row in conn.execute("SELECT checked FROM completed_batches")
    ) if not args.no_resume else 0

    no_efx = has_counterexample(conn, 'efr_not_efx') or has_counterexample(conn, 'neither')
    no_efr = has_counterexample(conn, 'neither')

    next_report = 100000
    if total_checked:
        print(f"Resuming: {total_checked}/{expected} instances checked")
        while next_report <= total_checked:
            next_report += 100000

    def pending():
        for task in fast_tasks(distributions):
            tid = task[0]
            if tid < args.task_start or tid >= task_end:
                continue
            if tid not in done_ids:
                yield task

    print(f"Searching {len(distributions)} distribution(s), {workers} worker(s)")
    if args.sleep > 0:
        print(f"CPU throttling: {args.sleep}s sleep between batches")
    print(f"Task range: [{args.task_start}, {task_end}) of {all_expected_batches}")
    print(f"Instances in range: {expected:,}")
    print(f"Checkpoint: {db_path}")
    print()

    try:
        if workers == 1:
            for task_id, checked_batch, results in map(check_pair_batch, pending()):
                total_checked += checked_batch
                save_batch(conn, task_id, checked_batch)
                for result_type, dist, pv, em in results:
                    no_efx, no_efr = process_result(
                        result_type, dist, pv, em, no_efx, no_efr, conn
                    )
                if args.sleep > 0:
                    time.sleep(args.sleep)
                if total_checked >= next_report:
                    print(f"  {total_checked}/{expected} checked", flush=True)
                    while next_report <= total_checked:
                        next_report += 100000
                if no_efx and no_efr:
                    print("\nBoth counterexamples found! Stopping.")
                    break
        else:
            with Pool(processes=workers) as pool:
                for task_id, checked_batch, results in pool.imap_unordered(
                    check_pair_batch, pending(), chunksize=1
                ):
                    total_checked += checked_batch
                    save_batch(conn, task_id, checked_batch)
                    for result_type, dist, pv, em in results:
                        no_efx, no_efr = process_result(
                            result_type, dist, pv, em, no_efx, no_efr, conn
                        )
                    if args.sleep > 0:
                        time.sleep(args.sleep)
                    if total_checked >= next_report:
                        print(f"  {total_checked}/{expected} checked", flush=True)
                        while next_report <= total_checked:
                            next_report += 100000
                    if no_efx and no_efr:
                        pool.terminate()
                        print("\nBoth counterexamples found! Stopping.")
                        break
    except KeyboardInterrupt:
        print(f"\nInterrupted. {total_checked}/{expected} checked.")
    finally:
        print(f"\nWriting results to {args.output}...")
        counts = write_results(conn, args.output)
        print(f"\nFinal: {total_checked:,}/{expected:,} instances checked")
        if no_efx or no_efr:
            print("Counterexamples found:")
            for cat, c in counts.items():
                if c:
                    print(f"  {cat}: {c}")
        else:
            print("No counterexamples found yet. Resume with the same command.")
        conn.close()


if __name__ == '__main__':
    main()
