"""
main.py
-------
Run the search and write results to a human-readable TXT file.

Usage:
    python main.py --dist 3 3 2          # single distribution
    python main.py --all                 # all 5 distributions
    python main.py --all --fail-only     # only write instances with no EFX
    python main.py --all --fail-only --workers 0
"""

import argparse
from multiprocessing import Pool, cpu_count
from os import path
import sqlite3
import sys
from generator import generate_instances, generate_all, DISTRIBUTIONS
from checker import check_instance, check_instance_for_failures, format_result
from fast_search import check_pair_batch, fast_tasks, total_batches, total_instances


WORKER_FAIL_ONLY = True
WORKER_SPLIT_RESULTS = False


def category_name(result):
    if result['has_efr'] and not result['has_efx']:
        return 'efr_not_efx'
    if not result['has_efx'] and not result['has_efr']:
        return 'neither'
    return None


def split_output_files(output_file):
    prefix, suffix = path.splitext(output_file)

    return {
        'efx_not_efr': f"{prefix}_efx_not_efr{suffix}",
        'efr_not_efx': f"{prefix}_efr_not_efx{suffix}",
        'neither': f"{prefix}_neither{suffix}",
    }


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
        CREATE TABLE IF NOT EXISTS results (
            task_id INTEGER NOT NULL,
            row_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            formatted TEXT NOT NULL,
            PRIMARY KEY (task_id, row_id)
        )
    """)
    conn.commit()
    return conn


def completed_task_ids(conn):
    return {row[0] for row in conn.execute("SELECT task_id FROM completed_batches")}


def save_fast_batch(conn, task_id, checked, results):
    conn.executemany(
        "INSERT OR REPLACE INTO results (task_id, row_id, category, formatted) "
        "VALUES (?, ?, ?, ?)",
        (
            (task_id, row_id, category, formatted)
            for row_id, (category, formatted) in enumerate(results)
        ),
    )
    conn.execute(
        "INSERT OR REPLACE INTO completed_batches (task_id, checked) VALUES (?, ?)",
        (task_id, checked),
    )
    conn.commit()


def rebuild_split_outputs(conn, output_files):
    files = {category: open(output_path, 'w') for category, output_path in output_files.items()}
    counts = {category: 0 for category in output_files}

    try:
        for category, formatted in conn.execute(
            "SELECT category, formatted FROM results ORDER BY task_id, row_id"
        ):
            files[category].write(formatted)
            files[category].write("\n")
            counts[category] += 1
    finally:
        for f in files.values():
            f.close()

    return counts


def _init_worker(fail_only, split_results=False):
    global WORKER_FAIL_ONLY
    global WORKER_SPLIT_RESULTS
    WORKER_FAIL_ONLY = fail_only
    WORKER_SPLIT_RESULTS = split_results


def _check_and_format(instance):
    if WORKER_FAIL_ONLY:
        result = check_instance_for_failures(instance)
    else:
        result = check_instance(instance)

    efx_fails = not result['has_efx']
    efr_fails = not result['has_efr']
    interesting = efx_fails or efr_fails

    if WORKER_FAIL_ONLY and not interesting:
        return None

    formatted = format_result(instance, result) + "\n"
    if WORKER_SPLIT_RESULTS:
        category = category_name(result)
        if category is None:
            return None
        return category, formatted

    return formatted


def run(instances, output_file, fail_only=False, split_results=False):
    checked = 0
    written = 0
    category_counts = {
        'efx_not_efr': 0,
        'efr_not_efx': 0,
        'neither': 0,
    }

    if split_results:
        output_files = split_output_files(output_file)
        files = {category: open(path, 'w') for category, path in output_files.items()}
        primary_file = None
    else:
        output_files = None
        files = None
        primary_file = open(output_file, 'w')

    try:
        i = 0
        for inst in instances:
            i += 1
            if i % 100000 == 0:
                print(f"Checked {i} instances so far")
            if fail_only:
                result = check_instance_for_failures(inst)
            else:
                result = check_instance(inst)
            checked += 1

            efx_fails = not result['has_efx']
            efr_fails = not result['has_efr']
            interesting = efx_fails or efr_fails

            if fail_only and not interesting:
                continue

            formatted = format_result(inst, result)
            if split_results:
                category = category_name(result)
                if category is None:
                    continue
                files[category].write(formatted)
                files[category].write("\n")
                category_counts[category] += 1
            else:
                primary_file.write(formatted)
                primary_file.write("\n")
            written += 1

            if checked % 10000 == 0:
                print(f"  checked {checked}, written {written}", flush=True)
    finally:
        if split_results:
            for f in files.values():
                f.close()
        else:
            primary_file.close()

    print(f"Done. Checked {checked} instances, wrote {written} to {output_file}.")
    if split_results:
        for category, path in output_files.items():
            print(f"  {category}: {category_counts[category]} -> {path}")


def run_parallel(instances, output_file, workers, fail_only=False, chunksize=1000,
                 split_results=False):
    checked = 0
    written = 0
    category_counts = {
        'efx_not_efr': 0,
        'efr_not_efx': 0,
        'neither': 0,
    }

    if split_results:
        output_files = split_output_files(output_file)
        files = {category: open(path, 'w') for category, path in output_files.items()}
        primary_file = None
    else:
        output_files = None
        files = None
        primary_file = open(output_file, 'w')

    try:
        with Pool(processes=workers, initializer=_init_worker,
                  initargs=(fail_only, split_results)) as pool:
            for item in pool.imap_unordered(_check_and_format, instances, chunksize):
                checked += 1

                if checked % 100000 == 0:
                    print(f"Checked {checked} instances so far")

                if item is None:
                    continue

                if split_results:
                    category, formatted = item
                    files[category].write(formatted)
                    category_counts[category] += 1
                else:
                    primary_file.write(item)
                written += 1

                if checked % 10000 == 0:
                    print(f"  checked {checked}, written {written}", flush=True)
    finally:
        if split_results:
            for f in files.values():
                f.close()
        else:
            primary_file.close()

    print(f"Done. Checked {checked} instances, wrote {written} to {output_file}.")
    if split_results:
        for category, path in output_files.items():
            print(f"  {category}: {category_counts[category]} -> {path}")


def run_fast_fail_only(distributions, output_file, workers, chunksize=1, resume=True,
                        task_start=0, task_end=None):
    next_report = 100000
    output_files = split_output_files(output_file)
    db_path = checkpoint_file(output_file)
    conn = init_checkpoint(db_path)
    expected = total_instances(len(distributions))
    expected_batches = total_batches(len(distributions))
    done_ids = completed_task_ids(conn) if resume else set()
    checked = sum(
        row[0] for row in conn.execute("SELECT checked FROM completed_batches")
    ) if resume else 0

    def pending_tasks():
        for task in fast_tasks(distributions):
            task_id = task[0]
            if task_id < task_start:
                continue
            if task_end is not None and task_id >= task_end:
                continue
            if task_id not in done_ids:
                yield task

    def have_both_failures():
        neither = conn.execute("SELECT COUNT(*) FROM results WHERE category='neither'").fetchone()[0]
        efr = conn.execute("SELECT COUNT(*) FROM results WHERE category='efr_not_efx'").fetchone()[0]
        return neither > 0 and efr > 0

    try:
        if checked:
            print(f"Resuming from {db_path}: {checked}/{expected} instances complete")
            while next_report <= checked:
                next_report += 100000

        if workers == 1:
            iterator = map(check_pair_batch, pending_tasks())
            for task_id, checked_batch, results in iterator:
                save_fast_batch(conn, task_id, checked_batch, results)
                checked += checked_batch
                if checked >= next_report:
                    print(f"Checked {checked}/{expected} instances so far", flush=True)
                    while checked >= next_report:
                        next_report += 100000
                if have_both_failures():
                    print(f"Both failure types found at {checked}/{expected} instances. Stopping early.")
                    break
        else:
            with Pool(processes=workers) as pool:
                iterator = pool.imap_unordered(
                    check_pair_batch, pending_tasks(), chunksize
                )
                for task_id, checked_batch, results in iterator:
                    save_fast_batch(conn, task_id, checked_batch, results)
                    checked += checked_batch
                    if checked >= next_report:
                        print(f"Checked {checked}/{expected} instances so far", flush=True)
                        while checked >= next_report:
                            next_report += 100000
                    if have_both_failures():
                        print(f"Both failure types found at {checked}/{expected} instances. Stopping early.")
                        pool.terminate()
                        break
    finally:
        category_counts = rebuild_split_outputs(conn, output_files)
        written = sum(category_counts.values())
        print(f"Done. Checked {checked} instances, wrote {written} to {output_file}.")
        print(f"Total instances expected: {expected}")
        print(f"Total allocation checks worst-case: {expected * 1400}")
        for category, output_path in output_files.items():
            print(f"  {category}: {category_counts[category]} -> {output_path}")
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dist', nargs=3, type=int, metavar=('sA', 'sB', 'sC'),
                        help='Single distribution, e.g. --dist 3 3 2')
    parser.add_argument('--all', action='store_true',
                        help='Run over all 5 distributions')
    parser.add_argument('--fail-only', action='store_true',
                        help='Only write instances where EFX fails')
    parser.add_argument('--output', default='results.txt',
                        help='Output file (default: results.txt)')
    parser.add_argument('--split-results', action='store_true',
                        help='Write separate files for EFX-not-EFR, EFR-not-EFX, and neither')
    parser.add_argument('--workers', type=int, default=1,
                        help='Parallel worker processes. Use 0 for all CPU cores. Default: 1')
    parser.add_argument('--chunksize', type=int, default=100,
                        help='Instances sent to each worker per batch. Default: 100')
    parser.add_argument('--no-resume', action='store_true',
                        help='Ignore any existing fast-path checkpoint')
    parser.add_argument('--task-start', type=int, default=0,
                        help='First task_id to process (inclusive). For matrix splitting.')
    parser.add_argument('--task-end', type=int, default=None,
                        help='Last task_id to process (exclusive). For matrix splitting.')
    args = parser.parse_args()

    if args.all:
        instances = generate_all()
        distributions = DISTRIBUTIONS
        label = "all distributions"
    elif args.dist:
        dist = tuple(args.dist)
        if dist not in DISTRIBUTIONS:
            print(f"Unknown distribution {dist}. Valid: {DISTRIBUTIONS}")
            sys.exit(1)
        instances = generate_instances(dist)
        distributions = [dist]
        label = f"distribution {dist}"
    else:
        parser.print_help()
        sys.exit(0)

    if args.workers < 0:
        print("--workers must be >= 0")
        sys.exit(1)
    if args.chunksize < 1:
        print("--chunksize must be >= 1")
        sys.exit(1)

    workers = cpu_count() if args.workers == 0 else args.workers

    print(f"Starting search over {label}. Output -> {args.output}")
    if args.fail_only and args.split_results:
        print("Using compact batched fast path")
        run_fast_fail_only(distributions, args.output, workers, args.chunksize,
                           resume=not args.no_resume,
                           task_start=args.task_start, task_end=args.task_end)
    elif workers == 1:
        run(instances, args.output, fail_only=args.fail_only,
            split_results=args.split_results)
    else:
        print(f"Using {workers} worker processes with chunksize {args.chunksize}")
        run_parallel(instances, args.output, workers, fail_only=args.fail_only,
                     chunksize=args.chunksize, split_results=args.split_results)


if __name__ == '__main__':
    main()
