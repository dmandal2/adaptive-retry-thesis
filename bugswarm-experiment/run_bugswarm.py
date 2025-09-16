#!/usr/bin/env python3
"""
run_bugswarm.py
Batch-run BugSwarm Docker images, collect logs & container metrics,
and apply static vs adaptive retry policies.

Usage:
 python3 run_bugswarm.py --pair-file pair.csv --out-dir ./results --mode adaptive
"""

import argparse
import subprocess
import time
import os
import csv
import pandas as pd
import re
import datetime
import uuid
from pathlib import Path

# -------------------------
# Helpers
# -------------------------
def run_cmd(cmd, check=False, capture_output=True, text=True):
    res = subprocess.run(cmd, shell=True, check=check, capture_output=capture_output, text=text)
    return res

def choose_column(cols, candidates):
    for c in candidates:
        if c in cols:
            return c
    return None

def parse_mem_str(mem_str):
    # mem_str like "123.4MiB / 1.95GiB"
    parts = mem_str.split('/')
    if len(parts) != 2:
        return None, None
    used_s = parts[0].strip()
    total_s = parts[1].strip()
    def _to_mb(s):
        s = s.strip()
        m = re.match(r'([\d\.]+)\s*([KMGT]?i?B)', s, re.I)
        if not m:
            return None
        val = float(m.group(1))
        unit = m.group(2).lower()
        if unit.endswith('kb'):
            return val / 1024.0
        if unit.endswith('kib'):
            return val / 1024.0
        if unit.endswith('mb') or unit.endswith('mib'):
            return val
        if unit.endswith('gb') or unit.endswith('gib'):
            return val * 1024.0
        if unit.endswith('tb') or unit.endswith('tib'):
            return val * 1024.0 * 1024.0
        return val
    used_mb = _to_mb(used_s)
    total_mb = _to_mb(total_s)
    return used_mb, total_mb

def parse_cpu_str(cpu_str):
    # "12.34%" -> 12.34
    try:
        return float(cpu_str.strip().strip('%'))
    except:
        return None

def sample_stats(container_name, stop_flag, stats_list):
    # poll docker stats every 1s until stop_flag becomes True
    while not stop_flag['stop']:
        cmd = f"docker stats --no-stream --format \"{{{{.CPUPerc}}}}|{{{{.MemUsage}}}}\" {container_name}"
        res = run_cmd(cmd, check=False)
        if res.returncode == 0 and res.stdout.strip():
            out = res.stdout.strip()
            parts = out.split('|', 1)
            if len(parts) == 2:
                cpu_s, mem_s = parts[0].strip(), parts[1].strip()
                cpu = parse_cpu_str(cpu_s)
                used_mb, total_mb = parse_mem_str(mem_s)
                stats_list.append({'cpu_perc': cpu, 'used_mb': used_mb, 'total_mb': total_mb, 'raw': out, 'ts': time.time()})
        time.sleep(1)

# -------------------------
# Main run logic for a single pair
# -------------------------
def run_pair(row, args, writer):
    # row: dict-like from pandas
    pair_id = str(row.get(args.id_col) or row.get('pair_id') or str(uuid.uuid4())[:8])
    image = row.get(args.image_col)
    cmd_override = row.get(args.cmd_col) if args.cmd_col else None

    print(f"[INFO] Running pair_id={pair_id} image={image} cmd_override={cmd_override}")

    # prepare directories
    logs_dir = Path(args.out_dir) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    attempt = 0
    success = False
    final_failure_reason = ""
    attempts_meta = []

    while attempt <= args.max_retries and not success:
        attempt_name = f"{pair_id}-attempt{attempt}"
        container_name = f"bs_{pair_id}_{int(time.time())}_{attempt}"

        # pull image
        print(f"[INFO] Pulling image {image} (attempt {attempt})")
        run_cmd(f"docker pull {image}", check=False)

        # run container (detached)
        if cmd_override and not pd.isna(cmd_override):
            run_cmd(f"docker run --name {container_name} -d {image} /bin/bash -c \"{cmd_override}\"", check=False)
        else:
            # assume image's default entrypoint runs tests
            run_cmd(f"docker run --name {container_name} -d {image}", check=False)

        # sample stats while container runs
        stats_list = []
        stop_flag = {'stop': False}
        import threading
        sampler = threading.Thread(target=sample_stats, args=(container_name, stop_flag, stats_list))
        sampler.start()

        # wait for container to finish
        wait_res = run_cmd(f"docker wait {container_name}", check=False)
        exit_code = None
        if wait_res.returncode == 0 and wait_res.stdout.strip().isdigit():
            exit_code = int(wait_res.stdout.strip())
        else:
            # fallback: try inspect
            insp = run_cmd(f"docker inspect --format='{{{{.State.ExitCode}}}}' {container_name}", check=False)
            try:
                exit_code = int(insp.stdout.strip())
            except:
                exit_code = -1

        # stop sampler
        stop_flag['stop'] = True
        sampler.join(timeout=5)

        # collect logs
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        logfile = logs_dir / f"{pair_id}_attempt{attempt}_{ts}.log"
        logs = run_cmd(f"docker logs {container_name}", check=False)
        with open(logfile, "w", encoding="utf-8") as f:
            f.write("-- DOCKER LOGS START --\n")
            f.write(logs.stdout if logs.stdout else "")
            f.write("\n-- DOCKER LOGS END --\n")

        # try to parse failure type from logs (first Exception/Error)
        log_text = logs.stdout or ""
        m = re.search(r'([A-Za-z0-9_\.]+(?:Exception|Error))', log_text)
        failure_type = m.group(1) if m else ""

        # compute metrics from stats_list
        cpu_vals = [s['cpu_perc'] for s in stats_list if s['cpu_perc'] is not None]
        used_vals = [s['used_mb'] for s in stats_list if s['used_mb'] is not None]
        total_vals = [s['total_mb'] for s in stats_list if s['total_mb'] is not None]

        max_cpu = max(cpu_vals) if cpu_vals else None
        max_used = max(used_vals) if used_vals else None
        total_mem = total_vals[0] if total_vals else None
        avail_mem = (total_mem - max_used) if (total_mem is not None and max_used is not None) else None

        # remove container to free resources
        run_cmd(f"docker rm -f {container_name}", check=False)

        attempts_meta.append({
            'attempt': attempt,
            'exit_code': exit_code,
            'logfile': str(logfile),
            'failure_type': failure_type,
            'max_cpu': max_cpu,
            'max_used_mb': max_used,
            'total_mb': total_mem,
            'avail_mb': avail_mem
        })

        # decide success/failure and retry logic
        if exit_code == 0:
            success = True
            final_failure_reason = ""
            print(f"[INFO] pair {pair_id} success on attempt {attempt}")
            break
        else:
            final_failure_reason = failure_type or f"exit_code_{exit_code}"
            print(f"[WARN] pair {pair_id} failed on attempt {attempt} (exit={exit_code}) failure_type={failure_type}")
            # decide retry
            if attempt < args.max_retries:
                if args.mode == 'static':
                    do_retry = True
                else:  # adaptive
                    # only retry if CPU not too high AND available memory >= threshold
                    cpu_ok = (max_cpu is None) or (max_cpu <= args.cpu_threshold)
                    mem_ok = (avail_mem is None) or (avail_mem >= args.mem_threshold)
                    do_retry = cpu_ok and mem_ok
                    if not do_retry:
                        print(f"[ADAPTIVE] Not retrying due to metrics: max_cpu={max_cpu}, avail_mb={avail_mem}")
                if do_retry:
                    attempt += 1
                    # short backoff before retry
                    time.sleep(args.retry_backoff)
                    continue
                else:
                    # do not retry further
                    break
            else:
                # no retries left
                break

    # write summary row to results CSV via writer (csv.DictWriter)
    summary = {
        'pair_id': pair_id,
        'image': image,
        'mode': args.mode,
        'attempts_total': attempt + (1 if success else 1),  # approximate
        'success': bool(success),
        'final_failure': final_failure_reason,
        'max_cpu': max_cpu,
        'max_used_mb': max_used,
        'total_mb': total_mem,
        'avail_mb': avail_mem,
        'attempts_meta': str(attempts_meta)
    }
    writer.writerow(summary)
    # flush
    args.out_csv_f.flush()
    return summary

# -------------------------
# CLI
# -------------------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--pair-file', required=True, help='pair.csv from BugSwarm')
    p.add_argument('--out-dir', default='./results', help='output folder (logs, plots, results.csv)')
    p.add_argument('--mode', choices=['static', 'adaptive'], default='adaptive', help='retry mode')
    p.add_argument('--max-retries', type=int, default=2, help='max retry attempts (per pair)')
    p.add_argument('--cpu-threshold', type=float, default=85.0, help='CPU percent threshold for adaptive retries')
    p.add_argument('--mem-threshold', type=float, default=100.0, help='Available memory threshold (MB) for adaptive retries')
    p.add_argument('--retry-backoff', type=int, default=5, help='seconds to wait before retrying')
    p.add_argument('--id-col', default=None, help='column name to use as pair id if present')
    p.add_argument('--image-col', default=None, help='column name for docker image (if omitted script will try to auto-detect)')
    p.add_argument('--cmd-col', default=None, help='(optional) column name containing an override test command to run in the image')
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "logs").mkdir(parents=True, exist_ok=True)
    results_csv = out_dir / "results.csv"

    # read pair file
    df = pd.read_csv(args.pair_file)
    cols = [c.lower() for c in df.columns]

    # auto-detect columns if not provided
    image_candidates = [args.image_col, 'image', 'image_name', 'docker_image', 'docker_img']
    cmd_candidates = [args.cmd_col, 'test_command', 'command', 'cmd', 'run_cmd']
    id_candidates = [args.id_col, 'pair_id', 'id', 'pair']

    # normalize detection (case-insensitive)
    image_col = args.image_col or choose_column(df.columns, [c for c in ['image','image_name','docker_image','docker_img'] if c in df.columns])
    if image_col is None:
        # check lowercase matches
        for c in df.columns:
            if c.lower() in ['image','image_name','docker_image','docker_img']:
                image_col = c; break
    if image_col is None:
        raise SystemExit("[ERROR] Could not detect an image column. Please specify --image-col explicitly.")

    cmd_col = None
    for c in df.columns:
        if c.lower() in ['test_command','command','cmd','run_cmd']:
            cmd_col = c; break

    id_col = None
    for c in df.columns:
        if c.lower() in ['pair_id','id','pair']:
            id_col = c; break

    args.image_col = image_col
    args.cmd_col = cmd_col
    args.id_col = id_col

    # prepare CSV writer
    fieldnames = ['pair_id','image','mode','attempts_total','success','final_failure','max_cpu','max_used_mb','total_mb','avail_mb','attempts_meta']
    out_csv_f = open(results_csv, 'a', newline='', encoding='utf-8')
    args.out_csv_f = out_csv_f
    writer = csv.DictWriter(out_csv_f, fieldnames=fieldnames)
    # write header if empty
    if results_csv.exists() and results_csv.stat().st_size == 0:
        writer.writeheader()

    # iterate rows sequentially (safer on small EC2)
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        try:
            run_pair(row_dict, args, writer)
        except Exception as e:
            print(f"[ERROR] exception while processing row idx={idx}: {e}")

    out_csv_f.close()
    print("[DONE] Batch run complete. Results in:", results_csv)

if __name__ == '__main__':
    main()

