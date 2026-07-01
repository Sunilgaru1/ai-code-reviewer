import logging
from celery import shared_task
from django.db import transaction
from .models import Repository, WebhookEvent, Commit, FileChange

# This creates a permanent paper trail on your server so we know what Celery is doing.
logger = logging.getLogger(__name__)

# If the database is locked, Celery won't just fail and give up. It will wait 60 seconds and try again, up to 3 times.
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_github_webhook(self, event_type, payload):
    if event_type != 'push':
        logger.info(f"Ignored event type: {event_type}")
        return f"Ignored event type: {event_type}"

    # Wrap everything in a try/except block to catch crashes
    try:
        with transaction.atomic():
            repo_data = payload.get('repository', {})
            commits_data = payload.get('commits', [])
            
            # Log that we are starting work
            logger.info(f"Processing webhook for repo: {repo_data.get('full_name')}")
            
            repo, _ = Repository.objects.get_or_create(
                full_name=repo_data.get('full_name'),
                defaults={
                    'name': repo_data.get('name'),
                    'url': repo_data.get('html_url'),
                    'github_id': repo_data.get('id'),
                }
            )

            event = WebhookEvent.objects.create(
                repository=repo,
                event_type=event_type,
                payload=payload,
                processed=True
            )

            files_to_save_at_once = []

            for c in commits_data:
                commit_obj, created = Commit.objects.get_or_create(
                    commit_id=c.get('id'),
                    defaults={
                        'repo': repo,
                        'event': event,
                        'message': c.get('message', ''),
                        'author': (c.get('author') or {}).get('name', 'unknown'),
                        'timestamp': c.get('timestamp'),
                    }
                )

                if created:
                    for f in c.get("added", []):
                        files_to_save_at_once.append(FileChange(commit=commit_obj, filename=f, status="added"))
                    for f in c.get("modified", []):
                        files_to_save_at_once.append(FileChange(commit=commit_obj, filename=f, status="modified"))
                    for f in c.get("removed", []):
                        files_to_save_at_once.append(FileChange(commit=commit_obj, filename=f, status="removed"))
            
            if files_to_save_at_once:
                FileChange.objects.bulk_create(files_to_save_at_once)
                # Log exactly how many files we saved efficiently
                logger.info(f"Bulk created {len(files_to_save_at_once)} file changes.")
        
        success_msg = f"Successfully processed {len(commits_data)} commits for {repo.name}"
        logger.info(success_msg)
        return success_msg

    except Exception as exc:
        # If a crash happens, log the exact error and tell Celery to restart the task.
        logger.error(f"Error processing webhook: {exc}. Retrying...")
        raise self.retry(exc=exc)