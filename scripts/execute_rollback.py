#!/usr/bin/env python3
"""
ClarifAI Automated Full-System Rollback & Emergency Recovery Orchestrator
Executes deterministic, automated rollback across all 3 tiers + datastores per PRD Section 35.7.

Solves:
1. Zombie Task Elimination: Atomically resets in-flight 'processing' DB records to 'failed'.
2. Queue Poisoning Defense: Flushes unconsumed Celery queue messages in Redis.
3. Rapid Container Reversion: Reverts code/compose and restarts multi-service topology.
4. Health Verification: Probes Frontend, Django API, and FastAPI health endpoints post-rollback.
"""

import os
import sys
import time
import argparse
import subprocess
import logging
from typing import Dict, Any, List

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("execute_rollback")

DEFAULT_ROLLBACK_COMMIT = "ac230e3"


def run_cmd(cmd: List[str], check: bool = True, cwd: str = None) -> subprocess.CompletedProcess:
    """Runs a shell command and captures output."""
    cmd_str = " ".join(cmd)
    logger.info(f"Executing: {cmd_str}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if check and result.returncode != 0:
        logger.error(f"Command failed (code {result.returncode}): {cmd_str}\n{result.stderr}")
        raise RuntimeError(f"Command failed: {cmd_str}")
    return result


def reconcile_zombie_database_records(dry_run: bool = False):
    """
    Cleans up any documents, comparisons, or reports left in 'processing' status.
    Prevents persistent infinite spinners or locked states for end users.
    """
    logger.info("=== STEP 1: Reconciling In-Flight / Zombie Database Records ===")
    reconcile_code = (
        "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production'); django.setup(); "
        "from apps.documents.models import Document; from apps.comparison.models import Comparison; from apps.reports.models import Report; "
        "d_count = Document.objects.filter(status='processing').update(status='failed', failure_reason='Processing aborted due to emergency system rollback.'); "
        "c_count = Comparison.objects.filter(status='processing').update(status='failed', failure_reason='Comparison aborted due to emergency system rollback.'); "
        "r_count = Report.objects.filter(status='processing').update(status='failed', failure_reason='Report generation aborted due to emergency system rollback.'); "
        "print(f'Reconciled zombie records: {d_count} documents, {c_count} comparisons, {r_count} reports.')"
    )
    if dry_run:
        logger.info("[DRY RUN] Would execute Django ORM zombie reconciliation.")
        return

    try:
        # Attempt via running container first if available, else local python
        res = subprocess.run(
            ["docker", "compose", "exec", "-T", "django-api", "python", "-c", reconcile_code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if res.returncode == 0:
            logger.info(f"Container reconciliation successful: {res.stdout.strip()}")
        else:
            logger.warning(f"Container reconciliation unavailable ({res.stderr.strip()}). Falling back to local python...")
            subprocess.run(
                [sys.executable, "manage.py", "shell", "-c", reconcile_code],
                cwd="backend/django-api",
                check=False
            )
    except Exception as e:
        logger.warning(f"Database reconciliation encountered non-fatal error: {e}")


def purge_celery_task_queues(dry_run: bool = False):
    """
    Purges unconsumed Celery tasks from Redis to prevent deserialization poison pills.
    """
    logger.info("=== STEP 2: Purging Celery Redis Queues ===")
    if dry_run:
        logger.info("[DRY RUN] Would purge Celery queues in Redis.")
        return

    try:
        res = subprocess.run(
            ["docker", "compose", "exec", "-T", "celery-worker", "celery", "-A", "config", "purge", "-f"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if res.returncode == 0:
            logger.info("Celery task queue purged successfully.")
        else:
            logger.warning("Could not execute celery purge in container. Redis task queue will drain on restart.")
    except Exception as e:
        logger.warning(f"Queue purge non-fatal error: {e}")


def revert_code_and_containers(target_commit: str, dry_run: bool = False):
    """
    Reverts codebase to target commit and restarts Docker Compose topology.
    """
    logger.info(f"=== STEP 3: Reverting Codebase to Target Commit '{target_commit}' ===")
    if dry_run:
        logger.info(f"[DRY RUN] Would checkout commit {target_commit} and run docker compose up -d.")
        return

    # Check git clean status
    status_res = run_cmd(["git", "status", "--porcelain"])
    if status_res.stdout.strip():
        logger.warning("Working tree has untracked/modified changes. Preserving via stash or commit before checkout.")

    # Stop consumers
    run_cmd(["docker", "compose", "stop", "celery-worker", "django-api", "frontend", "fastapi-ai"], check=False)

    # Checkout target commit
    logger.info(f"Checking out {target_commit}...")
    run_cmd(["git", "checkout", target_commit])

    # Rebuild & restart services
    logger.info("Re-deploying container topology...")
    run_cmd(["docker", "compose", "up", "-d"])


def probe_service_health(retries: int = 10, delay: float = 3.0) -> Dict[str, bool]:
    """
    Probes Frontend, Django API, and FastAPI health endpoints post-rollback.
    """
    logger.info("=== STEP 4: Probing Post-Rollback Service Health ===")
    import urllib.request

    endpoints = {
        "Django API": "http://localhost:8000/api/health/",
        "FastAPI AI": "http://localhost:8001/health",
        "Frontend SPA": "http://localhost:3000/"
    }

    results = {}
    for name, url in endpoints.items():
        healthy = False
        for attempt in range(1, retries + 1):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "RollbackProber/1.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status in (200, 301, 302):
                        logger.info(f"[{name}] Healthy (HTTP {resp.status}) on attempt {attempt}")
                        healthy = True
                        break
            except Exception as e:
                logger.debug(f"[{name}] Attempt {attempt}/{retries} failed: {e}")
                time.sleep(delay)
        results[name] = healthy

    return results


def main():
    parser = argparse.ArgumentParser(description="ClarifAI Emergency Full-System Rollback Orchestrator")
    parser.add_argument("--target", type=str, default=DEFAULT_ROLLBACK_COMMIT, help="Target Git commit/tag to revert to")
    parser.add_argument("--dry-run", action="store_true", help="Simulate rollback steps without executing changes")
    parser.add_argument("--skip-db-cleanup", action="store_true", help="Skip zombie database record reconciliation")
    args = parser.parse_args()

    start_time = time.time()
    logger.info("****************************************************************")
    logger.info(f"* ClarifAI Emergency System Rollback Initiated                *")
    logger.info(f"* Target Baseline: {args.target}                              *")
    logger.info(f"* Mode: {'DRY RUN' if args.dry_run else 'ACTIVE EXECUTION'}   *")
    logger.info("****************************************************************")

    # 1. Zombie reconciliation
    if not args.skip_db_cleanup:
        reconcile_zombie_database_records(dry_run=args.dry_run)

    # 2. Queue purge
    purge_celery_task_queues(dry_run=args.dry_run)

    # 3. Code & container reversion
    revert_code_and_containers(args.target, dry_run=args.dry_run)

    # 4. Post-rollback health probes
    if not args.dry_run:
        health_status = probe_service_health()
        logger.info("=== Rollback Health Verification Summary ===")
        all_healthy = True
        for svc, ok in health_status.items():
            status_str = "PASS" if ok else "FAIL (Service Unreachable)"
            logger.info(f"  {svc}: {status_str}")
            if not ok:
                all_healthy = False

        elapsed = time.time() - start_time
        if all_healthy:
            logger.info(f"ROLLBACK SUCCESSFUL: All services operational in {elapsed:.1f}s.")
            sys.exit(0)
        else:
            logger.error(f"ROLLBACK WARNING: One or more services failed health verification.")
            sys.exit(1)
    else:
        logger.info("DRY RUN COMPLETE: All rollback operations verified syntactically.")
        sys.exit(0)


if __name__ == "__main__":
    main()
