"""
main.py
-------
Search for EFX/EFR counterexamples with 5 types of goods (2,2,2,1,1).

Two modes:
  1. Singletons fixed at 1 (default): fast, ~15B instances
  2. Vary singletons (--vary-singletons): exhaustive, much larger

Usage:
    python main.py --all --workers 0
    python main.py --all --workers 2 --max-pair-val 4
    python main.py --all --vary-singletons --workers 0
"""

import argparse
import sqlite3
import sys
import time
from multiprocessing import Pool, cpu_count
from os import path

from fast_search import (
    check_pair_batch, fast_tasks, total_batches, total_instances,
    format_instance, CANONICAL_EXC_MASKS, generate_singleton_combos,
    count_singleton_combos,
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


def process_result(result_type, pv, em, sv, no_efx, no_efr, conn):
    formatted = format_instance(pv, em, sv)
    if result_type == 'efr_not_efx':
        if not no_efx:
            no_efx = True
            save_counterexample(conn, 'efr_not_efx', formatted)
            print(f"  FOUND no-EFX instance (has EFR)!")
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
    parser = argparse.ArgumentParser(
        description="Search for EFX/EFR counterexamples (5 types: 2,2,2,1,1)")
    parser.add_argument('--all', action='store_true', help='Run the search')
    parser.add_argument('--output', default='results.txt', help='Output file base name')
    parser.add_argument('--workers', type=int, default=1,
                        help='Parallel workers. 0 = all CPU cores. Default: 1')
    parser.add_argument('--max-pair-val', type=int, default=6,
                        help='Maximum pair value (1-6). Default: 6.')
    parser.add_argument('--vary-singletons', action='store_true',
                        help='Search over all singleton value combos (much larger)')
    parser.add_argument('--sleep', type=float, default=0,
                        help='Seconds to sleep between batches. Default: 0')
    parser.add_argument('--no-resume', action='store_true',
                        help='Ignore existing checkpoint')
    parser.add_argument('--task-start', type=int, default=0,
                        help='First task_id to process (inclusive).')
    parser.add_argument('--task-end', type=int, default=None,
                        help='Last task_id to process (exclusive).')
    args = parser.parse_args()

    if not args.all:
        parser.print_help()
        sys.exit(0)

    if args.max_pair_val < 1 or args.max_pair_val > 6:
        print("--max-pair-val must be between 1 and 6")
        sys.exit(1)

    workers = cpu_count() if args.workers == 0 else args.workers
    db_path = checkpoint_file(args.output)
    conn = init_checkpoint(db_path)
    done_ids = set() if args.no_resume else completed_task_ids(conn)

    # Build singleton combos
    if args.vary_singletons:
        singleton_combos = list(generate_singleton_combos())
        n_singletons = len(singleton_combos)
    else:
        singleton_combos = None
        n_singletons = 1

    all_expected_batches = total_batches(args.max_pair_val, n_singletons)
    all_expected = total_instances(args.max_pair_val, n_singletons)
    task_end = args.task_end if args.task_end is not None else all_expected_batches

    expected_batches_in_range = max(0, task_end - args.task_start)
    n_exc = len(CANONICAL_EXC_MASKS[DISTRIBUTIONS[0]])
    expected = expected_batches_in_range * (n_exc + 1) if DISTRIBUTIONS else 0

    total_checked = sum(
        row[0] for row in conn.execute("SELECT checked FROM completed_batches")
    ) if not args.no_resume else 0

    no_efx = has_counterexample(conn, 'efr_not_efx') or has_counterexample(conn, 'neither')
    no_efr = has_counterexample(conn, 'neither')

    next_report = 100000
    if total_checked:
        print(f"Resuming: {total_checked:,}/{expected:,} instances checked")
        while next_report <= total_checked:
            next_report += 100000

    def pending():
        for ft_id, pv, sv in fast_tasks(args.max_pair_val, singleton_combos):
            if ft_id < args.task_start:
                continue
            if ft_id >= task_end:
                break
            if ft_id not in done_ids:
                yield ft_id, pv, sv

    mode = "vary-singletons" if args.vary_singletons else "singletons=1"
    print(f"Search: distribution (2,2,2,1,1), mode={mode}, max_pair_val={args.max_pair_val}")
    print(f"Workers: {workers}")
    print(f"Task range: [{args.task_start}, {task_end}) of {all_expected_batches}")
    print(f"Instances in range: {expected:,}")
    print(f"Checkpoint: {db_path}")
    print()

    try:
        if workers == 1:
            for task_id, checked_batch, results in map(check_pair_batch, pending()):
                total_checked += checked_batch
                save_batch(conn, task_id, checked_batch)
                for result_type, pv, em, sv in results:
                    no_efx, no_efr = process_result(
                        result_type, pv, em, sv, no_efx, no_efr, conn
                    )
                if args.sleep > 0:
                    time.sleep(args.sleep)
                if total_checked >= next_report:
                    print(f"  {total_checked:,}/{expected:,} checked", flush=True)
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
                    for result_type, pv, em, sv in results:
                        no_efx, no_efr = process_result(
                            result_type, pv, em, sv, no_efx, no_efr, conn
                        )
                    if args.sleep > 0:
                        time.sleep(args.sleep)
                    if total_checked >= next_report:
                        print(f"  {total_checked:,}/{expected:,} checked", flush=True)
                        while next_report <= total_checked:
                            next_report += 100000
                    if no_efx and no_efr:
                        pool.terminate()
                        print("\nBoth counterexamples found! Stopping.")
                        break
    except KeyboardInterrupt:
        print(f"\nInterrupted. {total_checked:,}/{expected:,} checked.")
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
