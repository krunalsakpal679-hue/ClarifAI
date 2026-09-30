"""
Django management command to reprocess stale documents processed before Phase 1 fix (commit 941da05).
Supports --dry-run (default), --execute, --inline, and --before-date options.
"""
from datetime import datetime
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.documents.models import Document, DocumentStatus, Clause, DocumentSummary

logger = logging.getLogger(__name__)

# Default cutoff: commit 941da05 timestamp (2026-09-30 00:22:42+05:30)
PHASE1_COMMIT_TIMESTAMP = "2026-09-30T00:22:42+05:30"


class Command(BaseCommand):
    help = "Identifies and re-queues documents processed before commit 941da05 (Phase 1 SAFE-fallback elimination)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Report count and IDs of stale documents without modifying database or queueing jobs.'
        )
        parser.add_argument(
            '--execute',
            action='store_true',
            default=False,
            help='Execute actual reprocessing of identified stale documents.'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            default=False,
            help='Process all documents regardless of uploaded_at timestamp.'
        )
        parser.add_argument(
            '--before-date',
            type=str,
            default=PHASE1_COMMIT_TIMESTAMP,
            help=f'ISO-8601 timestamp cutoff (default: {PHASE1_COMMIT_TIMESTAMP}).'
        )
        parser.add_argument(
            '--inline',
            action='store_true',
            default=False,
            help='Execute reprocessing inline synchronously using the real process_document task logic.'
        )

    def handle(self, *args, **options):
        is_dry_run = options.get('dry_run')
        is_execute = options.get('execute')
        process_all = options.get('all')
        before_date_str = options.get('before_date')
        run_inline = options.get('inline')

        if not is_execute and not is_dry_run:
            # Default to dry-run mode for safety
            is_dry_run = True
            self.stdout.write(self.style.WARNING("No mode specified: defaulting to --dry-run for safety."))

        try:
            cutoff_dt = datetime.fromisoformat(before_date_str)
            if timezone.is_naive(cutoff_dt):
                cutoff_dt = timezone.make_aware(cutoff_dt)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Invalid timestamp format '{before_date_str}': {e}"))
            return

        self.stdout.write(f"Querying stale documents with cutoff: {cutoff_dt.isoformat()} (all={process_all})...")

        if process_all:
            query = Document.objects.all()
        else:
            query = Document.objects.filter(uploaded_at__lt=cutoff_dt)

        docs = list(query.order_by('uploaded_at'))
        count = len(docs)

        self.stdout.write(self.style.SUCCESS(f"Found {count} candidate documents."))

        for idx, doc in enumerate(docs, start=1):
            clause_count = doc.clauses.count()
            self.stdout.write(
                f" [{idx}/{count}] Doc ID: {doc.id} | Name: {doc.original_filename} | "
                f"Uploaded: {doc.uploaded_at.isoformat()} | Status: {doc.status} | Clauses: {clause_count}"
            )

        if is_dry_run:
            self.stdout.write(self.style.NOTICE(
                f"\n[DRY RUN COMPLETE] Total documents identified: {count}. No database changes or task dispatches made."
            ))
            return

        if is_execute:
            self.stdout.write(self.style.WARNING(f"\n[EXECUTION START] Reprocessing {count} documents..."))
            reprocessed_count = 0

            for doc in docs:
                self.stdout.write(f"Processing doc {doc.id} ({doc.original_filename})...")
                # Reset document status and clean previous clauses/summaries for fresh run
                doc.clauses.all().delete()
                if hasattr(doc, 'summary'):
                    try:
                        doc.summary.delete()
                    except Exception:
                        pass

                # Reset state machine to QUEUED
                doc.status = DocumentStatus.QUEUED
                doc.failure_reason = None
                doc.save(update_fields=['status', 'failure_reason', 'updated_at'])

                if run_inline:
                    from tasks.document_tasks import process_document
                    try:
                        res = process_document(str(doc.id))
                        reprocessed_count += 1
                        doc.refresh_from_db()
                        self.stdout.write(
                            self.style.SUCCESS(f"  -> Successfully reprocessed doc {doc.id}: status={doc.status}, clauses={doc.clauses.count()}")
                        )
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"  -> Failed to reprocess doc {doc.id}: {e}"))
                else:
                    from tasks.document_tasks import process_document
                    process_document.delay(str(doc.id))
                    reprocessed_count += 1
                    self.stdout.write(self.style.SUCCESS(f"  -> Dispatched Celery task for doc {doc.id}"))

            self.stdout.write(self.style.SUCCESS(f"\n[EXECUTION COMPLETE] Successfully reprocessed/queued {reprocessed_count}/{count} documents."))
